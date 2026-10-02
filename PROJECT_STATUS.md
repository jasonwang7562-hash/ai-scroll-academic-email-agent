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
- A competitor-informed UI revision now combines a proactive status brief, three-column academic inbox, evidence cards, timeline update view and explicit calendar-review flow. The design decisions are recorded in `docs/COMPETITOR_UI_DECISIONS.md`; extraction and safety behavior remain unchanged.
- A second competitor study added a daily focus banner, academic work-queue filters, source context, a visible capture-to-approval route and an explanatory merge flow. The adopted and rejected patterns are recorded in `docs/COMPETITOR_UI_ROUND_2.md`.
- A third competitor study strengthened trust and reviewability with a dynamic processing route, a human-readable decision statement, a four-check validation panel, scenario-specific calendar policy cards and a readable safety audit. The rationale is recorded in `docs/COMPETITOR_UI_ROUND_3.md`.
- A fourth competitor study added student-planner references and replaced the promotional dashboard header with a compact Today command center. The first screen now prioritizes the current review decision, next deadline, agent activity, course scope and safety state. The research and scope decisions are recorded in `docs/COMPETITOR_UI_ROUND_4.md`.
- A fifth visual pass replaced the card-heavy navy dashboard with a compact, light academic workspace inspired by Shortwave, Notion Calendar, MyStudyLife and Superhuman. The sidebar is now white, today's decision and agent state share one surface, summary data is one flat strip, navigation uses a restrained green underline, and contextual help remains available. The rationale is recorded in `docs/COMPETITOR_UI_ROUND_5.md`.
- The Today workspace now includes a first-run mailbox connection guide. Personal Outlook users see a four-step path from provider choice through Microsoft `Mail.Read` consent, connection verification and the first inbox scan; restricted school-tenant configuration is kept under an advanced option.
- Outlook authorization now uses a visible Microsoft device-code flow instead of relying on a hidden browser launch. The one-time code and Microsoft login link appear directly in the app.
- An optional real Google Calendar adapter is implemented behind the existing approval gate. It has a separate OAuth token, creates or updates only explicitly approved proposals, and uses a private proposal fingerprint to deduplicate retries. The simulated calendar remains the default.
- The submission UI now combines Shortwave's task-focused workspace, Notion Calendar's restrained layout and the original prototype's strongest element: one prominent blue-to-teal Today card. Demo mode is the reliable default, while real account connectors remain available for later integration. The rationale is recorded in `docs/COMPETITOR_UI_ROUND_6.md`.
- A backward-planning layer now converts a verified DDL into staged work sessions, keeps a configurable buffer, avoids existing calendar events and prepares deterministic proposals for review. The mailbox run also exposes a concise ReAct-style tool trace. Both the final DDL reminder and the generated study plan remain behind separate explicit approval controls.
- A bilingual four-step quick-start guide now tracks mailbox connection, inbox scanning, evidence review and calendar approval. It highlights the next action, uses Chinese/English labels on the main workflow and keeps plan generation as an explicit user step.
- Live model selection now applies to the full mailbox Agent pipeline rather than only the single-email screen. A bilingual local setup panel stores the OpenRouter key in the Git-ignored `.env`, defaults to `openai/gpt-5-mini`, and records current provider pricing for evaluation.
- Six additional synthetic tests derived from official Canvas, Google Classroom and NTU guidance now distinguish assessed due dates from availability windows and scheduled publication times. The research trail is recorded in `docs/WEB_RESEARCH_TESTS.md`.
- Calendar review now places the exact source evidence before approval, explains the simulated write and retry protection, and suppresses duplicate audit rows caused by Streamlit reruns.
- The Evaluation tab now presents the primary high-priority deadline metric, exact denominators, baseline deltas, split-specific results, current-pipeline error analysis and per-thread merge verification.
- The live-model evaluation, token and cost analysis, independent real-email test set, remote GitHub repository, final report and final demo are still outstanding.
- The app now has an Agent workspace that connects once, scans a mailbox, filters unrelated mail, consolidates course update chains and stops at human review before any calendar write. The bundled demo run scans five messages, keeps four academic messages, ignores one unrelated message and prepares two consolidated timeline items; real Gmail or Outlook access still requires OAuth setup and one user authorization.
- A real Gmail read-only connector and local OAuth authorization flow are implemented. Client secrets and refresh tokens stay in the ignored `data/private` directory. Google Cloud currently requires the selected account to enable two-step verification before an OAuth client can be created, so the live mailbox authorization is not complete yet.
- A parallel Outlook / Microsoft 365 connector now supports an NTU student mailbox through delegated Microsoft Graph `Mail.Read`. The Agent workspace includes local app-registration settings, interactive authorization and provider switching; an Entra application registration and student-account consent are still required before live scanning.
- NTU blocks both student-created Entra applications and unassigned Microsoft Graph Command Line Tools access. The Microsoft device-code flow was validated with delegated `Mail.Read`, but the browser selected accounts other than the intended mailbox. Those live credentials were removed, and the submission build therefore opens safely in Demo mode until the correct account is connected later.
- The Agent workspace now exposes a configurable course-code scope, filters out-of-scope mail before extraction, records a metadata-only process/ignore decision for every scanned message and reports run latency. Ignored message bodies remain outside the extraction pipeline, making the privacy boundary visible in the demo and auditable in evaluation.

## Next milestone

Review and freeze the 50 draft labels. Then run a configured live model on the frozen cases and produce the cost comparison without tuning against the test or holdout splits.
