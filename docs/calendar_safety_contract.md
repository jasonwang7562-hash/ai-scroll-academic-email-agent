# Calendar Safety Contract - Version 1

## Separation of actions

AI Scroll treats these as three different operations:

1. Extract and validate a timeline item.
2. Prepare a calendar preview.
3. Commit the event only after a fresh explicit confirmation.

Preparing a preview never writes an event. Viewing an event does not count as confirmation.

## Write eligibility

A proposal is blocked when:

- the date, time, task or time zone requires clarification;
- the task was cancelled;
- there is no normalized deadline;
- the requested action is `do_not_create` or `ask_clarification`;
- the deadline is already in the past.

## Confirmation and deduplication

- Every write method requires `user_confirmed=True` from the confirmation control.
- Calling the write method without confirmation raises an error before the adapter is invoked.
- The proposal ID is a fingerprint of the thread, task, deadline and requested action.
- Repeating the same confirmed request returns `deduplicated` and does not create a second event.

## Current adapter

The current demo uses an in-memory calendar adapter and records no external event. The same gate will sit in front of the Google Calendar adapter in the later integration milestone.

