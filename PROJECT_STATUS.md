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
- A cross-email matcher and merge engine now handle deadline extensions, reminders, metadata changes and cancellations while retaining an evidence and change audit trail.
- The eight synthetic multi-email chains pass both consolidation and final-state checks. This remains provisional because the draft labels still require human approval.
- The deterministic urgency policy, clarification handling, approval gate and event deduplication are implemented and covered by automated tests.
- The development safety test reports zero unauthorized writes using the local in-memory calendar adapter. External Google Calendar integration is still outstanding.
- A reproducible provisional offline evaluation now preserves baseline outputs, development-system outputs, field-level errors, split metrics and explicit denominators. On draft labels, the current pipeline scores 43/50 task types, 40/43 exact deadlines, 48/50 urgency labels, 45/50 calendar actions and 8/8 multi-email final states; these are not final report numbers.
- The Streamlit app now includes a human label-review workflow. It shows the source email, validates edited fields and verbatim evidence, tracks approval progress, and keeps the freeze command blocked until all 50 labels are explicitly approved.
- A gated final-evaluation runner now performs a safe preflight by default and refuses live calls until frozen labels, checksum and model configuration are present. Its execution mode preserves per-case outputs plus token and latency usage.
- A cost pipeline now compares on-demand, naive hourly, naive 15-minute and event-filtered polling. It currently reports `PENDING` rather than inventing a cost because live token usage and dated provider prices are not yet available.
- A visually verified three-page Word draft of the Business and Technical Trade Off Analysis now covers the problem, hybrid architecture, build-versus-buy decision, dataset counts, provisional component metrics, cost design, safety controls and limitations in 1,024 words. Final model and measured cost values remain explicitly pending.
- The live-model evaluation, token and cost analysis, independent real-email test set, remote GitHub repository, final report and final demo are still outstanding.

## Next milestone

Review and freeze the 50 draft labels. Then run a configured live model on the frozen cases and produce the cost comparison without tuning against the test or holdout splits.
