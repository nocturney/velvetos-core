#!/usr/bin/env python3
"""Generate Stage 8D evidence that remaining TOOL-STATUS refs are rollback-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-tool-status-semantic-correction.json"
PRIOR = REPORTS / "stage8d-tool-status-consumer-migration.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"
LEGACY = "packages/velvetos/TOOL-STATUS.json"
CONTRACT = "packages/velvetos/tool-status-contract.json"
STATE = "instances/velvet-factory/instance/tool-status.json"

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


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig", errors="replace")


def git_json(sha: str, rel: str) -> dict[str, Any]:
    value = json.loads(git_text(sha, rel))
    require(isinstance(value, dict), f"{rel}@{sha} must be a JSON object")
    return value


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def snapshot_tool_status_audit(sha: str) -> tuple[dict[str, Any], Any]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_tool_status_semantic_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "tool_status")
    require(isinstance(row, dict), "snapshot tool-status semantic audit did not return an object")
    return row, module


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    for label, value in (("prepared-against", args.prepared_against), ("source-commit", args.source_commit)):
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"--{label} must be a full lowercase Git SHA")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", args.prepared_against, args.source_commit],
            cwd=ROOT,
            capture_output=True,
        ).returncode == 0,
        "source commit must descend from prepared-against",
    )

    prior = git_json(args.source_commit, PRIOR.relative_to(ROOT).as_posix())
    require(prior.get("repository_acceptance") == "PASS", "prior tool-status migration receipt must PASS")
    require((prior.get("consumer_scan") or {}).get("active_authority_legacy_references") == [],
            "prior tool-status migration still has active legacy authority refs")
    require((prior.get("parity") or {}).get("equal") is True, "prior tool-status parity must PASS")
    require((prior.get("rollback") or {}).get("window_open") is True, "prior rollback window must stay open")
    require((prior.get("rollback") or {}).get("delete_authorized") is False, "prior delete authority drift")

    legacy_before = git_json(args.prepared_against, LEGACY)
    legacy_after = git_json(args.source_commit, LEGACY)
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(args.source_commit, LEGACY),
            "legacy TOOL-STATUS changed during semantic correction")

    contract = git_json(args.source_commit, CONTRACT)
    state = git_json(args.source_commit, STATE)
    comp = contract.get("composition") or {}
    require(comp.get("activeAuthority") == "instance:surface:toolStatus", "active tool-status authority drift")
    require(comp.get("rollbackCompatibilityPath") == LEGACY, "rollback path drift")
    require(comp.get("consumerCutover") is True, "consumer cutover must remain active")
    require(comp.get("rollbackCompatibilityRetained") is True, "rollback compatibility must remain retained")
    composed = {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }
    parity = csha(composed) == csha(legacy_after)
    require(parity, "canonical tool-status composition is not parity-equal to legacy composite")

    audit, module = snapshot_tool_status_audit(args.source_commit)
    require(audit.get("retirement_preflight_clear") is True, "tool_status semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [], "tool_status semantic blockers remain")
    classes = audit.get("classes") or {}
    actual_safe = {}
    for rel, expected_class in EXPECTED_SAFE.items():
        actual_class = module.tool_status_safe_class(args.source_commit, rel)
        actual_safe[rel] = actual_class
        require(actual_class == expected_class, f"{rel}: safe classification drift ({actual_class!r})")
        require(rel in (classes.get(expected_class) or []), f"{rel}: audit class missing {expected_class}")

    policy_before = csha(git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix()))
    policy_after = csha(git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix()))
    require(policy_before == policy_after, "external-effect policy authority changed")

    criteria = {
        "prior_tool_status_consumer_migration_is_pass": True,
        "active_authority_legacy_references_are_zero": True,
        "canonical_composition_remains_exactly_parity_equal": parity,
        "legacy_tool_status_is_byte_unchanged": True,
        "six_remaining_machine_refs_are_content_validated_rollback_only": len(actual_safe) == 6,
        "tool_status_semantic_preflight_has_zero_blockers": True,
        "tool_status_active_authority_remains_instance_surface": True,
        "rollback_window_remains_open": True,
        "delete_authority_remains_false": True,
        "external_effect_authority_is_unchanged": True,
    }
    report = {
        "schema": "velvetos.stage8d-tool-status-semantic-correction.v1",
        "stage": "8D_TOOL_STATUS_SEMANTIC_CORRECTION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "surface_id": "tool_status",
        "legacy_path": LEGACY,
        "canonical_contract_path": CONTRACT,
        "canonical_state_path": STATE,
        "purpose": (
            "Prove the remaining TOOL-STATUS semantic references are rollback/parity/test metadata after "
            "active consumers were already migrated to instance:surface:toolStatus."
        ),
        "classification": {
            "content_validated_safe_references": actual_safe,
            "remaining_blockers": [],
            "retirement_preflight_clear": True,
        },
        "parity": {
            "canonical_composed_sha256": csha(composed),
            "legacy_sha256": csha(legacy_after),
            "equal": parity,
        },
        "rollback": {
            "window_open": True,
            "closure_evidence": None,
            "retirement_ready_for_deletion_gate": False,
            "delete_authorized": False,
        },
        "authority": {
            "active_authority": comp.get("activeAuthority"),
            "policy_registry_sha256": policy_after,
            "prepared_against_policy_registry_sha256": policy_before,
            "external_effect_authority_changed": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "retirement_authorized": False,
        "delete_authorized": False,
        "next_action": (
            "Merge this semantic correction and collect fresh downstream main evidence before explicit "
            "tool-status rollback closure. Remove rollback/parity metadata only in a later deletion gate."
        ),
        "constraints": [
            "legacy TOOL-STATUS remains present and byte-unchanged",
            "rollback window remains open",
            "no deletion in this change",
            "content validation must fail closed if any reviewed reference changes role",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "tool-status semantic correction criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION "
        f"assessment=PASS safe_refs={len(actual_safe)} blockers=0 parity={str(parity).lower()} delete_authorized=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
