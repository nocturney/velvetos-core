#!/usr/bin/env python3
"""Read-only Cloudflare Instagram Publisher schedule snapshot for Morning Green."""
from __future__ import annotations
import argparse, json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "https://velvetos-instagram-publisher.velvetos-vf.workers.dev"

def get_json(base: str, path: str, token: str) -> dict:
    req=urllib.request.Request(base.rstrip("/") + path, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def iso(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00","Z")

def snapshot(base: str, token: str) -> dict:
    listing=get_json(base, "/v1/jobs", token)
    scheduled=[]
    for row in listing.get("jobs") or []:
        if row.get("status") not in {"scheduled","retry"}:
            continue
        jid=str(row.get("id") or "")
        detail=get_json(base, "/v1/jobs/" + jid, token).get("job") or {}
        media=detail.get("media") or []
        first=media[0] if media else {}
        scheduled.append({
            "publication_id": jid,
            "title": detail.get("content_id") or row.get("content_id") or jid,
            "scheduled_at": iso(detail.get("scheduled_at") or row.get("scheduled_at")),
            "content_profile": detail.get("kind") or row.get("kind") or "post",
            "thumbnail_url": first.get("url") or "",
            "status": detail.get("status") or row.get("status"),
            "source": "cloudflare-instagram-publisher",
        })
    scheduled.sort(key=lambda x: x["scheduled_at"])
    return {
        "schema": "vf.instagram.schedule-snapshot.v1",
        "source": "cloudflare-instagram-publisher",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "scheduled": scheduled,
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--base-url", default=os.environ.get("VELVET_INSTAGRAM_PUBLISHER_URL", DEFAULT_URL))
    args=ap.parse_args()
    token=(os.environ.get("VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN") or "").strip()
    if not token:
        raise SystemExit("missing VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN")
    data=snapshot(args.base_url, token)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"OK source={data['source']} scheduled={len(data['scheduled'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
