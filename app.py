#!/usr/bin/env python3
"""Streamlit frontend for generating eating-disorders quiz PowerPoint decks."""

import io
import json
import random
import tempfile
from pathlib import Path

import streamlit as st
from pptx import Presentation

from generate_quiz_pptx import QUIZ_BANK_PATH, _load_quiz_bank, build_presentation


st.set_page_config(page_title="Eating Disorders Quiz PPT Builder", layout="wide")

st.title("Eating Disorders Quiz PPT Builder")
st.caption("Generate customized quiz decks and append them to existing PowerPoints.")


def _flatten_questions(quiz_bank: dict) -> list[dict]:
    flat = []
    for category in quiz_bank.get("categories", []):
        category_name = category.get("name", "Uncategorized")
        for question in category.get("questions", []):
            flat.append(
                {
                    "id": question.get("id", "UNKNOWN"),
                    "type": question.get("type", "multiple_choice"),
                    "category": category_name,
                    "question": question.get("question", ""),
                }
            )
    return flat


def _build_selected_bank(quiz_bank: dict, selected_ids: set[str]) -> dict:
    categories = []
    for category in quiz_bank.get("categories", []):
        questions = [
            question
            for question in category.get("questions", [])
            if question.get("id") in selected_ids
        ]
        if questions:
            categories.append(
                {
                    "name": category.get("name", "Uncategorized"),
                    "questions": questions,
                }
            )

    metadata = dict(quiz_bank.get("metadata", {}))
    metadata["selection_count"] = len(selected_ids)
    return {"metadata": metadata, "categories": categories}


def _question_label(question: dict) -> str:
    preview = question.get("question", "").strip().replace("\n", " ")
    if len(preview) > 110:
        preview = f"{preview[:107]}..."
    return (
        f"{question.get('id', 'UNKNOWN')} | "
        f"{question.get('type', 'multiple_choice')} | "
        f"{question.get('category', 'Uncategorized')} | "
        f"{preview}"
    )


def _all_question_ids(quiz_bank: dict) -> set[str]:
    ids = set()
    for category in quiz_bank.get("categories", []):
        for question in category.get("questions", []):
            qid = question.get("id")
            if qid:
                ids.add(qid)
    return ids


def _category_map(quiz_bank: dict) -> dict[str, dict]:
    return {
        category.get("name", "Uncategorized"): category
        for category in quiz_bank.get("categories", [])
    }


def _add_category_if_missing(quiz_bank: dict, category_name: str):
    category_name = category_name.strip()
    if not category_name:
        return
    existing = _category_map(quiz_bank)
    if category_name not in existing:
        quiz_bank.setdefault("categories", []).append({"name": category_name, "questions": []})


def _add_question_to_bank(quiz_bank: dict, category_name: str, question: dict):
    _add_category_if_missing(quiz_bank, category_name)
    categories = _category_map(quiz_bank)
    categories[category_name].setdefault("questions", []).append(question)


def _all_questions_with_category(quiz_bank: dict):
    for category in quiz_bank.get("categories", []):
        category_name = category.get("name", "Uncategorized")
        for question in category.get("questions", []):
            yield category_name, question


def _merge_quiz_banks(base_bank: dict, incoming_bank: dict, overwrite_existing: bool) -> tuple[int, int]:
    """Merge incoming questions into base bank by question ID.

    Returns tuple: (added_count, updated_count)
    """
    base_index = {}
    for category_name, question in _all_questions_with_category(base_bank):
        qid = question.get("id")
        if qid:
            base_index[qid] = (category_name, question)

    added_count = 0
    updated_count = 0

    for incoming_category_name, incoming_question in _all_questions_with_category(incoming_bank):
        incoming_id = incoming_question.get("id")
        if not incoming_id:
            continue

        if incoming_id in base_index:
            if not overwrite_existing:
                continue

            current_category_name, _current_question = base_index[incoming_id]
            _delete_question_from_bank(base_bank, incoming_id)
            _add_question_to_bank(
                base_bank,
                incoming_category_name or current_category_name,
                json.loads(json.dumps(incoming_question)),
            )
            updated_count += 1
        else:
            _add_question_to_bank(
                base_bank,
                incoming_category_name,
                json.loads(json.dumps(incoming_question)),
            )
            added_count += 1

    return added_count, updated_count


