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


def required_paths() -> dict[str, Path]:
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


def parse_print_cards() -> list[dict]:
    rows: list[dict] = []
    if PRINT_EVENTS.is_file():
        for ev in load_jsonl(PRINT_EVENTS):
            if (ev.get("name") or ev.get("event") or "") != "print.done" and "print.done" not in str(
                ev.get("event") or ""
            ):
                # still accept envelopes that look like print.done
                if (ev.get("name") or "") != "print.done":
                    if not ev.get("correlationId") and not (ev.get("payload") or {}).get("sku"):
                        continue
            payload = dict(ev.get("payload") or {})
            corr = (ev.get("correlationId") or payload.get("sku") or payload.get("jobId") or "").strip()
            media = (
                payload.get("mediaPath")
                or (payload.get("media") or {}).get("timelapse_path")
                or ""
            ).strip()
            rows.append(
                {
                    "correlation_id": corr,
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
            if "print.done" not in text and "event: print.done" not in text:
                # cards folder implies print.done cards
                pass
            corr = ""
            for line in text.splitlines():
                low = line.lower()
                if "sku" in low or "correlation" in low or "שם עבודה" in line:
                    part = line.split(":", 1)
                    if len(part) == 2 and part[1].strip():
                        corr = part[1].strip()
                        break
            if not corr:
                # stem often YYYY-MM-DD-<sku-or-job>
                stem = path.stem
                bits = stem.split("-", 3)
                corr = bits[3] if len(bits) >= 4 else stem
            has_media = ("timelapse" in text.lower() or "still path" in text.lower()) and "חסר" not in text
            # weaker: explicit media path with non-empty value
            for line in text.splitlines():
                if "timelapse" in line.lower() or "still path" in line.lower() or "drive id" in line.lower():
                    val = line.split(":", 1)[-1].strip() if ":" in line else ""
                    if val and val not in {"חסר", "-", "—", "missing"}:
                        has_media = True
            rows.append(
                {
                    "correlation_id": corr,
                    "media": "card" if has_media else "",
                    "source": str(path.relative_to(ROOT)),
                    "has_media": has_media,
                    "path": str(path.relative_to(ROOT)),
                }
            )
    return [r for r in rows if r.get("correlation_id")]


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
    """WIP→finished bridge. Never invent correlation_id."""
    data = load_json(FOLLOWUPS, {"items": []})
    items = list(data.get("items") or [])
    by_corr = {i.get("correlation_id"): i for i in items if i.get("correlation_id")}
    prints = parse_print_cards()
    changed = False

    # Advance waiting followups when matching print.done appears
    for item in items:
        if item.get("type") != "wip_to_finished":
            continue
        corr = item.get("correlation_id") or ""
        if not corr:
            continue
        match = next((p for p in prints if p["correlation_id"] == corr), None)
        if item.get("state") == "waiting_for_print_done" and match:
            item["state"] = "ready_for_finished_content"
            item["print_source"] = match.get("source")
            item["updated_at"] = now_iso()
            if not match.get("has_media"):
                item["state"] = "waiting_for_media"
                item["next_action"] = "internal_capture_task"
            else:
                item["next_action"] = "prepare_finished_content"
                item["required_gates"] = ["EDIT-GATE", "PREFLIGHT"]
                item["suggested_slot"] = next_calendar_slot()
                item["publication"] = "not_published"  # scheduling ≠ live
            changed = True
        elif item.get("state") == "ready_for_finished_content" and match and not match.get("has_media"):
            item["state"] = "waiting_for_media"
            item["next_action"] = "internal_capture_task"
            item["updated_at"] = now_iso()
            changed = True

    # Ensure print.done with media without followup gets ready followup (deterministic)
    for p in prints:
        corr = p["correlation_id"]
        if not corr or corr in by_corr:
            continue
        if p.get("has_media"):
            neu = {
                "id": f"fu-{corr}",
                "type": "wip_to_finished",
                "correlation_id": corr,
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
            by_corr[corr] = neu
            changed = True

    if mutate and changed:
        data["items"] = items
        data["updatedAt"] = today()
        write_json(FOLLOWUPS, data)
    return items


def watchdog_issues() -> list[dict]:
    issues: list[dict] = []
    p = plane()
    sot = p.get("sourcesOfTruth") or {}

    for key, path in required_paths().items():
        if not path.exists():
            issues.append({"level": "red", "code": "missing_file", "detail": str(path.relative_to(ROOT)), "key": key})

    # JSON parse
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
                issues.append({"level": "red", "code": "json_parse", "detail": f"{label}: {exc}"})

    # Duplicate source-of-truth claims (explicit parallel maps)
    claimed: dict[str, list[str]] = {}
    for domain, loc in sot.items():
        claimed.setdefault(str(loc), []).append(domain)
    # Also fail if a second media catalog appears
    for extra in ROOT.glob("**/media-catalog.json"):
        if extra.resolve() != MEDIA_CATALOG.resolve():
            issues.append(
                {
                    "level": "red",
                    "code": "duplicate_media_catalog",
                    "detail": str(extra.relative_to(ROOT)),
                }
            )
    # Parallel control maps
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
                }
            )

    # Dead letters forgotten
    dead = load_json(DEAD, {"items": []})
    for item in dead.get("items") or []:
        if item.get("status") in {"open", "unresolved", None, "failed"}:
            age = item.get("created_at") or ""
            issues.append(
                {
                    "level": "yellow" if not item.get("owner_required") else "orange",
                    "code": "unresolved_dead_letter",
                    "detail": item.get("id") or item.get("action") or age,
                    "owner_required": bool(item.get("owner_required")),
                }
            )

    # WIP stuck after matching print.done
    items = sync_followups(mutate=True)
    prints = {p["correlation_id"] for p in parse_print_cards()}
    for item in items:
        if (
            item.get("type") == "wip_to_finished"
            and item.get("state") == "waiting_for_print_done"
            and item.get("correlation_id") in prints
        ):
            issues.append(
                {
                    "level": "red",
                    "code": "wip_stuck_after_print_done",
                    "detail": item.get("correlation_id"),
                }
            )

    # Approved content without next action
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    for item in queue.get("items") or []:
        gate = item.get("gate") or ""
        if gate in {"approved_for_manual_posting", "pending_human_approval"} and not item.get("slot") and not item.get(
            "next_action"
        ):
            # pending with calendar_rule is ok
            if not item.get("calendar_rule") and not item.get("slot"):
                issues.append(
                    {
                        "level": "yellow",
                        "code": "approved_without_next_action",
                        "detail": item.get("content_id"),
                    }
                )

    # Published claim without verification
    for item in items:
        pub = (item.get("publication") or "").lower()
        if pub in {"published", "live", "posted"} and not item.get("verification_evidence"):
            issues.append(
                {
                    "level": "red",
                    "code": "published_without_verification",
                    "detail": item.get("correlation_id") or item.get("id"),
                }
            )
        if item.get("state") == "scheduled" and pub in {"published", "live", "posted"}:
            issues.append(
                {
                    "level": "red",
                    "code": "schedule_marked_as_live",
                    "detail": item.get("id"),
                }
            )

    # Policy text scans (repo laws — not inventing)
    for path in (CONSTITUTION, ORCHESTRA, CALENDAR):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "Meta Business Suite" in text and "לא Meta Suite" not in text and "no Suite" not in text.lower():
            # allow forbid mentions
            if "לא" not in text[max(0, text.find("Meta Business Suite") - 40) : text.find("Meta Business Suite") + 40]:
                issues.append({"level": "orange", "code": "suite_language", "detail": str(path.relative_to(ROOT))})

    # One media catalog lock
    cat = load_json(MEDIA_CATALOG, {})
    if cat.get("oneCatalog") is not True:
        issues.append({"level": "red", "code": "media_catalog_not_one", "detail": "oneCatalog must be true"})

    # Auto-DM / shipping language in control plane itself
    cp_text = CONTROL_PLANE.read_text(encoding="utf-8") if CONTROL_PLANE.is_file() else ""
    if "auto-dm" in cp_text.lower() and "no-auto-dm" not in cp_text.lower():
        issues.append({"level": "red", "code": "auto_dm_allowed", "detail": "control-plane"})

    return issues


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
    surface = owner_surface_items(inbox=inbox, dead={"items": dead})
    degraded = [i for i in issues if i.get("level") in {"red", "orange"}]
    safe = [
        "python3 scripts/vf_control_plane.py watchdog",
        "python3 scripts/vf_control_plane.py followups",
        "python3 scripts/vfops_loop.py brief",
        "python3 scripts/check-all.py",
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
        "next": [
            "הרץ watchdog",
            "סגור followups ready_for_finished_content דרך EDIT-GATE+PREFLIGHT",
            "אל תטריד את כריסטיאן על מדדים חלשים",
        ],
        "changed_today": [
            "Office Control Plane מוטמע",
            f"followups={len(followups)}",
            f"dead_letters={len(dead)}",
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


def cmd_watchdog(_args: argparse.Namespace) -> int:
    sync_followups(mutate=True)
    if not HANDOFF_JSON.is_file():
        build_handoff()
    issues = watchdog_issues()
    reds = [i for i in issues if i.get("level") == "red"]
    print("=== watchdog ===")
    print(f"issues={len(issues)} red={len(reds)}")
    for i in issues:
        print(f"{i.get('level')}\t{i.get('code')}\t{i.get('detail')}")
    if reds:
        return 1
    print("OK watchdog")
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
    data = load_json(DEAD, {"items": []})
    item = {
        "id": f"dl-{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}",
        "created_at": now_iso(),
        "source": source,
        "action": action,
        "correlation_id": correlation_id,
        "risk": risk,
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


def cmd_selftest(_args: argparse.Namespace) -> int:
    """Acceptance fixtures from the handoff — isolated temp mutations restored."""
    errors: list[str] = []

    # C. WIP→Finished
    fus_path = FOLLOWUPS
    backup_fu = fus_path.read_text(encoding="utf-8") if fus_path.is_file() else None
    try:
        write_json(
            fus_path,
            {
                "updatedAt": today(),
                "items": [
                    {
                        "id": "fu-test-sku",
                        "type": "wip_to_finished",
                        "correlation_id": "TEST-SKU-001",
                        "state": "waiting_for_print_done",
                        "created_at": now_iso(),
                    }
                ],
            },
        )
        # create matching print card fixture
        cards = CARDS
        cards.mkdir(parents=True, exist_ok=True)
        card = cards / "2099-01-01-TEST-SKU-001.md"
        card.write_text(
            "# Print card · TEST-SKU-001\n\n"
            "producedAt: 2099-01-01\nevent: print.done\n\n"
            "## מטא\n- sku / שם עבודה: TEST-SKU-001\n\n"
            "## מדיה\n- timelapse path / Drive id: /tmp/fake-timelapse.mp4\n"
            "- still path: /tmp/fake-still.jpg\n- proof על המיטה: כן\n",
            encoding="utf-8",
        )
        items = sync_followups(mutate=True)
        hit = next((i for i in items if i.get("correlation_id") == "TEST-SKU-001"), None)
        if not hit or hit.get("state") != "ready_for_finished_content":
            errors.append(f"WIP bridge failed: {hit}")
        elif hit.get("publication") in {"published", "live", "posted"}:
            errors.append("WIP bridge claimed published")
        elif not hit.get("suggested_slot") or "CALENDAR" not in (hit.get("suggested_slot") or "") and "חסר" in (
            hit.get("suggested_slot") or ""
        ):
            # slot must come from calendar — allow Hebrew slot strings from CALENDAR.md
            if "CALENDAR" not in (hit.get("suggested_slot") or "") and "16:00" not in (
                hit.get("suggested_slot") or ""
            ) and "20:30" not in (hit.get("suggested_slot") or "") and "12:00" not in (
                hit.get("suggested_slot") or ""
            ):
                errors.append(f"slot not from calendar: {hit.get('suggested_slot')}")
        if "PREFLIGHT" not in (hit or {}).get("required_gates", []):
            errors.append("PREFLIGHT not required")
    finally:
        if backup_fu is not None:
            fus_path.write_text(backup_fu, encoding="utf-8")
        else:
            fus_path.unlink(missing_ok=True)
        card = CARDS / "2099-01-01-TEST-SKU-001.md"
        if card.is_file():
            card.unlink()

    # D. Dead letter
    backup_dl = DEAD.read_text(encoding="utf-8") if DEAD.is_file() else None
    try:
        item = record_dead_letter(
            action="test_failover_exhausted",
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
            errors.append("dead letter not recorded")
    finally:
        if backup_dl is not None:
            DEAD.write_text(backup_dl, encoding="utf-8")

    # E. Source-of-truth conflict
    rogue = ROOT / "office" / "sources-of-truth.json"
    try:
        write_json(rogue, {"jobs": "somewhere-else"})
        issues = watchdog_issues()
        if not any(i.get("code") == "duplicate_source_of_truth_map" for i in issues):
            errors.append("SOT conflict not detected")
    finally:
        if rogue.is_file():
            rogue.unlink()

    # F. Owner surface
    backup_inbox = INBOX.read_text(encoding="utf-8") if INBOX.is_file() else None
    try:
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
                        {"id": "p1", "kind": "price", "risk": "red", "text": "approve price", "owner_required": True}
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
            errors.append("owner surface leaked internal items")
        if "p1" not in ids:
            errors.append("owner surface missed price decision")
    finally:
        if backup_inbox is not None:
            INBOX.write_text(backup_inbox, encoding="utf-8")

    if errors:
        for e in errors:
            print(f"FAIL {e}", file=sys.stderr)
        return 1
    print("OK selftest (WIP bridge · dead-letter · SOT conflict · owner surface)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS Office Control Plane")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("watchdog").set_defaults(func=cmd_watchdog)
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
