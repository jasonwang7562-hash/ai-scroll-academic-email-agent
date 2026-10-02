from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from app.models import CalendarProposal, TimelineItem


class PlanningError(ValueError):
    """Raised when a safe plan cannot fit before the deadline."""


@dataclass(frozen=True)
class BusyWindow:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class PlanMilestone:
    title: str
    start: datetime
    end: datetime
    purpose: str


@dataclass(frozen=True)
class BackwardPlan:
    deadline: datetime
    estimated_hours: float
    buffer_hours: float
    milestones: tuple[PlanMilestone, ...]


STAGES = {
    "assignment": (
        ("Understand the brief", 0.10, "Confirm the deliverables, rubric and source requirements."),
        ("Research and outline", 0.25, "Collect evidence and decide the structure."),
        ("Build the first draft", 0.40, "Complete the main written or technical work."),
        ("Revise and verify", 0.18, "Check correctness, evidence and presentation quality."),
        ("Final submission check", 0.07, "Export, name and verify every submission file."),
    ),
    "exam": (
        ("Map the syllabus", 0.10, "Identify examinable topics and weak areas."),
        ("Review core material", 0.35, "Revisit notes and required readings."),
        ("Practice questions", 0.35, "Complete timed or representative questions."),
        ("Fix weak areas", 0.15, "Review errors and repeat difficult topics."),
        ("Final review", 0.05, "Prepare a concise final revision pass."),
    ),
}


def suggested_effort_hours(item: TimelineItem) -> float:
    return {
        "assignment": 8.0,
        "exam": 10.0,
        "administrative": 1.0,
        "class_change": 0.5,
        "other": 3.0,
    }[item.task_type]


def _overlaps(start: datetime, end: datetime, busy: BusyWindow) -> bool:
    return start < busy.end and end > busy.start


def _latest_slot(
    cursor: datetime,
    duration: timedelta,
    busy: list[BusyWindow],
    earliest: datetime,
) -> tuple[datetime, datetime] | None:
    day = cursor.date()
    while day >= earliest.date():
        # A wide but humane study window. Existing calendar events are removed below.
        window_start = datetime.combine(day, time(8, 0), tzinfo=cursor.tzinfo)
        window_end = datetime.combine(day, time(22, 0), tzinfo=cursor.tzinfo)
        candidate_end = min(cursor, window_end)
        candidate_start = candidate_end - duration
        while candidate_start >= max(window_start, earliest):
            conflict = next(
                (entry for entry in sorted(busy, key=lambda value: value.start, reverse=True)
                 if _overlaps(candidate_start, candidate_end, entry)),
                None,
            )
            if conflict is None:
                return candidate_start, candidate_end
            candidate_end = min(candidate_end, conflict.start)
            candidate_start = candidate_end - duration
        day -= timedelta(days=1)
        cursor = datetime.combine(day, time(22, 0), tzinfo=cursor.tzinfo)
    return None


def build_backward_plan(
    item: TimelineItem,
    *,
    now: datetime,
    estimated_hours: float | None = None,
    buffer_hours: float = 4.0,
    busy: list[BusyWindow] | None = None,
) -> BackwardPlan:
    if item.status != "active" or item.needs_clarification or not item.deadline_iso:
        raise PlanningError("A verified active deadline is required before planning.")
    deadline = datetime.fromisoformat(item.deadline_iso)
    if now.tzinfo is None:
        now = now.replace(tzinfo=deadline.tzinfo)
    else:
        now = now.astimezone(deadline.tzinfo)
    effort = estimated_hours if estimated_hours is not None else suggested_effort_hours(item)
    if effort <= 0 or buffer_hours < 0:
        raise PlanningError("Estimated work and buffer must be positive.")
    cursor = deadline - timedelta(hours=buffer_hours)
    if cursor <= now:
        raise PlanningError("The selected buffer leaves no working time before the deadline.")

    stages = STAGES.get(item.task_type, STAGES["assignment"][:3])
    weights = sum(weight for _, weight, _ in stages)
    scheduled: list[PlanMilestone] = []
    occupied = list(busy or [])
    for title, weight, purpose in reversed(stages):
        hours = max(0.5, round((effort * weight / weights) * 2) / 2)
        slot = _latest_slot(cursor, timedelta(hours=hours), occupied, now)
        if slot is None:
            raise PlanningError(
                "The work estimate does not fit before the deadline. Reduce the hours or buffer, or free calendar time."
            )
        start, end = slot
        scheduled.append(PlanMilestone(title=title, start=start, end=end, purpose=purpose))
        occupied.append(BusyWindow(start=start, end=end))
        cursor = start
    scheduled.reverse()
    return BackwardPlan(
        deadline=deadline,
        estimated_hours=effort,
        buffer_hours=buffer_hours,
        milestones=tuple(scheduled),
    )


def milestone_proposal(item: TimelineItem, milestone: PlanMilestone) -> CalendarProposal:
    fingerprint = "|".join(
        [item.thread_id, milestone.title, milestone.start.isoformat(), milestone.end.isoformat()]
    )
    return CalendarProposal(
        proposal_id=hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16],
        source_thread_id=item.thread_id,
        title=f"{item.course} · {milestone.title}",
        start=milestone.start.isoformat(),
        end=milestone.end.isoformat(),
        timezone=item.timezone,
        description=(
            f"AI Scroll backward plan for: {item.task_title}\n"
            f"Purpose: {milestone.purpose}\n"
            f"Final deadline: {item.deadline_iso}"
        ),
        action="create",
    )
