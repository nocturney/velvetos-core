#!/usr/bin/env python3
"""Generate the isolated Stage 8D sample_profile deletion gate.

Evidence-only: authorizes deletion of exactly one compatibility file on a later
isolated PR. This gate does not delete the file and does not authorize any other
compatibility surface.
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
OUT = REPORTS / "stage8d-sample-profile-deletion-gate.json"
CLOSURE = REPORTS / "stage8d-sample-profile-rollback-reclosure.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL = "instances/velvet-factory/instance/velvet-factory.json"
PREPARED_MAIN = "495a6c91e8dea4b65dacf415be42aa22fc471ae4"
LATEST_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37277013397,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T07:18:29Z",
}
CLOSURES = {
    "sample_profile": "stage8d-sample-profile-rollback-reclosure.json",
    "root_desk": "stage8d-root-desk-rollback-closure.json",
    "fleet": "stage8d-fleet-rollback-closure.json",
    "tool_status": "stage8d-tool-status-rollback-closure.json",
    "chatgpt_core_bundle": "stage8d-chatgpt-rollback-closure.json",
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


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    proc = subprocess.run(["git", "hash-object", "--stdin"], cwd=ROOT, input=raw, capture_output=True)
    require(proc.returncode == 0, "git hash-object failed for sample restore anchor")
    value = proc.stdout.decode("ascii", errors="strict").strip()
    require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "invalid Git blob SHA")
    return value


def covered_by(legacy: Any, canonical: Any, path: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(legacy, dict):
        if not isinstance(canonical, dict):
            return [f"{path or '<root>'}: type mismatch"]
        for key, value in legacy.items():
            child = f"{path}.{key}" if path else key
            if key not in canonical:
                problems.append(f"{child}: missing")
            else:
                problems.extend(covered_by(value, canonical[key], child))
        return problems
    if isinstance(legacy, list):
        if not isinstance(canonical, list):
            return [f"{path}: type mismatch"]
        for idx, item in enumerate(legacy):
            if item not in canonical:
                problems.append(f"{path}[{idx}]: item missing")
        return problems
    if legacy != canonical:
        problems.append(f"{path}: value mismatch")
    return problems


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
    require(args.prepared_against == PREPARED_MAIN,
            "sample deletion gate must be generated against its verified exact main boundary")

    closure = git_json(args.prepared_against, CLOSURE.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(
        closure.get("schema") == "velvetos.stage8d-sample-profile-rollback-reclosure.v2"
        and closure.get("surface_id") == "sample_profile"
        and closure.get("repository_assessment") == "PASS"
        and closure.get("rollback_window_closed") is True
        and closure.get("retirement_ready_for_deletion_gate") is True
        and closure.get("delete_authorized") is False
        and closure.get("retirement_authorized") is False,
        "sample rollback re-closure is not a valid deletion-gate prerequisite",
    )
    closure_evidence = closure.get("current_evidence") or {}
    require(
        closure_evidence.get("runtime_authority") is False
        and closure_evidence.get("active_semantic_legacy_consumer_count") == 0
        and closure_evidence.get("semantic_preflight_clear") is True
        and closure_evidence.get("all_stage8d_semantic_preflights_clear") is True
        and closure_evidence.get("external_effect_authority_unchanged") is True,
        "sample re-closure current evidence drift",
    )

    cross_surface: dict[str, Any] = {}
    for surface_id, filename in CLOSURES.items():
        receipt = git_json(args.prepared_against, (REPORTS / filename).relative_to(ROOT).as_posix())
        row = {
            "repository_assessment": receipt.get("repository_assessment"),
            "rollback_window_closed": receipt.get("rollback_window_closed"),
            "retirement_ready_for_deletion_gate": receipt.get("retirement_ready_for_deletion_gate"),
            "delete_authorized": receipt.get("delete_authorized"),
            "retirement_authorized": receipt.get("retirement_authorized"),
        }
        cross_surface[surface_id] = row
        require(
            row["repository_assessment"] == "PASS"
            and row["rollback_window_closed"] is True
            and row["retirement_ready_for_deletion_gate"] is True
            and row["delete_authorized"] is False
            and row["retirement_authorized"] is False,
            f"{surface_id}: rollback closure prerequisite drift",
        )

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

    legacy_for_coverage = dict(legacy)
    require(legacy_for_coverage.pop("role", None) == "sample", "legacy sample role compatibility marker drift")
    legacy_notes = legacy_for_coverage.pop("notes", None)
    require(
        isinstance(legacy_notes, str)
        and "Reference profile hosted in VelvetOS Core for sensors/compat" in legacy_notes
        and "Live frontend office lives in instances/velvet-factory/" in legacy_notes,
        "legacy sample notes are not the expected compatibility-only metadata",
    )
    coverage_problems = covered_by(legacy_for_coverage, canonical)
    require(coverage_problems == [], "canonical instance does not semantically cover retained sample business/config fields: " + "; ".join(coverage_problems))
    require(set(legacy.get("modulesEnabled") or []) == set(canonical.get("modulesEnabled") or []),
            "canonical and legacy module sets diverged")

    raw = git_bytes(args.prepared_against, LEGACY)
    legacy_sha256 = hashlib.sha256(raw).hexdigest()
    blob_sha1 = git_blob_sha1(raw)
    require(len(raw) > 0, "sample compatibility file is unexpectedly empty")

    policy_sha = csha(policy)
    closure_authority = closure.get("authority") or {}
    require(
        policy_sha == closure_authority.get("policy_registry_sha256")
        and closure_authority.get("external_effect_authority_changed") is False,
        "external-effect policy authority changed since sample re-closure",
    )
    require(
        LATEST_MAIN_CI["sha"] == args.prepared_against
        and LATEST_MAIN_CI["conclusion"] == "success"
        and LATEST_MAIN_CI["event"] == "push",
        "latest main CI evidence is not bound to the prepared main SHA",
    )

    criteria = {
        "sample_reclosure_is_pass_and_closed": True,
        "sample_reclosure_is_ready_for_deletion_gate": True,
        "sample_reclosure_did_not_pre_authorize_deletion": True,
        "all_five_rollback_windows_are_closed_and_gate_ready": True,
        "all_other_surfaces_remain_deletion_unauthorized": True,
        "current_sample_semantic_preflight_is_clear": True,
        "current_global_semantic_preflight_is_5_of_5_clear": True,
        "active_semantic_sample_legacy_consumers_are_zero": True,
        "canonical_instance_semantically_covers_legacy_business_config_except_compat_metadata": True,
        "canonical_and_legacy_module_sets_match": True,
        "exact_legacy_blob_is_anchored_for_restore": True,
        "latest_exact_main_core_sensor_run_is_success": True,
        "external_effect_authority_is_unchanged": True,
        "gate_authorizes_only_sample_profile_target": True,
        "deletion_is_not_performed_in_gate_change": True,
        "retirement_completion_waits_for_separate_deletion_pr": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-deletion-gate.v1",
        "stage": "8D_SAMPLE_PROFILE_DELETION_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
        "target": {
            "legacy_path": LEGACY,
            "canonical_path": CANONICAL,
            "delete_exactly": [LEGACY],
            "delete_other_surfaces": False,
        },
        "purpose": (
            "Authorize one later isolated deletion of the sample_profile compatibility file after revalidating "
            "current main, semantic clearance, canonical coverage, rollback closure, restore evidence and policy "
            "authority. This gate performs no deletion."
        ),
        "prerequisite_closure": {
            "receipt": CLOSURE.relative_to(ROOT).as_posix(),
            "schema": closure.get("schema"),
            "rollback_window_closed": True,
            "retirement_ready_for_deletion_gate": True,
        },
        "cross_surface_state": cross_surface,
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_semantic_legacy_consumer_count": 0,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "compatibility_metadata_excluded_from_canonical_coverage": {"role": "sample", "notes": legacy_notes},
            "canonical_semantically_covers_legacy_business_config": True,
            "canonical_legacy_module_parity": True,
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
            "sample_reclosure_policy_registry_sha256": closure_authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
            "delete_authorized": True,
            "delete_authorized_surface": "sample_profile",
            "delete_authorized_paths": [LEGACY],
            "retirement_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this evidence-only gate, verify post-merge main, then create a separate isolated sample_profile "
            "deletion PR that removes exactly the authorized path and re-runs semantic, policy and full-suite checks."
        ),
        "constraints": [
            "this gate does not delete files",
            "authorization applies only to the exact sample_profile target recorded above",
            "no other Stage 8D compatibility surface is deletion-authorized by this receipt",
            "actual deletion requires a separate isolated PR",
            "restore anchor must remain available in Git history",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "sample deletion gate acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_PROFILE_DELETION_GATE "
        f"assessment=PASS delete_authorized=true path={LEGACY} "
        f"blob={blob_sha1[:12]} sha256={legacy_sha256[:12]} deletion_performed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
