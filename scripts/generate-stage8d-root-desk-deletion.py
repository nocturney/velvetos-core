#!/usr/bin/env python3
"""Generate the isolated Stage 8D root_desk deletion-completion receipt.

This generator never deletes files. It runs on the isolated deletion candidate
and proves that only the gate-authorized root compatibility desk is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-root-desk-deletion.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
GATE = REPORTS / "stage8d-root-desk-deletion-gate.json"
SAMPLE_RETIREMENT = REPORTS / "stage8d-sample-profile-deletion.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY = ".cursor/vf-desk.json"
CANONICAL = "instances/velvet-factory/.cursor/vf-desk.json"
SAMPLE_LEGACY = "packages/velvetos/samples/velvet-factory.json"
PREPARED_MAIN = "98ac4ce14e20564f5161af5ad7bc9bc96a774e2a"
GATE_HEAD = "fe0944086b7d158048715eef273b530a68122fee"
GATE_PR = 549
POST_GATE_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37286661000,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T08:55:17Z",
}
OTHER_SURFACES = {
    "fleet": "packages/vfprod/FLEET.json",
    "tool_status": "packages/velvetos/TOOL-STATUS.json",
    "chatgpt_core_bundle": "packages/velvetos/chatgpt-project",
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
HISTORICAL_REPLAY = {
    "stage8c_root_desk_readers": {
        "commit": "4b074e9c203f678d6b2216ff52e5a46782136a3c",
        "generator": "scripts/generate-stage8c-root-desk-readers.py",
        "receipt": "packages/velvetos/policy/reports/stage8c-root-desk-readers.json",
    },
    "stage8c_desk_catalog_bindings": {
        "commit": "da5388f2b8c2739461fd247f441d10ab7b61987e",
        "generator": "scripts/generate-stage8c-desk-catalog-bindings.py",
        "receipt": "packages/velvetos/policy/reports/stage8c-desk-catalog-bindings.json",
    },
}
ALLOWED_EVIDENCE_CHANGES = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "packages/velvetos/policy/reports/stage8d-root-desk-deletion.json",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8c-root-desk-readers.py",
    "scripts/generate-stage8c-desk-catalog-bindings.py",
    "scripts/generate-stage8d-retirement-semantic-audit.py",
    "scripts/generate-stage8d-root-desk-deletion.py",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    value = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    require(isinstance(value, dict), f"{rel}@{sha} must be a JSON object")
    return value


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig", errors="replace")


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def source_commit() -> str | None:
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", REPORT_REL],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return commits[-1] if commits else None


def csha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def rows_by(value: Any, key: str) -> dict[str, dict[str, Any]]:
    return {
        str(row[key]): row
        for row in (value or [])
        if isinstance(row, dict) and row.get(key) is not None
    }


def changed_paths(base: str, commit: str | None = None) -> tuple[list[str], list[str], list[str]]:
    cmd = ["git", "diff", "--name-status", base]
    if commit:
        cmd.append(commit)
    cmd.append("--")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", check=True)
    deleted: list[str] = []
    changed: list[str] = []
    for raw in proc.stdout.splitlines():
        cols = raw.split("\t")
        if len(cols) < 2:
            continue
        status, rel = cols[0], cols[-1].replace("\\", "/")
        changed.append(rel)
        if status.startswith("D"):
            deleted.append(rel)
    if commit:
        untracked: list[str] = []
    else:
        extra = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", check=True,
        )
        untracked = sorted({line.strip().replace("\\", "/") for line in extra.stdout.splitlines() if line.strip()})
    return sorted(set(deleted)), sorted(set(changed)), untracked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None, "bad prepared SHA")
    require(args.prepared_against == PREPARED_MAIN, "root desk deletion must use the verified gate merge SHA")

    src = source_commit()
    gate = git_json(src, GATE.relative_to(ROOT).as_posix()) if src else load_json(GATE)
    sample = git_json(src, SAMPLE_RETIREMENT.relative_to(ROOT).as_posix()) if src else load_json(SAMPLE_RETIREMENT)

    require(
        gate.get("schema") == "velvetos.stage8d-root-desk-deletion-gate.v1"
        and gate.get("surface_id") == "root_desk"
        and gate.get("repository_assessment") == "PASS"
        and gate.get("delete_authorized") is True
        and gate.get("deletion_performed") is False
        and gate.get("retirement_authorized") is False,
        "merged root-desk deletion gate is invalid",
    )
    target = gate.get("target") or {}
    require(
        target.get("legacy_path") == LEGACY
        and target.get("canonical_path") == CANONICAL
        and target.get("delete_exactly") == [LEGACY]
        and target.get("delete_other_surfaces") is False,
        "root-desk gate target drift",
    )
    require(csha(gate) == csha(git_json(args.prepared_against, GATE.relative_to(ROOT).as_posix())),
            "root-desk gate differs from verified deletion base")

    sample_deletion = sample.get("deletion") or {}
    require(
        sample.get("schema") == "velvetos.stage8d-sample-profile-deletion.v1"
        and sample.get("repository_assessment") == "PASS"
        and sample.get("deletion_performed") is True
        and sample.get("retirement_authorized") is True
        and sample_deletion.get("legacy_path") == SAMPLE_LEGACY
        and sample_deletion.get("legacy_present") is False,
        "prior sample retirement drift",
    )

    legacy_present = git_exists(src, LEGACY) if src else (ROOT / LEGACY).exists()
    canonical_present = git_exists(src, CANONICAL) if src else (ROOT / CANONICAL).is_file()
    require(not legacy_present, "authorized root desk still exists")
    require(canonical_present, "canonical instance desk is missing")

    deleted, changed, untracked = changed_paths(args.prepared_against, src)
    require(deleted == [LEGACY], f"deletion scope drift: {deleted}")
    non_target = set(changed) - {LEGACY}
    require(non_target <= ALLOWED_EVIDENCE_CHANGES,
            f"non-evidence tracked changes: {sorted(non_target - ALLOWED_EVIDENCE_CHANGES)}")
    require(set(untracked) <= ALLOWED_EVIDENCE_CHANGES,
            f"non-evidence untracked changes: {sorted(set(untracked) - ALLOWED_EVIDENCE_CHANGES)}")

    other_state: dict[str, Any] = {}
    for surface_id, rel in OTHER_SURFACES.items():
        present = git_exists(src, rel) if src else (ROOT / rel).exists()
        require(present, f"{surface_id}: retained compatibility surface missing")
        cmd = ["git", "diff", "--quiet", args.prepared_against]
        if src:
            cmd.append(src)
        cmd.extend(["--", rel])
        require(subprocess.run(cmd, cwd=ROOT).returncode == 0, f"{surface_id}: retained surface changed")
        other_state[surface_id] = {
            "path": rel,
            "present": True,
            "unchanged_from_prepared_against": True,
            "deletion_authorized": False,
        }

    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(src, CANONICAL) if src else load_json(ROOT / CANONICAL)
    legacy_tools = legacy.get("tools") or {}
    canonical_tools = canonical.get("tools") or {}
    tools_equal = len(legacy_tools) == 18 and len(canonical_tools) == 18 and all(
        key in canonical_tools and canonical_tools[key] == value for key, value in legacy_tools.items()
    )
    legacy_seats, canonical_seats = rows_by(legacy.get("seats"), "id"), rows_by(canonical.get("seats"), "id")
    legacy_desk, canonical_desk = rows_by(legacy.get("desk"), "slug"), rows_by(canonical.get("desk"), "slug")
    seats_equal = len(legacy_seats) == 6 and len(canonical_seats) == 6 and all(
        key in canonical_seats and canonical_seats[key] == value for key, value in legacy_seats.items()
    )
    desk_equal = len(legacy_desk) == 38 and len(canonical_desk) == 38 and all(
        key in canonical_desk and canonical_desk[key] == value for key, value in legacy_desk.items()
    )
    skills_superset = set(legacy.get("skills") or []) <= set(canonical.get("skills") or [])
    legacy_notes, canonical_notes = set(legacy.get("notes") or []), set(canonical.get("notes") or [])
    legacy_fleet = {n for n in legacy_notes if "packages/vfprod/FLEET.json" in n}
    canonical_fleet = {n for n in canonical_notes if "instance:surface:fleet" in n}
    require(len(legacy_fleet) == 1 and len(canonical_fleet) == 1, "fleet-note shape drift")
    lf, cf = next(iter(legacy_fleet)), next(iter(canonical_fleet))
    fleet_note_superseded = (" — " in lf and " — " in cf and lf.split(" — ", 1)[1] == cf.split(" — ", 1)[1])
    nonfleet_notes_preserved = (legacy_notes - legacy_fleet) <= canonical_notes
    require(tools_equal and seats_equal and desk_equal and skills_superset
            and fleet_note_superseded and nonfleet_notes_preserved, "canonical root-desk parity drift")
    require(canonical.get("role") == "instance" and canonical.get("instanceId") == "velvet-factory",
            "canonical desk identity drift")
    for name in ("brandAssetLock", "creativeTransformationLock", "projectRequestGate"):
        require((canonical.get(name) or {}).get("mode") == "fail_closed", f"canonical desk lost {name}")

    readers: dict[str, dict[str, bool]] = {}
    for rel in READERS:
        text = git_text(src, rel) if src else (ROOT / rel).read_text(encoding="utf-8")
        uses = "resolve_surface" in text and "toolDesk" in text
        direct = 'ROOT / ".cursor" / "vf-desk.json"' in text or "ROOT / '.cursor' / 'vf-desk.json'" in text
        readers[rel] = {"uses_instance_surface_resolver": uses, "direct_root_legacy_read": direct}
        require(uses and not direct, f"{rel}: runtime reader regressed")

    policy_now = git_json(src, POLICY.relative_to(ROOT).as_posix()) if src else load_json(POLICY)
    policy_base = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    require(csha(policy_now) == csha(policy_base), "external-effect authority changed")

    restore = gate.get("restore_anchor") or {}
    raw = git_bytes(str(restore.get("source_commit_sha")), LEGACY)
    require(
        restore.get("git_blob_sha1") == "30ddd380f1d556dd1b444c3ca6b153f6d6188e1f"
        and hashlib.sha256(raw).hexdigest() == restore.get("sha256")
        and restore.get("sha256") == "702695ffa72b8f0e56738cc533cc95ee2d6a6cd76c66cf58f2a84d3658a1116b"
        and len(raw) == restore.get("size_bytes") == 34186,
        "root-desk restore anchor drift",
    )

    replay: dict[str, Any] = {}
    for name, row in HISTORICAL_REPLAY.items():
        receipt_raw = git_bytes(src, row["receipt"]) if src else (ROOT / row["receipt"]).read_bytes()
        creation_raw = git_bytes(row["commit"], row["receipt"])
        require(receipt_raw == creation_raw, f"{name}: historical receipt bytes drifted")
        replay[name] = {
            **row,
            "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "receipt_matches_creation_commit": True,
        }

    require(
        POST_GATE_MAIN_CI["sha"] == args.prepared_against
        and POST_GATE_MAIN_CI["event"] == "push"
        and POST_GATE_MAIN_CI["conclusion"] == "success",
        "post-gate main CI is not bound to deletion base",
    )

    criteria = {
        "merged_gate_is_pass_and_exactly_authorizes_root_desk": True,
        "gate_itself_did_not_perform_deletion": True,
        "gate_merge_main_push_ci_is_success": True,
        "authorized_root_desk_is_absent": True,
        "no_other_tracked_path_is_deleted": True,
        "non_target_changes_are_evidence_only": True,
        "prior_sample_retirement_remains_authoritative": True,
        "remaining_three_compatibility_surfaces_are_present_and_unchanged": True,
        "canonical_root_desk_preserves_operational_parity": True,
        "all_runtime_readers_remain_on_explicit_instance_tool_desk_surface": True,
        "external_effect_authority_is_unchanged": True,
        "exact_restore_anchor_still_resolves": True,
        "historical_stage8c_root_receipts_remain_byte_anchored": True,
        "retirement_is_limited_to_root_desk": True,
    }

    report = {
        "schema": "velvetos.stage8d-root-desk-deletion.v1",
        "stage": "8D_ROOT_DESK_DELETION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "root_desk",
        "gate": {
            "receipt": GATE.relative_to(ROOT).as_posix(),
            "gate_head_sha": GATE_HEAD,
            "gate_merge_sha": args.prepared_against,
            "gate_pr": GATE_PR,
            "repository_assessment": "PASS",
            "delete_authorized": True,
            "authorized_paths": [LEGACY],
        },
        "post_gate_main_ci": POST_GATE_MAIN_CI,
        "prior_retirement": {
            "surface_id": "sample_profile",
            "receipt": SAMPLE_RETIREMENT.relative_to(ROOT).as_posix(),
            "repository_assessment": "PASS",
            "deletion_performed": True,
            "retirement_authorized": True,
        },
        "deletion": {
            "legacy_path": LEGACY,
            "canonical_path": CANONICAL,
            "legacy_present": False,
            "deleted_paths": deleted,
            "delete_exactly": [LEGACY],
            "deletion_performed": True,
            "other_surfaces_deleted": False,
        },
        "cross_surface_isolation": other_state,
        "current_evidence": {
            "runtime_authority": False,
            "runtime_reader_count": len(readers),
            "runtime_readers": readers,
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
            "source_commit_sha": restore.get("source_commit_sha"),
            "legacy_path": LEGACY,
            "git_blob_sha1": restore.get("git_blob_sha1"),
            "sha256": restore.get("sha256"),
            "size_bytes": restore.get("size_bytes"),
            "restore_command": restore.get("restore_command"),
            "verified_after_deletion": True,
        },
        "historical_replay": replay,
        "authority": {
            "policy_registry_sha256": csha(policy_now),
            "external_effect_authority_changed": False,
            "delete_authorized_surface": "root_desk",
            "retirement_authorized": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": True,
        "retirement_authorized": True,
        "next_action": (
            "Run exact-SHA selector plus independent full suite, merge only this isolated root_desk deletion PR, "
            "then verify the merge SHA locally and with main push CI before opening the fleet deletion gate."
        ),
        "constraints": [
            "one compatibility surface retired per deletion PR",
            "sample_profile remains retired and is not modified",
            "fleet, tool_status and chatgpt_core_bundle remain deletion-unauthorized by this receipt",
            "historical Stage 8C receipts replay against creation snapshots",
            "restore anchor remains available in Git history",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "root-desk deletion acceptance criteria failed")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_ROOT_DESK_DELETION "
        f"assessment=PASS deletion_performed=true retirement_authorized=true "
        f"path={LEGACY} restore_sha256={str(restore.get('sha256'))[:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
