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
AUTOPILOT = ROOT / "packages" / "vfom" / "CREATIVE-AUTOPILOT.md"


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



def check_business_release_acceptance(policy: dict) -> None:
    """Pin a future PRODUCT readiness gate, not another per-post publish gate.

    This is a static contract check only. It cannot claim a live E2E pass.
    The later release evaluator must independently verify live evidence.
    """
    gate = policy.get("businessReleaseAcceptance")
    if not isinstance(gate, dict):
        fail("missing businessReleaseAcceptance gate")
    exact = {
        "id": "VF_INSTAGRAM_BUSINESS_E2E",
        "version": 1,
        "scope": "velvet-factory-instagram-autonomy-product-readiness",
        "kind": "business_release_acceptance_not_per_content_publish_gate",
        "statusWithoutVerifiedLiveProof": "PENDING_LIVE_E2E",
        "canonicalPublishPolicyId": "instagram.publish",
    }
    for key, value in exact.items():
        if gate.get(key) != value:
            fail(f"businessReleaseAcceptance.{key} drift")

    for key in (
        "historicalReformV2TechnicalClosureUnaffected",
        "doNotBlockAlreadyAuthorizedRoutinePublishing",
        "noSecondPublishAuthority",
        "noSecondSchedulerOrStateStore",
    ):
        if gate.get(key) is not True:
            fail(f"businessReleaseAcceptance.{key} must remain true")
    claims = set(gate.get("releaseClaimsBlockedUntilPass") or [])
    if not {
        "instagram_autonomy_business_ready",
        "unattended_instagram_autopilot_production_ready",
    }.issubset(claims):
        fail("business release claims must remain blocked pending real proof")

    intents = gate.get("intentBoundary") or {}
    if (
        intents.get("prepare") != "prepare_and_verify_exact_media_and_copy_without_publishing"
        or intents.get("publish") != "publish_only_for_explicit_publish_intent_with_canonical_policy_ALLOW"
        or intents.get("autopilot") != "publish_only_from_explicitly_enrolled_autopilot_queue_with_canonical_policy_ALLOW"
    ):
        fail("prepare, explicit publish and enrolled-autopilot intent boundaries must remain distinct")

    happy = gate.get("routineHappyPath") or {}
    if happy.get("exampleRequest") != "תכין ותפרסם את התמונות האלה":
        fail("business release scenario must be the real user request")
    if happy.get("maxOwnerPromptsForKnownLowRisk") != 0 or happy.get("maxPerAssetOwnerApprovalsWithStandingAuthorization") != 0:
        fail("routine LOW-risk business release requires zero owner prompts/per-item approvals")
    if happy.get("noDuplicateOrUnauthorizedPublishes") is not True or happy.get("successfulEndState") != "published_verified":
        fail("business release must require exactly-authorized, live-verified publishing")
    steps = set(happy.get("requiredSteps") or [])
    if not {
        "user_source_asset_ingest_and_identity",
        "verified_product_truth_and_rights",
        "editorial_selection_and_actual_visual_edit",
        "independent_visual_and_copy_qa_with_bounded_targeted_repair",
        "exact_final_media_caption_and_CONTENT_READY",
        "one_canonical_instagram_publish_policy_ALLOW",
        "connected_tool_publish_with_provider_receipt",
        "independent_live_meta_readback_and_permalink",
        "existing_media_publication_state_closeout",
    }.issubset(steps):
        fail("business happy path omitted required actual end-to-end step")

    negative = set(gate.get("requiredNegativeControls") or [])
    if not {
        "prepare_intent_never_publishes",
        "missing_truth_or_unclear_rights_blocks_publish",
        "unverified_claim_or_price_does_not_silently_pass",
        "forbidden_dm_boost_and_spend_stay_denied",
        "ambiguous_provider_write_requires_reconciliation_not_blind_retry",
        "tool_outage_without_safe_fallback_does_not_claim_success",
        "duplicate_request_does_not_create_second_live_post",
        "unknown_or_high_risk_requires_real_owner_decision",
    }.issubset(negative):
        fail("business release negative controls incomplete")

    evidence = set(gate.get("releaseEvidenceRequired") or [])
    if not {
        "real_user_initiated_end_to_end_trace",
        "source_asset_and_exact_final_artifact_hashes",
        "actual_visual_edit_output_and_qa_repair_receipts",
        "exact_bound_CONTENT_READY",
        "canonical_instagram_publish_decision_receipt",
        "provider_media_id_and_publish_receipt",
        "independent_live_media_readback_with_permalink",
        "owner_prompt_and_per_asset_approval_counts",
        "negative_control_and_reconciliation_results",
        "bounded_repeatability_observation",
    }.issubset(evidence):
        fail("business release evidence requirement incomplete")

    decision = gate.get("releaseDecision") or {}
    if (
        decision.get("unverified") != "BLOCK_RELEASE_CLAIM"
        or decision.get("success") != "PASS_ONLY_WITH_INDEPENDENT_LIVE_EVIDENCE"
    ):
        fail("unverified Instagram business acceptance must block release claims")
    if decision.get("simulatedOrCiOnlyProofSufficient") is not False:
        fail("CI-only/static tests cannot satisfy business release acceptance")
    for key in (
        "capabilityScopedClaimsOnly",
        "doNotManufacturePublicPostsForTestCoverage",
        "noLiveE2ETestIsScheduledByThisContract",
    ):
        if decision.get(key) is not True:
            fail(f"businessReleaseAcceptance.releaseDecision.{key} must remain true")

def main() -> None:
    policy = load(POLICY)
    if policy.get("name") != "instagram-content-decision-pipeline" or policy.get("noSecondRuntime") is not True:
        fail("policy identity/noSecondRuntime invalid")

    check_business_release_acceptance(policy)

    required_order = [
        "content_matrix",
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

    matrix = stages["content_matrix"]
    if matrix.get("enabled") is not True or matrix.get("noPublishAuthority") is not True:
        fail("content matrix must be enabled and non-publishing")
    if set(matrix.get("formats") or []) != {"actionable", "motivational", "analytical", "contrarian", "observation", "x_vs_y", "present_vs_future", "listicle"}:
        fail("content matrix angle families incomplete")

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

    must_contain(SKILL, ("content_matrix", "saturation_scan", "anti_generic_check", "hook_tournament", "retention_pass", "authority_voice_pass", "engagement_pass", "visual_qa", "final_quality_gate", "performance_feedback"))
    must_contain(CREW, ("content_matrix", "saturation_scan", "hook_tournament", "engagementBait=false", "final_quality_gate", "performance_feedback"))
    must_contain(SCENARIO, ("content matrix", "saturation scan", "hook tournament", "Visual QA", "final quality gate", "performance feedback"))
    must_contain(AUTOPILOT, ("VF_INSTAGRAM_BUSINESS_E2E", "business release", "policy_id: instagram.publish"))

    print("OK instagram content decision pipeline enforced")


if __name__ == "__main__":
    main()
