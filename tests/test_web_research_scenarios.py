import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.extractor import demo_extract
from app.models import EmailInput


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "02_data" / "web_research_scenarios.jsonl"
NOW = datetime(2026, 7, 1, 9, 0, tzinfo=ZoneInfo("Asia/Singapore"))


def test_public_platform_scenarios_preserve_due_date_semantics():
    rows = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) >= 6
    assert all(row["source_url"].startswith("https://") for row in rows)
    for row in rows:
        task = demo_extract(
            EmailInput(subject=row["subject"], body=row["body"]),
            now=NOW,
        )
        assert task.calendar_action == row["expected_action"], row["case_id"]
        assert task.deadline_iso == row["expected_deadline"], row["case_id"]
