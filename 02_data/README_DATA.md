# Data Plan

Use 50 selected or synthetic academic emails only if all 50 can be reviewed and labelled before evaluation. Separate raw email count from evaluation-case count because several emails may form one thread.

## Required inventory

- Total emails.
- Independent emails.
- Multi-email threads.
- Emails inside those threads.
- Deadline corrections.
- Conflicting or ambiguous cases.
- Cases with no deadline.

## Privacy

Remove names, student identifiers, email addresses, links containing tokens, and unrelated personal content. Keep only the minimum text needed to reproduce the task. If real emails cannot be redistributed, publish a synthetic sample and the generation method in the repository.

## Split

- Development set: used while writing prompts.
- Frozen test set: labelled before the final run and not used to tune prompts.
- External or independently generated holdout: reduces the risk of grading cases designed by the same person who built the system.
