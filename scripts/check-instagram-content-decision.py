#!/usr/bin/env python3
"""Validate the enforced Instagram content decision policy. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "vfom" / "INSTAGRAM-CONTENT-DECISION.json"
FOUNDRY = ROOT / "packages" / "vfom" / "FOUNDRY.json"
SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
CREW = ROOT / "packages" / "vfe2b" / "crews" / "content.md"
SCENARIO = ROOT / "packages" / "vfe2b" / "scenarios" / "content-live.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be object")
    return value


def must_contain(path: Path, needles: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")


def main() -> None:
    policy = load(POLICY)
    if policy.get("name") != "instagram-content-decision-pipeline" or policy.get("noSecondRuntime") is not True:
        fail("policy identity/noSecondRuntime invalid")

    required_order = [
        "saturation_scan",
        "anti_generic_check",
        "format_selection",
        "hook_tournament",
        "retention_pass",
        "authority_voice_pass",
        "engagement_pass",
        "visual_qa",
        "final_quality_gate",
        "performance_feedback",
    ]
    if policy.get("order") != required_order:
        fail("decision stage order changed or incomplete")

    stages = policy.get("stages") or {}
    missing = [name for name in required_order if name not in stages]
    if missing:
        fail(f"missing stages {missing}")

    saturation = stages["saturation_scan"]
    if saturation.get("neverInventExternalPatterns") is not True or saturation.get("unknownWhenEvidenceMissing") is not True:
        fail("saturation scan must fail honestly when evidence is missing")

    hooks = stages["hook_tournament"]
    if int(hooks.get("candidateMin", 0)) < 8 or int(hooks.get("candidateMax", 0)) < 15:
        fail("hook tournament must generate broad cheap candidate set")
    if set(hooks.get("components") or []) != {"text", "visual", "motion"}:
        fail("hook tournament must include text+visual+motion")
    dims = hooks.get("scoreDimensions") or {}
    required_dims = {"clarity", "curiosity", "relevance", "brandFit", "visualPotential"}
    if set(dims) != required_dims:
        fail("hook score dimensions incomplete")
    if abs(sum(float(v) for v in dims.values()) - 1.0) > 1e-9:
        fail("hook score weights must sum to 1")
    if hooks.get("antiClickbait") is not True:
        fail("anti-clickbait guard must remain enabled")

    fmt = stages["format_selection"]
    if fmt.get("chooseOnePrimary") is not True or fmt.get("doNotGenerateAllFormatsByDefault") is not True:
        fail("format selection must choose one primary and avoid forced multi-format output")

    engagement = stages["engagement_pass"]
    if engagement.get("engagementBaitMustBeFalse") is not True:
        fail("engagement bait guard missing")

    visual = stages["visual_qa"]
    critical = set(visual.get("criticalChecks") or [])
    required_visual = {"contrast", "readability", "crop", "safe_zones", "hierarchy", "branding", "product_visibility", "hebrew_typography", "mobile_preview"}
    if not required_visual.issubset(critical) or visual.get("allCriticalChecksRequiredForPass") is not True:
        fail("visual QA critical checks incomplete")

    gate = stages["final_quality_gate"]
    if gate.get("failClosed") is not True or gate.get("mayRejectPublication") is not True:
        fail("final quality gate must fail closed and be allowed to reject publication")
    required_pre = set(gate.get("requiredPrePublishStages") or [])
    if not set(required_order[:-2]).issubset(required_pre):
        fail("final quality gate does not require all pre-publish decision stages")

    feedback = stages["performance_feedback"]
    if feedback.get("onlyMeasuredEvidence") is not True or feedback.get("neverInventMetrics") is not True:
        fail("performance feedback must use measured evidence only")
    if int(feedback.get("minimumMeasuredPostsBeforePatternPromotion", 0)) < 3:
        fail("pattern promotion sample floor too low")
    if set(feedback.get("writeAuthority") or []) != {"vfinsights", "office-learning"}:
        fail("performance feedback must reuse existing learning authorities")

    foundry = load(FOUNDRY)
    decision = foundry.get("instagramDecisionPolicy") or {}
    if decision.get("enabled") is not True or decision.get("requiredBeforePublish") is not True or decision.get("failClosed") is not True:
        fail("Foundry does not enforce Instagram decision policy")
    if foundry.get("sharedAuthorities", {}).get("instagramDecisionPolicy") != "packages/vfom/INSTAGRAM-CONTENT-DECISION.json":
        fail("Foundry policy authority path mismatch")

    must_contain(SKILL, ("saturation_scan", "anti_generic_check", "hook_tournament", "retention_pass", "authority_voice_pass", "engagement_pass", "visual_qa", "final_quality_gate", "performance_feedback"))
    must_contain(CREW, ("saturation_scan", "hook_tournament", "engagementBait=false", "final_quality_gate", "performance_feedback"))
    must_contain(SCENARIO, ("saturation scan", "hook tournament", "Visual QA", "final quality gate", "performance feedback"))

    print("OK instagram content decision pipeline enforced")


if __name__ == "__main__":
    main()