def _find_question_entry(quiz_bank: dict, question_id: str):
    for category in quiz_bank.get("categories", []):
        for idx, question in enumerate(category.get("questions", [])):
            if question.get("id") == question_id:
                return category, idx, question
    return None, None, None


def _delete_question_from_bank(quiz_bank: dict, question_id: str) -> bool:
    category, idx, _question = _find_question_entry(quiz_bank, question_id)
    if category is None:
        return False
    category.get("questions", []).pop(idx)
    return True


st.subheader("1) Quiz Bank")
use_default_bank = st.checkbox("Use default quiz bank", value=True)
uploaded_bank = None
if not use_default_bank:
    uploaded_bank = st.file_uploader(
        "Upload quiz bank JSON",
        type=["json"],
        help="Upload a JSON file following the same schema as questions/quiz_bank.json.",
    )

quiz_bank = None
try:
    if use_default_bank:
        quiz_bank = _load_quiz_bank(QUIZ_BANK_PATH)
    elif uploaded_bank is not None:
        quiz_bank = json.loads(uploaded_bank.getvalue().decode("utf-8"))
except Exception as exc:
    st.error("Unable to load quiz bank JSON.")
    st.exception(exc)

if not quiz_bank:
    st.info("Load a quiz bank to continue.")
    st.stop()

source_signature = "default" if use_default_bank else (
    uploaded_bank.name if uploaded_bank is not None else "none"
)
if (
    "working_quiz_bank" not in st.session_state
    or st.session_state.get("bank_source_signature") != source_signature
):
    st.session_state["working_quiz_bank"] = json.loads(json.dumps(quiz_bank))
    st.session_state["bank_source_signature"] = source_signature

quiz_bank = st.session_state["working_quiz_bank"]

