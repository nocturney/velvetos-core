#!/usr/bin/env python3
"""Generate the isolated Stage 8D fleet deletion-completion receipt.

This generator never deletes files. It runs on the isolated deletion candidate
and proves that only the gate-authorized fleet compatibility file is absent.
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
OUT = REPORTS / "stage8d-fleet-deletion.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
GATE = REPORTS / "stage8d-fleet-deletion-gate.json"
SAMPLE_RETIREMENT = REPORTS / "stage8d-sample-profile-deletion.json"
ROOT_RETIREMENT = REPORTS / "stage8d-root-desk-deletion.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY = "packages/vfprod/FLEET.json"
CANONICAL = "instances/velvet-factory/instance/fleet.json"
SAMPLE_LEGACY = "packages/velvetos/samples/velvet-factory.json"
ROOT_LEGACY = ".cursor/vf-desk.json"
PREPARED_MAIN = "416ea12b125d0ad3b276165413403cab56dc5635"
GATE_HEAD = "e98015e7650a74619d00457f56dab2f65fdce66e"
GATE_PR = 551
POST_GATE_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37296310577,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T10:23:51Z",
}
OTHER_SURFACES = {
    "tool_status": "packages/velvetos/TOOL-STATUS.json",
    "chatgpt_core_bundle": "packages/velvetos/chatgpt-project",
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
HISTORICAL_REPLAY = {
    "stage8c_control_api_fleet": {
        "commit": "df183de7f4f40ea691f7746646d5fb3ef0ba1e06",
        "generator": "scripts/generate-stage8c-control-api-fleet.py",
        "receipt": "packages/velvetos/policy/reports/stage8c-control-api-fleet.json",
    },
    "stage8d_fleet_consumer_migration": {
        "commit": "b68439c0c593ce2d506b93295bc7ac473c0a184d",
        "generator": "scripts/generate-stage8d-fleet-consumer-migration.py",
        "receipt": "packages/velvetos/policy/reports/stage8d-fleet-consumer-migration.json",
    },
    "stage8d_fleet_runtime_correction": {
        "commit": "dd528b857ac7cdb88d0043864338e87ede177402",
        "generator": "scripts/generate-stage8d-fleet-runtime-consumer-correction.py",
        "receipt": "packages/velvetos/policy/reports/stage8d-fleet-runtime-consumer-correction.json",
    },
    "stage8d_fleet_rollback_closure": {
        "commit": "a2fc177cb7b39a3f647ea32c71c2ca41b4564bc5",
        "generator": "scripts/generate-stage8d-fleet-rollback-closure.py",
        "receipt": "packages/velvetos/policy/reports/stage8d-fleet-rollback-closure.json",
    },
}
ALLOWED_EVIDENCE_CHANGES = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "packages/velvetos/policy/reports/stage8d-fleet-deletion.json",
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8c-control-api-fleet.py",
    "scripts/generate-stage8d-retirement-semantic-audit.py",
    "scripts/generate-stage8d-fleet-deletion.py",
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
    value = proc.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value or "") else None


def csha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def changed_paths(base: str, commit: str | None = None) -> tuple[list[str], list[str], list[str]]:
    cmd = ["git", "diff", "--name-status", base]
    if commit:
        cmd.append(commit)
    cmd.append("--")
    proc = subprocess.run(
        cmd, cwd=ROOT, text=True, capture_output=True,
        encoding="utf-8", errors="replace", check=True,
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
            cwd=ROOT, text=True, capture_output=True,
            encoding="utf-8", errors="replace", check=True,
        )
        untracked = sorted({
            line.strip().replace("\\", "/")
            for line in extra.stdout.splitlines() if line.strip()
        })
    return sorted(set(deleted)), sorted(set(changed)), untracked


def current_json(src: str | None, rel: str) -> dict[str, Any]:
    return git_json(src, rel) if src else load_json(ROOT / rel)


def current_text(src: str | None, rel: str) -> str:
    return git_text(src, rel) if src else (ROOT / rel).read_text(encoding="utf-8-sig")


def current_exists(src: str | None, rel: str) -> bool:
    return git_exists(src, rel) if src else (ROOT / rel).exists()


def validate_prior_retirement(
    receipt: dict[str, Any], surface_id: str, legacy_path: str, schema: str
) -> None:
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
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None, "bad prepared SHA")
    require(args.prepared_against == PREPARED_MAIN, "fleet deletion must use the verified gate merge SHA")

    src = source_commit()
    gate = current_json(src, GATE.relative_to(ROOT).as_posix())
    sample = current_json(src, SAMPLE_RETIREMENT.relative_to(ROOT).as_posix())
    root_retirement = current_json(src, ROOT_RETIREMENT.relative_to(ROOT).as_posix())

    require(
        gate.get("schema") == "velvetos.stage8d-fleet-deletion-gate.v1"
        and gate.get("surface_id") == "fleet"
        and gate.get("repository_assessment") == "PASS"
        and gate.get("delete_authorized") is True
        and gate.get("deletion_performed") is False
        and gate.get("retirement_authorized") is False,
        "merged fleet deletion gate is invalid",
    )
    target = gate.get("target") or {}
    require(
        target.get("legacy_path") == LEGACY
        and target.get("canonical_path") == CANONICAL
        and target.get("delete_exactly") == [LEGACY]
        and target.get("delete_other_surfaces") is False,
        "fleet gate target drift",
    )
    require(
        csha(gate) == csha(git_json(args.prepared_against, GATE.relative_to(ROOT).as_posix())),
        "fleet gate differs from verified deletion base",
    )

    validate_prior_retirement(
        sample, "sample_profile", SAMPLE_LEGACY,
        "velvetos.stage8d-sample-profile-deletion.v1",
    )
    validate_prior_retirement(
        root_retirement, "root_desk", ROOT_LEGACY,
        "velvetos.stage8d-root-desk-deletion.v1",
    )
    require(not current_exists(src, SAMPLE_LEGACY), "retired sample_profile unexpectedly present")
    require(not current_exists(src, ROOT_LEGACY), "retired root_desk unexpectedly present")

    legacy_present = current_exists(src, LEGACY)
    canonical_present = current_exists(src, CANONICAL)
    require(not legacy_present, "authorized fleet compatibility file still exists")
    require(canonical_present, "canonical instance fleet is missing")

    deleted, changed, untracked = changed_paths(args.prepared_against, src)
    require(deleted == [LEGACY], f"deletion scope drift: {deleted}")
    non_target = set(changed) - {LEGACY}
    require(
        non_target <= ALLOWED_EVIDENCE_CHANGES,
        f"non-evidence tracked changes: {sorted(non_target - ALLOWED_EVIDENCE_CHANGES)}",
    )
    require(
        set(untracked) <= ALLOWED_EVIDENCE_CHANGES,
        f"non-evidence untracked changes: {sorted(set(untracked) - ALLOWED_EVIDENCE_CHANGES)}",
    )

    retained_state: dict[str, Any] = {}
    for surface_id, rel in OTHER_SURFACES.items():
        require(current_exists(src, rel), f"{surface_id}: retained compatibility surface missing")
        cmd = ["git", "diff", "--quiet", args.prepared_against]
        if src:
            cmd.append(src)
        cmd.extend(["--", rel])
        require(subprocess.run(cmd, cwd=ROOT).returncode == 0, f"{surface_id}: retained surface changed")
        retained_state[surface_id] = {
            "path": rel,
            "present": True,
            "unchanged_from_prepared_against": True,
            "deletion_authorized": False,
        }

    legacy = git_json(args.prepared_against, LEGACY)
    canonical = current_json(src, CANONICAL)
    exact_parity = legacy == canonical and csha(legacy) == csha(canonical)
    require(exact_parity, "canonical fleet no longer exactly matches deleted compatibility fleet")
    require(len(legacy.get("printers") or []) == 4, "fleet printer count drift")

    code_rows: dict[str, dict[str, bool]] = {}
    for rel in MIGRATED_CODE:
        text = current_text(src, rel)
        no_legacy = LEGACY not in text
        canonical_binding = ("resolve_surface" in text and '"fleet"' in text) or "instance/fleet.json" in text
        code_rows[rel] = {
            "legacy_path_absent": no_legacy,
            "canonical_fleet_binding_present": canonical_binding,
        }
        require(no_legacy and canonical_binding, f"{rel}: fleet runtime reader regressed")

    doc_rows: dict[str, dict[str, bool]] = {}
    for rel in ACTIVE_DOCS:
        text = current_text(src, rel)
        no_legacy = LEGACY not in text
        doc_rows[rel] = {"legacy_path_absent": no_legacy}
        require(no_legacy, f"{rel}: active documentation reintroduced legacy fleet path")

    policy_now = current_json(src, POLICY.relative_to(ROOT).as_posix())
    policy_base = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    require(csha(policy_now) == csha(policy_base), "external-effect authority changed")

    restore = gate.get("restore_anchor") or {}
    restore_source = str(restore.get("source_commit_sha") or "")
    require(re.fullmatch(r"[0-9a-f]{40}", restore_source) is not None, "fleet restore source SHA drift")
    raw = git_bytes(restore_source, LEGACY)
    require(
        restore_source == "12e8ea4c0a38286eccc30972579270739411b5f2"
        and restore.get("git_blob_sha1") == "d76126ce8ac08b5faf86b5069df18886118b8f1a"
        and hashlib.sha256(raw).hexdigest() == restore.get("sha256")
        and restore.get("sha256") == "baffa4db8f61d33339f89161155e620d0914a802fe230b241a566bdadb085f3c"
        and len(raw) == restore.get("size_bytes") == 1364,
        "fleet restore anchor drift",
    )

    replay: dict[str, Any] = {}
    for name, row in HISTORICAL_REPLAY.items():
        receipt_raw = git_bytes(src, row["receipt"]) if src else (ROOT / row["receipt"]).read_bytes()
        anchor_raw = git_bytes(row["commit"], row["receipt"])
        require(receipt_raw == anchor_raw, f"{name}: historical receipt bytes drifted")
        replay[name] = {
            **row,
            "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "receipt_matches_anchor_commit": True,
        }

    require(
        POST_GATE_MAIN_CI["sha"] == args.prepared_against
        and POST_GATE_MAIN_CI["event"] == "push"
        and POST_GATE_MAIN_CI["conclusion"] == "success",
        "post-gate main CI is not bound to deletion base",
    )

    criteria = {
        "merged_gate_is_pass_and_exactly_authorizes_fleet": True,
        "gate_itself_did_not_perform_deletion": True,
        "gate_merge_main_push_ci_is_success": True,
        "authorized_fleet_is_absent": True,
        "no_other_tracked_path_is_deleted": True,
        "non_target_changes_are_evidence_only": True,
        "sample_profile_retirement_remains_authoritative": True,
        "root_desk_retirement_remains_authoritative": True,
        "tool_status_and_chatgpt_surfaces_are_present_and_unchanged": True,
        "canonical_fleet_remains_exactly_equal_to_deleted_legacy": exact_parity,
        "all_live_fleet_readers_remain_canonical": True,
        "all_active_fleet_documentation_remains_canonical": True,
        "external_effect_authority_is_unchanged": True,
        "exact_restore_anchor_still_resolves": True,
        "historical_fleet_receipts_remain_byte_anchored": True,
        "retirement_is_limited_to_fleet": True,
    }

    report = {
        "schema": "velvetos.stage8d-fleet-deletion.v1",
        "stage": "8D_FLEET_DELETION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "fleet",
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
        "prior_retirements": {
            "sample_profile": {
                "receipt": SAMPLE_RETIREMENT.relative_to(ROOT).as_posix(),
                "repository_assessment": "PASS",
                "deletion_performed": True,
                "retirement_authorized": True,
            },
            "root_desk": {
                "receipt": ROOT_RETIREMENT.relative_to(ROOT).as_posix(),
                "repository_assessment": "PASS",
                "deletion_performed": True,
                "retirement_authorized": True,
            },
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
        "retained_surface_isolation": retained_state,
        "current_evidence": {
            "runtime_authority": False,
            "migrated_code": code_rows,
            "active_documentation": doc_rows,
            "canonical_legacy_exact_equal": exact_parity,
            "printer_count": len(legacy.get("printers") or []),
            "external_effect_authority_unchanged": True,
        },
        "restore_anchor": {
            "source_commit_sha": restore_source,
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
            "delete_authorized_surface": "fleet",
            "retirement_authorized": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": True,
        "retirement_authorized": True,
        "next_action": (
            "Run exact-SHA selector plus independent full suite, merge only this isolated fleet deletion PR, "
            "then verify the merge SHA locally and with main push CI before opening the tool_status deletion gate."
        ),
        "constraints": [
            "one compatibility surface retired per deletion PR",
            "sample_profile and root_desk remain retired and are not modified",
            "tool_status and chatgpt_core_bundle remain deletion-unauthorized by this receipt",
            "historical fleet receipts remain byte-anchored to their source snapshots",
            "restore anchor remains available in Git history",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "fleet deletion acceptance criteria failed")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_FLEET_DELETION "
        f"assessment=PASS deletion_performed=true retirement_authorized=true "
        f"path={LEGACY} restore_sha256={str(restore.get('sha256'))[:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
