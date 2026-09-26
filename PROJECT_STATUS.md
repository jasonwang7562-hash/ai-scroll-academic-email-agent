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
- No AI Scroll application code, frozen dataset, completed evaluation, GitHub repository, or final demo was found in the inspected PE6201 folders on 26 September 2026.

## Next milestone

Build the smallest end-to-end path using manually uploaded email text before adding Gmail integration. A successful first slice accepts one email, returns structured JSON with evidence, creates a timeline item, and displays a calendar proposal without writing it.
