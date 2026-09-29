from pathlib import Path

from app.evaluation_reporting import (
    comparison_rows,
    error_counts,
    filter_errors,
    load_errors,
    load_evaluation,
    primary_metrics,
)


ROOT = Path(__file__).resolve().parents[1]


def test_formal_evaluation_summary_preserves_denominators_and_deltas():
    evaluation = load_evaluation(ROOT / "04_evaluation" / "outputs" / "development_metrics.json")
    rows = comparison_rows(evaluation)
    task_row = next(row for row in rows if row["Capability"] == "Task type")
    assert task_row == {
        "Capability": "Task type",
        "Baseline": "28/50 (56.0%)",
        "AI Scroll": "43/50 (86.0%)",
        "Improvement": "+30.0 pp",
    }
    assert primary_metrics(evaluation)[0]["detail"] == "6/7 cases"


def test_split_comparison_excludes_metrics_without_split_denominators():
    evaluation = load_evaluation(ROOT / "04_evaluation" / "outputs" / "development_metrics.json")
    rows = comparison_rows(evaluation, split="test")
    assert all(row["Capability"] != "Cross-email merge" for row in rows)
    assert next(row for row in rows if row["Capability"] == "Exact deadline")["AI Scroll"] == "12/14 (85.7%)"


def test_error_explorer_filters_current_pipeline_errors():
    errors = load_errors(ROOT / "04_evaluation" / "outputs" / "development_errors.csv")
    filtered = filter_errors(errors, split="test", field="deadline_iso")
    assert filtered
    assert all(row["system"] == "deterministic_dev_pipeline_v1" for row in filtered)
    assert all(row["split"] == "test" and row["field"] == "deadline_iso" for row in filtered)
    assert sum(row["Errors"] for row in error_counts(errors)) == len(errors)
