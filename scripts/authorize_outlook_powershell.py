from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.outlook_connector import outlook_graph_marker_path  # noqa: E402


def main() -> int:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        print("PowerShell is required.")
        return 1
    command = (
        "$ErrorActionPreference='Stop'; Import-Module Microsoft.Graph.Authentication; "
        "Connect-MgGraph -TenantId 'consumers' -Scopes 'Mail.Read' -NoWelcome -ContextScope CurrentUser; "
        "$ctx=Get-MgContext; $ctx | Select-Object Account,TenantId,Scopes | ConvertTo-Json -Compress"
    )
    completed = subprocess.run([shell, "-NoProfile", "-Command", command], text=True)
    if completed.returncode != 0:
        return completed.returncode
    marker = outlook_graph_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps({"authorized_at": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    print(f"Outlook authorization marker saved to: {marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
