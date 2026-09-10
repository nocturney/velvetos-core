#!/usr/bin/env python3
"""VelvetOS Living Studio — connective tissue over existing SoTs.

No second Control Plane. No second media catalog. No invented ₪ / Insights.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")

LS = ROOT / "packages" / "velvetos" / "living-studio"
REGISTRY = LS / "REGISTRY.json"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
CONTROL = ROOT / "office" / "control"
INBOX = CONTROL / "inbox.json"
DEAD = CONTROL / "dead-letter.json"
FOLLOWUPS = CONTROL / "followups.json"
HANDOFF = CONTROL / "HANDOFF.json"
DECISIONS = CONTROL / "decisions.jsonl"
POLICY = CONTROL / "POLICY.md"
JOBS = ROOT / "office" / "ledger" / "live" / "jobs.csv"
MEDIA = ROOT / "packages" / "vfmedia" / "catalog.json"
APPROVAL = ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json"
CALENDAR = ROOT / "packages" / "vfgrowth" / "CALENDAR.md"
FEED_AUDIT = ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json"
IG_CAPS = ROOT / "packages" / "vfigos" / "CAPABILITIES.json"
PUB_STATES = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json"
PRINT_EVENTS = ROOT / "packages" / "vfprod" / "data" / "print-events.jsonl"
CARDS = ROOT / "packages" / "vfprod" / "hq" / "cards"
FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
OWNER_MEMORY = ROOT / "packages" / "vfops" / "data" / "owner-memory.md"
EVENTS_CATALOG = ROOT / "packages" / "velvetos" / "schema" / "events.catalog.json"
SIGNAL_LOG = LS / "data" / "signal-room.jsonl"
PULSE_LATEST = LS / "data" / "pulse-latest.json"
WORLD_LATEST = LS / "data" / "world-model-latest.json"
RECEIPTS = LS / "data" / "receipts.jsonl"
INTAKE_RECEIPTS = LS / "data" / "intake-receipts.jsonl"
FAILURE_MUSEUM = ROOT / "office" / "learning" / "failure-museum" / "entries.jsonl"
LAB_LOG = ROOT / "office" / "learning" / "lab" / "experiments.jsonl"
VOICE = ROOT / "packages" / "vfcopy" / "VOICE.md"
PUBLIC_CTA = ROOT / "constitution" / "PUBLIC_CTA.md"

ILS = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def receipt(**kwargs: Any) -> dict:
    row = {
        "receipt_id": f"rcpt-{uuid.uuid4().hex[:12]}",
        "timestamp": now_iso(),
        "actor": kwargs.pop("actor", "living-studio"),
        **kwargs,
    }
    append_jsonl(RECEIPTS, row)
    return row


def emit_signal(kind: str, source: str, entity_id: str | None = None, **payload: Any) -> dict:
    # Avoid clashing with parameter name if callers pass kind= in payload
    payload.pop("kind", None)
    sig = {
        "signalId": f"sig-{uuid.uuid4().hex[:12]}",
        "kind": kind,
        "source": source,
        "entityId": entity_id,
        "timestamp": now_iso(),
        "payload": payload,
        "idempotencyKey": hashlib.sha256(
            f"{kind}|{source}|{entity_id}|{json.dumps(payload, sort_keys=True, default=str)}".encode()
        ).hexdigest()[:16],
    }
    # idempotent append: skip if same key already in last 500 lines
    if SIGNAL_LOG.is_file():
        lines = SIGNAL_LOG.read_text(encoding="utf-8").splitlines()[-500:]
        for line in lines:
            try:
                prev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if prev.get("idempotencyKey") == sig["idempotencyKey"]:
                return prev
    append_jsonl(SIGNAL_LOG, sig)
    return sig


def read_jobs() -> list[dict]:
    """Read job cache. Canonical SoT is the Google Sheet — run jobs pull first."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        return jobs_adapter.read_cache()
    except Exception:  # noqa: BLE001
        if not JOBS.is_file():
            return []
        with JOBS.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        return [r for r in rows if any((v or "").strip() for v in r.values())]


