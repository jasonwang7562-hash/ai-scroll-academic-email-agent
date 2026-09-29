from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


def test_explicit_confirmation_records_one_demo_event():
    app = AppTest.from_file(str(APP)).run(timeout=10)
    confirm = next(button for button in app.button if button.label.startswith("Confirm reviewed event"))
    confirm.click().run(timeout=10)
    assert not list(app.exception)
    assert len(app.session_state["calendar_events"]) == 1
    assert any("Approved event recorded" in message.value for message in app.success)
    assert any("No external calendar was changed" in caption.value for caption in app.caption)


def test_ambiguous_ui_scenario_is_blocked_before_confirmation():
    app = AppTest.from_file(str(APP)).run(timeout=10)
    app.selectbox[0].select("Ambiguous next Friday").run(timeout=10)
    assert not list(app.exception)
    assert any("Calendar action blocked" in warning.value for warning in app.warning)
    assert not any(button.label.startswith("Confirm reviewed event") for button in app.button)
