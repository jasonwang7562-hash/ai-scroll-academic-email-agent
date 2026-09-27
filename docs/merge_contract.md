# Cross-email Merge Contract - Version 1

## Goal

Related emails about one academic task become one timeline item while every source and change remains auditable.

## Matching signals

1. The course code must match.
2. Subject and body keywords are compared after removing dates, course codes and common email words.
3. A minimum overlap score is required. A low score creates a separate task.
4. A later message marked as an update or cancellation can modify only the best matching task.

## Merge precedence

- Messages are processed in sent-time order.
- A later explicit deadline replaces an earlier deadline.
- A reminder with the same deadline adds evidence without creating a duplicate.
- A cancellation changes status to cancelled and blocks calendar creation.
- An unresolved later message changes status to clarification and blocks calendar creation.

## Audit requirements

The merged item retains all source email IDs, all evidence quotes and a field-level change history containing the old value, new value and reason.

## Acceptance cases

1. `c01`: two PE6201 emails become one item and the deadline changes from 1 October to 4 October.
2. `c04`: the later cancellation produces one cancelled item with no calendar action.
3. Two unrelated tasks from the same course remain two timeline items.