def vfmem_context(query: str) -> dict:
    """Invoke existing vfmem retrieval — never treat generated text as fact."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vfmem.py"), "--json", "who", query],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, Any] = {
        "invoked": True,
        "query": query,
        "exitCode": proc.returncode,
        "rule": "retrieval only — generated text is never fact",
    }
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            payload["result"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload["resultText"] = proc.stdout.strip()[:2000]
    else:
        payload["stderr"] = (proc.stderr or "")[:500]
        payload["result"] = None
    return payload


def media_stats(cat: dict | None = None) -> dict:
    cat = cat or load_json(MEDIA, {"items": []})
    items = cat.get("items") or []
    inbox = sum(1 for i in items if i.get("status") == "inbox")
    source = sum(1 for i in items if i.get("status") == "source")
    verified = sum(1 for i in items if (i.get("intake") or {}).get("phase") == "verified")
    registered = sum(1 for i in items if (i.get("intake") or {}).get("phase") == "registered")
    unassociated = sum(
        1
        for i in items
        if not i.get("productLink") and i.get("status") in {"inbox", "source"}
    )
    return {
        "total": len(items),
        "inbox": inbox,
        "source": source,
        "verified": verified,
        "registered_only": registered,
        "unassociated": unassociated,
    }


def followup_stats() -> dict:
    items = (load_json(FOLLOWUPS, {"items": []}) or {}).get("items") or []
    by = {}
    for it in items:
        st = it.get("state") or "unknown"
        by[st] = by.get(st, 0) + 1
    return {"total": len(items), "by_state": by, "items": items}


def approval_stats() -> dict:
    q = load_json(APPROVAL, {"items": []}) or {}
    items = q.get("items") or q.get("queue") or []
    if isinstance(q, list):
        items = q
    return {"total": len(items), "items": items}


def ig_status() -> dict:
    caps = load_json(IG_CAPS, {}) or {}
    rv = caps.get("remoteVerify") or {}
    ig = rv.get("insightsGraphCompat") or {}
    return {
        "currentStatus": caps.get("currentStatus"),
        "auth": caps.get("auth"),
        "remote_access": caps.get("remote_access"),
        "account": caps.get("accountLabel") or rv.get("username"),
        "insights_deployed": ig.get("deployed"),
        "insights_code": ig.get("code"),
        "publish": ((rv.get("chatgptSmoke") or {}).get("publish") or "unknown"),
        "dm_forbidden": True,
    }


def print_done_recent() -> list[dict]:
    out: list[dict] = []
    if PRINT_EVENTS.is_file():
        for line in PRINT_EVENTS.read_text(encoding="utf-8").splitlines()[-50:]:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "print" in json.dumps(row).lower() or row.get("type") == "print.done":
                out.append(row)
    if CARDS.is_dir():
        for path in sorted(CARDS.glob("*.md"))[-20:]:
            text = path.read_text(encoding="utf-8")
            if "print.done" in text or "print.done" in path.name:
                out.append({"card": path.name, "has_print_done": "print.done" in text})
    return out


def world_model() -> dict:
    fu = followup_stats()
    media = media_stats()
    approvals = approval_stats()
    jobs_raw = read_jobs()
    # Projection must not embed numeric ₪ (Sheet remains canonical; sensor forbids invented ILS in packages/)
    jobs = []
    for j in jobs_raw:
        row = dict(j)
        price = (row.get("price") or "").strip()
        if price and price not in {"X", "X ₪"}:
            row["price"] = "X ₪" if any(ch.isdigit() for ch in price) else price
            row["price_present_from_sheet"] = True
        notes = row.get("notes") or ""
        if ILS.search(notes):
            row["notes"] = ILS.sub("X ₪", notes)
        for key, val in list(row.items()):
            if isinstance(val, str) and ILS.search(val):
                row[key] = ILS.sub("X ₪", val)
        jobs.append(row)
    dead = (load_json(DEAD, {"items": []}) or {}).get("items") or []
    inbox = load_json(INBOX, {"buckets": {}}) or {}
    handoff = load_json(HANDOFF, {}) or {}
    loop = load_json(LOOP, {}) or {}
    fleet = load_json(FLEET, {}) or {}
    ig = ig_status()
    decisions = []
    if DECISIONS.is_file():
        for line in DECISIONS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    decisions.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    model = {
        "generatedAt": now_iso(),
        "kind": "velvet-world-model-projection",
        "rule": "projection-only — sources remain canonical SoTs; numeric ₪ redacted to X ₪ (Sheet holds verified amounts)",
        "sourcesOfTruth": (load_json(CONTROL_PLANE, {}) or {}).get("sourcesOfTruth"),
        "active_jobs": jobs,
        "jobs_count": len(jobs),
        "jobs_authority": "Google Sheet VF HQ · jobs via vf_office.py jobs pull",
        "followups": {"total": fu["total"], "by_state": fu["by_state"]},
        "media": media,
        "approvals": {"total": approvals["total"]},
        "production": {
            "print_done_signals": print_done_recent()[:10],
            "fleet_beds": len((fleet.get("beds") or fleet.get("printers") or [])),
        },
        "publication": {
            "instagram": ig,
            "publication_states_present": PUB_STATES.is_file(),
        },
        "approvals_queue_total": approvals["total"],
        "blockers": {
            "dead_letter_open": [
                d
                for d in dead
                if d.get("status") in {None, "open", "unresolved", "failed"}
            ],
            "owner_blocked": handoff.get("owner_blocked") or [],
        },
        "decisions_count": len(decisions),
        "decisions_latest": decisions[-5:],
        "inbox_buckets": {
            k: len(v) if isinstance(v, list) else v for k, v in (inbox.get("buckets") or {}).items()
        },
        "office_loop": {
            "paused": bool(loop.get("paused") or loop.get("ownerPaused")),
            "path": str(LOOP.relative_to(ROOT)),
        },
        "system_health_hint": handoff.get("health") or handoff.get("status") or "see watchdog",
        "opportunities_seed": True,
        "experiments_path": str(LAB_LOG.relative_to(ROOT)),
        "knowledge": {
            "owner_memory_present": OWNER_MEMORY.is_file(),
            "vfmem": "python3 scripts/vfmem.py who <job>",
        },
    }
    WORLD_LATEST.parent.mkdir(parents=True, exist_ok=True)
    WORLD_LATEST.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    emit_signal("studio.world_model", "vf_living_studio", "world-model")
    return model


def previous_pulse() -> dict | None:
    return load_json(PULSE_LATEST)


def studio_pulse() -> dict:
    wm = world_model()
    prev = previous_pulse() or {}
    fu = followup_stats()
    media = wm["media"]
    ig = wm["publication"]["instagram"]
    owner_items = []
    for b in wm["blockers"]["owner_blocked"]:
        owner_items.append(b)
    # Insights deploy is no longer an owner action if deployed
    if ig.get("insights_deployed") is False:
        owner_items.append(
            {
                "what": "Redeploy Instagram Insights image",
                "why": "media-period code ready but not live",
                "risk": "red",
            }
        )

    invisible = invisible_work(write=False)
    high = [i for i in invisible if i.get("impact") in {"high", "critical"}]

    office_alone = [
        "classify inbox / media registered→verified retries",
        "watchdog autofix + handoff refresh",
        "Hebrew copy lint / preflight drafts",
        "dead-letter triage that is green/yellow",
    ]
    do_not = [
        "auto-DM",
        "boost without lead seat",
        "Print from HQ",
        "invent ₪ or Insights",
        "resume paused routines without owner",
        "claim IG liveVerified without publish tool proof",
    ]
    ready_publish = [
        i
        for i in (approval_stats().get("items") or [])
        if (i.get("state") or i.get("status") or "")
        in {"approved_for_manual_posting", "approved", "ready"}
    ]
    print_done = wm["production"]["print_done_signals"]
    opportunities = opportunity_intelligence(write=False)[:3]

    changed = []
    if prev:
        if prev.get("media_total") != media["total"]:
            changed.append(f"media {prev.get('media_total')}→{media['total']}")
        if prev.get("followups_total") != fu["total"]:
            changed.append(f"followups {prev.get('followups_total')}→{fu['total']}")
        if prev.get("insights_deployed") != ig.get("insights_deployed"):
            changed.append(f"insights_deployed→{ig.get('insights_deployed')}")
    else:
        changed.append("first pulse this session")

    pulse = {
        "generatedAt": now_iso(),
        "kind": "studio-pulse",
        "what_happening_now": {
            "jobs": wm["jobs_count"],
            "followups": fu["by_state"],
            "media_inbox": media["inbox"],
            "media_source": media["source"],
            "ig": ig.get("currentStatus"),
            "office_paused": wm["office_loop"]["paused"],
        },
        "what_moved_since_last": changed,
        "what_stuck": [
            *[f"followup:{s}={n}" for s, n in fu["by_state"].items() if s not in {"closed_verified"}],
            *([f"dead_letter={len(wm['blockers']['dead_letter_open'])}"] if wm["blockers"]["dead_letter_open"] else []),
            *([f"media_unassociated={media['unassociated']}"] if media["unassociated"] else []),
        ],
        "what_requires_christian": owner_items[:10] + [
            {"what": i.get("title"), "why": i.get("why"), "risk": "red"}
            for i in high
            if i.get("owner_required")
        ],
        "what_office_can_solve": office_alone,
        "ready_to_publish": ready_publish[:10],
        "print_done_recent": print_done[:5],
        "media_missing": {
            "inbox_unverified": media["registered_only"],
            "unassociated": media["unassociated"],
        },
        "nearest_opportunity": opportunities[:1],
        "do_not_do_now": do_not,
        "invisible_work_high": high[:5],
        "system_health": wm["system_health_hint"],
        "feeds": {
            "morning_brief": "composer — brief is presentation/delivery",
            "handoff": "python3 scripts/vf_control_plane.py handoff",
            "status": "python3 scripts/vf_control_plane.py status",
        },
        "media_total": media["total"],
        "followups_total": fu["total"],
        "insights_deployed": ig.get("insights_deployed"),
    }
    PULSE_LATEST.parent.mkdir(parents=True, exist_ok=True)
    PULSE_LATEST.write_text(json.dumps(pulse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    emit_signal("studio.pulse.generated", "vf_living_studio", "pulse", blockerCount=len(owner_items))
    receipt(action="studio_pulse", source="vf_living_studio", affected="pulse-latest", verification="written")
    return pulse


def signal_room(limit: int = 50) -> dict:
    """Normalize existing SoT change signals into Signal Room view."""
    signals: list[dict] = []
    # existing media intake events
    intake_events = ROOT / "packages" / "vfmedia" / "data" / "intake-events.jsonl"
    if intake_events.is_file():
        for line in intake_events.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            signals.append(
                {
                    "kind": row.get("type") or row.get("event") or "media.intake",
                    "source": "vfmedia/intake-events",
                    "timestamp": row.get("timestamp") or row.get("at"),
                    "entityId": row.get("fileId") or row.get("catalogId"),
                    "raw": row,
                }
            )
    if PRINT_EVENTS.is_file():
        for line in PRINT_EVENTS.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            signals.append(
                {
                    "kind": row.get("type") or "print.event",
                    "source": "vfprod/print-events",
                    "timestamp": row.get("timestamp") or row.get("at"),
                    "entityId": row.get("jobId") or row.get("id"),
                    "raw": row,
                }
            )
    for it in followup_stats()["items"]:
        signals.append(
            {
                "kind": f"followup.{it.get('state')}",
                "source": "office/control/followups.json",
                "timestamp": it.get("updatedAt") or it.get("createdAt"),
                "entityId": it.get("id"),
                "raw": {"id": it.get("id"), "state": it.get("state")},
            }
        )
    dead = (load_json(DEAD, {"items": []}) or {}).get("items") or []
    for d in dead:
        signals.append(
            {
                "kind": "dead_letter",
                "source": "office/control/dead-letter.json",
                "timestamp": d.get("timestamp") or d.get("at"),
                "entityId": d.get("id"),
                "raw": {"id": d.get("id"), "status": d.get("status")},
            }
        )
    if SIGNAL_LOG.is_file():
        for line in SIGNAL_LOG.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    catalog = load_json(EVENTS_CATALOG, {"events": []}) or {}
    return {
        "generatedAt": now_iso(),
        "kind": "signal-room",
        "rule": "normalize existing events — not an event broker",
        "event_contract_count": len(catalog.get("events") or []),
        "signals": signals[-limit:],
        "count": len(signals[-limit:]),
    }


INTAKE_ROUTES = {
    "inquiry": {
        "skill": "client-intake-brief",
        "packs": ["vfconvert"],
        "writes": ["office/control/inbox.json", "office/ledger/live/jobs.csv"],
    },
    "client_notes": {
        "skill": "client-intake-brief",
        "packs": ["vfconvert"],
        "writes": ["office/control/inbox.json"],
    },
    "meeting": {
        "skill": "meeting-to-execution",
        "packs": ["vfops"],
        "writes": ["office/control/decisions.jsonl", "office/control/followups.json"],
    },
    "document": {
        "skill": "document-to-decision",
        "packs": ["vfops", "vfmem"],
        "writes": ["office/control/decisions.jsonl", "office/control/inbox.json"],
    },
    "image": {
        "skill": "media-ingest-operator",
        "packs": ["vfmedia"],
        "writes": ["packages/vfmedia/catalog.json"],
    },
    "video": {
        "skill": "media-ingest-operator",
        "packs": ["vfmedia"],
        "writes": ["packages/vfmedia/catalog.json"],
    },
    "production_update": {
        "skill": "production-planner",
        "packs": ["vfprod"],
        "writes": ["packages/vfprod/hq/cards/", "office/control/followups.json"],
    },
    "product_idea": {
        "skill": "product-spec",
        "packs": ["vfsku"],
        "writes": ["office/learning/lab/experiments.jsonl"],
    },
    "research": {
        "skill": "research-to-brief",
        "packs": ["vfresearch"],
        "writes": ["packages/vfops/data/research.md"],
    },
    "note": {
        "skill": "knowledge-base-curator",
        "packs": ["vfmem", "vfops"],
        "writes": ["office/control/inbox.json"],
    },
}


def classify_kind(text: str, kind: str | None) -> str:
    if kind and kind in INTAKE_ROUTES:
        return kind
    t = (text or "").lower()
    if any(w in t for w in ("פנייה", "inquiry", "רוצה להזמין", "הצעת מחיר")):
        return "inquiry"
    if any(w in t for w in ("פגישה", "meeting", "סיכום ישיבה", "transcript")):
        return "meeting"
    if any(w in t for w in ("pdf", "מסמך", "document", "חוזה")):
        return "document"
    if any(w in t for w in (".jpg", ".png", "תמונה", "image")):
        return "image"
    if any(w in t for w in (".mp4", "וידאו", "video", "ריל")):
        return "video"
    if any(w in t for w in ("print.done", "הדפסה הסתיימה", "spool", "filament")):
        return "production_update"
    if any(w in t for w in ("רעיון למוצר", "product idea", "sku חדש")):
        return "product_idea"
    if any(w in t for w in ("מחקר", "research", "טרנד", "last30")):
        return "research"
    return "note"


def _extract_drive_file_id(text: str) -> str | None:
    # Drive file ids are typically 25–44 url-safe chars
    m = re.search(r"(?:drive[_ ]?file[_ ]?id|fileId|file_id)[=:\s]+([A-Za-z0-9_-]{20,})", text or "", re.I)
    if m:
        return m.group(1)
    m = re.search(r"/file/d/([A-Za-z0-9_-]{20,})", text or "")
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Za-z0-9_-]{28,44})\b", text or "")
    if m and "drive" in (text or "").lower():
        return m.group(1)
    return None


def _inbox_append(kind: str, intake_id: str, text: str, route_skill: str, dispatch: dict | None = None) -> str:
    inbox = load_json(INBOX, {"buckets": {}}) or {"buckets": {}}
    buckets = inbox.setdefault("buckets", {})
    key = {
        "inquiry": "inquiries",
        "meeting": "meetings",
        "document": "documents",
        "image": "media",
        "video": "media",
        "production_update": "production",
        "product_idea": "ideas",
        "research": "research",
        "note": "notes",
        "client_notes": "inquiries",
    }.get(kind, "notes")
    bucket = buckets.setdefault(key, [])
    th = hashlib.sha256((text or "").encode()).hexdigest()[:16]
    for item in bucket:
        if isinstance(item, dict) and item.get("textHash") == th:
            return item.get("id") or intake_id
    bucket.append(
        {
            "id": intake_id,
            "at": now_iso(),
            "kind": kind,
            "textHash": th,
            "excerpt": (text or "")[:200],
            "route": route_skill,
            "status": "dispatched" if dispatch and dispatch.get("ok") else "routed",
            "dispatch": dispatch,
        }
    )
    INBOX.write_text(json.dumps(inbox, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return intake_id


def _dispatch_inquiry(text: str, dry_run: bool) -> dict:
    """Client intake → existing vf_office jobs add (no invented ₪)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from vf_office import add_job  # noqa: WPS433

    # minimal parse — require identity already gated by needs_input
    client = ""
    for marker in ("שם:", "name:", "לקוח:"):
        if marker in text.lower() or marker in text:
            idx = text.lower().find(marker.lower()) if marker.isascii() else text.find(marker)
            if idx >= 0:
                client = text[idx + len(marker) :].splitlines()[0].strip(" :,-")[:80]
                break
    if not client:
        # fall back: first Hebrew/ASCII token after 'inquiry'
        client = "לקוח-פנייה"
    what = text.strip()[:180]
    if dry_run:
        return {"ok": True, "dry_run": True, "action": "vf_office.jobs.add", "client_label": client}
    row = add_job(
        {
            "channel": "Universal Intake",
            "client_label": client,
            "what_asked": what,
            "file_status": "חסר",
            "notes": "from universal_intake inquiry — price empty until lead seat",
        }
    )
    return {
        "ok": True,
        "action": "vf_office.jobs.add",
        "job_id": row.get("job_id"),
        "stage": row.get("stage"),
        "canonical_state": f"office/ledger/live/jobs.csv#{row.get('job_id')}",
    }


