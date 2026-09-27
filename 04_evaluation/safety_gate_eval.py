from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.calendar_gate import ApprovalRequiredError, CalendarApprovalGate, CalendarPolicyError, InMemoryCalendarStore
from app.merge_engine import build_timeline
from app.models import EmailInput


OUTPUT = ROOT / "04_evaluation" / "outputs" / "safety_gate_results.json"
NOW = datetime(2026, 9, 27, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def timeline(*emails):
    return build_timeline(list(emails), now=NOW)[0]


def main() -> None:
    store = InMemoryCalendarStore()
    audit = []
    gate = CalendarApprovalGate(store=store, audit=audit)

    eligible = timeline(EmailInput(
        subject="PE6201 project deadline",
        body="The PE6201 project is due on 4 October 2026 at 11:59 PM SGT.",
    ))
    proposal = gate.preview(eligible, now=NOW)

    unconfirmed_blocked = False
    events_before = len(store.events)
    try:
        gate.commit(proposal, user_confirmed=False)
    except ApprovalRequiredError:
        unconfirmed_blocked = True
    unauthorized_writes = len(store.events) - events_before

    first = gate.commit(proposal, user_confirmed=True)
    duplicate = gate.commit(proposal, user_confirmed=True)

    ambiguous = timeline(EmailInput(
        subject="PE6201 consultation",
        body="Please attend the PE6201 consultation next Friday.",
    ))
    ambiguous_blocked = False
    try:
        gate.preview(ambiguous, now=NOW)
    except CalendarPolicyError:
        ambiguous_blocked = True

    cancelled = timeline(
        EmailInput(
            subject="PE6201 workshop",
            body="The PE6201 workshop is on 3 October 2026 at 10:00 AM SGT.",
            sent_at="2026-09-20T09:00:00+08:00",
        ),
        EmailInput(
            subject="PE6201 workshop cancelled",
            body="The PE6201 workshop on 3 October 2026 has been cancelled.",
            sent_at="2026-09-26T09:00:00+08:00",
        ),
    )
    cancelled_blocked = False
    try:
        gate.preview(cancelled, now=NOW)
    except CalendarPolicyError:
        cancelled_blocked = True

    result = {
        "evaluation_type": "development_safety_gate_test",
        "warning": "This uses an in-memory adapter. Google Calendar integration is a later milestone.",
        "unconfirmed_attempts": 1,
        "unconfirmed_attempts_blocked": int(unconfirmed_blocked),
        "unauthorized_writes": unauthorized_writes,
        "authorized_writes": int(first.status == "committed"),
        "duplicate_attempts": 1,
        "duplicates_prevented": int(duplicate.status == "deduplicated"),
        "unsafe_cases_checked": 2,
        "unsafe_cases_blocked": int(ambiguous_blocked) + int(cancelled_blocked),
        "stored_event_count": len(store.events),
        "audit": audit,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary_keys = [
        "unconfirmed_attempts", "unconfirmed_attempts_blocked", "unauthorized_writes",
        "authorized_writes", "duplicates_prevented", "unsafe_cases_blocked",
    ]
    print(json.dumps({key: result[key] for key in summary_keys}, indent=2))


if __name__ == "__main__":
    main()

