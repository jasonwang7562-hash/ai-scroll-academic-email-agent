# Competitor UI decisions

Reviewed 28 September 2026 against the public product pages for Gemini in Gmail, Shortwave, Spark, Superhuman Mail, Fyxer, Lindy, Mailbutler, Akiflow, Sunsama, Reclaim and Motion.

## Patterns selected for this milestone

| Reference | Pattern adopted | AI Scroll implementation |
|---|---|---|
| Fyxer | Proactive priority summary | A top status strip surfaces selected mail, update chains, evaluation cases and unauthorized writes. |
| Gemini in Gmail / Spark | Mail and assistant remain visible together | The Academic inbox uses a three-column course rail, source email and AI details layout. |
| Superhuman | Focused inbox categories | Course updates, needs-review state and compact status badges separate different kinds of attention. |
| Mailbutler | One clear extraction action | The primary action is named `Analyze email`, and the result is split into task, evidence and calendar preview. |
| Reclaim | Calendar preview before scheduling | Extracted deadlines are presented as a reviewable calendar card rather than an immediate write. |
| Lindy | Human-in-the-loop execution | Calendar actions remain behind the existing explicit approval gate. |

## Deliberately deferred

- Automatic rescheduling from Motion and Reclaim: outside the evidence-first scope of the current assignment.
- Autonomous sending from Lindy and Fyxer: unnecessary for an academic deadline assistant and increases safety risk.
- Full keyboard command system from Superhuman: valuable after the core workflow is stable.
- Daily timeboxing from Sunsama: a possible later layer after extraction and cross-email merging are validated.

## Resulting product hierarchy

1. Show what needs attention.
2. Keep the source email visible.
3. Present a structured task and exact evidence.
4. Show the proposed calendar result.
5. Require explicit confirmation before any write.

The redesign changes presentation only. Extraction, merge, evaluation and calendar-safety behavior remain unchanged.
