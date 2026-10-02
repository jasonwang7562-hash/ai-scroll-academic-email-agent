# Competitor UI study — round 4

Reviewed 2 October 2026. This round combines student-built planners, established student products, AI email clients and AI scheduling products. It focuses on what the user should see in the first five seconds of opening AI Scroll.

## Reference set

### Student and academic products

| Product | Reference | Useful interface pattern |
|---|---|---|
| MyStudyLife | https://mystudylife.com/tour/ | A day-first dashboard: next class, due work and the academic calendar are visible before settings or analytics. Course colour and short labels make dense information scannable. |
| Shovel | https://shovelapp.io/mobile/ | Treats assignments as scheduled workload rather than a flat checklist. Dates, task state and course context remain together. |
| Study Planner | https://github.com/eaddodankwhak/Study-Planner | Student-built example with onboarding, subject cards, upcoming deadlines and tasks in one dashboard. It shows the value of a clear empty state before data exists. |
| StudyFlow | https://github.com/Dilhara-De-Alwis/StudyFlow | Strong visual personality, responsive cards and useful countdowns. Its many gamification elements would distract from AI Scroll's evidence-first purpose, so only its hierarchy and responsive card rhythm are relevant. |
| Smart Student Planner | https://github.com/shaakir30/Smart-Student-Planner | Academic progress and overdue counts are visible at dashboard level, with filters for today, this week and priority. |
| Slate student dashboard | https://github.com/matthewgwang/class-organization-web-app | Calendar and Kanban views provide different representations of the same academic work instead of duplicating data. |

### AI email and planning products

| Product | Reference | Useful interface pattern |
|---|---|---|
| Superhuman Mail | https://superhuman.com/agents/email-assistant | Proactive labels show what requires attention before a message is opened. AI assistance stays inside the existing inbox workflow. |
| Shortwave | https://www.shortwave.com/docs/guides/ai-assistant/ | Keeps source mail, AI output and the next action in one context. Natural-language assistance does not replace the inbox itself. |
| Reclaim 2.0 | https://help.reclaim.ai/en/articles/14846468-reclaim-ai-2-0-overview | The assistant acts as a control center, surfaces the highest-impact issue and stages changes in Preview Mode before applying them. |
| Reclaim Planner | https://help.reclaim.ai/en/articles/6206998-planner-overview-view-and-manage-your-schedule | A contextual details pane appears only after an item is selected. Priorities and actions remain close to the schedule. |
| Akiflow | https://akiflow.com/ | Combines inbox, tasks and calendar in one flow. The Today view and short time labels reduce planning friction. |
| Sunsama | https://help.sunsama.com/docs/usage-guides/sunny/ | Uses a calm daily-planning ritual and a small number of guided actions instead of a dense dashboard. |

## Shared design principles

1. **Start with today.** The first screen answers what needs attention now and what is due next.
2. **Use progressive disclosure.** The overview stays compact; source evidence, audit detail and configuration appear when requested.
3. **Show state, not marketing copy.** Connection, scan progress, review count and next deadline are more useful than a large product slogan.
4. **Keep one dominant action.** The current decision should be obvious: connect, scan or review.
5. **Keep source and action traceable.** AI output must retain its course, source email and evidence before the user approves a calendar change.
6. **Separate prepared work from completed work.** A proposal waiting for review must never look scheduled.
7. **Prefer calm density.** Compact cards, restrained colour and clear labels beat decorative charts for this use case.
8. **Explain unfamiliar automation in place.** Short labels stay readable while contextual help and a short guided workflow remain one click away.

## Patterns adopted in AI Scroll

- Replace the oversized promotional hero with a compact academic command center.
- Make **Today** the first tab and shorten navigation labels.
- Add one dominant focus card for the current decision.
- Put agent activity beside the focus card: scanned mail, prepared items and review count.
- Keep a permanent zero-unauthorized-write indicator in the primary view.
- Add a compact strip for the next deadline, course scope and review queue.
- Add a persistent question-mark help entry, a four-step quick-start guide and contextual tooltips for evidence, agent activity and the review queue.
- Preserve the existing evidence, merge history and approval controls in their detailed views.

## Patterns deliberately excluded

- Gamification, streaks, virtual pets and GPA charts do not support the assessed email-to-calendar workflow.
- Automatic rescheduling is outside the frozen project scope.
- Chat is not the homepage because the core value is proactive inbox processing rather than another general prompt box.
- Confidence percentages remain excluded until a calibrated confidence measure exists.
