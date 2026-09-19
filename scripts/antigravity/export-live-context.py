#!/usr/bin/env python3
"""Export current Velvet Factory office Sheets to an ephemeral JSON context."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = ROOT / "office" / "ledger" / "bindings.json"
DEFAULT_OUT = ROOT / "out" / "antigravity-live-context.json"
DRIVE_ENDPOINT = "https://drivemcp.googleapis.com/mcp/v1"
SHEETS_ENDPOINT = "https://sheetsmcp.googleapis.com/mcp/v1"


def credentials() -> Credentials:
    token = (os.environ.get("GOOGLE_TOKEN") or "").strip()
    if token:
        return Credentials(token=token)

    store = os.environ.get("VELVETOS_ANTIGRAVITY_OAUTH_STORE")
    if not store:
        raise SystemExit("Google auth unavailable: no GOOGLE_TOKEN or Antigravity OAuth store")
    path = Path(store).expanduser()
    if not path.is_file():
        raise SystemExit("Antigravity OAuth store not found")
    payload = json.loads(path.read_text(encoding="utf-8"))
    entry = payload.get(SHEETS_ENDPOINT) or payload.get(DRIVE_ENDPOINT) or {}
    tok = entry.get("token") or {}
    creds = Credentials(
        token=tok.get("access_token"),
        refresh_token=tok.get("refresh_token"),
        token_uri=entry.get("token_url") or "https://oauth2.googleapis.com/token",
        client_id=entry.get("client_id"),
        client_secret=entry.get("client_secret"),
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def main() -> int:
    bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
    workbooks = bindings.get("workbooks") or {}
    sheets = build("sheets", "v4", credentials=credentials(), cache_discovery=False)

    payload: dict[str, object] = {
        "schema": "velvet.antigravity.live_context.v1",
        "authority": "Google Sheets provider snapshot; ephemeral execution input",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "githubRunId": os.environ.get("GITHUB_RUN_ID"),
        "githubSha": os.environ.get("GITHUB_SHA"),
        "workbooks": {},
    }

    for key in ("jobs", "sku", "quotes", "books"):
        row = workbooks.get(key) or {}
        spreadsheet_id = row.get("spreadsheetId")
        if not spreadsheet_id:
            raise SystemExit(f"missing spreadsheetId for {key}")

        meta = sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="properties.title,sheets.properties",
        ).execute()
        tabs = []
        for sheet in meta.get("sheets") or []:
            props = sheet.get("properties") or {}
            title = props.get("title")
            if not title:
                continue
            safe_title = title.replace("'", "''")
            values = (
                sheets.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=f"'{safe_title}'!A1:ZZ")
                .execute()
                .get("values")
                or []
            )
            tabs.append(
                {
                    "title": title,
                    "sheetId": props.get("sheetId"),
                    "rowCount": len(values),
                    "values": values,
                }
            )
        payload["workbooks"][key] = {
            "spreadsheetId": spreadsheet_id,
            "title": (meta.get("properties") or {}).get("title") or row.get("title"),
            "tabs": tabs,
        }

    out = Path(os.environ.get("VELVETOS_LIVE_CONTEXT_OUT") or DEFAULT_OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"OK live context exported: workbooks={len(payload['workbooks'])} "
        f"path={out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
