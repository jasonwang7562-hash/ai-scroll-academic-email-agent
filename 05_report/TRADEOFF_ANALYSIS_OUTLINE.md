# Business and Technical Trade-off Analysis Outline

Target length: no more than 1,200 words.

## 1 Problem and significance

Define one student persona, quantify the email and deadline-management problem, name the closest existing alternative, and state what remains out of scope.

## 2 Design choice

Explain why a hybrid system is appropriate: a foundation model for language understanding, retrieval for related messages, and deterministic rules for dates, labels, deduplication, and approval.

## 3 Build versus buy

State which layers are built and rented. Include time-to-deploy, privacy, portability, latency, and cost per use.

## 4 Data and evaluation

Give exact counts for emails and threads. Explain the frozen gold labels, baseline, component metrics, abstention, and error analysis. Report counts before percentages.

## 5 Risks and mitigations

Pair each risk with an implemented control: privacy minimization, evidence display, confidence or abstention, timezone validation, deduplication, rate limits, and explicit calendar confirmation.

## 6 Results and limitations

Report actual baseline and model results, cost, and failure examples. State what the small dataset and synthetic cases cannot prove.
