"""Live feed CTA / constitution audit for @velvets_cloud (read-only).

Classifies captions from Instagram MCP `list_media` / `get_profile` payloads.
Does NOT mutate live content. Historical violations are reported separately from
publish candidates.

Laws: constitution/PUBLIC_CTA.md — WhatsApp phone is BUSINESS_CONTACT_RECORD only.
"""

from __future__ import annotations

import json
import re
from typing import Any

WA_PHONE = "050-2517000"
WA_PHONE_COMPACT = "0502517000"
HASHTAG_RE = re.compile(r"(?:^|[\s])(#[\w\u0590-\u05FF]+)", re.UNICODE)
MAX_HASHTAGS = 5

FORBIDDEN_CTA_PATTERNS = (
    (r"050[\-\s]?251[\-\s]?7000", "phone_cta"),
    (r"wa\.me/", "wa_me_link"),
    (r"api\.whatsapp\.com", "whatsapp_api_link"),
    (r"וואטסאפ", "whatsapp_he"),
    (r"whatsapp", "whatsapp_en"),
    (r"\bDM\b", "bare_english_dm"),  # constitution: not bare «שלחו DM»
)


def count_hashtags(caption: str) -> int:
    return len(HASHTAG_RE.findall(caption or ""))


def find_forbidden_cta(text: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    blob = text or ""
    compact = re.sub(r"[\s\-]", "", blob)
    if WA_PHONE_COMPACT in compact:
        hits.append({"code": "phone_cta", "match": WA_PHONE})
    for pattern, code in FORBIDDEN_CTA_PATTERNS:
        if code == "phone_cta":
            continue  # handled above
        if re.search(pattern, blob, flags=re.IGNORECASE):
            hits.append({"code": code, "match": pattern})
    # de-dupe by code
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for h in hits:
        if h["code"] in seen:
            continue
        seen.add(h["code"])
        out.append(h)
    return out


def audit_caption(caption: str | None, *, shortcode: str | None = None) -> dict[str, Any]:
    text = caption or ""
    forbidden = find_forbidden_cta(text)
    tags = count_hashtags(text)
    violations: list[str] = []
    if forbidden:
        violations.append("forbidden_public_cta")
    if tags > MAX_HASHTAGS:
        violations.append("hashtag_over_limit")
    return {
        "shortcode": shortcode,
        "hashtag_count": tags,
        "hashtag_limit": MAX_HASHTAGS,
        "forbidden_cta": forbidden,
        "violations": violations,
        "compliant": not violations,
    }


def shortcode_from_permalink(permalink: str | None) -> str | None:
    if not permalink:
        return None
    m = re.search(r"instagram\.com/(?:p|reel|tv)/([^/?#]+)", permalink)
    return m.group(1) if m else None


def audit_media_item(item: dict[str, Any]) -> dict[str, Any]:
    permalink = item.get("permalink") or ""
    shortcode = shortcode_from_permalink(permalink) or item.get("shortcode")
    cap = audit_caption(item.get("caption"), shortcode=shortcode)
    return {
        "id": item.get("id"),
        "shortcode": shortcode,
        "permalink": permalink,
        "media_type": item.get("media_type"),
        "media_product_type": item.get("media_product_type"),
        "timestamp": item.get("timestamp"),
        "bucket": "historical_live",
        "recommended_action": (
            "EDIT_CAPTION_CANDIDATE"
            if "forbidden_public_cta" in cap["violations"]
            else ("TRIM_HASHTAGS" if "hashtag_over_limit" in cap["violations"] else "KEEP")
        ),
        "editable_via_official_graph": False,  # caption mutate unsupported_by_official_graph
        "auto_mutate": False,
        **cap,
    }


def audit_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    profile = profile or {}
    bio = profile.get("biography") or ""
    website = profile.get("website") or ""
    name = profile.get("name") or ""
    blob = "\n".join([name, bio, website])
    forbidden = find_forbidden_cta(blob)
    return {
        "username": profile.get("username"),
        "name": name,
        "biography": bio,
        "website": website,
        "followers_count": profile.get("followers_count"),
        "forbidden_cta": forbidden,
        "violations": ["forbidden_public_cta"] if forbidden else [],
        "compliant": not forbidden,
        "editable_via_official_graph": False,
        "status": "unsupported_by_official_graph" if True else None,
        "note": (
            "Bio/website/name mutations are unsupported_by_official_graph. "
            "Human/app edit required. See PROFILE-DESIRED.json for compliant replacement."
        ),
    }


def audit_list_media_payload(
    media_payload: dict[str, Any] | list[dict[str, Any]],
    *,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(media_payload, dict):
        items = media_payload.get("media") or media_payload.get("data") or []
    else:
        items = media_payload
    audited = [audit_media_item(i) for i in items if isinstance(i, dict)]
    historical_violations = [a for a in audited if not a["compliant"]]
    return {
        "ok": True,
        "handle": "@velvets_cloud",
        "law": "constitution/PUBLIC_CTA.md",
        "public_cta": "instagram_message_only",
        "business_contact_record": WA_PHONE,
        "auto_dm": "forbidden",
        "profile": audit_profile(profile),
        "historical_live": audited,
        "historical_violations": historical_violations,
        "publish_candidates": [],  # filled by office when reviewing queue — not live history
        "counts": {
            "media_scanned": len(audited),
            "historical_violations": len(historical_violations),
        },
        "locks": [
            "no-auto-mutate-history",
            "no-auto-dm",
            "no-invented-insights",
            "unsupported_by_official_graph-caption-edit",
        ],
    }


def dumps(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)
