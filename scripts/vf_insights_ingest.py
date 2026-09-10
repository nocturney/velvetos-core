#!/usr/bin/env python3
"""Ingest verified Instagram MCP Insights into vfinsights canonical data.

Never invent. Missing/unsupported metric → empty cell / אין ספירה / unknown.
Zero is only written when Meta returned an explicit 0.

Usage:
  python3 scripts/vf_insights_ingest.py --from-json PATH
  python3 scripts/vf_insights_ingest.py --account-json PATH [--media-json PATH]
  python3 packages/vfinsights/scripts/vf_insights_loop.py   # after ingest
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "packages" / "vfinsights" / "data"
POSTS = DATA / "posts.csv"
ACCOUNT_SNAP = DATA / "account-insights-latest.json"
RECEIPT = DATA / "ingest-receipt.json"
LEARNINGS = ROOT / "packages" / "vfinsights" / "LEARNINGS.md"
FIELDS = ["post_id", "date", "type", "reach", "likes", "saves", "comments", "caption_style", "views", "shares", "source"]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metric_value(entry: dict[str, Any]) -> Any:
    """Extract a scalar from Graph-style insight entry. None = unknown (not zero)."""
    if not entry:
        return None
    if "total_value" in entry and isinstance(entry["total_value"], dict):
        if "value" in entry["total_value"]:
            return entry["total_value"]["value"]
    values = entry.get("values")
    if isinstance(values, list) and values:
        # prefer latest end_time
        last = values[-1]
        if isinstance(last, dict) and "value" in last:
            return last["value"]
    if "value" in entry:
        return entry["value"]
    return None


def parse_account_insights(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("ok", True) and not payload.get("insights"):
        return {
            "ok": False,
            "metrics": {},
            "unknown": list(payload.get("metrics_requested") or []),
            "note": "account insights not ok — אין ספירה",
        }
    metrics: dict[str, Any] = {}
    unknown: list[str] = []
    fetched = set(payload.get("metrics_fetched") or [])
    for name in payload.get("metrics_requested") or []:
        if name not in fetched:
            unknown.append(name)
    by_name = {row.get("name"): row for row in (payload.get("insights") or []) if row.get("name")}
    for name, row in by_name.items():
        val = _metric_value(row)
        if val is None:
            unknown.append(name)
        else:
            metrics[name] = val
    # follower_count requested but empty insights list → unknown (privacy floor)
    for name in payload.get("metrics_requested") or []:
        if name not in metrics and name not in unknown:
            unknown.append(name)
    return {
        "ok": True,
        "period": payload.get("period"),
        "metrics": metrics,
        "unknown": sorted(set(unknown)),
        "graph_compat": payload.get("graph_compat"),
        "raw_ok": payload.get("ok"),
        "rule": "unknown ≠ 0; only verified scalars stored",
    }


def parse_media_insights(payload: dict[str, Any], *, media_id: str, media_type: str = "", date: str = "") -> dict[str, str]:
    row = {k: "" for k in FIELDS}
    row["post_id"] = media_id
    row["date"] = date or datetime.now(timezone.utc).date().isoformat()
    row["type"] = media_type or payload.get("media_type") or ""
    row["source"] = "instagram_mcp"
    insights = {r.get("name"): r for r in (payload.get("insights") or []) if r.get("name")}
    mapping = {
        "reach": "reach",
        "likes": "likes",
        "saved": "saves",
        "saves": "saves",
        "comments": "comments",
        "views": "views",
        "shares": "shares",
        "total_interactions": None,  # account-ish; keep out of posts unless needed
    }
    for graph_name, col in mapping.items():
        if col is None:
            continue
        if graph_name not in insights:
            continue
        val = _metric_value(insights[graph_name])
        if val is None:
            row[col] = ""  # אין ספירה
        else:
            row[col] = str(val)
    return row


def load_posts() -> list[dict[str, str]]:
    if not POSTS.is_file():
        return []
    with POSTS.open(encoding="utf-8-sig", newline="") as fh:
        rows = []
        for raw in csv.DictReader(fh):
            rows.append({k: (raw.get(k) or "").strip() for k in FIELDS if k in FIELDS or True})
            # normalize
            rows[-1] = {k: (raw.get(k) or "").strip() for k in set(FIELDS) | set(raw.keys())}
        # ensure fields
        out = []
        for r in rows:
            out.append({k: (r.get(k) or "") for k in FIELDS})
        return out


def upsert_post(row: dict[str, str]) -> list[dict[str, str]]:
    rows = load_posts()
    found = False
    for existing in rows:
        if existing.get("post_id") == row["post_id"]:
            for k, v in row.items():
                if v != "":
                    existing[k] = v
                # explicit empty from MCP means unknown — do not coerce to 0
            found = True
            break
    if not found:
        rows.append({k: row.get(k, "") for k in FIELDS})
    POSTS.parent.mkdir(parents=True, exist_ok=True)
    with POSTS.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    return rows


def write_account_snapshot(parsed: dict[str, Any], raw: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    snap = {
        "ingestedAt": now_utc(),
        "source": "instagram_mcp.get_account_insights",
        "parsed": parsed,
        "raw_period": raw.get("period"),
        "raw_ok": raw.get("ok"),
        "rule": "verified only; unknown metrics listed — never invent",
    }
    ACCOUNT_SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_receipt(payload: dict[str, Any]) -> None:
    RECEIPT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh_learnings() -> dict[str, Any]:
    loop = ROOT / "packages" / "vfinsights" / "scripts" / "vf_insights_loop.py"
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(loop), "--data", str(POSTS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {"ok": proc.returncode == 0, "stdout": (proc.stdout or "")[:1000], "stderr": (proc.stderr or "")[:400]}


def ingest_account(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    parsed = parse_account_insights(raw)
    write_account_snapshot(parsed, raw)
    return parsed


def ingest_media(path: Path, *, media_id: str, media_type: str = "", date: str = "") -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    row = parse_media_insights(raw, media_id=media_id, media_type=media_type, date=date)
    upsert_post(row)
    return {"row": row, "ok": True}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-json", help="account insights JSON from Instagram MCP")
    p.add_argument("--account-json", help="alias of --from-json")
    p.add_argument("--media-json", help="media insights JSON")
    p.add_argument("--media-id", default="")
    p.add_argument("--media-type", default="")
    p.add_argument("--date", default="")
    p.add_argument("--refresh-learnings", action="store_true")
    args = p.parse_args(argv)

    account_path = args.from_json or args.account_json
    receipt: dict[str, Any] = {"at": now_utc(), "source": "vf_insights_ingest"}
    if account_path:
        parsed = ingest_account(Path(account_path))
        receipt["account"] = parsed
    if args.media_json:
        if not args.media_id:
            print("FAIL --media-json requires --media-id", file=sys.stderr)
            return 2
        media = ingest_media(
            Path(args.media_json),
            media_id=args.media_id,
            media_type=args.media_type,
            date=args.date,
        )
        receipt["media"] = media
    if args.refresh_learnings or account_path or args.media_json:
        receipt["learnings"] = refresh_learnings()
    if not account_path and not args.media_json:
        print("FAIL need --from-json and/or --media-json", file=sys.stderr)
        return 2
    write_receipt(receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
