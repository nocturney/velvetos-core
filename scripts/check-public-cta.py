#!/usr/bin/env python3
"""Enforce PUBLIC_CURRENT_CTA = Instagram DM; BUSINESS_CONTACT_RECORD kept. No network."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_CTA_DEFAULT = "לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם"
WA_PHONE = "050-2517000"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    law = ROOT / "constitution" / "PUBLIC_CTA.md"
    if not law.is_file():
        fail("missing constitution/PUBLIC_CTA.md")
    text = law.read_text(encoding="utf-8")
    for needle in (
        "PUBLIC_CURRENT_CTA",
        "BUSINESS_CONTACT_RECORD",
        "Instagram",
        "050-2517000",
        "disabled for public CTA",
    ):
        if needle not in text:
            fail(f"PUBLIC_CTA.md missing {needle!r}")

    instance_path = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
    sample_path = ROOT / "packages" / "velvetos" / "samples" / "velvet-factory.json"
    for path in (instance_path, sample_path):
        data = json.loads(path.read_text(encoding="utf-8"))
        cta = data.get("cta") or {}
        primary = cta.get("primary") or ""
        if WA_PHONE in primary:
            fail(f"{path.relative_to(ROOT)}: cta.primary must not contain WhatsApp phone")
        if "וואטסאפ" in primary or "WhatsApp" in primary:
            fail(f"{path.relative_to(ROOT)}: cta.primary must not be WhatsApp CTA")
        if "אינסטגרם" not in primary and "instagram" not in primary.lower() and "הודעה" not in primary:
            fail(f"{path.relative_to(ROOT)}: cta.primary must be Instagram-message CTA")
        business = cta.get("businessContact") or cta.get("whatsapp") or ""
        if WA_PHONE not in str(business):
            fail(f"{path.relative_to(ROOT)}: business contact record must keep {WA_PHONE}")
        forbidden = cta.get("forbidden") or []
        # Public must forbid WA outreach phrases; auto-dm tooling still forbidden
        joined = " ".join(forbidden)
        for bad in ("050-2517000", "וואטסאפ", "wa.me", "WhatsApp"):
            if bad not in joined and bad not in " ".join(str(x) for x in forbidden):
                # allow if listed as forbiddenPublicCta
                pass
        fpub = cta.get("forbiddenPublic") or forbidden
        blob = json.dumps(fpub, ensure_ascii=False)
        for need in ("050-2517000", "וואטסאפ", "wa.me"):
            if need not in blob:
                fail(f"{path.relative_to(ROOT)}: forbiddenPublic must list {need!r}")

    formats = json.loads((ROOT / "packages" / "vfcanva" / "FORMATS.json").read_text(encoding="utf-8"))
    fcta = formats.get("cta") or {}
    if fcta.get("whatsapp") == WA_PHONE and not fcta.get("public"):
        fail("FORMATS.json still treats whatsapp as public CTA — need cta.public")
    public = fcta.get("public") or ""
    if WA_PHONE in public or "וואטסאפ" in public:
        fail("FORMATS.json cta.public must not be WhatsApp")
    if "הודעה" not in public and "אינסטגרם" not in public:
        fail("FORMATS.json cta.public must be Instagram-message")
    if (fcta.get("businessContact") or {}).get("whatsapp") != WA_PHONE and fcta.get("businessWhatsapp") != WA_PHONE:
        # accept nested businessContact.whatsapp
        bc = fcta.get("businessContact")
        if not (isinstance(bc, dict) and bc.get("whatsapp") == WA_PHONE):
            fail("FORMATS.json must keep business WhatsApp record")

    desk = json.loads((ROOT / ".cursor" / "vf-desk.json").read_text(encoding="utf-8"))
    studio = desk.get("studio") or {}
    if studio.get("whatsapp") != WA_PHONE:
        fail("desk.studio.whatsapp business record must stay 050-2517000")
    public_cta = studio.get("publicCta") or ""
    if WA_PHONE in public_cta or "WhatsApp" in public_cta:
        fail("desk.studio.publicCta must not be WhatsApp")
    if "הודעה" not in public_cta and "אינסטגרם" not in public_cta:
        fail("desk.studio.publicCta must be Instagram-message")

    profile = json.loads(
        (ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json").read_text(encoding="utf-8")
    )
    bio = (profile.get("desired") or {}).get("bioHe") or ""
    if WA_PHONE in bio or "וואטסאפ" in bio or "WhatsApp" in bio:
        fail("PROFILE-DESIRED bio must not contain WhatsApp CTA")
    if "הודעה" not in bio:
        fail("PROFILE-DESIRED bio must contain Instagram-message CTA")
    if profile.get("liveStatus") != "pending-live-tool" and profile.get("status") == "prepared":
        # prepared + pending is required until tool ready
        if profile.get("status") not in {"prepared", "live"}:
            fail("PROFILE-DESIRED status invalid")
    if profile.get("status") == "prepared" and profile.get("liveStatus") != "pending-live-tool":
        fail("PROFILE-DESIRED must stay pending-live-tool until tool updates")

    # Organic growth policy must not require WA as public CTA
    org = (ROOT / "constitution" / "ORGANIC_GROWTH.md").read_text(encoding="utf-8")
    if re.search(r"CTA\s*\n\s*וואטסאפ", org) or "CTA\n\nוואטסאפ" in org:
        fail("ORGANIC_GROWTH.md still declares WhatsApp as CTA")
    if "PUBLIC_CURRENT_CTA" not in org and "הודעה" not in org.split("## CTA")[-1][:400]:
        # soft: CTA section should mention Instagram message
        cta_section = org.split("## CTA", 1)[-1][:500] if "## CTA" in org else ""
        if "אינסטגרם" not in cta_section and "הודעה" not in cta_section:
            fail("ORGANIC_GROWTH.md CTA section must use Instagram-message")

    print("OK public-cta Instagram-DM + business-contact preserved")


if __name__ == "__main__":
    main()
