# AI Scroll Evaluation Data

This folder contains a reproducible, privacy-safe synthetic dataset for the PE6201 individual project.

## Generate and validate

```powershell
python 02_data/generate_synthetic_dataset.py
python 02_data/validate_dataset.py
```

The generator creates:

- `evaluation_emails.jsonl`: 50 synthetic input emails;
- `gold_labels_draft.jsonl`: one draft human label per email;
- `thread_gold_draft.jsonl`: final expected state for the eight multi-email threads;
- `gold_label_review.csv`: a spreadsheet-friendly review sheet;
- `dataset_summary.json`: exact inventory counts and the evaluation reference time.

## Important label status

Every generated label begins as `pending_human_review`. The labels must be checked by Jason before the final model run. After review, run:

```powershell
python 02_data/freeze_labels.py
```

The freeze command refuses to run while any row remains unapproved. This prevents the project from claiming that model-generated draft labels are already human gold labels.

## Evaluation units

The dataset contains 50 emails but 38 evaluation threads:

- 30 independent single-email threads;
- 8 genuine multi-email threads containing 20 emails.

## Privacy and limitations

All names, addresses and course messages are fictional. No private inbox content is included. Synthetic data is useful for repeatability and edge-case coverage, but it cannot prove performance on the full diversity of real university emails. The final report must state this limitation.

