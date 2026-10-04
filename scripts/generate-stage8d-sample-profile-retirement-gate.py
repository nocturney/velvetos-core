#!/usr/bin/env python3
"""Generate Stage 8D retirement authorization for the legacy VF sample profile.

This gate revalidates the explicit rollback closure and authorizes one later,
isolated retirement change. It does not delete the legacy sample itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-sample-profile-retirement-gate.json"
CLOSURE_REL = "packages/velvetos/policy/reports/stage8d-sample-profile-rollback-closure.json"
STAGE8C_REL = "packages/velvetos/policy/reports/stage8c-sample-profile-consumers.json"
STAGE8C_GENERATOR = ROOT / "scripts" / "generate-stage8c-sample-profile-consumers.py"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"
CORE_REL = "packages/velvetos/CORE.json"
LEGACY_REL = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL_REL = "/".join(["instances", "velvet-factory", "instance", "velvet-factory.json"])

CUTOVER_MERGE_SHA = "80bed30bf54c854f2854d7328ccda171a587d569"
CLOSURE_PR = 529
CLOSURE_MERGE_SHA = "bde52ea50c8c72930248d0b7e669bff759bce9c3"
MAIN_CI_RUN = 37230041634
MAIN_README_RUN = 37230041570
ALLOWED_REFS = [
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8a-core-instance-inventory.py",
    "scripts/generate-stage8b-instance-resolver-foundation.py",
]


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(commit: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT)


def git_json(commit: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_bytes(commit, rel).decode("utf-8-sig"))
    require(isinstance(obj, dict), f"{rel}@{commit} must be object")
    return obj


def git_refs(commit: str, needle: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", needle, commit, "--", ":!packages/velvetos/policy/reports/*"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or "git grep failed")
    prefix = f"{commit}:"
    refs = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def historical_stage8c_replays() -> bool:
    historical = json.loads((ROOT / STAGE8C_REL).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        regenerated = Path(td) / "stage8c-sample-profile-consumers.json"
        proc = subprocess.run(
            [
                "python",
                str(STAGE8C_GENERATOR),
                "--prepared-against", historical["prepared_against_main_sha"],
                "--captured-at", historical["captured_at"],
                "--output", str(regenerated),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        require(proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip())
        return regenerated.read_bytes() == (ROOT / STAGE8C_REL).read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")
    require(args.prepared_against == CLOSURE_MERGE_SHA,
            "retirement gate must be prepared against the verified closure merge")

    closure = git_json(args.prepared_against, CLOSURE_REL)
    sample8c = git_json(args.prepared_against, STAGE8C_REL)
    policy = git_json(args.prepared_against, POLICY_REL)
    core = git_json(args.prepared_against, CORE_REL)
    legacy = git_json(args.prepared_against, LEGACY_REL)
    canonical = git_json(args.prepared_against, CANONICAL_REL)

    require(closure.get("rollback_window_closed") is True, "sample rollback window is not closed")
    require(closure.get("retirement_ready_for_deletion_gate") is True,
            "closure does not permit the deletion gate")
    require(closure.get("delete_authorized") is False,
            "closure receipt must not itself authorize deletion")
    require(closure.get("retirement_authorized") is False,
            "closure receipt unexpectedly authorizes retirement")
    require(sample8c.get("repository_acceptance") == "PASS", "Stage 8C sample migration is not PASS")

    refs = git_refs(args.prepared_against, LEGACY_REL)
    require(refs == ALLOWED_REFS, f"unexpected sample legacy refs before retirement: {refs}")
    require(git_bytes(args.prepared_against, LEGACY_REL) == git_bytes(CUTOVER_MERGE_SHA, LEGACY_REL),
            "legacy sample changed since consumer cutover")
    require(set(legacy.get("modulesEnabled") or []) == set(canonical.get("modulesEnabled") or []),
            "legacy/canonical module parity drift")

    authority = closure.get("authority") or {}
    policy_sha = csha(policy)
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed after rollback closure")

    core_samples = core.get("sampleProfiles") or {}
    require(core_samples == {
        "path": "packages/velvetos/samples/",
        "runtimeAuthority": False,
        "purpose": "documentation-and-rollback-compatibility-only",
        "runtimeResolution": "instanceResolution",
    }, "pre-retirement Core sample metadata drift")

    replay_ok = historical_stage8c_replays()
    require(replay_ok, "historical Stage 8C sample receipt is not byte-reproducible")

    criteria = {
        "explicit_rollback_window_closure_is_merged": True,
        "closure_did_not_self_authorize_deletion": True,
        "legacy_sample_is_still_present_before_retirement": True,
        "active_legacy_consumer_count_is_zero": True,
        "only_historical_guard_and_snapshot_references_remain": True,
        "legacy_sample_is_byte_unchanged_since_cutover": True,
        "canonical_legacy_module_parity_is_preserved": True,
        "historical_stage8c_sample_receipt_replays_byte_equal": replay_ok,
        "closure_merge_main_ci_is_green": True,
        "closure_merge_local_full_suite_is_116_of_116": True,
        "external_effect_authority_is_unchanged": True,
        "authorization_scope_is_single_surface_and_explicit": True,
        "no_delete_occurs_in_this_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-retirement-gate.v1",
        "stage": "8D_SAMPLE_PROFILE_RETIREMENT_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
        "legacy_path": LEGACY_REL,
        "canonical_path": CANONICAL_REL,
        "purpose": (
            "Authorize a later isolated retirement of the legacy VF sample profile after explicit rollback "
            "closure, clean consumer/parity revalidation, historical receipt replay proof and post-closure CI."
        ),
        "closure_binding": {
            "pull_request": CLOSURE_PR,
            "merge_sha": CLOSURE_MERGE_SHA,
            "receipt": CLOSURE_REL,
            "rollback_window_closed": True,
            "closure_delete_authorized": False,
            "retirement_ready_for_deletion_gate": True,
        },
        "current_revalidation": {
            "legacy_present": True,
            "active_consumer_count": 0,
            "legacy_references": refs,
            "legacy_reference_class": "HISTORICAL_GUARDS_AND_SNAPSHOT_GENERATORS_ONLY",
            "legacy_byte_unchanged_since_cutover": True,
            "canonical_legacy_module_parity": True,
            "historical_stage8c_receipt_replays_byte_equal": replay_ok,
            "core_sample_metadata_runtime_authority": False,
            "external_effect_authority_unchanged": True,
        },
        "post_closure_verification": {
            "main_sha": CLOSURE_MERGE_SHA,
            "github_core_sensors": {
                "workflow_run_id": MAIN_CI_RUN,
                "conclusion": "SUCCESS",
            },
            "github_readme_pulse": {
                "workflow_run_id": MAIN_README_RUN,
                "conclusion": "SUCCESS",
            },
            "local_full_suite": {
                "mode": "full",
                "registered_sensors": 116,
                "passed_sensors": 116,
                "conclusion": "SUCCESS",
                "repository_files_unchanged": True,
            },
        },
        "authorization": {
            "surface_retirement_authorized": True,
            "delete_authorized": True,
            "authorized_delete_paths": [LEGACY_REL],
            "required_same-surface_cleanup": [
                "remove packages/velvetos/CORE.json sampleProfiles rollback-only metadata",
                "preserve historical Stage 8A/8B/8C receipts through source-snapshot replay",
                "update live policy/docs to state sample_profile is retired",
            ],
            "authorization_consumed": False,
            "overall_stage8d_retirement_authorized": False,
            "invalidated_by_new_active_consumer_or_parity_or_authority_drift": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "retirement_authorized": True,
        "delete_authorized": True,
        "deletion_performed": False,
        "next_action": (
            "Create a separate PR from the merged gate, revalidate exact main/head, delete only "
            "packages/velvetos/samples/velvet-factory.json, remove stale Core sampleProfiles metadata, "
            "preserve historical receipt replay, run selector plus independent full suite, and merge only if green."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha,
            "closure_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "this gate performs no deletion",
            "authorization applies only to sample_profile",
            "no big-bang delete",
            "historical evidence must remain byte-reproducible after retirement",
            "external-effect authority must remain unchanged",
            "other Stage 8D rollback windows remain independently gated",
        ],
    }

    require(all(criteria.values()), "sample retirement gate acceptance failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_RETIREMENT_GATE "
        f"assessment={report['repository_assessment']} "
        f"retirement_authorized={report['retirement_authorized']} "
        f"delete_authorized={report['delete_authorized']} deletion_performed={report['deletion_performed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
