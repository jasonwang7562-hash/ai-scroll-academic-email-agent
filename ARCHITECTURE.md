# System Architecture

## Main flow

`Selected emails -> metadata and keyword filter -> related-email retrieval -> LLM structured extraction -> deterministic validation -> thread merge -> timeline -> calendar proposal -> user confirmation -> Calendar API`

## What AI should do

- Understand varied academic language.
- Extract implicit tasks and evidence spans.
- Match messages that refer to the same assessment or event.
- Explain uncertainty in plain language.

## What rules should do

- Normalize dates and Singapore time.
- Reject impossible or incomplete dates.
- Apply the published urgency policy.
- Deduplicate identical events.
- Enforce the calendar confirmation gate.
- Log model calls, tokens, latency, and cost.

## Build and rent decisions

| Layer | Decision | Reason |
|---|---|---|
| Interface | Build a small local web app or CLI | Keeps the demo reproducible. |
| Workflow and merge logic | Build | This is the project-specific value. |
| Language model | Rent through a model API | Faster to deploy and compare. |
| Gmail access | Add after the manual-upload MVP | Avoids blocking the first working slice on OAuth. |
| Google Calendar | Rent the Calendar API | Commodity integration with explicit confirmation. |
| Evaluation and logging | Build | Needed for credible, repeatable evidence. |
