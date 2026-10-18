#!/usr/bin/env python3
"""Reel candidates from the one media catalog — suggestions only, never a reel.

Reads packages/vfmedia/catalog.json (the vault's single catalog) and proposes the
best 2-3 unpublished source videos. Each candidate carries a proposed edit recipe
that names an existing active office editing tool (VIDEO-TOOLCHAIN editIntelligence
bridge + HyperFrames canonical overlay).

Locks: no direct publish, no edit, no render, no network, no schedule. A candidate
is not a reel and does not show a specific product unless the catalog links one
(`productLink`). Routine creative selection may be office-owned, but nothing is
publish-ready until exact-final PREFLIGHT + EDIT-GATE pass and
`policy_id: instagram.publish` authorizes the external effect.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VELVETOS_PACK = ROOT / "packages" / "velvetos"
if str(VELVETOS_PACK) not in sys.path:
    sys.path.insert(0, str(VELVETOS_PACK))
from tool_status_resolver import compose_tool_status  # noqa: E402

MEDIA_CATALOG = ROOT / "packages" / "vfmedia" / "catalog.json"
VIDEO_TOOLCHAIN = ROOT / "packages" / "vfom" / "VIDEO-TOOLCHAIN.json"
HYPERFRAMES_BACKEND = ROOT / "packages" / "vfom" / "HYPERFRAMES-BACKEND.json"

REEL_CTA = "לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם"
MAX_CANDIDATES = 3
TRIM_SECONDS = (7, 15)
VIDEO_EXTS = ("mp4", "mov", "m4v")
CANDIDATE_STATUSES = {"source"}
BLOCKED_TOOL_STATUSES = {"frozen", "retired", "dormant", "forbidden", "removed"}
ACTIVE_EDIT_STATUSES = {"implemented", "active", "canonical"}
UNUSABLE_MARKERS = ("פגום", "לא שמיש", "נפסל", "לא לשימוש", "corrupt", "unusable", "rejected")
REJECTED_REVIEW_STATES = {"rejected", "failed", "unusable"}
_FILE_RE = re.compile(r"שם קובץ:\s*(.+?\.(?:%s))(?=$|[\s·,;)])" % "|".join(VIDEO_EXTS), re.I)
_ANY_VIDEO_RE = re.compile(r"([^\s·/\\]+\.(?:%s))(?=$|[\s·,;)])" % "|".join(VIDEO_EXTS), re.I)
_TIMELAPSE_RE = re.compile(r"_(?:PLA|PETG|TPU|ABS|ASA|PA|NYLON)[^_]*_(?:\d+d)?\d+h\d+m_|_plate_\d+_", re.I)


def _load(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def video_file_name(item: dict) -> str:
    """File name when the catalog row is a video; '' otherwise. Never guesses."""
    src = item.get("sourceFile") or {}
    for key in ("mimeType",):
        for holder in (item, src):
            mime = str(holder.get(key) or "")
            if mime.startswith("video/"):
                return str(holder.get("name") or item.get("fileName") or src.get("name") or item.get("id") or "")
    for name in (item.get("fileName"), src.get("name")):
        if name and str(name).lower().rsplit(".", 1)[-1] in VIDEO_EXTS:
            return str(name)
    desc = str(item.get("viewDescription") or "")
    m = _FILE_RE.search(desc) or _ANY_VIDEO_RE.search(desc)
    return m.group(1).strip() if m else ""


def clip_kind(name: str, desc: str) -> str:
    if _TIMELAPSE_RE.search(name):
        return "printer_timelapse"
    if "מהטלפון" in desc or name.upper().startswith("IMG_"):
        return "phone_clip"
    return "video"


def family(name: str) -> str:
    """Print-job family for timelapses (e.g. king_v3) so takes are not repeated."""
    m = _TIMELAPSE_RE.search(name)
    return name[: m.start()].strip().lower() if m else name.strip().lower()


def duration_seconds(item: dict):
    for key in ("durationSeconds", "duration"):
        val = item.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return float(val)
    return None


def unusable_reason(item: dict) -> str:
    status = str(item.get("status") or "")
    if status not in CANDIDATE_STATUSES:
        return f"status={status or 'missing'}"
    if item.get("derivativeIds"):
        return "already has derivatives"
    intake = item.get("intake") or {}
    if intake and intake.get("phase") not in (None, "verified"):
        return f"intake.phase={intake.get('phase')}"
    if intake.get("lastError"):
        return "intake.lastError"
    review = (item.get("visualReview") or {}).get("state")
    if review in REJECTED_REVIEW_STATES:
        return f"visualReview={review}"
    desc = str(item.get("viewDescription") or "").lower()
    if any(marker.lower() in desc for marker in UNUSABLE_MARKERS):
        return "marked unusable in viewDescription"
    dur = duration_seconds(item)
    if dur is not None and dur < TRIM_SECONDS[0]:
        return f"shorter than {TRIM_SECONDS[0]}s"
    return ""


def active_edit_tools(toolchain_path: Path = VIDEO_TOOLCHAIN, backend_path: Path = HYPERFRAMES_BACKEND,
                      tool_status_path: Path | None = None, root: Path = ROOT) -> dict:
    """Existing active editing bridges, gated by selected-instance tool status.

    ``tool_status_path`` is fixture-only compatibility for isolated tests. Normal
    production selection resolves the explicit Velvet Factory ``toolStatus``
    instance surface through the generic resolver.
    """
    toolchain = _load(toolchain_path, {})
    backend = _load(backend_path, {})
    status_doc = (
        _load(tool_status_path, {})
        if tool_status_path is not None
        else compose_tool_status(root, instance_id="velvet-factory", env={})
    )
    blocked_blob = json.dumps(
        [v for v in (status_doc.get("tools") or {}).values()
         if isinstance(v, dict) and str(v.get("status") or "").lower() in BLOCKED_TOOL_STATUSES],
        ensure_ascii=False,
    )
    tools: dict = {}
    edit = toolchain.get("editIntelligence") or {}
    if edit.get("status") in ACTIVE_EDIT_STATUSES and edit.get("bridge"):
        tools["base_cut"] = {"tool": edit["bridge"], "status": edit["status"]}
    hf_slot = (toolchain.get("animationSlots") or {}).get("hyperframes") or {}
    hf_bridge = (backend.get("execution") or {}).get("bridge")
    if hf_slot.get("status") in ACTIVE_EDIT_STATUSES and hf_bridge:
        tools["overlay"] = {"tool": hf_bridge, "status": hf_slot["status"]}
    return {
        k: v for k, v in tools.items()
        if (root / v["tool"]).is_file() and v["tool"] not in blocked_blob
    }


def edit_recipe(name: str, kind: str, tools: dict) -> dict:
    beat = "הוכחת הדפסה" if kind == "printer_timelapse" else "קלוז־אפ/שימוש"
    steps = []
    if "base_cut" in tools:
        steps.append({
            "tool": tools["base_cut"]["tool"],
            "commands": ["doctor", "plan", "run", "inspect"],
            "params": {
                "segments": [{"source": name, "start": "נבחר אחרי צפייה", "end": "start+7..15s",
                              "beat": "hook", "reason": beat}],
                "trimSeconds": list(TRIM_SECONDS),
                "resolution": "portrait",  # 1080x1920 · 9:16
                "fps": 30,
                "cutPolicy": "visual-only",
                "audioRequired": False,
            },
        })
    if "overlay" in tools:
        steps.append({
            "tool": tools["overlay"]["tool"],
            "commands": ["doctor", "plan", "run"],
            "params": {
                "backend": "hyperframes",
                "target": "reel_master",
                "resolution": "portrait",
                "fps": 30,
                "stage": "rough→review→final",
                "hookText": "NO_TEXT או עד 5 מילים (OWNER-APPROVED-GRID-STANDARD)",
                "ctaEndCard": REEL_CTA,
            },
        })
    return {
        "tool": steps[0]["tool"] if steps else "",
        "host": "office host · sderot-mac → sderot-windows (RENDER-HOSTS) · ידני, לא בתזמון",
        "steps": steps,
        "gates": ["exact-final visual review", "packages/vfgrowth/PREFLIGHT.md", "packages/vfgrowth/EDIT-GATE.md", "policy_id: instagram.publish"],
        "cta": REEL_CTA,
        "note": "הצעה בלבד — לא authorization ולא פרסום; routine selection can stay office-owned",
    }


def select_candidates(catalog_path: Path = MEDIA_CATALOG, limit: int = MAX_CANDIDATES,
                      tools: dict | None = None) -> dict:
    catalog = _load(catalog_path, {"items": []})
    items = catalog.get("items") if isinstance(catalog, dict) else catalog
    items = items or []
    tools = active_edit_tools() if tools is None else tools
    videos, published_families, skipped = [], set(), {}
    for item in items:
        name = video_file_name(item)
        if not name:
            continue
        if str(item.get("status") or "") in {"published", "approved"}:
            published_families.add(family(name))
        reason = unusable_reason(item)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        videos.append((item, name))
    seen, ranked = set(), []
    for item, name in videos:
        key = (item.get("intake") or {}).get("contentFingerprint") or name.lower()
        if key in seen:
            skipped["duplicate"] = skipped.get("duplicate", 0) + 1
            continue
        seen.add(key)
        ranked.append((item, name))

    def recency(pair):
        item, _name = pair
        return (str(item.get("uploadedAt") or ""), str((item.get("intake") or {}).get("registeredAt") or ""))

    def preference(pair):
        item, name = pair
        dur = duration_seconds(item)
        return (
            1 if family(name) in published_families else 0,  # series already published → later
            0 if dur is None or dur >= TRIM_SECONDS[1] else 1,  # room for a 15s cut → first
        )

    ranked.sort(key=recency, reverse=True)
    ranked.sort(key=preference)  # stable: newest first within each preference band
    picked, families = [], set()
    for item, name in ranked:
        fam = family(name)
        if fam in families:
            continue
        families.add(fam)
        picked.append((item, name))
        if len(picked) >= limit:
            break
    candidates = []
    for item, name in picked:
        desc = str(item.get("viewDescription") or "")
        kind = clip_kind(name, desc)
        dur = duration_seconds(item)
        why = ["מקור לא מפורסם", f"הועלה {item.get('uploadedAt') or 'חסר'}"]
        if (item.get("visualReview") or {}).get("state") in (None, "none") or "טרם" in desc:
            why.append("טרם נצפה")
        why.append(f"משך {dur:g}ש" if dur is not None else "משך לא ידוע (inspect בעריכה)")
        if family(name) in published_families:
            why.append("סדרה שכבר פורסמה")
        link = item.get("productLink")
        candidates.append({
            "id": item.get("id"),
            "fileName": name,
            "sourceUrl": (item.get("sourceFile") or {}).get("url"),
            "uploadedAt": item.get("uploadedAt"),
            "kind": kind,
            "durationSeconds": dur,
            "productLink": link,
            "productClaim": link if link else "אין — אין productLink בקטלוג; לא לטעון איזה מוצר מופיע",
            "why": " · ".join(why),
            "recipe": edit_recipe(name, kind, tools),
            "gate": "candidates_ready",
        })
    return {
        "catalog": str(catalog_path.relative_to(ROOT)) if catalog_path.is_relative_to(ROOT) else str(catalog_path),
        "videosInCatalog": sum(1 for it in items if video_file_name(it)),
        "usableVideos": len(ranked),
        "skipped": skipped,
        "activeEditTools": sorted(v["tool"] for v in tools.values()),
        "candidates": candidates,
    }


def candidate_lines(result: dict) -> list[str]:
    """Short Hebrew brief lines; never claims a product without productLink."""
    lines = []
    for n, cand in enumerate(result.get("candidates") or [], start=1):
        steps = cand["recipe"].get("steps") or []
        tools = " → ".join(Path(s["tool"]).name for s in steps) or "אין כלי עריכה פעיל — ידני"
        kind_he = {"printer_timelapse": "טיימלאפס מדפסת", "phone_clip": "קליפ טלפון"}.get(cand["kind"], "וידאו")
        lines.append(
            f"{n}) {cand['fileName']} · {kind_he} · {cand['uploadedAt']} · {cand['id']}\n"
            f"   למה: {cand['why']}\n"
            f"   מתכון: {tools} · חיתוך 7–15ש · 9:16 1080x1920 · הוק NO_TEXT/עד 5 מילים · CTA בסוף"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Reel candidates from vfmedia/catalog.json (suggestions only)")
    parser.add_argument("--catalog", type=Path, default=MEDIA_CATALOG)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = select_candidates(args.catalog.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n".join(candidate_lines(result)) or "אין וידאו שמיש בקטלוג")
    return 0


if __name__ == "__main__":
    sys.exit(main())