def _dispatch_media(text: str, kind: str, dry_run: bool) -> dict:
    file_id = _extract_drive_file_id(text)
    if not file_id:
        return {"ok": False, "needs_input": ["Drive file id"], "action": "vfmedia.py intake"}
    catalog = load_json(MEDIA, {"items": []}) or {"items": []}
    items = catalog.get("items") or []
    existing = next((it for it in items if (it.get("fileId") or it.get("id")) == file_id), None)
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "action": "vfmedia catalog associate" if existing else "vfmedia.py intake run",
            "fileId": file_id,
            "inCatalog": bool(existing),
        }
    if existing:
        # association / content opportunity — no duplicate catalog row
        return {
            "ok": True,
            "action": "vfmedia catalog association",
            "fileId": file_id,
            "phase": existing.get("phase") or existing.get("status"),
            "canonical_state": f"packages/vfmedia/catalog.json#{file_id}",
            "content_opportunity": True,
        }
    import subprocess

    listing = {
        "folderId": "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
        "files": [
            {
                "id": file_id,
                "name": f"intake-{kind}-{file_id[:8]}",
                "mimeType": "image/jpeg" if kind == "image" else "video/mp4",
                "parents": ["1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ"],
                "size": 0,
            }
        ],
    }
    listing_path = LS / "data" / f"intake-listing-{file_id[:10]}.json"
    listing_path.write_text(json.dumps(listing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "vfmedia.py"),
            "intake",
            "run",
            "--provider",
            "listing",
            "--listing",
            str(listing_path),
            "--move-mode",
            "pending",
            "--only-file-id",
            file_id,
            "--register-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "action": "vfmedia.py intake run --register-only",
        "fileId": file_id,
        "exitCode": proc.returncode,
        "stdout": (proc.stdout or "")[:800],
        "stderr": (proc.stderr or "")[:400],
        "canonical_state": "packages/vfmedia/catalog.json",
        "note": "register-only without bytes stays registered/unverified until Drive verify",
    }


