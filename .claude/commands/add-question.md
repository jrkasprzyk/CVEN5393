Add trivia questions to a promptukit-format question bank used by JRB Industries trivia games.

## Bank file path

Use a path to the question-bank JSON file; examples below use `<bank.json>`. If your project maintains a canonical bank file (commonly under `promptukit/data/question_banks/`), treat tracked bank files as production content.

## Workflow

### 1. Choose a mode

Ask the user how they'd like to add questions:

- **Topic mode** — user names a topic (e.g. "90s hip-hop") and you draft 3–5 questions across difficulties.
- **Bulk mode** — user names a category and a count; you generate that many questions.
- **Dictation mode** — user provides a fully-formed question; you format it into the JSON schema.
- **Source material mode** — user provides a PDF, markdown, or plain text; you extract factual, testable claims and write questions from them.

For source material mode: read the source carefully, identify specific numbers, named concepts, definitions, relationships, and dates. Prefer testable facts over vague claims.

### 2. Draft questions

Read the bank file first to see which categories exist and check current answer distribution before choosing positions.

Each question must have:

```json
{
  "category":      "<must match one of the bank's declared categories>",
  "difficulty":    "easy|medium|hard",
  "prompt":        "The question text?",
  "choices":       ["Option A", "Option B", "Option C", "Option D"],
  "answer":        0,
  "quip_correct":  "Short, punchy — ideally teaches something.",
  "quip_wrong":    "Short corrective hint."
}
```

- `answer` is the **0-based index** of the correct choice.
- Do **not** include an `"id"` field — it is auto-assigned.
- Distribute correct answers across indices 0–3; aim for a roughly equal A/B/C/D split.
- Mix difficulties: roughly 40–50% easy, 30% medium, 20–30% hard.
- Distractors should be plausible — wrong answers from the same domain, not absurdities.
- Keep prompts unambiguous; avoid "which of the following" when a direct question works.
- `quip_correct` / `quip_wrong` are shown in the game UI after answering — make them punchy and, where possible, educational.

### 3. Show and get approval

Present the proposed questions in a readable format. Ask for approval before writing anything.

### 4. Add via batch mode

Save the approved draft as a temp JSON array and run (replace `<bank.json>` with your bank path):

```bash
python -m promptukit.questions.add_question --batch questions_draft.json <bank.json>
```

Or pipe directly:

```bash
cat questions_draft.json | python -m promptukit.questions.add_question --batch - <bank.json>
```

### 5. Validate

Validate the target bank file (use the same `<bank.json>` you wrote to):

```bash
python -m promptukit.questions.validate_question <bank.json>
```

Fix any reported errors (missing fields, wrong category name, bad answer index, overrepresented answer letter).

### 6. Spot-check with extract

```bash
python -m promptukit.questions.extract_question --file <bank.json> --list-categories

python -m promptukit.questions.extract_question --file <bank.json> --category "<cat>" --fields prompt,answer
```

### 7. Report stats

Report the updated stats: total count, per-category breakdown, answer distribution.

## Creating a new bank from scratch

```bash
python -m promptukit.questions.question_bank create --dest <new-bank.json> --categories "category-one,category-two"
```

Then follow steps 2–7 above.

## Question-writing guidelines

- **Easy**: recall of a single named fact (a number, a name, a definition).
- **Medium**: application or comparison (which tool does X, what does acronym Y mean).
- **Hard**: precise technical detail, edge case, or multi-step reasoning.
- Quips should have educational content — a fun fact, a correction, or context that teaches something. Purely comedic quips are fine occasionally, but don't let them dominate.
- If you're unsure about a fact, say so and let the user confirm rather than guessing.
