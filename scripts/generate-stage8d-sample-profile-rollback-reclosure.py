#!/usr/bin/env python3
"""Generate Stage 8D sample-profile rollback re-closure evidence.

This is the authoritative re-closure after the hidden-consumer correction.
The earlier v1 closure remains historical and superseded for retirement.
No deletion is performed or authorized here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-sample-profile-rollback-reclosure.json"
CORRECTION = REPORTS / "stage8d-sample-profile-consumer-correction.json"
HISTORICAL_CLOSURE = REPORTS / "stage8d-sample-profile-rollback-closure.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL = "instances/velvet-factory/instance/velvet-factory.json"
CORRECTION_PR = 531
CORRECTION_MERGE_SHA = "30d72da6a257c2973d9d1b96e4caff0377135db3"

OBSERVATION_RUNS = [
    {"id": 37232107606, "sha": "44a2546a90a9b31051556cdc882842e471cd0eb1", "created_at": "2026-10-04T20:26:36Z", "conclusion": "success"},
    {"id": 37234390255, "sha": "a6f74bcd3fe9cd9b4c116df1dbc2a06b09519634", "created_at": "2026-10-04T21:01:38Z", "conclusion": "success"},
    {"id": 37261424137, "sha": "027700b3077bc900658313186e313772f539bd7d", "created_at": "2026-10-05T03:56:40Z", "conclusion": "success"},
    {"id": 37262173012, "sha": "ed183f59959b4eaebd5a092e61d4ef969e834df7", "created_at": "2026-10-05T04:07:50Z", "conclusion": "success"},
    {"id": 37263663917, "sha": "adf1b3195951ca00f0f1d976fa06523c7e90b069", "created_at": "2026-10-05T04:28:24Z", "conclusion": "success"},
    {"id": 37267662064, "sha": "b722f622dd2eab031c087fe051c56a5eb019d705", "created_at": "2026-10-05T05:24:39Z", "conclusion": "success"},
]


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    value = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    require(isinstance(value, dict), f"{rel}@{sha} must be a JSON object")
    return value


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        capture_output=True,
    ).returncode == 0


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_audit(source_commit: str, captured_at: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "semantic-audit.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(AUDIT_GENERATOR),
                "--source-commit", source_commit,
                "--captured-at", captured_at,
                "--output", str(out),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        require(proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip() or "semantic audit failed")
        value = json.loads(out.read_text(encoding="utf-8"))
        require(isinstance(value, dict), "semantic audit output must be an object")
        return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")
    require(args.prepared_against == OBSERVATION_RUNS[-1]["sha"],
            "re-closure must end at the latest recorded observation SHA")
    require(is_ancestor(CORRECTION_MERGE_SHA, args.prepared_against),
            "prepared-against main does not descend from the hidden-consumer correction")

    correction = git_json(args.prepared_against, CORRECTION.relative_to(ROOT).as_posix())
    historical = git_json(args.prepared_against, HISTORICAL_CLOSURE.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(correction.get("repository_assessment") == "PASS",
            "sample hidden-consumer correction must PASS")
    rollback_fix = correction.get("rollback_window") or {}
    require(
        rollback_fix.get("previous_closure_superseded_for_retirement") is True
        and rollback_fix.get("reopened") is True
        and rollback_fix.get("closed") is False
        and rollback_fix.get("closure_evidence") is None
        and rollback_fix.get("reclosure_requires_fresh_downstream_main_full_suite_observation") is True,
        "sample correction rollback state drift",
    )
    corrected = correction.get("correction") or {}
    require(corrected.get("hidden_consumer_migrated") is True, "hidden consumer migration drift")
    require(corrected.get("active_semantic_legacy_refs_after") == [], "sample active legacy refs reappeared")
    require(corrected.get("legacy_present_after_correction") is True, "legacy sample unexpectedly absent at correction")
    require(corrected.get("legacy_unchanged") is True, "correction did not preserve legacy sample")

    require(historical.get("rollback_window_closed") is True,
            "historical v1 closure must remain preserved as evidence")
    require(historical.get("delete_authorized") is False,
            "historical v1 closure unexpectedly authorizes deletion")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    sample_audit = surfaces.get("sample_profile") or {}
    assessment = audit.get("assessment") or {}
    require(sample_audit.get("retirement_preflight_clear") is True, "sample semantic preflight is not clear")
    require(sample_audit.get("retirement_preflight_blockers") == [], "sample semantic blockers remain")
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic preflight is not 5/5 clear",
    )

    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(CORRECTION_MERGE_SHA, LEGACY),
            "legacy sample changed after hidden-consumer correction")
    require(set(legacy.get("modulesEnabled") or []) == set(canonical.get("modulesEnabled") or []),
            "canonical and legacy module sets diverged")

    authority = correction.get("authority") or {}
    policy_sha = csha(policy)
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed since sample correction")
    require(authority.get("external_effect_authority_changed") is False,
            "sample correction authority state drift")

    require(len(OBSERVATION_RUNS) >= 5, "insufficient fresh downstream main observation coverage")
    require(len({row["sha"] for row in OBSERVATION_RUNS}) == len(OBSERVATION_RUNS),
            "observation SHAs must be distinct")
    require(all(row["conclusion"] == "success" for row in OBSERVATION_RUNS),
            "fresh downstream observation includes a non-success conclusion")
    require(all(is_ancestor(CORRECTION_MERGE_SHA, row["sha"]) for row in OBSERVATION_RUNS),
            "observation includes a pre-correction SHA")
    require(all(is_ancestor(OBSERVATION_RUNS[i]["sha"], OBSERVATION_RUNS[i + 1]["sha"])
                for i in range(len(OBSERVATION_RUNS) - 1)),
            "observation SHAs are not a monotonic main lineage")
    require(OBSERVATION_RUNS[-1]["sha"] == args.prepared_against,
            "latest observation does not match prepared-against main")

    criteria = {
        "historical_v1_closure_is_preserved_but_superseded": True,
        "hidden_consumer_correction_is_pass": True,
        "correction_reopened_the_rollback_window": True,
        "active_semantic_legacy_consumers_remain_zero": True,
        "sample_semantic_preflight_is_clear": True,
        "all_five_stage8d_semantic_preflights_are_clear": True,
        "legacy_sample_is_byte_unchanged_since_correction": True,
        "canonical_and_legacy_module_sets_match": True,
        "external_effect_authority_is_unchanged": True,
        "fresh_observation_window_contains_multiple_distinct_downstream_main_runs": True,
        "all_fresh_downstream_main_runs_are_successful": True,
        "all_observations_descend_from_the_hidden_consumer_correction": True,
        "latest_observation_matches_prepared_against_main": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_file_is_retained_after_reclosure": True,
        "deletion_requires_a_separate_isolated_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-rollback-reclosure.v2",
        "stage": "8D_SAMPLE_PROFILE_ROLLBACK_RECLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
        "path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Authoritatively re-close the sample_profile rollback observation window after the hidden-consumer "
            "correction, using fresh post-correction semantic and downstream-main evidence while retaining the "
            "compatibility file and keeping deletion unauthorized."
        ),
        "supersession": {
            "historical_closure_receipt": HISTORICAL_CLOSURE.relative_to(ROOT).as_posix(),
            "historical_closure_preserved": True,
            "historical_closure_superseded_for_current_retirement_authority": True,
            "correction_receipt": CORRECTION.relative_to(ROOT).as_posix(),
            "correction_pull_request": CORRECTION_PR,
            "correction_merge_sha": CORRECTION_MERGE_SHA,
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_semantic_legacy_consumer_count": 0,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "legacy_byte_unchanged_since_correction": True,
            "canonical_legacy_module_parity": True,
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "FRESH_POST_CORRECTION_DOWNSTREAM_MAIN_FULL_SUITE_AND_SEMANTIC_STABILITY",
            "elapsed_time_is_not_closure_authority": True,
            "start_after_merge_sha": CORRECTION_MERGE_SHA,
            "end_main_sha": args.prepared_against,
            "workflow": "VelvetOS Core Sensors",
            "main_push_run_count": len(OBSERVATION_RUNS),
            "success_count": len(OBSERVATION_RUNS),
            "failure_count": 0,
            "runs": OBSERVATION_RUNS,
            "all_descend_from_correction": True,
            "monotonic_main_lineage": True,
            "latest_main_full_suite_success": True,
        },
        "rollback_window": {
            "reopened_by_correction": True,
            "closure_evidence": "this_receipt",
            "closed": True,
            "closure_reason": (
                "The hidden consumer remains migrated, semantic preflight is clean, all five compatibility surfaces "
                "are semantically clear, the legacy sample is unchanged, canonical module parity and policy authority "
                "are preserved, and multiple distinct downstream main full-suite observations are green."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Run a separate isolated sample_profile deletion gate. Revalidate current semantic state, this re-closure "
            "receipt, latest main CI and external-effect authority before explicitly authorizing deletion."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha,
            "sample_correction_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "re-closure evidence does not itself authorize deletion",
            "legacy sample remains present in this change",
            "historical v1 closure remains preserved but superseded",
            "no big-bang delete",
            "retirement must be isolated to sample_profile",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "sample rollback re-closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_ROLLBACK_RECLOSURE "
        f"assessment={report['repository_assessment']} closed={report['rollback_window_closed']} "
        f"delete_authorized={report['delete_authorized']} runs={len(OBSERVATION_RUNS)} "
        f"all_surfaces_clear=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
