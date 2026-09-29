from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

import requests

from app.models import EmailInput


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MICROSOFT_SCOPES = ["Mail.Read"]
ROOT = Path(__file__).resolve().parents[1]


def _configured_path(env_name: str, fallback: str) -> Path:
    raw = os.getenv(env_name, fallback)
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def microsoft_token_path() -> Path:
    return _configured_path(
        "AI_SCROLL_MICROSOFT_TOKEN", "data/private/microsoft_token_cache.json"
    )


def microsoft_config_path() -> Path:
    return _configured_path(
        "AI_SCROLL_MICROSOFT_CONFIG", "data/private/microsoft_oauth.json"
    )


def _local_config() -> dict:
    path = microsoft_config_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def microsoft_client_id() -> str:
    return os.getenv("AI_SCROLL_MICROSOFT_CLIENT_ID", "").strip() or str(
        _local_config().get("client_id", "")
    ).strip()


def microsoft_tenant_id() -> str:
    return os.getenv("AI_SCROLL_MICROSOFT_TENANT_ID", "").strip() or str(
        _local_config().get("tenant_id", "common")
    ).strip() or "common"


def save_microsoft_config(client_id: str, tenant_id: str = "common") -> Path:
    path = microsoft_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"client_id": client_id.strip(), "tenant_id": tenant_id.strip() or "common"},
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def outlook_is_configured() -> bool:
    return bool(microsoft_client_id())


def outlook_is_authorized() -> bool:
    return outlook_is_configured() and microsoft_token_path().is_file()


def _body_text(message: dict) -> str:
    body = message.get("body", {})
    content = body.get("content", "")
    if body.get("contentType", "").lower() == "html":
        content = re.sub(r"<style[\s\S]*?</style>|<script[\s\S]*?</script>", " ", content, flags=re.I)
        content = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", content, flags=re.I)
        content = re.sub(r"<[^>]+>", " ", content)
        content = html.unescape(content)
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"\s+([.,;:!?])", r"\1", content)
        content = re.sub(r"\n\s*\n+", "\n", content)
    return content.strip() or message.get("bodyPreview", "").strip() or "(Empty message)"


def graph_message_to_email(message: dict) -> EmailInput:
    sender = message.get("from", {}).get("emailAddress", {})
    sender_value = sender.get("address", "")
    if sender.get("name"):
        sender_value = f'{sender["name"]} <{sender_value}>' if sender_value else sender["name"]
    return EmailInput(
        subject=message.get("subject") or "(No subject)",
        sender=sender_value,
        body=_body_text(message),
        sent_at=message.get("receivedDateTime"),
    )


def _load_cache():
    try:
        import msal
    except ImportError as exc:
        raise RuntimeError(
            "Microsoft OAuth dependency is missing. Run: pip install -r requirements.txt"
        ) from exc
    cache = msal.SerializableTokenCache()
    path = microsoft_token_path()
    if path.is_file():
        cache.deserialize(path.read_text(encoding="utf-8"))
    return cache


def acquire_outlook_token_silent() -> str:
    try:
        import msal
    except ImportError as exc:
        raise RuntimeError(
            "Microsoft OAuth dependency is missing. Run: pip install -r requirements.txt"
        ) from exc
    if not microsoft_client_id():
        raise RuntimeError("Microsoft client ID is not configured.")
    cache = _load_cache()
    app = msal.PublicClientApplication(
        microsoft_client_id(),
        authority=f"https://login.microsoftonline.com/{microsoft_tenant_id()}",
        token_cache=cache,
    )
    accounts = app.get_accounts()
    result = app.acquire_token_silent(MICROSOFT_SCOPES, account=accounts[0]) if accounts else None
    if not result or "access_token" not in result:
        raise RuntimeError("Outlook is not authorized yet. Run scripts/authorize_outlook.py first.")
    if cache.has_state_changed:
        path = microsoft_token_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cache.serialize(), encoding="utf-8")
    return result["access_token"]


class OutlookMailboxConnector:
    """Read-only Outlook / Microsoft 365 connector using Microsoft Graph."""

    name = "Outlook (read only)"

    def __init__(self, *, max_results: int = 100):
        self.max_results = min(max_results, 100)

    def fetch_new(self) -> list[EmailInput]:
        response = requests.get(
            f"{GRAPH_BASE_URL}/me/mailFolders/inbox/messages",
            headers={"Authorization": f"Bearer {acquire_outlook_token_silent()}"},
            params={
                "$top": self.max_results,
                "$orderby": "receivedDateTime desc",
                "$select": "subject,from,receivedDateTime,body,bodyPreview",
            },
            timeout=60,
        )
        if not response.ok:
            raise RuntimeError(f"Microsoft Graph request failed ({response.status_code}): {response.text[:300]}")
        return [graph_message_to_email(item) for item in response.json().get("value", [])]
