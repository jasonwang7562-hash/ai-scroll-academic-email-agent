from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.merge_engine import build_timeline
from app.models import EmailInput


DATA = ROOT / "02_data"
OUTPUT = ROOT / "04_evaluation" / "outputs" / "merge_smoke_results.json"


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    emails = read_jsonl(DATA / "evaluation_emails.jsonl")
    thread_gold = read_jsonl(DATA / "thread_gold_draft.jsonl")
    results = []

    for expected in thread_gold:
        rows = [row for row in emails if row["thread_id"] == expected["thread_id"]]
        inputs = [
            EmailInput(
                subject=row["subject"], sender=row["sender"],
                body=row["body"], sent_at=row["sent_at"],
            )
            for row in rows
        ]
        timeline = build_timeline(inputs)
        one_item = len(timeline) == 1
        actual = timeline[0] if one_item else None
        passed = bool(
            one_item
            and actual.deadline_iso == expected["final_deadline_gold"]
            and actual.status == expected["final_status_gold"]
            and actual.calendar_action == expected["final_calendar_action_gold"]
        )
        results.append({
            "thread_id": expected["thread_id"],
            "source_email_count": len(rows),
            "timeline_item_count": len(timeline),
            "expected_deadline": expected["final_deadline_gold"],
            "actual_deadline": actual.deadline_iso if actual else None,
            "expected_status": expected["final_status_gold"],
            "actual_status": actual.status if actual else None,
            "expected_calendar_action": expected["final_calendar_action_gold"],
            "actual_calendar_action": actual.calendar_action if actual else None,
            "passed": passed,
            "label_status": expected["review_status"],
        })

    output = {
        "evaluation_type": "development_smoke_test",
        "warning": "Draft labels are pending human review. These are not final report metrics.",
        "threads_checked": len(results),
        "threads_passed": sum(result["passed"] for result in results),
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("evaluation_type", "warning", "threads_checked", "threads_passed")}, indent=2))


if __name__ == "__main__":
    main()
