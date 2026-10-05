#!/usr/bin/env python3
"""Generate Stage 8D tool-status rollback-window closure evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-tool-status-rollback-closure.json"
CORRECTION = REPORTS / "stage8d-tool-status-semantic-correction.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join(["packages", "velvetos", "TOOL-STATUS.json"])
CONTRACT = "packages/velvetos/tool-status-contract.json"
STATE = "instances/velvet-factory/instance/tool-status.json"
CORRECTION_PR = 536
CORRECTION_MERGE_SHA = "ed183f59959b4eaebd5a092e61d4ef969e834df7"

EXPECTED_SAFE = {
    "packages/velvetos/CORE.json": "rollback_contract_reference",
    "packages/velvetos/policy/sensor-registry.json": "rollback_sensor_binding",
    "packages/velvetos/schema/tool-status-contract.schema.json": "rollback_contract_schema_reference",
    "packages/velvetos/tool-status-contract.json": "rollback_contract_reference",
    "packages/velvetos/tool_status_resolver.py": "rollback_parity_implementation",
    "scripts/check-velvetos.py": "rollback_parity_sensor",
}

OBSERVATION_RUNS = [
    {"id": 37262173012, "sha": "ed183f59959b4eaebd5a092e61d4ef969e834df7", "created_at": "2026-10-05T04:07:50Z", "event": "push", "conclusion": "success"},
    {"id": 37263663917, "sha": "adf1b3195951ca00f0f1d976fa06523c7e90b069", "created_at": "2026-10-05T04:28:24Z", "event": "push", "conclusion": "success"},
    {"id": 37267662064, "sha": "b722f622dd2eab031c087fe051c56a5eb019d705", "created_at": "2026-10-05T05:24:39Z", "event": "push", "conclusion": "success"},
    {"id": 37269082934, "sha": "e3a91cabcfdd2a145cdb79339ffc8a68c724a18a", "created_at": "2026-10-05T05:44:01Z", "event": "push", "conclusion": "success"},
    {"id": 37270696543, "sha": "dcf7fab530f97ac326018182a8545625897a95fa", "created_at": "2026-10-05T06:05:39Z", "event": "push", "conclusion": "success"},
    {"id": 37270881356, "sha": "840206d08a6d13638fd560dddca1dd6583076612", "created_at": "2026-10-05T06:08:00Z", "event": "push", "conclusion": "success"},
    {"id": 37272603427, "sha": "e853c0497546b2528f56da2578cb4cc9f3d2ab80", "created_at": "2026-10-05T06:28:34Z", "event": "push", "conclusion": "success"},
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


def snapshot_tool_status_audit(sha: str) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_tool_status_closure_semantic_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "tool_status")
    require(isinstance(row, dict), "snapshot tool-status semantic audit did not return an object")
    all_rows = {surface_id: module.scan_surface(sha, surface_id) for surface_id in module.SURFACES}
    return row, module, all_rows


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
            "prepared-against main does not descend from the tool-status correction")

    correction = git_json(args.prepared_against, CORRECTION.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    contract = git_json(args.prepared_against, CONTRACT)
    state = git_json(args.prepared_against, STATE)

    require(correction.get("repository_assessment") == "PASS",
            "tool-status semantic correction must PASS")
    require(correction.get("surface_id") == "tool_status", "tool-status correction surface drift")
    rollback_fix = correction.get("rollback") or {}
    require(
        rollback_fix.get("window_open") is True
        and rollback_fix.get("closure_evidence") is None
        and rollback_fix.get("retirement_ready_for_deletion_gate") is False
        and rollback_fix.get("delete_authorized") is False,
        "tool-status correction rollback baseline drift",
    )
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(CORRECTION_MERGE_SHA, LEGACY),
            "legacy TOOL-STATUS changed after semantic correction")

    comp = contract.get("composition") or {}
    require(comp.get("activeAuthority") == "instance:surface:toolStatus",
            "active tool-status authority drift")
    require(comp.get("rollbackCompatibilityPath") == LEGACY, "rollback compatibility path drift")
    require(comp.get("consumerCutover") is True, "tool-status consumer cutover drift")
    require(comp.get("rollbackCompatibilityRetained") is True,
            "tool-status rollback compatibility retention drift")

    composed = {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }
    parity = csha(composed) == csha(legacy)
    require(parity, "canonical tool-status composition is not parity-equal to retained legacy composite")

    audit, module, all_rows = snapshot_tool_status_audit(args.prepared_against)
    require(audit.get("retirement_preflight_clear") is True, "tool_status semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [], "tool_status semantic blockers remain")
    classes = audit.get("classes") or {}
    safe_refs: dict[str, str] = {}
    for rel, expected_class in EXPECTED_SAFE.items():
        actual_class = module.tool_status_safe_class(args.prepared_against, rel)
        safe_refs[rel] = actual_class
        require(actual_class == expected_class, f"{rel}: safe classification drift ({actual_class!r})")
        require(rel in (classes.get(expected_class) or []), f"{rel}: semantic audit class missing {expected_class}")
    require(len(safe_refs) == 6, "tool-status safe reference count drift")

    all_clear = all(
        isinstance(row, dict)
        and row.get("retirement_preflight_clear") is True
        and row.get("retirement_preflight_blockers") == []
        for row in all_rows.values()
    )
    require(len(all_rows) == 5 and all_clear, "global Stage 8D semantic preflight is not 5/5 clear")

    authority = correction.get("authority") or {}
    policy_sha = csha(policy)
    require(authority.get("active_authority") == "instance:surface:toolStatus",
            "tool-status correction active-authority receipt drift")
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed since tool-status correction")
    require(authority.get("external_effect_authority_changed") is False,
            "tool-status correction authority state drift")

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
    require(OBSERVATION_RUNS[-1]["sha"] == args.prepared_against,
            "latest observation does not match prepared-against main")

    criteria = {
        "tool_status_semantic_correction_is_pass": True,
        "active_authority_remains_instance_surface_tool_status": True,
        "six_remaining_machine_refs_remain_content_validated_rollback_only": True,
        "tool_status_semantic_preflight_is_clear": True,
        "all_five_stage8d_semantic_preflights_are_clear": True,
        "legacy_tool_status_is_byte_unchanged_since_correction": True,
        "canonical_composition_remains_exactly_parity_equal": parity,
        "external_effect_authority_is_unchanged": True,
        "observation_window_contains_multiple_distinct_downstream_main_heads": True,
        "all_downstream_main_head_verifications_are_successful": True,
        "all_observations_descend_from_tool_status_correction": True,
        "latest_observation_matches_prepared_against_main": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_file_is_retained_after_closure": True,
        "deletion_requires_a_separate_isolated_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-tool-status-rollback-closure.v1",
        "stage": "8D_TOOL_STATUS_ROLLBACK_CLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "tool_status",
        "legacy_path": LEGACY,
        "canonical_contract_path": CONTRACT,
        "canonical_state_path": STATE,
        "purpose": (
            "Close the tool_status rollback observation window using post-correction content classification, "
            "semantic, exact-composition parity, legacy immutability and downstream-main evidence while retaining "
            "the compatibility composite and keeping deletion unauthorized."
        ),
        "correction": {
            "receipt": CORRECTION.relative_to(ROOT).as_posix(),
            "pull_request": CORRECTION_PR,
            "merge_sha": CORRECTION_MERGE_SHA,
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_authority": comp.get("activeAuthority"),
            "content_validated_safe_references": safe_refs,
            "safe_reference_count": len(safe_refs),
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "legacy_byte_unchanged_since_correction": True,
            "canonical_composed_sha256": csha(composed),
            "legacy_sha256": csha(legacy),
            "canonical_composition_exact_equal": parity,
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY",
            "elapsed_time_is_not_closure_authority": True,
            "start_merge_sha": CORRECTION_MERGE_SHA,
            "end_main_sha": args.prepared_against,
            "workflow": "VelvetOS Core Sensors",
            "verified_main_head_run_count": len(OBSERVATION_RUNS),
            "workflow_events": ["push"],
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
                "Active authority remains instance:surface:toolStatus, all six remaining machine references remain "
                "content-validated rollback/parity metadata, semantic preflight is clear, canonical composition is "
                "exactly parity-equal to the retained legacy composite, legacy bytes and policy authority are "
                "unchanged, and multiple downstream exact-main-head full-suite observations are green."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Run a separate isolated tool_status deletion gate. Revalidate current semantic classification, this "
            "closure receipt, latest main CI, exact composition parity and external-effect authority before "
            "authorizing deletion or removing rollback metadata."
        ),
        "authority": {
            "active_authority": comp.get("activeAuthority"),
            "policy_registry_sha256": policy_sha,
            "tool_status_correction_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "closure evidence does not itself authorize deletion",
            "legacy TOOL-STATUS remains present in this change",
            "six reviewed rollback/parity references remain fail-closed content classifications",
            "no big-bang delete",
            "retirement must be isolated to tool_status",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "tool-status rollback closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE "
        f"assessment={report['repository_assessment']} closed={report['rollback_window_closed']} "
        f"safe_refs={len(safe_refs)} parity={str(parity).lower()} runs={len(OBSERVATION_RUNS)} "
        f"delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
