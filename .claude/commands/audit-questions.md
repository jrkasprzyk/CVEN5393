Audit a promptukit-format question-bank JSON file (e.g. `<bank.json>`) for correctness and quality. This is a human/AI pipeline — LLM judgment as a linter for prose content, the same way you'd use ESLint for JavaScript.

## Steps

### 1. Run the automated validator

Run the validator against the target bank file:

```bash
python -m promptukit.questions.validate_question <bank.json>
```

Report any errors or warnings it surfaces before continuing.

### 2. Read the full question list

Read `<bank.json>` and scan every question for the issues below. Keep a running list of findings grouped by check type.

---

### Check A — Category correctness

The list of categories is constantly growing. Don't flag new categories, but verify the file's `"categories"` array is in sync with what's actually used in questions.

For each question, ask: does this question actually belong in its stated category? Flag any that feel miscategorized and suggest the better category. For example, a question filed under 'music' whose subject matter is really 'film soundtracks'.

---

### Check B — Content quality rules

#### Lauren's Time-Sensitive Rule

Any question whose answer could change over time — indicated by words like "last", "latest", "current", "most recent", "first active", "reigning", "current holder", "current record" — **must** begin with "As of [year],".

Flag any time-sensitive question missing this qualifier. Propose the corrected prompt text.

#### Education Rule

Quips should have educational content — a fun fact, a correction, or context that teaches something. Some purely comedic quips are fine, but the educational aspect should dominate. Flag quips that are pure throwaway with no informational value.

#### Continuity Rule

- Reject questions where the answer is embedded in the prompt text.
- Reject questions where two answer choices are functionally synonymous.
- Reject questions where wrong answers are obviously absurd (no 'Which planet is closest to the sun? A) Saturn B) The Moon C) Mercury D) A Toaster').

---

### Check C — Answer correctness

Verify that the answer at index `answer` is actually correct for each question. Cross-check your own knowledge. Flag any question where the stated answer appears wrong, and state what you believe the correct answer (and index) should be.

If genuinely uncertain about a fact, flag it as "NEEDS VERIFICATION" rather than guessing.

---

### 3. Report findings

```
AUTOMATED VALIDATOR
  <pass / list errors>

CATEGORY ISSUES  (or "None found")
  - <id>: currently '<category>', suggest '<better>' — reason

TIME-SENSITIVE ISSUES  (or "None found")
  - <id>: missing "As of [year]," — suggested fix: "<corrected prompt>"

CONTENT QUALITY ISSUES  (or "None found")
  - <id>: <description of issue>

ANSWER CORRECTNESS ISSUES  (or "None found")
  - <id>: answer index <n> ("<choice text>") appears wrong — correct answer is index <n> ("<choice text>")
  - <id>: NEEDS VERIFICATION — <what you're unsure about>
```

---

### 4. Apply fixes

After showing the report, ask the user which fixes to apply. Then:

- Apply all approved fixes to the target bank file (`<bank.json>`).
- Re-run the validator to confirm clean.
- Report final stats (total count, per-category breakdown).

## Important

- If your repo maintains a canonical bank file (commonly stored in a place like content/<bank.json>, Exam Prep/<bank.json>, assets/<bank.json>, data/<bank.json> and so forth, treat tracked bank files as production content — coordinate before moving, renaming, or removing them.
- When adding "As of [year]," use the year the answer was last verifiably correct — not necessarily the current year.
- Do not change answer positions or reformat choices unnecessarily — only fix what's actually wrong.
