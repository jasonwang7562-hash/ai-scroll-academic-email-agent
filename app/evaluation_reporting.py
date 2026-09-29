from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SYSTEM_BASELINE = "keyword_date_baseline_v1"
SYSTEM_CURRENT = "deterministic_dev_pipeline_v1"

METRIC_LABELS = (
    ("Course identification", "course_identification"),
    ("Task type", "task_type_classification"),
    ("Exact deadline", "deadline_exact_on_deadline_cases"),
    ("Urgency", "urgency_classification"),
    ("Calendar action", "calendar_action"),
    ("Clarification recall", "clarification_recall"),
    ("Cross-email merge", "cross_email_merging"),
)


def load_evaluation(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_errors(path: Path, *, system: str = SYSTEM_CURRENT) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["system"] == system]


def metric_source(system: dict, split: str) -> dict:
    if split == "all":
        return system["metrics"]
    return system["metrics_by_split"][split]


def comparison_rows(evaluation: dict, split: str = "all") -> list[dict]:
    baseline = metric_source(evaluation["systems"][SYSTEM_BASELINE], split)
    current = metric_source(evaluation["systems"][SYSTEM_CURRENT], split)
    rows = []
    for label, key in METRIC_LABELS:
        if key not in baseline or key not in current:
            continue
        baseline_metric = baseline[key]
        current_metric = current[key]
        baseline_percent = baseline_metric.get("percent")
        current_percent = current_metric.get("percent")
        delta = None if baseline_percent is None or current_percent is None else round(current_percent - baseline_percent, 1)
        rows.append({
            "Capability": label,
            "Baseline": _metric_text(baseline_metric),
            "AI Scroll": _metric_text(current_metric),
            "Improvement": "—" if delta is None else f"{delta:+.1f} pp",
        })
    return rows


def primary_metrics(evaluation: dict) -> list[dict]:
    metrics = evaluation["systems"][SYSTEM_CURRENT]["metrics"]
    return [
        _summary("High-priority deadline recall", metrics["high_priority_deadline_recall"]),
        _summary("Exact deadline", metrics["deadline_exact_on_deadline_cases"]),
        _summary("Calendar action", metrics["calendar_action"]),
        _summary("Cross-email final state", metrics["cross_email_merging"]),
    ]


def filter_errors(errors: list[dict], *, split: str = "all", field: str = "all") -> list[dict]:
    return [
        row for row in errors
        if (split == "all" or row["split"] == split)
        and (field == "all" or row["field"] == field)
    ]


def error_counts(errors: list[dict]) -> list[dict]:
    counts = Counter(row["field"] for row in errors)
    return [
        {"Field": field.replace("_", " ").title(), "Errors": count}
        for field, count in counts.most_common()
    ]


def _summary(label: str, metric: dict) -> dict:
    return {
        "label": label,
        "value": "N/A" if metric.get("percent") is None else f"{metric['percent']:.1f}%",
        "detail": f"{metric['correct']}/{metric['total']} cases",
    }


def _metric_text(metric: dict) -> str:
    percent = metric.get("percent")
    if percent is None:
        return f"{metric['correct']}/{metric['total']} (N/A)"
    return f"{metric['correct']}/{metric['total']} ({percent:.1f}%)"
