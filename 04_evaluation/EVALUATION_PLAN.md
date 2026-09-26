# Evaluation Plan

## Primary value metric

High-priority deadline recall: correctly captured human-labelled high-priority deadline cases divided by all human-labelled high-priority deadline cases. Report the count as `x/N` and the percentage. The label must be frozen before running the model.

## Baseline

Implement a deterministic baseline using sender or course keywords, deadline keywords, and a date parser. Compare the AI system with this baseline on the same frozen cases.

## Component metrics

1. Course identification: correct / labelled emails.
2. Task extraction: correct, missed, and extra tasks.
3. Deadline extraction: exact normalized deadline / deadline-bearing cases; false deadlines separately.
4. Urgency classification: correct / labelled cases plus confusion counts.
5. Cross-email merging: correctly merged threads / genuine multi-email threads.
6. Calendar proposal: correct proposals / eligible cases; unauthorized writes must equal zero.

## Abstention

Report how often the system asks for clarification and how many of those cases would otherwise have been wrong. A system that abstains on every case is safe but unusable, so record both abstention rate and error-capture rate.

## Cost

Record model, price date, input tokens, output tokens, latency, and cost for every call. Report average cost per email, average and maximum cost per thread, and monthly estimates for on-demand, hourly, and 15-minute polling.

## Evidence to preserve

- Frozen input cases and labels.
- Baseline outputs.
- Model outputs.
- Scoring script.
- Error analysis.
- Token and cost log.
- Exact model ID, prompt version, and run date.
