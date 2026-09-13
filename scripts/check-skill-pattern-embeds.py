#!/usr/bin/env python3
"""Prove the 12 reviewed Claude-skill recommendations are mapped into VelvetOS."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPINGS = [
    ("affaan-m/ECC", "packages/vfharness/AGENT-SURFACE-SECURITY.md", "AgentShield"),
    ("multica-ai/andrej-karpathy-skills", "packages/vfharness/playbooks/implementation-discipline.md", "Karpathy"),
    ("nextlevelbuilder/ui-ux-pro-max-skill", "packages/vfbriefux/hq/UI-SYSTEM.md", "ui-ux-pro-max"),
    ("JuliusBrussee/caveman", "packages/vfharness/playbooks/terse-worker-output.md", "caveman"),
    ("Leonxlnx/taste-skill", "packages/vfbriefux/hq/UI-AUDIT.md", "taste-skill"),
    ("ComposioHQ/awesome-claude-skills", "packages/vfresearch/hq/SKILL-SCOUTING-SOURCES.md", "awesome-claude-skills"),
    ("mvanhorn/last30days-skill", "packages/vfresearch/hq/LAST30.md", "last30days-skill"),
    ("OthmanAdi/planning-with-files", "packages/vfharness/PLANNING-FILES.md", "planning-with-files"),
    ("Nutlope/hallmark", "packages/vfbriefux/hq/UI-AUDIT.md", "hallmark"),
    ("phuryn/pm-skills", "packages/velvetos/PRODUCTIZATION.md", "pm-skills"),
    ("conorbronsdon/avoid-ai-writing", "packages/vfcopy/hq/AI-TELLS-GAP.md", "avoid-ai-writing"),
    ("NeoLabHQ/context-engineering-kit", "packages/vfharness/playbooks/critique-review.md", "context-engineering-kit"),
]


def main() -> int:
    problems: list[str] = []
    for source, rel, needle in MAPPINGS:
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"{source}: missing {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if needle.lower() not in text.lower():
            problems.append(f"{source}: {rel} missing marker {needle!r}")
    wiring = {
        "packages/vfharness/SKILL.md": ["implementation-discipline.md", "critique-review.md", "terse-worker-output.md", "AGENT-SURFACE-SECURITY.md"],
        "packages/vfbriefux/SKILL.md": ["UI-SYSTEM.md", "UI-AUDIT.md"],
    }
    for rel, needles in wiring.items():
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"missing wiring file {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                problems.append(f"{rel}: missing wiring {needle!r}")
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        return 1
    print(f"OK skill-pattern-embeds mapped={len(MAPPINGS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
