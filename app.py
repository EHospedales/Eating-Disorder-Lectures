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
    st.dataframe(table_rows, use_container_width=True, hide_index=True, height=340)

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
