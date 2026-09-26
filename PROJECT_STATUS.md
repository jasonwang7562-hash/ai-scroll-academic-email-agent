# Project Status

## Decision

Keep the AI Scroll topic. The instructor's feedback supports the core idea and specifically approves the confirmation step before a real calendar write. The project now needs stronger evidence rather than a new topic.

## What must be proved

1. The system extracts actionable academic information more reliably than a simple keyword and date-rule baseline.
2. It correctly merges genuine multi-email update chains without overstating how many such chains exist.
3. Urgency is evaluated against human labels created before the model run.
4. Ambiguous cases can be escalated or left unanswered instead of guessed.
5. The calendar approval gate prevents every unauthorized write.
6. Token use and scheduled polling cost are measured.

## Current evidence

- The original Problem Statement and its NTULearn submission receipt are present.
- The instructor feedback identifies the required evaluation and cost corrections.
- Version 1 of the product contract and extraction JSON schema are frozen.
- A runnable Streamlit first slice accepts one email and displays a validated task, normalized deadline, verbatim evidence and a calendar preview.
- The deterministic sample path and clarification path pass automated tests.
- A local Git repository was initialized on 26 September 2026 at commit `3c524c6`.
- A reproducible draft dataset now contains 50 synthetic emails across 38 threads: 30 independent emails and eight multi-email chains containing 20 emails.
- Dataset structure, evidence integrity and thread counts pass automated validation. All draft labels remain pending Jason's human review before freezing.
- The completed model evaluation, remote GitHub repository, final report and final demo are still outstanding.

## Next milestone

Review and freeze the 50 draft labels, then implement cross-email matching and update merging without changing the Version 1 extraction contract.
