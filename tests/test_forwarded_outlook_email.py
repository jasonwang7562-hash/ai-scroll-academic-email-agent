from datetime import datetime
from zoneinfo import ZoneInfo

from app.extractor import demo_extract
from app.merge_engine import build_timeline
from app.models import EmailInput


def test_forwarded_outlook_deadline_with_ordinal_day_and_24_hour_time():
    task = demo_extract(
        EmailInput(
            subject="转发: PE6201 End of course project deliverables",
            sender="Wang Jason <jasonwang7562@outlook.com>",
            body="Finish line is coming Sunday, October the 4th, 23:59 hrs Singapore time.",
            sent_at="2026-10-04T12:32:00+08:00",
        ),
        now=datetime(2026, 10, 1, 9, 0, tzinfo=ZoneInfo("Asia/Singapore")),
    )

    assert task.deadline_iso == "2026-10-04T23:59:00+08:00"
    assert task.needs_clarification is False
    assert task.calendar_action == "create"
    assert task.task_title == "End of course project deliverables"


def test_shared_forwarded_lms_footer_does_not_merge_unrelated_announcements():
    boilerplate = "26S1-PE6201-A New announcement from PaCE. View Announcement."
    timeline = build_timeline(
        [
            EmailInput(
                subject="转发: PE6201 My contact details",
                body=f"{boilerplate} Email: instructor@example.com",
                sent_at="2026-08-04T11:28:00+08:00",
            ),
            EmailInput(
                subject="转发: PE6201 End of course project deliverables",
                body=f"{boilerplate} Finish line is coming Sunday, October the 4th, 23:59 hrs Singapore time.",
                sent_at="2026-10-01T15:57:00+08:00",
            ),
        ],
        now=datetime(2026, 10, 1, 9, 0, tzinfo=ZoneInfo("Asia/Singapore")),
    )

    assert len(timeline) == 2
    active = next(item for item in timeline if item.deadline_iso)
    assert active.deadline_iso == "2026-10-04T23:59:00+08:00"
