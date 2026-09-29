from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.gmail_connector import (  # noqa: E402
    GMAIL_READONLY_SCOPE,
    client_secrets_path,
    gmail_token_path,
)


def main() -> int:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install dependencies first: python -m pip install -r requirements.txt")
        return 1

    secrets = client_secrets_path()
    if not secrets.is_file():
        print(f"Missing OAuth client file: {secrets}")
        print("Create a Google OAuth Desktop app, download its JSON, and save it there.")
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets), scopes=[GMAIL_READONLY_SCOPE]
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=True,
        authorization_prompt_message="Opening Google authorization in your browser...",
        success_message="Gmail authorization complete. You can close this tab and return to AI Scroll.",
    )
    token = gmail_token_path()
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Gmail read-only token saved to: {token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
