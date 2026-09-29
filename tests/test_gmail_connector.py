import base64

from app.gmail_connector import gmail_message_to_email


def encoded(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def test_gmail_message_conversion_prefers_plain_text_part():
    message = {
        "snippet": "fallback",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "PE6201 deadline update"},
                {"name": "From", "value": "Course Team <course@example.edu>"},
                {"name": "Date", "value": "Tue, 29 Sep 2026 10:00:00 +0800"},
            ],
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": encoded("Due 4 October.")}},
                {"mimeType": "text/html", "body": {"data": encoded("<b>Due</b>")}},
            ],
        },
    }

    email = gmail_message_to_email(message)

    assert email.subject == "PE6201 deadline update"
    assert email.sender == "Course Team <course@example.edu>"
    assert email.body == "Due 4 October."
    assert email.sent_at == "2026-09-29T10:00:00+08:00"


def test_gmail_message_conversion_uses_snippet_when_body_is_missing():
    email = gmail_message_to_email(
        {"snippet": "PE6201 report is due tomorrow.", "payload": {"headers": []}}
    )

    assert email.subject == "(No subject)"
    assert email.body == "PE6201 report is due tomorrow."
