from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.calendar_gate import (
    ApprovalRequiredError,
    CalendarApprovalGate,
    CalendarPolicyError,
    InMemoryCalendarStore,
)
from app.merge_engine import build_timeline
from app.models import EmailInput


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def active_item():
    return build_timeline([EmailInput(
        subject="PE6201 project deadline",
        body="The PE6201 project is due on 4 October 2026 at 11:59 PM SGT.",
    )], now=NOW)[0]


def test_unconfirmed_write_is_blocked_before_store():
    store = InMemoryCalendarStore()
    gate = CalendarApprovalGate(store=store)
    proposal = gate.preview(active_item(), now=NOW)
    with pytest.raises(ApprovalRequiredError):
        gate.commit(proposal, user_confirmed=False)
    assert store.events == {}
    assert gate.audit[-1]["status"] == "blocked_unconfirmed"


def test_confirmed_write_commits_once_and_deduplicates_retry():
    store = InMemoryCalendarStore()
    gate = CalendarApprovalGate(store=store)
    proposal = gate.preview(active_item(), now=NOW)
    first = gate.commit(proposal, user_confirmed=True)
    second = gate.commit(proposal, user_confirmed=True)
    assert first.status == "committed"
    assert second.status == "deduplicated"
    assert len(store.events) == 1


def test_clarification_case_cannot_reach_confirmation():
    item = build_timeline([EmailInput(
        subject="PE6201 consultation",
        body="Please attend the PE6201 consultation next Friday.",
    )], now=NOW)[0]
    gate = CalendarApprovalGate()
    with pytest.raises(CalendarPolicyError):
        gate.preview(item, now=NOW)
    assert gate.store.events == {}


def test_cancelled_item_cannot_create_event():
    item = build_timeline([
        EmailInput(
            subject="PE6201 workshop",
            body="The PE6201 workshop is on 3 October 2026 at 10:00 AM SGT.",
            sent_at="2026-09-20T10:00:00+08:00",
        ),
        EmailInput(
            subject="PE6201 workshop cancelled",
            body="The PE6201 workshop on 3 October 2026 has been cancelled.",
            sent_at="2026-09-26T10:00:00+08:00",
        ),
    ], now=NOW)[0]
    gate = CalendarApprovalGate()
    with pytest.raises(CalendarPolicyError):
        gate.preview(item, now=NOW)

