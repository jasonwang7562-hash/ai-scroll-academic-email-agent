import importlib.util
from pathlib import Path


def load_runner():
    path = Path(__file__).resolve().parents[1] / "04_evaluation" / "run_final_evaluation.py"
    spec = importlib.util.spec_from_file_location("run_final_evaluation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_final_run_is_blocked_without_frozen_labels(monkeypatch):
    for name in ("AI_SCROLL_API_KEY", "AI_SCROLL_BASE_URL", "AI_SCROLL_MODEL"):
        monkeypatch.delenv(name, raising=False)
    checks = load_runner().preflight()
    assert checks["ready"] is False
    assert checks["frozen_labels_present"] is False
    assert set(checks["missing_environment_variables"]) == {
        "AI_SCROLL_API_KEY", "AI_SCROLL_BASE_URL", "AI_SCROLL_MODEL"
    }
