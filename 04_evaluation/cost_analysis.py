from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.cost_model import CostInputs, polling_cost_scenarios


OUTPUT = ROOT / "04_evaluation" / "outputs" / "cost_analysis.json"


def live_usage_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    if path.suffix == ".jsonl":
        return [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and int(json.loads(line).get("prompt_tokens") or 0) > 0
        ]
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            row for row in csv.DictReader(handle)
            if row.get("mode") == "Live model" and int(row.get("prompt_tokens") or 0) > 0
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AI Scroll cost and polling scenarios.")
    parser.add_argument("--input-price", type=float, help="USD per million input tokens")
    parser.add_argument("--output-price", type=float, help="USD per million output tokens")
    parser.add_argument("--price-date", help="Date the provider price was checked, YYYY-MM-DD")
    parser.add_argument("--model", help="Exact model ID")
    parser.add_argument("--emails-per-day", type=int, default=20)
    parser.add_argument("--usage-log", type=Path, help="CSV model log or final_model_usage JSONL")
    args = parser.parse_args()

    if args.usage_log:
        usage_path = args.usage_log
    else:
        final_logs = sorted((ROOT / "04_evaluation" / "outputs").glob("final_model_usage_*.jsonl"))
        usage_path = final_logs[-1] if final_logs else ROOT / "logs" / "model_calls.csv"
    usage = live_usage_rows(usage_path)
    missing = []
    if not usage:
        missing.append("live model token usage")
    if args.input_price is None or args.output_price is None:
        missing.append("provider input/output prices")
    if not args.price_date:
        missing.append("provider price date")
    if not args.model:
        missing.append("exact model ID")

    if missing:
        result = {
            "status": "PENDING",
            "missing": missing,
            "note": "No cost claim is produced until measured token usage and dated provider prices are supplied.",
            "architecture_decision": "Poll the inbox without an LLM; call the model only for new messages.",
        }
    else:
        prompt = [int(row["prompt_tokens"]) for row in usage]
        completion = [int(row["completion_tokens"]) for row in usage]
        inputs = CostInputs(
            average_prompt_tokens=sum(prompt) / len(prompt),
            average_completion_tokens=sum(completion) / len(completion),
            input_price_per_million_usd=args.input_price,
            output_price_per_million_usd=args.output_price,
            new_emails_per_day=args.emails_per_day,
        )
        result = {
            "status": "MEASURED",
            "model": args.model,
            "price_date": args.price_date,
            "usage_source": str(usage_path),
            "measured_calls": len(usage),
            **polling_cost_scenarios(inputs),
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
