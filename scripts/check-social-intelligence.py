#!/usr/bin/env python3
"""Validate Social Intelligence integration. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "packages" / "vfresearch" / "SOCIAL-INTELLIGENCE.md"
PACKET_SCHEMA = ROOT / "packages" / "vfresearch" / "social-research-packet.schema.json"
REFERENCE_SCHEMA = ROOT / "packages" / "vfresearch" / "reference-pattern.schema.json"
SCRIPT = ROOT / "scripts" / "vf_social_intelligence.py"
DECISION = ROOT / "packages" / "vfom" / "INSTAGRAM-CONTENT-DECISION.json"
INSIGHTS = ROOT / "packages" / "vfinsights" / "scripts" / "vf_insights_loop.py"
ANNOTATIONS = ROOT / "packages" / "vfinsights" / "data" / "creative-annotations.csv"
INSIGHTS_SKILL = ROOT / "packages" / "vfinsights" / "SKILL.md"
RESEARCH_SKILL = ROOT / "packages" / "vfresearch" / "SKILL.md"
CONTENT_SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"

EXPECTED_ANGLES = {
    "actionable", "motivational", "analytical", "contrarian",
    "observation", "x_vs_y", "present_vs_future", "listicle",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (DOC, PACKET_SCHEMA, REFERENCE_SCHEMA, SCRIPT, DECISION, INSIGHTS, ANNOTATIONS, INSIGHTS_SKILL, RESEARCH_SKILL, CONTENT_SKILL, LINKS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    for schema in (PACKET_SCHEMA, REFERENCE_SCHEMA):
        data = json.loads(schema.read_text(encoding="utf-8"))
        if data.get("type") != "object":
            fail(f"{schema.name} must be object schema")

    doc = DOC.read_text(encoding="utf-8")
    for needle in (
        "Instagram MCP remains canonical",
        "public material",
        "No cookies",
        "Content Matrix",
        "outlier_score: null",
        "CREATIVE-PERFORMANCE-PROFILE.json",
        "no composite virality score",
    ):
        if needle.lower() not in doc.lower():
            fail(f"SOCIAL-INTELLIGENCE.md missing {needle}")

    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    if decision.get("version", 0) < 2:
        fail("INSTAGRAM-CONTENT-DECISION version must be >=2")
    order = decision.get("order") or []
    if not order or order[0] != "content_matrix":
        fail("content_matrix must run before saturation_scan")
    stage = (decision.get("stages") or {}).get("content_matrix") or {}
    if stage.get("enabled") is not True:
        fail("content_matrix must be enabled")
    if set(stage.get("formats") or []) != EXPECTED_ANGLES:
        fail("content_matrix must expose exact 8 angle families")
    if stage.get("noPublishAuthority") is not True:
        fail("content_matrix must have no publish authority")
    required = ((decision.get("stages") or {}).get("final_quality_gate") or {}).get("requiredPrePublishStages") or []
    if "content_matrix" not in required:
        fail("final gate must require evidenced content_matrix stage/N-A")

    insight_text = INSIGHTS.read_text(encoding="utf-8")
    for needle in ("CREATIVE-PERFORMANCE-PROFILE.json", "creative-annotations.csv", "MIN_MEASURED_POSTS_FOR_RECOMMENDATION"):
        if needle not in insight_text:
            fail(f"vf_insights_loop missing {needle}")

    content = CONTENT_SKILL.read_text(encoding="utf-8")
    if "content_matrix" not in content or "SocialResearchPacket" not in content:
        fail("vf-content-sprint must consume content_matrix + SocialResearchPacket")

    research = RESEARCH_SKILL.read_text(encoding="utf-8")
    if "SOCIAL-INTELLIGENCE.md" not in research:
        fail("vfresearch SKILL must route Social Intelligence")

    links = json.loads(LINKS.read_text(encoding="utf-8"))
    ids = {x.get("id") for x in links.get("links") or []}
    for need in ("charlie947-social-media-skills", "cporter202-automate-for-growth", "cporter202-social-media-scraping-apis"):
        if need not in ids:
            fail(f"LINKS.json missing {need}")

    proc = subprocess.run([sys.executable, str(SCRIPT), "--self-test"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail((proc.stderr or proc.stdout or "self-test failed").strip())

    print("OK social-intelligence integration")


if __name__ == "__main__":
    main()
