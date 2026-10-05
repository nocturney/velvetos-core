#!/usr/bin/env python3
"""Generate the isolated Stage 8D tool_status deletion gate.

Evidence-only: authorizes deletion of exactly the retained TOOL-STATUS
compatibility composite in a later isolated PR. This gate performs no deletion
and grants no authority over chatgpt_core_bundle.
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
OUT = REPORTS / "stage8d-tool-status-deletion-gate.json"
CLOSURE = REPORTS / "stage8d-tool-status-rollback-closure.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "packages/velvetos/TOOL-STATUS.json"
CONTRACT = "packages/velvetos/tool-status-contract.json"
STATE = "instances/velvet-factory/instance/tool-status.json"
PREPARED_MAIN = "3f7bd148ebf31dae67a02e86ba2b8727dc14c171"
LATEST_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37301696406,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T11:14:47Z",
}
PRIOR_RETIREMENTS = {
    "sample_profile": {
        "receipt": "stage8d-sample-profile-deletion.json",
        "schema": "velvetos.stage8d-sample-profile-deletion.v1",
        "legacy": "packages/velvetos/samples/velvet-factory.json",
    },
    "root_desk": {
        "receipt": "stage8d-root-desk-deletion.json",
        "schema": "velvetos.stage8d-root-desk-deletion.v1",
        "legacy": ".cursor/vf-desk.json",
    },
    "fleet": {
        "receipt": "stage8d-fleet-deletion.json",
        "schema": "velvetos.stage8d-fleet-deletion.v1",
        "legacy": "packages/vfprod/FLEET.json",
    },
}
CHATGPT_CLOSURE = REPORTS / "stage8d-chatgpt-rollback-closure.json"
EXPECTED_SAFE = {
    "packages/velvetos/CORE.json": "rollback_contract_reference",
    "packages/velvetos/policy/sensor-registry.json": "rollback_sensor_binding",
    "packages/velvetos/schema/tool-status-contract.schema.json": "rollback_contract_schema_reference",
    "packages/velvetos/tool-status-contract.json": "rollback_contract_reference",
    "packages/velvetos/tool_status_resolver.py": "rollback_parity_implementation",
    "scripts/check-velvetos.py": "rollback_parity_sensor",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    value = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    require(isinstance(value, dict), f"{rel}@{sha} must be a JSON object")
    return value


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    proc = subprocess.run(["git", "hash-object", "--stdin"], cwd=ROOT, input=raw, capture_output=True)
    require(proc.returncode == 0, "git hash-object failed for tool-status restore anchor")
    value = proc.stdout.decode("ascii", errors="strict").strip()
    require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "invalid Git blob SHA")
    return value


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


def validate_retirement(sha: str, surface_id: str, spec: dict[str, str]) -> dict[str, Any]:
    rel = (REPORTS / spec["receipt"]).relative_to(ROOT).as_posix()
    receipt = git_json(sha, rel)
    deletion = receipt.get("deletion") or {}
    authority = receipt.get("authority") or {}
    require(
        receipt.get("schema") == spec["schema"]
        and receipt.get("surface_id") == surface_id
        and receipt.get("repository_assessment") == "PASS"
        and receipt.get("deletion_performed") is True
        and receipt.get("retirement_authorized") is True
        and deletion.get("legacy_path") == spec["legacy"]
        and deletion.get("legacy_present") is False
        and deletion.get("deletion_performed") is True
        and authority.get("retirement_authorized") is True
        and not git_exists(sha, spec["legacy"]),
        f"{surface_id}: prior retirement receipt or absence drift",
    )
    return {
        "receipt": rel,
        "repository_assessment": "PASS",
        "deletion_performed": True,
        "retirement_authorized": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(
        re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
        "--prepared-against must be a full lowercase Git SHA",
    )
    require(
        args.prepared_against == PREPARED_MAIN,
        "tool-status deletion gate must be generated against its verified exact main boundary",
    )

    closure = git_json(args.prepared_against, CLOSURE.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    contract = git_json(args.prepared_against, CONTRACT)
    state = git_json(args.prepared_against, STATE)

    require(
        closure.get("schema") == "velvetos.stage8d-tool-status-rollback-closure.v1"
        and closure.get("surface_id") == "tool_status"
        and closure.get("repository_assessment") == "PASS"
        and closure.get("rollback_window_closed") is True
        and closure.get("retirement_ready_for_deletion_gate") is True
        and closure.get("delete_authorized") is False
        and closure.get("retirement_authorized") is False,
        "tool-status rollback closure is not a valid deletion-gate prerequisite",
    )
    closure_evidence = closure.get("current_evidence") or {}
    require(
        closure_evidence.get("runtime_authority") is False
        and closure_evidence.get("active_authority") == "instance:surface:toolStatus"
        and closure_evidence.get("safe_reference_count") == 6
        and closure_evidence.get("semantic_preflight_clear") is True
        and closure_evidence.get("all_stage8d_semantic_preflights_clear") is True
        and closure_evidence.get("canonical_composition_exact_equal") is True
        and closure_evidence.get("external_effect_authority_unchanged") is True,
        "tool-status closure current evidence drift",
    )

    prior = {
        surface_id: validate_retirement(args.prepared_against, surface_id, spec)
        for surface_id, spec in PRIOR_RETIREMENTS.items()
    }

    chatgpt = git_json(args.prepared_against, CHATGPT_CLOSURE.relative_to(ROOT).as_posix())
    remaining = {
        "repository_assessment": chatgpt.get("repository_assessment"),
        "rollback_window_closed": chatgpt.get("rollback_window_closed"),
        "retirement_ready_for_deletion_gate": chatgpt.get("retirement_ready_for_deletion_gate"),
        "delete_authorized": chatgpt.get("delete_authorized"),
        "retirement_authorized": chatgpt.get("retirement_authorized"),
    }
    require(
        remaining["repository_assessment"] == "PASS"
        and remaining["rollback_window_closed"] is True
        and remaining["retirement_ready_for_deletion_gate"] is True
        and remaining["delete_authorized"] is False
        and remaining["retirement_authorized"] is False,
        "chatgpt retained-surface closure prerequisite drift",
    )

    prior_sha = str(closure.get("prepared_against_main_sha") or "")
    require(re.fullmatch(r"[0-9a-f]{40}", prior_sha) is not None, "tool-status closure prepared SHA missing")
    require(
        git_bytes(args.prepared_against, LEGACY) == git_bytes(prior_sha, LEGACY),
        "legacy TOOL-STATUS changed after rollback closure",
    )

    comp = contract.get("composition") or {}
    require(comp.get("activeAuthority") == "instance:surface:toolStatus", "active tool-status authority drift")
    require(comp.get("rollbackCompatibilityPath") == LEGACY, "rollback compatibility path drift")
    require(comp.get("consumerCutover") is True, "tool-status consumer cutover drift")
    require(comp.get("rollbackCompatibilityRetained") is True, "tool-status retention drift")
    composed = {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }
    parity = csha(composed) == csha(legacy)
    require(parity, "canonical tool-status composition is not parity-equal to retained legacy composite")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    tool_audit = surfaces.get("tool_status") or {}
    assessment = audit.get("assessment") or {}
    classes = tool_audit.get("classes") or {}
    require(
        tool_audit.get("present") is True
        and tool_audit.get("retirement_preflight_clear") is True
        and tool_audit.get("retirement_preflight_blockers") == [],
        "current tool-status semantic preflight is not clear",
    )
    for rel, expected_class in EXPECTED_SAFE.items():
        require(rel in (classes.get(expected_class) or []), f"{rel}: safe semantic classification drift")
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and assessment.get("surfaces_retired") == 3
        and assessment.get("retired_surfaces") == ["fleet", "root_desk", "sample_profile"]
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic state is not 5/5 clear with exactly three retired surfaces",
    )

    raw = git_bytes(args.prepared_against, LEGACY)
    legacy_sha256 = hashlib.sha256(raw).hexdigest()
    blob_sha1 = git_blob_sha1(raw)
    require(len(raw) > 0, "tool-status compatibility file is unexpectedly empty")

    policy_sha = csha(policy)
    closure_authority = closure.get("authority") or {}
    require(
        closure_authority.get("active_authority") == "instance:surface:toolStatus"
        and policy_sha == closure_authority.get("policy_registry_sha256")
        and closure_authority.get("external_effect_authority_changed") is False,
        "external-effect policy authority changed since tool-status closure",
    )
    require(
        LATEST_MAIN_CI["sha"] == args.prepared_against
        and LATEST_MAIN_CI["conclusion"] == "success"
        and LATEST_MAIN_CI["event"] == "push",
        "latest main CI evidence is not bound to the prepared main SHA",
    )

    criteria = {
        "tool_status_closure_is_pass_and_closed": True,
        "tool_status_closure_is_ready_for_deletion_gate": True,
        "tool_status_closure_did_not_pre_authorize_deletion": True,
        "three_prior_retirements_are_authoritatively_proven": True,
        "chatgpt_core_bundle_is_closed_gate_ready_and_deletion_unauthorized": True,
        "current_tool_status_semantic_preflight_is_clear": True,
        "current_global_semantic_preflight_is_5_of_5_clear": True,
        "semantic_audit_recognizes_exactly_three_retired_surfaces": True,
        "six_machine_references_remain_content_validated_rollback_only": True,
        "active_authority_remains_instance_surface_tool_status": True,
        "legacy_tool_status_is_unchanged_since_closure": True,
        "canonical_composition_remains_exactly_parity_equal": True,
        "exact_legacy_blob_is_anchored_for_restore": True,
        "latest_exact_main_core_sensor_run_is_success": True,
        "external_effect_authority_is_unchanged": True,
        "gate_authorizes_only_tool_status_target": True,
        "deletion_is_not_performed_in_gate_change": True,
        "retirement_completion_waits_for_separate_deletion_pr": True,
    }

    report = {
        "schema": "velvetos.stage8d-tool-status-deletion-gate.v1",
        "stage": "8D_TOOL_STATUS_DELETION_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "tool_status",
        "target": {
            "legacy_path": LEGACY,
            "canonical_contract_path": CONTRACT,
            "canonical_state_path": STATE,
            "delete_exactly": [LEGACY],
            "delete_other_surfaces": False,
        },
        "purpose": (
            "Authorize one later isolated deletion of the TOOL-STATUS compatibility composite after revalidating "
            "current semantic classification, exact canonical composition parity, rollback closure, the prior "
            "three retirements, restore evidence and policy authority. This gate performs no deletion."
        ),
        "prerequisite_closure": {
            "receipt": CLOSURE.relative_to(ROOT).as_posix(),
            "schema": closure.get("schema"),
            "rollback_window_closed": True,
            "retirement_ready_for_deletion_gate": True,
        },
        "prior_retirements": prior,
        "remaining_surface_state": {"chatgpt_core_bundle": remaining},
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_authority": "instance:surface:toolStatus",
            "content_validated_safe_references": EXPECTED_SAFE,
            "safe_reference_count": len(EXPECTED_SAFE),
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "retired_surfaces": ["fleet", "root_desk", "sample_profile"],
            "legacy_byte_unchanged_since_closure": True,
            "canonical_composed_sha256": csha(composed),
            "legacy_canonical_sha256": csha(legacy),
            "canonical_composition_exact_equal": parity,
            "external_effect_authority_unchanged": True,
        },
        "restore_anchor": {
            "source_commit_sha": args.prepared_against,
            "legacy_path": LEGACY,
            "git_blob_sha1": blob_sha1,
            "sha256": legacy_sha256,
            "size_bytes": len(raw),
            "restore_command": f"git show {args.prepared_against}:{LEGACY} > {LEGACY}",
        },
        "latest_main_ci": LATEST_MAIN_CI,
        "authority": {
            "active_authority": "instance:surface:toolStatus",
            "policy_registry_sha256": policy_sha,
            "tool_status_closure_policy_registry_sha256": closure_authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
            "delete_authorized": True,
            "delete_authorized_surface": "tool_status",
            "delete_authorized_paths": [LEGACY],
            "retirement_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this evidence-only gate, verify post-merge main, then create a separate isolated tool_status "
            "deletion PR that removes exactly the authorized path and re-runs semantic, policy and full-suite checks."
        ),
        "constraints": [
            "this gate does not delete files",
            "authorization applies only to the exact tool_status target recorded above",
            "sample_profile, root_desk and fleet are already retired and are not modified by this gate",
            "chatgpt_core_bundle remains deletion-unauthorized by this receipt",
            "actual deletion requires a separate isolated PR",
            "restore anchor must remain available in Git history",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "tool-status deletion gate acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_TOOL_STATUS_DELETION_GATE "
        f"assessment=PASS delete_authorized=true path={LEGACY} "
        f"blob={blob_sha1[:12]} sha256={legacy_sha256[:12]} deletion_performed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
