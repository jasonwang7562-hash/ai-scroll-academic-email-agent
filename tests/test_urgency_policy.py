from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.date_validation import urgency_for


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def iso(hours):
    return (NOW + timedelta(hours=hours)).isoformat()


def test_fixed_urgency_boundaries():
    assert urgency_for(iso(72), "ordinary task", now=NOW) == "high"
    assert urgency_for(iso(73), "ordinary task", now=NOW) == "medium"
    assert urgency_for(iso(168), "ordinary task", now=NOW) == "medium"
    assert urgency_for(iso(169), "ordinary task", now=NOW) == "low"


def test_explicit_mandatory_language_is_high_priority():
    assert urgency_for(iso(240), "This task is mandatory.", now=NOW) == "high"