st.subheader("1b) Edit Question Bank (Optional)")
with st.expander("Add categories/questions from the frontend", expanded=False):
    st.markdown("### Import previously edited bank")
    import_bank_file = st.file_uploader(
        "Upload edited quiz bank JSON",
        type=["json"],
        key="import_bank_file",
        help="Import a previously downloaded quiz bank file.",
    )
    import_mode = st.radio(
        "Import mode",
        ["Replace current working bank", "Merge into current working bank"],
        horizontal=False,
        key="import_mode",
    )
    overwrite_existing_ids = st.checkbox(
        "When merging, overwrite existing questions with matching IDs",
        value=False,
        key="merge_overwrite_ids",
    )
    if st.button("Apply imported bank", key="apply_imported_bank"):
        if import_bank_file is None:
            st.error("Upload a JSON file to import.")
        else:
            try:
                imported_bank = json.loads(import_bank_file.getvalue().decode("utf-8"))
                if not isinstance(imported_bank, dict) or "categories" not in imported_bank:
                    st.error("Invalid quiz bank format: missing top-level 'categories'.")
                else:
                    if import_mode == "Replace current working bank":
                        st.session_state["working_quiz_bank"] = imported_bank
                        st.session_state["selected_question_ids"] = []
                        st.success("Replaced current working bank with imported bank.")
                    else:
                        added_count, updated_count = _merge_quiz_banks(
                            quiz_bank,
                            imported_bank,
                            overwrite_existing=overwrite_existing_ids,
                        )
                        st.success(
                            f"Merge complete. Added: {added_count}, Updated: {updated_count}."
                        )
                    st.rerun()
            except Exception as exc:
                st.error("Unable to import quiz bank JSON.")
                st.exception(exc)

    existing_categories = [c.get("name", "Uncategorized") for c in quiz_bank.get("categories", [])]

    new_category_col_1, new_category_col_2 = st.columns([3, 1])
    with new_category_col_1:
        new_category_name = st.text_input(
            "New category name",
            placeholder="e.g., Emergency Psychiatry Pearls",
            key="new_category_name",
        ).strip()
    with new_category_col_2:
        if st.button("Add category"):
            if not new_category_name:
                st.error("Enter a category name first.")
            elif new_category_name in existing_categories:
                st.warning("That category already exists.")
            else:
                _add_category_if_missing(quiz_bank, new_category_name)
                st.success(f"Added category: {new_category_name}")
                st.rerun()

    with st.expander("Add a question", expanded=False):
        st.markdown("### Add a new question")
        q_type = st.selectbox(
            "Question type",
            ["multiple_choice", "true_false", "case_vignette"],
            key="add_q_type",
        )

        category_options = [c.get("name", "Uncategorized") for c in quiz_bank.get("categories", [])]
        selected_category = st.selectbox(
            "Category",
            category_options,
            key="add_q_category",
        )

        with st.form("add_question_form"):
            q_id = st.text_input("Question ID", placeholder="e.g., CUSTOM-001").strip()
            board_topic = st.text_input("Board topic label", placeholder="Short topic label").strip()
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
            question_text = st.text_area("Question stem", height=110).strip()

            clinical_stem = ""
            choices = {}
            answer = ""

            if q_type in {"multiple_choice", "case_vignette"}:
                choice_col_1, choice_col_2 = st.columns(2)
                with choice_col_1:
                    choice_a = st.text_input("Choice A").strip()
                    choice_b = st.text_input("Choice B").strip()
                with choice_col_2:
                    choice_c = st.text_input("Choice C").strip()
                    choice_d = st.text_input("Choice D").strip()
                choices = {"A": choice_a, "B": choice_b, "C": choice_c, "D": choice_d}
                answer = st.selectbox("Correct answer", ["A", "B", "C", "D"]).strip()

                if q_type == "case_vignette":
                    clinical_stem = st.text_area("Clinical stem", height=120).strip()

            if q_type == "true_false":
                answer = st.selectbox("Correct answer", ["true", "false"]).strip()

            explanation = st.text_area("Explanation", height=120).strip()

            add_question_clicked = st.form_submit_button("Add question to bank")

            if add_question_clicked:
                existing_ids = _all_question_ids(quiz_bank)

                if not q_id:
                    st.error("Question ID is required.")
                elif q_id in existing_ids:
                    st.error("Question ID already exists. Use a unique ID.")
                elif not question_text:
                    st.error("Question stem is required.")
                elif not explanation:
                    st.error("Explanation is required.")
                elif q_type in {"multiple_choice", "case_vignette"} and any(not v for v in choices.values()):
                    st.error("All choices A-D are required for this question type.")
                elif q_type == "case_vignette" and not clinical_stem:
                    st.error("Clinical stem is required for case vignette questions.")
                else:
                    new_question = {
                        "id": q_id,
                        "type": q_type,
                        "question": question_text,
                        "answer": answer,
                        "explanation": explanation,
                        "difficulty": difficulty,
                        "board_topic": board_topic or selected_category,
                    }

                    if q_type in {"multiple_choice", "case_vignette"}:
                        new_question["choices"] = choices
                    if q_type == "case_vignette":
                        new_question["clinical_stem"] = clinical_stem

                    _add_question_to_bank(quiz_bank, selected_category, new_question)
                    st.success(f"Added question {q_id} to {selected_category}.")
                    st.rerun()

    with st.expander("Edit or delete a question", expanded=False):
        st.markdown("### Edit or delete an existing question")
        editable_flat = _flatten_questions(quiz_bank)

        if not editable_flat:
            st.info("No existing questions to edit yet.")
        else:
            edit_option_map = {
                _question_label(item): item["id"]
                for item in editable_flat
            }
            current_question = None
            edit_choice = st.selectbox(
                "Select question to edit",
                options=["-- Select question --", *edit_option_map.keys()],
            )

            if edit_choice != "-- Select question --":
                edit_qid = edit_option_map[edit_choice]
                current_category, _current_idx, current_question = _find_question_entry(quiz_bank, edit_qid)

            if current_question is not None:
                current_type = current_question.get("type", "multiple_choice")
                current_choices = current_question.get("choices", {})
                category_options = [c.get("name", "Uncategorized") for c in quiz_bank.get("categories", [])]
                current_category_name = current_category.get("name", "Uncategorized")
                if current_category_name not in category_options:
                    category_options.append(current_category_name)

                with st.form("edit_question_form"):
                    edit_q_id = st.text_input("Question ID", value=current_question.get("id", "")).strip()
                    edit_q_type = st.selectbox(
                        "Question type",
                        ["multiple_choice", "true_false", "case_vignette"],
                        index=["multiple_choice", "true_false", "case_vignette"].index(current_type)
                        if current_type in {"multiple_choice", "true_false", "case_vignette"}
                        else 0,
                    )
                    edit_category = st.selectbox(
                        "Category",
                        category_options,
                        index=category_options.index(current_category_name),
                    )
                    edit_board_topic = st.text_input(
                        "Board topic label",
                        value=current_question.get("board_topic", ""),
                    ).strip()
                    edit_difficulty = st.selectbox(
                        "Difficulty",
                        ["easy", "medium", "hard"],
                        index=["easy", "medium", "hard"].index(current_question.get("difficulty", "medium"))
                        if current_question.get("difficulty", "medium") in {"easy", "medium", "hard"}
                        else 1,
                    )
                    edit_question_text = st.text_area(
                        "Question stem",
                        value=current_question.get("question", ""),
                        height=110,
                    ).strip()

                    edit_clinical_stem = ""
                    edit_answer = ""
                    edit_choices = {}

                    if edit_q_type in {"multiple_choice", "case_vignette"}:
                        edit_choice_col_1, edit_choice_col_2 = st.columns(2)
                        with edit_choice_col_1:
                            edit_choice_a = st.text_input("Choice A", value=current_choices.get("A", "")).strip()
                            edit_choice_b = st.text_input("Choice B", value=current_choices.get("B", "")).strip()
                        with edit_choice_col_2:
                            edit_choice_c = st.text_input("Choice C", value=current_choices.get("C", "")).strip()
                            edit_choice_d = st.text_input("Choice D", value=current_choices.get("D", "")).strip()

                        edit_choices = {
                            "A": edit_choice_a,
                            "B": edit_choice_b,
                            "C": edit_choice_c,
                            "D": edit_choice_d,
                        }
                        edit_answer = st.selectbox(
                            "Correct answer",
                            ["A", "B", "C", "D"],
                            index=["A", "B", "C", "D"].index(current_question.get("answer", "A"))
                            if current_question.get("answer", "A") in {"A", "B", "C", "D"}
                            else 0,
                        ).strip()

                        if edit_q_type == "case_vignette":
                            edit_clinical_stem = st.text_area(
                                "Clinical stem",
                                value=current_question.get("clinical_stem", ""),
                                height=120,
                            ).strip()

                    if edit_q_type == "true_false":
                        current_tf_answer = str(current_question.get("answer", "true")).strip().lower()
                        edit_answer = st.selectbox(
                            "Correct answer",
                            ["true", "false"],
                            index=0 if current_tf_answer == "true" else 1,
                        ).strip()

                    edit_explanation = st.text_area(
                        "Explanation",
                        value=current_question.get("explanation", ""),
                        height=120,
                    ).strip()

                    save_edit_clicked = st.form_submit_button("Save changes")

                    if save_edit_clicked:
                        existing_ids = _all_question_ids(quiz_bank)

                        if not edit_q_id:
                            st.error("Question ID is required.")
                        elif edit_q_id != edit_qid and edit_q_id in existing_ids:
                            st.error("Question ID already exists. Use a unique ID.")
                        elif not edit_question_text:
                            st.error("Question stem is required.")
                        elif not edit_explanation:
                            st.error("Explanation is required.")
                        elif edit_q_type in {"multiple_choice", "case_vignette"} and any(
                            not value for value in edit_choices.values()
                        ):
                            st.error("All choices A-D are required for this question type.")
                        elif edit_q_type == "case_vignette" and not edit_clinical_stem:
                            st.error("Clinical stem is required for case vignette questions.")
                        else:
                            updated_question = {
                                "id": edit_q_id,
                                "type": edit_q_type,
                                "question": edit_question_text,
                                "answer": edit_answer,
                                "explanation": edit_explanation,
                                "difficulty": edit_difficulty,
                                "board_topic": edit_board_topic or edit_category,
                            }

                            if edit_q_type in {"multiple_choice", "case_vignette"}:
                                updated_question["choices"] = edit_choices
                            if edit_q_type == "case_vignette":
                                updated_question["clinical_stem"] = edit_clinical_stem

                            old_category = current_category_name
                            _delete_question_from_bank(quiz_bank, edit_qid)
                            _add_question_to_bank(quiz_bank, edit_category, updated_question)

                            if "selected_question_ids" in st.session_state:
                                selected_set = set(st.session_state["selected_question_ids"])
                                if edit_qid in selected_set:
                                    selected_set.remove(edit_qid)
                                    selected_set.add(edit_q_id)
                                    st.session_state["selected_question_ids"] = sorted(selected_set)

                            st.success(
                                f"Updated question {edit_qid} → {edit_q_id} "
                                f"({old_category} → {edit_category})."
                            )
                            st.rerun()

                delete_confirm = st.checkbox(
                    f"Confirm delete question {edit_qid}",
                    key=f"confirm_delete_{edit_qid}",
                )
                if st.button("Delete selected question", key=f"delete_button_{edit_qid}"):
                    if not delete_confirm:
                        st.error("Please confirm deletion first.")
                    else:
                        deleted = _delete_question_from_bank(quiz_bank, edit_qid)
                        if deleted:
                            if "selected_question_ids" in st.session_state:
                                st.session_state["selected_question_ids"] = [
                                    qid for qid in st.session_state["selected_question_ids"]
                                    if qid != edit_qid
                                ]
                            st.success(f"Deleted question {edit_qid}.")
                            st.rerun()
                        else:
                            st.warning("Question not found; it may have already been removed.")

    bank_json = json.dumps(quiz_bank, indent=2, ensure_ascii=False)
    st.download_button(
        label="Download updated quiz bank JSON",
        data=bank_json.encode("utf-8"),
        file_name="quiz_bank_updated.json",
        mime="application/json",
    )

