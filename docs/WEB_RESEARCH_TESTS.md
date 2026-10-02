# Web-researched academic workflow tests

The external scenarios are paraphrased synthetic emails. No student data or copied course email is included.

## Official references

- Google Classroom Help: assignment creation separates a scheduled publication time from an optional due date.  
  https://support.google.com/edu/classroom/answer/6020265
- Google Classroom Help: only classwork with a due date appears in Classroom and Google calendars, while students can add separate study sessions.  
  https://support.google.com/edu/classroom/answer/6272985
- Canvas Student Guide: a due date and an availability window have different meanings.  
  https://community.canvaslms.com/html/assets/Canvas_Student_Guide.pdf
- Canvas Observer Guide: due dates normally include a due time; availability can extend beyond the assessed due date.  
  https://community.canvaslms.com/html/assets/Canvas_Observer_Guide.pdf
- NTU MAE student announcement: registration periods have explicit closing dates and times.  
  https://www.ntu.edu.sg/mae/admissions/current-students/graduate-studies/announcement

## Product findings

The new cases exposed two unsafe shortcuts and now guard against both:

1. An `available until` date is not automatically treated as the assessed DDL.
2. A scheduled Classroom publication time is not treated as the assignment DDL.

The suite also verifies explicit assignment due dates, NTU registration closing times and clarification when a due time is missing.

## Live model result (3 October 2026)

`openai/gpt-5-mini` through OpenRouter passed all 6/6 sourced scenarios after the safety rules above were applied. The run used 3,879 prompt tokens and 4,886 completion tokens, with an estimated API cost of USD 0.01074 at the configured prices (USD 0.25/M input and USD 2.00/M output). The machine-readable record is in `04_evaluation/outputs/web_live_model_results.json`.

An end-to-end mailbox smoke run then scanned five messages, excluded one unrelated newsletter and consolidated four course messages into two timeline items. It correctly updated the PE6201 deadline, cancelled the HR6102 workshop and stopped one remaining action at the human approval gate. No external calendar write was performed.
