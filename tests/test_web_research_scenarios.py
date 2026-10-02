import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.extractor import demo_extract, enforce_live_safety
from app.models import EmailInput, ExtractedTask


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "02_data" / "web_research_scenarios.jsonl"
NOW = datetime(2026, 7, 1, 9, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def test_public_platform_scenarios_preserve_due_date_semantics():
    rows = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) >= 6
    assert all(row["source_url"].startswith("https://") for row in rows)
    for row in rows:
        task = demo_extract(
            EmailInput(subject=row["subject"], body=row["body"]),
            now=NOW,
        )
        assert task.calendar_action == row["expected_action"], row["case_id"]
        assert task.deadline_iso == row["expected_deadline"], row["case_id"]


def _unsafe_model_task(**changes):
    values = {
        "email_id": "email-model",
        "thread_id": "thread-model",
        "course": "CZ4013",
        "task_type": "assignment",
        "task_title": "Essay",
        "deadline_iso": "2026-10-12T23:59:00+08:00",
        "timezone": "Asia/Singapore",
        "urgency": "medium",
        "evidence_quote": "The assignment is available until 12 October 2026 at 11:59 PM SGT.",
        "relation_to_previous": "new",
        "calendar_action": "create",
        "needs_clarification": False,
        "clarification_reason": None,
        "source_subject": "CZ4013 availability",
    }
    values.update(changes)
    return ExtractedTask(**values)


def test_live_safety_blocks_availability_window_even_if_model_calls_it_a_deadline():
    email = EmailInput(
        subject="CZ4013 availability",
        body="The assignment is available until 12 October 2026 at 11:59 PM SGT.",
    )
    safe = enforce_live_safety(_unsafe_model_task(), email)
    assert safe.deadline_iso is None
    assert safe.calendar_action == "do_not_create"
    assert safe.email_id.startswith("email_")
    assert safe.email_id != "email-model"
    assert safe.source_subject == email.subject
    assert safe.course == "CZ4013"


def test_live_safety_removes_partial_deadline_from_clarification_case():
    email = EmailInput(subject="CS6204 quiz", body="The quiz is due on 15 October 2026.")
    unsafe = _unsafe_model_task(
        deadline_iso="2026-10-15",
        urgency="clarification",
        calendar_action="ask_clarification",
        needs_clarification=True,
        clarification_reason="Time and timezone are missing.",
        evidence_quote="The quiz is due on 15 October 2026.",
    )
    assert enforce_live_safety(unsafe, email).deadline_iso is None
