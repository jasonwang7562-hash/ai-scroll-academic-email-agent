import json
from collections import Counter
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "02_data"


def read_jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding="utf-8").splitlines() if line]


def test_dataset_inventory_and_evidence():
    emails = read_jsonl("evaluation_emails.jsonl")
    labels = read_jsonl("gold_labels_draft.jsonl")
    by_email = {row["email_id"]: row for row in emails}
    counts = Counter(row["thread_id"] for row in emails)

    assert len(emails) == len(labels) == 50
    assert len(counts) == 38
    assert sum(size == 1 for size in counts.values()) == 30
    assert sum(size > 1 for size in counts.values()) == 8
    assert sum(size for size in counts.values() if size > 1) == 20
    assert all(label["evidence_gold"] in by_email[label["email_id"]]["body"] for label in labels)


def test_draft_labels_cannot_be_mistaken_for_frozen_gold():
    labels = read_jsonl("gold_labels_draft.jsonl")
    assert all(row["review_status"] == "pending_human_review" for row in labels)
    assert not (DATA / "gold_labels_frozen.jsonl").exists()

