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
