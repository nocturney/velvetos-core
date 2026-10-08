#!/usr/bin/env python3
"""Read-only Cloudflare Instagram Publisher schedule snapshot for Morning Green."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "https://velvetos-instagram-publisher.velvetos-vf.workers.dev"
PROJECT_STATE = Path(r"D:\Velvet\State\OfficeV2\project-state\CURRENT.json")
PILOT_CHECKPOINT = "office-v2-phase3b-v0-cp016-pilot-active"
PRODUCTION_CHECKPOINT = "office-v2-phase3b-v0-cp017-production-read-active"


def snapshot_route(pointer_path: Path = PROJECT_STATE) -> str:
    """An absent Office v2 runtime keeps the incumbent; an invalid known runtime fails closed."""
    if not pointer_path.exists():
        return "INCUMBENT"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8-sig"))
    if pointer.get("schema") != "velvetos.office-v2.project-state-pointer.v0" or pointer.get("gate") != "GREEN":
        raise RuntimeError("Office v2 project-state pointer invalid or not GREEN")
    checkpoint_id = pointer.get("checkpoint_id")
    expected = {
        PILOT_CHECKPOINT: ("PHASE_3B_PILOT_ACTIVE", "INCUMBENT", "checkpoint-016-v0-phase3b-pilot-active.json"),
        PRODUCTION_CHECKPOINT: ("PHASE_3B_PRODUCTION_READ_ACTIVE", "OFFICEV2_PRODUCTION_READ", "checkpoint-017-v0-phase3b-production-read-active.json"),
    }.get(checkpoint_id)
    if expected is None or pointer.get("phase") != expected[0]:
        raise RuntimeError("Office v2 checkpoint/phase is not a recognized reader route")
    checkpoint_path = pointer_path.parent / expected[2]
    ref = str(pointer.get("current_checkpoint_ref") or "").replace("\\", "/")
    if ref.casefold() != str(checkpoint_path).replace("\\", "/").casefold():
        raise RuntimeError("Office v2 checkpoint reference mismatch")
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8-sig"))
    content = dict(checkpoint)
    declared_hash = content.pop("content_hash", None)
    calculated_hash = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if (checkpoint.get("schema_version") != "velvetos.office-v2.project-state.v0"
            or checkpoint.get("checkpoint_id") != checkpoint_id
            or checkpoint.get("migration_phase") != expected[0]
            or (checkpoint.get("gate_status") or {}).get("verdict") != "GREEN"
            or not declared_hash or calculated_hash != declared_hash
            or pointer.get("content_hash") != declared_hash):
        raise RuntimeError("Office v2 checkpoint integrity or gate verification failed")
    return expected[1]

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
    route=snapshot_route()
    if route == "OFFICEV2_PRODUCTION_READ":
        # Never fall back to the incumbent control credential if the secure route fails.
        if args.base_url.rstrip("/") != DEFAULT_URL:
            raise RuntimeError("Office v2 production read forbids publisher endpoint override")
        if __package__:
            from .officev2_secure_publisher_snapshot import DEFAULT_RESOLVER, secure_snapshot
        else:
            from officev2_secure_publisher_snapshot import DEFAULT_RESOLVER, secure_snapshot
        data=secure_snapshot(DEFAULT_RESOLVER, "Production")
    else:
        try:
            token=resolve_token()
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        data=snapshot(args.base_url, token)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"OK source={data['source']} scheduled={len(data['scheduled'])} reader_route={route}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
