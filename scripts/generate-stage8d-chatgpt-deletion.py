#!/usr/bin/env python3
"""Generate the isolated Stage 8D chatgpt_core_bundle deletion receipt.

This generator never deletes files. It proves that the merged evidence-only
gate authorized exactly the retained Core ChatGPT compatibility tree plus its
recorded legacy-only .gitattributes rules, that those compatibility bytes are
gone, and that the canonical Velvet Factory distribution, restore evidence,
historical receipts, and external-effect authority remain intact.
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
OUT = REPORTS / "stage8d-chatgpt-deletion.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
GATE_REL = "packages/velvetos/policy/reports/stage8d-chatgpt-deletion-gate.json"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"

LEGACY_ROOT = "packages/velvetos/chatgpt-project"
CANONICAL_ROOT = "instances/velvet-factory/distribution/chatgpt-project"
CANONICAL_ATTR = "/instances/velvet-factory/distribution/chatgpt-project/** -whitespace"
PREPARED_MAIN = "d593f1b620de491fa143e562e5e0ed514fb15f0b"
GATE_HEAD = "42a2b634eeb296c66c99774751402b345e323254"
GATE_MERGE = "b3af7b9e0dcf6c207a617c4c394228b498350c20"
GATE_PR = 555
POST_GATE_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37335910275,
    "run_attempt": 1,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
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
    "tool_status": {
        "receipt": "stage8d-tool-status-deletion.json",
        "schema": "velvetos.stage8d-tool-status-deletion.v1",
        "legacy": "packages/velvetos/TOOL-STATUS.json",
    },
}
HISTORICAL_REPLAY = {
    "consumer_migration": {
        "commit": "5e4c32bac19fe13ee1bbcac22513dcc2f5d36921",
        "receipt": "packages/velvetos/policy/reports/stage8d-chatgpt-core-consumer-migration.json",
    },
    "semantic_correction": {
        "commit": "57a84a84762de99ee6faf24af54a1247483b6bbe",
        "receipt": "packages/velvetos/policy/reports/stage8d-chatgpt-semantic-correction.json",
    },
    "rollback_closure": {
        "commit": "8fdc942136baec2101c46b4370acff8a234543c6",
        "receipt": "packages/velvetos/policy/reports/stage8d-chatgpt-rollback-closure.json",
    },
}
ALLOWED_SUPPORT_CHANGES = {
    ".gitattributes",
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "packages/velvetos/policy/reports/stage8d-chatgpt-deletion.json",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8d-chatgpt-deletion.py",
    "scripts/generate-stage8d-retirement-semantic-audit.py",
}
SAFE_REFERENCE_PREFIXES = (
    "packages/vfharness/state/",
    "packages/velvetos/policy/reports/",
    "scripts/generate-stage8",
)
SAFE_REFERENCE_EXACT = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8d-chatgpt-deletion-gate.py",
    "scripts/generate-stage8d-chatgpt-deletion.py",
    "scripts/generate-stage8d-retirement-semantic-audit.py",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def source_commit() -> str | None:
    if subprocess.run(["git", "diff", "--quiet", "--", REPORT_REL], cwd=ROOT).returncode != 0:
        return None
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", REPORT_REL],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    value = proc.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value or "") else None


def current_exists(src: str | None, rel: str) -> bool:
    return git_exists(src, rel) if src else (ROOT / rel).exists()


def current_bytes(src: str | None, rel: str) -> bytes:
    return git_bytes(src, rel) if src else (ROOT / rel).read_bytes()


def current_text(src: str | None, rel: str) -> str:
    return current_bytes(src, rel).decode("utf-8-sig", errors="replace")


def current_json(src: str | None, rel: str) -> dict[str, Any]:
    return git_json(src, rel) if src else load_json(ROOT / rel)


def tree_files_at(sha: str, root: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", sha, "--", root],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    prefix = root.rstrip("/") + "/"
    return sorted(line[len(prefix):] for line in out.splitlines() if line.startswith(prefix))


def current_tree_files(src: str | None, root: str) -> list[str]:
    if src:
        return tree_files_at(src, root)
    base = ROOT / root
    if not base.is_dir():
        return []
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def current_tree_bytes(src: str | None, root: str, rel: str) -> bytes:
    return git_bytes(src, f"{root}/{rel}") if src else (ROOT / root / rel).read_bytes()


def changed_paths(base: str, commit: str | None) -> tuple[list[str], list[str], list[str]]:
    cmd = ["git", "diff", "--name-status", base]
    if commit:
        cmd.append(commit)
    cmd.append("--")
    proc = subprocess.run(
        cmd,
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
        untracked = sorted(
            line.strip().replace("\\", "/")
            for line in extra.stdout.splitlines()
            if line.strip()
        )
    return sorted(set(deleted)), sorted(set(changed)), sorted(set(untracked))


def validate_prior_retirement(src: str | None, surface_id: str, spec: dict[str, str]) -> dict[str, Any]:
    rel = f"packages/velvetos/policy/reports/{spec['receipt']}"
    receipt = current_json(src, rel)
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
        and not current_exists(src, spec["legacy"]),
        f"{surface_id}: prior retirement receipt drift",
    )
    return {
        "receipt": rel,
        "repository_assessment": "PASS",
        "deletion_performed": True,
        "retirement_authorized": True,
    }


def legacy_references(src: str | None) -> tuple[list[str], list[str]]:
    if src:
        proc = subprocess.run(
            ["git", "grep", "-l", "-F", LEGACY_ROOT, src, "--", ".", ":(exclude)packages/velvetos/policy/reports/*"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        require(proc.returncode in {0, 1}, "legacy reference scan failed")
        prefix = src + ":"
        refs = sorted(
            line[len(prefix):] if line.startswith(prefix) else line
            for line in proc.stdout.splitlines()
            if line.strip()
        )
    else:
        proc = subprocess.run(
            ["git", "grep", "-l", "-F", LEGACY_ROOT, "--", ".", ":(exclude)packages/velvetos/policy/reports/*"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        require(proc.returncode in {0, 1}, "legacy reference scan failed")
        refs = sorted(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
        if (ROOT / "scripts/generate-stage8d-chatgpt-deletion.py").is_file():
            refs = sorted(set(refs + ["scripts/generate-stage8d-chatgpt-deletion.py"]))
    safe = []
    blockers = []
    for rel in refs:
        if rel in SAFE_REFERENCE_EXACT or rel.startswith(SAFE_REFERENCE_PREFIXES):
            safe.append(rel)
        else:
            blockers.append(rel)
    return safe, blockers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None, "bad prepared SHA")
    require(args.prepared_against == PREPARED_MAIN, "ChatGPT deletion must use verified current main")

    src = source_commit()
    gate = current_json(src, GATE_REL)
    require(
        gate.get("schema") == "velvetos.stage8d-chatgpt-deletion-gate.v1"
        and gate.get("surface_id") == "chatgpt_core_bundle"
        and gate.get("repository_assessment") == "PASS"
        and gate.get("delete_authorized") is True
        and gate.get("deletion_performed") is False
        and gate.get("retirement_authorized") is False,
        "merged ChatGPT deletion gate is invalid",
    )
    require(csha(gate) == csha(git_json(args.prepared_against, GATE_REL)), "ChatGPT gate differs from deletion base")
    target = gate.get("target") or {}
    authorized_attr_lines = list(target.get("remove_only_legacy_gitattributes_lines") or [])
    require(
        target.get("legacy_root") == LEGACY_ROOT
        and target.get("canonical_root") == CANONICAL_ROOT
        and target.get("delete_legacy_root") is True
        and target.get("legacy_file_count") == 33
        and target.get("modify_gitattributes") is True
        and len(authorized_attr_lines) == 24
        and target.get("canonical_gitattributes_rule_must_remain") == CANONICAL_ATTR
        and target.get("delete_other_surfaces") is False,
        "ChatGPT deletion gate target drift",
    )

    prior = {
        surface_id: validate_prior_retirement(src, surface_id, spec)
        for surface_id, spec in PRIOR_RETIREMENTS.items()
    }

    require(not current_exists(src, LEGACY_ROOT), "authorized ChatGPT compatibility tree still exists")
    require(current_exists(src, CANONICAL_ROOT), "canonical ChatGPT distribution is missing")
    legacy_files = tree_files_at(args.prepared_against, LEGACY_ROOT)
    canonical_base_files = tree_files_at(args.prepared_against, CANONICAL_ROOT)
    canonical_now_files = current_tree_files(src, CANONICAL_ROOT)
    require(len(legacy_files) == 33, f"expected 33 legacy ChatGPT files, got {len(legacy_files)}")
    require(legacy_files == canonical_base_files == canonical_now_files, "canonical ChatGPT file set drift")

    byte_mismatches = []
    for rel in legacy_files:
        legacy_raw = git_bytes(args.prepared_against, f"{LEGACY_ROOT}/{rel}")
        canonical_raw = current_tree_bytes(src, CANONICAL_ROOT, rel)
        if legacy_raw != canonical_raw:
            byte_mismatches.append(rel)
    require(byte_mismatches == [], f"canonical ChatGPT bytes drifted: {byte_mismatches}")

    expected_deleted = sorted(f"{LEGACY_ROOT}/{rel}" for rel in legacy_files)
    deleted, changed, untracked = changed_paths(args.prepared_against, src)
    require(deleted == expected_deleted, f"tracked deletion scope drift: {deleted}")
    non_target = set(changed) - set(expected_deleted)
    require(
        non_target <= ALLOWED_SUPPORT_CHANGES,
        f"non-retirement-support tracked changes: {sorted(non_target - ALLOWED_SUPPORT_CHANGES)}",
    )
    require(
        set(untracked) <= ALLOWED_SUPPORT_CHANGES,
        f"non-retirement-support untracked changes: {sorted(set(untracked) - ALLOWED_SUPPORT_CHANGES)}",
    )

    base_attr_lines = git_text(args.prepared_against, ".gitattributes").splitlines()
    current_attr_lines = current_text(src, ".gitattributes").splitlines()
    authorized_set = set(authorized_attr_lines)
    require(len(authorized_set) == 24, "authorized .gitattributes line set is not exactly 24 unique lines")
    expected_attr_lines = [line for line in base_attr_lines if line not in authorized_set]
    require(current_attr_lines == expected_attr_lines, ".gitattributes changed beyond the authorized legacy lines")
    require(all(line not in current_attr_lines for line in authorized_attr_lines), "legacy .gitattributes rule remains")
    require(CANONICAL_ATTR in current_attr_lines, "canonical ChatGPT .gitattributes rule was removed")

    canonical_diff = subprocess.run(
        ["git", "diff", "--quiet", args.prepared_against] + ([src] if src else []) + ["--", CANONICAL_ROOT],
        cwd=ROOT,
    )
    require(canonical_diff.returncode == 0, "canonical ChatGPT distribution changed in deletion")

    policy_now = current_json(src, POLICY_REL)
    policy_base = git_json(args.prepared_against, POLICY_REL)
    require(csha(policy_now) == csha(policy_base), "external-effect policy authority changed")

    restore = gate.get("restore_anchor") or {}
    require(
        restore.get("source_commit_sha") == "774d4e6164277057f91eb5681551735a1928404f"
        and restore.get("legacy_root") == LEGACY_ROOT
        and restore.get("git_tree_sha1") == "d7961fe63ff483b0085d9689b8b3c1b4d35a35f4"
        and restore.get("file_count") == 33
        and restore.get("manifest_sha256") == "9d99f8dc6f7f5dc0972cb66dcc3dbba38e5ba5e272d7a3aed4588acfb26193bb"
        and restore.get("legacy_gitattributes_line_count") == 24
        and restore.get("legacy_gitattributes_sha256") == "dd0fe2cd643d43a7eae46b016e4403856f6f74dc9a64b414e2a64ad9326a530f",
        "ChatGPT restore anchor drift",
    )
    tree_sha = subprocess.check_output(
        ["git", "rev-parse", f"{restore['source_commit_sha']}:{LEGACY_ROOT}"],
        cwd=ROOT,
        text=True,
    ).strip()
    require(tree_sha == restore.get("git_tree_sha1"), "legacy ChatGPT restore tree no longer resolves")
    attr_hash = hashlib.sha256(("\n".join(authorized_attr_lines) + "\n").encode("utf-8")).hexdigest()
    require(attr_hash == restore.get("legacy_gitattributes_sha256"), "legacy attribute restore hash drift")

    replay: dict[str, Any] = {}
    for name, spec in HISTORICAL_REPLAY.items():
        current_raw = current_bytes(src, spec["receipt"])
        anchor_raw = git_bytes(spec["commit"], spec["receipt"])
        require(current_raw == anchor_raw, f"{name}: historical ChatGPT receipt bytes drifted")
        replay[name] = {
            **spec,
            "receipt_sha256": hashlib.sha256(current_raw).hexdigest(),
            "receipt_matches_creation_commit": True,
        }

    safe_refs, blockers = legacy_references(src)
    require(blockers == [], f"active/ambiguous legacy ChatGPT references remain: {blockers}")

    require(
        POST_GATE_MAIN_CI["sha"] == args.prepared_against
        and POST_GATE_MAIN_CI["event"] == "push"
        and POST_GATE_MAIN_CI["conclusion"] == "success",
        "post-gate main CI evidence invalid",
    )

    criteria = {
        "merged_gate_is_pass_and_exactly_authorizes_chatgpt_core_bundle": True,
        "gate_itself_did_not_perform_deletion": True,
        "post_gate_current_main_ci_is_success": True,
        "four_prior_retirements_remain_authoritative": True,
        "authorized_legacy_chatgpt_tree_is_absent": True,
        "all_33_authorized_legacy_files_are_deleted": True,
        "no_other_tracked_path_is_deleted": True,
        "only_authorized_legacy_gitattributes_lines_are_removed": True,
        "canonical_gitattributes_rule_remains": True,
        "canonical_distribution_file_set_is_unchanged": True,
        "canonical_distribution_bytes_match_retired_legacy": True,
        "external_effect_authority_is_unchanged": True,
        "exact_restore_tree_and_manifest_remain_valid": True,
        "legacy_attribute_restore_anchor_remains_valid": True,
        "historical_chatgpt_receipts_remain_byte_anchored": True,
        "remaining_legacy_references_are_evidence_or_history_only": True,
        "retirement_is_limited_to_chatgpt_core_bundle": True,
    }

    report = {
        "schema": "velvetos.stage8d-chatgpt-deletion.v1",
        "stage": "8D_CHATGPT_DELETION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "chatgpt_core_bundle",
        "gate": {
            "receipt": GATE_REL,
            "gate_head_sha": GATE_HEAD,
            "gate_merge_sha": GATE_MERGE,
            "gate_pr": GATE_PR,
            "repository_assessment": "PASS",
            "delete_authorized": True,
            "authorized_root": LEGACY_ROOT,
            "authorized_legacy_gitattributes_line_count": 24,
        },
        "post_gate_main_ci": POST_GATE_MAIN_CI,
        "prior_retirements": prior,
        "deletion": {
            "legacy_path": LEGACY_ROOT,
            "canonical_path": CANONICAL_ROOT,
            "legacy_present": False,
            "deleted_file_count": len(expected_deleted),
            "deleted_paths": expected_deleted,
            "delete_exactly": [LEGACY_ROOT],
            "legacy_gitattributes_lines_removed": authorized_attr_lines,
            "legacy_gitattributes_line_count_removed": 24,
            "canonical_gitattributes_rule_present": True,
            "deletion_performed": True,
            "other_surfaces_deleted": False,
        },
        "current_evidence": {
            "runtime_authority": False,
            "active_authority": "instance:surface:chatgptProject",
            "canonical_file_count": len(canonical_now_files),
            "canonical_file_set_unchanged": True,
            "canonical_bytes_equal_retired_legacy": True,
            "byte_mismatches": [],
            "safe_legacy_references": safe_refs,
            "active_or_ambiguous_legacy_reference_count": 0,
            "external_effect_authority_unchanged": True,
        },
        "restore_anchor": {
            "source_commit_sha": restore.get("source_commit_sha"),
            "legacy_root": LEGACY_ROOT,
            "git_tree_sha1": restore.get("git_tree_sha1"),
            "file_count": restore.get("file_count"),
            "manifest_sha256": restore.get("manifest_sha256"),
            "legacy_gitattributes_line_count": restore.get("legacy_gitattributes_line_count"),
            "legacy_gitattributes_sha256": restore.get("legacy_gitattributes_sha256"),
            "restore_bundle_command": restore.get("restore_bundle_command"),
            "verified_after_deletion": True,
        },
        "historical_replay": replay,
        "authority": {
            "active_authority": "instance:surface:chatgptProject",
            "policy_registry_sha256": csha(policy_now),
            "external_effect_authority_changed": False,
            "delete_authorized_surface": "chatgpt_core_bundle",
            "retirement_authorized": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": True,
        "retirement_authorized": True,
        "next_action": (
            "Run exact-SHA selector plus an independent full suite, merge this final isolated Stage 8D "
            "compatibility deletion, verify the merge SHA and main CI, then complete the Stage 8D final acceptance."
        ),
        "constraints": [
            "all five compatibility surfaces are now retirement-complete only after this deletion merges",
            "canonical Velvet Factory ChatGPT distribution remains authoritative and untouched",
            "historical ChatGPT receipts remain byte-anchored to creation commits",
            "restore anchors remain available in Git history",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "ChatGPT deletion acceptance criteria failed")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_CHATGPT_DELETION "
        f"assessment=PASS deletion_performed=true retirement_authorized=true "
        f"files={len(expected_deleted)} attrs=24 canonical={len(canonical_now_files)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
