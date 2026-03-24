# AHP Streamlit App

An interactive AHP (Analytic Hierarchy Process) calculator that reads the
[gluc/ahp](https://github.com/gluc/ahp) YAML file format.

## Files

- `app.py` — the Streamlit app
- `requirements.txt` — Python dependencies

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a GitHub repository (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Deploy** — your app will be live at a `*.streamlit.app` URL

Share that URL with students. No installation required on their end.

## YAML format

The app accepts `.ahp` / `.yaml` files in the `gluc/ahp` format:

```yaml
Version: 2.0

Alternatives: &alternatives
  OptionA:
  OptionB:
  OptionC:

Goal:
  name: Choose the best option
  preferences:
    pairwise:
      - [CriterionA, CriterionB, 3]   # A is moderately preferred over B
      - [CriterionA, CriterionC, 1/5] # C is strongly preferred over A
      - [CriterionB, CriterionC, 1/3]
  children:
    CriterionA:
      preferences:
        pairwise:
          - [OptionA, OptionB, 2]
          - [OptionA, OptionC, 4]
          - [OptionB, OptionC, 3]
      children: *alternatives
    CriterionB:
      preferences:
        pairwise:
          - [OptionA, OptionB, 1/3]
          - [OptionA, OptionC, 1]
          - [OptionB, OptionC, 5]
      children: *alternatives
    CriterionC:
      preferences:
        pairwise:
          - [OptionA, OptionB, 1]
          - [OptionA, OptionC, 1/2]
          - [OptionB, OptionC, 1/3]
      children: *alternatives
```

### Saaty scale reminder

| Value | Meaning |
|-------|---------|
| 1     | Equal importance |
| 3     | Moderate preference |
| 5     | Strong preference |
| 7     | Very strong preference |
| 9     | Extreme preference |
| 1/3, 1/5... | Reciprocal (B preferred over A) |