flat_questions = _flatten_questions(quiz_bank)
if not flat_questions:
    st.error("No questions found in the loaded quiz bank.")
    st.stop()

st.subheader("2) Select Questions")

if "selected_question_ids" not in st.session_state:
    st.session_state["selected_question_ids"] = []

all_types = sorted({item["type"] for item in flat_questions})
category_order = list(dict.fromkeys(item["category"] for item in flat_questions))

filter_col_1, filter_col_2 = st.columns(2)
with filter_col_1:
    selected_types = st.multiselect(
        "Question types",
        all_types,
        default=all_types,
    )
with filter_col_2:
    selected_categories = st.multiselect(
        "Categories",
        category_order,
        default=category_order,
    )

search_query = st.text_input(
    "Search question text / ID",
    placeholder="Type keywords like electrolyte, DSM-5, BN...",
).strip().lower()

eligible_questions = [
    item for item in flat_questions
    if item["type"] in selected_types and item["category"] in selected_categories
]

if search_query:
    eligible_questions = [
        item for item in eligible_questions
        if (
            search_query in item.get("question", "").lower()
            or search_query in item.get("id", "").lower()
            or search_query in item.get("category", "").lower()
        )
    ]

summary_col_1, summary_col_2 = st.columns(2)
with summary_col_1:
    st.caption(f"Eligible questions: {len(eligible_questions)}")
