#!/usr/bin/env python3
"""Generate Stage 8D root-desk rollback-window closure evidence.

Evidence-only. This closes the root_desk observation window after the runtime
consumer correction. It retains the compatibility desk and does not authorize
deletion.
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
OUT = REPORTS / "stage8d-root-desk-rollback-closure.json"
CORRECTION = REPORTS / "stage8d-root-desk-runtime-consumer-correction.json"
FLEET_CORRECTION = REPORTS / "stage8d-fleet-runtime-consumer-correction.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY = "/".join([".cursor", "vf-desk.json"])
CANONICAL = "instances/velvet-factory/.cursor/vf-desk.json"
CORRECTION_PR = 533
CORRECTION_MERGE_SHA = "a6f74bcd3fe9cd9b4c116df1dbc2a06b09519634"

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

OBSERVATION_RUNS = [
    {"id": 37234390255, "sha": "a6f74bcd3fe9cd9b4c116df1dbc2a06b09519634", "created_at": "2026-10-04T21:01:38Z", "event": "push", "conclusion": "success"},
    {"id": 37261424137, "sha": "027700b3077bc900658313186e313772f539bd7d", "created_at": "2026-10-05T03:56:40Z", "event": "push", "conclusion": "success"},
    {"id": 37262173012, "sha": "ed183f59959b4eaebd5a092e61d4ef969e834df7", "created_at": "2026-10-05T04:07:50Z", "event": "push", "conclusion": "success"},
    {"id": 37263663917, "sha": "adf1b3195951ca00f0f1d976fa06523c7e90b069", "created_at": "2026-10-05T04:28:24Z", "event": "push", "conclusion": "success"},
    {"id": 37267662064, "sha": "b722f622dd2eab031c087fe051c56a5eb019d705", "created_at": "2026-10-05T05:24:39Z", "event": "push", "conclusion": "success"},
    {"id": 37269082934, "sha": "e3a91cabcfdd2a145cdb79339ffc8a68c724a18a", "created_at": "2026-10-05T05:44:01Z", "event": "push", "conclusion": "success"},
    {"id": 37269731921, "sha": "8aa691f9ece02c50838ed11b64d5cde5528fb75c", "created_at": "2026-10-05T05:52:53Z", "event": "workflow_dispatch", "conclusion": "success", "additional_successful_run_ids": [37269817015]},
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


def rows_by(items: Any, key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in items or []:
        if isinstance(row, dict) and isinstance(row.get(key), str):
            out[row[key]] = row
    return out


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
            "prepared-against main does not descend from the root-desk correction")

    correction = git_json(args.prepared_against, CORRECTION.relative_to(ROOT).as_posix())
    fleet_correction = git_json(args.prepared_against, FLEET_CORRECTION.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(args.prepared_against, CANONICAL)

    require(correction.get("repository_assessment") == "PASS",
            "root-desk runtime correction must PASS")
    require(correction.get("surface_id") == "root_desk", "root-desk correction surface drift")
    rollback_fix = correction.get("rollback") or {}
    require(
        rollback_fix.get("window_open") is True
        and rollback_fix.get("closure_evidence") is None
        and rollback_fix.get("retirement_ready_for_deletion_gate") is False
        and rollback_fix.get("delete_authorized") is False,
        "root-desk correction rollback baseline drift",
    )

    migration = correction.get("migration") or {}
    require(migration.get("runtime_consumers_migrated") is True, "root-desk consumers not migrated")
    require(migration.get("legacy_present") is True, "root-desk legacy baseline missing")
    require(migration.get("legacy_byte_unchanged") is True, "root-desk correction changed legacy bytes")

    require(git_bytes(args.prepared_against, LEGACY) == git_bytes(CORRECTION_MERGE_SHA, LEGACY),
            "legacy root desk changed after correction")

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
    preserved_nonfleet_notes = (legacy_notes - legacy_fleet_notes) <= canonical_notes
    require(len(legacy_fleet_notes) == 1, "legacy root desk fleet note count drift")
    require(len(canonical_fleet_notes) == 1, "canonical root desk fleet note count drift")
    legacy_fleet_note = next(iter(legacy_fleet_notes))
    canonical_fleet_note = next(iter(canonical_fleet_notes))
    require(" + ROUTING.md" in legacy_fleet_note, "legacy fleet note shape drift")
    require(" + packages/vfprod/ROUTING.md" in canonical_fleet_note, "canonical fleet note shape drift")
    legacy_tail = legacy_fleet_note.split(" — ", 1)[1] if " — " in legacy_fleet_note else ""
    canonical_tail = canonical_fleet_note.split(" — ", 1)[1] if " — " in canonical_fleet_note else ""
    fleet_note_semantically_superseded = legacy_tail == canonical_tail and bool(legacy_tail)

    require(fleet_correction.get("repository_assessment") == "PASS", "fleet correction dependency must PASS")
    fleet_migration = fleet_correction.get("migration") or {}
    fleet_semantic = fleet_correction.get("semantic_audit") or {}
    require(
        fleet_migration.get("runtime_consumers_migrated") is True
        and (fleet_migration.get("active_documentation") or {}).get("instances/velvet-factory/.cursor/vf-desk.json") is True
        and fleet_semantic.get("retirement_preflight_clear") is True
        and fleet_semantic.get("remaining_blockers") == [],
        "fleet correction does not prove the canonical root-desk note migration",
    )

    require(tools_equal, "canonical toolDesk no longer preserves every legacy tool row")
    require(seats_equal, "canonical toolDesk no longer preserves every legacy seat row")
    require(desk_equal, "canonical toolDesk no longer preserves every legacy specialist row")
    require(skills_superset, "canonical toolDesk no longer preserves legacy skills")
    require(preserved_nonfleet_notes, "canonical toolDesk lost a non-fleet legacy note")
    require(fleet_note_semantically_superseded, "legacy fleet note was not canonically superseded")
    require(len(legacy_tools) == 18 and len(legacy_seats) == 6 and len(legacy_desk) == 38,
            "root-desk legacy operational counts drifted")
    require(canonical.get("role") == "instance" and canonical.get("instanceId") == "velvet-factory",
            "canonical toolDesk identity drift")
    for gate in ("brandAssetLock", "creativeTransformationLock", "projectRequestGate"):
        require((canonical.get(gate) or {}).get("mode") == "fail_closed",
                f"canonical toolDesk lost fail-closed {gate}")

    reader_rows: dict[str, dict[str, bool]] = {}
    for rel in READERS:
        text = git_text(args.prepared_against, rel)
        uses_resolver = "resolve_surface" in text and "toolDesk" in text
        direct_legacy = 'ROOT / ".cursor" / "vf-desk.json"' in text or "ROOT / '.cursor' / 'vf-desk.json'" in text
        reader_rows[rel] = {
            "uses_instance_surface_resolver": uses_resolver,
            "direct_root_legacy_read": direct_legacy,
        }
        require(uses_resolver, f"{rel}: toolDesk resolver binding missing")
        require(not direct_legacy, f"{rel}: direct root compatibility read reappeared")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    root_audit = surfaces.get("root_desk") or {}
    assessment = audit.get("assessment") or {}
    require(root_audit.get("retirement_preflight_clear") is True, "root_desk semantic preflight is not clear")
    require(root_audit.get("retirement_preflight_blockers") == [], "root_desk semantic blockers remain")
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global Stage 8D semantic preflight is not 5/5 clear",
    )

    authority = correction.get("authority") or {}
    policy_sha = csha(policy)
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed since root-desk correction")
    require(authority.get("external_effect_authority_changed") is False,
            "root-desk correction authority state drift")

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
        "root_desk_correction_is_pass": True,
        "all_runtime_readers_remain_on_explicit_instance_tool_desk_surface": True,
        "root_desk_semantic_preflight_is_clear": True,
        "all_five_stage8d_semantic_preflights_are_clear": True,
        "legacy_root_desk_is_byte_unchanged_since_correction": True,
        "canonical_tools_preserve_all_legacy_rows": tools_equal,
        "canonical_seats_preserve_all_legacy_rows": seats_equal,
        "canonical_specialists_preserve_all_legacy_rows": desk_equal,
        "canonical_skills_are_legacy_superset": skills_superset,
        "nonfleet_legacy_notes_are_preserved": preserved_nonfleet_notes,
        "legacy_fleet_note_is_canonically_superseded_and_receipt_gated": fleet_note_semantically_superseded,
        "canonical_instance_identity_and_fail_closed_gates_are_preserved": True,
        "external_effect_authority_is_unchanged": True,
        "observation_window_contains_multiple_distinct_downstream_main_runs": True,
        "all_downstream_main_runs_are_successful": True,
        "all_observations_descend_from_root_desk_correction": True,
        "latest_observation_matches_prepared_against_main": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_file_is_retained_after_closure": True,
        "deletion_requires_a_separate_isolated_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-root-desk-rollback-closure.v1",
        "stage": "8D_ROOT_DESK_ROLLBACK_CLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "root_desk",
        "legacy_path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Close the root_desk rollback observation window using post-correction semantic, parity, "
            "immutability and downstream-main evidence while retaining the compatibility desk and "
            "keeping deletion unauthorized."
        ),
        "correction": {
            "receipt": CORRECTION.relative_to(ROOT).as_posix(),
            "pull_request": CORRECTION_PR,
            "merge_sha": CORRECTION_MERGE_SHA,
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "runtime_reader_count": len(reader_rows),
            "runtime_readers": reader_rows,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "legacy_byte_unchanged_since_correction": True,
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
            "nonfleet_notes_preserved": preserved_nonfleet_notes,
            "legacy_fleet_note": legacy_fleet_note,
            "canonical_fleet_note": canonical_fleet_note,
            "fleet_note_semantically_superseded": fleet_note_semantically_superseded,
            "fleet_correction_receipt": FLEET_CORRECTION.relative_to(ROOT).as_posix(),
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "POST_CORRECTION_DOWNSTREAM_MAIN_FULL_SUITE_AND_SEMANTIC_STABILITY",
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
                "All root-desk runtime readers remain canonical, semantic preflight is clear, operational parity "
                "is preserved, legacy bytes and policy authority are unchanged, and multiple downstream main "
                "full-suite observations are green."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Run a separate isolated root_desk deletion gate. Revalidate current semantic state, this closure "
            "receipt, latest main CI, operational parity and external-effect authority before authorizing deletion."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha,
            "root_desk_correction_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "closure evidence does not itself authorize deletion",
            "legacy root desk remains present in this change",
            "no big-bang delete",
            "retirement must be isolated to root_desk",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "root-desk rollback closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE "
        f"assessment={report['repository_assessment']} closed={report['rollback_window_closed']} "
        f"readers={len(reader_rows)} parity={tools_equal and seats_equal and desk_equal} "
        f"runs={len(OBSERVATION_RUNS)} delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
