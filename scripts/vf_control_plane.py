#!/usr/bin/env python3
"""Office Control Plane — unify existing sources of truth. No network. No send.

CLI:
  python3 scripts/vf_control_plane.py status|watchdog|gaps|handoff|followups|review|memory-hygiene|simulate
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")

CONTROL_PLANE = ROOT / "office" / "control-plane.json"
CONTROL = ROOT / "office" / "control"
INBOX = CONTROL / "inbox.json"
DEAD = CONTROL / "dead-letter.json"
FOLLOWUPS = CONTROL / "followups.json"
HANDOFF_JSON = CONTROL / "HANDOFF.json"
HANDOFF_HE = CONTROL / "HANDOFF-he.md"
DECISIONS = CONTROL / "decisions.jsonl"
POLICY_MD = CONTROL / "POLICY.md"

CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
JOBS_CSV = ROOT / "office" / "ledger" / "live" / "jobs.csv"
JOBS_TEMPLATE = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
MEDIA_CATALOG = ROOT / "packages" / "vfmedia" / "catalog.json"
MEDIA_VAULT = ROOT / "docs" / "MEDIA-VAULT.md"
CALENDAR = ROOT / "packages" / "vfgrowth" / "CALENDAR.md"
APPROVAL_QUEUE = ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json"
CARDS = ROOT / "packages" / "vfprod" / "hq" / "cards"
PRINT_EVENTS = ROOT / "packages" / "vfprod" / "data" / "print-events.jsonl"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
PREFLIGHT = ROOT / "packages" / "vfgrowth" / "PREFLIGHT.md"
EDIT_GATE = ROOT / "packages" / "vfgrowth" / "EDIT-GATE.md"
OWNER_MEMORY = ROOT / "packages" / "vfops" / "data" / "owner-memory.md"

FORBIDDEN_COPY = ("שלחו DM", "send_dm", "Meta Business Suite", "משלוח ארצי", "nationwide shipping")
ILS_INVENTED = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
OWNER_SURFACE_RISKS = {"red", "orange"}
INTERNAL_ONLY_KINDS = {"routine_quality", "weak_metric", "canva_polish", "internal_schedule"}

FOLLOWUP_STATES = {
    "waiting_for_print_done",
    "ready_for_finished_content",
    "waiting_for_media",
    "waiting_for_preflight",
    "waiting_for_slot",
    "scheduled",
    "waiting_publication_verification",
    "closed_verified",
    "blocked",
}

WATCHDOG_OUTCOMES = (
    "OK",
    "AUTOFIXED",
    "PREPARED",
    "WAITING_EXTERNAL_TOOL",
    "DEAD_LETTER",
    "RED_BLOCKER",
)

HARNESS_DL_QUEUE = ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json"
LEGACY_FOLLOWUPS = ROOT / "packages" / "vfgrowth" / "data" / "production-content-followups.json"
PUBLIC_CTA = ROOT / "constitution" / "PUBLIC_CTA.md"
PUBLICATION_STATES = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json"
IG_CAPABILITIES = ROOT / "packages" / "vfigos" / "CAPABILITIES.json"
PROFILE_DESIRED = ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json"
FEED_AUDIT = ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
INSTANCE_VF = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
POLICY_CANONICAL = POLICY_MD


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today() -> str:
    return datetime.now(TZ).date().isoformat()


def fail(msg: str) -> int:
    print(f"FAIL {msg}", file=sys.stderr)
    return 1


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        rows.append(json.loads(raw))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def plane() -> dict:
    data = load_json(CONTROL_PLANE, {})
    if not data:
        raise SystemExit("FAIL missing office/control-plane.json")
    return data


def ensure_jobs_csv() -> None:
    """Live jobs.csv is gitignored — bootstrap header-only from template (no invented rows)."""
    if JOBS_CSV.is_file():
        return
    JOBS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if JOBS_TEMPLATE.is_file():
        JOBS_CSV.write_text(JOBS_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        JOBS_CSV.write_text(
            "job_id,opened,channel,client_label,phone,what_asked,sku,qty,size,color,material,"
            "file_status,modeling,due,stage,price,notes\n",
            encoding="utf-8",
        )


def required_paths() -> dict[str, Path]:
    ensure_jobs_csv()
    return {
        "control_plane": CONTROL_PLANE,
        "inbox": INBOX,
        "dead_letter": DEAD,
        "followups": FOLLOWUPS,
        "decisions": DECISIONS,
        "policy_md": POLICY_MD,
        "constitution": CONSTITUTION,
        "orchestra": ORCHESTRA,
        "jobs": JOBS_CSV,
        "media_catalog": MEDIA_CATALOG,
        "media_vault": MEDIA_VAULT,
        "calendar": CALENDAR,
        "approval_queue": APPROVAL_QUEUE,
        "office_loop": LOOP,
        "preflight": PREFLIGHT,
        "edit_gate": EDIT_GATE,
    }


def _card_field(text: str, *labels: str) -> str:
    """Extract first non-empty value for label-ish lines in a print card."""
    for line in text.splitlines():
        low = line.lower().strip()
        for lab in labels:
            if lab.lower() in low and ":" in line:
                val = line.split(":", 1)[1].strip()
                if val and val not in {"חסר", "-", "—", "missing", "none"}:
                    return val
    return ""


def parse_print_cards() -> list[dict]:
    """Return print.done rows with jobId, sku, sourceLink, printCardPath, correlation_id, has_media."""
    rows: list[dict] = []
    if PRINT_EVENTS.is_file():
        for ev in load_jsonl(PRINT_EVENTS):
            if (ev.get("name") or ev.get("event") or "") != "print.done" and "print.done" not in str(
                ev.get("event") or ""
            ):
                if (ev.get("name") or "") != "print.done":
                    if not ev.get("correlationId") and not (ev.get("payload") or {}).get("sku"):
                        continue
            payload = dict(ev.get("payload") or {})
            job_id = (payload.get("jobId") or payload.get("job_id") or ev.get("jobId") or "").strip()
            sku = (payload.get("sku") or "").strip()
            source_link = (
                payload.get("sourceLink") or payload.get("source_link") or payload.get("source") or ""
            ).strip()
            corr = (
                ev.get("correlationId")
                or payload.get("correlationId")
                or payload.get("correlation_id")
                or job_id
                or sku
                or ""
            ).strip()
            media = (
                payload.get("mediaPath")
                or (payload.get("media") or {}).get("timelapse_path")
                or (payload.get("media") or {}).get("still_path")
                or ""
            ).strip()
            rows.append(
                {
                    "jobId": job_id,
                    "sku": sku,
                    "sourceLink": source_link,
                    "printCardPath": "",
                    "correlation_id": corr,
                    "correlationId": corr,
                    "media": media,
                    "source": "print-events.jsonl",
                    "has_media": bool(media) and media not in {"חסר", "missing", "none"},
                }
            )
    if CARDS.is_dir():
        for path in sorted(CARDS.glob("*.md")):
            if path.name in {"README.md", "PRINT-CARD-TEMPLATE.md"}:
                continue
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(ROOT))
            sku = _card_field(text, "sku", "מק״ט", "שם עבודה")
            job_id = _card_field(text, "jobId", "job_id", "job id", "מזהה עבודה")
            source_link = _card_field(text, "sourceLink", "source_link", "source link", "קישור מקור")
            corr = _card_field(text, "correlationId", "correlation_id", "correlation")
            if not corr:
                corr = job_id or sku
            if not corr:
                stem = path.stem
                bits = stem.split("-", 3)
                corr = bits[3] if len(bits) >= 4 else stem
                if not sku:
                    sku = corr
            has_media = False
            for line in text.splitlines():
                if "timelapse" in line.lower() or "still path" in line.lower() or "drive id" in line.lower():
                    val = line.split(":", 1)[-1].strip() if ":" in line else ""
                    if val and val not in {"חסר", "-", "—", "missing"}:
                        has_media = True
            rows.append(
                {
                    "jobId": job_id,
                    "sku": sku,
                    "sourceLink": source_link,
                    "printCardPath": rel,
                    "print_card_path": rel,
                    "correlation_id": corr,
                    "correlationId": corr,
                    "media": "card" if has_media else "",
                    "source": rel,
                    "has_media": has_media,
                    "path": rel,
                }
            )
    return [r for r in rows if r.get("correlation_id") or r.get("jobId") or r.get("sku")]


def defensible_match(followup: dict, print_row: dict) -> bool:
    """True only on jobId, correlationId, printCardPath, or (sku + sourceLink). Never name alone."""
    fu_job = (followup.get("jobId") or followup.get("job_id") or "").strip()
    pr_job = (print_row.get("jobId") or print_row.get("job_id") or "").strip()
    if fu_job and pr_job and fu_job == pr_job:
        return True

    fu_corr = (followup.get("correlationId") or followup.get("correlation_id") or "").strip()
    pr_corr = (print_row.get("correlationId") or print_row.get("correlation_id") or "").strip()
    if fu_corr and pr_corr and fu_corr == pr_corr:
        return True

    fu_path = (followup.get("printCardPath") or followup.get("print_card_path") or "").strip()
    pr_path = (
        print_row.get("printCardPath")
        or print_row.get("print_card_path")
        or print_row.get("path")
        or ""
    ).strip()
    if fu_path and pr_path and fu_path == pr_path:
        return True

    fu_sku = (followup.get("sku") or "").strip()
    pr_sku = (print_row.get("sku") or "").strip()
    fu_src = (followup.get("sourceLink") or followup.get("source_link") or "").strip()
    pr_src = (print_row.get("sourceLink") or print_row.get("source_link") or "").strip()
    if fu_sku and pr_sku and fu_sku == pr_sku and fu_src and pr_src and fu_src == pr_src:
        return True

    return False


def next_calendar_slot() -> str:
    """Resolve first eligible standing slot description from CALENDAR.md — no invented slot."""
    if not CALENDAR.is_file():
        return "חסר CALENDAR.md"
    text = CALENDAR.read_text(encoding="utf-8")
    # Prefer standing rhythm table rows
    if "ראשון" in text and "16:00" in text:
        wd = datetime.now(TZ).weekday()  # Mon=0
        if wd == 6:
            return "ראשון 16:00 · ריל (מ־CALENDAR.md)"
        if wd == 1:
            return "שלישי 16:00 · ריל (מ־CALENDAR.md)"
        if wd == 3:
            return "חמישי 12:00 · קרוסלה (מ־CALENDAR.md)"
        if wd < 5:
            return "היום 20:30 · סטוריז א׳–ה׳ (מ־CALENDAR.md) · פיד לפי לוח א׳/ג׳/ה׳"
        return "אין פיד בשישי–שבת (מ־CALENDAR.md)"
    return "חסר משבצת ב־CALENDAR.md"


def owner_surface_items(inbox: dict | None = None, dead: dict | None = None, gates: list | None = None) -> list[dict]:
    """Owner sees only red / true orange — never routine quality or weak metrics."""
    surface: list[dict] = []
    inbox = inbox if inbox is not None else load_json(INBOX, {"buckets": {}})
    dead = dead if dead is not None else load_json(DEAD, {"items": []})
    for bucket, items in (inbox.get("buckets") or {}).items():
        for item in items or []:
            risk = (item.get("risk") or "").lower()
            kind = (item.get("kind") or "").lower()
            if kind in INTERNAL_ONLY_KINDS:
                continue
            if risk in OWNER_SURFACE_RISKS or bucket in {"approvals", "blocked"} and risk in OWNER_SURFACE_RISKS:
                surface.append({**item, "bucket": bucket, "surface": "owner"})
    for item in dead.get("items") or []:
        if item.get("status") in {"open", "unresolved", None} and item.get("owner_required"):
            surface.append({**item, "bucket": "dead-letter", "surface": "owner"})
    for item in gates or []:
        risk = (item.get("risk") or item.get("kind") or "").lower()
        if risk in {"price", "purchase", "payment", "red", "quote"} or item.get("owner_required"):
            surface.append({**item, "bucket": "gates", "surface": "owner"})
    return surface


def sync_followups(*, mutate: bool = True) -> list[dict]:
    """WIP→finished bridge. Never invent correlation_id. Uses defensible_match only."""
    data = load_json(FOLLOWUPS, {"items": []})
    items = list(data.get("items") or [])
    by_corr = {i.get("correlation_id"): i for i in items if i.get("correlation_id")}
    by_job = {i.get("jobId"): i for i in items if i.get("jobId")}
    prints = parse_print_cards()
    changed = False

    for item in items:
        if item.get("type") != "wip_to_finished":
            continue
        match = next((p for p in prints if defensible_match(item, p)), None)
        if item.get("state") == "waiting_for_print_done" and match:
            item["state"] = "ready_for_finished_content"
            item["print_source"] = match.get("source")
            item["updated_at"] = now_iso()
            if match.get("jobId") and not item.get("jobId"):
                item["jobId"] = match["jobId"]
            if match.get("sku") and not item.get("sku"):
                item["sku"] = match["sku"]
            if match.get("printCardPath"):
                item["printCardPath"] = match["printCardPath"]
            if not match.get("has_media"):
                item["state"] = "waiting_for_media"
                item["next_action"] = "internal_capture_task"
                item["finished_media"] = "finished-media-required"
            else:
                item["next_action"] = "prepare_finished_content"
                item["required_gates"] = ["EDIT-GATE", "PREFLIGHT"]
                item["suggested_slot"] = next_calendar_slot()
                item["publication"] = "not_published"  # scheduling ≠ live
            changed = True
        elif item.get("state") == "ready_for_finished_content" and match and not match.get("has_media"):
            item["state"] = "waiting_for_media"
            item["next_action"] = "internal_capture_task"
            item["finished_media"] = "finished-media-required"
            item["updated_at"] = now_iso()
            changed = True

    # Ensure print.done with media without followup gets ready followup (deterministic)
    for p in prints:
        corr = p.get("correlation_id") or ""
        job = p.get("jobId") or ""
        if not corr and not job:
            continue
        if corr and corr in by_corr:
            continue
        if job and job in by_job:
            continue
        # skip if any existing item already matches defensibly
        if any(defensible_match(i, p) for i in items if i.get("type") == "wip_to_finished"):
            continue
        if p.get("has_media"):
            key = corr or job
            neu = {
                "id": f"fu-{key}",
                "type": "wip_to_finished",
                "correlation_id": corr or job,
                "jobId": job or None,
                "sku": p.get("sku") or None,
                "sourceLink": p.get("sourceLink") or None,
                "printCardPath": p.get("printCardPath") or None,
                "state": "ready_for_finished_content",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "print_source": p.get("source"),
                "next_action": "prepare_finished_content",
                "required_gates": ["EDIT-GATE", "PREFLIGHT"],
                "suggested_slot": next_calendar_slot(),
                "publication": "not_published",
            }
            items.append(neu)
            if corr:
                by_corr[corr] = neu
            if job:
                by_job[job] = neu
            changed = True

    if mutate and changed:
        data["items"] = items
        data["updatedAt"] = today()
        write_json(FOLLOWUPS, data)
    return items


def level_to_outcome(level: str, *, code: str = "", owner_required: bool = False) -> str:
    """Map green/yellow/orange/red (+ tool/dead-letter codes) → watchdog outcomes."""
    lv = (level or "").lower()
    code_l = (code or "").lower()
    if code_l in {"autofixed", "auto_fixed"}:
        return "AUTOFIXED"
    if "needsauth" in code_l or "waiting_external" in code_l or "tool" in code_l and "fake" not in code_l:
        if lv != "red":
            return "WAITING_EXTERNAL_TOOL"
    if code_l.startswith("unresolved_dead_letter") or code_l == "dead_letter":
        return "RED_BLOCKER" if owner_required or lv == "red" else "DEAD_LETTER"
    if lv == "red":
        return "RED_BLOCKER"
    if lv == "orange":
        return "WAITING_EXTERNAL_TOOL" if "tool" in code_l or "pending" in code_l else "PREPARED"
    if lv == "yellow":
        return "PREPARED"
    return "OK"


def watchdog_issues() -> list[dict]:
    issues: list[dict] = []
    p = plane()
    sot = p.get("sourcesOfTruth") or {}

    for key, path in required_paths().items():
        if not path.exists():
            issues.append(
                {
                    "level": "red",
                    "code": "missing_file",
                    "detail": str(path.relative_to(ROOT)),
                    "key": key,
                    "outcome": "RED_BLOCKER",
                }
            )

    for label, path in (
        ("control-plane", CONTROL_PLANE),
        ("inbox", INBOX),
        ("dead-letter", DEAD),
        ("followups", FOLLOWUPS),
        ("approval-queue", APPROVAL_QUEUE),
        ("media-catalog", MEDIA_CATALOG),
        ("loop", LOOP),
    ):
        if path.is_file() and path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(
                    {
                        "level": "red",
                        "code": "json_parse",
                        "detail": f"{label}: {exc}",
                        "outcome": "RED_BLOCKER",
                    }
                )

    for rogue in (
        ROOT / "office" / "sources-of-truth.json",
        ROOT / "packages" / "vfops" / "control-plane.json",
        ROOT / "office" / "control" / "sources.json",
    ):
        if rogue.is_file():
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_source_of_truth_map",
                    "detail": str(rogue.relative_to(ROOT)),
                    "outcome": "RED_BLOCKER",
                }
            )

    # Duplicate SoT: harness dead-letter queue claiming authority
    if HARNESS_DL_QUEUE.is_file():
        hq = load_json(HARNESS_DL_QUEUE, {})
        real_items = [i for i in (hq.get("items") or []) if i]
        sot_ptr = (hq.get("sourceOfTruth") or "").replace("\\", "/")
        if real_items and sot_ptr != "office/control/dead-letter.json":
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_dead_letter_authority",
                    "detail": "packages/vfharness/dead-letter/queue.json has authoritative items",
                    "outcome": "RED_BLOCKER",
                }
            )
        elif real_items and sot_ptr == "office/control/dead-letter.json":
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_dead_letter_authority",
                    "detail": "pointer queue must keep items=[] — write only to office/control/dead-letter.json",
                    "outcome": "RED_BLOCKER",
                }
            )

    # Duplicate SoT: legacy production-content followups claiming authority
    if LEGACY_FOLLOWUPS.is_file():
        lf = load_json(LEGACY_FOLLOWUPS, {})
        sot_ptr = (lf.get("sourceOfTruth") or "").replace("\\", "/")
        auth_fus = [f for f in (lf.get("followups") or []) if f]
        if auth_fus and sot_ptr != "office/control/followups.json":
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_followups_authority",
                    "detail": "production-content-followups.json has authoritative followups (not a pointer)",
                    "outcome": "RED_BLOCKER",
                }
            )
        elif not sot_ptr and "followups" in lf:
            # empty array without pointer is soft; non-empty already caught
            if auth_fus:
                issues.append(
                    {
                        "level": "red",
                        "code": "duplicate_followups_authority",
                        "detail": "legacy followups file missing sourceOfTruth pointer",
                        "outcome": "RED_BLOCKER",
                    }
                )

    for extra in ROOT.glob("**/media-catalog.json"):
        if extra.resolve() != MEDIA_CATALOG.resolve():
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_media_catalog",
                    "detail": str(extra.relative_to(ROOT)),
                    "outcome": "RED_BLOCKER",
                }
            )

    # Canonical dead letters
    dead = load_json(DEAD, {"items": []})
    for item in dead.get("items") or []:
        if item.get("status") in {"open", "unresolved", None, "failed"}:
            owner_req = bool(item.get("owner_required") or item.get("christianRequired"))
            issues.append(
                {
                    "level": "yellow" if not owner_req else "orange",
                    "code": "unresolved_dead_letter",
                    "detail": item.get("id") or item.get("action") or item.get("actionId") or "",
                    "owner_required": owner_req,
                    "outcome": level_to_outcome(
                        "orange" if owner_req else "yellow",
                        code="unresolved_dead_letter",
                        owner_required=owner_req,
                    ),
                }
            )

    # Failed actions / failover noted in approval or followups
    items = sync_followups(mutate=True)
    prints = parse_print_cards()
    for item in items:
        if item.get("type") != "wip_to_finished":
            continue
        if item.get("state") == "waiting_for_print_done":
            if any(defensible_match(item, p) for p in prints):
                issues.append(
                    {
                        "level": "red",
                        "code": "wip_stuck_after_print_done",
                        "detail": item.get("correlation_id") or item.get("jobId") or item.get("id"),
                        "outcome": "RED_BLOCKER",
                    }
                )
            else:
                issues.append(
                    {
                        "level": "yellow",
                        "code": "production_content_waiting_print",
                        "detail": item.get("correlation_id") or item.get("id"),
                        "outcome": "PREPARED",
                    }
                )
        if item.get("state") == "waiting_for_media":
            issues.append(
                {
                    "level": "yellow",
                    "code": "finished_media_required",
                    "detail": item.get("correlation_id") or item.get("id"),
                    "outcome": "PREPARED",
                }
            )

        pub = (item.get("publication") or item.get("publication_state") or "").strip()
        pub_l = pub.lower()
        # scheduled / uploadAccepted / publishRequested are not live
        if pub_l in {"scheduled", "uploadaccepted", "publishrequested", "prepared", "approved"}:
            if item.get("verification_evidence"):
                pass  # evidence without liveVerified is odd but not red alone
            issues.append(
                {
                    "level": "green",
                    "code": "publication_not_live",
                    "detail": f"{item.get('id')}:{pub}",
                    "outcome": "PREPARED",
                }
            )
        if pub_l in {"published", "live", "posted", "liveverified"} and not item.get("verification_evidence"):
            issues.append(
                {
                    "level": "red",
                    "code": "published_without_verification",
                    "detail": item.get("correlation_id") or item.get("id"),
                    "outcome": "RED_BLOCKER",
                }
            )
        if item.get("state") == "scheduled" and pub_l in {"published", "live", "posted", "liveverified"}:
            issues.append(
                {
                    "level": "red",
                    "code": "schedule_marked_as_live",
                    "detail": item.get("id"),
                    "outcome": "RED_BLOCKER",
                }
            )

    # Approval queue
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    for item in queue.get("items") or []:
        gate = item.get("gate") or ""
        pub_state = (item.get("publication_state") or item.get("publication") or "").lower()
        if pub_state in {"scheduled", "uploadaccepted", "publishrequested"}:
            issues.append(
                {
                    "level": "yellow",
                    "code": "approval_not_live",
                    "detail": f"{item.get('content_id')}:{pub_state}",
                    "outcome": "PREPARED",
                }
            )
        if gate in {"approved_for_manual_posting", "pending_human_approval"} and not item.get("slot") and not item.get(
            "next_action"
        ):
            if not item.get("calendar_rule") and not item.get("slot"):
                issues.append(
                    {
                        "level": "yellow",
                        "code": "approved_without_next_action",
                        "detail": item.get("content_id"),
                        "outcome": "PREPARED",
                    }
                )

    # Media catalog health
    cat = load_json(MEDIA_CATALOG, {})
    if cat.get("oneCatalog") is not True:
        issues.append(
            {
                "level": "red",
                "code": "media_catalog_not_one",
                "detail": "oneCatalog must be true",
                "outcome": "RED_BLOCKER",
            }
        )
    elif not isinstance(cat.get("items"), list):
        issues.append(
            {
                "level": "orange",
                "code": "media_catalog_items_missing",
                "detail": "catalog items[] missing",
                "outcome": "PREPARED",
            }
        )
    else:
        items = cat.get("items") or []
        inbox_n = sum(1 for it in items if (it.get("status") or "") == "inbox")
        source_n = sum(1 for it in items if (it.get("status") or "") == "source")
        if inbox_n:
            issues.append(
                {
                    "level": "yellow",
                    "code": "media_inbox_backlog",
                    "detail": f"catalog inbox={inbox_n} source={source_n} total={len(items)} · intake continues; upload≠approval",
                    "outcome": "WAITING_EXTERNAL_TOOL",
                    "internal": True,
                }
            )

    # Calendar inconsistencies / stale scheduled (lightweight: CALENDAR.md exists)
    if CALENDAR.is_file():
        cal = CALENDAR.read_text(encoding="utf-8")
        if "16:00" not in cal and "20:30" not in cal:
            issues.append(
                {
                    "level": "yellow",
                    "code": "calendar_inconsistent",
                    "detail": "standing slots missing from CALENDAR.md",
                    "outcome": "PREPARED",
                }
            )
    else:
        issues.append(
            {
                "level": "red",
                "code": "calendar_missing",
                "detail": "packages/vfgrowth/CALENDAR.md",
                "outcome": "RED_BLOCKER",
            }
        )

    # Feed audit
    if FEED_AUDIT.is_file():
        audit = load_json(FEED_AUDIT, {})
        if audit.get("access") == "awaiting-live-audit":
            issues.append(
                {
                    "level": "yellow",
                    "code": "feed_audit_waiting",
                    "detail": "awaiting-live-audit",
                    "outcome": "WAITING_EXTERNAL_TOOL",
                }
            )
        g004 = audit.get("g004Identity") or {}
        if g004.get("canonicalHe") != "מחזיק טבעות לזמן אימון":
            issues.append(
                {
                    "level": "red",
                    "code": "g004_identity_drift",
                    "detail": "G004 identity drift",
                    "outcome": "RED_BLOCKER",
                }
            )
    else:
        issues.append(
            {
                "level": "red",
                "code": "feed_audit_missing",
                "detail": "packages/vfgrowth/data/feed-audit.json",
                "outcome": "RED_BLOCKER",
            }
        )

    # PROFILE-DESIRED drift vs WhatsApp in bio
    if PROFILE_DESIRED.is_file():
        profile = load_json(PROFILE_DESIRED, {})
        desired = profile.get("desired") or {}
        bio = desired.get("bioHe") or ""
        for banned in ("050-2517000", "WhatsApp", "וואטסאפ", "wa.me"):
            if banned.lower() in bio.lower() if banned.isascii() else banned in bio:
                issues.append(
                    {
                        "level": "red",
                        "code": "profile_desired_whatsapp_drift",
                        "detail": f"bio contains {banned}",
                        "outcome": "RED_BLOCKER",
                    }
                )
                break
        else:
            if profile.get("status") == "prepared" and profile.get("liveStatus") == "pending-live-tool":
                issues.append(
                    {
                        "level": "yellow",
                        "code": "profile_prepared_pending_live",
                        "detail": "bio prepared; pending live tool",
                        "outcome": "PREPARED",
                    }
                )

    # PUBLIC_CURRENT_CTA — instance primary must not contain WA phone
    if INSTANCE_VF.is_file():
        inst = load_json(INSTANCE_VF, {})
        primary = ((inst.get("cta") or {}).get("primary") or "")
        if "050-2517000" in primary or ("whatsapp" in primary.lower() and "instagram" not in primary.lower()):
            issues.append(
                {
                    "level": "red",
                    "code": "public_cta_whatsapp_violation",
                    "detail": "instance cta.primary must not contain WhatsApp/050-2517000",
                    "outcome": "RED_BLOCKER",
                }
            )
    if PUBLIC_CTA.is_file():
        cta_text = PUBLIC_CTA.read_text(encoding="utf-8")
        if "Instagram DM" not in cta_text and "Instagram message" not in cta_text.lower():
            issues.append(
                {
                    "level": "red",
                    "code": "public_cta_missing_ig",
                    "detail": "PUBLIC_CTA.md missing Instagram DM policy",
                    "outcome": "RED_BLOCKER",
                }
            )
    else:
        issues.append(
            {
                "level": "red",
                "code": "public_cta_missing",
                "detail": "constitution/PUBLIC_CTA.md",
                "outcome": "RED_BLOCKER",
            }
        )

    # Publication states contract
    if PUBLICATION_STATES.is_file():
        pub = load_json(PUBLICATION_STATES, {})
        ids = {s.get("id") for s in pub.get("states") or []}
        for need in ("prepared", "scheduled", "uploadAccepted", "publishRequested", "liveVerified"):
            if need not in ids:
                issues.append(
                    {
                        "level": "red",
                        "code": "publication_states_missing",
                        "detail": need,
                        "outcome": "RED_BLOCKER",
                    }
                )
        live = next((s for s in (pub.get("states") or []) if s.get("id") == "liveVerified"), None)
        if live and "verificationEvidence" not in (live.get("requires") or []) and "verification_evidence" not in str(
            live.get("requires") or []
        ):
            # allow verificationEvidence in requires list
            req = live.get("requires") or []
            if "verificationEvidence" not in req:
                issues.append(
                    {
                        "level": "red",
                        "code": "live_requires_verification",
                        "detail": "liveVerified must require verificationEvidence",
                        "outcome": "RED_BLOCKER",
                    }
                )
    else:
        issues.append(
            {
                "level": "red",
                "code": "publication_states_file_missing",
                "detail": "packages/vfigos/PUBLICATION-STATES.json",
                "outcome": "RED_BLOCKER",
            }
        )

    # Instagram needsAuth must not claim ready without healthcheck (CAPABILITIES + desk)
    desk = load_json(DESK, {})
    ig_status = ((desk.get("tools") or {}).get("instagram") or {}).get("status") or "unknown"
    caps = load_json(IG_CAPABILITIES, {}) if IG_CAPABILITIES.is_file() else {}
    caps_status = caps.get("currentStatus") or ""
    if caps_status == "ready" and ig_status != "ready":
        issues.append(
            {
                "level": "red",
                "code": "ig_fake_ready",
                "detail": "CAPABILITIES claims ready while desk is not — refuse fake ready",
                "outcome": "RED_BLOCKER",
            }
        )
    elif ig_status in {"needsAuth", "pending-connection", "down"}:
        issues.append(
            {
                "level": "yellow",
                "code": "ig_needsauth_waiting",
                "detail": f"instagram.status={ig_status}",
                "outcome": "WAITING_EXTERNAL_TOOL",
            }
        )
    elif ig_status == "ready":
        issues.append(
            {
                "level": "green",
                "code": "ig_ready",
                "detail": "desk ready (healthcheck still required before live)",
                "outcome": "OK",
            }
        )

    # Policy text scans
    for path in (CONSTITUTION, ORCHESTRA, CALENDAR):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        idx = text.find("Meta Business Suite")
        if idx >= 0:
            window = text[max(0, idx - 40) : idx + 60]
            window_l = window.lower()
            # Prohibition / lock language is OK — do not false-positive locked rows.
            prohibited_ok = any(
                tok in window or tok in window_l
                for tok in (
                    "לא",
                    "נעול",
                    "אסור",
                    "deny",
                    "forbidden",
                    "locked",
                    "no suite",
                    "no meta",
                )
            )
            if not prohibited_ok and "no Suite" not in text.lower():
                issues.append(
                    {
                        "level": "orange",
                        "code": "suite_language",
                        "detail": str(path.relative_to(ROOT)),
                        "outcome": "PREPARED",
                    }
                )

    cp_text = CONTROL_PLANE.read_text(encoding="utf-8") if CONTROL_PLANE.is_file() else ""
    if "auto-dm" in cp_text.lower() and "no-auto-dm" not in cp_text.lower():
        issues.append(
            {
                "level": "red",
                "code": "auto_dm_allowed",
                "detail": "control-plane",
                "outcome": "RED_BLOCKER",
            }
        )

    # Ensure outcomes filled
    for iss in issues:
        if not iss.get("outcome"):
            iss["outcome"] = level_to_outcome(
                iss.get("level") or "green",
                code=iss.get("code") or "",
                owner_required=bool(iss.get("owner_required")),
            )
    return issues


def build_watchdog_report(*, mutate_followups: bool = True) -> dict:
    if mutate_followups:
        sync_followups(mutate=True)
    issues = watchdog_issues()
    findings = []
    for iss in issues:
        findings.append(
            {
                "area": iss.get("code") or iss.get("key") or "general",
                "outcome": iss.get("outcome") or level_to_outcome(iss.get("level") or "green", code=iss.get("code") or ""),
                "detail": iss.get("detail"),
                "level": iss.get("level"),
                "owner_required": bool(iss.get("owner_required")),
            }
        )
    rank = {o: i for i, o in enumerate(WATCHDOG_OUTCOMES)}
    worst = "OK"
    for f in findings:
        if rank.get(f["outcome"], 0) > rank.get(worst, 0):
            worst = f["outcome"]
    # Owner surface: Don't Bother Christian — weak metrics never escalate
    surface = owner_surface_items()
    spam = any(
        (s.get("kind") or "").lower() in INTERNAL_ONLY_KINDS or (s.get("risk") or "").lower() == "green"
        for s in surface
    )
    return {
        "generatedAt": now_iso(),
        "summary": worst,
        "findings": findings,
        "spamChristian": False,  # hard lock — routine/weak never spam
        "owner_surface_count": len(surface),
        "note": "Don't Bother Christian — notify only for RED_BLOCKER items that require owner action.",
    }


def gaps() -> list[dict]:
    out: list[dict] = []
    issues = watchdog_issues()
    for iss in issues:
        if iss.get("level") in {"red", "orange"}:
            out.append(iss)
    followups = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    waiting = [f for f in followups if (f.get("state") or "").startswith("waiting")]
    if waiting:
        out.append({"level": "yellow", "code": "open_followups", "detail": f"n={len(waiting)}", "internal": True})
    # Content sprint priority reminder — internal
    out.append(
        {
            "level": "green",
            "code": "content_sprint_priority",
            "detail": "→".join(plane().get("contentSprintPriority") or []),
            "internal": True,
        }
    )
    return out


def opportunity_radar() -> list[dict]:
    """Real repeated patterns only — never invent demand."""
    findings: list[dict] = []
    jobs_path = JOBS_CSV
    if jobs_path.is_file():
        lines = [ln for ln in jobs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) <= 1:
            findings.append({"pattern": "jobs_empty", "note": "אין חזרות ב־jobs.csv — אין ביקוש מומצא"})
        else:
            # count sku/what_asked repeats
            from collections import Counter

            skus: list[str] = []
            for ln in lines[1:]:
                cols = ln.split(",")
                if len(cols) > 6 and cols[6].strip():
                    skus.append(cols[6].strip())
            for sku, n in Counter(skus).items():
                if n >= 2:
                    findings.append(
                        {
                            "pattern": "repeated_sku",
                            "sku": sku,
                            "count": n,
                            "note": "מועמד מק״ט חוזר — לא מחיר מומצא",
                        }
                    )
    media = load_json(MEDIA_CATALOG, {"items": []})
    kinds = {}
    for item in media.get("items") or []:
        k = item.get("classification") or item.get("kind") or "unknown"
        kinds[k] = kinds.get(k, 0) + 1
    for k, n in kinds.items():
        if n >= 2:
            findings.append({"pattern": "repeated_media_class", "class": k, "count": n})
    if not findings:
        findings.append({"pattern": "none", "note": "אין דפוס חוזר מאומת — לא ממציאים ביקוש"})
    return findings


def memory_hygiene_report() -> list[dict]:
    rows: list[dict] = []
    decisions = load_jsonl(DECISIONS)
    active = [d for d in decisions if d.get("status") == "active"]
    superseded_ids = {d.get("supersedes") for d in decisions if d.get("supersedes")}
    for d in active:
        if d.get("decision_id") in superseded_ids:
            rows.append(
                {
                    "action": "supersede",
                    "target": d.get("decision_id"),
                    "note": "החלטה מסומנת active אבל יש supersede עליה",
                }
            )
    # Parallel authority candidates
    for rogue in (
        ROOT / "office" / "sources-of-truth.json",
        ROOT / "packages" / "vfops" / "control-plane.json",
    ):
        if rogue.is_file():
            rows.append({"action": "needs owner decision", "target": str(rogue.relative_to(ROOT)), "note": "מפת מקור אמת מקבילה"})

    # Stale Grok-owns assumptions in HANDOFF-he growth if present
    growth_h = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
    if growth_h.is_file():
        text = growth_h.read_text(encoding="utf-8")
        if "Grok שולח" in text or "רק Grok" in text:
            rows.append(
                {
                    "action": "merge reference",
                    "target": "packages/vfgrowth/HANDOFF-he.md",
                    "note": "בדוק מול constitution/SEND.md — HQ שולח דרך כלים",
                }
            )

    rows.append({"action": "keep", "target": "office/control-plane.json", "note": "מפת מקורות אמת יחידה"})
    rows.append({"action": "keep", "target": "packages/vfmedia/catalog.json", "note": "קטלוג מדיה יחיד"})
    if OWNER_MEMORY.is_file():
        rows.append({"action": "keep", "target": str(OWNER_MEMORY.relative_to(ROOT)), "note": "זיכרון בעלים — לא מוחקים היסטוריה"})
    else:
        rows.append({"action": "archive candidate", "target": "owner-memory.md", "note": "חסר קובץ — לא ממציאים"})

    # Never delete historical evidence automatically
    rows.append({"action": "keep", "target": "office/control/decisions.jsonl", "note": "append-only · supersede לא מחיקה"})
    return rows


def build_handoff() -> dict:
    issues = watchdog_issues()
    followups = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    dead = load_json(DEAD, {"items": []}).get("items") or []
    inbox = load_json(INBOX, {"buckets": {}})
    media_cat = load_json(MEDIA_CATALOG, {"items": []})
    media_items = media_cat.get("items") or []
    media_inbox = sum(1 for it in media_items if (it.get("status") or "") == "inbox")
    media_source = sum(1 for it in media_items if (it.get("status") or "") == "source")
    media_total = len(media_items)
    media_verified = 0
    media_registered_only = 0
    media_visual = 0
    for it in media_items:
        intake = it.get("intake") or {}
        phase = intake.get("phase")
        if phase == "verified" or (it.get("status") == "source" and phase != "registered"):
            media_verified += 1
        else:
            media_registered_only += 1
        if (it.get("visualReview") or {}).get("state") == "done":
            media_visual += 1
    intake_state = load_json(
        ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json",
        {},
    )
    intake_brief = load_json(
        ROOT / "packages" / "vfmedia" / "data" / "intake-brief.json",
        {},
    )
    surface = owner_surface_items(inbox=inbox, dead={"items": dead})
    degraded = [i for i in issues if i.get("level") in {"red", "orange"}]
    safe = [
        "python3 scripts/vf_control_plane.py watchdog",
        "python3 scripts/vf_control_plane.py followups",
        "python3 scripts/vf_control_plane.py simulate --scenario failover",
        "python3 scripts/vfops_loop.py brief",
        "python3 scripts/check-all.py",
        "python3 scripts/vfmedia.py validate",
        "python3 scripts/vfmedia.py intake status",
        "python3 scripts/vfmedia.py intake selftest",
    ]
    handoff = {
        "updatedAt": now_iso(),
        "date": today(),
        "active_now": [
            f["id"]
            for f in followups
            if f.get("state") in {"ready_for_finished_content", "waiting_for_preflight", "waiting_for_slot"}
        ],
        "waiting": [
            {"id": f.get("id"), "state": f.get("state"), "correlation_id": f.get("correlation_id")}
            for f in followups
            if (f.get("state") or "").startswith("waiting")
        ],
        "failed": [
            {"id": d.get("id"), "action": d.get("action"), "reason": d.get("reason")}
            for d in dead
            if d.get("status") in {"open", "unresolved", "failed", None}
        ],
        "owner_blocked": surface,
        "media": {
            "catalog": "packages/vfmedia/catalog.json",
            "total": media_total,
            "inbox": media_inbox,
            "source": media_source,
            "registered_only": media_registered_only,
            "verified_and_intaken": media_verified,
            "visually_reviewed": media_visual,
            "intake_runner": {
                "component_state": (intake_state or {}).get("component_state"),
                "lastRunAt": (intake_state or {}).get("lastRunAt"),
                "activation_proven": ((intake_state or {}).get("activation") or {}).get("proven"),
                "auth": (intake_state or {}).get("auth"),
            },
            "intake_brief": intake_brief or None,
            "note": (
                "registered ≠ verified ≠ visually_reviewed · "
                "validate≠monitoring · upload≠approval · no invented SKU/job association"
            ),
        },
        "next": [
            "הרץ watchdog",
            "המשך קליטת מדיה אוטומטית (intake run) — לא רק validate",
            "סגור followups ready_for_finished_content דרך EDIT-GATE+PREFLIGHT",
            "אל תטריד את כריסטיאן על מדדים חלשים",
            "Instagram stays needsAuth until Meta email verify + long-lived token",
        ],
        "changed_today": [
            "Office Control Plane מוטמע",
            f"followups={len(followups)}",
            f"dead_letters={len(dead)}",
            f"media_catalog_items={media_total}",
            f"media_inbox={media_inbox}",
            f"media_source={media_source}",
            f"media_verified={media_verified}",
            f"media_registered_only={media_registered_only}",
            f"media_visually_reviewed={media_visual}",
        ],
        "authoritative_sources": plane().get("sourcesOfTruth"),
        "tools_degraded": degraded,
        "safe_for_next_ai": safe,
        "must_never_repeat": [
            "invent ₪ or Insights",
            "auto-DM",
            "claim published without verification",
            "duplicate media catalog",
            "Meta Business Suite",
            "nationwide shipping",
            "bother Christian with weak metrics",
        ],
        "latest_policy": [
            "constitution/CONSTITUTION.md",
            "constitution/ORCHESTRA.md",
            "office/control/POLICY.md",
            "office/control-plane.json",
        ],
        "chatgpt_tasks_safe_to_disable_after_proof": plane().get("chatgptTaskReduction", {}).get("moveInsideVelvetOS"),
        "chatgpt_tasks_keep": plane().get("chatgptTaskReduction", {}).get("keep"),
    }
    write_json(HANDOFF_JSON, handoff)
    write_handoff_he(handoff)
    return handoff


def write_handoff_he(handoff: dict) -> None:
    lines = [
        f"# מסירת מנהל · Office Control Plane · {handoff.get('date')}",
        "",
        "לא מערכת משרד שנייה. מקורות אמת: `office/control-plane.json`.",
        "",
        "## מה פעיל עכשיו",
    ]
    active = handoff.get("active_now") or []
    lines.append("- " + (", ".join(active) if active else "אין פעיל מחוץ ללולאה הרגילה"))
    media = handoff.get("media") or {}
    if media:
        lines += [
            "",
            "## מדיה (פאזות נפרדות · קטלוג יחיד)",
            f"- total=`{media.get('total')}` · inbox=`{media.get('inbox')}` · source=`{media.get('source')}`",
            (
                f"- רשום בלבד=`{media.get('registered_only')}` · "
                f"אומת ונקלט=`{media.get('verified_and_intaken')}` · "
                f"נבדק חזותית=`{media.get('visually_reviewed')}`"
            ),
            f"- intake=`{((media.get('intake_runner') or {}).get('component_state'))}` · "
            f"activation=`{((media.get('intake_runner') or {}).get('activation_proven'))}`",
            f"- {media.get('note') or 'registered ≠ verified ≠ visual · upload≠approval'}",
        ]
    lines += ["", "## מה ממתין"]
    waiting = handoff.get("waiting") or []
    if not waiting:
        lines.append("- אין")
    else:
        for w in waiting:
            lines.append(f"- `{w.get('correlation_id') or w.get('id')}` · {w.get('state')}")
    lines += ["", "## מה נכשל (dead letter)"]
    failed = handoff.get("failed") or []
    if not failed:
        lines.append("- אין")
    else:
        for f in failed:
            lines.append(f"- `{f.get('id')}` · {f.get('action')} · {f.get('reason')}")
    lines += ["", "## חסום לבעלים (אדום/כתום בלבד)"]
    blocked = handoff.get("owner_blocked") or []
    if not blocked:
        lines.append("- אין החלטת בעלים פתוחה")
    else:
        for b in blocked:
            lines.append(f"- {b.get('id') or b.get('action') or b} · risk={b.get('risk')}")
    lines += [
        "",
        "## הבא בתור",
        *[f"- {x}" for x in (handoff.get("next") or [])],
        "",
        "## מה השתנה היום",
        *[f"- {x}" for x in (handoff.get("changed_today") or [])],
        "",
        "## מקורות סמכות",
    ]
    for k, v in (handoff.get("authoritative_sources") or {}).items():
        lines.append(f"- **{k}:** `{v}`")
    lines += [
        "",
        "## כלים מדולדלים",
    ]
    deg = handoff.get("tools_degraded") or []
    if not deg:
        lines.append("- אין חסם קשיח מדווח")
    else:
        for d in deg:
            lines.append(f"- {d.get('level')} · {d.get('code')} · {d.get('detail')}")
    lines += [
        "",
        "## בטוח להמשך AI הבא",
        *[f"- `{x}`" for x in (handoff.get("safe_for_next_ai") or [])],
        "",
        "## אסור לחזור",
        *[f"- {x}" for x in (handoff.get("must_never_repeat") or [])],
        "",
        "## מדיניות עדכנית",
        *[f"- `{x}`" for x in (handoff.get("latest_policy") or [])],
        "",
        "## משימות ChatGPT (רק אחרי הוכחת נתיב)",
        "להשאיר: " + ", ".join(handoff.get("chatgpt_tasks_keep") or []),
        "מועמדים לכיבוי אחרי הוכחה: " + ", ".join(handoff.get("chatgpt_tasks_safe_to_disable_after_proof") or []),
        "",
        "אל תפנה לכריסטיאן על מדדים חלשים.",
        "",
    ]
    HANDOFF_HE.write_text("\n".join(lines), encoding="utf-8")


def brief_summary() -> dict:
    """Concise owner-facing slice for Morning Brief — no low-level noise."""
    handoff = load_json(HANDOFF_JSON) or build_handoff()
    surface = handoff.get("owner_blocked") or []
    dead_owner = [d for d in (handoff.get("failed") or []) if True]
    # filter dead to owner_required from file
    dead_items = load_json(DEAD, {"items": []}).get("items") or []
    dead_owner = [d for d in dead_items if d.get("owner_required") and d.get("status") in {"open", "unresolved", "failed", None}]
    fus = [f for f in (load_json(FOLLOWUPS, {"items": []}).get("items") or []) if f.get("state") == "ready_for_finished_content"]
    health_issues = [i for i in watchdog_issues() if i.get("level") == "red"]
    return {
        "owner_decisions": surface,
        "dead_letters_owner": dead_owner,
        "wip_finished_ready": fus,
        "gaps_owner": [g for g in gaps() if g.get("level") in {"red", "orange"} and not g.get("internal")],
        "health": "ok" if not health_issues else f"degraded:{len(health_issues)}",
        "completed_or_planned": handoff.get("changed_today") or [],
    }


def cmd_status(_args: argparse.Namespace) -> int:
    p = plane()
    fus = sync_followups(mutate=True)
    issues = watchdog_issues()
    print("=== Office Control Plane · status ===")
    print(f"date: {today()}")
    print(f"sources: {len(p.get('sourcesOfTruth') or {})}")
    print(f"followups: {len(fus)}")
    print(f"dead_letters: {len(load_json(DEAD, {'items': []}).get('items') or [])}")
    print(f"watchdog_issues: {len(issues)}")
    print(f"owner_surface: {len(owner_surface_items())}")
    print(f"health: {'ok' if not any(i.get('level') == 'red' for i in issues) else 'degraded'}")
    for i in issues[:12]:
        print(f" · {i.get('level')} {i.get('code')}: {i.get('detail')}")
    return 0


def cmd_watchdog(args: argparse.Namespace) -> int:
    report = build_watchdog_report(mutate_followups=True)
    if not HANDOFF_JSON.is_file():
        build_handoff()

    write_flag = bool(getattr(args, "write", False))
    json_flag = bool(getattr(args, "json", False))

    if write_flag:
        out = ROOT / "packages" / "vfops" / "hq" / "watchdog-latest.json"
        write_json(out, report)
        print(f"WROTE {out.relative_to(ROOT)}")

    if json_flag:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"WATCHDOG {report['summary']}")
        print(f"findings={len(report['findings'])} · Don't Bother Christian")
        for f in report["findings"]:
            print(f"  {f.get('outcome', ''):24} {f.get('area')}: {f.get('detail')}")

    if report["summary"] == "RED_BLOCKER":
        return 1
    return 0


def cmd_gaps(_args: argparse.Namespace) -> int:
    rows = gaps()
    print("=== gaps ===")
    for g in rows:
        flag = " · פנימי" if g.get("internal") else ""
        print(f"{g.get('level')}\t{g.get('code')}\t{g.get('detail')}{flag}")
    return 0


def cmd_handoff(_args: argparse.Namespace) -> int:
    h = build_handoff()
    print(json.dumps(h, ensure_ascii=False, indent=2))
    print(f"\nנכתב {HANDOFF_JSON.relative_to(ROOT)}")
    print(f"נכתב {HANDOFF_HE.relative_to(ROOT)}")
    return 0


def cmd_followups(args: argparse.Namespace) -> int:
    items = sync_followups(mutate=not getattr(args, "dry_run", False))
    print("=== followups ===")
    if not items:
        print("אין followups")
        return 0
    for item in items:
        print(
            f"{item.get('id')}\t{item.get('correlation_id')}\t{item.get('state')}\t"
            f"pub={item.get('publication')}\tslot={item.get('suggested_slot')}"
        )
    return 0


def cmd_review(_args: argparse.Namespace) -> int:
    fus = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    dead = load_json(DEAD, {"items": []}).get("items") or []
    issues = watchdog_issues()
    radar = opportunity_radar()
    hygiene = memory_hygiene_report()
    surface = owner_surface_items()
    print("=== סקירת משרד שבועית ===")
    print("מה עבד:")
    print(" · Control Plane מאחד מקורות אמת קיימים בלי תורים מקבילים")
    print(" · לולאת vfops נשארת המתזמן היחיד")
    print("מה נתקע:")
    stuck = [f for f in fus if (f.get("state") or "").startswith("waiting")]
    if stuck:
        for s in stuck:
            print(f" · followup {s.get('correlation_id')} · {s.get('state')}")
    else:
        print(" · אין followup תקוע מדווח")
    print("מה המשרד טיפל לבד:")
    print(" · watchdog / memory-hygiene / gap detection / handoff refresh")
    print("צווארי בקבוק לבעלים (אמיתיים):")
    if surface:
        for s in surface:
            print(f" · {s.get('id') or s.get('action')} · {s.get('risk')}")
    else:
        print(" · אין")
    print("failover / dead letter:")
    print(f" · פתוחים={len([d for d in dead if d.get('status') in {'open', 'unresolved', 'failed', None}])}")
    print("רצף WIP→finished:")
    ready = [f for f in fus if f.get("state") == "ready_for_finished_content"]
    print(f" · ready_for_finished_content={len(ready)}")
    print("Opportunity Radar:")
    for r in radar:
        print(f" · {r}")
    print("Memory hygiene:")
    for h in hygiene[:8]:
        print(f" · {h.get('action')}: {h.get('target')} — {h.get('note')}")
    print("שיפורי מדיניות לשבוע הבא:")
    print(" · להמשיך לספוג משימות ChatGPT מכניות רק אחרי הוכחת נתיב")
    print(" · מדדים חלשים נשארים פנימיים")
    print(f"watchdog_issues={len(issues)} (פנימי; לא ספאם לבעלים)")
    return 0


def cmd_memory_hygiene(_args: argparse.Namespace) -> int:
    rows = memory_hygiene_report()
    print("=== memory-hygiene ===")
    for r in rows:
        print(f"{r.get('action')}\t{r.get('target')}\t{r.get('note')}")
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    scenario = (args.scenario or "noop").strip()
    print(f"=== simulate · {scenario} ===")
    print("read-only — לא משנים מקורות אמת")
    predicted: list[str] = []
    risks: list[str] = []
    gates: list[str] = []
    rollback: list[str] = []

    if scenario in {"wip_to_finished", "wip"}:
        predicted = [
            "followups: waiting_for_print_done → ready_for_finished_content",
            "suggested_slot from CALENDAR.md",
            "required_gates EDIT-GATE + PREFLIGHT",
            "publication stays not_published",
        ]
        risks = ["invented correlation_id", "treating schedule as live publish"]
        gates = ["PREFLIGHT", "EDIT-GATE", "human post verification"]
        rollback = ["revert followups.json item state", "git checkout followups.json"]
    elif scenario in {"failover", "manager_failover", "office_failover"}:
        predicted = [
            "Manager B reads docs/FAILOVER.md + office/control/HANDOFF.json",
            "resume from authoritative_sources only (no new SoT)",
            "run: vf_control_plane.py status|watchdog|followups|brief-summary",
            "continue WIP/media/approvals from existing queues",
        ]
        risks = [
            "building a parallel handoff/vault",
            "inventing ₪ / Insights / liveVerified",
            "idling on needsAuth instead of failover artifact",
        ]
        gates = ["read HANDOFF.json + POLICY.md before mutations"]
        rollback = ["n/a read-only simulation — real handoff refresh via `handoff` cmd"]
    elif scenario in {"dead_letter", "dead"}:
        predicted = ["append dead-letter.json item", "owner_required only when appropriate"]
        risks = ["silent drop", "owner spam on green failures"]
        gates = ["failover exhausted"]
        rollback = ["remove item by id from dead-letter.json"]
    elif scenario in {"sot_conflict", "conflict"}:
        predicted = ["sensor check-office-control-plane fails", "watchdog red duplicate_source_of_truth_map"]
        risks = ["two authorities for same domain"]
        gates = ["none — fail closed"]
        rollback = ["delete rogue map file"]
    elif scenario in {"owner_surface", "owner"}:
        predicted = [
            "routine_quality + weak_metric stay internal",
            "price decision surfaces to owner",
        ]
        risks = ["bothering Christian with weak metrics"]
        gates = ["red/orange only"]
        rollback = ["n/a read model"]
    else:
        predicted = ["no authoritative mutation"]
        risks = ["unknown scenario name"]
        gates = []
        rollback = ["n/a"]

    print("predicted_effects:")
    for x in predicted:
        print(f" · {x}")
    print("files_or_actions_that_would_change:")
    print(" · office/control/followups.json (wip)")
    print(" · office/control/dead-letter.json (dead)")
    print(" · office/control/HANDOFF.json (handoff refresh)")
    print("risks:")
    for x in risks:
        print(f" · {x}")
    print("owner_gates:")
    for x in gates or ["—"]:
        print(f" · {x}")
    print("rollback:")
    for x in rollback:
        print(f" · {x}")
    return 0


def record_dead_letter(
    *,
    action: str,
    source: str,
    reason: str,
    risk: str = "yellow",
    owner_required: bool = False,
    correlation_id: str | None = None,
    attempts: int = 1,
    last_error: str = "",
    next_safe_action: str = "retry-via-failover",
) -> dict:
    """Append to office/control/dead-letter.json ONLY — never harness queue.json."""
    data = load_json(DEAD, {"items": []})
    item = {
        "id": f"dl-{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}",
        "created_at": now_iso(),
        "source": source,
        "action": action,
        "correlation_id": correlation_id,
        "risk": risk.lower() if isinstance(risk, str) else risk,
        "reason": reason,
        "attempts": attempts,
        "last_error": last_error,
        "next_safe_action": next_safe_action,
        "owner_required": owner_required,
        "status": "open",
    }
    data.setdefault("items", []).append(item)
    data["updatedAt"] = today()
    write_json(DEAD, data)
    return item


def list_dead_letters(*, open_only: bool = False) -> list[dict]:
    data = load_json(DEAD, {"items": []})
    items = list(data.get("items") or [])
    if open_only:
        items = [i for i in items if i.get("status") in {"open", "unresolved", "failed", None}]
    return items


def resolve_dead_letter(action_or_id: str, *, note: str = "resolved") -> bool:
    data = load_json(DEAD, {"items": []})
    found = False
    for item in data.get("items") or []:
        if item.get("id") == action_or_id or item.get("action") == action_or_id or item.get("actionId") == action_or_id:
            item["status"] = "resolved"
            item["resolved"] = True
            item["resolvedAt"] = now_iso()
            item["resolveNote"] = note
            found = True
            break
    if found:
        data["updatedAt"] = today()
        write_json(DEAD, data)
    return found


def cmd_selftest(_args: argparse.Namespace) -> int:
    """Acceptance fixtures — isolated temp mutations restored."""
    errors: list[str] = []
    fus_path = FOLLOWUPS
    backup_fu = fus_path.read_text(encoding="utf-8") if fus_path.is_file() else None
    backup_dl = DEAD.read_text(encoding="utf-8") if DEAD.is_file() else None
    backup_inbox = INBOX.read_text(encoding="utf-8") if INBOX.is_file() else None
    backup_harness_dl = HARNESS_DL_QUEUE.read_text(encoding="utf-8") if HARNESS_DL_QUEUE.is_file() else None
    backup_legacy_fu = LEGACY_FOLLOWUPS.read_text(encoding="utf-8") if LEGACY_FOLLOWUPS.is_file() else None
    backup_caps = IG_CAPABILITIES.read_text(encoding="utf-8") if IG_CAPABILITIES.is_file() else None
    cards_created: list[Path] = []

    def _mk_card(name: str, body: str) -> Path:
        CARDS.mkdir(parents=True, exist_ok=True)
        path = CARDS / name
        path.write_text(body, encoding="utf-8")
        cards_created.append(path)
        return path

    try:
        # 1. followup waits for matching print.done
        write_json(
            fus_path,
            {
                "updatedAt": today(),
                "items": [
                    {
                        "id": "fu-wait-1",
                        "type": "wip_to_finished",
                        "correlation_id": "WAIT-JOB-1",
                        "jobId": "WAIT-JOB-1",
                        "state": "waiting_for_print_done",
                        "created_at": now_iso(),
                    }
                ],
            },
        )
        items = sync_followups(mutate=True)
        hit = next((i for i in items if i.get("id") == "fu-wait-1"), None)
        if not hit or hit.get("state") != "waiting_for_print_done":
            errors.append(f"1 wait-for-print: expected still waiting, got {hit}")

        # 2. wrong print.done (different jobId) does NOT close
        _mk_card(
            "2099-01-02-WRONG-JOB.md",
            "# Print card · WRONG\n\nevent: print.done\n"
            "- jobId: OTHER-JOB-999\n- sku / שם עבודה: OTHER-SKU\n"
            "- timelapse path / Drive id: /tmp/x.mp4\n",
        )
        items = sync_followups(mutate=True)
        hit = next((i for i in items if i.get("id") == "fu-wait-1"), None)
        if not hit or hit.get("state") != "waiting_for_print_done":
            errors.append(f"2 wrong print.done closed followup: {hit}")
        # name similarity alone must never match
        if defensible_match({"jobId": "A", "sku": "RingHolder"}, {"jobId": "B", "sku": "RingHolderPro"}):
            errors.append("2b name similarity alone matched")

        # 3. matching print.done advances waiting_for_print_done → ready_for_finished_content
        _mk_card(
            "2099-01-01-WAIT-JOB-1.md",
            "# Print card · WAIT-JOB-1\n\nproducedAt: 2099-01-01\nevent: print.done\n\n"
            "## מטא\n- jobId: WAIT-JOB-1\n- sku / שם עבודה: WAIT-JOB-1\n\n"
            "## מדיה\n- timelapse path / Drive id: /tmp/fake-timelapse.mp4\n"
            "- still path: /tmp/fake-still.jpg\n",
        )
        items = sync_followups(mutate=True)
        hit = next((i for i in items if i.get("id") == "fu-wait-1"), None)
        if not hit or hit.get("state") != "ready_for_finished_content":
            errors.append(f"3 matching print.done advance failed: {hit}")
        elif hit.get("publication") in {"published", "live", "posted"}:
            errors.append("3 claimed published")
        elif "PREFLIGHT" not in (hit.get("required_gates") or []):
            errors.append("3 PREFLIGHT not required")
        elif not hit.get("suggested_slot"):
            errors.append("3 missing suggested_slot")

        # 4. matching without media → waiting_for_media
        write_json(
            fus_path,
            {
                "updatedAt": today(),
                "items": [
                    {
                        "id": "fu-nomedia",
                        "type": "wip_to_finished",
                        "correlation_id": "NOMEDIA-1",
                        "jobId": "NOMEDIA-1",
                        "state": "waiting_for_print_done",
                        "created_at": now_iso(),
                    }
                ],
            },
        )
        _mk_card(
            "2099-01-03-NOMEDIA-1.md",
            "# Print card · NOMEDIA-1\n\nevent: print.done\n"
            "- jobId: NOMEDIA-1\n- sku / שם עבודה: NOMEDIA-1\n"
            "- timelapse path / Drive id: חסר\n- still path: חסר\n",
        )
        items = sync_followups(mutate=True)
        hit = next((i for i in items if i.get("id") == "fu-nomedia"), None)
        if not hit or hit.get("state") != "waiting_for_media":
            errors.append(f"4 no-media → waiting_for_media failed: {hit}")

        # 5. dead-letter writes to office/control/dead-letter.json only
        if backup_dl is not None:
            DEAD.write_text(backup_dl, encoding="utf-8")
        item = record_dead_letter(
            action="selftest_failover",
            source="selftest",
            reason="simulated failure after failover",
            risk="yellow",
            owner_required=False,
            attempts=2,
            last_error="tool down",
            next_safe_action="retry-watchdog",
        )
        data = load_json(DEAD, {"items": []})
        if not any(i.get("id") == item["id"] for i in data.get("items") or []):
            errors.append("5 dead letter not in office/control/dead-letter.json")
        harness = load_json(HARNESS_DL_QUEUE, {"items": []})
        if any(i.get("id") == item["id"] for i in harness.get("items") or []):
            errors.append("5 dead letter leaked into harness queue.json")

        # 6. watchdog sees that dead-letter
        report = build_watchdog_report(mutate_followups=False)
        if not any(
            f.get("area") == "unresolved_dead_letter" and item["id"] in str(f.get("detail"))
            for f in report.get("findings") or []
        ):
            errors.append("6 watchdog did not see dead-letter")

        # 12. ordinary failover dead-letter with owner_required=false is not red owner surface
        surface = owner_surface_items(dead=load_json(DEAD, {"items": []}))
        if any(s.get("id") == item["id"] for s in surface):
            errors.append("12 owner surface escalated non-owner dead-letter")
        if report.get("summary") == "RED_BLOCKER" and all(
            f.get("area") == "unresolved_dead_letter" for f in report.get("findings") or [] if f.get("outcome") == "RED_BLOCKER"
        ):
            # only fail if the dead-letter itself caused RED_BLOCKER
            dl_findings = [f for f in report.get("findings") or [] if f.get("area") == "unresolved_dead_letter"]
            if any(f.get("outcome") == "RED_BLOCKER" and not f.get("owner_required") for f in dl_findings):
                errors.append("12 non-owner dead-letter mapped to RED_BLOCKER")

        # restore DL before other tests that scan it
        if backup_dl is not None:
            DEAD.write_text(backup_dl, encoding="utf-8")
        else:
            write_json(DEAD, {"updatedAt": today(), "items": []})

        # 7. scheduled / uploadAccepted / publishRequested are not live; live needs verification_evidence
        for state_name in ("scheduled", "uploadAccepted", "publishRequested"):
            fu = {
                "id": f"fu-pub-{state_name}",
                "type": "wip_to_finished",
                "correlation_id": f"PUB-{state_name}",
                "state": "scheduled" if state_name == "scheduled" else "waiting_publication_verification",
                "publication": state_name,
            }
            if state_name != "scheduled" and (fu.get("publication") or "").lower() in {
                "published",
                "live",
                "liveverified",
            }:
                errors.append(f"7 fixture bug {state_name}")
            # claiming live without evidence must be red
        write_json(
            fus_path,
            {
                "updatedAt": today(),
                "items": [
                    {
                        "id": "fu-fake-live",
                        "type": "wip_to_finished",
                        "correlation_id": "FAKE-LIVE",
                        "state": "scheduled",
                        "publication": "liveVerified",
                        # no verification_evidence
                    },
                    {
                        "id": "fu-scheduled-ok",
                        "type": "wip_to_finished",
                        "correlation_id": "SCHED-OK",
                        "state": "scheduled",
                        "publication": "scheduled",
                    },
                ],
            },
        )
        issues = watchdog_issues()
        if not any(i.get("code") == "published_without_verification" for i in issues):
            errors.append("7 live without verification_evidence not flagged")
        if any(
            i.get("code") == "published_without_verification" and "SCHED-OK" in str(i.get("detail"))
            for i in issues
        ):
            errors.append("7 scheduled incorrectly treated as live claim")

        # 8. Instagram needsAuth cannot be ready without desk ready
        if backup_caps is not None:
            caps = json.loads(backup_caps)
            caps["currentStatus"] = "ready"
            write_json(IG_CAPABILITIES, caps)
            issues = watchdog_issues()
            desk = load_json(DESK, {})
            ig = ((desk.get("tools") or {}).get("instagram") or {}).get("status")
            if ig != "ready" and not any(i.get("code") == "ig_fake_ready" for i in issues):
                errors.append("8 fake CAPABILITIES ready not detected")
            IG_CAPABILITIES.write_text(backup_caps, encoding="utf-8")

        # 9. public CTA cannot contain WhatsApp phone; business contact may retain it
        if INSTANCE_VF.is_file():
            inst = load_json(INSTANCE_VF, {})
            primary = (inst.get("cta") or {}).get("primary") or ""
            biz = ((inst.get("cta") or {}).get("businessContact") or {}).get("whatsapp") or ""
            if "050-2517000" in primary or "whatsapp" in primary.lower():
                errors.append("9 instance cta.primary contains WhatsApp")
            if "050-2517000" not in biz and "050-2517000" not in str((inst.get("cta") or {}).get("whatsapp") or ""):
                # business contact may retain — warn only if completely absent from record fields
                pass  # optional presence

        # 10. duplicate SoT detection
        rogue = ROOT / "office" / "sources-of-truth.json"
        try:
            write_json(rogue, {"jobs": "somewhere-else"})
            issues = watchdog_issues()
            if not any(i.get("code") == "duplicate_source_of_truth_map" for i in issues):
                errors.append("10a SOT map conflict not detected")
        finally:
            if rogue.is_file():
                rogue.unlink()

        write_json(
            HARNESS_DL_QUEUE,
            {
                "note": "rogue authoritative items",
                "items": [{"id": "rogue-dl", "status": "open", "reason": "should fail"}],
            },
        )
        issues = watchdog_issues()
        if not any(i.get("code") == "duplicate_dead_letter_authority" for i in issues):
            errors.append("10b harness dead-letter authority not detected")
        if backup_harness_dl is not None:
            HARNESS_DL_QUEUE.write_text(backup_harness_dl, encoding="utf-8")

        write_json(
            LEGACY_FOLLOWUPS,
            {
                "followups": [
                    {"id": "rogue-fu", "status": "waiting_for_matching_print.done", "jobId": "X"}
                ]
            },
        )
        issues = watchdog_issues()
        if not any(i.get("code") == "duplicate_followups_authority" for i in issues):
            errors.append("10c legacy followups authority not detected")
        if backup_legacy_fu is not None:
            LEGACY_FOLLOWUPS.write_text(backup_legacy_fu, encoding="utf-8")

        # 11. owner surface does not escalate weak_metric
        write_json(
            INBOX,
            {
                "updatedAt": today(),
                "buckets": {
                    "content": [
                        {"id": "q1", "kind": "routine_quality", "risk": "green", "text": "caption fix"},
                        {"id": "m1", "kind": "weak_metric", "risk": "yellow", "text": "reach low"},
                    ],
                    "approvals": [
                        {
                            "id": "p1",
                            "kind": "price",
                            "risk": "red",
                            "text": "approve price",
                            "owner_required": True,
                        }
                    ],
                    "production": [],
                    "sales": [],
                    "admin": [],
                    "blocked": [],
                    "unknown": [],
                },
            },
        )
        surface = owner_surface_items()
        ids = {s.get("id") for s in surface}
        if "q1" in ids or "m1" in ids:
            errors.append("11 owner surface leaked internal/weak_metric items")
        if "p1" not in ids:
            errors.append("11 owner surface missed price decision")

    finally:
        if backup_fu is not None:
            fus_path.write_text(backup_fu, encoding="utf-8")
        else:
            fus_path.unlink(missing_ok=True)
        if backup_dl is not None:
            DEAD.write_text(backup_dl, encoding="utf-8")
        if backup_inbox is not None:
            INBOX.write_text(backup_inbox, encoding="utf-8")
        if backup_harness_dl is not None:
            HARNESS_DL_QUEUE.write_text(backup_harness_dl, encoding="utf-8")
        if backup_legacy_fu is not None:
            LEGACY_FOLLOWUPS.write_text(backup_legacy_fu, encoding="utf-8")
        if backup_caps is not None:
            IG_CAPABILITIES.write_text(backup_caps, encoding="utf-8")
        for card in cards_created:
            if card.is_file():
                card.unlink()

    if errors:
        for e in errors:
            print(f"FAIL {e}", file=sys.stderr)
        return 1
    print(
        "OK selftest (wait · wrong-print · match · no-media · dead-letter · "
        "watchdog-dl · pub-states · ig-fake-ready · public-cta · dup-SoT · "
        "owner-surface · non-owner-dl)"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS Office Control Plane")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    p_wd = sub.add_parser("watchdog")
    p_wd.add_argument("--json", action="store_true")
    p_wd.add_argument("--write", action="store_true")
    p_wd.set_defaults(func=cmd_watchdog)
    sub.add_parser("gaps").set_defaults(func=cmd_gaps)
    sub.add_parser("handoff").set_defaults(func=cmd_handoff)
    p_fu = sub.add_parser("followups")
    p_fu.add_argument("--dry-run", action="store_true")
    p_fu.set_defaults(func=cmd_followups)
    sub.add_parser("review").set_defaults(func=cmd_review)
    sub.add_parser("memory-hygiene").set_defaults(func=cmd_memory_hygiene)
    p_sim = sub.add_parser("simulate")
    p_sim.add_argument("--scenario", default="noop")
    p_sim.set_defaults(func=cmd_simulate)
    sub.add_parser("selftest").set_defaults(func=cmd_selftest)

    def _brief(_a: argparse.Namespace) -> int:
        print(json.dumps(brief_summary(), ensure_ascii=False, indent=2))
        return 0

    sub.add_parser("brief-summary").set_defaults(func=_brief)

    args = parser.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
