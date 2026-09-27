from __future__ import annotations

import re

from app.models import EmailInput, TimelineItem


TOKEN_PATTERN = re.compile(r"[a-z]{3,}")
COURSE_PATTERN = re.compile(r"\b[a-z]{2,4}\d{4}[a-z]?\b", re.IGNORECASE)
STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "your", "will",
    "has", "have", "been", "please", "dear", "student", "regards", "course",
    "team", "deadline", "updated", "update", "reminder", "scheduled", "submit",
    "submission", "instead", "email", "remains", "now", "not", "through",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "sgt",
}


def keywords(text: str) -> set[str]:
    text = COURSE_PATTERN.sub(" ", text.lower())
    return {token for token in TOKEN_PATTERN.findall(text) if token not in STOPWORDS}


def match_score(email: EmailInput, item: TimelineItem) -> float:
    course_match = re.search(COURSE_PATTERN, f"{email.subject} {email.body}")
    if not course_match or course_match.group(0).upper() != item.course.upper():
        return 0.0
    incoming = keywords(f"{email.subject} {email.body}")
    existing = keywords(
        " ".join(
            [item.task_title]
            + [record.source_subject for record in item.evidence_history]
            + [record.evidence_quote for record in item.evidence_history]
        )
    )
    if not incoming or not existing:
        return 0.0
    overlap = len(incoming & existing) / min(len(incoming), len(existing))
    return round(overlap, 4)


def best_match(email: EmailInput, items: list[TimelineItem], threshold: float = 0.20):
    scored = [(match_score(email, item), index) for index, item in enumerate(items)]
    if not scored:
        return None, 0.0
    score, index = max(scored)
    return (index, score) if score >= threshold else (None, score)
