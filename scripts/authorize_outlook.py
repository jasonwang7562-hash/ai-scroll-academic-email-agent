from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.outlook_connector import (  # noqa: E402
    MICROSOFT_SCOPES,
    microsoft_client_id,
    microsoft_tenant_id,
    microsoft_token_path,
)


def main() -> int:
    try:
        import msal
    except ImportError:
        print("Install dependencies first: python -m pip install -r requirements.txt")
        return 1

    client_id = microsoft_client_id()
    if not client_id:
        print("Missing AI_SCROLL_MICROSOFT_CLIENT_ID.")
        print("Register a Microsoft Entra public client app and add its Application (client) ID to .env.")
        return 2

    cache = msal.SerializableTokenCache()
    app = msal.PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{microsoft_tenant_id()}",
        token_cache=cache,
    )
    result = app.acquire_token_interactive(
        scopes=MICROSOFT_SCOPES,
        prompt="select_account",
        parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
    )
    if "access_token" not in result:
        print(f'Authorization failed: {result.get("error_description", result)}')
        return 3
    path = microsoft_token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cache.serialize(), encoding="utf-8")
    print(f"Outlook read-only token cache saved to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
