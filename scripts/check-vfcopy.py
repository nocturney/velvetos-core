#!/usr/bin/env python3
"""Content quality sensor for vfcopy.

- Ensures IG captions/stories marked as ready do not contain weak patterns
  (forbidden phrases, DM-only CTA, apology/opening with negation).
- Ensures required STORIES-FIX and PREFLIGHT exist for any G00X in HANDOFF.

This is a static lint: no network, no send.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VFCOPY = ROOT / "packages" / "vfcopy"
VFGROWTH = ROOT / "packages" / "vfgrowth"

FORBIDDEN_PHRASES = [
    "בעידן הדיגיטלי",
    "בעולם שבו",
    "נשמח לעמוד לשירותך",
    "חוויה ייחודית",
    "פתרון מקיף",
    "game-changer",
    "unlock",
]

FORBIDDEN_OPENING_NEG = re.compile(r"^\s*(לא|בלי|אין)\b")
DM_ONLY = re.compile(r"שלחו(?:\s+)?DM", re.IGNORECASE)


def bad_caption_text(text: str, path: Path) -> list[str]:
    problems: list[str] = []
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return [f"ריק: {path}"]
    first = lines[0]
    # Opening should not start with negation
    if FORBIDDEN_OPENING_NEG.search(first):
        problems.append(f"פתיחה מתנצלת/מקטינה ב-{path.name}: {first!r}")
    # Only one emoji in hook (heuristic: too many)
    emojis = re.findall(r"[\U0001F300-\U0001FAFF]", first)
    if len(emojis) > 1:
        problems.append(f"יותר מדי אמוג׳ים בהוק ב-{path.name}: {first!r}")
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in lower:
            problems.append(f"ביטוי AI/שיווק ריק ב-{path.name}: {phrase!r}")
    if DM_ONLY.search(text):
        problems.append(f"CTA 'שלחו DM' אסור ב-{path.name}")
    return problems


def check_vfcopy() -> int:
    if not VFCOPY.is_dir():
        print("OK vfcopy missing (no captions)")
        return 0

    bad: list[str] = []
    # Check main caption files G00X*.md (not VOICE, BIO, DESK)
    for path in sorted(VFCOPY.glob("G0*.md")):
        if path.name.endswith("-STORIES-FIX.md"):
            continue
        text = path.read_text(encoding="utf-8")
        bad.extend(bad_caption_text(text, path))

    # Check STORIES-FIX files as well
    for path in sorted(VFCOPY.glob("G0*-STORIES-FIX.md")):
        text = path.read_text(encoding="utf-8")
        bad.extend(bad_caption_text(text, path))

    # Enforce that any G0XX mentioned in HANDOFF has STORIES-FIX + PREFLIGHT
    handoff = VFGROWTH / "HANDOFF-he.md"
    if handoff.is_file():
        text = handoff.read_text(encoding="utf-8")
        mentioned = sorted(set(re.findall(r"G0\d+", text)))
        preflight_dir = VFGROWTH / "preflight"
        for gid in mentioned:
            stories_fix = VFCOPY / f"{gid}-STORIES-FIX.md"
            preflight = preflight_dir / f"{gid}.md"
            if not stories_fix.is_file():
                bad.append(f"חסר {stories_fix} בעוד {gid} מופיע ב-HANDOFF")
            if not preflight.is_file():
                bad.append(f"חסר {preflight} בעוד {gid} מופיע ב-HANDOFF")

    if bad:
        print("FAIL vfcopy content lint:")
        for line in bad:
            print("-", line)
        return 1
    print("OK vfcopy captions+stories linted")
    return 0


if __name__ == "__main__":
    sys.exit(check_vfcopy())
