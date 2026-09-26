# AI Scroll Execution Plan to Submission

Official NTU Learn deadline: **4 October 2026, 23:59 SGT**  
Internal target: **3 October 2026, 22:00 SGT**  
Submission day is reserved for final checks and upload.

## Definition of done

The project is complete only when all of these are true:

- A user can import selected academic email text.
- The app returns course, task, normalized deadline, urgency and exact source evidence.
- Related emails can be merged, including a later deadline correction.
- Ambiguous or conflicting cases produce a clarification request.
- A calendar event is only written after explicit user confirmation.
- A frozen labelled dataset, rule baseline and repeatable scoring script are included.
- Six component metrics, abstention, token use, latency and cost are reported.
- The repository runs from a clean environment using its README.
- The trade-off analysis is at most 1,200 words.
- The video shows the product, one update chain, one abstention and the evaluation results.

## Scope lock

### Build now

1. Manual email text/file import.
2. Structured extraction with evidence.
3. Related-email grouping and update merging.
4. Deterministic urgency and date validation.
5. Clarification/abstention state.
6. Calendar preview and confirmation gate.
7. Baseline, evaluation and cost logging.

### Leave as future work

- Continuous Gmail monitoring.
- Multi-user accounts.
- General-purpose email question answering.
- Mobile application.
- Automatic calendar writes.
- Complex vector database infrastructure.

## Step 1 - Freeze the product contract

### Actions

1. Write one input and one output example.
2. Fix the JSON schema:
   - `email_id`
   - `thread_id`
   - `course`
   - `task_type`
   - `task_title`
   - `deadline_iso`
   - `timezone`
   - `urgency`
   - `evidence_quote`
   - `relation_to_previous`
   - `calendar_action`
   - `needs_clarification`
   - `clarification_reason`
3. Fix the urgency policy before model testing.
4. Decide that Singapore time is the default only when the email/course context supports it.

### Output

- `docs/product_contract.md`
- `schemas/extraction_schema.json`

### Completion check

Five sample emails can be labelled using the schema without changing any field names.

## Step 2 - Create the repository and runnable skeleton

### Actions

1. Create folders: `app`, `data`, `evaluation`, `tests`, `docs`, and `demo`.
2. Add `.gitignore` for `.env`, keys, raw private emails and Python cache files.
3. Add `requirements.txt` and `.env.example`.
4. Create a Streamlit page with email input, Run button and empty result panels.
5. Add a sample-data mode so the marker can run the project without private emails.

### Output

- Runnable `streamlit run app/main.py`
- Initial Git commit

### Completion check

The app starts on a clean terminal and displays a sample email without errors.

## Step 3 - Build the single-email extraction path

### Actions

1. Send one email and the fixed schema to the model.
2. Require structured JSON output.
3. Validate the response with Pydantic.
4. Normalize dates to ISO format.
5. Reject impossible dates and missing required evidence.
6. Display the result and evidence quote in Streamlit.
7. Log model ID, prompt version, tokens, latency and estimated cost.

### Output

- `app/extractor.py`
- `app/models.py`
- `app/date_validation.py`
- `logs/model_calls.csv`

### Completion check

Five different single emails run end to end and malformed model output does not crash the app.

## Step 4 - Build thread matching and update merging

### Actions

1. Use course name, assignment name, sender, subject and message time as matching signals.
2. Ask the model whether an email creates, updates, cancels or does not relate to an existing task.
3. Preserve every source message and evidence quote.
4. Apply the latest explicit correction to the timeline item.
5. Show old value, new value and update source in the interface.
6. Route unresolved contradictions to clarification.

### Output

- `app/thread_matcher.py`
- `app/merge_engine.py`
- At least eight labelled multi-email chains

### Completion check

The demo chain updates an earlier deadline without creating a duplicate task.

## Step 5 - Add urgency, abstention and the safety gate

### Actions

1. Calculate urgency in code using the frozen policy.
2. Add `needs_clarification` for missing date, unclear task, unresolved conflict or unsupported time zone.
3. Block calendar proposals when clarification is required.
4. Build calendar preview separately from calendar write.
5. Require a fresh explicit button click before every write.
6. Record approval status in an audit log.

### Output

- `app/urgency.py`
- `app/safety.py`
- `logs/calendar_actions.csv`

### Completion check

All automated tests show zero calendar writes before confirmation.

## Step 6 - Prepare and freeze the evaluation dataset

### Actions

1. Inventory exactly 50 emails and count genuine chains.
2. Include normal deadlines, corrections, cancellations, relative dates, missing times, conflicting messages and no-action announcements.
3. Create human labels before running the final model.
4. Give every case a stable `email_id` and `thread_id`.
5. Keep real private emails outside Git; publish anonymized or synthetic samples with a generation note.
6. Save a checksum or version tag so the final test set cannot silently change.

### Output

- `data/evaluation_emails.jsonl`
- `data/gold_labels.jsonl`
- `data/dataset_card.md`

### Completion check

Every email has course, task, deadline, urgency, evidence and expected calendar-action labels, including blank values where appropriate.

## Step 7 - Implement the rule baseline

### Actions

1. Detect course and action keywords.
2. Extract dates using a date parser.
3. Apply the same urgency rules as AI Scroll.
4. Do not give the baseline hidden access to gold labels.
5. Save baseline output in the same schema as the AI system.

