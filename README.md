# AI Scroll

AI Scroll converts selected academic emails into evidence-backed timeline items and calendar proposals. Calendar writes remain blocked until the user explicitly approves them.

## Current milestone

This first working slice accepts one email and returns:

- course;
- task;
- normalized deadline;
- urgency from a fixed rule;
- an exact evidence quote;
- a calendar preview that is not written anywhere.

The second working slice accepts a related email chain and returns one timeline item with:

- later deadline corrections applied;
- reminders deduplicated;
- cancellations blocking calendar action;
- complete evidence and field-level change history.

The default Demo mode is deterministic and requires no API key. Live model mode supports an OpenAI-compatible chat-completions endpoint through environment variables.

## Run

```powershell
cd "C:\Users\admin\Desktop\科目\PE06201\Course_Project_AI_Scroll"
python -m streamlit run app/main.py
```

Open the local URL printed by Streamlit, keep the included sample email, and select **Extract task**.

## Smoke test

```powershell
python -m app.smoke_test
python -m pytest -q
python 04_evaluation/merge_smoke_eval.py
```

## Optional live model configuration

Copy `.env.example` to `.env` or set the variables in the terminal. Never commit a real API key.

```powershell
$env:AI_SCROLL_API_KEY="your-key"
$env:AI_SCROLL_BASE_URL="https://openrouter.ai/api/v1"
$env:AI_SCROLL_MODEL="provider/model-id"
python -m streamlit run app/main.py
```

The first assessed run should record the exact model ID and provider price date. Prices are deliberately not hard-coded.

## Repository map

- `app/`: runnable application and extraction logic.
- `docs/`: frozen product contract and decisions.
- `schemas/`: machine-readable output contract.
- `02_data/`: dataset inventory and later frozen evaluation cases.
- `04_evaluation/`: evaluation plan and later scoring code.
- `05_report/`: final trade-off analysis.
- `06_demo/`: demo plan and recording assets.
- `07_submission/`: final checklist.

## Privacy

Use anonymized or synthetic emails in the public repository. `.env`, private emails and call logs are excluded from Git.
