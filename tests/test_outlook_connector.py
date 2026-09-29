from app.outlook_connector import graph_message_to_email


def test_graph_message_conversion_strips_html_and_preserves_sender():
    email = graph_message_to_email(
        {
            "subject": "PE6201 deadline update",
            "from": {"emailAddress": {"name": "Course Team", "address": "course@ntu.edu.sg"}},
            "receivedDateTime": "2026-09-29T04:00:00Z",
            "body": {"contentType": "html", "content": "<p>Submit by <b>4 October</b>.</p>"},
            "bodyPreview": "fallback",
        }
    )

    assert email.subject == "PE6201 deadline update"
    assert email.sender == "Course Team <course@ntu.edu.sg>"
    assert email.body == "Submit by 4 October."
    assert email.sent_at == "2026-09-29T04:00:00Z"


def test_graph_message_conversion_uses_preview_when_body_missing():
    email = graph_message_to_email({"bodyPreview": "PE6201 reminder", "from": {}})

    assert email.subject == "(No subject)"
    assert email.body == "PE6201 reminder"
