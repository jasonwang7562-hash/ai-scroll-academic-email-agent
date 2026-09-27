import csv
from pathlib import Path

from app.label_review import review_progress, save_review_row, validate_review


def sample_email():
    return {"body": "Submit PE6201 work by 4 October 2026 at 11:59 PM SGT."}


def sample_row():
    return {
        "email_id": "x1", "thread_id": "tx1", "course_gold": "PE6201",
        "task_type_gold": "assignment", "task_title_gold": "Submit work",
        "deadline_gold": "2026-10-04T23:59:00+08:00", "timezone_gold": "Asia/Singapore",
        "urgency_gold": "low", "urgency_reason": "rule",
        "evidence_gold": "Submit PE6201 work by 4 October 2026 at 11:59 PM SGT.",
        "relation_gold": "new", "calendar_action_gold": "create",
        "needs_clarification_gold": "False", "clarification_reason_gold": "",
        "split": "development", "review_status": "pending_human_review", "reviewer_notes": "",
    }


def write_review(path: Path, row: dict):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def test_valid_review_can_be_approved_atomically(tmp_path):
    path = tmp_path / "review.csv"
    row = sample_row()
    write_review(path, row)
    assert validate_review(row, sample_email()) == []
    saved = save_review_row(path, "x1", {"reviewer_notes": "Checked source."}, approve=True)
    assert saved["review_status"] == "approved"
    assert review_progress([saved]) == {"approved": 1, "pending": 0, "total": 1}


def test_non_verbatim_evidence_is_rejected():
    row = sample_row()
    row["evidence_gold"] = "Paraphrased evidence"
    assert "Evidence must be copied exactly from the email body." in validate_review(row, sample_email())


def test_clarification_requires_safe_action_and_reason():
    row = sample_row()
    row["needs_clarification_gold"] = "True"
    errors = validate_review(row, sample_email())
    assert any("clarification urgency" in error for error in errors)
    assert any("ask for clarification" in error for error in errors)
    assert any("need a reason" in error for error in errors)
