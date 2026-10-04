#!/usr/bin/env python3
"""Generate Stage 8D corrective evidence for fleet runtime consumers."""
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
OUT = REPORTS / "stage8d-fleet-runtime-consumer-correction.json"
PRIOR = REPORTS / "stage8d-fleet-consumer-migration.json"
BASE_AUDIT = REPORTS / "stage8d-retirement-semantic-audit.json"
ROOT_DESK_CORRECTION = REPORTS / "stage8d-root-desk-runtime-consumer-correction.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"

LEGACY = "packages/vfprod/FLEET.json"
CANONICAL = "instances/velvet-factory/instance/fleet.json"
ROOT_DESK = ".cursor/vf-desk.json"
CANONICAL_DESK = "instances/velvet-factory/.cursor/vf-desk.json"
MIGRATED_CODE = (
    "scripts/vfprod.py",
    "scripts/check-vfprod.py",
    "scripts/vf_living_studio.py",
    "scripts/check-velvetos.py",
)
NEGATIVE_CONTROLS = (
    "packages/velvetos/living-studio/tests/test_living_studio.py",
    "packages/velvetos_control_api/tests/test_control_api.py",
)
DOC_EXPECTATIONS = {
    "docs/chief-of-staff/SOT-INDEX.md": CANONICAL,
    "docs/chief-of-staff/PACKS-CATALOG.md": "instance:surface:fleet",
    "docs/chief-of-staff/SYSTEM-MAP.md": "instance:surface:fleet",
    "packages/manifest.json": "instance:surface:fleet",
    "packages/vfprod/FLOOR.md": "instance:surface:fleet",
    "packages/vfprod/ROUTING.md": "instance:surface:fleet",
    CANONICAL_DESK: "instance:surface:fleet",
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
    require(isinstance(value, dict), f"{rel}@{sha} must contain an object")
    return value


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def semantic_legacy_ref(text: str) -> bool:
    low = text.lower().replace("\\", "/")
    return LEGACY.lower() in low or (
        "packages" in low and "vfprod" in low and "fleet.json" in low
    )


def snapshot_fleet_audit(sha: str) -> dict[str, Any]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_retirement_semantic_audit_fleet_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "fleet")
    require(isinstance(row, dict), "snapshot fleet semantic audit did not return an object")
    return row


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
        "source commit must descend from prepared-against main",
    )

    prior = git_json(args.prepared_against, PRIOR.relative_to(ROOT).as_posix())
    base_audit = git_json(args.prepared_against, BASE_AUDIT.relative_to(ROOT).as_posix())
    root_fix = git_json(args.source_commit, ROOT_DESK_CORRECTION.relative_to(ROOT).as_posix())
    require(prior.get("repository_acceptance") == "PASS", "prior fleet migration receipt must PASS")
    require((prior.get("rollback") or {}).get("window_open") is True, "prior fleet rollback window must be open")
    require((prior.get("rollback") or {}).get("delete_authorized") is False, "prior fleet delete authority drift")
    require(
        root_fix.get("repository_assessment") == "PASS"
        and (root_fix.get("semantic_audit") or {}).get("retirement_preflight_clear") is True
        and root_fix.get("delete_authorized") is False,
        "root-desk correction dependency is not satisfied",
    )

    base_fleet = (base_audit.get("compatibility_surfaces") or {}).get("fleet") or {}
    base_blockers = set(base_fleet.get("retirement_preflight_blockers") or [])
    expected_runtime = set(MIGRATED_CODE)
    require(expected_runtime <= base_blockers, f"base audit no longer exposes fleet runtime blockers: {sorted(base_blockers)}")

    for rel in MIGRATED_CODE:
        text = git_text(args.source_commit, rel)
        require(not semantic_legacy_ref(text), f"{rel} still semantically references legacy fleet")
        require("resolve_surface" in text or "canonical_fleet_path" in text, f"{rel} is not canonical-fleet bound")

    canonical = git_json(args.source_commit, CANONICAL)
    legacy = git_json(args.source_commit, LEGACY)
    parity = csha(canonical) == csha(legacy)
    require(parity, "canonical/legacy fleet parity changed")
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(args.source_commit, LEGACY),
            "legacy fleet changed during corrective migration")
    require(git_bytes(args.prepared_against, ROOT_DESK) == git_bytes(args.source_commit, ROOT_DESK),
            "root-desk rollback surface changed during fleet correction")

    docs_proof: dict[str, bool] = {}
    for rel, needle in DOC_EXPECTATIONS.items():
        text = git_text(args.source_commit, rel)
        docs_proof[rel] = needle in text
        require(docs_proof[rel], f"active fleet surface not canonicalized: {rel}")

    audit = snapshot_fleet_audit(args.source_commit)
    classes = audit.get("classes") or {}
    require(sorted(classes.get("negative_control") or []) == sorted(NEGATIVE_CONTROLS),
            "fleet negative-control classification drift")
    require(classes.get("retained_legacy_surface_reference") == [ROOT_DESK],
            "root desk must be the only retained cross-surface fleet reference")
    require(audit.get("retirement_preflight_clear") is True, "fleet semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [], "fleet semantic blockers remain")

    policy_before = csha(git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix()))
    policy_after = csha(git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix()))
    require(policy_before == policy_after, "external-effect policy authority changed")

    criteria = {
        "prior_fleet_migration_receipt_is_preserved": True,
        "semantic_audit_exposed_remaining_runtime_consumers": True,
        "all_live_fleet_readers_use_canonical_instance_surface": True,
        "active_fleet_documentation_uses_canonical_surface": True,
        "canonical_and_legacy_fleet_remain_parity_equal": parity,
        "legacy_fleet_is_byte_unchanged": True,
        "root_desk_rollback_surface_is_byte_unchanged": True,
        "root_desk_correction_dependency_is_satisfied": True,
        "legacy_path_test_assertions_are_explicit_negative_controls": True,
        "retained_root_desk_reference_is_receipt_gated_not_runtime_authority": True,
        "semantic_preflight_has_zero_fleet_blockers": True,
        "fleet_rollback_window_remains_open": True,
        "fleet_delete_authority_remains_false": True,
        "external_effect_authority_is_unchanged": True,
    }

    report = {
        "schema": "velvetos.stage8d-fleet-runtime-consumer-correction.v2",
        "stage": "8D_FLEET_RUNTIME_CONSUMER_CORRECTION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "surface_id": "fleet",
        "legacy_path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Complete fleet runtime/documentation cutover exposed by the fail-closed semantic audit, "
            "while retaining the parity-equal fleet compatibility file and keeping rollback open."
        ),
        "migration": {
            "migrated_code": list(MIGRATED_CODE),
            "runtime_consumers_migrated": True,
            "active_documentation": docs_proof,
            "legacy_present": True,
            "legacy_byte_unchanged": True,
            "canonical_legacy_parity": parity,
        },
        "semantic_audit": {
            "base_blockers": sorted(base_blockers),
            "negative_controls": list(NEGATIVE_CONTROLS),
            "retained_legacy_surface_references": [ROOT_DESK],
            "remaining_blockers": [],
            "retirement_preflight_clear": True,
            "root_desk_dependency_receipt": ROOT_DESK_CORRECTION.relative_to(ROOT).as_posix(),
        },
        "rollback": {
            "window_open": True,
            "closure_evidence": None,
            "retirement_ready_for_deletion_gate": False,
            "delete_authorized": False,
        },
        "authority": {
            "policy_registry_sha256": policy_after,
            "prepared_against_policy_registry_sha256": policy_before,
            "external_effect_authority_changed": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "retirement_authorized": False,
        "delete_authorized": False,
        "next_action": (
            "Merge this correction, verify downstream main, then collect explicit fresh evidence for fleet "
            "rollback-window closure. Do not delete packages/vfprod/FLEET.json in this change."
        ),
        "constraints": [
            "no fleet legacy deletion in this change",
            "no fleet rollback-window closure in this change",
            "cross-surface compatibility classification requires a passing root-desk correction receipt",
            "negative controls do not count as live consumers",
            "no big-bang retirement",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "fleet corrective acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_FLEET_RUNTIME_CORRECTION "
        f"assessment={report['repository_assessment']} blockers=0 parity={str(parity).lower()} "
        f"delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
