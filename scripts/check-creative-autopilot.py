#!/usr/bin/env python3
"""Validate Velvet Factory Visual Foundry / Creative Autopilot contracts. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOPILOT = ROOT / "packages" / "vfom" / "CREATIVE-AUTOPILOT.md"
FOUNDRY = ROOT / "packages" / "vfom" / "FOUNDRY.json"
CONTRACT = ROOT / "packages" / "vfom" / "CONTENT-CONTRACT.schema.json"
DNA = ROOT / "packages" / "vfom" / "VISUAL-DNA.json"
VISUAL = ROOT / "packages" / "vfom" / "VISUAL-OS.md"
EDIT = ROOT / "packages" / "vfom" / "EDIT-DIRECTOR.md"
MEDIA_DIRECTOR = ROOT / "packages" / "vfom" / "experts" / "MEDIA-DIRECTOR.md"
MODULE = ROOT / "packages" / "velvetos" / "modules" / "expert-media-director.md"
CREW = ROOT / "packages" / "vfe2b" / "crews" / "content.md"
SCENARIO = ROOT / "packages" / "vfe2b" / "scenarios" / "content-live.md"
GATE = ROOT / "packages" / "vfgrowth" / "GATE.md"
POLICY = ROOT / "constitution" / "ORGANIC_GROWTH.md"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
MEDIA_SKILL = ROOT / "packages" / "vfmedia" / "SKILL.md"
MEDIA_SCHEMA = ROOT / "packages" / "vfmedia" / "catalog.schema.json"
CONTENT_GRAPH = ROOT / "packages" / "vfgraft" / "graph" / "content-job.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def must_contain(path: Path, needles: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def require_subset(actual: set[str], required: set[str], label: str) -> None:
    missing = required - actual
    if missing:
        fail(f"{label} missing {sorted(missing)}")


def main() -> None:
    must_contain(AUTOPILOT, (
        "orchestrator שני",
        "Content Contract",
        "Claim Provenance",
        "Progressive Multi-Variant Director",
        "Evaluation Engine",
        "Artifact Repair Router",
        "Novelty / Fatigue Memory",
        "Exception Queue",
        "AUTO_WITH_GUARDRAILS",
        "HUMAN_REQUIRED",
        "standingAuthorization",
        "waiting_for_media",
        "published_verified",
        "performance_learned",
    ))
    must_contain(VISUAL, (
        "brandScore",
        ">=80",
        "First-frame law",
        "Proof-first law",
        "Subject Lock",
        "Evaluation split",
        "Originality + fatigue guard",
    ))
    must_contain(EDIT, ("Edit Decision List", "shotRequest", "hard cut"))
    must_contain(MEDIA_DIRECTOR, ("Creative Director", "Edit Director", "Publishing Director", "standingAuthorization"))
    must_contain(MODULE, ("FOUNDRY.json", "CONTENT-CONTRACT.schema.json", "VISUAL-DNA.json", "Asset Truth", "Claim Provenance"))
    must_contain(CREW, ("waiting_for_media", "published_verified", "performance_learned", "Content Contract", "vfigos"))
    must_contain(SCENARIO, ("standing authorization", "auto-fix", "receipt + live evidence"))
    must_contain(GATE, ("authorized_for_tool_publish", "pending_human_approval", "published_verified", "human_marked"))
    must_contain(POLICY, ("Creative Autopilot", "standingAuthorization", "אין ריל כל יום", "posted_manually"))
    must_contain(SKILL, ("Velvet Visual Foundry", "Content Contract", "Asset Truth", "progressive variants", "published_verified"))
    must_contain(MEDIA_SKILL, ("Asset Truth", "Claim Truth", "CONTENT-CONTRACT.schema.json"))
    must_contain(CONTENT_GRAPH, ("Visual Foundry", "contracted", "visually_scored", "performance_learned", "Claim Provenance"))

    foundry = load_json(FOUNDRY)
    if foundry.get("name") != "velvet-visual-foundry" or foundry.get("noSecondRuntime") is not True:
        fail("FOUNDRY.json identity/noSecondRuntime contract invalid")

    layers = foundry.get("layers") or {}
    require_subset(set(layers), {"creativeIntelligence", "orchestration", "deterministicServices"}, "Foundry layers")

    states = set(foundry.get("stateMachine") or [])
    require_subset(states, {
        "discovered", "qualified", "contracted", "concepted", "storyboarded",
        "media_ready", "rough_generated", "visually_scored", "repaired", "rendered",
        "authorized_for_tool_publish", "published_verified", "performance_learned",
        "ready_for_publish", "waiting_for_media", "human_required", "archived",
    }, "Foundry states")

    truth = foundry.get("truth") or {}
    require_subset(set(truth.get("levels") or []), {
        "verified_real", "derived_real", "illustrative_ai", "synthetic", "unverified"
    }, "Foundry truth levels")
    if truth.get("defaultWhenMissing") != "unverified":
        fail("missing Asset Truth must default to unverified")

    variants = foundry.get("progressiveVariants") or {}
    if variants.get("enabled") is not True:
        fail("progressive variants must be enabled")
    if int(variants.get("maxFinalRenders", 99)) > 2:
        fail("default maxFinalRenders must remain <=2")
    if int(variants.get("maxRepairCycles", 0)) < 1:
        fail("repair loop must be bounded and non-zero")

    evaluation = foundry.get("evaluation") or {}
    require_subset(set(evaluation.get("perceptualRubrics") or []), {"brand", "hook", "reality", "originality"}, "perceptual rubrics")
    require_subset(set(evaluation.get("referenceChecks") or []), {"subject_fidelity", "material_fidelity", "geometry_invariants"}, "reference checks")

    learning = foundry.get("learning") or {}
    if "office-learning" not in str(learning.get("memoryAuthority", "")) or "vfinsights" not in str(learning.get("memoryAuthority", "")):
        fail("Foundry learning must reuse office-learning + vfinsights")
    exploration = learning.get("explorationPolicy") or {}
    total = sum(float(exploration.get(k, 0)) for k in ("exploit", "controlledVariation", "experimental"))
    if abs(total - 1.0) > 1e-9:
        fail("explorationPolicy weights must sum to 1")

    contract = load_json(CONTRACT)
    required_contract = set(contract.get("required") or [])
    require_subset(required_contract, {"jobId", "objective", "format", "truthClaims", "syntheticPolicy", "successDefinition"}, "Content Contract required fields")
    contract_props = contract.get("properties") or {}
    require_subset(set(contract_props), {"truthClaims", "syntheticPolicy", "subjectPack", "successDefinition", "novelty"}, "Content Contract properties")

    dna = load_json(DNA)
    if dna.get("brandName") != "Velvet Factory":
        fail("VISUAL-DNA brandName must be Velvet Factory")
    if dna.get("authority") != "packages/vfom/VISUAL-OS.md":
        fail("VISUAL-DNA must defer to VISUAL-OS authority")
    if dna.get("syntheticRole") is None:
        fail("VISUAL-DNA synthetic role missing")

    media_schema = load_json(MEDIA_SCHEMA)
    defs = media_schema.get("$defs") or {}
    asset_truth = defs.get("assetTruth") or {}
    truth_props = asset_truth.get("properties") or {}
    levels = set(((truth_props.get("truthLevel") or {}).get("enum") or []))
    require_subset(levels, {"verified_real", "derived_real", "illustrative_ai", "synthetic", "unverified"}, "vfmedia Asset Truth levels")
    media_item_props = ((defs.get("mediaItem") or {}).get("properties") or {})
    if "truth" not in media_item_props:
        fail("vfmedia mediaItem must expose optional truth metadata")

    instance = load_json(INSTANCE)
    autonomy = instance.get("creativeAutonomy") or {}
    publish = autonomy.get("publish") or {}
    if autonomy.get("enabled") is not True:
        fail("creativeAutonomy.enabled must be true for Velvet Factory")
    if autonomy.get("mode") != "exception-only":
        fail("creativeAutonomy.mode must be exception-only")
    if autonomy.get("ownerSurface") != "human_required_only":
        fail("creativeAutonomy.ownerSurface must be human_required_only")
    if autonomy.get("autoRepairQuality") is not True:
        fail("creativeAutonomy.autoRepairQuality must be true")
    expected_paths = {
        "visualAuthority": "packages/vfom/VISUAL-OS.md",
        "visualDNA": "packages/vfom/VISUAL-DNA.json",
        "orchestration": "packages/vfom/CREATIVE-AUTOPILOT.md",
        "foundryPolicy": "packages/vfom/FOUNDRY.json",
        "contentContractSchema": "packages/vfom/CONTENT-CONTRACT.schema.json",
        "mediaCatalog": "packages/vfmedia/catalog.json",
    }
    for key, expected in expected_paths.items():
        if autonomy.get(key) != expected:
            fail(f"creativeAutonomy.{key} must be {expected}")
    if autonomy.get("progressiveVariants") is not True or autonomy.get("noveltyFatigue") is not True:
        fail("Visual Foundry progressiveVariants and noveltyFatigue must be enabled")
    queue = autonomy.get("exceptionQueue") or {}
    if queue.get("low") != "auto_with_standing_authorization" or queue.get("high") != "human_required":
        fail("exceptionQueue LOW/HIGH policy invalid")

    if publish.get("standingAuthorization") is not True:
        fail("routine organic Instagram standingAuthorization must be true")
    for key in (
        "requirePreflight", "requireKnownRights", "requireContentContract",
        "requireSupportedClaims", "requireToolReceipt", "requireLiveVerification"
    ):
        if publish.get(key) is not True:
            fail(f"creativeAutonomy.publish.{key} must be true")
    if "organic-instagram-routine" not in (publish.get("scope") or []):
        fail("standing authorization scope must be organic-instagram-routine")

    human_required = set(autonomy.get("humanRequired") or [])
    required_human = {
        "physical-footage-or-staging",
        "rights-or-privacy-unclear",
        "unsupported-high-stakes-claim",
        "sale-ils-or-price-change",
        "purchase-or-spend",
        "boost-or-ads",
        "customer-whatsapp-send",
        "print-from-hq",
        "irreversible-destructive-action",
        "hard-blocker-after-failover",
    }
    require_subset(human_required, required_human, "creativeAutonomy humanRequired")

    mcp = instance.get("mcpBind") or {}
    ig = mcp.get("instagram") or {}
    wa = mcp.get("whatsapp") or {}
    if ig.get("publish") is not True or ig.get("dm") is not False:
        fail("Instagram must allow publish and keep DM disabled")
    if wa.get("send") is not False:
        fail("customer WhatsApp send must remain disabled")

    compliance = instance.get("compliance") or {}
    for key in ("noInventedPrices", "noInventedInsights", "noAutoDm", "noBoostWithoutLead"):
        if compliance.get(key) is not True:
            fail(f"compliance lock {key} must remain true")

    print("OK visual foundry exception-only truth-contract progressive-autonomy")


if __name__ == "__main__":
    main()
