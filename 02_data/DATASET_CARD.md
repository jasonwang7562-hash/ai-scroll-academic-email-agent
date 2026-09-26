# Dataset Card - AI Scroll Synthetic Academic Email Set

## Purpose

This dataset supports repeatable evaluation of academic email extraction, urgency labelling, cross-email merging, abstention and calendar-action proposals.

## Composition

- 50 synthetic emails.
- 38 threads.
- 30 independent single-email threads.
- 8 multi-email threads containing 20 emails.
- Development, test and synthetic-holdout splits are assigned at thread level.
- Evaluation reference time: 26 September 2026, 12:00 SGT.

## Covered cases

- Explicit deadlines and event times.
- Deadline extensions.
- Time and venue corrections.
- Changed submission methods and requirements.
- Cancellation.
- Missing time zone.
- Relative or incomplete deadline language.
- Informational emails requiring no calendar action.

## Generation and labelling

`generate_synthetic_dataset.py` contains the deterministic source specifications. It creates draft labels. Jason must review every row in `gold_label_review.csv`, correct any errors and change `review_status` to `approved`. The final labels are frozen with a SHA256 checksum before the final model run.

## Privacy

The messages use fictional senders and contain no student identifiers, private links, real email addresses or API credentials.

## Limitations

The dataset was designed alongside the system and cannot represent every writing style or real inbox condition. The synthetic-holdout split is held out from prompt development but is produced by the same generator, so it is not an independent external test. Final reporting must state this limitation.

