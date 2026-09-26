# Application Build Order

## Version 0.1

- Input: one pasted academic email.
- Output: structured JSON containing course, task, deadline, urgency, evidence, and confidence.
- Validation: deterministic date and timezone checks.

## Version 0.2

- Input: several emails from one course.
- Add thread grouping and latest-instruction merge logic.
- Keep every source and show which message changed the final timeline item.

## Version 0.3

- Add a timeline view and calendar-event preview.
- Add explicit approve, reject, and edit actions.
- Use a mock calendar writer first; connect the real Calendar API only after the gate is tested.

## Version 0.4

- Add Gmail label import, observability, token and cost logging, and a repeatable evaluation command.

## Definition of done

A new reviewer can clone the GitHub repository, install dependencies, use a sample environment file, run the app, run tests, and reproduce the reported metrics without access to private emails.
