from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.outlook_connector import (  # noqa: E402
    MICROSOFT_SCOPES,
    microsoft_client_id,
    microsoft_token_path,
    outlook_device_flow_path,
    outlook_graph_marker_path,
)


def main() -> int:
    try:
        import msal
    except ImportError:
        print("Install dependencies first: python -m pip install -r requirements.txt")
        return 1

    status_path = outlook_device_flow_path()
    status_path.parent.mkdir(parents=True, exist_ok=True)
    cache = msal.SerializableTokenCache()
    app = msal.PublicClientApplication(
        microsoft_client_id(),
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )
    flow = app.initiate_device_flow(scopes=MICROSOFT_SCOPES)
    if "user_code" not in flow:
        status_path.write_text(
            json.dumps({"status": "error", "message": flow.get("error_description", "Microsoft did not start device authorization.")}),
            encoding="utf-8",
        )
        return 2
    status_path.write_text(
        json.dumps(
            {
                "status": "waiting",
                "user_code": flow["user_code"],
                "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
                "message": flow.get("message", "Enter the code on the Microsoft device login page."),
                "expires_in": flow.get("expires_in"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        status_path.write_text(
            json.dumps({"status": "error", "message": result.get("error_description", "Microsoft authorization failed.")}),
            encoding="utf-8",
        )
        return 3
    token_path = microsoft_token_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(cache.serialize(), encoding="utf-8")
    marker = outlook_graph_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps({"authorized_at": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    status_path.write_text(
        json.dumps({"status": "authorized", "authorized_at": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    print(f"Outlook authorization saved to: {token_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
