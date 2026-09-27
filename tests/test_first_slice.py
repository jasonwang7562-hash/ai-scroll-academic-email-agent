from datetime import datetime
from zoneinfo import ZoneInfo

from app.extractor import demo_extract
from app.models import EmailInput
from app.sample_data import SAMPLE_BODY, SAMPLE_SENDER, SAMPLE_SUBJECT


NOW = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def test_sample_email_matches_product_contract():
    result = demo_extract(
        EmailInput(subject=SAMPLE_SUBJECT, sender=SAMPLE_SENDER, body=SAMPLE_BODY),
        now=NOW,
    )
    assert result.course == "PE6201"
    assert result.task_type == "assignment"
    assert result.deadline_iso == "2026-10-04T23:59:00+08:00"
    assert result.evidence_quote in SAMPLE_BODY
    assert result.calendar_action == "create"
    assert result.needs_clarification is False


def test_missing_time_requests_clarification():
    email = EmailInput(
        subject="PE6201 report deadline",
        body="The report is due on 4 October 2026.",
    )
    result = demo_extract(email, now=NOW)
    assert result.needs_clarification is True
    assert result.calendar_action == "ask_clarification"
    assert result.urgency == "clarification"


def test_evidence_is_verbatim():
    result = demo_extract(
        EmailInput(subject=SAMPLE_SUBJECT, sender=SAMPLE_SENDER, body=SAMPLE_BODY),
        now=NOW,
    )
    assert result.evidence_quote in SAMPLE_BODY


def test_informational_email_does_not_request_clarification():
    email = EmailInput(
        subject="PE6201 weekly resources",
        body="The PE6201 weekly resources are now available in NTU Learn.",
    )
    result = demo_extract(email, now=NOW)
    assert result.calendar_action == "do_not_create"
    assert result.needs_clarification is False
    assert result.evidence_quote in email.body