with summary_col_2:
    st.caption(f"Currently selected: {len(st.session_state['selected_question_ids'])}")

if not eligible_questions:
    st.warning("No questions match the selected type/category filters.")
    st.stop()

selection_mode = st.radio(
    "Question selection mode",
    ["Pick specific questions", "Random sample", "First N in bank order"],
    horizontal=False,
)

selected_question_ids = list(st.session_state["selected_question_ids"])
if selection_mode in {"Random sample", "First N in bank order"}:
    default_count = min(20, len(eligible_questions))
    question_count = st.slider(
        "How many questions to include",
        min_value=1,
        max_value=len(eligible_questions),
        value=default_count,
    )
    if selection_mode == "Random sample":
        selected_question_ids = [item["id"] for item in random.sample(eligible_questions, question_count)]
    else:
        selected_question_ids = [item["id"] for item in eligible_questions[:question_count]]
else:
    st.markdown("Use quick actions or manually pick exact questions below.")

    action_col_1, action_col_2, action_col_3 = st.columns([1, 1, 2])
    with action_col_1:
        if st.button("Select all filtered"):
            st.session_state["selected_question_ids"] = [item["id"] for item in eligible_questions]
    with action_col_2:
        if st.button("Clear selection"):
            st.session_state["selected_question_ids"] = []
    with action_col_3:
        random_pick_n = st.number_input(
            "Random add (N)",
            min_value=1,
            max_value=len(eligible_questions),
            value=min(10, len(eligible_questions)),
            step=1,
        )
        if st.button("Apply random add"):
            st.session_state["selected_question_ids"] = [
                item["id"] for item in random.sample(eligible_questions, int(random_pick_n))
            ]

    filtered_by_id = {item["id"]: item for item in eligible_questions}
    retained_defaults = {
        qid for qid in st.session_state["selected_question_ids"]
        if qid in filtered_by_id
    }

    picker_view = st.radio(
        "Picker view",
        ["Grouped by category", "Single combined list"],
        horizontal=True,
    )

    if picker_view == "Single combined list":
        selected_question_ids = st.multiselect(
            "Pick exact questions",
            options=[item["id"] for item in eligible_questions],
            default=sorted(retained_defaults),
            format_func=lambda qid: _question_label(filtered_by_id[qid]),
        )
    else:
        selected_question_ids = []
        filtered_categories = list(dict.fromkeys(item["category"] for item in eligible_questions))
        category_counts = {
            category: sum(1 for item in eligible_questions if item["category"] == category)
            for category in filtered_categories
        }

        for category in filtered_categories:
            category_items = [item for item in eligible_questions if item["category"] == category]
            category_ids = [item["id"] for item in category_items]
            category_default = [qid for qid in category_ids if qid in retained_defaults]

            with st.expander(f"{category} ({category_counts[category]})", expanded=False):
                category_selected = st.multiselect(
                    f"Questions in {category}",
                    options=category_ids,
                    default=category_default,
                    key=f"cat_picker_{category}",
                    format_func=lambda qid: _question_label(filtered_by_id[qid]),
                )
                selected_question_ids.extend(category_selected)

    table_rows = []
    selected_id_set = set(selected_question_ids)
    for item in eligible_questions:
        table_rows.append(
            {
                "selected": "✓" if item["id"] in selected_id_set else "",
                "id": item["id"],
                "type": item["type"],
                "category": item["category"],
                "question": item["question"],
            }
        )
    st.dataframe(table_rows, width="stretch", hide_index=True, height=340)

