from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    emails = read_jsonl("evaluation_emails.jsonl")
    labels = read_jsonl("gold_labels_draft.jsonl")
    threads = read_jsonl("thread_gold_draft.jsonl")

    assert len(emails) == 50, f"Expected 50 emails, found {len(emails)}"
    assert len(labels) == 50, f"Expected 50 labels, found {len(labels)}"
    assert len({row['email_id'] for row in emails}) == 50, "Duplicate email_id"
    assert {row["email_id"] for row in emails} == {row["email_id"] for row in labels}, "Email/label mismatch"

    by_email = {row["email_id"]: row for row in emails}
    for label in labels:
        evidence = label["evidence_gold"]
        if evidence:
            assert evidence in by_email[label["email_id"]]["body"], f"Non-verbatim evidence: {label['email_id']}"
        if label["needs_clarification_gold"]:
            assert label["calendar_action_gold"] == "ask_clarification"
            assert label["urgency_gold"] == "clarification"
            assert label["clarification_reason_gold"]
        assert label["review_status"] in {"pending_human_review", "approved", "needs_change"}

    counts = Counter(row["thread_id"] for row in emails)
    assert len(counts) == 38, f"Expected 38 threads, found {len(counts)}"
    assert sum(value == 1 for value in counts.values()) == 30
    assert sum(value > 1 for value in counts.values()) == 8
    assert sum(value for value in counts.values() if value > 1) == 20
    assert len(threads) == 8
    assert {row["thread_id"] for row in threads} == {key for key, value in counts.items() if value > 1}

    for thread in threads:
        assert len(thread["source_email_ids"]) == counts[thread["thread_id"]]
        assert all(email_id in by_email for email_id in thread["source_email_ids"])

    print("DATASET VALIDATION PASSED")
    print("50 emails | 38 threads | 30 independent | 8 multi-email threads | 20 chain emails")
    print("Draft labels remain pending human review.")


if __name__ == "__main__":
    main()

