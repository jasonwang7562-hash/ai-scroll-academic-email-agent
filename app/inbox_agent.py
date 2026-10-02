from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
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
class ScanDecision:
    subject: str
    sender: str
    course_codes: tuple[str, ...]
    decision: str
    reason: str


@dataclass(frozen=True)
class AgentTraceStep:
    phase: str
    tool: str
    result: str


@dataclass(frozen=True)
class AgentRunResult:
    connector: str
    scanned: int
    academic: int
    ignored: int
    review_required: int
    timeline: list[TimelineItem]
    decisions: list[ScanDecision]
    trace: list[AgentTraceStep]
    duration_ms: int


class InboxAgent:
    def __init__(self, connector: MailboxConnector, *, allowed_courses: set[str] | None = None):
        self.connector = connector
        self.allowed_courses = {course.upper() for course in allowed_courses or set()}

    def run(self, *, now: datetime | None = None) -> AgentRunResult:
        started = perf_counter()
        messages = self.connector.fetch_new()
        decisions = [self.classify(message) for message in messages]
        academic = [
            message for message, decision in zip(messages, decisions)
            if decision.decision == "process"
        ]
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
            decisions=decisions,
            trace=[
                AgentTraceStep(
                    phase="Observe",
                    tool="mailbox.fetch_new",
                    result=f"Read {len(messages)} new messages from {self.connector.name}.",
                ),
                AgentTraceStep(
                    phase="Act",
                    tool="scan_policy.classify",
                    result=f"Kept {len(academic)} course messages and excluded {len(messages) - len(academic)} unrelated messages.",
                ),
                AgentTraceStep(
                    phase="Act",
                    tool="timeline.extract_and_merge",
                    result=f"Consolidated the retained mail into {len(timeline)} timeline items.",
                ),
                AgentTraceStep(
                    phase="Observe",
                    tool="calendar.approval_gate",
                    result=f"Stopped with {review_required} item(s) requiring human review before any write.",
                ),
            ],
            duration_ms=round((perf_counter() - started) * 1000),
        )

    def classify(self, message: EmailInput) -> ScanDecision:
        found = tuple(dict.fromkeys(
            match.upper() for match in COURSE_CODE.findall(f"{message.subject}\n{message.body}")
        ))
        if not found:
            return ScanDecision(
                subject=message.subject,
                sender=message.sender,
                course_codes=(),
                decision="ignore",
                reason="No course code detected",
            )
        if self.allowed_courses and not self.allowed_courses.intersection(found):
            return ScanDecision(
                subject=message.subject,
                sender=message.sender,
                course_codes=found,
                decision="ignore",
                reason="Outside configured course scope",
            )
        return ScanDecision(
            subject=message.subject,
            sender=message.sender,
            course_codes=found,
            decision="process",
            reason="Course code matched scan policy",
        )

    def is_academic(self, message: EmailInput) -> bool:
        return self.classify(message).decision == "process"