st.session_state["selected_question_ids"] = selected_question_ids

st.subheader("3) Output Options")
fmt = st.selectbox(
    "Format",
    ["standard", "lightning_round", "audience_response"],
    index=0,
    help="Presentation interaction style.",
)

uploaded_template = st.file_uploader(
    "Optional: upload existing PowerPoint template (.pptx)",
    type=["pptx"],
    help="If provided, generated quiz slides are merged into this deck.",
)

insert_position = st.selectbox(
    "When using a template, place generated quiz slides at",
    ["end", "start"],
    index=0,
)

output_name = st.text_input(
    "Output filename",
    value="eating_disorders_quiz.pptx",
    help="Name used for downloaded file.",
).strip()

generate_clicked = st.button("Generate PowerPoint", type="primary")

if generate_clicked:
    try:
        if not selected_question_ids:
            st.error("Please select at least one question.")
            st.stop()

        if not output_name:
            st.error("Please provide an output filename.")
            st.stop()
        if not output_name.lower().endswith(".pptx"):
            output_name = f"{output_name}.pptx"

        custom_bank = _build_selected_bank(quiz_bank, set(selected_question_ids))

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            template_path = None
            if uploaded_template is not None:
                template_path = tmpdir_path / "template_input.pptx"
                template_path.write_bytes(uploaded_template.getvalue())

            output_path = tmpdir_path / output_name
            built_path = build_presentation(
                quiz_bank=custom_bank,
                category_filter=None,
                fmt=fmt,
                output_path=str(output_path),
                template_path=str(template_path) if template_path else None,
                insert_position=insert_position,
            )

            pptx_bytes = Path(built_path).read_bytes()
            slides_count = len(Presentation(io.BytesIO(pptx_bytes)).slides)

        st.success(
            f"Presentation generated successfully ({slides_count} slides, "
            f"{len(selected_question_ids)} selected questions)."
        )
        st.download_button(
            label="Download PowerPoint",
            data=pptx_bytes,
            file_name=output_name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    except Exception as exc:
        st.exception(exc)
