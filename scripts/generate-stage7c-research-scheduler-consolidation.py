#!/usr/bin/env python3
"""Generate Reform v2 Stage 7C Research/Scheduler consolidation acceptance evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "velvetos" / "policy"
MODEL = POLICY / "research-scheduler-consolidation.json"
POLICY_REGISTRY = POLICY / "policy-registry.json"
MANIFEST = ROOT / "automation" / "grok" / "manifest.json"
DAILY = ROOT / "packages" / "vfresearch" / "DAILY.md"
ARTIFACT_CONTRACT = ROOT / "packages" / "vfresearch" / "ARTIFACT-CONTRACT.md"
CADENCE = ROOT / "scripts" / "vfresearch_cadence.py"
WATCH = ROOT / "packages" / "vfresearch" / "sources" / "upstream-watch-latest.json"
REVIEW = ROOT / "packages" / "vfresearch" / "sources" / "upstream-review-latest.json"
WORKFLOWS = ROOT / ".github" / "workflows"
OUT = POLICY / "reports" / "stage7c-research-scheduler-consolidation.json"
STAGE7C_WITNESS_SHA = "99074637d96c6b6211ed781bb7ced67a9370e040"

META_KEYS = {"asOf", "provenance", "uncertainty", "refreshTarget"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def scheduled_workflows(historical_sha: str | None = None) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    if historical_sha:
        names = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", historical_sha, ".github/workflows"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        for rel in sorted(name for name in names if name.endswith(".yml")):
            text = git_show(historical_sha, rel).decode("utf-8")
            crons = re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", text)
            if crons:
                found[Path(rel).name] = crons
        return found
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        crons = re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", text)
        if crons:
            found[path.name] = crons
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument(
        "--provider-readback-artifact",
        help="Stable provider-readback witness for historical receipt replay; defaults to the current manifest pointer for a new capture.",
    )
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    require(len(args.prepared_against) == 40, "--prepared-against must be a full Git SHA")

    # Stage 7C scheduler ownership is historical after the 2026-10-06 ChatGPT cutover.
    # Replay pinned evidence from the original prepared-against SHA; never force the
    # current scheduler manifest/model to pretend Grok is still owner-facing authority.
    if args.provider_readback_artifact:
        model = load(MODEL)
        historical_model = dict(model)
        historical_model.pop("current_authority_override", None)
        model_bytes = (json.dumps(historical_model, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        model = historical_model
        manifest = json.loads(git_show(args.prepared_against, "automation/grok/manifest.json").decode("utf-8-sig"))
    else:
        model_bytes = MODEL.read_bytes()
        model = load(MODEL)
        manifest = load(MANIFEST)
        require(manifest.get("productionScheduler") == "grok-bot-routines",
                "Stage 7C is historical after scheduler cutover; use a pinned provider readback for replay")
    watch = load(WATCH)
    review = load(REVIEW)
    policies = load(POLICY_REGISTRY)

    require(
        model.get("schema_version") == 1
        and model.get("registry_kind") == "velvetos_research_scheduler_consolidation"
        and model.get("status") == "ACTIVE_STAGE7C",
        "Stage 7C model identity drift",
    )

    router = model.get("research_router") or {}
    require(router.get("seat_id") == "velvet-research-seat", "Research Router must use existing Research Seat")
    require(router.get("clock_authority") == "grok-bot-routines", "Research Seat clock authority drift")
    require(router.get("existing_seat_only") is True, "Stage 7C may not create a new research seat")
    require(router.get("no_new_daemon") is True and router.get("no_new_scheduler") is True,
            "Stage 7C may not add a research daemon/scheduler")
    deep = router.get("deep_review") or {}
    require(deep.get("reuse_current_review_when_exact_binding_matches") is True,
            "current exact upstream reviews must be reusable")
    require(set(deep.get("binding_fields") or []) == {"reviewedRemoteHead", "reviewedRelease"},
            "deep-review binding fields drift")

    scheduler = model.get("scheduler_authority") or {}
    require(manifest.get("productionScheduler") == scheduler.get("owner_facing_primary") == "grok-bot-routines",
            "owner-facing primary scheduler drift")
    require(manifest.get("provider") == scheduler.get("provider") == "grok-bot",
            "scheduler provider drift")
    require(manifest.get("timezone") == scheduler.get("timezone") == "Asia/Jerusalem",
            "scheduler timezone drift")
    require(scheduler.get("provider_readback_role") == "EVIDENCE_ONLY_NOT_POLICY",
            "provider readback must remain evidence, not policy")
    require(scheduler.get("previous_schedulers") == manifest.get("previousSchedulers"),
            "retired scheduler state differs from live manifest")

    manifest_rows = manifest.get("routines") or []
    manifest_by_id = {row["id"]: row for row in manifest_rows if isinstance(row, dict) and row.get("id")}
    protected = model.get("protected_routines") or []
    protected_ids = [row.get("id") for row in protected if isinstance(row, dict)]
    require(len(protected_ids) == len(set(protected_ids)) == 9, "Stage 7C must map exactly nine protected routines")
    require(set(protected_ids) == set(manifest_by_id), "Stage 7C protected routine map differs from manifest")
    require(all(row.get("primary_scheduler") == "grok-bot-routines" for row in protected),
            "every protected routine must have Grok as its primary clock")
    require(all(row.get("fallback") and row.get("fallback_is_active_duplicate_clock") is False for row in protected),
            "every protected routine needs an explicit non-duplicate fallback")

    latest = manifest.get("latestProviderReadback") or {}
    if args.provider_readback_artifact:
        artifact_rel = args.provider_readback_artifact
    else:
        artifact_rel = latest.get("artifact")
        require(latest.get("status") == "live_verified" and isinstance(artifact_rel, str),
                "latest provider readback is not live verified")
    require(isinstance(artifact_rel, str) and bool(artifact_rel), "provider readback artifact is required")
    artifact_path = ROOT / artifact_rel
    require(artifact_path.is_file(), f"provider readback artifact missing: {artifact_rel}")
    readback = load(artifact_path)
    observed_rows = readback.get("protectedRoutines") or []
    observed_ids = {row.get("providerRoutineId") for row in observed_rows if isinstance(row, dict)}
    require(readback.get("protectedRoutineCount") == 9 and observed_ids == set(protected_ids),
            "live provider readback does not prove the nine protected routines")
    require(all(row.get("enabled") is True and row.get("matchesCanonicalClock") is True for row in observed_rows),
            "live protected routine clock/enabled state drift")

    historical_replay = bool(args.provider_readback_artifact)
    workflows = scheduled_workflows(args.prepared_against if historical_replay else None)
    machine = model.get("machine_workflows") or []
    machine_by_id = {row.get("id"): row for row in machine if isinstance(row, dict)}
    require(set(machine_by_id) == set(workflows), "scheduled GitHub workflow inventory drift")
    allowed_workflow_roles = {
        "MACHINE_EXECUTION_OR_VERIFIER_NOT_OWNER_CLOCK",
        "RESEARCH_FRESHNESS_INDEX_VERIFIER_NOT_BODY_CLOCK",
    }
    require(all(row.get("role") in allowed_workflow_roles for row in machine),
            "GitHub workflow role must explicitly deny owner-clock/body-clock authority")
    if historical_replay:
        research_workflow = git_show(STAGE7C_WITNESS_SHA, ".github/workflows/velvetos-research.yml").decode("utf-8")
        cadence_text = git_show(STAGE7C_WITNESS_SHA, "scripts/vfresearch_cadence.py").decode("utf-8")
        daily = git_show(STAGE7C_WITNESS_SHA, "packages/vfresearch/DAILY.md").decode("utf-8")
    else:
        research_workflow = (WORKFLOWS / "velvetos-research.yml").read_text(encoding="utf-8")
        cadence_text = CADENCE.read_text(encoding="utf-8")
        daily = DAILY.read_text(encoding="utf-8")
    require("actual research body is produced by the owner-facing Velvet Research Seat" in research_workflow
            and "verifies" in research_workflow
            and "freshness" in research_workflow,
            "historical velvetos-research workflow must remain verifier/index, not research-body clock")

    require("protected Grok Bot routine velvet-research-seat" in cadence_text,
            "Stage 7C cadence witness drift")
    require("review-routing" in cadence_text and "reuse_current_review" in cadence_text,
            "signal-driven deep-review routing missing")
    proc = subprocess.run(
        [__import__("sys").executable, str(CADENCE), "routing-selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    require(proc.returncode == 0 and "OK research-review-routing" in (proc.stdout or ""),
            "research review-routing selftest failed")
    routing_proc = subprocess.run(
        [__import__("sys").executable, str(CADENCE), "review-routing"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    require(routing_proc.returncode == 0, "research review-routing command failed")
    routed = json.loads(routing_proc.stdout)
    require(routed.get("cheapDetectionFirst") is True, "cheap detection must precede deep review")
    require(routed.get("pending") == routed.get("deepReviewRequired") + routed.get("reusableCurrentReview"),
            "review routing does not partition pending updates")

    require("vfresearch_cadence.py review-routing" in daily
            and "Pending ישן" in daily
            and "ARTIFACT-CONTRACT.md" in daily,
            "historical DAILY.md does not enforce Stage 7C routing/artifact contract")
    contract = ARTIFACT_CONTRACT.read_text(encoding="utf-8")
    for marker in ("as_of", "provenance", "uncertainty", "refresh_target"):
        require(marker in contract, f"research artifact contract missing {marker}")
    for payload, label in ((watch, "upstream-watch-latest"), (review, "upstream-review-latest")):
        meta = payload.get("artifactMeta") or {}
        require(META_KEYS <= set(meta), f"{label} missing Stage 7C artifact metadata")

    invariants = model.get("invariants") or {}
    required_invariants = {
        "one_clock_owner_per_protected_routine",
        "fallbacks_are_not_active_duplicate_clocks",
        "provider_readback_proves_state_not_policy",
        "github_schedules_do_not_override_owner_facing_clock_authority",
        "cheap_detection_precedes_deep_review",
        "unchanged_current_review_is_reused",
        "no_auto_upgrade",
        "no_new_research_daemon",
        "no_new_scheduler",
        "no_new_recurring_cost",
    }
    require(all(invariants.get(key) is True for key in required_invariants), "Stage 7C invariant drift")
    require(invariants.get("external_effect_authority_change") is False,
            "Stage 7C must not change external-effect authority")

    current_policy = POLICY_REGISTRY.read_bytes()
    baseline_policy = git_show(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    require(current_policy == baseline_policy, "Stage 7C changed policy-registry authority")
    require((policies.get("external_effect_contract") or {}).get("single_authority_per_effect") is True,
            "single external-effect authority invariant drift")

    criteria = {
        "research_router_reuses_existing_research_seat": True,
        "cheap_detection_precedes_signal_driven_deep_review": routed.get("cheapDetectionFirst") is True,
        "current_bound_reviews_are_reused": routed.get("reusableCurrentReview", 0) >= 0,
        "all_protected_routines_have_one_primary_clock_owner": len(protected_ids) == 9,
        "fallbacks_are_explicit_and_not_duplicate_recurring_clocks": all(
            row.get("fallback_is_active_duplicate_clock") is False for row in protected
        ),
        "github_schedules_are_execution_or_verification_not_owner_clock": set(machine_by_id) == set(workflows),
        "live_provider_readback_proves_nine_of_nine": len(observed_ids) == 9,
        "provider_readback_remains_evidence_not_policy": scheduler.get("provider_readback_role") == "EVIDENCE_ONLY_NOT_POLICY",
        "research_artifact_truth_metadata_is_required": all(
            key in ARTIFACT_CONTRACT.read_text(encoding="utf-8") for key in ("as_of", "provenance", "uncertainty", "refresh_target")
        ),
        "no_new_daemon_scheduler_cost_or_auto_upgrade": (
            router.get("no_new_daemon") is True
            and router.get("no_new_scheduler") is True
            and invariants.get("no_new_recurring_cost") is True
            and invariants.get("no_auto_upgrade") is True
        ),
        "external_effect_policy_registry_is_unchanged": current_policy == baseline_policy,
    }

    report = {
        "schema": "velvetos.stage7c-research-scheduler-consolidation.v1",
        "stage": "7C",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Consolidate Research Router and scheduler ownership without adding a daemon, scheduler, or policy authority.",
        "model": {
            "path": MODEL.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(model_bytes).hexdigest(),
            "protected_routine_count": len(protected_ids),
            "scheduled_github_workflow_count": len(workflows),
        },
        "live_scheduler_evidence": {
            "provider": manifest.get("provider"),
            "primary": manifest.get("productionScheduler"),
            "timezone": manifest.get("timezone"),
            "provider_readback": artifact_rel,
            "provider_readback_sha256": sha256(ROOT / artifact_rel),
            "protected_routines_verified": len(observed_ids),
        },
        "research_routing": {
            "pending": routed.get("pending"),
            "deep_review_required": routed.get("deepReviewRequired"),
            "reusable_current_review": routed.get("reusableCurrentReview"),
            "cheap_detection_first": routed.get("cheapDetectionFirst"),
        },
        "artifact_contract": {
            "path": ARTIFACT_CONTRACT.relative_to(ROOT).as_posix(),
            "required_metadata": ["as_of", "provenance", "uncertainty", "refresh_target"],
            "historical_rewrite_required": False,
        },
        "authority_baseline": {
            "policy_registry_sha256": sha256(POLICY_REGISTRY),
            "unchanged_from_prepared_against": current_policy == baseline_policy,
        },
        "acceptance": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 7D — Artifact retention" if all(criteria.values()) else None,
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE7C_RESEARCH_SCHEDULER "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(1 for value in criteria.values() if value)}/{len(criteria)} "
        f"protected={len(protected_ids)} live={len(observed_ids)} "
        f"deep={routed.get('deepReviewRequired')} reuse={routed.get('reusableCurrentReview')}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
