from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.extractor import PROMPT_VERSION, live_extract
from app.models import EmailInput


DATA = ROOT / "02_data"
OUTPUT = ROOT / "04_evaluation" / "outputs"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def preflight() -> dict:
    frozen = DATA / "gold_labels_frozen.jsonl"
    checksum = DATA / "FROZEN_LABELS_SHA256.txt"
    required_env = ("AI_SCROLL_API_KEY", "AI_SCROLL_BASE_URL", "AI_SCROLL_MODEL")
    missing_env = [name for name in required_env if not os.getenv(name, "").strip()]
    checks = {
        "frozen_labels_present": frozen.exists(),
        "frozen_checksum_present": checksum.exists(),
        "live_model_configured": not missing_env,
        "missing_environment_variables": missing_env,
        "prompt_version": PROMPT_VERSION,
    }
    checks["ready"] = all((checks["frozen_labels_present"], checks["frozen_checksum_present"], checks["live_model_configured"]))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the final frozen-label model evaluation.")
    parser.add_argument("--execute", action="store_true", help="Make live model calls after all preflight checks pass.")
    args = parser.parse_args()
    checks = preflight()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "final_evaluation_preflight.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))

    if not args.execute:
        print("Preflight only. Add --execute after labels are frozen and the model is configured.")
        return
    if not checks["ready"]:
        raise SystemExit("Final evaluation blocked: complete every preflight requirement first.")

    emails = read_jsonl(DATA / "evaluation_emails.jsonl")
    run_id = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y%m%dT%H%M%S%z")
    output_path = OUTPUT / f"final_model_outputs_{run_id}.jsonl"
    usage_path = OUTPUT / f"final_model_usage_{run_id}.jsonl"
    for index, row in enumerate(emails, 1):
        email = EmailInput(**{key: row.get(key) for key in ("subject", "sender", "body", "sent_at")})
        task, usage = live_extract(email)
        result = task.model_dump()
        result["dataset_email_id"] = row["email_id"]
        result["split"] = row["split"]
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
        with usage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"dataset_email_id": row["email_id"], **usage}) + "\n")
        print(f"Completed {index}/{len(emails)}: {row['email_id']}")
    print(f"Saved model outputs to {output_path}")
    print(f"Saved token and latency usage to {usage_path}")


if __name__ == "__main__":
    main()
