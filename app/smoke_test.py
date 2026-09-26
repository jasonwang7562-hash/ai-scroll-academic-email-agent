from datetime import datetime
from zoneinfo import ZoneInfo

from app.extractor import demo_extract
from app.models import EmailInput
from app.sample_data import SAMPLE_BODY, SAMPLE_SENDER, SAMPLE_SUBJECT


def main() -> None:
    result = demo_extract(
        EmailInput(subject=SAMPLE_SUBJECT, sender=SAMPLE_SENDER, body=SAMPLE_BODY),
        now=datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("Asia/Singapore")),
    )
    assert result.course == "PE6201"
    assert result.deadline_iso == "2026-10-04T23:59:00+08:00"
    assert result.evidence_quote in SAMPLE_BODY
    assert result.calendar_action == "create"
    print(result.model_dump_json(indent=2))
    print("\nSMOKE TEST PASSED: no external account was changed.")


if __name__ == "__main__":
    main()