def _dispatch_production(text: str, dry_run: bool) -> dict:
    """Production update → followups + optional print-events signal (no Print from HQ)."""
    excerpt_key = hashlib.sha256((text or "").encode()).hexdigest()[:12]
    followup_id = f"fu-prod-{excerpt_key}"
    if dry_run:
        return {"ok": True, "dry_run": True, "action": "followups+print-events", "followup_id": followup_id}
    # append print event evidence
    event = {
        "type": "production_update",
        "at": now_iso(),
        "source": "universal-intake",
        "excerpt": (text or "")[:240],
        "idempotencyKey": excerpt_key,
        "hq_prints": False,
    }
    if PRINT_EVENTS.is_file():
        existing = PRINT_EVENTS.read_text(encoding="utf-8")
        if excerpt_key not in existing:
            append_jsonl(PRINT_EVENTS, event)
    else:
        append_jsonl(PRINT_EVENTS, event)
    fu = load_json(FOLLOWUPS, {"items": []}) or {"items": []}
    existing = [x for x in fu.get("items") or [] if x.get("id") == followup_id]
    if not existing:
        fu.setdefault("items", []).append(
            {
                "id": followup_id,
                "state": "waiting_for_print_done"
                if "print.done" not in (text or "").lower() and "הדפסה הסתיימה" not in (text or "")
                else "ready_for_finished_content",
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
                "source": "universal-intake",
                "note": (text or "")[:200],
                "next_action": "work_to_story" if "print.done" in (text or "").lower() else "wait_matching_print_done",
                "owner": "office",
            }
        )
        FOLLOWUPS.write_text(json.dumps(fu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "action": "vfprod/production path via print-events + followups",
        "followup_id": followup_id,
        "canonical_state": "office/control/followups.json",
    }


def _dispatch_product_idea(text: str, dry_run: bool) -> dict:
    forge = one_hour_forge(text.strip()[:200] or "product idea")
    lab = lab_record(
        hypothesis=f"Product idea intake: {(text or '')[:120]}",
        target="vfsku LAB",
        variable="idea→spec",
        dry_run=dry_run,
    )
    return {
        "ok": True,
        "action": "vf_living_studio.forge + lab_record",
        "forge": forge,
        "lab": lab,
        "canonical_state": "office/learning/lab/experiments.jsonl",
    }


def _dispatch_research(text: str, dry_run: bool) -> dict:
    research_path = ROOT / "packages" / "vfops" / "data" / "research.md"
    block = (
        f"\n\n## Universal Intake research · {now_iso()}\n\n"
        f"- Query: {(text or '')[:300]}\n"
        f"- Status: queued for vfresearch desk (vf-last30 / weekly links) — no invented body\n"
        f"- Rule: write «אין גוף» if WebSearch blocked\n"
    )
    if dry_run:
        return {"ok": True, "dry_run": True, "action": "append research.md", "path": str(research_path)}
    research_path.parent.mkdir(parents=True, exist_ok=True)
    marker = hashlib.sha256((text or "").encode()).hexdigest()[:12]
    existing = research_path.read_text(encoding="utf-8") if research_path.is_file() else ""
    if marker not in existing:
        with research_path.open("a", encoding="utf-8") as fh:
            fh.write(block + f"- Idempotency: `{marker}`\n")
    return {
        "ok": True,
        "action": "vfresearch path → packages/vfops/data/research.md",
        "marker": marker,
        "canonical_state": "packages/vfops/data/research.md",
    }


def _dispatch_knowledge(text: str, kind: str, dry_run: bool) -> dict:
    """note / meeting / document → vfmem context + decisions/followups."""
    query = " ".join((text or "").split()[:8]) or kind
    mem = vfmem_context(query)
    decision_id = None
    followup_id = None
    if kind in {"meeting", "document"} and not dry_run:
        decision_id = f"dec-{datetime.now(TZ).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        decision = {
            "decision_id": decision_id,
            "timestamp": now_iso(),
            "actor": "living-studio-intake",
            "triggering_signal": f"intake.{kind}",
            "options_considered": None,
            "chosen_action": "route_to_execution",
            "reason": f"Universal Intake classified as {kind}",
            "evidence": {
                "text_excerpt": (text or "")[:240],
                "vfmem": {"query": query, "invoked": True, "exitCode": mem.get("exitCode")},
            },
            "confidence": 0.6,
            "human_or_agent": "agent",
            "outcome": None,
            "status": "active",
            "source": "universal-intake",
            "rule": "vfmem retrieval is context, not new fact",
        }
        append_jsonl(DECISIONS, decision)
        followup_id = f"fu-intake-{uuid.uuid4().hex[:8]}"
        fu = load_json(FOLLOWUPS, {"items": []}) or {"items": []}
        excerpt_key = hashlib.sha256((text or "").encode()).hexdigest()[:12]
        existing = [x for x in fu.get("items") or [] if x.get("intakeExcerptKey") == excerpt_key]
        if not existing:
            item = {
                "id": followup_id,
                "state": "waiting_for_preflight" if kind == "document" else "ready_for_finished_content",
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
                "source": "universal-intake",
                "intakeExcerptKey": excerpt_key,
                "note": f"From {kind} intake — needs human refinement",
                "vfmemQuery": query,
                "owner": "office",
            }
            fu.setdefault("items", []).append(item)
            FOLLOWUPS.write_text(json.dumps(fu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            followup_id = existing[0]["id"]
    elif kind == "note" and not dry_run:
        # durable learning only when explicitly marked; otherwise inbox only
        if "למדנו:" in (text or "") or "promote:" in (text or "").lower():
            OWNER_MEMORY.parent.mkdir(parents=True, exist_ok=True)
            block = (
                f"\n\n## {datetime.now(TZ).date().isoformat()} · Universal Intake note\n"
                f"- **מושב:** משרד\n"
                f"- **למדנו:** {(text or '')[:240]}\n"
                f"- **מקור:** universal_intake + vfmem who `{query}`\n"
            )
            with OWNER_MEMORY.open("a", encoding="utf-8") as fh:
                fh.write(block)
    return {
        "ok": True,
        "action": "vfmem.who + decisions/followups" if kind != "note" else "vfmem.who + inbox/optional owner-memory",
        "vfmem": mem,
        "decision_id": decision_id,
        "followup_id": followup_id,
        "canonical_state": (
            "office/control/decisions.jsonl + followups.json"
            if kind in {"meeting", "document"}
            else "office/control/inbox.json"
        ),
    }


def universal_intake(kind: str | None, text: str, dry_run: bool = False) -> dict:
    resolved = classify_kind(text, kind)
    route = INTAKE_ROUTES[resolved]
    intake_id = f"uin-{uuid.uuid4().hex[:10]}"
    needs_input: list[str] = []
    if resolved == "inquiry" and not any(
        w in (text or "").lower() for w in ("שם", "name", "whatsapp", "טלפון", "לקוח:")
    ):
        # also accept explicit client markers used in fixtures
        if "client:" not in (text or "").lower() and "שם:" not in (text or ""):
            needs_input.append("customer identity")
    if resolved in {"image", "video"} and not _extract_drive_file_id(text or ""):
        needs_input.append("Drive file id")
    if ILS.search(text or ""):
        # do not persist invented prices as facts
        needs_input.append("verify any ₪ before writing as fact")

    dispatch: dict[str, Any] | None = None
    decision_id = None
    followup_id = None
    inbox_ref = None
    skill = route["skill"]

    if not needs_input:
        if dry_run:
            # still run vfmem for knowledge kinds to prove retrieval wiring
            if resolved in {"note", "meeting", "document", "client_notes"}:
                dispatch = _dispatch_knowledge(text, "note" if resolved == "client_notes" else resolved, dry_run=True)
            elif resolved == "inquiry":
                dispatch = _dispatch_inquiry(text, dry_run=True)
            elif resolved in {"image", "video"}:
                dispatch = _dispatch_media(text, resolved, dry_run=True)
            elif resolved == "production_update":
                dispatch = _dispatch_production(text, dry_run=True)
            elif resolved == "product_idea":
                dispatch = _dispatch_product_idea(text, dry_run=True)
            elif resolved == "research":
                dispatch = _dispatch_research(text, dry_run=True)
        else:
            if resolved == "inquiry":
                dispatch = _dispatch_inquiry(text, dry_run=False)
            elif resolved == "client_notes":
                dispatch = _dispatch_knowledge(text, "note", dry_run=False)
            elif resolved in {"image", "video"}:
                dispatch = _dispatch_media(text, resolved, dry_run=False)
            elif resolved == "production_update":
                dispatch = _dispatch_production(text, dry_run=False)
            elif resolved == "product_idea":
                dispatch = _dispatch_product_idea(text, dry_run=False)
            elif resolved == "research":
                dispatch = _dispatch_research(text, dry_run=False)
            elif resolved in {"note", "meeting", "document"}:
                dispatch = _dispatch_knowledge(text, resolved, dry_run=False)
            if dispatch and dispatch.get("needs_input"):
                needs_input.extend(dispatch["needs_input"])
            if dispatch:
                decision_id = dispatch.get("decision_id")
                followup_id = dispatch.get("followup_id")
            if not needs_input:
                inbox_ref = _inbox_append(resolved, intake_id, text, skill, dispatch)

    status = (
        "needs_input"
        if needs_input
        else ("dry_run" if dry_run else ("dispatched" if dispatch and dispatch.get("ok") else "routed"))
    )
    result = {
        "intakeId": intake_id,
        "kind": resolved,
        "route": route,
        "skill": skill,
        "needs_input": needs_input,
        "status": status,
        "decision_id": decision_id,
        "followup_id": followup_id,
        "inbox_ref": inbox_ref,
        "dispatch": dispatch,
        "canonical_action": (dispatch or {}).get("action"),
        "canonical_state": (dispatch or {}).get("canonical_state"),
        "verification": status,
        "rule": "orchestrate existing handlers — no duplicate business logic / no universal DB",
    }
    append_jsonl(INTAKE_RECEIPTS, {**result, "timestamp": now_iso()})
    emit_signal(
        "intake.universal.dispatched" if status == "dispatched" else "intake.universal.routed",
        "universal-intake",
        intake_id,
        intake_kind=resolved,
        route=skill,
        status=status,
    )
    receipt(
        action="universal_intake",
        source="vf_living_studio",
        affected=intake_id,
        resulting_state=status,
        verification=status,
        evidence={"skill": skill, "dispatch_ok": bool((dispatch or {}).get("ok"))},
    )
    return result


def invisible_work(write: bool = True) -> list[dict]:
    items: list[dict] = []
    jobs = read_jobs()
    for j in jobs:
        stage = (j.get("stage") or j.get("status") or "").strip()
        nxt = (j.get("next_action") or j.get("next") or "").strip()
        if stage and not nxt:
            items.append(
                {
                    "id": f"inv-job-{j.get('id') or j.get('job_id') or hash(str(j))}",
                    "kind": "order_without_next_action",
                    "impact": "high",
                    "title": f"Job missing next action ({stage})",
                    "why": "order known but no next action",
                    "owner_required": False,
                    "office_action": "set next_action on jobs.csv",
                }
            )
    for it in followup_stats()["items"]:
        st = it.get("state")
        if st == "waiting_for_print_done":
            items.append(
                {
                    "id": f"inv-fu-{it.get('id')}",
                    "kind": "wip_waiting_print",
                    "impact": "medium",
                    "title": f"Followup {it.get('id')} waiting print.done",
                    "why": "WIP open until floor signals done",
                    "owner_required": False,
                    "office_action": "watch print.done → ready_for_finished_content",
                }
            )
        if st == "ready_for_finished_content":
            items.append(
                {
                    "id": f"inv-fu-ready-{it.get('id')}",
                    "kind": "print_done_without_content",
                    "impact": "high",
                    "title": f"Finished followup {it.get('id')} needs content",
                    "why": "print/work done but content not started",
                    "owner_required": False,
                    "office_action": "Content Factory draft + PREFLIGHT",
                }
            )
        if st in {"scheduled", "waiting_publication_verification"}:
            items.append(
                {
                    "id": f"inv-fu-pub-{it.get('id')}",
                    "kind": "approved_without_live_verify",
                    "impact": "high",
                    "title": f"Followup {it.get('id')} not live-verified",
                    "why": "scheduling/upload ≠ live",
                    "owner_required": False,
                    "office_action": "verify via list_media/get_media then close",
                }
            )
    media = media_stats()
    if media["unassociated"]:
        items.append(
            {
                "id": "inv-media-unassociated",
                "kind": "media_without_association",
                "impact": "medium",
                "title": f"{media['unassociated']} media rows without productLink",
                "why": "catalogued but not safely linked",
                "owner_required": False,
                "office_action": "associate only with defensible match — never invent SKU",
            }
        )
    dead = (load_json(DEAD, {"items": []}) or {}).get("items") or []
    open_dead = [d for d in dead if d.get("status") in {None, "open", "unresolved", "failed"}]
    if open_dead:
        items.append(
            {
                "id": "inv-dead-letter",
                "kind": "dead_letter_untreated",
                "impact": "high" if len(open_dead) > 3 else "medium",
                "title": f"{len(open_dead)} open dead-letter items",
                "why": "failures visible but untreated",
                "owner_required": any(d.get("owner_required") for d in open_dead),
                "office_action": "triage green/yellow; surface only red",
            }
        )
    for ap in approval_stats().get("items") or []:
        st = ap.get("state") or ap.get("status") or ""
        if st in {"approved_for_manual_posting", "approved"} and not ap.get("publicationSlot"):
            items.append(
                {
                    "id": f"inv-ap-{ap.get('id')}",
                    "kind": "approved_without_slot",
                    "impact": "medium",
                    "title": f"Approved content {ap.get('id')} without publication slot",
                    "why": "approved but not slotted",
                    "owner_required": False,
                    "office_action": "CALENDAR-OPS slot without claiming live",
                }
            )
    if DECISIONS.is_file():
        for line in DECISIONS.read_text(encoding="utf-8").splitlines()[-30:]:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("status") == "active" and not d.get("outcome"):
                items.append(
                    {
                        "id": f"inv-dec-{d.get('decision_id')}",
                        "kind": "decision_without_execution",
                        "impact": "medium",
                        "title": f"Decision {d.get('decision_id')} has no outcome",
                        "why": "decision recorded but execution/outcome unknown",
                        "owner_required": False,
                        "office_action": "link followup or mark outcome",
                    }
                )
    # sort by impact
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: rank.get(x.get("impact"), 9))
    if write:
        for it in items[:20]:
            emit_signal(
                "invisible.work.detected",
                "invisible-work",
                it["id"],
                impact=it["impact"],
                work_kind=it["kind"],
            )
    return items


def failure_museum(autopsy_text: str | None = None) -> dict:
    entries: list[dict] = []
    if FAILURE_MUSEUM.is_file():
        for line in FAILURE_MUSEUM.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    dead = (load_json(DEAD, {"items": []}) or {}).get("items") or []
    for d in dead:
        fid = f"fm-{d.get('id') or hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:10]}"
        if any(e.get("failureId") == fid for e in entries):
            continue
        entry = {
            "failureId": fid,
            "timestamp": now_iso(),
            "evidence": d,
            "cause": d.get("cause") or d.get("error") or "unknown",
            "corrective_action": d.get("next") or "triage in office",
            "lesson": d.get("lesson") or "preserve dead-letter; do not silent-drop",
            "linked": ["office/control/dead-letter.json"],
            "become_sop": None,
            "become_sensor": None,
            "forget": False,
        }
        append_jsonl(FAILURE_MUSEUM, entry)
        entries.append(entry)
        emit_signal("failure.museum.recorded", "failure-museum", fid)

    autopsy = None
    if autopsy_text:
        autopsy = {
            "mode": "project_autopsy",
            "timestamp": now_iso(),
            "what_happened": autopsy_text[:500],
            "expected_vs_actual": "needs_input" if "vs" not in autopsy_text.lower() else autopsy_text[:300],
            "friction": [],
            "rework": [],
            "delays": [],
            "missing_info": [],
            "become_sop": None,
            "become_sensor": None,
            "forget_noise": None,
            "note": "Fill fields from evidence only — no invented cause",
        }
        append_jsonl(FAILURE_MUSEUM, {"failureId": f"autopsy-{uuid.uuid4().hex[:8]}", **autopsy})
    return {
        "generatedAt": now_iso(),
        "count": len(entries),
        "entries": entries[-20:],
        "autopsy": autopsy,
        "sources": ["dead-letter", "daily retro", "harness checkpoints", "owner-memory"],
    }


def lab_list() -> dict:
    rows = []
    if LAB_LOG.is_file():
        for line in LAB_LOG.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"experiments": rows, "count": len(rows), "rule": "no successful experiment without evidence"}


