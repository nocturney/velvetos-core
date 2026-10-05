#!/usr/bin/env python3
"""Generate the isolated Stage 8D tool_status deletion-completion receipt.

This generator never deletes files. It proves that the merged deletion gate
authorized exactly the legacy TOOL-STATUS compatibility composite, that only
that compatibility path is absent, and that canonical tool-status authority,
historical evidence, restore evidence, and external-effect authority remain
intact.
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
OUT = REPORTS / "stage8d-tool-status-deletion.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
GATE = REPORTS / "stage8d-tool-status-deletion-gate.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY = "packages/velvetos/TOOL-STATUS.json"
CONTRACT = "packages/velvetos/tool-status-contract.json"
STATE = "instances/velvet-factory/instance/tool-status.json"
CHATGPT = "packages/velvetos/chatgpt-project"
PREPARED_MAIN = "376652dc035e2e6a0cdb59453f1c37c79b42f872"
GATE_HEAD = "e46a752929781091d6b5cf724418b716a04f5b84"
GATE_PR = 553
POST_GATE_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37310304615,
    "run_attempt": 2,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T12:33:05Z",
    "run_started_at": "2026-10-05T12:35:32Z",
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
}
EXPECTED_SAFE = {
    "packages/velvetos/CORE.json": "rollback_contract_reference",
    "packages/velvetos/policy/sensor-registry.json": "rollback_sensor_binding",
    "packages/velvetos/schema/tool-status-contract.schema.json": "rollback_contract_schema_reference",
    "packages/velvetos/tool-status-contract.json": "rollback_contract_reference",
    "packages/velvetos/tool_status_resolver.py": "rollback_parity_implementation",
    "scripts/check-velvetos.py": "rollback_parity_sensor",
}
HISTORICAL_REPLAY = {
    "consumer_migration": {
        "commit": "541de91794e07b23493304e4af7d653849be869a",
        "receipt": "packages/velvetos/policy/reports/stage8d-tool-status-consumer-migration.json",
    },
    "semantic_correction": {
        "commit": "e43ee067c702603ae54e4f295939a8c4a723432e",
        "receipt": "packages/velvetos/policy/reports/stage8d-tool-status-semantic-correction.json",
    },
    "rollback_closure": {
        "commit": "5d218b18305bb09c0b1a2f78d118c0a3acb4a329",
        "receipt": "packages/velvetos/policy/reports/stage8d-tool-status-rollback-closure.json",
    },
}
ALLOWED_RETIREMENT_SUPPORT_CHANGES = {
    "CHANGELOG.md",
    "README.md",
    "packages/velvetos/policy/README.md",
    "packages/velvetos/policy/reports/stage8d-tool-status-deletion.json",
    "packages/velvetos/tool_status_resolver.py",
    "scripts/check-policy-architecture.py",
    "scripts/check-velvetos.py",
    "scripts/generate-stage8d-retirement-semantic-audit.py",
    "scripts/generate-stage8d-tool-status-deletion.py",
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
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def csha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_commit() -> str | None:
    # While intentionally regenerating an already-committed receipt, use the
    # working tree. Once committed/merged, bind replay to the last commit that
    # changed the receipt so later repository drift cannot rewrite history.
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


def current_json(src: str | None, rel: str) -> dict[str, Any]:
    return git_json(src, rel) if src else load_json(ROOT / rel)


def current_bytes(src: str | None, rel: str) -> bytes:
    return git_bytes(src, rel) if src else (ROOT / rel).read_bytes()


def current_exists(src: str | None, rel: str) -> bool:
    return git_exists(src, rel) if src else (ROOT / rel).exists()


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None, "bad prepared SHA")
    require(args.prepared_against == PREPARED_MAIN, "tool_status deletion must use verified gate merge SHA")

    src = source_commit()
    gate_rel = GATE.relative_to(ROOT).as_posix()
    gate = current_json(src, gate_rel)
    require(
        gate.get("schema") == "velvetos.stage8d-tool-status-deletion-gate.v1"
        and gate.get("surface_id") == "tool_status"
        and gate.get("repository_assessment") == "PASS"
        and gate.get("delete_authorized") is True
        and gate.get("deletion_performed") is False
        and gate.get("retirement_authorized") is False,
        "merged tool_status deletion gate is invalid",
    )
    target = gate.get("target") or {}
    require(
        target.get("legacy_path") == LEGACY
        and target.get("canonical_contract_path") == CONTRACT
        and target.get("canonical_state_path") == STATE
        and target.get("delete_exactly") == [LEGACY]
        and target.get("delete_other_surfaces") is False,
        "tool_status gate target drift",
    )
    require(
        csha(gate) == csha(git_json(args.prepared_against, gate_rel)),
        "tool_status gate differs from verified deletion base",
    )

    prior = {
        surface_id: validate_prior_retirement(src, surface_id, spec)
        for surface_id, spec in PRIOR_RETIREMENTS.items()
    }
    require(not current_exists(src, LEGACY), "authorized TOOL-STATUS compatibility file still exists")
    require(current_exists(src, CONTRACT), "canonical tool-status contract missing")
    require(current_exists(src, STATE), "canonical tool-status state missing")
    require(current_exists(src, CHATGPT), "retained chatgpt_core_bundle is missing")

    deleted, changed, untracked = changed_paths(args.prepared_against, src)
    require(deleted == [LEGACY], f"deletion scope drift: {deleted}")
    non_target = set(changed) - {LEGACY}
    require(
        non_target <= ALLOWED_RETIREMENT_SUPPORT_CHANGES,
        f"non-retirement-support tracked changes: {sorted(non_target - ALLOWED_RETIREMENT_SUPPORT_CHANGES)}",
    )
    require(
        set(untracked) <= ALLOWED_RETIREMENT_SUPPORT_CHANGES,
        f"non-retirement-support untracked changes: {sorted(set(untracked) - ALLOWED_RETIREMENT_SUPPORT_CHANGES)}",
    )

    cmd = ["git", "diff", "--quiet", args.prepared_against]
    if src:
        cmd.append(src)
    cmd.extend(["--", CHATGPT])
    require(subprocess.run(cmd, cwd=ROOT).returncode == 0, "chatgpt_core_bundle changed in tool_status deletion")

    legacy = git_json(args.prepared_against, LEGACY)
    contract = current_json(src, CONTRACT)
    state = current_json(src, STATE)
    composition = contract.get("composition") or {}
    require(composition.get("activeAuthority") == "instance:surface:toolStatus", "active authority drift")
    require(composition.get("rollbackCompatibilityPath") == LEGACY, "rollback compatibility path drift")
    require(composition.get("consumerCutover") is True, "consumer cutover drift")
    composed = {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }
    parity = csha(composed) == csha(legacy)
    require(parity, "canonical tool-status composition no longer matches deleted compatibility composite")

    check_velvetos_text = current_bytes(src, "scripts/check-velvetos.py").decode("utf-8", errors="replace")
    resolver_text = current_bytes(src, "packages/velvetos/tool_status_resolver.py").decode("utf-8", errors="replace")
    require(
        "if LEGACY_TOOL_STATUS.is_file()" in check_velvetos_text
        and "TOOL_STATUS_DELETION_RECEIPT" in check_velvetos_text
        and "canonical_composed_sha256" in check_velvetos_text,
        "check-velvetos retired tool-status validation is not receipt/hash anchored",
    )
    require(
        "if legacy_path.is_file()" in resolver_text
        and "DELETION_RECEIPT_REL" in resolver_text
        and "retired legacy parity anchor" in resolver_text,
        "tool_status_resolver legacy-parity command is not retirement-aware",
    )

    gate_evidence = gate.get("current_evidence") or {}
    require(
        gate_evidence.get("content_validated_safe_references") == EXPECTED_SAFE
        and gate_evidence.get("safe_reference_count") == 6
        and gate_evidence.get("runtime_authority") is False
        and gate_evidence.get("active_authority") == "instance:surface:toolStatus",
        "tool_status safe-reference evidence drift",
    )
    for rel in EXPECTED_SAFE:
        require(current_exists(src, rel), f"{rel}: rollback/parity reference disappeared unexpectedly")

    policy_rel = POLICY.relative_to(ROOT).as_posix()
    policy_now = current_json(src, policy_rel)
    policy_base = git_json(args.prepared_against, policy_rel)
    require(csha(policy_now) == csha(policy_base), "external-effect policy authority changed")

    restore = gate.get("restore_anchor") or {}
    restore_source = str(restore.get("source_commit_sha") or "")
    raw = git_bytes(restore_source, LEGACY)
    require(
        restore_source == "3f7bd148ebf31dae67a02e86ba2b8727dc14c171"
        and restore.get("git_blob_sha1") == "e5bb196c5bfd0a0bd5b6fe95df1549de9b1d2372"
        and restore.get("sha256") == "0b1f082887c9e4d5367574b746bee36f62f4aced0f8cf631a08551e553030add"
        and hashlib.sha256(raw).hexdigest() == restore.get("sha256")
        and len(raw) == restore.get("size_bytes") == 6753,
        "tool_status restore anchor drift",
    )

    replay: dict[str, Any] = {}
    for name, spec in HISTORICAL_REPLAY.items():
        receipt_raw = current_bytes(src, spec["receipt"])
        anchor_raw = git_bytes(spec["commit"], spec["receipt"])
        require(receipt_raw == anchor_raw, f"{name}: historical receipt bytes drifted")
        replay[name] = {
            **spec,
            "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "receipt_matches_creation_commit": True,
        }

    require(
        POST_GATE_MAIN_CI["sha"] == args.prepared_against
        and POST_GATE_MAIN_CI["event"] == "push"
        and POST_GATE_MAIN_CI["conclusion"] == "success"
        and POST_GATE_MAIN_CI["run_attempt"] == 2,
        "post-gate main CI evidence is not the verified successful rerun",
    )

    criteria = {
        "merged_gate_is_pass_and_exactly_authorizes_tool_status": True,
        "gate_itself_did_not_perform_deletion": True,
        "gate_merge_main_push_ci_rerun_is_success": True,
        "authorized_tool_status_is_absent": True,
        "no_other_tracked_path_is_deleted": True,
        "non_target_changes_are_retirement_support_only": True,
        "three_prior_retirements_remain_authoritative": True,
        "chatgpt_core_bundle_is_present_and_unchanged": True,
        "canonical_composition_remains_exactly_parity_equal": parity,
        "active_authority_remains_instance_surface_tool_status": True,
        "six_rollback_parity_references_remain_bounded": True,
        "external_effect_authority_is_unchanged": True,
        "exact_restore_anchor_still_resolves": True,
        "historical_tool_status_receipts_remain_byte_anchored": True,
        "retirement_is_limited_to_tool_status": True,
    }

    report = {
        "schema": "velvetos.stage8d-tool-status-deletion.v1",
        "stage": "8D_TOOL_STATUS_DELETION",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "tool_status",
        "gate": {
            "receipt": gate_rel,
            "gate_head_sha": GATE_HEAD,
            "gate_merge_sha": args.prepared_against,
            "gate_pr": GATE_PR,
            "repository_assessment": "PASS",
            "delete_authorized": True,
            "authorized_paths": [LEGACY],
        },
        "post_gate_main_ci": POST_GATE_MAIN_CI,
        "prior_retirements": prior,
        "deletion": {
            "legacy_path": LEGACY,
            "canonical_contract_path": CONTRACT,
            "canonical_state_path": STATE,
            "legacy_present": False,
            "deleted_paths": deleted,
            "delete_exactly": [LEGACY],
            "deletion_performed": True,
            "other_surfaces_deleted": False,
        },
        "retained_surface_isolation": {
            "chatgpt_core_bundle": {
                "path": CHATGPT,
                "present": True,
                "unchanged_from_prepared_against": True,
                "deletion_authorized": False,
            }
        },
        "current_evidence": {
            "runtime_authority": False,
            "active_authority": "instance:surface:toolStatus",
            "content_validated_safe_references": EXPECTED_SAFE,
            "safe_reference_count": 6,
            "retired_legacy_validation": {
                "mode": "deletion_receipt_hash_anchor",
                "live_legacy_file_read_required": False,
                "validators": [
                    "scripts/check-velvetos.py",
                    "packages/velvetos/tool_status_resolver.py",
                ],
            },
            "canonical_composed_sha256": csha(composed),
            "legacy_canonical_sha256": csha(legacy),
            "canonical_composition_exact_equal": parity,
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
            "active_authority": "instance:surface:toolStatus",
            "policy_registry_sha256": csha(policy_now),
            "external_effect_authority_changed": False,
            "delete_authorized_surface": "tool_status",
            "retirement_authorized": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": True,
        "retirement_authorized": True,
        "next_action": (
            "Run exact-SHA selector plus an independent full suite, merge only this isolated tool_status deletion PR, "
            "verify the merge SHA locally and with main push CI, then open the separate chatgpt_core_bundle deletion gate."
        ),
        "constraints": [
            "one compatibility surface retired per deletion PR",
            "sample_profile, root_desk and fleet remain retired and are not modified",
            "chatgpt_core_bundle remains deletion-unauthorized by this receipt",
            "historical tool_status receipts remain byte-anchored to creation commits",
            "restore anchor remains available in Git history",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "tool_status deletion acceptance criteria failed")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_TOOL_STATUS_DELETION "
        f"assessment=PASS deletion_performed=true retirement_authorized=true "
        f"path={LEGACY} parity={str(parity).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
