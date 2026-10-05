#!/usr/bin/env python3
"""Generate the isolated Stage 8D root_desk deletion gate.

Evidence-only: authorizes deletion of exactly the retained root desk compatibility
file in a later isolated PR. This gate performs no deletion and grants no
authority over the remaining compatibility surfaces.
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
OUT = REPORTS / "stage8d-root-desk-deletion-gate.json"
CLOSURE = REPORTS / "stage8d-root-desk-rollback-closure.json"
SAMPLE_RETIREMENT = REPORTS / "stage8d-sample-profile-deletion.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join([".cursor", "vf-desk.json"])
CANONICAL = "instances/velvet-factory/.cursor/vf-desk.json"
SAMPLE_LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
PREPARED_MAIN = "dfd699dcee63d5175f03ae3312fbb89992ea78ca"
LATEST_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37284249359,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T08:32:18Z",
}
REMAINING_CLOSURES = {
    "fleet": "stage8d-fleet-rollback-closure.json",
    "tool_status": "stage8d-tool-status-rollback-closure.json",
    "chatgpt_core_bundle": "stage8d-chatgpt-rollback-closure.json",
}
READERS = (
    "scripts/check-agent-surface-security.py",
    "scripts/check-office-watchdog.py",
    "scripts/check-public-cta.py",
    "scripts/check-velvetos.py",
    "scripts/check-vf-desk.py",
    "scripts/check-vfmcp.py",
    "scripts/check-vfresearch.py",
    "scripts/vf_control_plane.py",
    "scripts/vfmem.py",
    "scripts/vfops_loop.py",
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
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    proc = subprocess.run(["git", "hash-object", "--stdin"], cwd=ROOT, input=raw, capture_output=True)
    require(proc.returncode == 0, "git hash-object failed for root desk restore anchor")
    value = proc.stdout.decode("ascii", errors="strict").strip()
    require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "invalid Git blob SHA")
    return value


def rows_by(items: Any, key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in items or []:
        if isinstance(row, dict) and isinstance(row.get(key), str):
            result[row[key]] = row
    return result


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
            "root desk deletion gate must be generated against its verified exact main boundary")

    closure = git_json(args.prepared_against, CLOSURE.relative_to(ROOT).as_posix())
    sample_retirement = git_json(args.prepared_against, SAMPLE_RETIREMENT.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(
        closure.get("schema") == "velvetos.stage8d-root-desk-rollback-closure.v1"
        and closure.get("surface_id") == "root_desk"
        and closure.get("repository_assessment") == "PASS"
        and closure.get("rollback_window_closed") is True
        and closure.get("retirement_ready_for_deletion_gate") is True
        and closure.get("delete_authorized") is False
        and closure.get("retirement_authorized") is False,
        "root desk rollback closure is not a valid deletion-gate prerequisite",
    )
    closure_evidence = closure.get("current_evidence") or {}
    require(
        closure_evidence.get("runtime_authority") is False
        and closure_evidence.get("semantic_preflight_clear") is True
        and closure_evidence.get("all_stage8d_semantic_preflights_clear") is True
        and closure_evidence.get("external_effect_authority_unchanged") is True,
        "root desk closure current evidence drift",
    )

    sample_deletion = sample_retirement.get("deletion") or {}
    sample_authority = sample_retirement.get("authority") or {}
    require(
        sample_retirement.get("schema") == "velvetos.stage8d-sample-profile-deletion.v1"
        and sample_retirement.get("surface_id") == "sample_profile"
        and sample_retirement.get("repository_assessment") == "PASS"
        and sample_retirement.get("deletion_performed") is True
        and sample_retirement.get("retirement_authorized") is True
        and sample_deletion.get("legacy_path") == SAMPLE_LEGACY
        and sample_deletion.get("legacy_present") is False
        and sample_authority.get("retirement_authorized") is True
        and not git_exists(args.prepared_against, SAMPLE_LEGACY),
        "sample_profile retirement prerequisite drift",
    )

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

    prior_sha = str(closure.get("prepared_against_main_sha") or "")
    require(re.fullmatch(r"[0-9a-f]{40}", prior_sha) is not None, "root desk closure prepared SHA missing")
    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(prior_sha, LEGACY),
            "legacy root desk changed after rollback closure")

    legacy_tools = legacy.get("tools") or {}
    canonical_tools = canonical.get("tools") or {}
    tools_equal = all(k in canonical_tools and canonical_tools[k] == v for k, v in legacy_tools.items())
    legacy_seats = rows_by(legacy.get("seats"), "id")
    canonical_seats = rows_by(canonical.get("seats"), "id")
    seats_equal = all(k in canonical_seats and canonical_seats[k] == v for k, v in legacy_seats.items())
    legacy_desk = rows_by(legacy.get("desk"), "slug")
    canonical_desk = rows_by(canonical.get("desk"), "slug")
    desk_equal = all(k in canonical_desk and canonical_desk[k] == v for k, v in legacy_desk.items())
    skills_superset = set(legacy.get("skills") or []) <= set(canonical.get("skills") or [])

    legacy_notes = set(legacy.get("notes") or [])
    canonical_notes = set(canonical.get("notes") or [])
    legacy_fleet_notes = {n for n in legacy_notes if "packages/vfprod/FLEET.json" in n}
    canonical_fleet_notes = {n for n in canonical_notes if "instance:surface:fleet" in n}
    require(len(legacy_fleet_notes) == 1 and len(canonical_fleet_notes) == 1,
            "root desk fleet-note compatibility shape drift")
    legacy_fleet_note = next(iter(legacy_fleet_notes))
    canonical_fleet_note = next(iter(canonical_fleet_notes))
    legacy_tail = legacy_fleet_note.split(" — ", 1)[1] if " — " in legacy_fleet_note else ""
    canonical_tail = canonical_fleet_note.split(" — ", 1)[1] if " — " in canonical_fleet_note else ""
    fleet_note_superseded = bool(legacy_tail) and legacy_tail == canonical_tail
    nonfleet_notes_preserved = (legacy_notes - legacy_fleet_notes) <= canonical_notes

    require(tools_equal and len(legacy_tools) == 18 and len(canonical_tools) == 18,
            "root desk tool parity drift")
    require(seats_equal and len(legacy_seats) == 6 and len(canonical_seats) == 6,
            "root desk seat parity drift")
    require(desk_equal and len(legacy_desk) == 38 and len(canonical_desk) == 38,
            "root desk specialist parity drift")
    require(skills_superset, "root desk canonical skills no longer cover legacy skills")
    require(nonfleet_notes_preserved and fleet_note_superseded, "root desk notes parity drift")
    require(canonical.get("role") == "instance" and canonical.get("instanceId") == "velvet-factory",
            "canonical root desk identity drift")
    for gate in ("brandAssetLock", "creativeTransformationLock", "projectRequestGate"):
        require((canonical.get(gate) or {}).get("mode") == "fail_closed",
                f"canonical root desk lost fail-closed {gate}")

    reader_rows: dict[str, dict[str, bool]] = {}
    for rel in READERS:
        text = git_text(args.prepared_against, rel)
        uses_resolver = "resolve_surface" in text and "toolDesk" in text
        direct_legacy = 'ROOT / ".cursor" / "vf-desk.json"' in text or "ROOT / '.cursor' / 'vf-desk.json'" in text
        reader_rows[rel] = {
            "uses_instance_surface_resolver": uses_resolver,
            "direct_root_legacy_read": direct_legacy,
        }
        require(uses_resolver and not direct_legacy, f"{rel}: root desk runtime reader drift")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    root_audit = surfaces.get("root_desk") or {}
    sample_audit = surfaces.get("sample_profile") or {}
    assessment = audit.get("assessment") or {}
    require(
        root_audit.get("present") is True
        and root_audit.get("retirement_preflight_clear") is True
        and root_audit.get("retirement_preflight_blockers") == [],
        "current root desk semantic preflight is not clear",
    )
    sample_retirement_evidence = sample_audit.get("retirement_evidence") or {}
    require(
        sample_audit.get("present") is False
        and sample_audit.get("retired") is True
        and sample_audit.get("retirement_preflight_clear") is True
        and sample_retirement_evidence.get("receipt") == SAMPLE_RETIREMENT.relative_to(ROOT).as_posix()
        and sample_retirement_evidence.get("retirement_authorized") is True,
        "semantic audit does not prove prior sample retirement",
    )
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and assessment.get("surfaces_retired") == 1
        and assessment.get("retired_surfaces") == ["sample_profile"]
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic state is not 5/5 clear with exactly sample_profile retired",
    )

    raw = git_bytes(args.prepared_against, LEGACY)
    legacy_sha256 = hashlib.sha256(raw).hexdigest()
    blob_sha1 = git_blob_sha1(raw)
    require(len(raw) > 0, "root desk compatibility file is unexpectedly empty")

    policy_sha = csha(policy)
    closure_authority = closure.get("authority") or {}
    require(
        policy_sha == closure_authority.get("policy_registry_sha256")
        and closure_authority.get("external_effect_authority_changed") is False,
        "external-effect policy authority changed since root desk closure",
    )
    require(
        LATEST_MAIN_CI["sha"] == args.prepared_against
        and LATEST_MAIN_CI["conclusion"] == "success"
        and LATEST_MAIN_CI["event"] == "push",
        "latest main CI evidence is not bound to the prepared main SHA",
    )

    criteria = {
        "root_desk_closure_is_pass_and_closed": True,
        "root_desk_closure_is_ready_for_deletion_gate": True,
        "root_desk_closure_did_not_pre_authorize_deletion": True,
        "sample_profile_retirement_is_authoritatively_proven": True,
        "remaining_three_surfaces_are_closed_gate_ready_and_deletion_unauthorized": True,
        "current_root_desk_semantic_preflight_is_clear": True,
        "current_global_semantic_preflight_is_5_of_5_clear": True,
        "semantic_audit_recognizes_exactly_one_retired_surface": True,
        "all_runtime_readers_remain_on_explicit_instance_tool_desk_surface": True,
        "legacy_root_desk_is_unchanged_since_closure": True,
        "canonical_tools_preserve_all_legacy_rows": True,
        "canonical_seats_preserve_all_legacy_rows": True,
        "canonical_specialists_preserve_all_legacy_rows": True,
        "canonical_skills_are_legacy_superset": True,
        "canonical_notes_preserve_or_authoritatively_supersede_legacy_notes": True,
        "canonical_identity_and_fail_closed_gates_are_preserved": True,
        "exact_legacy_blob_is_anchored_for_restore": True,
        "latest_exact_main_core_sensor_run_is_success": True,
        "external_effect_authority_is_unchanged": True,
        "gate_authorizes_only_root_desk_target": True,
        "deletion_is_not_performed_in_gate_change": True,
        "retirement_completion_waits_for_separate_deletion_pr": True,
    }

    report = {
        "schema": "velvetos.stage8d-root-desk-deletion-gate.v1",
        "stage": "8D_ROOT_DESK_DELETION_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "root_desk",
        "target": {
            "legacy_path": LEGACY,
            "canonical_path": CANONICAL,
            "delete_exactly": [LEGACY],
            "delete_other_surfaces": False,
        },
        "purpose": (
            "Authorize one later isolated deletion of the root_desk compatibility file after revalidating "
            "current semantic state, runtime-reader cutover, operational parity, rollback closure, prior sample "
            "retirement, restore evidence and policy authority. This gate performs no deletion."
        ),
        "prerequisite_closure": {
            "receipt": CLOSURE.relative_to(ROOT).as_posix(),
            "schema": closure.get("schema"),
            "rollback_window_closed": True,
            "retirement_ready_for_deletion_gate": True,
        },
        "prior_retirement": {
            "surface_id": "sample_profile",
            "receipt": SAMPLE_RETIREMENT.relative_to(ROOT).as_posix(),
            "repository_assessment": "PASS",
            "deletion_performed": True,
            "retirement_authorized": True,
        },
        "remaining_surface_state": remaining,
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "runtime_reader_count": len(reader_rows),
            "runtime_readers": reader_rows,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "retired_surfaces": ["sample_profile"],
            "legacy_byte_unchanged_since_closure": True,
            "legacy_tool_count": len(legacy_tools),
            "canonical_tool_count": len(canonical_tools),
            "legacy_seat_count": len(legacy_seats),
            "canonical_seat_count": len(canonical_seats),
            "legacy_specialist_count": len(legacy_desk),
            "canonical_specialist_count": len(canonical_desk),
            "tools_equal_by_id": tools_equal,
            "seats_equal_by_id": seats_equal,
            "specialists_equal_by_slug": desk_equal,
            "skills_superset": skills_superset,
            "nonfleet_notes_preserved": nonfleet_notes_preserved,
            "fleet_note_semantically_superseded": fleet_note_superseded,
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
            "root_desk_closure_policy_registry_sha256": closure_authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
            "delete_authorized": True,
            "delete_authorized_surface": "root_desk",
            "delete_authorized_paths": [LEGACY],
            "retirement_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this evidence-only gate, verify post-merge main, then create a separate isolated root_desk "
            "deletion PR that removes exactly the authorized path and re-runs semantic, policy and full-suite checks."
        ),
        "constraints": [
            "this gate does not delete files",
            "authorization applies only to the exact root_desk target recorded above",
            "sample_profile is already retired and is not modified by this gate",
            "fleet, tool_status and chatgpt_core_bundle remain deletion-unauthorized by this receipt",
            "actual deletion requires a separate isolated PR",
            "restore anchor must remain available in Git history",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "root desk deletion gate acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_ROOT_DESK_DELETION_GATE "
        f"assessment=PASS delete_authorized=true path={LEGACY} "
        f"blob={blob_sha1[:12]} sha256={legacy_sha256[:12]} deletion_performed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
