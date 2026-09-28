from __future__ import annotations

import hashlib
from datetime import datetime

from app.models import CalendarProposal, CalendarWriteResult, TimelineItem


class CalendarPolicyError(ValueError):
    """Raised when a timeline item is not safe enough for a calendar proposal."""


class ApprovalRequiredError(PermissionError):
    """Raised when code attempts a write without explicit user confirmation."""


class InMemoryCalendarStore:
    """A safe demo adapter. It never contacts an external calendar."""

    def __init__(self, events: dict[str, dict] | None = None):
        self.events = events if events is not None else {}

    def create_or_update(self, proposal: CalendarProposal) -> CalendarWriteResult:
        if proposal.proposal_id in self.events:
            return CalendarWriteResult(
                event_id=self.events[proposal.proposal_id]["event_id"],
                proposal_id=proposal.proposal_id,
                status="deduplicated",
            )
        event_id = f"demo_event_{len(self.events) + 1:03d}"
        record = proposal.model_dump()
        record.update({"event_id": event_id, "committed": True})
        self.events[proposal.proposal_id] = record
        return CalendarWriteResult(
            event_id=event_id,
            proposal_id=proposal.proposal_id,
            status="committed",
        )


class CalendarApprovalGate:
    def __init__(self, store: InMemoryCalendarStore | None = None, audit: list[dict] | None = None):
        self.store = store or InMemoryCalendarStore()
        self.audit = audit if audit is not None else []

    def preview(self, item: TimelineItem, now: datetime | None = None) -> CalendarProposal:
        reason = self._blocked_reason(item, now=now)
        if reason:
            self._append_audit_once({"action": "preview", "status": "blocked_unsafe", "reason": reason})
            raise CalendarPolicyError(reason)

        evidence = "\n".join(
            f"- {record.source_subject}: {record.evidence_quote}"
            for record in item.evidence_history
        )
        fingerprint = "|".join(
            [item.thread_id, item.course, item.task_title, item.deadline_iso or "", item.calendar_action]
        )
        proposal_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
        proposal = CalendarProposal(
            proposal_id=proposal_id,
            source_thread_id=item.thread_id,
            title=f"{item.course} - {item.task_title}",
            start=item.deadline_iso,
            timezone=item.timezone,
            description=f"AI Scroll evidence:\n{evidence}",
            action="update" if item.calendar_action == "update" else "create",
        )
        self._append_audit_once({"action": "preview", "status": "prepared", "proposal_id": proposal_id})
        return proposal

    def commit(self, proposal: CalendarProposal, *, user_confirmed: bool) -> CalendarWriteResult:
        if not user_confirmed:
            self.audit.append({
                "action": "write", "status": "blocked_unconfirmed", "proposal_id": proposal.proposal_id
            })
            raise ApprovalRequiredError("Explicit user confirmation is required before every calendar write.")
        result = self.store.create_or_update(proposal)
        self.audit.append({
            "action": "write", "status": result.status,
            "proposal_id": proposal.proposal_id, "event_id": result.event_id,
        })
        return result

    def _append_audit_once(self, entry: dict) -> None:
        """Avoid repeated audit rows caused by harmless Streamlit reruns."""
        if entry not in self.audit:
            self.audit.append(entry)

    @staticmethod
    def _blocked_reason(item: TimelineItem, now: datetime | None = None) -> str | None:
        if item.needs_clarification or item.status == "clarification":
            return item.clarification_reason or "The task requires clarification."
        if item.status == "cancelled":
            return "Cancelled tasks cannot create or update a calendar event."
        if item.calendar_action not in {"create", "update"}:
            return f"Calendar action '{item.calendar_action}' is not eligible for a write."
        if not item.deadline_iso:
            return "A verified deadline is required for a calendar proposal."
        deadline = datetime.fromisoformat(item.deadline_iso)
        if now is not None:
            comparison_now = now if now.tzinfo else now.replace(tzinfo=deadline.tzinfo)
            if deadline <= comparison_now:
                return "The deadline is already in the past."
        return None
