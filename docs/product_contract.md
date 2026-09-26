# AI Scroll Product Contract - Version 1

## Product statement

Selected academic email in; one validated, evidence-backed timeline item and an uncommitted calendar proposal out.

## Primary user

Jason is a university student managing several courses through email. He needs to see what action is required, when it is due and which sentence supports the result before accepting a calendar entry.

## Input

Version 1 accepts one manually pasted academic email containing a subject, sender and body. It does not connect to a live inbox.

## Output

The output follows `schemas/extraction_schema.json` and includes:

- stable email and thread identifiers;
- course;
- task type and title;
- ISO 8601 deadline and time zone;
- urgency;
- an exact quote copied from the email;
- relationship to an earlier message;
- proposed calendar action;
- clarification status and reason.

## Fixed urgency policy

Urgency is calculated by code after extraction:

- High: the deadline is within 72 hours, or the email explicitly says urgent/mandatory.
- Medium: the deadline is more than 72 hours and within 7 days.
- Low: the deadline is more than 7 days away.
- Clarification: the date, time, task or time zone is too ambiguous for a safe calendar proposal.

The final evaluation uses a frozen reference time for reproducibility.

## Safety rules

1. The evidence quote must appear verbatim in the source email.
2. Missing or ambiguous date/time information triggers clarification.
3. Calendar preview and calendar write are separate actions.
4. Version 1 never writes to a calendar.
5. API keys and private emails must not be saved in the repository.

## Explicitly out of scope for Version 1

- Gmail or Outlook monitoring.
- Cross-email merging.
- Automatic calendar writes.
- General email question answering.
- Multiple users and production authentication.

Cross-email merging and the confirmation-gated Calendar API are the next milestones after this contract passes the smoke test.

## Version 1 acceptance test

Given the included PE6201 sample email, the app must return course `PE6201`, task type `assignment`, deadline `2026-10-04T23:59:00+08:00`, a verbatim evidence sentence and a calendar preview. No external account may be changed.

