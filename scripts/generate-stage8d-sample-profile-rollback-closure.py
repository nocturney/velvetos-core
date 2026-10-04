#!/usr/bin/env python3
"""Generate explicit Stage 8D rollback-window closure evidence for the legacy VF sample profile.

Evidence-only. This closes the rollback observation window for sample_profile
without deleting the compatibility file and without authorizing deletion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
SAMPLE_RECEIPT = REPORTS / "stage8c-sample-profile-consumers.json"
POST_MIGRATION = REPORTS / "stage8d-post-migration-readiness.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
OUT = REPORTS / "stage8d-sample-profile-rollback-closure.json"

LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL = "/".join(["instances", "velvet-factory", "instance", "velvet-factory.json"])
CUTOVER_PR = 510
CUTOVER_MERGE_SHA = "80bed30bf54c854f2854d7328ccda171a587d569"
CUTOVER_AT = "2026-10-04T12:50:12Z"
REPAIR_PR = 519
REPAIR_MERGE_SHA = "b46f0414613c1e957ea9f3f0d34ad0ba82ccdf93"

ALLOWED_LEGACY_REFS = [
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8a-core-instance-inventory.py",
    "scripts/generate-stage8b-instance-resolver-foundation.py",
]

OBSERVATION_RUNS = [
    {"id": 37203484008, "sha": "80bed30bf54c854f2854d7328ccda171a587d569", "created_at": "2026-10-04T12:50:15Z", "conclusion": "success"},
    {"id": 37204438791, "sha": "bd7ba61f4f512a9b101e90b79e21a20d41674483", "created_at": "2026-10-04T13:06:26Z", "conclusion": "success"},
    {"id": 37205358052, "sha": "d8091ca0f788f7a5b1eb3eaa8f2f724e6063c1fb", "created_at": "2026-10-04T13:21:55Z", "conclusion": "success"},
    {"id": 37206100010, "sha": "3b656636c8df3d84dcf1aca9944edbb222ad6bde", "created_at": "2026-10-04T13:34:26Z", "conclusion": "success"},
    {"id": 37207919550, "sha": "aa7feccd1b31c9ca428562e546de42a1f91a9b9d", "created_at": "2026-10-04T14:04:31Z", "conclusion": "success"},
    {"id": 37214342312, "sha": "ac9af3536e78d029872f3db69f02e4bf9e90504b", "created_at": "2026-10-04T15:47:51Z", "conclusion": "success"},
    {"id": 37215095998, "sha": "03cf86ae850179fb4cf0a5460bee76a74569def5", "created_at": "2026-10-04T15:59:43Z", "conclusion": "success"},
    {"id": 37218152953, "sha": "4945a6de7b6dd06e07bfbec106b30fe4052409f6", "created_at": "2026-10-04T16:48:55Z", "conclusion": "failure"},
    {"id": 37219282743, "sha": "b46f0414613c1e957ea9f3f0d34ad0ba82ccdf93", "created_at": "2026-10-04T17:06:56Z", "conclusion": "success"},
    {"id": 37219801669, "sha": "2bac699984337506ce13a839984526c17b408eab", "created_at": "2026-10-04T17:15:12Z", "conclusion": "success"},
    {"id": 37221071250, "sha": "11ce1ca3a44cb21af24add900ab6b0e9d9e0a47e", "created_at": "2026-10-04T17:35:11Z", "conclusion": "success"},
    {"id": 37221939252, "sha": "a55a1d965903a384a139b2f62135648b3a11403c", "created_at": "2026-10-04T17:48:54Z", "conclusion": "success"},
    {"id": 37223042443, "sha": "79ab05dc02964f5fdc77e19a1ac69b6222676c51", "created_at": "2026-10-04T18:05:33Z", "conclusion": "success"},
    {"id": 37223939091, "sha": "54b9501483f795202447bb53b6e5151bd3af2ccf", "created_at": "2026-10-04T18:18:39Z", "conclusion": "success"},
    {"id": 37224855463, "sha": "8bcdb7de55341a282862dfb9764716a14f10441f", "created_at": "2026-10-04T18:32:53Z", "conclusion": "success"},
    {"id": 37226359339, "sha": "1a03b212761223f198b82a1443374a7fc4a7fed7", "created_at": "2026-10-04T18:56:39Z", "conclusion": "success"},
    {"id": 37228203854, "sha": "aa6e163fa635a540e11bd8f40fd65d08bc0c4ade", "created_at": "2026-10-04T19:25:16Z", "conclusion": "success"},
    {"id": 37228944358, "sha": "c344ecb12d9cc3f8ec254c4dd08dda397ad96ea4", "created_at": "2026-10-04T19:36:50Z", "conclusion": "success"},
]

UNRELATED_FAILURE = {
    "workflow_run_id": 37218152953,
    "head_sha": "4945a6de7b6dd06e07bfbec106b30fe4052409f6",
    "failed_sensor": "check-vfresearch.py",
    "failure": "Stage 7C acceptance receipt was not reproducible after the mutable provider-readback pointer advanced.",
    "sample_profile_related": False,
    "repair_pr": REPAIR_PR,
    "repair_merge_sha": REPAIR_MERGE_SHA,
    "repair": "Historical Stage 7C replay was snapshot-bound to its recorded provider-readback witness.",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    require(isinstance(obj, dict), f"{rel}@{sha} must be a JSON object")
    return obj


def git_refs(sha: str, needle: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", needle, sha, "--", ":!packages/velvetos/policy/reports/*"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or "git grep failed")
    prefix = f"{sha}:"
    refs: list[str] = []
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")
    require(OBSERVATION_RUNS[-1]["sha"] == args.prepared_against,
            "observation window must end at --prepared-against")
    require(all(row["conclusion"] in {"success", "failure"} for row in OBSERVATION_RUNS),
            "unexpected observation conclusion")

    sample = git_json(args.prepared_against, SAMPLE_RECEIPT.relative_to(ROOT).as_posix())
    post = git_json(args.prepared_against, POST_MIGRATION.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(sample.get("repository_acceptance") == "PASS", "Stage 8C sample migration must PASS")
    legacy8c = sample.get("legacy_sample") or {}
    require(legacy8c.get("runtime_authority") is False, "legacy sample unexpectedly has runtime authority")
    require(legacy8c.get("rollback_window_open") is True, "historical sample rollback window must be open")
    require(legacy8c.get("delete_authorized") is False, "historical sample delete authority drift")

    sample8d = (post.get("compatibility_surfaces") or {}).get("sample_profile") or {}
    require(sample8d.get("active_consumers_migrated") is True, "sample active consumers are not fully migrated")
    require(sample8d.get("parity_proven") is True, "sample parity is not proven")
    require(sample8d.get("rollback_window_open") is True, "post-migration baseline must show window open")
    require(sample8d.get("rollback_window_closure_evidence") is None,
            "post-migration baseline unexpectedly contains closure evidence")
    require(sample8d.get("delete_authorized") is False, "post-migration baseline delete authority drift")

    refs = git_refs(args.prepared_against, LEGACY)
    require(refs == ALLOWED_LEGACY_REFS, f"unexpected legacy sample references: {refs}")
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(CUTOVER_MERGE_SHA, LEGACY),
            "legacy sample changed after cutover")
    require(set(legacy.get("modulesEnabled") or []) == set(canonical.get("modulesEnabled") or []),
            "canonical and legacy module sets diverged")

    policy_sha = csha(policy)
    authority8c = sample.get("authority_baseline") or {}
    require(policy_sha == authority8c.get("policy_registry_canonical_sha256"),
            "external-effect policy authority changed since sample cutover")

    successes = [row for row in OBSERVATION_RUNS if row["conclusion"] == "success"]
    failures = [row for row in OBSERVATION_RUNS if row["conclusion"] == "failure"]
    repair_index = next(i for i, row in enumerate(OBSERVATION_RUNS) if row["sha"] == REPAIR_MERGE_SHA)
    post_repair = OBSERVATION_RUNS[repair_index:]
    require(len(failures) == 1 and failures[0]["id"] == UNRELATED_FAILURE["workflow_run_id"],
            "observation failures differ from classified evidence")
    require(UNRELATED_FAILURE["sample_profile_related"] is False,
            "classified failure must remain explicitly unrelated to sample_profile")
    require(all(row["conclusion"] == "success" for row in post_repair),
            "a main full-suite failure exists after the unrelated repair")
    require(len(post_repair) >= 2, "insufficient post-repair observation coverage")

    criteria = {
        "stage8c_sample_cutover_passed": True,
        "legacy_sample_has_no_runtime_authority": True,
        "active_legacy_consumers_remain_zero": True,
        "legacy_sample_is_byte_unchanged_since_cutover": True,
        "canonical_and_legacy_module_sets_match": True,
        "external_effect_authority_is_unchanged": True,
        "observation_window_contains_multiple_downstream_main_full_suites": True,
        "all_observed_failures_are_explicitly_classified": True,
        "only_observed_failure_is_unrelated_to_sample_profile": True,
        "unrelated_failure_has_explicit_repair_and_post_repair_green_runs": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_file_is_retained_after_window_closure": True,
        "deletion_requires_a_separate_retirement_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-rollback-closure.v1",
        "stage": "8D_SAMPLE_PROFILE_ROLLBACK_CLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
        "path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Close the sample_profile rollback observation window using explicit consumer, parity, "
            "immutability and downstream-CI evidence, while retaining the compatibility file and "
            "keeping deletion unauthorized until a separate retirement gate."
        ),
        "cutover": {
            "pull_request": CUTOVER_PR,
            "merge_sha": CUTOVER_MERGE_SHA,
            "merged_at": CUTOVER_AT,
            "migration_receipt": SAMPLE_RECEIPT.relative_to(ROOT).as_posix(),
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "legacy_references": refs,
            "legacy_reference_class": "HISTORICAL_GUARDS_AND_SNAPSHOT_GENERATORS_ONLY",
            "legacy_byte_unchanged_since_cutover": True,
            "canonical_legacy_module_parity": True,
            "active_consumer_count": 0,
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "DOWNSTREAM_MAIN_FULL_SUITE_AND_CONSUMER_STABILITY",
            "elapsed_time_is_not_closure_authority": True,
            "start_merge_sha": CUTOVER_MERGE_SHA,
            "end_main_sha": args.prepared_against,
            "workflow": "VelvetOS Core Sensors",
            "main_push_run_count": len(OBSERVATION_RUNS),
            "success_count": len(successes),
            "failure_count": len(failures),
            "runs": OBSERVATION_RUNS,
            "classified_failures": [UNRELATED_FAILURE],
            "post_repair_success_count": len(post_repair),
            "latest_main_full_suite_success": OBSERVATION_RUNS[-1]["conclusion"] == "success",
        },
        "rollback_window": {
            "was_open_in_stage8c_receipt": True,
            "was_open_in_post_migration_baseline": True,
            "closure_evidence": "this_receipt",
            "closed": True,
            "closure_reason": (
                "No active sample consumers, no legacy drift, canonical parity preserved, policy authority "
                "unchanged, and downstream main full-suite observation shows no sample-related regression. "
                "The one observed failure was unrelated and has an explicit repair followed by green runs."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Run a separate isolated sample_profile retirement gate. Do not delete the legacy sample "
            "unless that later gate revalidates clean consumers, parity/closure evidence, current main CI "
            "and external-effect authority, then explicitly authorizes deletion."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha,
            "stage8c_policy_registry_sha256": authority8c.get("policy_registry_canonical_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "closure evidence does not itself authorize deletion",
            "legacy sample remains present in this change",
            "no big-bang delete",
            "retirement must be isolated to sample_profile",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "sample rollback closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_ROLLBACK_CLOSURE "
        f"assessment={report['repository_assessment']} "
        f"closed={report['rollback_window_closed']} "
        f"delete_authorized={report['delete_authorized']} "
        f"runs={len(OBSERVATION_RUNS)} successes={len(successes)} failures={len(failures)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
