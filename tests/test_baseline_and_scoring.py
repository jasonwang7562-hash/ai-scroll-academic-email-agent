import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.baseline import baseline_extract
from app.models import EmailInput


NOW = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def test_baseline_extracts_explicit_deadline_but_has_no_update_memory():
    result = baseline_extract(EmailInput(
        subject="PE6201 project deadline extended",
        body="Submit the PE6201 project by 4 October 2026 at 11:59 PM SGT.",
    ), NOW)
    assert result["course"] == "PE6201"
    assert result["deadline_iso"] == "2026-10-04T23:59:00+08:00"
    assert result["relation_to_previous"] == "new"
    assert result["calendar_action"] == "create"


def test_baseline_does_not_create_event_for_informational_email():
    result = baseline_extract(EmailInput(
        subject="PE6201 weekly reading list",
        body="This week's optional reading list is now available.",
    ), NOW)
    assert result["deadline_iso"] is None
    assert result["calendar_action"] == "do_not_create"
    assert result["needs_clarification"] is False


def test_ratio_preserves_count_and_denominator():
    script = Path(__file__).resolve().parents[1] / "04_evaluation" / "score_development.py"
    spec = importlib.util.spec_from_file_location("score_development", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.ratio(2, 4) == {"correct": 2, "total": 4, "percent": 50.0}
