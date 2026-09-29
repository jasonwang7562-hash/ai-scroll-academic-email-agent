from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.merge_engine import build_timeline
from app.models import EmailInput, TimelineItem


COURSE_CODE = re.compile(r"\b[A-Z]{2,4}\d{4}[A-Z]?\b")


class MailboxConnector(Protocol):
    name: str

    def fetch_new(self) -> list[EmailInput]: ...


class DemoMailboxConnector:
    """Local mailbox used to demonstrate autonomous scanning without external access."""

    name = "Local demo mailbox"

    def fetch_new(self) -> list[EmailInput]:
        return [
            EmailInput(
                subject="PE6201 project deadline",
                sender="course-team@example.edu",
                body="The PE6201 project is due on 1 October 2026 at 11:59 PM SGT.",
                sent_at="2026-09-22T10:00:00+08:00",
            ),
            EmailInput(
                subject="PE6201 project deadline extended",
                sender="course-team@example.edu",
                body="The PE6201 project deadline has been extended to 4 October 2026 at 11:59 PM SGT.",
                sent_at="2026-09-25T10:00:00+08:00",
            ),
            EmailInput(
                subject="HR6102 research workshop",
                sender="programme-office@example.edu",
                body="The HR6102 research workshop is scheduled for 4 October 2026 at 10:00 AM SGT.",
                sent_at="2026-09-22T14:00:00+08:00",
            ),
            EmailInput(
                subject="HR6102 workshop cancelled",
                sender="programme-office@example.edu",
                body="The HR6102 research workshop on 4 October 2026 has been cancelled.",
                sent_at="2026-09-25T14:00:00+08:00",
            ),
            EmailInput(
                subject="Campus newsletter",
                sender="news@example.edu",
                body="This week's campus stories and dining updates are available now.",
                sent_at="2026-09-26T08:00:00+08:00",
            ),
        ]


@dataclass(frozen=True)
class AgentRunResult:
    connector: str
    scanned: int
    academic: int
    ignored: int
    review_required: int
    timeline: list[TimelineItem]


class InboxAgent:
    def __init__(self, connector: MailboxConnector):
        self.connector = connector

    def run(self, *, now: datetime | None = None) -> AgentRunResult:
        messages = self.connector.fetch_new()
        academic = [message for message in messages if self.is_academic(message)]
        timeline = build_timeline(academic, now=now)
        review_required = sum(
            item.calendar_action in {"create", "update", "ask_clarification"}
            for item in timeline
        )
        return AgentRunResult(
            connector=self.connector.name,
            scanned=len(messages),
            academic=len(academic),
            ignored=len(messages) - len(academic),
            review_required=review_required,
            timeline=timeline,
        )

    @staticmethod
    def is_academic(message: EmailInput) -> bool:
        return bool(COURSE_CODE.search(f"{message.subject}\n{message.body}"))
