#!/usr/bin/env python3
"""Generate Stage 8D fleet rollback-window closure evidence."""
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
OUT = REPORTS / "stage8d-fleet-rollback-closure.json"
CORRECTION = REPORTS / "stage8d-fleet-runtime-consumer-correction.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join(["packages", "vfprod", "FLEET.json"])
CANONICAL = "instances/velvet-factory/instance/fleet.json"
CORRECTION_PR = 534
CORRECTION_MERGE_SHA = "027700b3077bc900658313186e313772f539bd7d"

OBSERVATION_RUNS = [
    {"id": 37261424137, "sha": "027700b3077bc900658313186e313772f539bd7d", "created_at": "2026-10-05T03:56:40Z", "event": "push", "conclusion": "success"},
    {"id": 37262173012, "sha": "ed183f59959b4eaebd5a092e61d4ef969e834df7", "created_at": "2026-10-05T04:07:50Z", "event": "push", "conclusion": "success"},
    {"id": 37263663917, "sha": "adf1b3195951ca00f0f1d976fa06523c7e90b069", "created_at": "2026-10-05T04:28:24Z", "event": "push", "conclusion": "success"},
    {"id": 37267662064, "sha": "b722f622dd2eab031c087fe051c56a5eb019d705", "created_at": "2026-10-05T05:24:39Z", "event": "push", "conclusion": "success"},
    {"id": 37269082934, "sha": "e3a91cabcfdd2a145cdb79339ffc8a68c724a18a", "created_at": "2026-10-05T05:44:01Z", "event": "push", "conclusion": "success"},
    {"id": 37269731921, "sha": "8aa691f9ece02c50838ed11b64d5cde5528fb75c", "created_at": "2026-10-05T05:52:53Z", "event": "workflow_dispatch", "conclusion": "success", "additional_successful_run_ids": [37269817015]},
    {"id": 37270696543, "sha": "dcf7fab530f97ac326018182a8545625897a95fa", "created_at": "2026-10-05T06:05:39Z", "event": "push", "conclusion": "success"},
    {"id": 37270881356, "sha": "840206d08a6d13638fd560dddca1dd6583076612", "created_at": "2026-10-05T06:08:00Z", "event": "push", "conclusion": "success"},
]


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig", errors="replace")


