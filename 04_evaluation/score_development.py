from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.baseline import baseline_extract
from app.extractor import demo_extract
from app.merge_engine import build_timeline
from app.models import EmailInput


DATA = ROOT / "02_data"
OUTPUT = ROOT / "04_evaluation" / "outputs"
NOW = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))
SYSTEMS = ("keyword_date_baseline_v1", "deterministic_dev_pipeline_v1")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def ratio(correct: int, total: int) -> dict:
    return {"correct": correct, "total": total, "percent": round(100 * correct / total, 1) if total else None}


def score_rows(outputs: list[dict], gold_by_id: dict[str, dict]) -> tuple[dict, list[dict]]:
    pairs = [(row, gold_by_id[row["email_id"]]) for row in outputs]
    deadline_cases = [(o, g) for o, g in pairs if g["deadline_gold"] is not None]
    no_deadline_cases = [(o, g) for o, g in pairs if g["deadline_gold"] is None]
    high_cases = [(o, g) for o, g in pairs if g["urgency_gold"] == "high"]
    predicted_clarifications = [(o, g) for o, g in pairs if o["needs_clarification"]]
    gold_clarifications = [(o, g) for o, g in pairs if g["needs_clarification_gold"]]

    confusion = Counter(f"{g['urgency_gold']}->{o['urgency']}" for o, g in pairs)
    metrics = {
        "course_identification": ratio(sum(o["course"] == g["course_gold"] for o, g in pairs), len(pairs)),
        "task_type_classification": ratio(sum(o["task_type"] == g["task_type_gold"] for o, g in pairs), len(pairs)),
        "deadline_exact_on_deadline_cases": ratio(
            sum(o["deadline_iso"] == g["deadline_gold"] for o, g in deadline_cases), len(deadline_cases)
        ),
        "false_deadlines_on_no_deadline_cases": {
            "count": sum(o["deadline_iso"] is not None for o, _g in no_deadline_cases),
            "total": len(no_deadline_cases),
        },
        "urgency_classification": ratio(sum(o["urgency"] == g["urgency_gold"] for o, g in pairs), len(pairs)),
        "urgency_confusion": dict(sorted(confusion.items())),
        "high_priority_deadline_recall": ratio(
            sum(o["deadline_iso"] == g["deadline_gold"] for o, g in high_cases), len(high_cases)
        ),
        "calendar_action": ratio(
            sum(o["calendar_action"] == g["calendar_action_gold"] for o, g in pairs), len(pairs)
        ),
        "relation_classification": ratio(
            sum(o["relation_to_previous"] == g["relation_gold"] for o, g in pairs), len(pairs)
        ),
        "clarification_precision": ratio(
            sum(g["needs_clarification_gold"] for _o, g in predicted_clarifications), len(predicted_clarifications)
        ),
        "clarification_recall": ratio(
            sum(o["needs_clarification"] for o, _g in gold_clarifications), len(gold_clarifications)
        ),
        "abstention_rate": {
            "count": len(predicted_clarifications),
            "total": len(pairs),
            "percent": round(100 * len(predicted_clarifications) / len(pairs), 1),
        },
    }

    errors = []
    comparisons = {
        "course": "course_gold",
        "task_type": "task_type_gold",
        "deadline_iso": "deadline_gold",
        "urgency": "urgency_gold",
        "calendar_action": "calendar_action_gold",
        "relation_to_previous": "relation_gold",
        "needs_clarification": "needs_clarification_gold",
    }
    for output, gold in pairs:
        for predicted_field, gold_field in comparisons.items():
            if output[predicted_field] != gold[gold_field]:
                errors.append({
                    "system": output["system"],
                    "email_id": output["email_id"],
                    "split": gold["split"],
                    "field": predicted_field,
                    "predicted": output[predicted_field],
                    "gold_draft": gold[gold_field],
                })
    return metrics, errors


def score_threads(emails: list[dict], thread_gold: list[dict]) -> tuple[dict, dict, list[dict]]:
    by_id = {row["email_id"]: row for row in emails}
    details = []
    for gold in thread_gold:
        inputs = [EmailInput(**{k: by_id[email_id].get(k) for k in ("subject", "sender", "body", "sent_at")})
                  for email_id in gold["source_email_ids"]]
        timeline = build_timeline(inputs, now=NOW)
        item = timeline[0] if len(timeline) == 1 else None
        merged_final_state_correct = bool(
            item
            and item.deadline_iso == gold["final_deadline_gold"]
            and item.status == gold["final_status_gold"]
            and item.calendar_action == gold["final_calendar_action_gold"]
            and len(item.source_email_ids) == len(gold["source_email_ids"])
        )
        full_record_correct = bool(
            merged_final_state_correct
            and item.course == gold["course_gold"]
            and item.task_type == gold["task_type_gold"]
        )
        details.append({
            "thread_id": gold["thread_id"],
            "split": gold["split"],
            "merged_final_state_correct": merged_final_state_correct,
            "full_record_correct": full_record_correct,
            "timeline_items_returned": len(timeline),
            "predicted_deadline": item.deadline_iso if item else None,
            "gold_draft_deadline": gold["final_deadline_gold"],
            "predicted_status": item.status if item else None,
            "gold_draft_status": gold["final_status_gold"],
        })
    return (
        ratio(sum(row["merged_final_state_correct"] for row in details), len(details)),
        ratio(sum(row["full_record_correct"] for row in details), len(details)),
        details,
    )


