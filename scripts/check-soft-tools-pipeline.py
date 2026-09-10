#!/usr/bin/env python3
"""Fail closed when VelvetOS soft writing tools become documentation-only.

This sensor checks that the canonical public-copy chain is present and referenced
at the real content transition points. It does not judge copy quality; it proves
that agents cannot legitimately treat VOICE/Rubric alone as the full copy gate.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "contract": ROOT / "packages/vfcopy/SOFT-TOOLS-CONTRACT.md",
    "vfcopy": ROOT / "packages/vfcopy/SKILL.md",
    "copy_pipeline": ROOT / "packages/vfcopy/skills/velvet-hebrew-copy/PIPELINE.md",
    "content_sprint": ROOT / ".cursor/skills/vf-content-sprint/SKILL.md",
    "cursor_rule": ROOT / ".cursor/rules/velvet-public-copy-soft-tools.mdc",
    "marketing_embed": ROOT / "packages/vfmskill/EMBED.md",
    "edit_gate": ROOT / "packages/vfgrowth/EDIT-GATE.md",
    "preflight": ROOT / "packages/vfgrowth/PREFLIGHT.md",
    "preflight_template": ROOT / "packages/vfgrowth/preflight/TEMPLATE.md",
    "publish_gate": ROOT / "packages/vfgrowth/GATE.md",
    "playbook": ROOT / "packages/vfcopy/hq/PLAYBOOK.md",
    "reader_first": ROOT / "packages/vfcopy/hq/reader-first-he.md",
    "ai_tells": ROOT / "packages/vfcopy/hq/ai-tells-he.md",
    "voice": ROOT / "packages/vfcopy/VOICE.md",
    "voice_chart": ROOT / "packages/vfcopy/VOICE-CHART.md",
    "lint": ROOT / "scripts/check-vfcopy.py",
}

TOKEN_REQUIREMENTS = {
    "contract": [
        "reader-first",
        "VOICE.md",
        "VOICE-CHART.md",
        "voice/approved/",
        "copywriting",
        "copy-editing",
        "marketing-psychology",
        "prompts.chat",
        "velvet-hebrew-copy",
        "ai-tells-he.md",
        "write-better",
        "Humanizer",
        "check-vfcopy.py lint",
        "CONTENT-RUBRIC",
        "PREFLIGHT",
        "final copy",
    ],
    "vfcopy": [
        "SOFT-TOOLS-CONTRACT.md",
        "reader-first-he.md",
        "copywriting",
        "copy-editing",
        "marketing-psychology",
        "VOICE-CHART",
        "velvet-hebrew-copy",
        "ai-tells-he.md",
        "check-vfcopy.py lint",
        "CONTENT-RUBRIC",
        "PREFLIGHT",
    ],
    "copy_pipeline": [
        "Reader-first",
        "velvet-hebrew-copy",
        "Humanizer",
        "check-vfcopy.py lint",
        "Factual validation",
        "NO_TEXT",
    ],
    "content_sprint": [
        "SOFT-TOOLS-CONTRACT.md",
        "reader-first-he.md",
        "VOICE-CHART.md",
        "voice/approved/",
        "velvet-hebrew-copy",
        "ai-tells-he.md",
        "check-vfcopy.py lint",
        "final copy",
        "CONTENT-RUBRIC",
        "PREFLIGHT",
    ],
    "cursor_rule": [
        "alwaysApply: true",
        "SOFT-TOOLS-CONTRACT.md",
        "reader-first",
        "copywriting/copy-editing/marketing-psychology",
        "velvet-hebrew-copy",
        "check-vfcopy.py lint",
        "CONTENT-RUBRIC",
        "PREFLIGHT",
    ],
    "marketing_embed": [
        "SOFT-TOOLS-CONTRACT.md",
        "copywriting",
        "copy-editing",
        "marketing-psychology",
        "reader-first-he.md",
        "VOICE-CHART.md",
        "velvet-hebrew-copy",
        "check-vfcopy.py lint",
        "PUBLIC_CTA.md",
    ],
    "edit_gate": [
        "SOFT-TOOLS-CONTRACT.md",
        "reader-first",
        "velvet-hebrew-copy",
        "ai-tells-he",
        "check-vfcopy.py lint",
        "vfcopy_lint=pass",
    ],
    "preflight": [
        "SOFT-TOOLS-CONTRACT",
        "reader-first",
        "velvet-hebrew-copy",
        "ai-tells-he.md",
        "check-vfcopy.py lint",
        "vfcopy_lint=pass",
        "needs_input",
    ],
    "preflight_template": [
        "SOFT-TOOLS-CONTRACT.md",
        "reader_first:",
        "marketing_aids:",
        "copywriting:",
        "copy-editing:",
        "marketing-psychology:",
        "vfcopy_lint:",
        "vfcopy_lint_version:",
        "fact_gate:",
        "visual_copy_decision:",
    ],
    "publish_gate": [
        "SOFT-TOOLS-CONTRACT.md",
        "reader-first",
        "velvet-hebrew-copy",
        "check-vfcopy.py lint",
        "fact gate",
        "vfcopy_lint=pass",
    ],
    "playbook": [
        "reader-first-he.md",
        "velvet-hebrew-copy/SKILL.md",
        "ai-tells-he.md",
        "check-vfcopy.py lint",
    ],
}

FORBIDDEN_WEAKENING = {
    "content_sprint": [
        "draft Hebrew through `vfcopy/VOICE.md`; use",
    ],
    "marketing_embed": [
        "CTA וואטסאפ",
        "שלחו DM",
    ],
}


def main() -> int:
    problems: list[str] = []
    bodies: dict[str, str] = {}

    for name, path in REQUIRED_FILES.items():
        if not path.exists():
            problems.append(f"missing required soft-tools component: {path.relative_to(ROOT)}")
            continue
        bodies[name] = path.read_text(encoding="utf-8")

    for name, tokens in TOKEN_REQUIREMENTS.items():
        body = bodies.get(name)
        if body is None:
            continue
        body_folded = body.casefold()
        for token in tokens:
            if token.casefold() not in body_folded:
                problems.append(f"{name} is not wired to required token: {token!r}")

    for name, forbidden in FORBIDDEN_WEAKENING.items():
        body = bodies.get(name, "")
        for token in forbidden:
            if token in body:
                problems.append(
                    f"{name} still contains a weakening/legacy route that can bypass current copy policy: {token!r}"
                )

    contract = bodies.get("contract", "")
    if "Origin grants no exemption" not in contract:
        problems.append("contract must apply equally to agent/tool/human-originated public copy")
    if "Any rewrite after lint requires lint again" not in contract:
        problems.append("contract must invalidate lint after rewrites")

    if problems:
        print("SOFT TOOLS PIPELINE: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("SOFT TOOLS PIPELINE: PASS")
    print("- reader-first -> voice -> marketing aids -> templates -> velvet-hebrew-copy -> humanizer/lint -> fact gate")
    print("- vfcopy, Cursor rule, content sprint, edit gate, preflight/template and publish gate all reference the mandatory contract")
    print("- copy-version invalidation is fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
