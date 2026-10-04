#!/usr/bin/env python3
"""Generate Reform v2 Stage 6B creative-readiness acceptance evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VFOM = ROOT / "packages" / "vfom"
FOUNDRY = VFOM / "FOUNDRY.json"
MANIFEST = VFOM / "CREATIVE-MANIFEST.schema.json"
AUTOPILOT = VFOM / "CREATIVE-AUTOPILOT.md"
REFINE = VFOM / "CREATIVE-REFINE-LOOP.md"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
STAGE6A = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6a-visible-text-tiers.json"
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6b-creative-readiness.json"

SPECIALISTS = [
    ".cursor/skills/vf-cad-design-craft/SKILL.md",
    ".cursor/skills/vf-dcc-modeling-craft/SKILL.md",
    ".cursor/skills/vf-material-lookdev/SKILL.md",
    ".cursor/skills/vf-product-visualization-craft/SKILL.md",
    ".cursor/skills/vf-post-production-craft/SKILL.md",
    ".cursor/skills/vf-vfx-compositing-craft/SKILL.md",
    ".cursor/skills/vf-image-design-craft/SKILL.md",
    ".cursor/skills/vf-technical-illustration-craft/SKILL.md",
]


def git_text(ref: str, rel: str) -> str:
    p = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
    )
    if p.returncode != 0:
        raise SystemExit(f"cannot read {rel} at {ref}: {p.stderr.strip()}")
    return p.stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json_text(text: str, label: str) -> dict[str, Any]:
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if len(args.prepared_against) != 40:
        ap.error("--prepared-against must be a full Git SHA")

    stage6a = json.loads(STAGE6A.read_text(encoding="utf-8"))
    if stage6a.get("repository_acceptance") != "PASS":
        raise SystemExit("Stage 6A must be PASS before Stage 6B")

    before_foundry_text = git_text(args.prepared_against, "packages/vfom/FOUNDRY.json")
    before_manifest_text = git_text(args.prepared_against, "packages/vfom/CREATIVE-MANIFEST.schema.json")
    before_policy = git_text(args.prepared_against, "packages/velvetos/policy/policy-registry.json").encode("utf-8")
    before_foundry = load_json_text(before_foundry_text, "pre-6B FOUNDRY")
    before_manifest = load_json_text(before_manifest_text, "pre-6B manifest")
    after_foundry = json.loads(FOUNDRY.read_text(encoding="utf-8"))
    after_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current_policy = POLICY.read_bytes()

    bf_manifest = before_foundry.get("creativeManifest") or {}
    af_manifest = after_foundry.get("creativeManifest") or {}
    bf_human = before_foundry.get("humanSurface") or {}
    af_human = after_foundry.get("humanSurface") or {}
    standing = after_foundry.get("ownerApprovedVisualStandard") or {}
    quality = after_foundry.get("creativeQualitySystem") or {}

    before_boundary_flags = {
        key: bf_manifest.get(key)
        for key in (
            "coordinationOnly",
            "notApprovalDatabase",
            "cannotAuthorizeExternalEffects",
            "statusIsEvidenceProjection",
            "productTruthAuthorityHigher",
            "policyDecisionSource",
        )
    }
    before_quality_exists = isinstance(before_foundry.get("creativeQualitySystem"), dict)

    required_manifest_flags = {
        "coordinationOnly": True,
        "notASecondStateMachine": True,
        "notAMediaCatalog": True,
        "notAClaimAuthority": True,
        "notApprovalDatabase": True,
        "cannotAuthorizeExternalEffects": True,
        "statusIsEvidenceProjection": True,
        "productTruthAuthorityHigher": True,
    }
    manifest_boundary_pass = all(af_manifest.get(k) == v for k, v in required_manifest_flags.items())
    manifest_boundary_pass = manifest_boundary_pass and (
        af_manifest.get("policyDecisionSource") == "packages/velvetos/policy/policy-registry.json"
        and "never creates that state" in str(af_manifest.get("rule", ""))
    )

    schema_desc = str(after_manifest.get("description", ""))
    status_desc = str(((after_manifest.get("properties") or {}).get("status") or {}).get("description", ""))
    visual_desc = str(((after_manifest.get("properties") or {}).get("visualStandard") or {}).get("description", ""))
    schema_boundary_pass = (
        "not an approval database" in schema_desc
        and "Product Truth" in schema_desc
        and "never authorizes or proves an external effect" in status_desc
        and "not a request for per-job owner approval" in visual_desc
    )

    quality_pass = (
        quality.get("enabled") is True
        and quality.get("version") == "2.0.0"
        and quality.get("role") == "authoring_and_quality_system_not_policy_hierarchy"
        and quality.get("router") == "packages/vfharness/devtools/creative-craft/skill/SKILL.md"
        and quality.get("registry") == "packages/vfharness/devtools/creative-craft/creative-craft-registry.json"
        and quality.get("specialists") == SPECIALISTS
        and quality.get("produceCritiqueTargetedRefine") == "internal"
        and quality.get("ordinaryAestheticChoice") == "office"
        and quality.get("qualityFailure") == "targeted_auto_repair_first"
        and quality.get("ownerEscalation") == "exception-only"
        and quality.get("mayAuthorizeExternalEffects") is False
        and quality.get("mayOverrideProductTruth") is False
        and quality.get("mayCreatePolicyHierarchy") is False
        and quality.get("manifestWritesAreEvidenceOnly") is True
        and quality.get("productTruthAuthority") == "higher_than_aesthetic_and_quality_system"
        and quality.get("completionRequiresExactFinalQa") is True
    )

    standing_pass = (
        standing.get("required") is True
        and standing.get("approvalScope") == "standing_visual_standard_not_per_job_owner_approval"
        and standing.get("perJobOwnerApprovalRequired") is False
    )

    human_required_before = bf_human.get("humanRequired") or []
    human_required_after = af_human.get("humanRequired") or []
    human_surface_pass = (
        af_human.get("mode") == "exception-only"
        and af_human.get("creativeQualityFailure") == "auto-repair"
        and af_human.get("routineCreativeChoice") == "office"
        and af_human.get("ordinaryAestheticChoice") == "office"
        and af_human.get("ownerApprovalForAestheticChoice") is False
        and af_human.get("ownerApprovalForRoutineQualityRepair") is False
        and human_required_after == human_required_before
    )

    autopilot = AUTOPILOT.read_text(encoding="utf-8")
    refine = REFINE.read_text(encoding="utf-8")
    prose_boundary_pass = all(
        marker in autopilot
        for marker in (
            "policy_id: instagram.publish",
            "Creative Manifest = coordination artifact, not approval database",
            "Creative Craft 2.0 = authoring + quality system, not policy hierarchy",
            "Produce → Critique → Targeted Refine",
            "standing standard",
        )
    ) and all(
        marker in refine
        for marker in (
            "policy_id: instagram.publish",
            "not an approval database",
            "authoring/quality system",
            "Product Truth is higher authority",
            "produce → critique → targeted refine",
        )
    )

    policy_unchanged = sha(before_policy) == sha(current_policy)

    acceptance = {
        "creative_manifest_is_coordination_not_approval_database": manifest_boundary_pass and schema_boundary_pass,
        "manifest_status_cannot_mint_external_authorization": (
            af_manifest.get("cannotAuthorizeExternalEffects") is True
            and af_manifest.get("statusIsEvidenceProjection") is True
            and "never authorizes or proves an external effect" in status_desc
        ),
        "product_truth_remains_higher_authority": (
            af_manifest.get("productTruthAuthorityHigher") is True
            and quality.get("mayOverrideProductTruth") is False
            and quality.get("productTruthAuthority") == "higher_than_aesthetic_and_quality_system"
        ),
        "owner_approved_visual_standard_is_standing_not_per_job_approval": standing_pass,
        "creative_craft_is_quality_system_not_policy_hierarchy": quality_pass,
        "produce_critique_targeted_refine_is_internal": (
            quality.get("produceCritiqueTargetedRefine") == "internal"
            and "produce → critique → targeted refine" in refine
        ),
        "ordinary_aesthetic_choices_and_repairs_do_not_ping_owner": human_surface_pass,
        "exception_only_owner_surface_preserved_exactly": human_required_after == human_required_before,
        "creative_authority_boundary_documented": prose_boundary_pass,
        "external_effect_policy_registry_unchanged": policy_unchanged,
    }

    report = {
        "schema": "velvetos.stage6b-creative-readiness.v1",
        "stage": "6B",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "stage6a_entry": {
            "receipt": "packages/velvetos/policy/reports/stage6a-visible-text-tiers.json",
            "acceptance": stage6a.get("repository_acceptance"),
        },
        "before": {
            "foundry_sha256": sha(before_foundry_text.encode("utf-8")),
            "manifest_schema_sha256": sha(before_manifest_text.encode("utf-8")),
            "creative_manifest_existing_safety": {
                "notASecondStateMachine": bf_manifest.get("notASecondStateMachine"),
                "notAMediaCatalog": bf_manifest.get("notAMediaCatalog"),
                "notAClaimAuthority": bf_manifest.get("notAClaimAuthority"),
            },
            "missing_explicit_manifest_boundary_fields": before_boundary_flags,
            "creative_quality_system_machine_contract_present": before_quality_exists,
            "human_surface": {
                "mode": bf_human.get("mode"),
                "creativeQualityFailure": bf_human.get("creativeQualityFailure"),
                "routineCreativeChoice": bf_human.get("routineCreativeChoice"),
                "humanRequired": human_required_before,
            },
        },
        "after": {
            "foundry_sha256": sha(FOUNDRY.read_bytes()),
            "manifest_schema_sha256": sha(MANIFEST.read_bytes()),
            "creative_manifest": af_manifest,
            "creative_quality_system": quality,
            "standing_visual_standard": {
                "approvalScope": standing.get("approvalScope"),
                "perJobOwnerApprovalRequired": standing.get("perJobOwnerApprovalRequired"),
            },
            "human_surface": {
                "mode": af_human.get("mode"),
                "creativeQualityFailure": af_human.get("creativeQualityFailure"),
                "routineCreativeChoice": af_human.get("routineCreativeChoice"),
                "ordinaryAestheticChoice": af_human.get("ordinaryAestheticChoice"),
                "ownerApprovalForAestheticChoice": af_human.get("ownerApprovalForAestheticChoice"),
                "ownerApprovalForRoutineQualityRepair": af_human.get("ownerApprovalForRoutineQualityRepair"),
                "humanRequired": human_required_after,
            },
        },
        "authorization_semantics": {
            "entry_policy_registry_sha256": sha(before_policy),
            "current_policy_registry_sha256": sha(current_policy),
            "external_effect_policy_registry_unchanged": policy_unchanged,
            "creative_manifest_is_policy_authority": False,
            "creative_craft_is_policy_authority": False,
        },
        "acceptance": acceptance,
        "repository_acceptance": "PASS" if all(acceptance.values()) else "FAIL",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE6B_CREATIVE_READINESS "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(1 for v in acceptance.values() if v)}/{len(acceptance)} "
        f"specialists={len(SPECIALISTS)} "
        f"exceptions_preserved={human_required_after == human_required_before} "
        f"policy_unchanged={policy_unchanged}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
