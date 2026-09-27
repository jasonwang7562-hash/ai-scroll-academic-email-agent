from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


TASK_TYPES = ("assignment", "exam", "class_change", "administrative", "other")
URGENCIES = ("high", "medium", "low", "clarification")
RELATIONS = ("new", "update", "cancel")
CALENDAR_ACTIONS = ("create", "update", "do_not_create", "ask_clarification")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_review_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def review_progress(rows: list[dict[str, str]]) -> dict[str, int]:
    approved = sum(row["review_status"] == "approved" for row in rows)
    return {"approved": approved, "pending": len(rows) - approved, "total": len(rows)}


def validate_review(row: dict[str, str], email: dict) -> list[str]:
    errors: list[str] = []
    if row["task_type_gold"] not in TASK_TYPES:
        errors.append("Task type is outside the allowed categories.")
    if row["urgency_gold"] not in URGENCIES:
        errors.append("Urgency is outside the allowed categories.")
    if row["relation_gold"] not in RELATIONS:
        errors.append("Relation is outside the allowed categories.")
    if row["calendar_action_gold"] not in CALENDAR_ACTIONS:
        errors.append("Calendar action is outside the allowed categories.")
    if not row["course_gold"].strip():
        errors.append("Course is required.")
    if not row["task_title_gold"].strip():
        errors.append("Task title is required.")
    if row["deadline_gold"]:
        try:
            datetime.fromisoformat(row["deadline_gold"])
        except ValueError:
            errors.append("Deadline must be a valid ISO date-time.")
    if row["evidence_gold"] not in email["body"]:
        errors.append("Evidence must be copied exactly from the email body.")

    needs_clarification = row["needs_clarification_gold"].lower() == "true"
    if needs_clarification:
        if row["urgency_gold"] != "clarification":
            errors.append("Clarification cases must use clarification urgency.")
        if row["calendar_action_gold"] != "ask_clarification":
            errors.append("Clarification cases must ask for clarification instead of writing a calendar event.")
        if not row["clarification_reason_gold"].strip():
            errors.append("Clarification cases need a reason.")
    elif row["urgency_gold"] == "clarification" or row["calendar_action_gold"] == "ask_clarification":
        errors.append("Clarification urgency/action requires needs_clarification to be selected.")
    return errors


def save_review_row(path: Path, email_id: str, updates: dict[str, object], approve: bool = False) -> dict[str, str]:
    rows = load_review_rows(path)
    target = next((row for row in rows if row["email_id"] == email_id), None)
    if target is None:
        raise KeyError(f"Unknown email ID: {email_id}")

    editable = {
        "course_gold", "task_type_gold", "task_title_gold", "deadline_gold", "timezone_gold",
        "urgency_gold", "evidence_gold", "relation_gold", "calendar_action_gold",
        "needs_clarification_gold", "clarification_reason_gold", "reviewer_notes",
    }
    for key, value in updates.items():
        if key not in editable:
            raise ValueError(f"Field is not editable: {key}")
        target[key] = str(value)
    target["review_status"] = "approved" if approve else "pending_human_review"

    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)
    return target
