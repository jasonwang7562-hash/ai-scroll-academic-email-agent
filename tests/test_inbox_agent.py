from datetime import datetime
from zoneinfo import ZoneInfo

from app.inbox_agent import DemoMailboxConnector, InboxAgent


NOW = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def test_agent_scans_mailbox_filters_noise_and_merges_threads():
    result = InboxAgent(DemoMailboxConnector()).run(now=NOW)
    assert result.scanned == 5
    assert result.academic == 4
    assert result.ignored == 1
    assert len(result.timeline) == 2
    assert result.review_required == 1
    assert len(result.decisions) == 5
    assert sum(item.decision == "process" for item in result.decisions) == 4
    assert result.duration_ms >= 0

    project = next(item for item in result.timeline if item.course == "PE6201")
    assert project.deadline_iso == "2026-10-04T23:59:00+08:00"
    assert len(project.source_email_ids) == 2
    assert project.calendar_action == "update"

    workshop = next(item for item in result.timeline if item.course == "HR6102")
    assert workshop.status == "cancelled"
    assert workshop.calendar_action == "do_not_create"


def test_course_scope_excludes_other_academic_courses():
    result = InboxAgent(
        DemoMailboxConnector(), allowed_courses={"PE6201"}
    ).run(now=NOW)

    assert result.scanned == 5
    assert result.academic == 2
    assert result.ignored == 3
    assert [item.course for item in result.timeline] == ["PE6201"]
    assert any(
        decision.reason == "Outside configured course scope"
        for decision in result.decisions
    )
