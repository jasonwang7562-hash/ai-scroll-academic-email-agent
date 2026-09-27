# Provisional Offline Evaluation

> **NOT FINAL:** every gold label is still pending human review. The 50 emails are synthetic, and no live language model was run.

Reference time: `2026-09-26T12:00:00+08:00`. Population: 50 emails, 38 threads, including 8 multi-email threads.

| Metric | Keyword/date baseline | Current deterministic pipeline |
|---|---:|---:|
| Course identification | 50/50 (100.0%) | 50/50 (100.0%) |
| Task type | 28/50 (56.0%) | 43/50 (86.0%) |
| Exact deadline | 32/43 (74.4%) | 40/43 (93.0%) |
| Urgency | 41/50 (82.0%) | 48/50 (96.0%) |
| Calendar action | 28/50 (56.0%) | 45/50 (90.0%) |
| Clarification recall | 0/3 (0.0%) | 3/3 (100.0%) |
| Cross-email merge | 0/8 (0.0%) | 8/8 (100.0%) |

The current pipeline is stronger on the draft labels, especially for thread updates and calendar decisions. These numbers are evidence for debugging only until Jason reviews and freezes the labels. A live model run, token/cost log, and independent real-email test set are still required for the final submission.

Detailed outputs: `outputs/development_metrics.json`, `outputs/development_errors.csv`, `outputs/baseline_outputs.jsonl`, and `outputs/dev_system_outputs.jsonl`.
