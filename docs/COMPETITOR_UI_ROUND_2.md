# Competitor UI study — round 2

Reviewed 28 September 2026 against official product and help pages for Notion Mail, Jace AI, Front, Missive and Amie. Notion Mail is treated as a historical pattern because Notion announced the inbox product would close on 22 September 2026.

## What this round studied

The first round established the three-column inbox, evidence panel and approval gate. This round focused on the operating layer around those features: what needs attention now, how users filter work, how status remains visible, and how a message becomes a verified action.

| Product | Strong pattern | Fit for AI Scroll |
|---|---|---|
| Notion Mail | Custom views, filters, grouping and auto-labels | Compact view pills for all items, deadlines and items awaiting review. |
| Jace AI | Priority labels, rules and a review-before-send workflow | A daily focus banner and a short capture-to-approval route. |
| Front | Shared conversation context, live summaries and request status | Keep context and the source email beside the extracted result. |
| Missive | Tasks linked to conversations, visible status and grouping | Show each academic item as work with a clear state rather than as an isolated email. |
| Amie | A calm daily-planning surface that joins tasks and calendar | Present one useful daily focus instead of a dense analytics dashboard. |

## Changes adopted

1. A **Today’s focus** banner identifies the single item that needs attention.
2. **View pills** expose All, Deadlines and Review as the core academic work queues.
3. A **source context card** keeps origin and readiness visible above the selected email.
4. A four-step **Capture → Understand → Verify → Schedule** route makes the agent’s current state legible.
5. The cross-email screen now explains the merge as **original message → later correction → final timeline**.

## Deliberately excluded

- Team assignment and workload balancing from Front and Missive do not fit a single-student product.
- Autonomous replies and cross-app actions from Jace and Amie remain outside the project scope.
- AI confidence percentages are not displayed because the current extractor does not produce calibrated confidence scores.
- The system does not claim that a deadline is scheduled until the existing approval gate succeeds.

These choices improve navigation and explainability without changing extraction, merging, evaluation or calendar safety behavior.
