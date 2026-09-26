#!/usr/bin/env python3
"""Read-only Cloudflare Instagram Publisher snapshot for Morning Green.

Never schedules, cancels or publishes. Never prints the control token.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://velvetos-instagram-publisher.velvetos-vf.workers.dev"

def get_json(base: str, path: str, token: str):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def iso_utc(value: object) -> str:
    try:
        ts = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid scheduled_at epoch: {value!r}") from exc
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")

def main() -> int:
    ap = argparse.ArgumentParser(description="Read canonical Publisher schedules for Morning Green")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    token = (os.environ.get("CLOUDFLARE_PUBLISHER_CONTROL_TOKEN") or "").strip()
    if not token:
        print("no token: set CLOUDFLARE_PUBLISHER_CONTROL_TOKEN", file=os.sys.stderr)
        return 2
    if args.days < 1 or args.days > 60:
        print("--days must be 1..60", file=os.sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    end = now + dt.timedelta(days=args.days)
    listing = get_json(args.base, "/v1/jobs", token)
    jobs = listing.get("jobs") if isinstance(listing, dict) else None
    if not isinstance(jobs, list):
        raise RuntimeError("publisher /v1/jobs returned no jobs list")

    rows = []
    for item in jobs:
        if str(item.get("status") or "") not in {"scheduled", "retry"}:
            continue
        scheduled = dt.datetime.fromtimestamp(int(item["scheduled_at"]), dt.timezone.utc)
        if not (now <= scheduled < end):
            continue
        job_id = str(item.get("id") or "").strip()
        detail = get_json(args.base, f"/v1/jobs/{job_id}", token)
        job = detail.get("job") if isinstance(detail, dict) else None
        if not isinstance(job, dict):
            raise RuntimeError(f"publisher job detail missing: {job_id}")
        media = job.get("media")
        if not isinstance(media, list) or not media:
            raise RuntimeError(f"publisher scheduled job has no media: {job_id}")
        safe_media = []
        for m in media:
            url = str(m.get("url") or "").strip()
            sha = str(m.get("sha256") or "").strip().lower()
            if not url.startswith("https://") or len(sha) != 64:
                raise RuntimeError(f"publisher scheduled job has invalid media binding: {job_id}")
            safe_media.append({"key": str(m.get("key") or ""), "url": url, "sha256": sha})
        kind = str(job.get("kind") or "").strip().lower()
        rows.append({
            "publication_id": job_id,
            "title": str(job.get("content_id") or job_id),
            "scheduled_at": iso_utc(job.get("scheduled_at")),
            "status": str(job.get("status") or ""),
            "content_profile": "carousel" if kind == "carousel" else "post",
            "thumbnail_url": safe_media[0]["url"],
            "thumbnail_cid": None,
            "media": safe_media,
        })

    rows.sort(key=lambda r: r["scheduled_at"])
    payload = {
        "schema": "velvet.morning_brief.publisher_snapshot.v1",
        "authority": "packages/vfigos/PUBLISHER.json",
        "endpoint": args.base,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "window_days": args.days,
        "scheduled": rows,
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw + "\n", encoding="utf-8")
        print(args.output)
    else:
        print(raw)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
