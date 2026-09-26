from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    review_path = ROOT / "gold_label_review.csv"
    with review_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    pending = [row["email_id"] for row in rows if row["review_status"] != "approved"]
    if pending:
        preview = ", ".join(pending[:8])
        raise SystemExit(f"Cannot freeze labels: {len(pending)} rows are not approved. First rows: {preview}")

    output = ROOT / "gold_labels_frozen.jsonl"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            normalized = {key: (None if value == "" else value) for key, value in row.items()}
            normalized["needs_clarification_gold"] = str(normalized["needs_clarification_gold"]).lower() == "true"
            handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (ROOT / "FROZEN_LABELS_SHA256.txt").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(f"Frozen 50 approved labels. SHA256: {digest}")


if __name__ == "__main__":
    main()