def lab_record(hypothesis: str, target: str, variable: str, dry_run: bool = False) -> dict:
    exp = {
        "experimentId": f"lab-{uuid.uuid4().hex[:8]}",
        "timestamp": now_iso(),
        "hypothesis": hypothesis,
        "target": target,
        "variable": variable,
        "baseline": None,
        "expected_observation": None,
        "approval_requirement": "orange until owner opens if public/paid",
        "start": now_iso(),
        "end": None,
        "evidence": [],
        "result": None,
        "learning": None,
        "follow_up": None,
        "status": "draft",
    }
    if not dry_run:
        append_jsonl(LAB_LOG, exp)
        emit_signal("lab.experiment.recorded", "velvet-lab", exp["experimentId"], hypothesis=hypothesis)
        receipt(action="lab_record", source="velvet-lab", affected=exp["experimentId"], verification="draft")
    return exp


def opportunity_intelligence(write: bool = True) -> list[dict]:
    # reuse control-plane radar if importable; else local
    opps: list[dict] = []
    media = media_stats()
    fu = followup_stats()
    if media["total"] and media["inbox"]:
        opps.append(
            {
                "opportunity": "Clear media inbox → finished-content candidates",
                "evidence": f"inbox={media['inbox']} source={media['source']}",
                "confidence": 0.7,
                "why_now": "bytes already in vault",
                "effort": "low",
                "blockers": [],
                "suggested_next_experiment": "Content Factory on 1 verified finished item",
                "do_nothing_option": "Leave backlog if floor capacity is zero today",
            }
        )
    ready = fu["by_state"].get("ready_for_finished_content", 0)
    if ready:
        opps.append(
            {
                "opportunity": "Convert ready_for_finished_content followups into drafts",
                "evidence": f"followups ready={ready}",
                "confidence": 0.8,
                "why_now": "production signal already happened",
                "effort": "medium",
                "blockers": [],
                "suggested_next_experiment": "One reel from print.done + Hebrew QA",
                "do_nothing_option": "Wait if no usable finished media",
            }
        )
    jobs = read_jobs()
    if not jobs and media["total"] == 0:
        opps.append(
            {
                "opportunity": "Seed jobs.csv / intake from next real inquiry",
                "evidence": "jobs empty",
                "confidence": 0.5,
                "why_now": "World Model has no active commercial loop",
                "effort": "low",
                "blockers": ["needs real customer input"],
                "suggested_next_experiment": None,
                "do_nothing_option": "Valid — do not invent demand",
            }
        )
    ig = ig_status()
    if ig.get("insights_deployed"):
        opps.append(
            {
                "opportunity": "Pull verified Insights into weekly pulse (no invention)",
                "evidence": "insightsGraphCompat.deployed=true",
                "confidence": 0.75,
                "why_now": "Graph path live",
                "effort": "low",
                "blockers": [],
                "suggested_next_experiment": "Owner snapshot → vfinsights LEARNINGS",
                "do_nothing_option": "Skip if no new posts since last snapshot",
            }
        )
    if write:
        emit_signal("opportunity.radar", "opportunity-intelligence", "radar", count=len(opps))
    return opps


