# Competitor UI study — round 3

Reviewed 28 September 2026 against the official product and help pages for Hiver, Gmelius, Canary Mail, SaneBox and Todoist.

## Focus of this round

Round one established a polished inbox workspace. Round two clarified queues and workflow. Round three focused on trust: how a user can understand the AI decision, verify the supporting information, and know whether an external action has happened.

| Product | Pattern observed | Decision for AI Scroll |
|---|---|---|
| Hiver | Triage, ownership and status remain visible throughout the request lifecycle | Make the four processing stages change state after analysis. |
| Gmelius | AI sorts first, then presents work for a fast human review | Put the final decision and the required review action directly above the preview. |
| Canary Mail | Privacy and processing boundaries are explained as product features | State that the source is traceable and the external calendar write remains locked. |
| SaneBox | AI-created drafts remain reviewable and are never sent automatically | Treat the calendar event as a proposal until explicit confirmation. |
| Todoist | Priority, labels and custom views reduce the time needed to find the next action | Keep the focused Deadline and Review queues introduced in round two. |

## Changes adopted

1. The processing route is now dynamic: before analysis, during clarification and after successful validation it shows different states.
2. Successful extraction includes a short human-readable decision statement.
3. A validation checklist shows four concrete guarantees: structured task, retained evidence, normalized time and locked calendar write.
4. The interface does not display an invented confidence percentage. Trust is based on inspectable checks and evidence.

## Scope control

Team assignment, automated replies, inbox migration and autonomous scheduling were rejected because they do not support the individual academic-deadline use case. This round changes explanation and presentation only; extraction, merge and approval policies remain unchanged.
