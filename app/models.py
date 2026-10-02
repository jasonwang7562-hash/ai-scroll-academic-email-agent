from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TaskType = Literal["assignment", "exam", "class_change", "administrative", "other"]
Urgency = Literal["high", "medium", "low", "clarification"]
Relation = Literal["new", "update", "cancel", "unrelated"]
CalendarAction = Literal["create", "update", "do_not_create", "ask_clarification"]


class EmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    sender: str = ""
    body: str = Field(min_length=1)
    sent_at: str | None = None


class ExtractedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_id: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)
    course: str = Field(min_length=1)
    task_type: TaskType
    task_title: str = Field(min_length=1)
    deadline_iso: str | None
    timezone: str = Field(min_length=1)
    urgency: Urgency
    evidence_quote: str
    relation_to_previous: Relation
    calendar_action: CalendarAction
    needs_clarification: bool
    clarification_reason: str | None
    source_subject: str

    @model_validator(mode="after")
    def validate_consistency(self) -> "ExtractedTask":
        if self.deadline_iso is not None:
            datetime.fromisoformat(self.deadline_iso)
        if self.needs_clarification:
            if self.urgency != "clarification":
                raise ValueError("Clarification cases must use clarification urgency")
            if self.calendar_action != "ask_clarification":
                raise ValueError("Clarification cases cannot propose a calendar write")
            if not self.clarification_reason:
                raise ValueError("Clarification reason is required")
        elif not self.evidence_quote:
            raise ValueError("A non-clarification result requires evidence")
        return self


class CalendarProposal(BaseModel):
    proposal_id: str = ""
    source_thread_id: str = ""
    title: str
    start: str
    end: str | None = None
    timezone: str
    description: str
    action: Literal["create", "update"] = "create"
    committed: bool = False


class CalendarWriteResult(BaseModel):
    event_id: str
    proposal_id: str
    status: Literal["committed", "deduplicated"]
    external_write: bool = False


class EvidenceRecord(BaseModel):
    email_id: str
    source_subject: str
    evidence_quote: str
    deadline_iso: str | None
    relation: Relation


class ChangeRecord(BaseModel):
    source_email_id: str
    field: str
    previous_value: str | None
    new_value: str | None
    reason: str


class TimelineItem(BaseModel):
    thread_id: str
    course: str
    task_type: TaskType
    task_title: str
    deadline_iso: str | None
    timezone: str
    urgency: Urgency
    status: Literal["active", "cancelled", "clarification"]
    calendar_action: CalendarAction
    needs_clarification: bool
    clarification_reason: str | None
    source_email_ids: list[str]
    evidence_history: list[EvidenceRecord]
    change_history: list[ChangeRecord]