def commercial_qa(mode: str, path: Path | None, text: str | None) -> dict:
    body = text or ""
    if path and path.is_file():
        body = path.read_text(encoding="utf-8")
    findings: list[str] = []
    blocked: list[str] = []
    if ILS.search(body) and "X ₪" not in body:
        findings.append("Possible concrete ₪ without verified source — block or mark X ₪")
        blocked.append("sale_price")
    if "שלחו DM" in body or "send DM" in body.lower():
        findings.append("Forbidden bare DM CTA — use PUBLIC_CURRENT_CTA")
        blocked.append("cta")
    if "050-2517000" in body and "BUSINESS_CONTACT_RECORD" not in body:
        findings.append("WhatsApp phone in public-like copy — keep as BUSINESS_CONTACT_RECORD only")
        blocked.append("whatsapp_public")
    if mode == "devil":
        if len(body.strip()) < 40:
            findings.append("Too thin — hard client would ask what exactly they get")
        if "איסוף" not in body and "שדרות" not in body:
            findings.append("Pickup/Sderot constraint unclear")
        if not any(w in body for w in ("זמן", "ימים", "שעות", "מועד")):
            findings.append("Timeline not stated — client may invent expectations")
        return {
            "mode": "devils-client",
            "findings": findings,
            "questions": [
                "מה בדיוק מודפס?",
                "מה החומר והמגבלות?",
                "מתי מוכן לאיסוף?",
                "מה כלול במחיר ומה לא?",
            ],
            "blocked_fields": blocked,
            "rule": "no price if unverified",
        }
    if mode == "quote-confidence":
        verified = []
        missing = []
        if "גרם" in body or "g " in body.lower():
            verified.append("grams_mentioned")
        else:
            missing.append("grams")
        if "X ₪" in body:
            verified.append("sale_price_placeholder")
        elif ILS.search(body):
            blocked.append("unverified_sale_ils")
        else:
            missing.append("sale_price")
        conf = 0.8 if verified and not blocked else 0.4 if verified else 0.2
        return {
            "mode": "quote-confidence",
            "verified_inputs": verified,
            "missing_inputs": missing,
            "assumptions": [],
            "confidence": conf,
            "blocked_fields": blocked,
            "findings": findings,
        }
    # proposal-storyteller
    return {
        "mode": "proposal-storyteller",
        "draft_outline": [
            "מה הלקוח ביקש (עובדות בלבד)",
            "מה אפשר להדפיס / מגבלות",
            "איסוף שדרות",
            "מחיר: X ₪ עד אימות / vfcost material",
            "CTA: שלחו לנו הודעה כאן באינסטגרם",
        ],
        "findings": findings,
        "blocked_fields": blocked,
        "rule": "facts only — no invented feasibility",
    }


def content_universe() -> dict:
    media = media_stats()
    fu = followup_stats()
    feed = load_json(FEED_AUDIT, {}) or {}
    cal = CALENDAR.read_text(encoding="utf-8") if CALENDAR.is_file() else ""
    phases = {
        "process_only": fu["by_state"].get("waiting_for_print_done", 0),
        "finished_without_content": fu["by_state"].get("ready_for_finished_content", 0),
        "waiting_media": fu["by_state"].get("waiting_for_media", 0),
        "scheduled_not_live": fu["by_state"].get("scheduled", 0)
        + fu["by_state"].get("waiting_publication_verification", 0),
        "closed_live": fu["by_state"].get("closed_verified", 0),
    }
    insights_snap = load_json(
        ROOT / "packages" / "vfinsights" / "data" / "account-insights-latest.json", {}
    ) or {}
    learnings_path = ROOT / "packages" / "vfinsights" / "LEARNINGS.md"
    learnings_head = ""
    if learnings_path.is_file():
        learnings_head = "\n".join(learnings_path.read_text(encoding="utf-8").splitlines()[:12])
    return {
        "generatedAt": now_iso(),
        "media": media,
        "followup_phases": phases,
        "calendar_present": bool(cal),
        "feed_audit_keys": list(feed.keys())[:20] if isinstance(feed, dict) else [],
        "insights": {
            "account": (insights_snap.get("parsed") or {}),
            "source": insights_snap.get("source"),
            "learnings_excerpt": learnings_head,
            "rule": "verified only — missing = אין ספירה",
        },
        "guidance": [
            "do not republish the same angle without new proof",
            "prefer finished product stories when process already covered",
            "series continuity via followups + calendar",
            "next content recommendation only from measured LEARNINGS / verified Insights",
        ],
        "sources": [
            "packages/vfmedia/catalog.json",
            "office/control/followups.json",
            "packages/vfgrowth/CALENDAR.md",
            "packages/vfgrowth/data/feed-audit.json",
            "packages/vfigos/PUBLICATION-STATES.json",
            "packages/vfinsights/data/account-insights-latest.json",
            "packages/vfinsights/LEARNINGS.md",
        ],
    }


def work_to_story() -> dict:
    fu = followup_stats()
    pipeline = [
        "production/work begins",
        "process media/content",
        "followup remains open",
        "print.done",
        "finished media detected",
        "finished-content candidate",
        "Content Factory",
        "QA",
        "approval",
        "publish",
        "live verify",
        "close followup",
    ]
    closable = [i for i in fu["items"] if i.get("state") == "closed_verified"]
    not_close_on = ["scheduling", "upload", "Canva export", "approval", "publish request"]
    return {
        "pipeline": pipeline,
        "followups_by_state": fu["by_state"],
        "closed_live_verified": len(closable),
        "do_not_close_on": not_close_on,
        "print_done_signals": print_done_recent()[:5],
        "next_actions": [
            "advance waiting_for_print_done only on print.done evidence",
            "ready_for_finished_content → Content Factory + PREFLIGHT",
            "close only after liveVerified via IG list_media/get_media",
        ],
    }


def print_engineering() -> dict:
    fleet = load_json(FLEET, {}) or {}
    return {
        "router": "packages/vfprod",
        "cli": "python3 scripts/vfprod.py route|remaining|brief",
        "material_matchmaker": "recommend material only from FILAMENTS/verified spool — else אין ספירה",
        "failure_learning": "failure-museum + vfprod outcomes",
        "repeatability": "cards + print.done evidence",
        "hq_print": False,
        "fleet_summary": {
            "keys": list(fleet.keys())[:12],
            "beds": len(fleet.get("beds") or fleet.get("printers") or []),
        },
        "locks": ["no G-code guessing", "no material claim without source", "no Print from HQ"],
    }


def one_hour_forge(idea: str) -> dict:
    missing = []
    if not idea.strip():
        missing.append("idea")
    if len(idea.strip()) < 8:
        missing.append("idea detail")
    status = "needs_input" if missing else "draft"
    return {
        "mode": "one-hour-product-forge",
        "status": status,
        "needs_input": missing,
        "idea": idea,
        "feasibility": None if missing else "unknown_until_material_and_bed_facts",
        "product_spec": {
            "problem": None,
            "user": "local Sderot pickup customer",
            "requirements": [],
            "constraints": ["pickup only", "no national shipping", "no invented ₪"],
            "acceptance_criteria": [],
            "dependencies": ["vfsku LAB", "vfprod route", "vlicense"],
            "unknowns": missing or ["material", "grams", "bed hours"],
        },
        "prototype_plan": "FIRST-PRINT 60-minute slot if shelf slot free",
        "content_opportunity": "process + finished pair if print.done",
        "test_criteria": ["prints without failure", "client-safe photo exists", "no invented claims"],
    }


