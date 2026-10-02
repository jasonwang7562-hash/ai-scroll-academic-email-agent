from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.backward_planner import BusyWindow, PlanningError, build_backward_plan, milestone_proposal
from app.merge_engine import build_timeline
from app.models import EmailInput


SGT = ZoneInfo("Asia/Singapore")
NOW = datetime(2026, 9, 30, 9, 0, tzinfo=SGT)


def assignment():
    return build_timeline([EmailInput(
        subject="PE6201 project deadline",
        body="The PE6201 assignment is due on 4 October 2026 at 11:59 PM SGT.",
    )], now=NOW)[0]


def test_backward_plan_finishes_before_buffer_and_avoids_busy_time():
    busy = [BusyWindow(
        start=datetime(2026, 10, 3, 18, 0, tzinfo=SGT),
        end=datetime(2026, 10, 3, 21, 0, tzinfo=SGT),
    )]
    plan = build_backward_plan(
        assignment(), now=NOW, estimated_hours=8, buffer_hours=4, busy=busy
    )
    assert len(plan.milestones) == 5
    assert list(plan.milestones) == sorted(plan.milestones, key=lambda item: item.start)
    assert plan.milestones[-1].end <= plan.deadline - timedelta(hours=4)
    assert all(
        not (milestone.start < busy[0].end and milestone.end > busy[0].start)
        for milestone in plan.milestones
    )


def test_plan_proposal_has_stable_id_and_explicit_end():
    plan = build_backward_plan(assignment(), now=NOW, estimated_hours=4, buffer_hours=2)
    first = milestone_proposal(assignment(), plan.milestones[0])
    second = milestone_proposal(assignment(), plan.milestones[0])
    assert first.proposal_id == second.proposal_id
    assert first.end == plan.milestones[0].end.isoformat()


def test_impossible_plan_is_explained():
    with pytest.raises(PlanningError):
        build_backward_plan(
            assignment(),
            now=datetime(2026, 10, 4, 22, 0, tzinfo=SGT),
            estimated_hours=8,
            buffer_hours=4,
        )