def main() -> None:
    emails = read_jsonl(DATA / "evaluation_emails.jsonl")
    gold = read_jsonl(DATA / "gold_labels_draft.jsonl")
    thread_gold = read_jsonl(DATA / "thread_gold_draft.jsonl")
    gold_by_id = {row["email_id"]: row for row in gold}

    baseline_outputs = []
    dev_outputs = []
    for row in emails:
        email = EmailInput(**{k: row.get(k) for k in ("subject", "sender", "body", "sent_at")})
        baseline_outputs.append({"system": SYSTEMS[0], "email_id": row["email_id"], **baseline_extract(email, NOW)})
        extracted = demo_extract(email, now=NOW).model_dump()
        extracted["internal_email_id"] = extracted.pop("email_id")
        dev_outputs.append({"system": SYSTEMS[1], "email_id": row["email_id"], **extracted})

    write_jsonl(OUTPUT / "baseline_outputs.jsonl", baseline_outputs)
    write_jsonl(OUTPUT / "dev_system_outputs.jsonl", dev_outputs)
    baseline_metrics, baseline_errors = score_rows(baseline_outputs, gold_by_id)
    dev_metrics, dev_errors = score_rows(dev_outputs, gold_by_id)
    merge_metric, full_thread_metric, merge_details = score_threads(emails, thread_gold)
    baseline_metrics["cross_email_merging"] = ratio(0, len(thread_gold))
    dev_metrics["cross_email_merging"] = merge_metric
    dev_metrics["cross_email_full_record"] = full_thread_metric

    result = {
        "evaluation_type": "provisional_offline_evaluation",
        "run_at": datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds"),
        "reference_time": NOW.isoformat(),
        "population": {
            "emails": len(emails),
            "threads": len({row["thread_id"] for row in emails}),
            "multi_email_threads": len(thread_gold),
            "splits": dict(Counter(row["split"] for row in emails)),
        },
        "readiness": "NOT_FINAL",
        "limitations": [
            "All gold labels are pending human review and are not frozen.",
            "The data is synthetic and was generated in the same project as the system.",
            "The synthetic holdout is not an independent real-world test set.",
            "No live language model was run because no API configuration is present.",
            "Token cost and latency comparisons are unavailable for deterministic systems.",
        ],
        "systems": {
            SYSTEMS[0]: {
                "description": "Keyword/date parser with no cross-email memory.",
                "metrics": baseline_metrics,
                "metrics_by_split": {
                    split: score_rows([o for o in baseline_outputs if gold_by_id[o["email_id"]]["split"] == split], gold_by_id)[0]
                    for split in ("development", "test", "synthetic_holdout")
                },
            },
            SYSTEMS[1]: {
                "description": "Current deterministic AI Scroll development pipeline.",
                "metrics": dev_metrics,
                "metrics_by_split": {
                    split: score_rows([o for o in dev_outputs if gold_by_id[o["email_id"]]["split"] == split], gold_by_id)[0]
                    for split in ("development", "test", "synthetic_holdout")
                },
            },
        },
        "merge_details": merge_details,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "development_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    def cell(metric: dict) -> str:
        return f"{metric['correct']}/{metric['total']} ({metric['percent']:.1f}%)"

    rows = []
    metric_labels = (
        ("Course identification", "course_identification"),
        ("Task type", "task_type_classification"),
        ("Exact deadline", "deadline_exact_on_deadline_cases"),
        ("Urgency", "urgency_classification"),
        ("Calendar action", "calendar_action"),
        ("Clarification recall", "clarification_recall"),
        ("Cross-email merge", "cross_email_merging"),
    )
    for label, key in metric_labels:
        rows.append(
            f"| {label} | {cell(baseline_metrics[key])} | {cell(dev_metrics[key])} |"
        )
    report = "\n".join([
        "# Provisional Offline Evaluation",
        "",
        "> **NOT FINAL:** every gold label is still pending human review. The 50 emails are synthetic, and no live language model was run.",
        "",
        f"Reference time: `{NOW.isoformat()}`. Population: 50 emails, 38 threads, including 8 multi-email threads.",
        "",
        "| Metric | Keyword/date baseline | Current deterministic pipeline |",
        "|---|---:|---:|",
        *rows,
        "",
        "The current pipeline is stronger on the draft labels, especially for thread updates and calendar decisions. These numbers are evidence for debugging only until Jason reviews and freezes the labels. A live model run, token/cost log, and independent real-email test set are still required for the final submission.",
        "",
        "Detailed outputs: `outputs/development_metrics.json`, `outputs/development_errors.csv`, `outputs/baseline_outputs.jsonl`, and `outputs/dev_system_outputs.jsonl`.",
        "",
    ])
    (ROOT / "04_evaluation" / "PROVISIONAL_RESULTS.md").write_text(report, encoding="utf-8")

    errors = baseline_errors + dev_errors
    with (OUTPUT / "development_errors.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["system", "email_id", "split", "field", "predicted", "gold_draft"])
        writer.writeheader()
        writer.writerows(errors)

    print(json.dumps({name: data["metrics"] for name, data in result["systems"].items()}, indent=2))
    print(f"Saved {len(errors)} field-level errors to {OUTPUT / 'development_errors.csv'}")


if __name__ == "__main__":
    main()
