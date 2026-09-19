#!/usr/bin/env python3
"""Export the live Velvet Factory office Sheets to a private CI artifact.

No values are printed to stdout. Authentication is a short-lived GOOGLE_TOKEN
minted by GitHub OIDC/WIF. The artifact is an execution input, not a new SoT.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = ROOT / "office" / "ledger" / "bindings.json"
OUT = ROOT / "out" / "antigravity-live-context.json"


def main() -> int:
    token = (os.environ.get("GOOGLE_TOKEN") or "").strip()
    if not token:
        raise SystemExit("GOOGLE_TOKEN missing")

    bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
    workbooks = bindings.get("workbooks") or {}
    creds = Credentials(token=token)
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)

    payload: dict[str, object] = {
        "schema": "velvet.antigravity.live_context.v1",
        "authority": "Google Sheets provider snapshot; ephemeral CI artifact",
        "workbooks": {},
    }

    for key in ("jobs", "sku", "quotes", "books"):
        row = workbooks.get(key) or {}
        spreadsheet_id = row.get("spreadsheetId")
        if not spreadsheet_id:
            raise SystemExit(f"missing spreadsheetId for {key}")

        meta = (
            sheets.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="properties.title,sheets.properties")
            .execute()
        )
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK live context exported: workbooks={len(payload['workbooks'])} path={OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
