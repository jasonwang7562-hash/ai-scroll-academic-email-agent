from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil import parser


SINGAPORE = ZoneInfo("Asia/Singapore")
DATE_PATTERN = re.compile(
    r"\b(?:by\s+)?(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
    r"(?:\s+at\s+(\d{1,2}:\d{2}\s*(?:AM|PM)))?\s*(SGT|Singapore time)?",
    re.IGNORECASE,
)

MONTH_FIRST_PATTERN = re.compile(
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*,?\s*"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?"
    r"\s*,?\s*(\d{1,2}:\d{2})(?:\s*(AM|PM))?\s*(?:hrs?)?\s*"
    r"(SGT|Singapore time)\b",
    re.IGNORECASE,
)


def parse_deadline(text: str, reference: datetime | None = None) -> tuple[str | None, str | None]:
    """Return an ISO deadline and a clarification reason, if any."""
    match = DATE_PATTERN.search(text)
    if not match:
        month_first = MONTH_FIRST_PATTERN.search(text)
        if not month_first:
            return None, "No explicit calendar date was found."
        month, day, year, clock, meridiem, _timezone = month_first.groups()
        reference = reference or datetime.now(SINGAPORE)
        resolved_year = int(year) if year else reference.year
        parsed = parser.parse(
            f"{day} {month} {resolved_year} {clock}{(' ' + meridiem) if meridiem else ''}",
            dayfirst=True,
        )
        localized = parsed.replace(tzinfo=SINGAPORE)
        return localized.isoformat(), None
    date_part, time_part, timezone_part = match.groups()
    if not time_part:
        return None, "A date was found, but the deadline time is missing."
    if not timezone_part:
        return None, "A date and time were found, but the time zone is missing."

    parsed = parser.parse(f"{date_part} {time_part}", dayfirst=True)
    localized = parsed.replace(tzinfo=SINGAPORE)
    return localized.isoformat(), None


def urgency_for(
    deadline_iso: str,
    source_text: str,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(SINGAPORE)
    if now.tzinfo is None:
        now = now.replace(tzinfo=SINGAPORE)
    deadline = datetime.fromisoformat(deadline_iso)
    hours = (deadline - now).total_seconds() / 3600
    if re.search(r"\b(urgent|mandatory)\b", source_text, re.IGNORECASE):
        return "high"
    if hours <= 72:
        return "high"
    if hours <= 7 * 24:
        return "medium"
    return "low"
