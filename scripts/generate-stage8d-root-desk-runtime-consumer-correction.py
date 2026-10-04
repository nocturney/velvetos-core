#!/usr/bin/env python3
"""Generate Stage 8D corrective evidence for root-desk runtime consumers."""
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
OUT = REPORTS / "stage8d-root-desk-runtime-consumer-correction.json"
PRIOR = REPORTS / "stage8d-root-desk-consumer-migration.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"
LEGACY_REL = ".cursor/vf-desk.json"
CANONICAL_REL = "instances/velvet-factory/.cursor/vf-desk.json"

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
    require(isinstance(value, dict), f"{rel}@{sha} must contain an object")
    return value


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def rows_by(items: Any, key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in items or []:
        if isinstance(row, dict) and isinstance(row.get(key), str):
            out[row[key]] = row
    return out


def snapshot_root_desk_audit(sha: str) -> dict[str, Any]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_retirement_semantic_audit_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "root_desk")
    require(isinstance(row, dict), "snapshot semantic audit did not return an object")
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

    prior = git_json(args.source_commit, PRIOR.relative_to(ROOT).as_posix())
    require(prior.get("repository_acceptance") == "PASS", "prior root-desk migration receipt must PASS")

    legacy_before = git_json(args.prepared_against, LEGACY_REL)
    legacy_after = git_json(args.source_commit, LEGACY_REL)
    canonical = git_json(args.source_commit, CANONICAL_REL)
    require(git_bytes(args.prepared_against, LEGACY_REL) == git_bytes(args.source_commit, LEGACY_REL),
            "legacy root desk changed during corrective migration")

    legacy_tools = legacy_after.get("tools") or {}
    canonical_tools = canonical.get("tools") or {}
    tools_equal = all(k in canonical_tools and canonical_tools[k] == v for k, v in legacy_tools.items())

    legacy_seats = rows_by(legacy_after.get("seats"), "id")
    canonical_seats = rows_by(canonical.get("seats"), "id")
    seats_equal = all(k in canonical_seats and canonical_seats[k] == v for k, v in legacy_seats.items())

    legacy_desk = rows_by(legacy_after.get("desk"), "slug")
    canonical_desk = rows_by(canonical.get("desk"), "slug")
    desk_equal = all(k in canonical_desk and canonical_desk[k] == v for k, v in legacy_desk.items())

    skills_superset = set(legacy_after.get("skills") or []) <= set(canonical.get("skills") or [])
    notes_superset = set(legacy_after.get("notes") or []) <= set(canonical.get("notes") or [])

    require(tools_equal, "canonical toolDesk does not preserve all legacy tool rows")
    require(seats_equal, "canonical toolDesk does not preserve all legacy seat rows")
    require(desk_equal, "canonical toolDesk does not preserve all legacy specialist rows")
    require(skills_superset, "canonical toolDesk does not preserve all legacy skills")
    require(notes_superset, "canonical toolDesk does not preserve all legacy notes")

    require(canonical.get("role") == "instance", "canonical toolDesk must retain role=instance")
    require(canonical.get("instanceId") == "velvet-factory", "canonical toolDesk instance id drift")
    for gate in ("brandAssetLock", "creativeTransformationLock", "projectRequestGate"):
        require((canonical.get(gate) or {}).get("mode") == "fail_closed", f"canonical toolDesk lost {gate}")

    reader_rows: dict[str, Any] = {}
    for rel in READERS:
        text = git_text(args.source_commit, rel)
        uses_resolver = "resolve_surface" in text and "toolDesk" in text
        root_literal = 'ROOT / ".cursor" / "vf-desk.json"' in text or "ROOT / '.cursor' / 'vf-desk.json'" in text
        reader_rows[rel] = {
            "uses_instance_surface_resolver": uses_resolver,
            "direct_root_legacy_read": root_literal,
        }
        require(uses_resolver, f"{rel}: does not resolve toolDesk through instance resolver")
        require(not root_literal, f"{rel}: still directly reads root compatibility desk")

    audit = snapshot_root_desk_audit(args.source_commit)
    require(audit.get("retirement_preflight_clear") is True, "root_desk semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [], "root_desk semantic blockers remain")

    policy_before = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    policy_after = git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix())
    policy_before_sha = csha(policy_before)
    policy_after_sha = csha(policy_after)
    require(policy_before_sha == policy_after_sha, "external-effect policy authority changed")

    criteria = {
        "prior_root_desk_migration_receipt_is_preserved": True,
        "legacy_root_desk_is_byte_unchanged": True,
        "all_runtime_readers_use_explicit_instance_tool_desk_surface": True,
        "semantic_preflight_has_zero_root_desk_blockers": True,
        "canonical_tools_preserve_legacy_rows": tools_equal,
        "canonical_seats_preserve_legacy_rows": seats_equal,
        "canonical_specialists_preserve_legacy_rows": desk_equal,
        "canonical_skills_are_legacy_superset": skills_superset,
        "canonical_notes_are_legacy_superset": notes_superset,
        "canonical_instance_identity_and_fail_closed_gates_are_preserved": True,
        "external_effect_authority_is_unchanged": True,
        "rollback_window_remains_open": True,
        "delete_authority_remains_false": True,
    }

    report = {
        "schema": "velvetos.stage8d-root-desk-runtime-consumer-correction.v1",
        "stage": "8D_ROOT_DESK_RUNTIME_CONSUMER_CORRECTION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "surface_id": "root_desk",
        "legacy_path": LEGACY_REL,
        "canonical_path": CANONICAL_REL,
        "purpose": (
            "Migrate root-desk runtime readers exposed by the fail-closed semantic audit to the canonical "
            "instance toolDesk surface, preserve operational parity, and keep rollback/deletion closed."
        ),
        "migration": {
            "runtime_readers": reader_rows,
            "runtime_consumers_migrated": True,
            "legacy_present": True,
            "legacy_byte_unchanged": True,
        },
        "operational_parity": {
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
            "notes_superset": notes_superset,
        },
        "semantic_audit": {
            "retirement_preflight_clear": True,
            "remaining_blockers": [],
            "reference_classes": audit.get("classes") or {},
        },
        "rollback": {
            "window_open": True,
            "closure_evidence": None,
            "retirement_ready_for_deletion_gate": False,
            "delete_authorized": False,
        },
        "authority": {
            "policy_registry_sha256": policy_after_sha,
            "prepared_against_policy_registry_sha256": policy_before_sha,
            "external_effect_authority_changed": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "retirement_authorized": False,
        "delete_authorized": False,
        "next_action": (
            "Merge this correction and collect fresh downstream main full-suite evidence before explicit "
            "root_desk rollback-window closure. Do not delete .cursor/vf-desk.json from this correction."
        ),
        "constraints": [
            "legacy root desk remains present and byte-unchanged",
            "rollback closure requires fresh post-correction evidence",
            "deletion requires a separate explicit preflight",
            "no big-bang retirement",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "root-desk correction acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_ROOT_DESK_RUNTIME_CORRECTION "
        f"assessment={report['repository_assessment']} readers={len(reader_rows)} "
        f"tools={len(legacy_tools)}/{len(canonical_tools)} seats={len(legacy_seats)}/{len(canonical_seats)} "
        f"desk={len(legacy_desk)}/{len(canonical_desk)} blockers=0 delete_authorized=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