### Output

- `evaluation/baseline.py`
- `evaluation/outputs/baseline.jsonl`

### Completion check

The baseline runs over all frozen cases with one command.

## Step 8 - Run evaluation and error analysis

### Actions

1. Freeze the prompt and record its version.
2. Run the baseline and AI Scroll on the same cases.
3. Calculate separate results for:
   - course identification;
   - task extraction;
   - deadline extraction;
   - urgency classification;
   - cross-email merging;
   - calendar proposal correctness.
4. Report counts before percentages.
5. Calculate high-priority deadline recall.
6. Report abstention rate and how many errors abstention prevented.
7. Confirm unauthorized writes equal zero.
8. Select at least one success, one error and one safe abstention for discussion.
9. Calculate cost per email, cost per thread and polling scenarios.

### Output

- `evaluation/score.py`
- `evaluation/results.csv`
- `evaluation/error_analysis.md`
- `evaluation/cost_analysis.csv`

### Completion check

One command regenerates every reported number from saved inputs and outputs.

## Step 9 - Write the 1,200-word analysis

### Structure

1. Problem and significance: about 140 words.
2. User and scope: about 100 words.
3. Why this hybrid design: about 220 words.
4. Build-versus-buy and cost: about 200 words.
5. Data and evaluation: about 240 words.
6. Risks and implemented controls: about 180 words.
7. Results, limitations and next step: about 120 words.

### Rules

- Write in first person.
- Use actual counts and costs.
- Name the baseline and exact model.
- Connect every risk to an implemented control.
- State limitations honestly.
- Keep the final body at or below 1,200 words.

### Output

- `report/AI_Scroll_Tradeoff_Analysis.docx`
- Final PDF copy if NTU Learn requests PDF

### Completion check

Every claim about performance can be traced to an evaluation file in the repository.

## Step 10 - Prepare the recorded demo

### Demo sequence

1. Introduce Jason and the problem.
2. Import a normal academic email.
3. Show structured output and exact evidence.
4. Import a later correction and show the merged deadline.
5. Show an ambiguous case that asks for clarification.
6. Show calendar preview, prove no write occurs, then approve one event.
7. Show the baseline comparison, six results and cost.
8. State one limitation and one next step.

### Output

- `demo/demo_script.docx`
- `demo/demo_inputs/`
- Recorded video and verified share link

### Completion check

The video contains no API keys, private addresses or identifiable email text, and the full frozen demo path works before recording.

## Step 11 - Repository and submission QA

### Actions

1. Clone or copy the repository into a clean directory.
2. Follow only the README to install and run it.
3. Confirm sample data works without access to private files.
4. Search the repository for API keys and email addresses.
5. Check every report number against the final result files.
6. Open the video link in a private/incognito window.
7. Confirm the repository is visible to the marker.
8. Upload before 21:00 SGT on 4 October.
9. Download the submitted files once and reopen them.
10. Save the NTU Learn receipt or confirmation screenshot.

## Daily schedule

### Saturday, 26 September - Scope and first running slice

- Freeze the product contract and JSON schema.
- Create the repository structure and Streamlit skeleton.
- Complete one-email extraction with evidence.
- Target: one input produces one validated output in the UI.

### Sunday, 27 September - Data and labels

- Keep this as a lighter workday if needed.
- Prepare the 50-email inventory and gold-label format.
- Label the first 15 cases and all multi-email chains.
- Target: dataset structure is frozen; no later schema redesign.

### Monday, 28 September - Complete extraction and validation

- Finish all 50 labels.
- Add date normalization, malformed-output handling and token logging.
- Target: all single-email cases run without crashing.

### Tuesday, 29 September - Cross-email intelligence

- Implement thread matching, merging, corrections and cancellations.
- Add the update-history view.
- Target: all genuine chains produce one correct final timeline item or clarification.

### Wednesday, 30 September - Safety and calendar

- Implement urgency rules, abstention and approval logging.
- Add Google Calendar integration or a fully working preview plus one tested write path.
- Target: zero unauthorized writes in tests.

### Thursday, 1 October - Baseline and final evaluation

- Run the rule baseline and frozen AI configuration.
- Generate six metrics, abstention, cost and error analysis.
- Target: all report numbers are generated automatically and saved.

### Friday, 2 October - Report and repository

- Write and edit the trade-off analysis.
- Complete README, setup instructions and dataset card.
- Test the repository from a clean folder.
- Target: report is at most 1,200 words and the repo runs from README alone.

### Saturday, 3 October - Video and final package

- Rehearse the frozen demo path.
- Record the video and verify its link.
- Perform secret scan and final repository cleanup.
- Target: every deliverable is complete by 22:00.

### Sunday, 4 October - Submission only

- Recheck repository URL and video access.
- Reopen the final report and verify the word count.
- Upload to `Assignments > Submission - Course Project` before 21:00.
- Download the submitted package and verify it.
- Save submission evidence.

## Stop conditions

If time becomes limited, preserve these in order:

1. Runnable end-to-end app.
2. Frozen evaluation and baseline comparison.
3. Evidence display and approval gate.
4. Accurate report.
5. Clear recorded demo.

Remove Gmail automation, interface decoration and extra chatbot features before cutting any item above.
