from __future__ import annotations

from copy import deepcopy

from app.extractor import extract
from app.models import ChangeRecord, EmailInput, EvidenceRecord, ExtractedTask, TimelineItem
from app.thread_matcher import best_match


def new_timeline_item(task: ExtractedTask) -> TimelineItem:
    status = "clarification" if task.needs_clarification else "cancelled" if task.relation_to_previous == "cancel" else "active"
    return TimelineItem(
        thread_id=task.thread_id,
        course=task.course,
        task_type=task.task_type,
        task_title=task.task_title,
        deadline_iso=task.deadline_iso,
        timezone=task.timezone,
        urgency=task.urgency,
        status=status,
        calendar_action=task.calendar_action,
        needs_clarification=task.needs_clarification,
        clarification_reason=task.clarification_reason,
        source_email_ids=[task.email_id],
        evidence_history=[EvidenceRecord(
            email_id=task.email_id,
            source_subject=task.source_subject,
            evidence_quote=task.evidence_quote,
            deadline_iso=task.deadline_iso,
            relation=task.relation_to_previous,
        )],
        change_history=[],
    )


def apply_update(item: TimelineItem, task: ExtractedTask) -> TimelineItem:
    result = deepcopy(item)
    result.source_email_ids.append(task.email_id)
    result.evidence_history.append(EvidenceRecord(
        email_id=task.email_id,
        source_subject=task.source_subject,
        evidence_quote=task.evidence_quote,
        deadline_iso=task.deadline_iso,
        relation=task.relation_to_previous,
    ))

    if task.relation_to_previous == "cancel":
        result.change_history.append(ChangeRecord(
            source_email_id=task.email_id,
            field="status",
            previous_value=result.status,
            new_value="cancelled",
            reason="A later email explicitly cancelled the event.",
        ))
        result.status = "cancelled"
        result.deadline_iso = None
        result.urgency = "low"
        result.calendar_action = "do_not_create"
        result.needs_clarification = False
        result.clarification_reason = None
        return result

    if task.deadline_iso and task.deadline_iso != result.deadline_iso:
        first_verified_deadline = result.deadline_iso is None
        result.change_history.append(ChangeRecord(
            source_email_id=task.email_id,
            field="deadline_iso",
            previous_value=result.deadline_iso,
            new_value=task.deadline_iso,
            reason="A later related email supplied a different explicit deadline.",
        ))
        result.deadline_iso = task.deadline_iso
        if first_verified_deadline:
            result.task_title = task.task_title
            result.task_type = task.task_type

    if task.needs_clarification:
        result.status = "clarification"
        result.calendar_action = "ask_clarification"
        result.needs_clarification = True
        result.clarification_reason = task.clarification_reason
        result.urgency = "clarification"
    else:
        result.status = "active"
        result.calendar_action = "update"
        result.needs_clarification = False
        result.clarification_reason = None
        result.urgency = task.urgency
    return result


def build_timeline(emails: list[EmailInput], now=None, mode: str = "Demo") -> list[TimelineItem]:
    ordered = sorted(emails, key=lambda email: email.sent_at or "")
    timeline: list[TimelineItem] = []
    for email in ordered:
        task = extract(email, mode=mode, now=now)
        index, _score = best_match(email, timeline)
        if index is None or (task.relation_to_previous == "new" and index is None):
            timeline.append(new_timeline_item(task))
        else:
            timeline[index] = apply_update(timeline[index], task)
    return timeline
