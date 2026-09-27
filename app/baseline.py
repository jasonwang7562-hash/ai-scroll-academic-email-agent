from __future__ import annotations

import re
from datetime import datetime

from app.date_validation import parse_deadline, urgency_for
from app.models import EmailInput


COURSE_PATTERN = re.compile(r"\b[A-Z]{2,4}\d{4}[A-Z]?\b")
ACTION_PATTERN = re.compile(
    r"\b(due|deadline|submit|upload|complete|exam|quiz|presentation|"
    r"consultation|workshop|briefing|registration|form|scheduled|begins|opens?)\b",
    re.IGNORECASE,
)


def _task_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("assignment", "project", "report", "submission")):
        return "assignment"
    if any(term in lowered for term in ("exam", "quiz", "test")):
        return "exam"
    if any(term in lowered for term in ("class moved", "class cancelled", "room changed")):
        return "class_change"
    if any(term in lowered for term in ("registration", "form", "declaration")):
        return "administrative"
    return "other"


def baseline_extract(email: EmailInput, now: datetime) -> dict:
    """A deliberately small keyword/date baseline with no thread memory."""
    text = f"{email.subject}\n{email.body}"
    course_match = COURSE_PATTERN.search(text)
    deadline, clarification = parse_deadline(email.body)
    has_action = bool(ACTION_PATTERN.search(text))
    cancelled = bool(re.search(r"\bcancell?ed\b", text, re.IGNORECASE))

    if cancelled or not has_action:
        deadline = None
        clarification = None
        urgency = "low"
        calendar_action = "do_not_create"
    elif clarification:
        urgency = "clarification"
        calendar_action = "ask_clarification"
    else:
        urgency = urgency_for(deadline, text, now=now)
        calendar_action = "create"

    return {
        "course": course_match.group(0) if course_match else "Unknown course",
        "task_type": _task_type(text),
        "deadline_iso": deadline,
        "urgency": urgency,
        "calendar_action": calendar_action,
        "needs_clarification": bool(clarification),
        "relation_to_previous": "new",
    }
