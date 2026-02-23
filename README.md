# Eating-Disorder-Lectures

Interactive quiz-style PowerPoint lecture tools for psychiatry residents covering eating disorders board exam content.

## Overview

This repository provides:

- **`questions/quiz_bank.json`** – A comprehensive board-exam question bank with 35+ questions across 8 topic areas, covering DSM-5 diagnostic criteria, epidemiology, medical complications, psychotherapy, pharmacotherapy, hospitalization criteria, comorbidities, and prognosis.
- **`generate_quiz_pptx.py`** – A Python script that generates interactive, visually styled PowerPoint presentations from the question bank.

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
```

This creates `eating_disorders_quiz.pptx` in the current directory.

---

## Usage

### Standard Format (default)
Question → audience thinks/discusses → advance to answer reveal slide.

```bash
python generate_quiz_pptx.py --output eating_disorders_quiz.pptx
```

### Jeopardy Format
Includes a category game board and score tracker for team competition.

```bash
python generate_quiz_pptx.py --format jeopardy --output jeopardy_game.pptx
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
3. For **Jeopardy format**, form teams of 3–5 residents and use the score tracker slide.
4. For **Audience Response format**, set up a Mentimeter or Poll Everywhere poll before the session and embed the QR code or URL in the question slide notes.
5. **End each session** with the High-Yield Facts summary slides for rapid review.

---

## Reference

Questions are based on:
- DSM-5-TR (APA, 2022)
- APA Practice Guidelines for Eating Disorders
- ABPN Psychiatry Examination Content Specifications