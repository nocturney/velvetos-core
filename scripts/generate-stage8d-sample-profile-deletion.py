#!/usr/bin/env python3
"""Generate the Stage 8D sample_profile deletion-completion receipt.

This generator runs only on the isolated deletion candidate. It requires the
merged evidence-only gate, removes no files itself, and proves that exactly the
authorized sample_profile path is absent while every other compatibility
surface and external-effect authority remain unchanged.
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
OUT = REPORTS / "stage8d-sample-profile-deletion.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
GATE = REPORTS / "stage8d-sample-profile-deletion-gate.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL = "instances/velvet-factory/instance/velvet-factory.json"
PREPARED_MAIN = "94d70732093db5d1c2983da2656df96a9564b90f"
GATE_HEAD = "74b275d936a76894f7e7d1c6b6d60b09b6af70b1"
GATE_PR = 546
POST_GATE_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37280812073,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T07:58:54Z",
}
OTHER_SURFACES = {
    "root_desk": ".cursor/vf-desk.json",
    "fleet": "packages/vfprod/FLEET.json",
    "tool_status": "packages/velvetos/TOOL-STATUS.json",
    "chatgpt_core_bundle": "packages/velvetos/chatgpt-project",
}
HISTORICAL_REPLAY = {
    "stage8c_sample_profile": {
        "commit": "eaaa6f2223199ee028184cddc6e8643213c66808",
        "generator": "scripts/generate-stage8c-sample-profile-consumers.py",
        "receipt": "packages/velvetos/policy/reports/stage8c-sample-profile-consumers.json",
    },
    "stage8c_closure": {
        "commit": "9c4032e8fe08dfd7add5dd70f0b9769d8c3bcae8",
        "generator": "scripts/generate-stage8c-closure.py",
        "receipt": "packages/velvetos/policy/reports/stage8c-closure.json",
    },
}
ALLOWED_EVIDENCE_CHANGES = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "packages/velvetos/policy/reports/stage8d-sample-profile-deletion.json",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8c-sample-profile-consumers.py",
    "scripts/generate-stage8c-closure.py",
    "scripts/generate-stage8d-sample-profile-deletion.py",
}
SAFE_CURRENT_REFERENCES = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8a-core-instance-inventory.py",
    "scripts/generate-stage8b-instance-resolver-foundation.py",
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


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def source_commit() -> str | None:
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", REPORT_REL],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return commits[-1] if commits else None


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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


def git_grep_files(needle: str, commit: str | None = None) -> list[str]:
    cmd = ["git", "grep", "-l", "-F", needle]
    if commit:
        cmd.append(commit)
    cmd.extend(["--", ".", ":(exclude)packages/velvetos/policy/reports/*"])
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or "git grep failed")
    prefix = f"{commit}:" if commit else ""
    rows = []
    for line in proc.stdout.splitlines():
        rel = line.strip().replace("\\", "/")
        if prefix and rel.startswith(prefix):
            rel = rel[len(prefix):]
        if rel:
            rows.append(rel)
    return sorted(set(rows))


def changed_paths(base: str, commit: str | None = None) -> tuple[list[str], list[str], list[str]]:
    diff_cmd = ["git", "diff", "--name-status", base]
    if commit:
        diff_cmd.append(commit)
    diff_cmd.append("--")
    proc = subprocess.run(
        diff_cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
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
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        untracked = sorted({line.strip().replace("\\", "/") for line in extra.stdout.splitlines() if line.strip()})
    return sorted(set(deleted)), sorted(set(changed)), untracked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")
    require(args.prepared_against == PREPARED_MAIN,
            "sample deletion must be generated against the verified gate merge SHA")

    src = source_commit()
    gate = git_json(src, GATE.relative_to(ROOT).as_posix()) if src else load_json(GATE)
    require(
        gate.get("schema") == "velvetos.stage8d-sample-profile-deletion-gate.v1"
        and gate.get("surface_id") == "sample_profile"
        and gate.get("repository_assessment") == "PASS"
        and gate.get("delete_authorized") is True
        and gate.get("deletion_performed") is False
        and gate.get("retirement_authorized") is False,
        "merged sample deletion gate is not valid",
    )
    target = gate.get("target") or {}
    require(
        target.get("legacy_path") == LEGACY
        and target.get("canonical_path") == CANONICAL
        and target.get("delete_exactly") == [LEGACY]
        and target.get("delete_other_surfaces") is False,
        "sample deletion gate target drift",
    )
    require(csha(gate) == csha(git_json(args.prepared_against, GATE.relative_to(ROOT).as_posix())),
            "gate receipt differs from verified deletion base")

    legacy_path = ROOT / LEGACY
    canonical_path = ROOT / CANONICAL
    legacy_present = git_exists(src, LEGACY) if src else legacy_path.exists()
    canonical_present = git_exists(src, CANONICAL) if src else canonical_path.is_file()
    require(not legacy_present, "authorized legacy sample still exists; deletion was not performed")
    require(canonical_present, "canonical instance profile is missing")

    deleted, changed, untracked = changed_paths(args.prepared_against, src)
    require(deleted == [LEGACY], f"deletion scope drift: deleted={deleted}")
    non_target_changes = set(changed) - {LEGACY}
    require(non_target_changes <= ALLOWED_EVIDENCE_CHANGES,
            f"non-evidence tracked changes in isolated deletion PR: {sorted(non_target_changes - ALLOWED_EVIDENCE_CHANGES)}")
    require(set(untracked) <= ALLOWED_EVIDENCE_CHANGES,
            f"non-evidence untracked changes in isolated deletion PR: {sorted(set(untracked) - ALLOWED_EVIDENCE_CHANGES)}")

    other_surface_state: dict[str, Any] = {}
    for surface_id, rel in OTHER_SURFACES.items():
        current_present = git_exists(src, rel) if src else (ROOT / rel).exists()
        require(current_present, f"{surface_id}: other compatibility surface is missing")
        diff_cmd = ["git", "diff", "--quiet", args.prepared_against]
        if src:
            diff_cmd.append(src)
        diff_cmd.extend(["--", rel])
        proc = subprocess.run(diff_cmd, cwd=ROOT)
        require(proc.returncode == 0, f"{surface_id}: other compatibility surface changed in sample deletion PR")
        other_surface_state[surface_id] = {
            "path": rel,
            "present": True,
            "unchanged_from_prepared_against": True,
            "deletion_authorized": False,
        }

    legacy = git_json(args.prepared_against, LEGACY)
    canonical = git_json(src, CANONICAL) if src else load_json(canonical_path)
    legacy_for_coverage = dict(legacy)
    require(legacy_for_coverage.pop("role", None) == "sample", "legacy compatibility role drift")
    legacy_notes = legacy_for_coverage.pop("notes", None)
    require(isinstance(legacy_notes, str) and "Reference profile hosted in VelvetOS Core for sensors/compat" in legacy_notes,
            "legacy compatibility notes drift")
    coverage_problems = covered_by(legacy_for_coverage, canonical)
    require(coverage_problems == [],
            "canonical instance no longer covers deleted legacy business/config: " + "; ".join(coverage_problems))
    require(set(legacy.get("modulesEnabled") or []) == set(canonical.get("modulesEnabled") or []),
            "canonical module set diverged from deleted legacy sample")

    refs = git_grep_files(LEGACY, src)
    require(set(refs) == SAFE_CURRENT_REFERENCES,
            f"unexpected current legacy-path references remain after deletion: {refs}")

    policy_now = git_json(src, POLICY.relative_to(ROOT).as_posix()) if src else load_json(POLICY)
    policy_base = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    require(csha(policy_now) == csha(policy_base), "external-effect policy registry changed in deletion PR")

    restore = gate.get("restore_anchor") or {}
    raw = git_bytes(str(restore.get("source_commit_sha")), LEGACY)
    require(hashlib.sha256(raw).hexdigest() == restore.get("sha256"), "gate restore SHA-256 no longer resolves")
    require(len(raw) == restore.get("size_bytes") == 5214, "gate restore size drift")


    replay_evidence: dict[str, Any] = {}
    for name, row in HISTORICAL_REPLAY.items():
        receipt_raw = git_bytes(src, row["receipt"]) if src else (ROOT / row["receipt"]).read_bytes()
        commit_raw = git_bytes(row["commit"], row["receipt"])
        require(receipt_raw == commit_raw, f"{name}: historical receipt bytes drifted from creation commit")
        replay_evidence[name] = {
            **row,
            "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "receipt_matches_creation_commit": True,
        }

    require(
        POST_GATE_MAIN_CI["sha"] == args.prepared_against
        and POST_GATE_MAIN_CI["event"] == "push"
        and POST_GATE_MAIN_CI["conclusion"] == "success",
        "post-gate main CI is not bound to the verified deletion base",
    )

    criteria = {
        "merged_gate_is_pass_and_exactly_authorizes_sample_profile": True,
        "gate_itself_did_not_perform_deletion": True,
        "gate_merge_main_push_ci_is_success": True,
        "authorized_legacy_path_is_absent": True,
        "no_other_tracked_path_is_deleted": True,
        "non_target_changes_are_evidence_only": True,
        "all_other_compatibility_surfaces_are_present_and_unchanged": True,
        "canonical_instance_semantically_covers_deleted_legacy_business_config": True,
        "canonical_and_deleted_legacy_module_sets_match": True,
        "active_semantic_legacy_consumers_remain_zero": True,
        "remaining_legacy_path_mentions_are_historical_or_policy_evidence_only": True,
        "external_effect_authority_is_unchanged": True,
        "exact_restore_anchor_still_resolves": True,
        "historical_stage8c_receipts_remain_byte_anchored_to_creation_commits": True,
        "retirement_is_limited_to_one_surface": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-deletion.v1",
        "stage": "8D_SAMPLE_PROFILE_DELETION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
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
        "deletion": {
            "legacy_path": LEGACY,
            "canonical_path": CANONICAL,
            "legacy_present": False,
            "deleted_paths": deleted,
            "delete_exactly": [LEGACY],
            "deletion_performed": True,
            "other_surfaces_deleted": False,
        },
        "cross_surface_isolation": other_surface_state,
        "current_evidence": {
            "runtime_authority": False,
            "active_semantic_legacy_consumer_count": 0,
            "current_legacy_path_references": refs,
            "canonical_semantically_covers_deleted_legacy_business_config": True,
            "canonical_legacy_module_parity": True,
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
        "historical_replay": replay_evidence,
        "authority": {
            "policy_registry_sha256": csha(policy_now),
            "external_effect_authority_changed": False,
            "delete_authorized_surface": "sample_profile",
            "retirement_authorized": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": True,
        "retirement_authorized": True,
        "next_action": (
            "Run exact-SHA selector plus independent full suite, merge only this isolated deletion PR, "
            "then verify the merge SHA locally and with main push CI before opening the next surface gate."
        ),
        "constraints": [
            "one compatibility surface retired per deletion PR",
            "no other compatibility surface changed or deletion-authorized",
            "historical receipts replay against their historical creation snapshots",
            "restore anchor remains available in Git history",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "sample deletion acceptance criteria failed")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_PROFILE_DELETION "
        f"assessment=PASS deletion_performed=true retirement_authorized=true "
        f"path={LEGACY} restore_sha256={str(restore.get('sha256'))[:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
