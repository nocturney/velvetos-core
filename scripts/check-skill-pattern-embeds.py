#!/usr/bin/env python3
"""Prove reviewed external skill patterns are mapped into VelvetOS."""
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

# Structural wiring only. Runtime/behavior is proved separately by
# check-vfharness-execution-discipline.py and the relevant package sensors.
SUPERPOWERS_V63 = {
    "packages/vfharness/playbooks/executing-plans.md": [
        "Ruling:",
        "preflight.md",
        "Parallel dispatch",
        "fresh whole-plan review",
    ],
    "packages/vfharness/playbooks/writing-plans.md": [
        "Spec / אישור",
        "Shared surfaces / dependencies",
        "RED proof",
        "producer/consumer",
    ],
    "packages/vfharness/playbooks/implementation-discipline.md": [
        "RED → GREEN → REFACTOR",
        "falsifiable",
        "No test theater",
    ],
    "packages/vfharness/playbooks/critique-review.md": [
        "Fresh-context review",
        "Reviewer packet:",
        "fresh whole-plan review",
    ],
    "packages/vfharness/scripts/vf_graceful_escalation.py": [
        "SAFE_RULING",
        "safe_to_rule=False",
        "ruling_text",
    ],
    "scripts/check-vfharness-execution-discipline.py": [
        "behavior-safe",
        "behavior-blocked",
        "behavior-malformed",
    ],
    "packages/vfharness/SKILL.md": [
        "evidence-bearing preflight",
        "RED → GREEN → REFACTOR",
        "fresh-context reviewer",
        "safe_ruling",
    ],
}


def _require_needles(problems: list[str], rel: str, needles: list[str], source: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        problems.append(f"{source}: missing {rel}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            problems.append(f"{source}: {rel} missing marker {needle!r}")


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

    for rel, needles in SUPERPOWERS_V63.items():
        _require_needles(problems, rel, needles, "obra/superpowers v6.3")

    wiring = {
        "packages/vfharness/SKILL.md": [
            "implementation-discipline.md",
            "critique-review.md",
            "terse-worker-output.md",
            "AGENT-SURFACE-SECURITY.md",
            "executing-plans.md",
        ],
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
    print(
        "OK skill-pattern-embeds "
        f"mapped={len(MAPPINGS)} superpowers_v63_files={len(SUPERPOWERS_V63)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
