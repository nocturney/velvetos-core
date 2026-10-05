#!/usr/bin/env python3
"""Generate the isolated Stage 8D chatgpt_core_bundle deletion gate.

Evidence-only: authorizes one later isolated retirement PR to remove the retained
Core ChatGPT compatibility bundle and only the legacy-specific .gitattributes
rules that exist solely to preserve that bundle's historical bytes. The canonical
Velvet Factory ChatGPT Project distribution remains untouched.
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
OUT = REPORTS / "stage8d-chatgpt-deletion-gate.json"
CLOSURE = REPORTS / "stage8d-chatgpt-rollback-closure.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"

LEGACY_ROOT = "packages/velvetos/chatgpt-project"
CANONICAL_ROOT = "instances/velvet-factory/distribution/chatgpt-project"
LEGACY_PREFIX = "/" + LEGACY_ROOT + "/"
CANONICAL_ATTR = "/instances/velvet-factory/distribution/chatgpt-project/** -whitespace"
PREPARED_MAIN = "774d4e6164277057f91eb5681551735a1928404f"
LATEST_MAIN_CI = {
    "workflow": "VelvetOS Core Sensors",
    "run_id": 37319349828,
    "run_attempt": 1,
    "sha": PREPARED_MAIN,
    "event": "push",
    "conclusion": "success",
    "created_at": "2026-10-05T13:46:04Z",
    "run_started_at": "2026-10-05T13:46:04Z",
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
EXPECTED_SAFE = {
    ".gitattributes": "rollback_git_attributes",
    "packages/velvetos/policy/sensor-registry.json": "canonical_sensor_binding",
    "packages/vfbrand/brand-tokens.json": "canonical_asset_source",
    "scripts/check-project-bundle.py": "canonical_surface_sensor",
    "scripts/check-reel-route-sync.py": "canonical_surface_sensor",
    "scripts/check-velvetos.py": "canonical_surface_sensor",
}


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


def tree_files(sha: str, root: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", sha, "--", root],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    prefix = root.rstrip("/") + "/"
    return sorted(line[len(prefix):] for line in out.splitlines() if line.startswith(prefix))


def tree_sha(sha: str, root: str) -> str:
    value = subprocess.check_output(
        ["git", "rev-parse", f"{sha}:{root}"], cwd=ROOT, text=True
    ).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, "invalid ChatGPT legacy tree SHA")
    return value


def manifest_rows(sha: str, root: str, files: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in files:
        raw = git_bytes(sha, f"{root}/{rel}")
        rows.append({"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    return rows


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


def validate_retirement(sha: str, surface_id: str, spec: dict[str, str]) -> dict[str, Any]:
    rel = (REPORTS / spec["receipt"]).relative_to(ROOT).as_posix()
    receipt = git_json(sha, rel)
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
        and not git_exists(sha, spec["legacy"]),
        f"{surface_id}: prior retirement receipt or absence drift",
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
    require(args.prepared_against == PREPARED_MAIN, "ChatGPT deletion gate must use verified exact main")

    closure_rel = CLOSURE.relative_to(ROOT).as_posix()
    closure = git_json(args.prepared_against, closure_rel)
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    require(
        closure.get("schema") == "velvetos.stage8d-chatgpt-rollback-closure.v1"
        and closure.get("surface_id") == "chatgpt_core_bundle"
        and closure.get("repository_assessment") == "PASS"
        and closure.get("rollback_window_closed") is True
        and closure.get("retirement_ready_for_deletion_gate") is True
        and closure.get("delete_authorized") is False
        and closure.get("retirement_authorized") is False,
        "ChatGPT rollback closure is not a valid deletion-gate prerequisite",
    )

    prior = {
        surface_id: validate_retirement(args.prepared_against, surface_id, spec)
        for surface_id, spec in PRIOR_RETIREMENTS.items()
    }

    require(git_exists(args.prepared_against, LEGACY_ROOT), "legacy ChatGPT bundle is missing before gate")
    require(git_exists(args.prepared_against, CANONICAL_ROOT), "canonical ChatGPT distribution is missing")
    legacy_files = tree_files(args.prepared_against, LEGACY_ROOT)
    canonical_files = tree_files(args.prepared_against, CANONICAL_ROOT)
    require(legacy_files == canonical_files, "ChatGPT legacy/canonical file sets differ")
    require(len(legacy_files) == 33, f"expected 33 ChatGPT files, got {len(legacy_files)}")
    mismatches = [
        rel for rel in legacy_files
        if git_bytes(args.prepared_against, f"{LEGACY_ROOT}/{rel}")
        != git_bytes(args.prepared_against, f"{CANONICAL_ROOT}/{rel}")
    ]
    require(mismatches == [], f"ChatGPT legacy/canonical bytes differ: {mismatches}")

    closure_evidence = closure.get("current_evidence") or {}
    require(
        closure_evidence.get("runtime_authority") is False
        and closure_evidence.get("active_authority") == "instance:surface:chatgptProject"
        and closure_evidence.get("file_count") == 33
        and closure_evidence.get("file_sets_equal") is True
        and closure_evidence.get("byte_equal") is True
        and closure_evidence.get("safe_reference_count") == 6
        and closure_evidence.get("canonical_sensor_binding_count") == 18
        and closure_evidence.get("brand_asset_source_canonical") is True
        and closure_evidence.get("semantic_preflight_clear") is True
        and closure_evidence.get("all_stage8d_semantic_preflights_clear") is True
        and closure_evidence.get("external_effect_authority_unchanged") is True,
        "ChatGPT closure current evidence drift",
    )
    require(
        closure_evidence.get("content_validated_safe_references") == EXPECTED_SAFE,
        "ChatGPT closure safe-reference classification drift",
    )

    closure_sha = str(closure.get("prepared_against_main_sha") or "")
    require(re.fullmatch(r"[0-9a-f]{40}", closure_sha) is not None, "ChatGPT closure prepared SHA missing")
    require(
        tree_sha(args.prepared_against, LEGACY_ROOT) == tree_sha(closure_sha, LEGACY_ROOT),
        "legacy ChatGPT tree changed after rollback closure",
    )
    require(
        git_bytes(args.prepared_against, ".gitattributes") == git_bytes(closure_sha, ".gitattributes"),
        ".gitattributes changed after ChatGPT rollback closure",
    )

    registry = git_text(args.prepared_against, "packages/velvetos/policy/sensor-registry.json").replace("\\", "/")
    brand = git_text(args.prepared_against, "packages/vfbrand/brand-tokens.json").replace("\\", "/")
    require(f"{LEGACY_ROOT}/" not in registry, "sensor registry reintroduced legacy ChatGPT bundle")
    require(registry.count(CANONICAL_ROOT + "/") == 18, "canonical sensor binding count drift")
    require(f"{LEGACY_ROOT}/" not in brand, "brand tokens reintroduced legacy ChatGPT bundle")
    require(CANONICAL_ROOT + "/ASSET-MANIFEST-v6.6.4.json" in brand, "brand source is not canonical")

    audit = run_audit(args.prepared_against, args.captured_at)
    surfaces = audit.get("compatibility_surfaces") or {}
    row = surfaces.get("chatgpt_core_bundle") or {}
    assessment = audit.get("assessment") or {}
    require(
        row.get("present") is True
        and row.get("retirement_preflight_clear") is True
        and row.get("retirement_preflight_blockers") == [],
        "current ChatGPT semantic preflight is not clear",
    )
    require(
        assessment.get("surfaces_total") == 5
        and assessment.get("surfaces_preflight_clear") == 5
        and assessment.get("surfaces_retired") == 4
        and assessment.get("retired_surfaces") == ["fleet", "root_desk", "sample_profile", "tool_status"]
        and (assessment.get("surfaces_with_candidate_blockers") or []) == [],
        "global semantic state is not 5/5 clear with exactly four retired surfaces",
    )

    attr_text = git_text(args.prepared_against, ".gitattributes")
    attr_lines = attr_text.splitlines()
    legacy_attr_lines = [line for line in attr_lines if line.startswith(LEGACY_PREFIX)]
    require(len(legacy_attr_lines) > 0, "legacy ChatGPT .gitattributes rules missing")
    require(CANONICAL_ATTR in attr_lines, "canonical ChatGPT .gitattributes preservation rule missing")
    require(all(CANONICAL_ROOT not in line for line in legacy_attr_lines), "legacy attr selection touched canonical rule")

    rows = manifest_rows(args.prepared_against, LEGACY_ROOT, legacy_files)
    manifest_sha256 = csha(rows)
    legacy_tree = tree_sha(args.prepared_against, LEGACY_ROOT)
    attr_sha256 = hashlib.sha256(("\n".join(legacy_attr_lines) + "\n").encode("utf-8")).hexdigest()

    authority = closure.get("authority") or {}
    policy_sha = csha(policy)
    require(
        authority.get("active_authority") == "instance:surface:chatgptProject"
        and authority.get("external_effect_authority_changed") is False
        and authority.get("policy_registry_sha256") == policy_sha,
        "external-effect policy authority changed since ChatGPT closure",
    )
    require(
        LATEST_MAIN_CI["sha"] == args.prepared_against
        and LATEST_MAIN_CI["event"] == "push"
        and LATEST_MAIN_CI["conclusion"] == "success",
        "latest exact-main CI evidence is invalid",
    )

    criteria = {
        "chatgpt_closure_is_pass_closed_and_gate_ready": True,
        "chatgpt_closure_did_not_pre_authorize_deletion": True,
        "four_prior_retirements_are_authoritatively_proven": True,
        "legacy_chatgpt_bundle_is_present": True,
        "canonical_chatgpt_distribution_is_present": True,
        "legacy_and_canonical_file_sets_are_equal": True,
        "legacy_and_canonical_bytes_are_equal": True,
        "legacy_bundle_is_exactly_33_files": True,
        "legacy_tree_is_unchanged_since_closure": True,
        "rollback_git_attributes_are_unchanged_since_closure": True,
        "legacy_git_attribute_rules_are_exactly_scoped": True,
        "canonical_git_attribute_rule_is_retained": True,
        "active_authority_remains_instance_surface_chatgpt_project": True,
        "sensor_registry_keeps_eighteen_canonical_bindings": True,
        "brand_asset_source_remains_canonical": True,
        "current_chatgpt_semantic_preflight_is_clear": True,
        "current_global_semantic_preflight_is_5_of_5_clear": True,
        "semantic_audit_recognizes_exactly_four_retired_surfaces": True,
        "exact_legacy_tree_and_file_manifest_are_restore_anchored": True,
        "latest_exact_main_core_sensor_run_is_success": True,
        "external_effect_authority_is_unchanged": True,
        "gate_authorizes_only_chatgpt_legacy_root_and_legacy_attr_cleanup": True,
        "deletion_is_not_performed_in_gate_change": True,
        "retirement_completion_waits_for_separate_deletion_pr": True,
    }

    report = {
        "schema": "velvetos.stage8d-chatgpt-deletion-gate.v1",
        "stage": "8D_CHATGPT_DELETION_GATE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "chatgpt_core_bundle",
        "target": {
            "legacy_root": LEGACY_ROOT,
            "canonical_root": CANONICAL_ROOT,
            "delete_legacy_root": True,
            "legacy_file_count": len(legacy_files),
            "modify_gitattributes": True,
            "remove_only_legacy_gitattributes_lines": legacy_attr_lines,
            "canonical_gitattributes_rule_must_remain": CANONICAL_ATTR,
            "delete_other_surfaces": False,
        },
        "purpose": (
            "Authorize one later isolated retirement PR to remove the retained Core ChatGPT compatibility "
            "bundle and only its legacy-specific byte-preservation attributes after revalidating exact "
            "canonical parity, rollback closure, four prior retirements, restore evidence and policy authority. "
            "This gate performs no deletion."
        ),
        "prerequisite_closure": {
            "receipt": closure_rel,
            "schema": closure.get("schema"),
            "rollback_window_closed": True,
            "retirement_ready_for_deletion_gate": True,
        },
        "prior_retirements": prior,
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_authority": "instance:surface:chatgptProject",
            "file_count": len(legacy_files),
            "file_sets_equal": True,
            "byte_equal": True,
            "mismatches": [],
            "content_validated_safe_references": EXPECTED_SAFE,
            "safe_reference_count": len(EXPECTED_SAFE),
            "canonical_sensor_binding_count": 18,
            "brand_asset_source_canonical": True,
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "retired_surfaces": ["fleet", "root_desk", "sample_profile", "tool_status"],
            "legacy_tree_unchanged_since_closure": True,
            "rollback_git_attributes_unchanged_since_closure": True,
            "external_effect_authority_unchanged": True,
        },
        "restore_anchor": {
            "source_commit_sha": args.prepared_against,
            "legacy_root": LEGACY_ROOT,
            "git_tree_sha1": legacy_tree,
            "file_count": len(rows),
            "manifest_sha256": manifest_sha256,
            "legacy_gitattributes_line_count": len(legacy_attr_lines),
            "legacy_gitattributes_sha256": attr_sha256,
            "legacy_gitattributes_lines": legacy_attr_lines,
            "restore_bundle_command": f"git checkout {args.prepared_against} -- {LEGACY_ROOT}",
        },
        "latest_main_ci": LATEST_MAIN_CI,
        "authority": {
            "active_authority": "instance:surface:chatgptProject",
            "policy_registry_sha256": policy_sha,
            "chatgpt_closure_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
            "delete_authorized": True,
            "delete_authorized_surface": "chatgpt_core_bundle",
            "delete_authorized_root": LEGACY_ROOT,
            "gitattributes_cleanup_authorized": True,
            "retirement_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "delete_authorized": True,
        "deletion_performed": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this evidence-only gate, verify post-merge main, then create a separate isolated "
            "chatgpt_core_bundle retirement PR that removes the authorized legacy root and only the "
            "recorded legacy-specific .gitattributes lines."
        ),
        "constraints": [
            "this gate does not delete files",
            "authorization applies only to the Core ChatGPT legacy root and recorded legacy .gitattributes lines",
            "the canonical Velvet Factory ChatGPT distribution must remain byte-identical and untouched",
            "sample_profile, root_desk, fleet and tool_status remain retired and are not modified",
            "actual deletion requires a separate isolated PR",
            "restore anchors remain available in Git history",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "ChatGPT deletion gate acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_CHATGPT_DELETION_GATE "
        f"assessment=PASS delete_authorized=true files={len(rows)} "
        f"tree={legacy_tree[:12]} attrs={len(legacy_attr_lines)} deletion_performed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
