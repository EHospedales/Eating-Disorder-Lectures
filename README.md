# Eating-Disorder-Lectures

Interactive quiz-style PowerPoint lecture tools for psychiatry residents covering eating disorders board exam content.

## Overview

This repository provides:

- **`questions/quiz_bank.json`** – A comprehensive board-exam question bank with 35+ questions across 8 topic areas, covering DSM-5 diagnostic criteria, epidemiology, medical complications, psychotherapy, pharmacotherapy, hospitalization criteria, comorbidities, and prognosis.
- **`generate_quiz_pptx.py`** – A Python script that generates interactive, visually styled PowerPoint presentations from the question bank.
- **`app.py`** – A Streamlit web interface for generating and downloading quiz decks without using command-line arguments.

Questions are formatted as:
- **Multiple-choice** (standard 4-option format, matching ABPN board style)
- **True/False** (with rapid-fire format for group voting)
- **Case Vignettes** (clinical stems + question + answer reveal)

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the full quiz presentation (standard format)
python generate_quiz_pptx.py

# 3. (Optional) Launch web interface
streamlit run app.py
```

This creates `eating_disorders_quiz.pptx` in the current directory.

---

## Deploy as a Shareable Website

This repo is configured for easy web deployment of the Streamlit app.

### Option A: Streamlit Community Cloud (fastest)

1. Push this repository to GitHub.
2. Go to Streamlit Community Cloud and click **New app**.
3. Select this repo/branch and set entry point to `app.py`.
4. Deploy.

You get a shareable public URL hosted by Streamlit.

### Option B: Render (Docker)

This repo includes `Dockerfile` and `render.yaml`.

1. Push the repo to GitHub.
2. In Render, create a new **Blueprint** service from the repository.
3. Render reads `render.yaml` and deploys automatically.

Render provides a shareable HTTPS URL.

### Option C: Any Docker host

```bash
docker build -t ed-quiz-app .
docker run -p 8501:8501 -e PORT=8501 ed-quiz-app
```

Then open `http://localhost:8501` (or your host's mapped URL).

---

## Usage

### Standard Format (default)
Question → audience thinks/discusses → advance to answer reveal slide.

```bash
python generate_quiz_pptx.py --output eating_disorders_quiz.pptx
```

### Lightning Round Team Challenge
Timed team-play mode with a rapid-fire rules slide and score tracker.

```bash
python generate_quiz_pptx.py --format lightning_round --output lightning_round_game.pptx
```

### Audience Response Format
Instructions guide presenters to integrate with Poll Everywhere, Mentimeter, or similar live-voting tools.

```bash
python generate_quiz_pptx.py --format audience_response --output ars_quiz.pptx
```

### Filter by Topic Category
Generate a focused quiz on a specific category:

```bash
python generate_quiz_pptx.py --category "Pharmacotherapy"
python generate_quiz_pptx.py --category "Medical Complications"
python generate_quiz_pptx.py --category "DSM-5"
```

### Custom Output Path
```bash
python generate_quiz_pptx.py --output /path/to/my_lecture.pptx
```

### Append Quiz Slides to an Existing PowerPoint
Use an existing `.pptx` as a template and append quiz slides to the end:

```bash
python generate_quiz_pptx.py --template /path/to/existing_deck.pptx --output combined_deck.pptx
```

To place generated slides at the beginning instead:

```bash
python generate_quiz_pptx.py --template /path/to/existing_deck.pptx --insert-position start --output combined_deck.pptx
```

### Front-End Interface (Streamlit)
Run the app locally:

```bash
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

If Streamlit does not load (e.g., port in use), run:

```bash
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

In the browser UI you can:
- Select format (`standard`, `lightning_round`, `audience_response`)
- Use default quiz bank or upload a custom JSON bank
- Choose question types to include (`multiple_choice`, `true_false`, `case_vignette`)
- Filter by categories and search question text/IDs
- Pick either random sample, first N, or exact questions from a readable selector
- In exact-selection mode, switch between a single list or collapsible category groups
- Set how many questions to include when using sample modes
- Upload an existing `.pptx` template to append generated slides
- Choose whether generated slides go at the start or end of the template
- Download the generated PowerPoint directly

---

## Question Bank Topics

| Category | Question Types | # Questions |
|---|---|---|
| DSM-5 Diagnostic Criteria | Multiple choice | 8 |
| Epidemiology & Risk Factors | Multiple choice | 4 |
| Medical Complications & Laboratory Findings | Multiple choice | 7 |
| Treatment – Psychotherapy | Multiple choice | 4 |
| Treatment – Pharmacotherapy | Multiple choice | 5 |
| Hospitalization & Level of Care | Multiple choice | 2 |
| Comorbidities & Special Populations | Multiple choice | 3 |
| Prognosis & Outcomes | Multiple choice | 2 |
| Clinical Vignettes | Case vignette | 4 |
| True or False | True/False | 5 |

---

## High-Yield Board Facts Covered

- AN has the **highest mortality rate** of any psychiatric disorder
- DSM-5 **removed amenorrhea** as a required criterion for AN
- DSM-5 reduced BN binge/purge frequency to **once per week** (was twice)
- **Fluoxetine 60 mg/day** = only FDA-approved medication for Bulimia Nervosa
- **Lisdexamfetamine (Vyvanse)** = only FDA-approved medication for Binge Eating Disorder
- **Bupropion is contraindicated** in BN (significantly increased seizure risk)
- **Refeeding syndrome** = hypophosphatemia → cardiac/respiratory failure
- **Russell's Sign** = dorsal hand calluses from self-induced vomiting (BN)
- **FBT (Maudsley Approach)** = first-line therapy for adolescents with AN
- **CBT-E** = first-line psychotherapy for BN and BED in adults

---

## Adding Questions

To add new questions, edit `questions/quiz_bank.json`. Each question follows this structure:

```json
{
  "id": "UNIQUE-ID",
  "type": "multiple_choice",
  "question": "Question stem text?",
  "choices": {
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  },
  "answer": "B",
  "explanation": "Detailed explanation with teaching points.",
  "difficulty": "easy|medium|hard",
  "board_topic": "Short topic label"
}
```

Supported `type` values: `multiple_choice`, `true_false`, `case_vignette`.

For `case_vignette`, also include a `"clinical_stem"` field with the patient scenario.

---

## Presentation Tips for Facilitators

1. **Use Presenter View** in PowerPoint to see notes while the audience sees the question.
2. **Pause on the question slide** and allow 60–90 seconds for discussion before advancing.
3. For **Lightning Round format**, form teams of 3–5 residents, use a 20–30 second timer, and track points on the score tracker slide.
4. For **Audience Response format**, set up a Mentimeter or Poll Everywhere poll before the session and embed the QR code or URL in the question slide notes.
5. **End each session** with the High-Yield Facts summary slides for rapid review.

---

## Reference

Questions are based on:
- DSM-5-TR (APA, 2022)
- APA Practice Guidelines for Eating Disorders
- ABPN Psychiatry Examination Content Specifications