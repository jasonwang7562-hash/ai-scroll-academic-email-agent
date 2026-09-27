import importlib.util
import json
from pathlib import Path


def load_cost_script():
    path = Path(__file__).resolve().parents[1] / "04_evaluation" / "cost_analysis.py"
    spec = importlib.util.spec_from_file_location("cost_analysis", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_final_usage_jsonl_is_accepted(tmp_path):
    path = tmp_path / "final_model_usage_test.jsonl"
    rows = [
        {"prompt_tokens": 100, "completion_tokens": 20},
        {"prompt_tokens": 0, "completion_tokens": 0},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    assert load_cost_script().live_usage_rows(path) == [rows[0]]
