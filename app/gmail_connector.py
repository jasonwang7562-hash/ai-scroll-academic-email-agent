from __future__ import annotations

import base64
import json
import os
from email.utils import parsedate_to_datetime
from pathlib import Path

from app.models import EmailInput


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
ROOT = Path(__file__).resolve().parents[1]


def _configured_path(env_name: str, fallback: str) -> Path:
    raw = os.getenv(env_name, fallback)
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def client_secrets_path() -> Path:
    return _configured_path(
        "AI_SCROLL_GOOGLE_CLIENT_SECRETS", "data/private/google_client_secret.json"
    )


def gmail_token_path() -> Path:
    return _configured_path("AI_SCROLL_GMAIL_TOKEN", "data/private/gmail_token.json")


def gmail_is_authorized() -> bool:
    return gmail_token_path().is_file()


def _decode_base64url(value: str) -> str:
    if not value:
        return ""
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode(
        "utf-8", errors="replace"
    )


def _plain_text(payload: dict) -> str:
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime_type == "text/plain" and body.get("data"):
        return _decode_base64url(body["data"])

    for part in payload.get("parts", []):
        text = _plain_text(part)
        if text:
            return text

    if body.get("data"):
        return _decode_base64url(body["data"])
    return ""


def gmail_message_to_email(message: dict) -> EmailInput:
    payload = message.get("payload", {})
    headers = {
        item.get("name", "").lower(): item.get("value", "")
        for item in payload.get("headers", [])
    }
    sent_at = None
    if headers.get("date"):
        try:
            sent_at = parsedate_to_datetime(headers["date"]).isoformat()
        except (TypeError, ValueError):
            sent_at = None

    body = _plain_text(payload).strip() or message.get("snippet", "").strip()
    return EmailInput(
        subject=headers.get("subject", "(No subject)"),
        sender=headers.get("from", ""),
        body=body or "(Empty message)",
        sent_at=sent_at,
    )


class GmailMailboxConnector:
    """Read-only Gmail connector using a locally stored OAuth refresh token."""

    name = "Gmail (read only)"

    def __init__(self, *, max_results: int = 100, query: str = "newer_than:60d"):
        self.max_results = max_results
        self.query = query

    def _credentials(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise RuntimeError(
                "Gmail dependencies are missing. Run: pip install -r requirements.txt"
            ) from exc

        path = gmail_token_path()
        if not path.is_file():
            raise RuntimeError("Gmail is not authorized yet. Run scripts/authorize_gmail.py first.")
        credentials = Credentials.from_authorized_user_file(str(path), [GMAIL_READONLY_SCOPE])
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            path.write_text(credentials.to_json(), encoding="utf-8")
        if not credentials.valid:
            raise RuntimeError("The Gmail authorization is invalid or expired. Authorize again.")
        return credentials

    def fetch_new(self) -> list[EmailInput]:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Gmail dependencies are missing. Run: pip install -r requirements.txt"
            ) from exc

        service = build("gmail", "v1", credentials=self._credentials(), cache_discovery=False)
        response = (
            service.users()
            .messages()
            .list(userId="me", q=self.query, maxResults=self.max_results)
            .execute()
        )
        messages = []
        for item in response.get("messages", []):
            raw = (
                service.users()
                .messages()
                .get(userId="me", id=item["id"], format="full")
                .execute()
            )
            messages.append(gmail_message_to_email(raw))
        return messages
