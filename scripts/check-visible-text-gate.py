#!/usr/bin/env python3
"""Validate global human-visible AI text gating across VelvetOS surfaces.

Static wiring sensor only. It proves the rules/routes/gate executable are present; it
must never be presented as proof that a particular future candidate actually ran.
Per-candidate execution evidence belongs in the relevant artifact/preflight/digest.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def require(rel: str, needles: tuple[str, ...]) -> None:
    body = text(rel)
    for needle in needles:
        if needle not in body:
            fail(f"{rel} missing {needle!r}")


def main() -> None:
    require(
        "constitution/VISIBLE_TEXT.md",
        (
            "כל טקסט",
            "כריסטיאן",
            "לקוח",
            "reader-first-he.md",
            "velvet-hebrew-copy",
            "ai-tells-he.md",
            "approved_static_copy",
            "visible_text_gate: PASS",
            "UNPROVEN",
        ),
    )
    require(
        "constitution/CONSTITUTION.md",
        ("Visible Text Gate", "VISIBLE_TEXT.md", "packages/vfcopy", "אין `PASS` בלי ביצוע בפועל"),
    )
    require(
        "AGENTS.md",
        (
            "Visible Text Gate is global",
            "constitution/VISIBLE_TEXT.md",
            "customer-message",
            "owner-brief",
            "human-document",
            "ui-microcopy",
            "UNPROVEN",
            "scripts/check-visible-text-gate.py",
        ),
    )
    rule = text(".cursor/rules/visible-text-gate.mdc")
    if "alwaysApply: true" not in rule:
        fail(".cursor/rules/visible-text-gate.mdc must be alwaysApply: true")
    for needle in (
        "constitution/VISIBLE_TEXT.md",
        "owner-facing",
        "customer",
        "reader-first-he.md",
        "vf-hebrew-copy",
        "ai-tells-he.md",
        "UNPROVEN",
    ):
        if needle not in rule:
            fail(f"always-on visible-text rule missing {needle!r}")

    require(
        "packages/vfcopy/SOFT-TOOLS-CONTRACT.md",
        (
            "human-visible AI text",
            "public-social",
            "customer-message",
            "sales-proposal",
            "owner-brief",
            "human-document",
            "ui-microcopy",
            "scripts/vf_visible_text.py",
            "text_sha256",
        ),
    )
    require(
        "packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md",
        (
            "לכל טקסט אנושי נראה",
            "customer-message",
            "sales-proposal",
            "owner-brief",
            "human-document",
            "ui-microcopy",
            "reader-first-he.md",
            "ai-tells-he.md",
            "visible_text_gate",
        ),
    )
    require(
        "packages/vfcopy/skills/velvet-hebrew-copy/PIPELINE.md",
        (
            "PIPELINE — Visible Text Gate",
            "public-social",
            "visual-microcopy",
            "customer-message",
            "sales-proposal",
            "owner-brief",
            "human-document",
            "ui-microcopy",
            "UNPROVEN",
        ),
    )
    require(
        ".cursor/skills/vf-hebrew-copy/SKILL.md",
        (
            "human-visible",
            "owner-brief",
            "customer-message",
            "sales-proposal",
            "human-document",
            "ui-microcopy",
            "visible_text_gate: PASS",
        ),
    )

    require(
        ".cursor/skills/vf-inquiry-chain/SKILL.md",
        ("VISIBLE_TEXT.md", "customer-message", "sales-proposal", "visible_text_gate: PASS"),
    )
    require(
        "packages/vfe2b/crews/inquiry.md",
        ("VISIBLE_TEXT.md", "customer-message", "ai-tells-he.md", "visible_text_gate: PASS"),
    )
    require(
        "packages/vfconvert/WHATSAPP.md",
        ("VISIBLE_TEXT.md", "customer-message", "surface-aware lint", "visible_text_gate: PASS"),
    )
    require(
        "packages/vfsales/QUOTE.md",
        ("VISIBLE_TEXT.md", "sales-proposal", "reader-first-he.md", "ai-tells-he.md", "visible_text_gate: PASS"),
    )

    require(
        ".cursor/skills/vf-morning-brief/SKILL.md",
        ("VISIBLE_TEXT.md", "owner-brief", "reader-first-he.md", "visible_text_gate: PASS"),
    )
    require(
        "packages/vfe2b/crews/morning-brief.md",
        ("VISIBLE_TEXT.md", "owner-brief", "ai-tells-he.md", "visible_text_gate: PASS"),
    )

    require(
        "constitution/SEND.md",
        (
            "VISIBLE_TEXT.md",
            "Transport readiness ≠ text readiness",
            "customer-message",
            "owner-brief",
            "public-social",
            "visual-microcopy",
            "visible_text_gate: PASS",
        ),
    )
    require(
        "packages/vfgrowth/PREFLIGHT.md",
        ("VISIBLE_TEXT.md", "visible_text_gate: PASS", "text_sha256", "visual-microcopy", "UNPROVEN"),
    )
    require(
        "packages/vfgrowth/preflight/TEMPLATE.md",
        (
            "visible_text_gate: FAIL",
            "visible_text_surface: public-social",
            "text_sha256",
            "humanizer_ai_tells",
            "visual_text_gate",
            "הודעת Instagram",
        ),
    )

    gate = text("scripts/vf_visible_text.py")
    for needle in (
        "public-social",
        "visual-microcopy",
        "customer-message",
        "sales-proposal",
        "owner-brief",
        "human-document",
        "ui-microcopy",
        "text_sha256",
        "visible_text_gate",
        "UNPROVEN",
        "--gate",
    ):
        if needle not in gate:
            fail(f"scripts/vf_visible_text.py missing {needle!r}")
    if "surface not in PUBLIC_SURFACES" not in gate:
        fail("surface-aware gate must distinguish public-only lint rules")

    require(
        "packages/vfom/FOUNDRY.json",
        ("visualCopyPolicy", "noTextBaselineRequired", "vf-hebrew-copy", "ai-tells-he.md"),
    )
    require(
        ".cursor/skills/velvet-creative-director/SKILL.md",
        ("NO_TEXT", "velvet-hebrew-copy"),
    )
    require(
        ".cursor/skills/velvet-brand-guardian/SKILL.md",
        ("NO_TEXT", "velvet-hebrew-copy", "ai-tells-he.md"),
    )

    print("OK visible-text-gate global human-facing routes + agent guide + surface-aware executable bound")


if __name__ == "__main__":
    main()