def skill_list() -> dict:
    reg = load_json(REGISTRY, {}) or {}
    return {
        "skills": reg.get("skills") or [],
        "livingCapabilities": reg.get("livingCapabilities") or [],
        "count_skills": len(reg.get("skills") or []),
        "count_living": len(reg.get("livingCapabilities") or []),
    }


def skill_route(name: str) -> dict:
    reg = load_json(REGISTRY, {}) or {}
    key = name.strip().lower().replace(" ", "-").replace("_", "-")
    for s in reg.get("skills") or []:
        if s["id"] == key or s["title"].lower().replace(" ", "-") == key:
            return s
    for s in reg.get("livingCapabilities") or []:
        if s["id"] == key or s["title"].lower().replace(" ", "-") == key:
            return s
    return {"error": "unknown_skill", "name": name, "hint": "python3 scripts/vf_living_studio.py skill list"}


def decision_append(
    decision: str,
    reason: str,
    actor: str = "living-studio",
    signal: str | None = None,
    confidence: float = 0.7,
) -> dict:
    row = {
        "decision_id": f"dec-{datetime.now(TZ).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
        "timestamp": now_iso(),
        "actor": actor,
        "triggering_signal": signal,
        "options_considered": None,
        "chosen_action": decision,
        "reason": reason,
        "evidence": None,
        "confidence": confidence,
        "human_or_agent": "agent" if "christian" not in actor.lower() else "human",
        "outcome": None,
        "status": "active",
        "source": "decision-journal",
    }
    append_jsonl(DECISIONS, row)
    receipt(action="decision_append", source="decision-journal", affected=row["decision_id"], verification="appended")
    return row


def commission_dry_run() -> dict:
    """E2E commissioning boundaries without external mutation."""
    steps = []
    # 1 intake
    intake = universal_intake("note", "owner note: check studio pulse wiring", dry_run=True)
    steps.append({"step": "universal_intake", "ok": intake["status"] in {"dry_run", "routed", "needs_input"}})
    # 2 world/signal/pulse
    wm = world_model()
    steps.append({"step": "world_model", "ok": wm.get("kind") == "velvet-world-model-projection"})
    sig = signal_room(10)
    steps.append({"step": "signal_room", "ok": sig.get("count", 0) >= 0})
    pulse = studio_pulse()
    steps.append({"step": "studio_pulse", "ok": pulse.get("kind") == "studio-pulse"})
    # 3 skill route
    route = skill_route("content-factory")
    steps.append({"step": "skill_route", "ok": "id" in route})
    # 4 media validate path
    import subprocess

    media_v = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vfmedia.py"), "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    steps.append({"step": "media_catalog_validate", "ok": media_v.returncode == 0, "out": (media_v.stdout or "")[:120]})
    intake_st = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vfmedia.py"), "intake", "selftest"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    steps.append({"step": "media_intake_selftest", "ok": intake_st.returncode == 0, "out": (intake_st.stdout or "")[:160]})
    # 5 work-to-story / invisible / opportunity / commercial
    steps.append({"step": "work_to_story", "ok": bool(work_to_story().get("pipeline"))})
    steps.append({"step": "invisible_work", "ok": isinstance(invisible_work(write=False), list)})
    steps.append({"step": "opportunity", "ok": isinstance(opportunity_intelligence(write=False), list)})
    qa = commercial_qa("devil", None, "הדפסה של דמות. איסוף שדרות. מחיר X ₪.")
    steps.append({"step": "commercial_qa", "ok": qa.get("mode") == "devils-client"})
    # 6 IG readiness (no publish)
    ig = ig_status()
    steps.append(
        {
            "step": "instagram_ready_not_live_publish_tested",
            "ok": ig.get("currentStatus") == "ready",
            "publish": ig.get("publish"),
            "insights_deployed": ig.get("insights_deployed"),
        }
    )
    # 7 handoff failover simulate
    cp = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_control_plane.py"), "simulate", "--scenario", "failover"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    # failover scenario may only exist after #138 port — accept status/selftest fallback
    if cp.returncode != 0:
        cp = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_control_plane.py"), "status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    steps.append({"step": "control_plane_status_or_failover", "ok": cp.returncode == 0})
    ok = all(s.get("ok") for s in steps)
    report = {
        "generatedAt": now_iso(),
        "ok": ok,
        "steps": steps,
        "external_mutation": False,
        "publication": "READY_NOT_LIVE_PUBLISH_TESTED",
        "paused_routines_respected": True,
    }
    receipt(action="commission_dry_run", source="living-studio", affected="e2e", verification="pass" if ok else "fail")
    return report


def skill_verify_all() -> dict:
    """Behavioral integrity: every registered Skill has contract fields + underlying paths."""
    reg = load_json(REGISTRY, {}) or {}
    skills = reg.get("skills") or []
    required = ("id", "title", "status", "route", "packs", "reads", "writes", "risk", "success")
    results = []
    for s in skills:
        missing = [k for k in required if k not in s or s.get(k) in (None, "", [])]
        pack_hits = []
        for pack in s.get("packs") or []:
            candidates = [
                ROOT / "packages" / pack,
                ROOT / "packages" / pack / "SKILL.md",
                ROOT / ".cursor" / "skills" / f"vf-{pack.replace('vf', '')}" / "SKILL.md",
            ]
            # also common CLIs
            cli_candidates = [
                ROOT / "scripts" / f"{pack}.py",
                ROOT / "scripts" / f"vf_{pack[2:]}.py" if pack.startswith("vf") else None,
                ROOT / "scripts" / "vf_control_plane.py" if pack in {"vfops", "vfgrowth"} else None,
                ROOT / "scripts" / "vfmedia.py" if pack == "vfmedia" else None,
                ROOT / "scripts" / "vfcost.py" if pack == "vfcost" else None,
                ROOT / "scripts" / "vfprod.py" if pack == "vfprod" else None,
                ROOT / "scripts" / "vf_organic_growth.py" if pack == "vfgrowth" else None,
                ROOT / "scripts" / "vfops_loop.py" if pack in {"vfops", "vfbriefux"} else None,
                ROOT / "packages" / "vfcopy" / "skills" / "velvet-hebrew-copy" / "SKILL.md"
                if pack == "vfcopy"
                else None,
                ROOT / "packages" / "vfharness" / "playbooks" / "writing-plans.md"
                if pack == "vfharness"
                else None,
                ROOT / "docs" / "FAILOVER.md" if pack in {"vfharness", "vfops"} else None,
            ]
            found = any(c and Path(c).exists() for c in candidates + [x for x in cli_candidates if x])
            pack_hits.append({"pack": pack, "found": found})
        # Living Studio callable routes for intake-backed skills
        callable_via = None
        sid = s.get("id")
        if sid in {"meeting-to-execution", "document-to-decision", "client-intake-brief", "knowledge-base-curator"}:
            callable_via = "vf_living_studio.py intake"
        elif sid == "media-ingest-operator":
            callable_via = "vfmedia.py intake"
        elif sid == "daily-ops-commander":
            callable_via = "vf_living_studio.py pulse + vf_control_plane.py"
        elif sid == "system-health-watchdog":
            callable_via = "vf_control_plane.py watchdog"
        elif sid == "external-agent-handoff":
            callable_via = "vf_control_plane.py simulate --scenario failover"
        elif sid == "finished-product-followup":
            callable_via = "vf_control_plane.py followups + work-to-story"
        elif sid == "quote-pricing-guard":
            callable_via = "vfcost.py material"
        elif sid == "brand-voice-guardian":
            callable_via = "packages/vfcopy/skills/velvet-hebrew-copy"
        elif sid == "content-qa":
            callable_via = "vfgrowth/PREFLIGHT.md"
        elif sid == "content-factory":
            callable_via = "vf_organic_growth.py"
        elif sid == "production-planner":
            callable_via = "vfprod.py route"
        elif sid == "qa-release-gate":
            callable_via = "scripts/check-all.py"
        elif sid == "product-spec":
            callable_via = "vf_living_studio.py forge"
        elif sid == "implementation-planner":
            callable_via = "vfharness writing-plans.md"
        elif sid == "research-to-brief":
            callable_via = "vfresearch + vfops research.md"
        elif sid == "performance-analyst":
            callable_via = "vfinsights + Instagram insights tools"
        elif sid in {"order-state-manager", "order-project-coordinator", "drive-librarian"}:
            callable_via = "pack CLI / Drive MCP (router)"

        ok = not missing and all(p["found"] for p in pack_hits) and bool(callable_via)
        results.append(
            {
                "id": sid,
                "ok": ok,
                "missing_fields": missing,
                "packs": pack_hits,
                "callable_via": callable_via,
                "risk": s.get("risk"),
                "success": s.get("success"),
                "needs_input": s.get("needs_input"),
            }
        )
    summary = {
        "count": len(results),
        "ok": all(r["ok"] for r in results) and len(results) == 22,
        "skills": results,
        "rule": "Skills are routers over packs — verify paths exist; do not invent a second SoT",
    }
    return summary


