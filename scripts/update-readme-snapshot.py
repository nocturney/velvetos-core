#!/usr/bin/env python3
"""Render/check the generated Operational Snapshot block in README.md.

Counts are derived from canonical repository sources; no network and no provider claims.
Use --check in CI to fail when README snapshot is stale.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
MANIFEST = ROOT / "packages" / "manifest.json"
WORKFLOWS = ROOT / ".github" / "workflows"
SCRIPTS = ROOT / "scripts"

START = "<!-- OPERATIONAL-SNAPSHOT:START -->"
END = "<!-- OPERATIONAL-SNAPSHOT:END -->"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render() -> str:
    registry = load_json(REGISTRY)
    manifest = load_json(MANIFEST)
    skills = len(registry.get("skills") or [])
    packs = len(manifest.get("packs") or [])
    sensors = len([p for p in SCRIPTS.glob("check-*.py") if p.name != "check-all.py"])
    workflows = len(list(WORKFLOWS.glob("*.yml"))) + len(list(WORKFLOWS.glob("*.yaml")))

    return f'''{START}
<table>
<tr>
<td align="center"><strong>{skills}</strong><br><sub>Skills · יכולות Living Studio</sub></td>
<td align="center"><strong>{sensors}</strong><br><sub>Sensors · חיישני חוזה</sub></td>
<td align="center"><strong>{workflows}</strong><br><sub>Workflows · אוטומציות GitHub</sub></td>
<td align="center"><strong>{packs}</strong><br><sub>Packs · חבילות מערכת</sub></td>
</tr>
</table>

> **System posture · מצב מערכת:** capability claims are evidence-based; provider-dependent actions remain gated/fail-closed unless live-verified. · הצהרות יכולת נשענות על ראיות; פעולות תלויות ספק נשארות מבוקרות/סגורות-בטוח עד אימות חי.
{END}'''


def apply(text: str, block: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit("README missing operational snapshot markers")
    return pattern.sub(block, text, count=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    current = README.read_text(encoding="utf-8")
    expected = apply(current, render())
    if args.check:
        if current != expected:
            print("FAIL README Operational Snapshot is stale. Run: python3 scripts/update-readme-snapshot.py")
            return 1
        print("OK README Operational Snapshot is current")
        return 0

    README.write_text(expected, encoding="utf-8")
    print("OK README Operational Snapshot updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
