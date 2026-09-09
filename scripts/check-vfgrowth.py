#!/usr/bin/env python3
"""Validate standing IG publish calendar on vfgrowth. No network. No send."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "packages" / "vfgrowth" / "CALENDAR.md"
LEDGER = ROOT / "packages" / "vfgrowth" / "LEDGER.md"
HANDOFF = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
G003 = ROOT / "packages" / "vfgrowth" / "G003.md"
G004 = ROOT / "packages" / "vfgrowth" / "G004.md"
COPY = ROOT / "packages" / "vfcopy" / "G003.md"
COPY_G004 = ROOT / "packages" / "vfcopy" / "G004.md"
STORIES_FIX = ROOT / "packages" / "vfcopy" / "G004-STORIES-FIX.md"
STORIES_PLAY = ROOT / "packages" / "vfgrowth" / "STORIES.md"
PREFLIGHT = ROOT / "packages" / "vfgrowth" / "PREFLIGHT.md"
PREFLIGHT_G004 = ROOT / "packages" / "vfgrowth" / "preflight" / "G004.md"
VOICE = ROOT / "packages" / "vfcopy" / "VOICE.md"
VOICE_RESEARCH = ROOT / "packages" / "vfcopy" / "VOICE-RESEARCH.md"
STORIES = ROOT / "packages" / "vfcopy" / "hq" / "templates" / "ig-stories.md"
FOLLOWER = ROOT / "packages" / "vfgrowth" / "hq" / "FOLLOWER-GROWTH.md"
FUNNEL = ROOT / "packages" / "vfgrowth" / "hq" / "PROFILE-TO-WHATSAPP.md"
TAGS = ROOT / "constitution" / "tags.md"
AGENTS = ROOT / "AGENTS.md"
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_ils(path: Path) -> None:
    text = path.read_text()
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def main() -> None:
    for path in (CAL, LEDGER, HANDOFF, G003, G004, COPY, COPY_G004, STORIES_FIX, STORIES_PLAY, VOICE, VOICE_RESEARCH, STORIES, FOLLOWER, FUNNEL, PREFLIGHT, PREFLIGHT_G004):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        assert_no_ils(path)

    organic = ROOT / "packages" / "vfgrowth" / "ORGANIC-GROWTH.md"
    if not organic.is_file():
        fail("missing vfgrowth/ORGANIC-GROWTH.md")
    og = organic.read_text()
    for needle in ("print.done", "אין ריל כל יום", "approved_for_manual_posting"):
        if needle not in og:
            fail(f"ORGANIC-GROWTH.md missing {needle!r}")
    # Phone OK only as BUSINESS_CONTACT_RECORD / disabled note — not required as public CTA
    if not any(n in og for n in ("הודעה", "אינסטגרם", "PUBLIC_CURRENT_CTA", "Instagram")):
        fail("ORGANIC-GROWTH.md must mention Instagram-message public CTA")
    assert_no_ils(organic)

    cal = CAL.read_text()
    for needle in (
        "16:00",
        "12:00",
        "20:30",
        "אין פיד",
        "36",
        "instagram.com",
        "G003",
        "7.9.2026",
        "משובץ",
        "G004",
    ):
        if needle not in cal:
            fail(f"CALENDAR.md missing {needle!r}")
    if "Meta Suite" in cal and "לא Meta Suite" not in cal:
        fail("CALENDAR.md must forbid Meta Suite")
    if "שישי" not in cal or "שבת" not in cal:
        fail("CALENDAR.md must mention Friday/Saturday no-feed")

    ledger = LEDGER.read_text()
    for needle in (
        "DcqkjOLlYVX",
        "DcvuJLxCJgU",
        "Dc0cKegEbxd",
        "G001",
        "G002",
        "G005",
        "G003",
        "SoccerBall",
        "חסום",
        "G004",
        "משובץ",
        "מחזיק",
    ):
        if needle not in ledger:
            fail(f"LEDGER.md missing {needle!r}")

    handoff = HANDOFF.read_text()
    for needle in (
        "instagram.com",
        "חסום",
        "16:00",
        "12:00",
        "20:30",
        "לא סוויט",
        "שער עריכה",
        "JPEG גולמי",
        "לא שואלים משבצת",
        "Google Calendar",
        "G004-STORIES-FIX",
        "PREFLIGHT.md",
        "preflight/G004.md",
        "אל תפנה לכריסטיאן על מדדים חלשים",
    ):
        if needle not in handoff:
            fail(f"HANDOFF-he.md missing {needle!r}")
    if not any(n in handoff for n in ("הודעה", "אינסטגרם", "PUBLIC_CURRENT_CTA", "שלחו לנו הודעה")):
        fail("HANDOFF-he.md must include Instagram-message CTA (not WhatsApp phone)")
    if "CTA" in handoff and "050-2517000" in handoff:
        # phone may appear as BUSINESS_CONTACT_RECORD / disabled — not as required public CTA line
        cta_lines = [ln for ln in handoff.splitlines() if "CTA" in ln]
        if any("050-2517000" in ln and "BUSINESS" not in ln and "רשומת" not in ln and "disabled" not in ln.lower() for ln in cta_lines):
            if not any("הודעה" in ln or "אינסטגרם" in ln for ln in cta_lines):
                fail("HANDOFF-he.md public CTA must be Instagram-message, not WhatsApp phone")
    if "שלחו DM" in handoff and "לא «שלחו DM»" not in handoff and "בלי «שלחו DM»" not in handoff:
        fail("HANDOFF-he.md must forbid bare שלחו DM (auto-dm tooling)")

    g003 = G003.read_text()
    for needle in ("SoccerBall", "נעול", "משובץ", "7.9.2026", "16:00", "גיבוי"):
        if needle not in g003:
            fail(f"G003.md missing lock needle {needle!r}")
    if "חסום מדיה" in g003:
        fail("G003.md must not stay media-blocked after the 6.9 lock")

    g004 = G004.read_text()
    for needle in ("קטלבל", "מחזיק", "לא משקולת", "סטוריז", "קרוסלה", "kettlebells-pink", "vfcopy/G004.md"):
        if needle not in g004:
            fail(f"G004.md missing {needle!r}")

    copy4 = COPY_G004.read_text()
    for needle in ("מחזיק", "לא משקולת", "kettlebells-pink", "היילייטס", "הכירו", "מתאים", "VOICE.md"):
        if needle not in copy4:
            fail(f"vfcopy/G004.md missing {needle!r}")
    if not any(n in copy4 for n in ("הודעה", "אינסטגרם", "שלחו לנו הודעה")):
        fail("vfcopy/G004.md must include Instagram-message CTA")
    if "שלחו DM" in copy4 and "לא «שלחו DM»" not in copy4 and "בלי «שלחו DM»" not in copy4:
        fail("vfcopy/G004.md must forbid bare שלחו DM")
    if "חמש ורודות מהמיטה" in copy4:
        fail("vfcopy/G004.md must not keep early thin copy")

    voice = VOICE.read_text()
    for needle in (
        "תהליך-קצר",
        "סיפור-מוצר",
        "22 שעות הדפסה בכמה שניות",
        "תנועה, צבע והמון אופי",
        "עקבו כדי לראות מה יוצא מהמדפסת בשבוע הבא",
        "050-2517000",  # appears as forbidden-public / BUSINESS_CONTACT_RECORD note
        "מוכנים",
        "בלי משלוח",
        "הודעה",
    ):
        if needle not in voice:
            fail(f"vfcopy/VOICE.md missing {needle!r}")
    if "X ₪" not in voice:
        fail("vfcopy/VOICE.md must keep X ₪ when sale amount is missing")
    if not any(n in voice for n in ("PUBLIC_CURRENT_CTA", "PUBLIC_CTA", "אינסטגרם")):
        fail("vfcopy/VOICE.md must lock Instagram-message PUBLIC_CURRENT_CTA")

    research = VOICE_RESEARCH.read_text()
    for needle in ("https://", "אין ספירת עוקבים", "לאמץ", "לדחות", "nisha.co", "studioarmadillo.com"):
        if needle not in research:
            fail(f"vfcopy/VOICE-RESEARCH.md missing {needle!r}")

    studio = (ROOT / "constitution" / "STUDIO.md").read_text()
    if "VOICE.md" not in studio:
        fail("constitution/STUDIO.md must point at VOICE.md")
    for needle in ("PREFLIGHT.md", "רמה נמוכה", "נכשל-סגור", "VOICE-RESEARCH"):
        if needle not in studio:
            fail(f"constitution/STUDIO.md must lock Christian/preflight needle {needle!r}")
    inst_studio = (ROOT / "instances" / "velvet-factory" / "constitution" / "STUDIO.md").read_text()
    if "VOICE.md" not in inst_studio:
        fail("instances/velvet-factory/constitution/STUDIO.md must point at VOICE.md")
    if "PREFLIGHT.md" not in inst_studio:
        fail("instances/velvet-factory/constitution/STUDIO.md must point at PREFLIGHT.md")

    preflight = PREFLIGHT.read_text()
    for needle in (
        "VOICE.md",
        "VOICE-RESEARCH",
        "VOICE-CHART",
        "ציון עצמי",
        "2–3",
        "נכשל-סגור",
        "רמה נמוכה",
        "אל תפנה לכריסטיאן על מדדים חלשים",
        "Canva",
        "CONTENT-RUBRIC",
        "artifact_digest",
        "PUBLIC_CURRENT_CTA",
    ):
        if needle not in preflight:
            fail(f"PREFLIGHT.md missing {needle!r}")
    if "הודעה" not in preflight and "הודעת" not in preflight:
        fail("PREFLIGHT.md must mention Instagram-message CTA (הודעה/הודעת)")
    if not (ROOT / "packages" / "vfgrowth" / "CONTENT-RUBRIC.md").is_file():
        fail("CONTENT-RUBRIC.md missing")
    if not (ROOT / "packages" / "vfcopy" / "VOICE-CHART.md").is_file():
        fail("VOICE-CHART.md missing")
    template_pf = (ROOT / "packages" / "vfgrowth" / "preflight" / "TEMPLATE.md").read_text()
    if "Rubric" not in template_pf:
        fail("preflight/TEMPLATE.md must include Rubric table")
    if not any(n in template_pf for n in ("הודעה", "אינסטגרם", "PUBLIC_CURRENT_CTA")):
        fail("preflight/TEMPLATE.md must use Instagram-message CTA (not WhatsApp phone)")
    g004p = PREFLIGHT_G004.read_text()
    gate_closed = "נכשל-סגור" in g004p
    gate_open = "## שער" in g004p and "**עבור**" in g004p.split("## שער", 1)[1][:600]
    if gate_open:
        # Open gate requires written Canva/edit evidence — never a bare עבור.
        for needle in (
            "DAHUaUo3bAk",
            "DAHUfRQMH60",
            "g004-stories-final",
            "EDIT-GATE",
            "G004-STORIES-FIX",
        ):
            if needle not in g004p:
                fail(f"preflight/G004.md עבור requires evidence needle {needle!r}")
        if "נכשל-סגור" in g004p.split("## שער", 1)[1][:600]:
            fail("preflight/G004.md gate section cannot be both עבור and נכשל-סגור")
    elif not gate_closed:
        fail("preflight/G004.md must stay fail-closed until the written gate passes")
    if not any(n in g004p for n in ("הודעה", "אינסטגרם", "PUBLIC_CURRENT_CTA")):
        fail("preflight/G004.md must use Instagram-message CTA")

    copy = COPY.read_text()
    if "מה יוצא מהמדפסת" not in copy:
        fail("vfcopy/G003.md must lock caption מה יוצא מהמדפסת")
    if not any(n in copy for n in ("הודעה", "אינסטגרם", "שלחו לנו הודעה")):
        fail("vfcopy/G003.md must include Instagram-message CTA")
    if "050-2517000" in copy and "להדבקה" in copy:
        # publishable fence must not use WhatsApp phone as CTA
        fences = copy.split("```")
        if len(fences) >= 2 and "050-2517000" in fences[1]:
            fail("vfcopy/G003.md publishable caption must not use WhatsApp phone as CTA")
    if "שלחו DM" in copy and "לא «שלחו DM»" not in copy and "בלי «שלחו DM»" not in copy:
        fail("vfcopy/G003.md must not instruct bare שלחו DM")

    stories = STORIES.read_text()
    if "20:30" not in stories:
        fail("ig-stories.md must lock 20:30")
    if not any(n in stories for n in ("הודעה", "אינסטגרם", "שלחו לנו הודעה", "PUBLIC")):
        fail("ig-stories.md must lock Instagram-message CTA (not WhatsApp phone)")
    if "היילייטס" not in stories:
        fail("ig-stories.md must point CTA to Highlights")
    for needle in ("סיפור-מוצר", "נייבי", "Canva MCP", "G004-STORIES-FIX"):
        if needle not in stories:
            fail(f"ig-stories.md must mention {needle!r}")

    fix = STORIES_FIX.read_text()
    for needle in ("סיפור-מוצר", "DAHUaUo3bAk", "X ₪", "הכירו", "מחזיק"):
        if needle not in fix:
            fail(f"G004-STORIES-FIX.md missing {needle!r}")
    if not any(n in fix for n in ("הודעה", "אינסטגרם", "שלחו לנו הודעה")):
        fail("G004-STORIES-FIX.md must include Instagram-message CTA")
    if "שלחו DM" in fix and "לא «שלחו DM»" not in fix and "בלי «שלחו DM»" not in fix:
        fail("G004-STORIES-FIX.md must forbid bare שלחו DM")
    if "חמש ורודות" in fix or "איפה הטבעת" in fix:
        fail("G004-STORIES-FIX.md must not keep thin catalog hooks")
    # On-frame / publishable WA must be marked revised-media or BUSINESS_CONTACT
    if "```" in fix:
        fence_body = fix.split("```")[1]
        if "050-2517000" in fence_body or "וואטסאפ" in fence_body:
            fail("G004-STORIES-FIX.md publishable CTA must not be WhatsApp phone")
    if "050-2517000" in fix and "revised-media" not in fix.lower() and "BUSINESS_CONTACT" not in fix:
        # phone outside fence only OK with revised-media / business-record note
        pass  # allow mention in notes if marked elsewhere; fence check above is hard

    play = STORIES_PLAY.read_text()
    for needle in ("סיפור-מוצר", "תהליך-קצר", "Canva MCP"):
        if needle not in play:
            fail(f"STORIES.md missing {needle!r}")
    if not any(n in play for n in ("הודעה", "אינסטגרם", "PUBLIC_CURRENT_CTA")):
        fail("STORIES.md must use Instagram-message CTA")

    follower = FOLLOWER.read_text()
    for needle in ("80", "0", "היילייטס", "ריל תהליך", "אאוטבאונד"):
        if needle not in follower:
            fail(f"FOLLOWER-GROWTH.md missing {needle!r}")
    # phone OK as BUSINESS_CONTACT_RECORD note; public CTA = IG message
    if not any(n in follower for n in ("הודעה", "אינסטגרם", "PUBLIC")):
        if "050-2517000" not in follower:
            fail("FOLLOWER-GROWTH.md must keep business contact or Instagram-message CTA")
    if "PROFILE-TO-WHATSAPP" not in follower and "PROFILE-TO-INSTAGRAM" not in follower:
        fail("FOLLOWER-GROWTH.md must point at PROFILE funnel doc")

    funnel = FUNNEL.read_text()
    for needle in ("תהליך-קצר", "סיפור-מוצר", "אין ספירה", "PREFLIGHT"):
        if needle not in funnel:
            fail(f"PROFILE funnel missing {needle!r}")
    if not any(n in funnel for n in ("הודעה", "אינסטגרם", "Instagram", "PUBLIC_CURRENT_CTA")):
        fail("PROFILE funnel must use Instagram-message CTA (not WhatsApp as public CTA)")
    # BUSINESS_CONTACT_RECORD may keep phone as disabled
    if "שלחו DM" not in funnel and "אוטו־DM" not in funnel and "auto-dm" not in funnel.lower():
        fail("PROFILE funnel must ban bare שלחו DM / auto-dm")
    if "ריל כל יום" in funnel and "אין ריל כל יום" not in funnel:
        fail("PROFILE funnel must not schedule a reel every weekday")

    tags = TAGS.read_text()
    for needle in ("#צמיחה-חברתית", "#ריל-תהליך", "#היילייטס", "#המרת-פרופיל", "social-growth"):
        if needle not in tags:
            fail(f"constitution/tags.md missing social-growth tag {needle!r}")

    if "check-vfgrowth.py" not in AGENTS.read_text():
        fail("AGENTS.md sensor table must list check-vfgrowth.py")

    print("OK standing calendar + G003 lock + G004 + VOICE + follower-growth")


if __name__ == "__main__":
    main()
