# Gold Label Human Review Guide

Open the Streamlit app and select **Label review** to review each case beside its source email. Excel remains available as a fallback by opening `gold_label_review.csv` directly.

## What to check in each row

1. `course_gold` matches the course named in the email.
2. `task_type_gold` uses the closest allowed category.
3. `task_title_gold` states the action clearly.
4. `deadline_gold` exactly matches the email and includes `+08:00` when SGT is explicit.
5. `urgency_gold` follows the fixed reference time of 26 September 2026, 12:00 SGT.
6. `evidence_gold` is copied word for word from the email.
7. `relation_gold` correctly distinguishes new, update and cancel messages.
8. `calendar_action_gold` is create, update, do_not_create or ask_clarification.
9. Clarification cases explain exactly which information is missing.

## How to approve

- Correct any field that is wrong.
- Enter a short explanation in `reviewer_notes` when you change a label.
- Change `review_status` from `pending_human_review` to `approved` only after checking the whole row.
- In the app, select **Approve this label** after checking the complete case. Use **Save as pending** when a case still needs investigation.
- If using Excel, save the CSV using UTF-8 encoding.

When all rows are approved, run:

```powershell
python 02_data/freeze_labels.py
```

The command creates `gold_labels_frozen.jsonl` and a SHA256 checksum. Do not edit the frozen file after running the final evaluation.
