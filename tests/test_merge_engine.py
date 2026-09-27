from datetime import datetime
from zoneinfo import ZoneInfo

from app.merge_engine import build_timeline
from app.models import EmailInput


NOW = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def mail(subject, body, sent_at):
    return EmailInput(subject=subject, body=body, sent_at=sent_at)


def test_deadline_extension_becomes_one_timeline_item():
    timeline = build_timeline([
        mail("PE6201 project deadline", "The PE6201 project analysis is due on 1 October 2026 at 11:59 PM SGT.", "2026-09-22T10:00:00+08:00"),
        mail("PE6201 project deadline extended", "The PE6201 project analysis deadline has been extended to 4 October 2026 at 11:59 PM SGT.", "2026-09-25T10:00:00+08:00"),
    ], now=NOW)
    assert len(timeline) == 1
    assert timeline[0].deadline_iso == "2026-10-04T23:59:00+08:00"
    assert len(timeline[0].source_email_ids) == 2
    assert timeline[0].change_history[0].previous_value == "2026-10-01T23:59:00+08:00"
    assert timeline[0].calendar_action == "update"


def test_later_cancellation_blocks_calendar_action():
    timeline = build_timeline([
        mail("HR6102 research workshop", "The HR6102 research workshop is scheduled for 4 October 2026 at 10:00 AM SGT.", "2026-09-22T14:00:00+08:00"),
        mail("HR6102 workshop cancelled", "The HR6102 research workshop on 4 October 2026 has been cancelled.", "2026-09-25T14:00:00+08:00"),
    ], now=NOW)
    assert len(timeline) == 1
    assert timeline[0].status == "cancelled"
    assert timeline[0].deadline_iso is None
    assert timeline[0].calendar_action == "do_not_create"


def test_unrelated_same_course_tasks_stay_separate():
    timeline = build_timeline([
        mail("PE6201 project deadline", "The PE6201 project is due on 4 October 2026 at 11:59 PM SGT.", "2026-09-22T10:00:00+08:00"),
        mail("PE6201 consultation", "The PE6201 consultation is on 2 October 2026 at 3:00 PM SGT.", "2026-09-23T10:00:00+08:00"),
    ], now=NOW)
    assert len(timeline) == 2

