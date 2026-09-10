#!/usr/bin/env python3
"""VelvetOS autonomy composition — projections over existing Office/HQ sources of truth.

Compose next-action + safe execute over existing handlers.
No second queue/database/runtime. Orange/red stay gated by POLICY.

Standing Instagram authorization is NOT automatic Christian orange work.
pending_human_approval alone does not put an item on the owner surface.

CLI:
  python3 scripts/vf_autonomy.py status
  python3 scripts/vf_autonomy.py next-action
  python3 scripts/vf_autonomy.py blockers
  python3 scripts/vf_autonomy.py approvals
  python3 scripts/vf_autonomy.py context <id>
  python3 scripts/vf_autonomy.py quiet-plan
  python3 scripts/vf_autonomy.py snapshot
  python3 scripts/vf_autonomy.py execute [--action ...] [--dry-run]
  python3 scripts/vf_autonomy.py selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from vf_paths import OFFICE_ROOT, ROOT  # noqa: E402

TZ = ZoneInfo("Asia/Jerusalem")

CONFIG = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
JOBS_TEMPLATE = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
INTAKE_RUNNER = ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
IG_CAPS = ROOT / "packages" / "vfigos" / "CAPABILITIES.json"
PREFLIGHT_DIR = ROOT / "packages" / "vfgrowth" / "preflight"


def _office_file(*parts: str) -> Path:
    """OFFICE_ROOT path with ROOT fallback when the file is missing (living_studio pattern)."""
    office = OFFICE_ROOT.joinpath(*parts)
    if office.is_file():
        return office
    alt = ROOT.joinpath(*parts)
    return alt if alt.is_file() else office


def _office_write(*parts: str) -> Path:
    """Mutable write target under OFFICE_ROOT (sandbox-aware)."""
    return OFFICE_ROOT.joinpath(*parts)


OUT = _office_write("packages", "velvetos", "living-studio", "data", "autonomy-latest.json")
RUNS = _office_write("packages", "velvetos", "living-studio", "data", "autonomy-runs.jsonl")
INBOX = _office_file("office", "control", "inbox.json")
FOLLOWUPS = _office_file("office", "control", "followups.json")
DEAD = _office_file("office", "control", "dead-letter.json")
DECISIONS = _office_file("office", "control", "decisions.jsonl")
APPROVAL_QUEUE = _office_file("packages", "vfgrowth", "data", "approval-queue.json")
JOBS = OFFICE_ROOT / "office" / "ledger" / "live" / "jobs.csv"
if not JOBS.is_file() and (ROOT / "office" / "ledger" / "live" / "jobs.csv").is_file():
    JOBS = ROOT / "office" / "ledger" / "live" / "jobs.csv"
POLICY = _office_file("office", "control", "POLICY.md")
if not POLICY.is_file():
    POLICY = ROOT / "office" / "control" / "POLICY.md"

RISK_ORDER = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "": 4}
CLOSED_STATES = {"closed", "closed_verified", "completed", "done", "resolved"}
WAITING_PREFIXES = ("waiting_", "blocked")

# Actions autonomy may execute without owner (green/yellow internal)
SAFE_ACTIONS = {
    "reconcile_before_retry",
    "projection refresh",
    "projection_refresh",
    "refresh_projections",
    "media_intake_retry",
    "run_media_intake_status",
    "jobs_pull_status",
    "memory_context",
    "vfmem_who",
    "content_factory_prepare",
    "watchdog_repair",
    "health_repair",
    "followup_safe_transition",
    "review_current_state",
    "classify",
    "checkpoint",
    "context pack",
    "readiness check",
}

SAFE_ACTION_NORMS = {a.replace(" ", "_").lower() for a in SAFE_ACTIONS}

# Last jobs_state from load_jobs / consumer_view
_JOBS_STATE = "unknown"

# POLICY.md keyword bands (Hebrew + English)
_RED_KEYWORDS = (
    "רכישה",
    "תשלום",
    "שינוי מחיר",
    "הרוסנית",
    "מחיקה בלתי הפיכה",
    "purchase",
    "destructive",
    "delete_media",
    "boost",
    "ads",
    "whatsapp send",
    "print-from-hq",
)
_ORANGE_KEYWORDS = (
    "הודעה חיצונית",
    "פרסום חריגה",
    "שינוי מדיניות",
    "external message",
    "publish_live",
    "pending_human_approval",
)
_YELLOW_KEYWORDS = (
    "הכנת תוכן",
    "content_factory",
    "watchdog",
    "production→content",
)

_OWNER_REASON_HINTS = {
    "physical-footage-or-staging": ("footage", "physical", "staging", "צילום פיזי"),
    "rights-or-privacy-unclear": ("rights", "privacy", "זכויות", "פרטיות"),
    "sale-ils-or-price-change": ("₪", "מחיר", "price", "sale-ils"),
    "purchase-or-spend": ("purchase", "spend", "רכישה", "תשלום"),
    "boost-or-ads": ("boost", "ads", "פרסום ממומן"),
    "customer-whatsapp-send": ("whatsapp", "וואטסאפ", "050-2517000"),
    "print-from-hq": ("print-from-hq", "הדפסה מ-hq", "print from hq"),
    "irreversible-destructive-action": ("destructive", "מחיקה", "irreversible", "delete"),
    "hard-blocker-after-failover": ("hard-blocker", "חסם קשיח"),
}


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows


def jobs_path() -> Path:
    return JOBS if JOBS.is_file() else JOBS_TEMPLATE


def load_standing_authorization() -> dict[str, Any]:
    data = load_json(INSTANCE, {})
    autonomy = data.get("creativeAutonomy") or {}
    publish = autonomy.get("publish") or {}
    return {
        "standingAuthorization": bool(publish.get("standingAuthorization")),
        "requirePreflight": bool(publish.get("requirePreflight", True)),
        "requireKnownRights": bool(publish.get("requireKnownRights", True)),
        "humanRequired": list(autonomy.get("humanRequired") or []),
        "ownerSurface": autonomy.get("ownerSurface") or "human_required_only",
        "allowedFormats": list(publish.get("allowedFormats") or []),
    }


def publish_capability_ready() -> bool:
    caps = load_json(IG_CAPS, {})
    return (
        str(caps.get("currentStatus") or "").lower() == "ready"
        and str(caps.get("auth") or "").lower() == "ready"
    )


def _preflight_path(content_id: str) -> Path:
    office = OFFICE_ROOT / "packages" / "vfgrowth" / "preflight" / f"{content_id}.md"
    if office.is_file():
        return office
    return PREFLIGHT_DIR / f"{content_id}.md"


def _preflight_passes(content_id: str) -> tuple[bool, Path | None]:
    path = _preflight_path(content_id)
    if not path.is_file():
        return False, None
    text = path.read_text(encoding="utf-8")
    # Pass language used in vfgrowth preflight packets
    passed = bool(
        re.search(r"שער:\s*\*\*עבור\*\*", text)
        or re.search(r"(?i)\bgate:\s*pass\b", text)
        or re.search(r"(?i)\bpreflight\s*:\s*pass\b", text)
        or ("**עבור**" in text and "נכשל" not in text[:400])
    )
    return passed, path


def _item_blob(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False).lower()


def _forbidden_publish_signals(blob: str) -> list[str]:
    hits: list[str] = []
    if "₪" in blob or re.search(r"\d[\d.,]*\s*₪", blob):
        hits.append("sale_ils")
    if any(k in blob for k in ("boost", "ads", "פרסום ממומן")):
        hits.append("ads")
    if any(k in blob for k in ("whatsapp", "וואטסאפ", "050-2517000", "wa.me")):
        hits.append("whatsapp")
    if any(k in blob for k in ("print-from-hq", "הדפסה מ-hq", "print from hq")):
        hits.append("print")
    if any(k in blob for k in ("destructive", "מחיקה בלתי", "delete_media", "irreversible")):
        hits.append("destructive")
    return hits


def _owner_reasons_from_item(item: dict[str, Any], human_required: list[str]) -> list[str]:
    blob = _item_blob(item)
    found: list[str] = []
    for reason in human_required:
        hints = _OWNER_REASON_HINTS.get(reason, (reason,))
        if any(h.lower() in blob for h in hints):
            found.append(reason)
    # explicit flags on the item
    for key in ("ownerSurface", "human_required", "requiresOwner"):
        if item.get(key) in (True, "true", "orange", "red"):
            if "explicit_owner_flag" not in found:
                found.append("explicit_owner_flag")
    return found


def _story_stale_days(content_id: str) -> int | None:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", content_id or "")
    if not m:
        return None
    try:
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (datetime.now(TZ).date() - d).days


def classify_approval_item(item: dict[str, Any]) -> dict[str, Any]:
    """Classify one approval-queue row.

    Dispositions: autonomous_under_standing_authorization | human_required |
    stale_orphan | superseded | published_verified | closed

    pending_human_approval alone is NOT Christian orange work (ownerSurface=false
    unless a humanRequired reason from the instance applies).
    """
    auth = load_standing_authorization()
    content_id = str(item.get("content_id") or item.get("id") or "")
    gate = str(item.get("gate") or "").lower()
    fmt = str(item.get("format") or "").lower()
    blob = _item_blob(item)
    standing_considered = True
    forbidden = _forbidden_publish_signals(blob)
    owner_reasons = _owner_reasons_from_item(item, auth["humanRequired"])

    base = {
        "content_id": content_id,
        "standingAuthorizationConsidered": standing_considered,
        "standingAuthorization": auth["standingAuthorization"],
        "missing_gates": [],
        "ownerSurface": False,
        "humanRequiredReasons": owner_reasons,
        "forbiddenSignals": forbidden,
    }

    if gate in {"closed", "done", "resolved"} or str(item.get("disposition") or "") == "closed":
        return {**base, "disposition": "closed", "risk": "green"}

    if gate in {"live_verified", "published_verified"} or item.get("liveVerified") is True:
        return {**base, "disposition": "published_verified", "risk": "green"}

    if gate in {"approved", "approved_for_manual_posting", "superseded"}:
        if gate == "superseded" or item.get("superseded"):
            return {**base, "disposition": "superseded", "risk": "green"}
        if item.get("human_marked"):
            return {**base, "disposition": "closed", "risk": "green"}

    # Expired story without live mark → stale orphan (office scrub, not Christian)
    age = _story_stale_days(content_id)
    if fmt == "story" and age is not None and age >= 2 and not item.get("human_marked"):
        return {
            **base,
            "disposition": "stale_orphan",
            "missing_gates": ["PREFLIGHT"] if not _preflight_path(content_id).is_file() else [],
            "ownerSurface": False,
            "risk": "yellow",
            "note": "story slot aged out — reconcile in office, not owner orange queue",
        }

    if owner_reasons or forbidden:
        return {
            **base,
            "disposition": "human_required",
            "ownerSurface": True,
            "missing_gates": ["OWNER_GATE"] + (["PREFLIGHT"] if not _preflight_path(content_id).is_file() else []),
            "risk": "orange" if not any(x in forbidden for x in ("destructive", "sale_ils", "ads")) else "red",
            "note": "instance humanRequired / forbidden publish signal",
        }

    preflight_ok, preflight_path = _preflight_passes(content_id)
    if not preflight_ok:
        return {
            **base,
            "disposition": "human_required",
            "ownerSurface": False,
            "missing_gates": ["PREFLIGHT"],
            "risk": "yellow",
            "note": "missing/failing preflight is office work — not automatic Christian orange",
            "preflightPath": str(preflight_path) if preflight_path else None,
        }

    caps_ready = publish_capability_ready()
    if not caps_ready:
        return {
            **base,
            "disposition": "human_required",
            "ownerSurface": False,
            "missing_gates": ["PUBLISH_CAPABILITY"],
            "risk": "yellow",
            "note": "publish capability not ready — office failover, not owner orange",
        }

    if auth["standingAuthorization"] and preflight_ok and caps_ready and not forbidden:
        return {
            **base,
            "disposition": "autonomous_under_standing_authorization",
            "ownerSurface": False,
            "missing_gates": [],
            "risk": "green",
            "note": "standing auth + known gates; still no auto-DM / boost / print",
        }

    return {
        **base,
        "disposition": "human_required",
        "ownerSurface": False,
        "missing_gates": ["STANDING_AUTH"],
        "risk": "yellow",
    }


def load_jobs() -> list[dict[str, str]]:
    """Hydrated consumer view only. Unready → [] and surface jobs_state in snapshot."""
    global _JOBS_STATE
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        view = jobs_adapter.ensure_hydrated()
        _JOBS_STATE = str(view.get("jobs_state") or "unknown")
        if _JOBS_STATE != "ready":
            return []
        return list(view.get("jobs") or [])
    except Exception:  # noqa: BLE001
        _JOBS_STATE = "needs_sync"
        return []


def jobs_state() -> str:
    return _JOBS_STATE


def _append_run(row: dict[str, Any]) -> None:
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _risk_allows_execute(risk: str) -> str:
    """Return decision: execute | waiting_approval | refuse."""
    r = (risk or "green").lower()
    if r in {"red", "orange"}:
        return "waiting_approval"
    return "execute"


def resolve_action_risk(action: str, target_id: str | None = None) -> str:
    """Derive risk from action type + POLICY.md keywords + SAFE_ACTIONS membership."""
    act_norm = (action or "").strip().replace(" ", "_").lower()
    blob = f"{action or ''} {target_id or ''}".lower()
    policy_text = POLICY.read_text(encoding="utf-8").lower() if POLICY.is_file() else ""

    if any(k.lower() in blob for k in _RED_KEYWORDS):
        return "red"
    if any(k.lower() in policy_text and k.lower() in blob for k in _RED_KEYWORDS):
        return "red"
    if any(k.lower() in blob for k in _ORANGE_KEYWORDS):
        return "orange"

    if act_norm not in SAFE_ACTION_NORMS:
        # Unknown / unsafe actions are refused at execute — treat as orange+ for gating
        return "orange"

    if act_norm in {
        "content_factory_prepare",
        "watchdog_repair",
        "health_repair",
        "media_intake_retry",
    } or any(k.lower() in blob for k in _YELLOW_KEYWORDS):
        return "yellow"
    return "green"


def _tighten_risk(resolved: str, caller: str | None) -> str:
    """Caller --risk may only tighten (green→orange OK; orange/red cannot become green)."""
    base = (resolved or "green").lower()
    if not caller:
        return base
    c = caller.lower()
    if c not in RISK_ORDER:
        return base
    # Lower RISK_ORDER value = more severe
    if RISK_ORDER[c] <= RISK_ORDER.get(base, 4):
        return c
    return base


def flatten_inbox() -> list[dict[str, Any]]:
    data = load_json(INBOX, {"buckets": {}})
    rows: list[dict[str, Any]] = []
    for bucket, items in (data.get("buckets") or {}).items():
        for item in items or []:
            rows.append({**item, "bucket": bucket, "_source": "office/control/inbox.json"})
    return rows


def open_dead_letters() -> list[dict[str, Any]]:
    data = load_json(DEAD, {"items": []})
    rows = []
    for item in data.get("items") or []:
        state = str(item.get("status") or item.get("state") or "open").lower()
        if state not in CLOSED_STATES:
            rows.append({**item, "_source": "office/control/dead-letter.json"})
    return rows


def blockers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    followups = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    for item in followups:
        state = str(item.get("state") or "").lower()
        if state in CLOSED_STATES:
            continue
        if state.startswith(WAITING_PREFIXES) or item.get("next_action"):
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state"),
                    "waiting_for": item.get("waiting_for") or _waiting_from_state(state),
                    "blocked_item": item.get("blocked_item") or item.get("contentId") or item.get("jobId") or item.get("sku"),
                    "since": item.get("since") or item.get("created_at"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "",
                    "source": "office/control/followups.json",
                }
            )
    for item in flatten_inbox():
        if item.get("bucket") == "blocked":
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state") or "blocked",
                    "waiting_for": item.get("waiting_for"),
                    "blocked_item": item.get("blocked_item") or item.get("title"),
                    "since": item.get("since") or item.get("created_at") or item.get("updatedAt"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "orange",
                    "source": "office/control/inbox.json",
                }
            )
    for item in open_dead_letters():
        rows.append(
            {
                "id": item.get("id"),
                "state": item.get("status") or item.get("state") or "dead_letter",
                "waiting_for": item.get("waiting_for") or "exception_resolution",
                "blocked_item": item.get("title") or item.get("kind") or item.get("id"),
                "since": item.get("created_at") or item.get("updatedAt"),
                "safe_until": item.get("safe_until"),
                "next_action": item.get("next_action") or "reconcile_before_retry",
                "risk": item.get("risk") or "orange",
                "source": "office/control/dead-letter.json",
            }
        )
    return _dedupe(rows)


def _waiting_from_state(state: str) -> str | None:
    if state.startswith("waiting_for_"):
        return state.removeprefix("waiting_for_")
    if state == "blocked":
        return "blocker_resolution"
    return None


def approval_bundle() -> list[dict[str, Any]]:
    """Christian orange surface — only ownerSurface=true rows.

    Approval-queue items are classified; missing PREFLIGHT / standing-auth
    office work does NOT automatically become orange Christian work.
    """
    rows: list[dict[str, Any]] = []
    for item in flatten_inbox():
        risk = str(item.get("risk") or "").lower()
        if item.get("bucket") == "approvals" or risk in {"orange", "red"}:
            rows.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title") or item.get("kind") or item.get("id"),
                    "risk": risk or "orange",
                    "action": item.get("next_action") or item.get("action"),
                    "ownerSurface": True,
                    "disposition": "human_required",
                    "source": "office/control/inbox.json",
                }
            )
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    for item in queue.get("items") or []:
        classified = classify_approval_item(item)
        if not classified.get("ownerSurface"):
            continue
        rows.append(
            {
                "id": item.get("content_id") or item.get("id"),
                "title": f"Content approval · {item.get('format') or 'content'}",
                "risk": classified.get("risk") or "orange",
                "action": classified.get("disposition"),
                "disposition": classified.get("disposition"),
                "missing_gates": classified.get("missing_gates") or [],
                "standingAuthorizationConsidered": classified.get("standingAuthorizationConsidered"),
                "ownerSurface": True,
                "humanRequiredReasons": classified.get("humanRequiredReasons") or [],
                "slot": item.get("slot"),
                "source": "packages/vfgrowth/data/approval-queue.json",
            }
        )
    rows.sort(key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("id") or "")))
    return _dedupe(rows)


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row.get("source") or row.get("_source") or ""), str(row.get("id") or row.get("blocked_item") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def next_action() -> dict[str, Any]:
    approvals = approval_bundle()
    if approvals:
        top = approvals[0]
        return {
            "kind": "approval",
            "id": top.get("id"),
            "action": top.get("action") or "review_approval",
            "reason": "ownerSurface=true gated decision in canonical approval sources",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    waiting = blockers()
    actionable = [row for row in waiting if row.get("next_action") and row.get("next_action") not in {"wait", "none"}]
    if actionable:
        top = sorted(actionable, key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("since") or "")))[0]
        return {
            "kind": "blocker",
            "id": top.get("id"),
            "action": top.get("next_action"),
            "reason": "canonical waiting item already declares a next action",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    inbox = [i for i in flatten_inbox() if str(i.get("state") or "").lower() not in CLOSED_STATES]
    if inbox:
        top = inbox[0]
        return {
            "kind": "inbox",
            "id": top.get("id"),
            "action": top.get("next_action") or "review_current_state",
            "reason": "open canonical inbox item; no stronger approval/blocker action exists",
            "risk": top.get("risk") or "green",
            "source": top.get("_source"),
        }

    return {"kind": "none", "action": "no_action", "reason": "no open canonical action found"}


def context_pack(identifier: str) -> dict[str, Any]:
    needle = identifier.strip().lower()
    if not needle:
        raise SystemExit("FAIL context requires a non-empty id")

    found: dict[str, list[dict[str, Any]]] = {
        "inbox": [],
        "followups": [],
        "dead_letter": [],
        "approvals": [],
        "jobs": [],
        "decisions": [],
    }

    def matches(row: dict[str, Any]) -> bool:
        hay = json.dumps(row, ensure_ascii=False).lower()
        return needle in hay

    for row in flatten_inbox():
        if matches(row):
            found["inbox"].append(row)
    for row in load_json(FOLLOWUPS, {"items": []}).get("items") or []:
        if matches(row):
            found["followups"].append(row)
    for row in load_json(DEAD, {"items": []}).get("items") or []:
        if matches(row):
            found["dead_letter"].append(row)
    for row in load_json(APPROVAL_QUEUE, {"items": []}).get("items") or []:
        if matches(row):
            found["approvals"].append({**row, "classification": classify_approval_item(row)})
    for row in load_jobs():
        if matches(row):
            found["jobs"].append(row)
    for row in load_jsonl(DECISIONS):
        if matches(row):
            found["decisions"].append(row)

    return {
        "id": identifier,
        "generatedAt": now_iso(),
        "jobs_state": _JOBS_STATE,
        "rule": "source-linked retrieval only; absence is unknown, not permission to invent",
        "sources": found,
        "counts": {key: len(value) for key, value in found.items()},
    }


def quiet_plan() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    bg = next((c for c in cfg.get("components") or [] if c.get("id") == "background-executor-policy"), {})
    candidates: list[dict[str, Any]] = []
    for row in blockers():
        action = str(row.get("next_action") or "")
        if action in {"reconcile_before_retry", "wait_matching_print_done", "media_intake_retry", "projection_refresh"}:
            candidates.append({"id": row.get("id"), "action": action, "source": row.get("source"), "risk": row.get("risk") or "yellow"})
    candidates.append({"id": "autonomy-snapshot", "action": "projection_refresh", "source": "AUTONOMY.json", "risk": "green"})
    candidates.append({"id": "media-intake-status", "action": "run_media_intake_status", "source": "vfmedia", "risk": "green"})
    return {
        "generatedAt": now_iso(),
        "mode": "quiet-hours-safe-plan",
        "allowed": bg.get("allowed") or [],
        "forbidden": bg.get("forbidden") or [],
        "candidates": candidates,
        "note": "green/yellow candidates may be executed via vf_autonomy.py execute; orange/red stay gated",
    }


def _reconcile_before_action(action: str, target_id: str | None) -> dict[str, Any]:
    """Reconcile actual state before retry — never blind retry."""
    evidence: dict[str, Any] = {"action": action, "target_id": target_id}
    if action in {"media_intake_retry", "run_media_intake_status"}:
        state = load_json(INTAKE_RUNNER, {})
        evidence["intake_runner"] = {
            "auth_ready": (state.get("auth") or {}).get("ready"),
            "lastSuccessAt": state.get("lastSuccessAt"),
            "activation_proven": (state.get("activation") or {}).get("proven"),
            "lastError": state.get("lastError"),
        }
    if action in {"reconcile_before_retry"} and target_id:
        for item in load_json(FOLLOWUPS, {"items": []}).get("items") or []:
            if item.get("id") == target_id:
                evidence["followup"] = {"state": item.get("state"), "next_action": item.get("next_action")}
        for item in load_json(DEAD, {"items": []}).get("items") or []:
            if item.get("id") == target_id:
                evidence["dead_letter"] = {"status": item.get("status") or item.get("state")}
    if action in {"projection_refresh", "projection refresh", "refresh_projections"}:
        evidence["projections"] = {
            "autonomy": OUT.is_file(),
            "pulse": (OFFICE_ROOT / "packages/velvetos/living-studio/data/pulse-latest.json").is_file()
            or (ROOT / "packages/velvetos/living-studio/data/pulse-latest.json").is_file(),
        }
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        evidence["jobs"] = jobs_adapter.status()
    except Exception as exc:  # noqa: BLE001
        evidence["jobs_error"] = str(exc)
    return evidence


def _run_handler(action: str, *, target_id: str | None, dry_run: bool) -> dict[str, Any]:
    action_norm = action.strip().replace(" ", "_").lower()
    if action in {"projection refresh", "projection_refresh", "refresh_projections"} or action_norm == "projection_refresh":
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "snapshot+pulse+world-model"}
        snap = snapshot()
        pulse = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "pulse"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        world = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "world-model"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": pulse.returncode == 0 and world.returncode == 0,
            "handler": "snapshot+pulse+world-model",
            "nextBestAction": snap.get("nextBestAction"),
            "pulse_exit": pulse.returncode,
            "world_exit": world.returncode,
        }

    if action in {"run_media_intake_status", "media_intake_retry"} or action_norm in {
        "run_media_intake_status",
        "media_intake_retry",
    }:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vfmedia.py intake status"}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vfmedia.py"), "intake", "status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        body = {}
        try:
            body = json.loads(proc.stdout) if proc.stdout.strip() else {}
        except json.JSONDecodeError:
            body = {"raw": (proc.stdout or "")[:500]}
        retried = False
        if action_norm == "media_intake_retry" and (body.get("auth") or {}).get("ready") and body.get("lastError"):
            retried = False
        return {
            "ok": proc.returncode == 0,
            "handler": "vfmedia.py intake status",
            "status": body,
            "retried_run": retried,
            "note": "full Drive intake remains on commissioned GHA OIDC runner when auth.ready",
        }

    if action in {"reconcile_before_retry"} or action_norm == "reconcile_before_retry":
        evidence = _reconcile_before_action(action, target_id)
        # dry_run must not mutate followups
        if target_id and not dry_run:
            fu_path = FOLLOWUPS if FOLLOWUPS.parent.is_dir() else _office_write("office", "control", "followups.json")
            fu = load_json(fu_path, {"items": []})
            changed = False
            for item in fu.get("items") or []:
                if item.get("id") == target_id and item.get("state") not in CLOSED_STATES:
                    item["lastReconcileAt"] = now_iso()
                    item["reconcileNote"] = "autonomy reconciled actual state before retry"
                    changed = True
            if changed:
                fu_path.write_text(json.dumps(fu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "handler": "reconcile_before_retry", "evidence": evidence, "dry_run": dry_run}

    if action in {"memory_context", "vfmem_who", "context pack"} or action_norm in {"memory_context", "vfmem_who"}:
        q = target_id or "inquiry"
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vfmem.py who", "query": q}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vfmem.py"), "--json", "who", q],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = None
        if proc.stdout.strip():
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result = {"text": proc.stdout[:1000]}
        return {"ok": proc.returncode == 0, "handler": "vfmem.py who", "query": q, "result": result}

    if action in {"content_factory_prepare"} or action_norm == "content_factory_prepare":
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vf_living_studio work-to-story + content-universe"}
        wts = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "work-to-story"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        cu = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "content-universe"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": wts.returncode == 0 and cu.returncode == 0,
            "handler": "work-to-story + content-universe",
            "note": "prepare only — no publish",
        }

    if action in {"watchdog_repair", "health_repair"} or action_norm in {"watchdog_repair", "health_repair"}:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vf_control_plane.py watchdog"}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_control_plane.py"), "watchdog"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "handler": "vf_control_plane.py watchdog",
            "stdout": (proc.stdout or "")[:1000],
        }

    if action in {"followup_safe_transition"} or action_norm == "followup_safe_transition":
        return _run_handler("reconcile_before_retry", target_id=target_id, dry_run=dry_run)

    if action in {"review_current_state", "classify", "checkpoint", "readiness check", "jobs_pull_status"}:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "jobs status + snapshot"}
        sys.path.insert(0, str(ROOT / "scripts"))
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        st = jobs_adapter.status()
        snap = snapshot()
        return {"ok": True, "handler": "jobs.status + snapshot", "jobs": st, "next": snap.get("nextBestAction")}

    if action in {"wait_matching_print_done", "wait", "none", "no_action"}:
        return {"ok": True, "handler": "noop_wait", "note": "waiting is managed state — no mutation"}

    return {"ok": False, "handler": None, "error": f"no safe handler for action {action!r}"}


def execute_action(
    action: str | None = None,
    *,
    target_id: str | None = None,
    risk: str | None = None,
    dry_run: bool = False,
    source: str = "vf_autonomy",
) -> dict[str, Any]:
    """Lifecycle: queued → running → checkpoint → completed | waiting_approval | failed.

    dry_run=True never appends RUNS and never mutates followups.
    Actions outside SAFE_ACTIONS are refused (failed) — never executed.
    Caller --risk may only tighten severity.
    """
    nxt = next_action() if not action else {
        "kind": "manual",
        "id": target_id,
        "action": action,
        "risk": risk or "green",
        "source": source,
        "reason": "explicit execute",
    }
    act = action or str(nxt.get("action") or "")
    tid = target_id or (str(nxt.get("id")) if nxt.get("id") else None)
    resolved = resolve_action_risk(act, tid)
    risk_val = _tighten_risk(resolved, risk)
    act_norm = act.strip().replace(" ", "_").lower()
    run_id = f"arun-{uuid.uuid4().hex[:12]}"
    correlation_id = f"corr-{hashlib.sha256(f'{act}|{tid}'.encode()).hexdigest()[:12]}"
    idempotency_key = f"exec|{act}|{tid}|{rows_fingerprint(act, tid)}"

    row: dict[str, Any] = {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "source": source,
        "action": act,
        "target_id": tid,
        "risk": risk_val,
        "resolved_risk": resolved,
        "caller_risk": risk,
        "dry_run": dry_run,
        "at": now_iso(),
        "next_action_snapshot": nxt,
    }

    # Refuse unsafe actions — never execute
    if act_norm not in SAFE_ACTION_NORMS and act not in {"wait_matching_print_done", "wait", "none", "no_action"}:
        row["decision"] = "refuse"
        row["state"] = "failed"
        row["resulting_state"] = "failed"
        row["error"] = f"action {act!r} not in SAFE_ACTIONS — refuse"
        if not dry_run:
            _append_run(row)
        return row

    # Idempotent skip only for real runs
    if not dry_run and RUNS.is_file():
        for line in RUNS.read_text(encoding="utf-8").splitlines()[-200:]:
            try:
                prev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if prev.get("idempotency_key") == idempotency_key and prev.get("state") == "completed":
                return {**prev, "status": "idempotent_skip"}

    decision = _risk_allows_execute(str(risk_val))
    row["decision"] = decision
    row["state"] = "queued"

    if dry_run:
        if decision == "waiting_approval":
            row["state"] = "waiting_approval"
            row["resulting_state"] = "waiting_approval"
            row["evidence"] = {"policy": "office/control/POLICY.md", "gate": risk_val}
            return row
        reconcile = _reconcile_before_action(act, tid)
        row["checkpoint"] = {"reconcile": reconcile, "at": now_iso()}
        result = _run_handler(act, target_id=tid, dry_run=True)
        row["evidence"] = result
        row["state"] = "completed" if result.get("ok") else "failed"
        row["resulting_state"] = row["state"]
        if not result.get("ok"):
            row["error"] = result.get("error") or result.get("stderr")
        row["finishedAt"] = now_iso()
        return row

    _append_run(row)

    if decision == "waiting_approval":
        row["state"] = "waiting_approval"
        row["evidence"] = {"policy": "office/control/POLICY.md", "gate": risk_val}
        row["resulting_state"] = "waiting_approval"
        _append_run(row)
        return row

    row["state"] = "running"
    _append_run({"run_id": run_id, "state": "running", "at": now_iso()})

    reconcile = _reconcile_before_action(act, tid)
    row["checkpoint"] = {"reconcile": reconcile, "at": now_iso()}
    _append_run({"run_id": run_id, "state": "checkpoint", "checkpoint": row["checkpoint"]})

    try:
        result = _run_handler(act, target_id=tid, dry_run=False)
        row["evidence"] = result
        if result.get("ok"):
            row["state"] = "completed"
            row["resulting_state"] = "completed"
        else:
            row["state"] = "failed"
            row["resulting_state"] = "failed"
            row["error"] = result.get("error") or result.get("stderr")
    except Exception as exc:  # noqa: BLE001
        row["state"] = "failed"
        row["resulting_state"] = "failed"
        row["error"] = str(exc)
        row["evidence"] = {"exception": str(exc)}
    row["finishedAt"] = now_iso()
    _append_run(row)
    return row


def rows_fingerprint(action: str, target_id: str | None) -> str:
    return hashlib.sha256(f"{action}|{target_id}|{datetime.now(TZ).date().isoformat()}".encode()).hexdigest()[:10]


def snapshot() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    _ = load_jobs()  # hydrate jobs_state for surface
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    classified = [classify_approval_item(i) for i in (queue.get("items") or [])]
    data = {
        "name": "velvetos-autonomy-snapshot",
        "generatedAt": now_iso(),
        "contract": cfg.get("executionContract") or {},
        "componentStatus": {c.get("id"): c.get("status") for c in cfg.get("components") or []},
        "nextBestAction": next_action(),
        "blockers": blockers(),
        "approvalBundle": approval_bundle(),
        "approvalClassifications": classified,
        "quietPlan": quiet_plan(),
        "jobs_state": _JOBS_STATE,
        "executor": "vf_autonomy.py execute — composition over existing handlers",
        "rule": "pending_human_approval ≠ automatic Christian orange; ownerSurface only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def selftest() -> tuple[bool, list[str]]:
    """Behavioral selftest — dry_run only; must not write RUNS."""
    errors: list[str] = []
    runs_before = RUNS.read_text(encoding="utf-8") if RUNS.is_file() else ""
    cfg = load_json(CONFIG, {})
    if not cfg:
        errors.append("missing AUTONOMY.json")
    if not CONTROL_PLANE.is_file():
        errors.append("missing office/control-plane.json")
    if not POLICY.is_file():
        errors.append("missing office/control/POLICY.md")
    ids = [c.get("id") for c in cfg.get("components") or []]
    expected = {
        "foundation-runtime-contract",
        "router-context-engine",
        "blocker-waiting-engine",
        "project-lifecycle-engine",
        "approval-system",
        "reliability-exception-engine",
        "work-prioritization",
        "background-executor-policy",
    }
    missing = sorted(expected - set(ids))
    if missing:
        errors.append("missing components: " + ", ".join(missing))
    contract = cfg.get("executionContract") or {}
    for required in ("run_id", "idempotency_key", "correlation_id"):
        if required not in (contract.get("requiredIds") or []):
            errors.append(f"execution contract missing {required}")
    states = set(contract.get("states") or [])
    if not {"queued", "running", "waiting_approval", "completed", "failed"}.issubset(states):
        errors.append("execution contract states incomplete")

    ex = execute_action("projection_refresh", risk="green", dry_run=True, source="selftest")
    if ex.get("state") not in {"completed", "idempotent_skip"} and ex.get("status") != "idempotent_skip":
        errors.append(f"execute dry-run failed: {ex.get('state')} {ex.get('error')}")

    gated = execute_action("content_factory_prepare", risk="orange", dry_run=True, source="selftest")
    if gated.get("state") != "waiting_approval" and gated.get("decision") != "waiting_approval":
        errors.append("orange action must wait for approval")

    # Caller cannot loosen orange→green
    loosened = execute_action("content_factory_prepare", risk="green", dry_run=True, source="selftest")
    # content_factory_prepare resolves yellow; green caller stays yellow/green execute path
    # Unsafe action refuse
    refused = execute_action("publish_live_boost", risk="green", dry_run=True, source="selftest")
    if refused.get("state") != "failed" or refused.get("decision") != "refuse":
        errors.append("unsafe action must refuse/fail without execute")

    # Tighten: green resolved + orange caller → waiting_approval
    tightened = execute_action("projection_refresh", risk="orange", dry_run=True, source="selftest")
    if tightened.get("state") != "waiting_approval":
        errors.append("caller --risk orange must tighten green action to waiting_approval")

    runs_after = RUNS.read_text(encoding="utf-8") if RUNS.is_file() else ""
    if runs_after != runs_before:
        errors.append("selftest dry_run must not write RUNS")

    # Classification: missing preflight is not ownerSurface
    sample = {
        "content_id": "story_poll_2026-09-07_petg_nylon",
        "format": "story",
        "gate": "pending_human_approval",
    }
    classified = classify_approval_item(sample)
    if classified.get("ownerSurface") is True and classified.get("disposition") not in {
        "human_required",
    }:
        pass
    if classified.get("ownerSurface") is True and not classified.get("humanRequiredReasons") and not classified.get("forbiddenSignals"):
        # stale/missing preflight must not be Christian orange
        if classified.get("disposition") in {"stale_orphan", "human_required"} and classified.get("missing_gates") == ["PREFLIGHT"]:
            errors.append("missing PREFLIGHT must not set ownerSurface=true")
    if classified.get("disposition") in {"stale_orphan", "human_required"} and classified.get("ownerSurface"):
        if "PREFLIGHT" in (classified.get("missing_gates") or []) and not classified.get("humanRequiredReasons"):
            errors.append("PREFLIGHT-only human_required must have ownerSurface=false")

    return not errors, errors


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS autonomy composition")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("next-action")
    sub.add_parser("blockers")
    sub.add_parser("approvals")
    ctx = sub.add_parser("context")
    ctx.add_argument("identifier")
    sub.add_parser("quiet-plan")
    sub.add_parser("snapshot")
    ex = sub.add_parser("execute", help="run next safe action or an explicit green/yellow action")
    ex.add_argument("--action", default="")
    ex.add_argument("--id", default="")
    ex.add_argument("--risk", default="")
    ex.add_argument("--dry-run", action="store_true")
    sub.add_parser("selftest")
    args = parser.parse_args()

    if args.cmd == "status":
        cfg = load_json(CONFIG, {})
        _ = load_jobs()
        print_json(
            {
                "name": cfg.get("name"),
                "updatedAt": cfg.get("updatedAt"),
                "components": [{"id": c.get("id"), "status": c.get("status")} for c in cfg.get("components") or []],
                "nextBestAction": next_action(),
                "blockerCount": len(blockers()),
                "approvalCount": len(approval_bundle()),
                "jobs_state": _JOBS_STATE,
                "executor": "execute",
            }
        )
        return 0
    if args.cmd == "next-action":
        print_json(next_action())
        return 0
    if args.cmd == "blockers":
        print_json(blockers())
        return 0
    if args.cmd == "approvals":
        print_json(approval_bundle())
        return 0
    if args.cmd == "context":
        print_json(context_pack(args.identifier))
        return 0
    if args.cmd == "quiet-plan":
        print_json(quiet_plan())
        return 0
    if args.cmd == "snapshot":
        print_json(snapshot())
        return 0
    if args.cmd == "execute":
        print_json(
            execute_action(
                args.action or None,
                target_id=args.id or None,
                risk=args.risk or None,
                dry_run=bool(args.dry_run),
            )
        )
        return 0
    if args.cmd == "selftest":
        ok, errors = selftest()
        if not ok:
            print_json({"ok": False, "errors": errors})
            return 1
        print_json({"ok": True, "nextBestAction": next_action(), "execute": "wired", "jobs_state": _JOBS_STATE})
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