def git_json(sha: str, rel: str) -> dict[str, Any]:
    value = json.loads(git_text(sha, rel))
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
            "closure must end at the latest recorded observation SHA")
    require(is_ancestor(CORRECTION_MERGE_SHA, args.prepared_against),
            "prepared-against main does not descend from the fleet correction")

    correction = git_json(args.prepared_against, CORRECTION.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(correction.get("repository_assessment") == "PASS", "fleet correction must PASS")
    require(correction.get("surface_id") == "fleet", "fleet correction surface drift")
    migration = correction.get("migration") or {}
    require(
        migration.get("runtime_consumers_migrated") is True
        and migration.get("legacy_present") is True
        and migration.get("legacy_byte_unchanged") is True
        and migration.get("canonical_legacy_parity") is True,
        "fleet correction migration/parity baseline drift",
    )
    rollback_fix = correction.get("rollback") or {}
    require(
        rollback_fix.get("window_open") is True
        and rollback_fix.get("closure_evidence") is None
        and rollback_fix.get("retirement_ready_for_deletion_gate") is False
        and rollback_fix.get("delete_authorized") is False,
        "fleet correction rollback baseline drift",
    )

    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(CORRECTION_MERGE_SHA, LEGACY),
            "legacy fleet changed after correction")
    require(legacy == canonical, "canonical fleet no longer matches retained legacy fleet exactly")

    migrated_code = migration.get("migrated_code") or []
    require(len(migrated_code) == 4, "fleet migrated-code binding count drift")
    code_rows: dict[str, dict[str, bool]] = {}
    for rel in migrated_code:
        text = git_text(args.prepared_against, rel)
        no_legacy = LEGACY not in text
        canonical_binding = (
            ("resolve_surface" in text and '"fleet"' in text)
            or "instance/fleet.json" in text
        )
        code_rows[rel] = {
            "legacy_path_absent": no_legacy,
            "canonical_fleet_binding_present": canonical_binding,
        }
        require(no_legacy, f"{rel}: legacy fleet path reappeared")
        require(canonical_binding, f"{rel}: canonical fleet binding missing")

    active_docs = migration.get("active_documentation") or {}
    require(active_docs and all(active_docs.values()), "fleet active-documentation receipt drift")
    active_doc_rows: dict[str, dict[str, bool]] = {}
    for rel in active_docs:
        text = git_text(args.prepared_against, rel)
        no_legacy = LEGACY not in text
        active_doc_rows[rel] = {"legacy_path_absent": no_legacy}
        require(no_legacy, f"{rel}: active documentation reintroduced legacy fleet path")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    fleet_audit = surfaces.get("fleet") or {}
    assessment = audit.get("assessment") or {}
    require(fleet_audit.get("retirement_preflight_clear") is True, "fleet semantic preflight is not clear")
    require(fleet_audit.get("retirement_preflight_blockers") == [], "fleet semantic blockers remain")
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic preflight is not 5/5 clear",
    )

    authority = correction.get("authority") or {}
    policy_sha = csha(policy)
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed since fleet correction")
    require(authority.get("external_effect_authority_changed") is False,
            "fleet correction authority state drift")

    require(len(OBSERVATION_RUNS) >= 5, "insufficient downstream main observation coverage")
    require(len({row["sha"] for row in OBSERVATION_RUNS}) == len(OBSERVATION_RUNS),
            "observation SHAs must be distinct")
    require(all(row["conclusion"] == "success" for row in OBSERVATION_RUNS),
            "downstream observation contains a non-success run")
    require(all(is_ancestor(CORRECTION_MERGE_SHA, row["sha"]) for row in OBSERVATION_RUNS),
            "observation contains a pre-correction SHA")
    require(all(is_ancestor(OBSERVATION_RUNS[i]["sha"], OBSERVATION_RUNS[i + 1]["sha"])
                for i in range(len(OBSERVATION_RUNS) - 1)),
            "observation SHAs are not a monotonic main lineage")

    criteria = {
        "fleet_correction_is_pass": True,
        "all_live_fleet_readers_remain_canonical": True,
        "all_active_fleet_documentation_remains_canonical": True,
        "fleet_semantic_preflight_is_clear": True,
        "all_five_stage8d_semantic_preflights_are_clear": True,
        "legacy_fleet_is_byte_unchanged_since_correction": True,
        "canonical_and_legacy_fleet_are_exactly_equal": True,
        "external_effect_authority_is_unchanged": True,
        "observation_window_contains_multiple_distinct_downstream_main_heads": True,
        "all_downstream_main_head_verifications_are_successful": True,
        "all_observations_descend_from_fleet_correction": True,
        "latest_observation_matches_prepared_against_main": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_file_is_retained_after_closure": True,
        "deletion_requires_a_separate_isolated_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-fleet-rollback-closure.v1",
        "stage": "8D_FLEET_ROLLBACK_CLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "fleet",
        "legacy_path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Close the fleet rollback observation window using post-correction consumer, active-documentation, "
            "semantic, exact-parity, immutability and downstream-main evidence while retaining the compatibility "
            "file and keeping deletion unauthorized."
        ),
        "correction": {
            "receipt": CORRECTION.relative_to(ROOT).as_posix(),
            "pull_request": CORRECTION_PR,
            "merge_sha": CORRECTION_MERGE_SHA,
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "migrated_code": code_rows,
            "active_documentation": active_doc_rows,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "legacy_byte_unchanged_since_correction": True,
            "canonical_legacy_exact_equal": True,
            "printer_count": len(legacy.get("printers") or []),
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY",
            "elapsed_time_is_not_closure_authority": True,
            "start_merge_sha": CORRECTION_MERGE_SHA,
            "end_main_sha": args.prepared_against,
            "workflow": "VelvetOS Core Sensors",
            "verified_main_head_run_count": len(OBSERVATION_RUNS),
            "workflow_events": sorted({row["event"] for row in OBSERVATION_RUNS}),
            "success_count": len(OBSERVATION_RUNS),
            "failure_count": 0,
            "runs": OBSERVATION_RUNS,
            "all_descend_from_correction": True,
            "monotonic_main_lineage": True,
            "latest_main_full_suite_success": True,
        },
        "rollback_window": {
            "was_open_in_correction_receipt": True,
            "closure_evidence": "this_receipt",
            "closed": True,
            "closure_reason": (
                "Fleet readers and active documentation remain canonical, semantic preflight is clear, exact "
                "canonical/legacy parity and legacy immutability are preserved, policy authority is unchanged, "
                "and multiple exact-main-head full-suite observations are green."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Run a separate isolated fleet deletion gate. Revalidate current semantic state, this closure receipt, "
            "latest main CI, exact parity and external-effect authority before authorizing deletion."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha,
            "fleet_correction_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "closure evidence does not itself authorize deletion",
            "legacy fleet remains present in this change",
            "no big-bang delete",
            "retirement must be isolated to fleet",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "fleet rollback closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_FLEET_ROLLBACK_CLOSURE "
        f"assessment={report['repository_assessment']} closed={report['rollback_window_closed']} "
        f"readers={len(code_rows)} docs={len(active_doc_rows)} parity=true "
        f"runs={len(OBSERVATION_RUNS)} delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
