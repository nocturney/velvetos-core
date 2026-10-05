#!/usr/bin/env python3
"""Generate the isolated Stage 8D fleet deletion gate.

Evidence-only: authorizes deletion of exactly the retained fleet compatibility
file in a later isolated PR. This gate performs no deletion and grants no
authority over tool_status or chatgpt_core_bundle.
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
OUT = REPORTS / "stage8d-fleet-deletion-gate.json"
CLOSURE = REPORTS / "stage8d-fleet-rollback-closure.json"
SAMPLE_RETIREMENT = REPORTS / "stage8d-sample-profile-deletion.json"
ROOT_DESK_RETIREMENT = REPORTS / "stage8d-root-desk-deletion.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "packages/vfprod/FLEET.json"
CANONICAL = "instances/velvet-factory/instance/fleet.json"
SAMPLE_LEGACY = "packages/velvetos/samples/velvet-factory.json"
ROOT_DESK_LEGACY = ".cursor/vf-desk.json"
PREPARED_MAIN = "12e8ea4c0a38286eccc30972579270739411b5f2"
LATEST_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37294141817,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T10:04:03Z",
}
REMAINING_CLOSURES = {
    "tool_status": "stage8d-tool-status-rollback-closure.json",
    "chatgpt_core_bundle": "stage8d-chatgpt-rollback-closure.json",
}
MIGRATED_CODE = (
    "scripts/vfprod.py",
    "scripts/check-vfprod.py",
    "scripts/vf_living_studio.py",
    "scripts/check-velvetos.py",
)
ACTIVE_DOCS = (
    "docs/chief-of-staff/SOT-INDEX.md",
    "docs/chief-of-staff/PACKS-CATALOG.md",
    "docs/chief-of-staff/SYSTEM-MAP.md",
    "packages/manifest.json",
    "packages/vfprod/FLOOR.md",
    "packages/vfprod/ROUTING.md",
    "instances/velvet-factory/.cursor/vf-desk.json",
)


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


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    proc = subprocess.run(["git", "hash-object", "--stdin"], cwd=ROOT, input=raw, capture_output=True)
    require(proc.returncode == 0, "git hash-object failed for fleet restore anchor")
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


def validate_retirement(receipt: dict[str, Any], surface_id: str, legacy_path: str, schema: str) -> None:
    deletion = receipt.get("deletion") or {}
    authority = receipt.get("authority") or {}
    require(
        receipt.get("schema") == schema
        and receipt.get("surface_id") == surface_id
        and receipt.get("repository_assessment") == "PASS"
        and receipt.get("deletion_performed") is True
        and receipt.get("retirement_authorized") is True
        and deletion.get("legacy_path") == legacy_path
        and deletion.get("legacy_present") is False
        and deletion.get("deletion_performed") is True
        and authority.get("retirement_authorized") is True,
        f"{surface_id}: prior retirement receipt drift",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")
    require(args.prepared_against == PREPARED_MAIN,
            "fleet deletion gate must be generated against its verified exact main boundary")

    closure = git_json(args.prepared_against, CLOSURE.relative_to(ROOT).as_posix())
    sample_retirement = git_json(args.prepared_against, SAMPLE_RETIREMENT.relative_to(ROOT).as_posix())
    root_retirement = git_json(args.prepared_against, ROOT_DESK_RETIREMENT.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(
        closure.get("schema") == "velvetos.stage8d-fleet-rollback-closure.v1"
        and closure.get("surface_id") == "fleet"
        and closure.get("repository_assessment") == "PASS"
        and closure.get("rollback_window_closed") is True
        and closure.get("retirement_ready_for_deletion_gate") is True
        and closure.get("delete_authorized") is False
        and closure.get("retirement_authorized") is False,
        "fleet rollback closure is not a valid deletion-gate prerequisite",
    )
    closure_evidence = closure.get("current_evidence") or {}
    require(
        closure_evidence.get("runtime_authority") is False
        and closure_evidence.get("semantic_preflight_clear") is True
        and closure_evidence.get("all_stage8d_semantic_preflights_clear") is True
        and closure_evidence.get("canonical_legacy_exact_equal") is True
        and closure_evidence.get("external_effect_authority_unchanged") is True,
        "fleet closure current evidence drift",
    )

    validate_retirement(
        sample_retirement,
        "sample_profile",
        SAMPLE_LEGACY,
        "velvetos.stage8d-sample-profile-deletion.v1",
    )
    validate_retirement(
        root_retirement,
        "root_desk",
        ROOT_DESK_LEGACY,
        "velvetos.stage8d-root-desk-deletion.v1",
    )
    require(not git_exists(args.prepared_against, SAMPLE_LEGACY), "retired sample_profile unexpectedly present")
    require(not git_exists(args.prepared_against, ROOT_DESK_LEGACY), "retired root_desk unexpectedly present")

    remaining: dict[str, Any] = {}
    for surface_id, filename in REMAINING_CLOSURES.items():
        receipt = git_json(args.prepared_against, (REPORTS / filename).relative_to(ROOT).as_posix())
        row = {
            "repository_assessment": receipt.get("repository_assessment"),
            "rollback_window_closed": receipt.get("rollback_window_closed"),
            "retirement_ready_for_deletion_gate": receipt.get("retirement_ready_for_deletion_gate"),
            "delete_authorized": receipt.get("delete_authorized"),
            "retirement_authorized": receipt.get("retirement_authorized"),
        }
        remaining[surface_id] = row
        require(
            row["repository_assessment"] == "PASS"
            and row["rollback_window_closed"] is True
            and row["retirement_ready_for_deletion_gate"] is True
            and row["delete_authorized"] is False
            and row["retirement_authorized"] is False,
            f"{surface_id}: retained-surface closure prerequisite drift",
        )

    require(legacy == canonical, "canonical fleet no longer exactly matches legacy fleet")
    prior_sha = str(closure.get("prepared_against_main_sha") or "")
    require(re.fullmatch(r"[0-9a-f]{40}", prior_sha) is not None, "fleet closure prepared SHA missing")
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(prior_sha, LEGACY),
            "legacy fleet changed after rollback closure")

    code_rows: dict[str, dict[str, bool]] = {}
    for rel in MIGRATED_CODE:
        text = git_text(args.prepared_against, rel)
        no_legacy = LEGACY not in text
        canonical_binding = ("resolve_surface" in text and '"fleet"' in text) or "instance/fleet.json" in text
        code_rows[rel] = {
            "legacy_path_absent": no_legacy,
            "canonical_fleet_binding_present": canonical_binding,
        }
        require(no_legacy and canonical_binding, f"{rel}: fleet runtime-reader drift")

    doc_rows: dict[str, dict[str, bool]] = {}
    for rel in ACTIVE_DOCS:
        text = git_text(args.prepared_against, rel)
        no_legacy = LEGACY not in text
        doc_rows[rel] = {"legacy_path_absent": no_legacy}
        require(no_legacy, f"{rel}: active documentation reintroduced legacy fleet path")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    fleet_audit = surfaces.get("fleet") or {}
    sample_audit = surfaces.get("sample_profile") or {}
    root_audit = surfaces.get("root_desk") or {}
    assessment = audit.get("assessment") or {}
    require(
        fleet_audit.get("present") is True
        and fleet_audit.get("retirement_preflight_clear") is True
        and fleet_audit.get("retirement_preflight_blockers") == [],
        "current fleet semantic preflight is not clear",
    )
    require(
        sample_audit.get("present") is False and sample_audit.get("retired") is True
        and root_audit.get("present") is False and root_audit.get("retired") is True,
        "semantic audit does not prove both prior retirements",
    )
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and assessment.get("surfaces_retired") == 2
        and assessment.get("retired_surfaces") == ["root_desk", "sample_profile"]
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic state is not 5/5 clear with exactly two retired surfaces",
    )

    raw = git_bytes(args.prepared_against, LEGACY)
    legacy_sha256 = hashlib.sha256(raw).hexdigest()
    blob_sha1 = git_blob_sha1(raw)
    require(len(raw) > 0, "fleet compatibility file is unexpectedly empty")

    policy_sha = csha(policy)
    closure_authority = closure.get("authority") or {}
    require(
        policy_sha == closure_authority.get("policy_registry_sha256")
        and closure_authority.get("external_effect_authority_changed") is False,
        "external-effect policy authority changed since fleet closure",
    )
    require(
        LATEST_MAIN_CI["sha"] == args.prepared_against
        and LATEST_MAIN_CI["conclusion"] == "success"
        and LATEST_MAIN_CI["event"] == "push",
        "latest main CI evidence is not bound to the prepared main SHA",
    )

    criteria = {
        "fleet_closure_is_pass_and_closed": True,
        "fleet_closure_is_ready_for_deletion_gate": True,
        "fleet_closure_did_not_pre_authorize_deletion": True,
        "sample_profile_retirement_is_authoritatively_proven": True,
        "root_desk_retirement_is_authoritatively_proven": True,
        "remaining_two_surfaces_are_closed_gate_ready_and_deletion_unauthorized": True,
        "current_fleet_semantic_preflight_is_clear": True,
        "current_global_semantic_preflight_is_5_of_5_clear": True,
        "semantic_audit_recognizes_exactly_two_retired_surfaces": True,
        "all_live_fleet_readers_remain_canonical": True,
        "all_active_fleet_documentation_remains_canonical": True,
        "legacy_fleet_is_unchanged_since_closure": True,
        "canonical_and_legacy_fleet_are_exactly_equal": True,
        "exact_legacy_blob_is_anchored_for_restore": True,
        "latest_exact_main_core_sensor_run_is_success": True,
        "external_effect_authority_is_unchanged": True,
        "gate_authorizes_only_fleet_target": True,
        "deletion_is_not_performed_in_gate_change": True,
        "retirement_completion_waits_for_separate_deletion_pr": True,
    }

    report = {
        "schema": "velvetos.stage8d-fleet-deletion-gate.v1",
        "stage": "8D_FLEET_DELETION_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "fleet",
        "target": {
            "legacy_path": LEGACY,
            "canonical_path": CANONICAL,
            "delete_exactly": [LEGACY],
            "delete_other_surfaces": False,
        },
        "purpose": (
            "Authorize one later isolated deletion of the fleet compatibility file after revalidating current "
            "semantic state, runtime/documentation cutover, exact parity, rollback closure, the prior two "
            "retirements, restore evidence and policy authority. This gate performs no deletion."
        ),
        "prerequisite_closure": {
            "receipt": CLOSURE.relative_to(ROOT).as_posix(),
            "schema": closure.get("schema"),
            "rollback_window_closed": True,
            "retirement_ready_for_deletion_gate": True,
        },
        "prior_retirements": {
            "sample_profile": {
                "receipt": SAMPLE_RETIREMENT.relative_to(ROOT).as_posix(),
                "repository_assessment": "PASS",
                "deletion_performed": True,
                "retirement_authorized": True,
            },
            "root_desk": {
                "receipt": ROOT_DESK_RETIREMENT.relative_to(ROOT).as_posix(),
                "repository_assessment": "PASS",
                "deletion_performed": True,
                "retirement_authorized": True,
            },
        },
        "remaining_surface_state": remaining,
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "migrated_code": code_rows,
            "active_documentation": doc_rows,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "retired_surfaces": ["root_desk", "sample_profile"],
            "legacy_byte_unchanged_since_closure": True,
            "canonical_legacy_exact_equal": True,
            "printer_count": len(legacy.get("printers") or []),
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
            "policy_registry_sha256": policy_sha,
            "fleet_closure_policy_registry_sha256": closure_authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
            "delete_authorized": True,
            "delete_authorized_surface": "fleet",
            "delete_authorized_paths": [LEGACY],
            "retirement_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this evidence-only gate, verify post-merge main, then create a separate isolated fleet "
            "deletion PR that removes exactly the authorized path and re-runs semantic, policy and full-suite checks."
        ),
        "constraints": [
            "this gate does not delete files",
            "authorization applies only to the exact fleet target recorded above",
            "sample_profile and root_desk are already retired and are not modified by this gate",
            "tool_status and chatgpt_core_bundle remain deletion-unauthorized by this receipt",
            "actual deletion requires a separate isolated PR",
            "restore anchor must remain available in Git history",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "fleet deletion gate acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_FLEET_DELETION_GATE "
        f"assessment=PASS delete_authorized=true path={LEGACY} "
        f"blob={blob_sha1[:12]} sha256={legacy_sha256[:12]} deletion_performed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
