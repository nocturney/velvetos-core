#!/usr/bin/env python3
"""Read-only Cloudflare Instagram Publisher schedule snapshot for Morning Green."""
from __future__ import annotations
import argparse, json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "https://velvetos-instagram-publisher.velvetos-vf.workers.dev"

def resolve_token() -> str:
    token=(os.environ.get("VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN") or "").strip()
    if token:
        return token
    if os.name != "nt":
        raise RuntimeError("missing VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN")
    appdata=(os.environ.get("APPDATA") or "").strip()
    if not appdata:
        raise RuntimeError("APPDATA unavailable for publisher DPAPI fallback")
    credential=Path(appdata) / "VelvetOS" / "cloudflare-publisher-control.dpapi"
    if not credential.is_file():
        raise RuntimeError("publisher DPAPI credential missing")
    script=(
        "$enc=(Get-Content -Raw $env:VF_PUBLISHER_DPAPI).Trim();"
        "$sec=ConvertTo-SecureString $enc;"
        "$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec);"
        "try {[Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)} "
        "finally {[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)}"
    )
    env=dict(os.environ)
    env["VF_PUBLISHER_DPAPI"]=str(credential)
    proc=subprocess.run(
        ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-Command",script],
        text=True, capture_output=True, timeout=20, env=env,
    )
    token=(proc.stdout or "").strip()
    if proc.returncode != 0 or len(token) < 32:
        raise RuntimeError("publisher DPAPI credential could not be decrypted")
    return token

def get_json(base: str, path: str, token: str) -> dict:
    req=urllib.request.Request(base.rstrip("/") + path, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "VelvetOS-Morning-Green/1.0",
    }, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def iso(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00","Z")

def snapshot(base: str, token: str) -> dict:
    observed=datetime.now(timezone.utc)
    runtime=get_json(base, "/v1/runtime", token)
    tick=int(runtime.get("last_cron_tick") or 0)
    heartbeat_age=max(0, int(observed.timestamp()) - tick) if tick else None
    if heartbeat_age is None or heartbeat_age > 180:
        raise RuntimeError(f"publisher cron heartbeat stale/missing: age={heartbeat_age}")
    meta=get_json(base, "/v1/meta-health", token)
    if meta.get("ok") is not True:
        raise RuntimeError("publisher Meta health failed")
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
        "observed_at": observed.isoformat().replace("+00:00","Z"),
        "runtime": {
            "last_cron_tick": tick,
            "heartbeat_age_seconds": heartbeat_age,
            "job_counts": runtime.get("job_counts") or [],
        },
        "meta_health": {
            "ok": True,
            "username": str(meta.get("username") or ""),
        },
        "scheduled": scheduled,
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--base-url", default=os.environ.get("VELVET_INSTAGRAM_PUBLISHER_URL", DEFAULT_URL))
    args=ap.parse_args()
    try:
        token=resolve_token()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    data=snapshot(args.base_url, token)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"OK source={data['source']} scheduled={len(data['scheduled'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