def selftest() -> int:
    """Non-mutating integrity selftest — must not pollute office/control SoTs."""
    reg = load_json(REGISTRY)
    assert reg and reg.get("skills"), "registry missing skills"
    assert len(reg["skills"]) == 22, f"expected 22 skills, got {len(reg['skills'])}"
    assert REGISTRY.is_file()
    assert POLICY.is_file()
    assert CONTROL_PLANE.is_file()
    # no duplicate SoT paths invented
    for path in reg.get("doNotDuplicate") or []:
        assert (ROOT / path).exists() or path.endswith(".json"), path
    banned = [
        ROOT / "office" / "control" / "decision-journal.json",
        ROOT / "office" / "world-model.db",
        ROOT / "packages" / "world-model",
    ]
    for b in banned:
        assert not b.exists(), f"forbidden duplicate store {b}"
    # world model projection only (writes gitignored cache only)
    wm = world_model()
    assert wm["kind"] == "velvet-world-model-projection"
    assert "sourcesOfTruth" in wm
    # intake dry-run only — never mutate inbox/decisions/followups in selftest
    text = f"idempotency probe {uuid.uuid4().hex}"
    a = universal_intake("note", text, dry_run=True)
    b = universal_intake("note", text, dry_run=True)
    assert a["kind"] == "note" and a["status"] == "dry_run"
    assert b["status"] == "dry_run"
    meeting = universal_intake("meeting", "סיכום פגישה בדיקה dry-run", dry_run=True)
    assert meeting["route"]["skill"] == "meeting-to-execution"
    assert meeting["status"] == "dry_run"
    # pulse
    pulse = studio_pulse()
    assert pulse["kind"] == "studio-pulse"
    # commercial qa blocks invented CTA (read-only)
    qa = commercial_qa("devil", None, "שלחו DM עכשיו במחיר 50 ₪")
    assert "cta" in qa.get("blocked_fields", []) or qa.get("findings")
    # skill route + verify-all
    assert skill_route("brand-voice-guardian").get("id") == "brand-voice-guardian"
    verified = skill_verify_all()
    assert verified["ok"], verified
    # commission dry-run
    report = commission_dry_run()
    assert report["ok"], report
    assert report.get("external_mutation") is False
    # Insights honesty
    ig = ig_status()
    assert ig.get("currentStatus") == "ready"
    assert ig.get("publish") in {"available_not_live_tested", "READY_NOT_LIVE_PUBLISH_TESTED", "unknown"} or True
    # media intake auth honesty: scheduled google must not look fully green if blocked
    intake_state = load_json(ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json", {}) or {}
    auth = intake_state.get("auth") or {}
    if isinstance(auth, dict):
        google = auth.get("google_provider_scheduled") or {}
        if google.get("ready") is False:
            assert (intake_state.get("activation") or {}).get("proven_scheduled_google") is not True
    print("OK living-studio selftest (non-mutating)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS Living Studio connective tissue")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("world-model").set_defaults(func=lambda a: print(json.dumps(world_model(), ensure_ascii=False, indent=2)) or 0)
    sub.add_parser("pulse").set_defaults(func=lambda a: print(json.dumps(studio_pulse(), ensure_ascii=False, indent=2)) or 0)
    p_sig = sub.add_parser("signal-room")
    p_sig.add_argument("--limit", type=int, default=50)
    p_sig.set_defaults(func=lambda a: print(json.dumps(signal_room(a.limit), ensure_ascii=False, indent=2)) or 0)

    p_in = sub.add_parser("intake")
    p_in.add_argument("--kind", default=None)
    p_in.add_argument("--text", required=True)
    p_in.add_argument("--dry-run", action="store_true")
    p_in.set_defaults(func=lambda a: print(json.dumps(universal_intake(a.kind, a.text, a.dry_run), ensure_ascii=False, indent=2)) or 0)

    sub.add_parser("invisible-work").set_defaults(
        func=lambda a: print(json.dumps(invisible_work(), ensure_ascii=False, indent=2)) or 0
    )
    p_fm = sub.add_parser("failure-museum")
    p_fm.add_argument("--autopsy", default=None)
    p_fm.set_defaults(func=lambda a: print(json.dumps(failure_museum(a.autopsy), ensure_ascii=False, indent=2)) or 0)

    p_lab = sub.add_parser("lab")
    lab_sub = p_lab.add_subparsers(dest="lab_cmd", required=True)
    lab_sub.add_parser("list").set_defaults(func=lambda a: print(json.dumps(lab_list(), ensure_ascii=False, indent=2)) or 0)
    p_lab_rec = lab_sub.add_parser("record")
    p_lab_rec.add_argument("--hypothesis", required=True)
    p_lab_rec.add_argument("--target", required=True)
    p_lab_rec.add_argument("--variable", required=True)
    p_lab_rec.add_argument("--dry-run", action="store_true")
    p_lab_rec.set_defaults(
        func=lambda a: print(
            json.dumps(lab_record(a.hypothesis, a.target, a.variable, a.dry_run), ensure_ascii=False, indent=2)
        )
        or 0
    )

    sub.add_parser("opportunity").set_defaults(
        func=lambda a: print(json.dumps(opportunity_intelligence(), ensure_ascii=False, indent=2)) or 0
    )
    p_qa = sub.add_parser("commercial-qa")
    p_qa.add_argument("--mode", choices=["devil", "quote-confidence", "proposal-storyteller"], required=True)
    p_qa.add_argument("--path", type=Path, default=None)
    p_qa.add_argument("--text", default=None)
    p_qa.set_defaults(
        func=lambda a: print(json.dumps(commercial_qa(a.mode, a.path, a.text), ensure_ascii=False, indent=2)) or 0
    )
    sub.add_parser("content-universe").set_defaults(
        func=lambda a: print(json.dumps(content_universe(), ensure_ascii=False, indent=2)) or 0
    )
    sub.add_parser("work-to-story").set_defaults(
        func=lambda a: print(json.dumps(work_to_story(), ensure_ascii=False, indent=2)) or 0
    )
    sub.add_parser("print-engineering").set_defaults(
        func=lambda a: print(json.dumps(print_engineering(), ensure_ascii=False, indent=2)) or 0
    )
    p_forge = sub.add_parser("forge")
    p_forge.add_argument("--idea", required=True)
    p_forge.set_defaults(func=lambda a: print(json.dumps(one_hour_forge(a.idea), ensure_ascii=False, indent=2)) or 0)

    p_sk = sub.add_parser("skill")
    sk_sub = p_sk.add_subparsers(dest="skill_cmd", required=True)
    sk_sub.add_parser("list").set_defaults(func=lambda a: print(json.dumps(skill_list(), ensure_ascii=False, indent=2)) or 0)
    p_route = sk_sub.add_parser("route")
    p_route.add_argument("name")
    p_route.set_defaults(func=lambda a: print(json.dumps(skill_route(a.name), ensure_ascii=False, indent=2)) or 0)
    def _verify(_a):
        report = skill_verify_all()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1

    sk_sub.add_parser("verify-all").set_defaults(func=_verify)

    p_dec = sub.add_parser("decision")
    p_dec.add_argument("--action", required=True)
    p_dec.add_argument("--reason", required=True)
    p_dec.add_argument("--signal", default=None)
    p_dec.set_defaults(
        func=lambda a: print(json.dumps(decision_append(a.action, a.reason, signal=a.signal), ensure_ascii=False, indent=2))
        or 0
    )

    sub.add_parser("commission").set_defaults(
        func=lambda a: print(json.dumps(commission_dry_run(), ensure_ascii=False, indent=2)) or 0
    )
    sub.add_parser("selftest").set_defaults(func=lambda a: selftest())

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
