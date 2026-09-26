# AI Scroll

## What this project is

AI Scroll is an individual PE6201 End-of-Course Project. It turns selected academic emails into one evidence-backed course timeline. It extracts tasks and deadlines, merges updates across related emails, ranks urgency using a fixed human-defined policy, and prepares a Google Calendar event. The calendar is changed only after the user confirms the proposed event.

## The one-sentence project

Selected academic emails in; one verified course timeline and a confirmation-gated calendar proposal out.

## Current status

- Completed: Problem Statement and submission receipt.
- Completed: instructor feedback review and revision plan.
- Not yet completed: final dataset inventory and gold labels.
- Not yet completed: runnable MVP and GitHub repository.
- Not yet completed: baseline comparison and model evaluation.
- Not yet completed: final trade-off analysis and recorded demo.

## Recommended MVP

1. Upload or select emails from one course.
2. Group related messages into threads.
3. Extract course, task, deadline, urgency, and supporting evidence into JSON.
4. Merge later corrections into one timeline item while retaining the earlier source.
5. Show a proposed calendar event.
6. Require explicit confirmation before any calendar write.

## Keep out of the first version

- Continuous whole-inbox monitoring.
- Multiple users and production authentication.
- General question answering unrelated to the timeline.
- Automatic calendar writes without confirmation.

## Folder map

- `01_brief_and_feedback`: submitted problem statement, receipt, course guidance, and teacher feedback.
- `02_data`: case inventory, labels, privacy notes, and synthetic data generator if used.
- `03_app`: runnable application and setup instructions.
- `04_evaluation`: baseline, scoring code, raw outputs, results, and cost logs.
- `05_report`: final business and technical trade-off analysis.
- `06_demo`: slides, script, sample inputs, and video plan.
- `07_submission`: final checklist, repository URL, video URL, and submitted files.
- `99_archive`: superseded drafts only.
