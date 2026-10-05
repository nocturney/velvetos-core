#!/usr/bin/env python3
"""Generate Stage 8D ChatGPT Core compatibility rollback-window closure evidence."""
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
OUT = REPORTS / "stage8d-chatgpt-rollback-closure.json"
CORRECTION = REPORTS / "stage8d-chatgpt-semantic-correction.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"

LEGACY_ROOT = "/".join(["packages", "velvetos", "chatgpt-project"])
CANONICAL_ROOT = "instances/velvet-factory/distribution/chatgpt-project"
LEGACY_PREFIX = LEGACY_ROOT + "/"
CANONICAL_PREFIX = CANONICAL_ROOT + "/"
CORRECTION_PR = 538
CORRECTION_MERGE_SHA = "b722f622dd2eab031c087fe051c56a5eb019d705"

EXPECTED_SAFE = {
    ".gitattributes": "rollback_git_attributes",
    "packages/velvetos/policy/sensor-registry.json": "canonical_sensor_binding",
    "packages/vfbrand/brand-tokens.json": "canonical_asset_source",
    "scripts/check-project-bundle.py": "canonical_surface_sensor",
    "scripts/check-reel-route-sync.py": "canonical_surface_sensor",
    "scripts/check-velvetos.py": "canonical_surface_sensor",
}

OBSERVATION_RUNS = [
    {"id": 37267662064, "sha": "b722f622dd2eab031c087fe051c56a5eb019d705", "created_at": "2026-10-05T05:24:39Z", "event": "push", "conclusion": "success"},
    {"id": 37269082934, "sha": "e3a91cabcfdd2a145cdb79339ffc8a68c724a18a", "created_at": "2026-10-05T05:44:01Z", "event": "push", "conclusion": "success"},
    {"id": 37270696543, "sha": "dcf7fab530f97ac326018182a8545625897a95fa", "created_at": "2026-10-05T06:05:39Z", "event": "push", "conclusion": "success"},
    {"id": 37270881356, "sha": "840206d08a6d13638fd560dddca1dd6583076612", "created_at": "2026-10-05T06:08:00Z", "event": "push", "conclusion": "success"},
    {"id": 37272603427, "sha": "e853c0497546b2528f56da2578cb4cc9f3d2ab80", "created_at": "2026-10-05T06:28:34Z", "event": "push", "conclusion": "success"},
    {"id": 37273584691, "sha": "725d2e922739bfceed688c3db36b7fb371931a61", "created_at": "2026-10-05T06:40:10Z", "event": "push", "conclusion": "success"},
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


def snapshot_chatgpt_audit(sha: str) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_chatgpt_closure_semantic_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "chatgpt_core_bundle")
    require(isinstance(row, dict), "snapshot ChatGPT semantic audit did not return an object")
    all_rows = {surface_id: module.scan_surface(sha, surface_id) for surface_id in module.SURFACES}
    return row, module, all_rows


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
            "prepared-against main does not descend from the ChatGPT semantic correction")

    correction = git_json(args.prepared_against, CORRECTION.relative_to(ROOT).as_posix())
    policy = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())

    require(correction.get("repository_assessment") == "PASS",
            "ChatGPT semantic correction must PASS")
    require(correction.get("surface_id") == "chatgpt_core_bundle",
            "ChatGPT correction surface drift")
    rollback_fix = correction.get("rollback") or {}
    require(
        rollback_fix.get("window_open") is True
        and rollback_fix.get("closure_evidence") is None
        and rollback_fix.get("retirement_ready_for_deletion_gate") is False
        and rollback_fix.get("delete_authorized") is False,
        "ChatGPT correction rollback baseline drift",
    )

    legacy_files = tree_files(args.prepared_against, LEGACY_ROOT)
    canonical_files = tree_files(args.prepared_against, CANONICAL_ROOT)
    require(legacy_files == canonical_files, "ChatGPT legacy/canonical file sets differ")
    require(len(legacy_files) == 33, f"expected 33 ChatGPT distribution files, got {len(legacy_files)}")
    mismatches = [
        rel for rel in legacy_files
        if git_bytes(args.prepared_against, f"{LEGACY_ROOT}/{rel}")
        != git_bytes(args.prepared_against, f"{CANONICAL_ROOT}/{rel}")
    ]
    require(mismatches == [], f"ChatGPT legacy/canonical bytes differ: {mismatches}")

    legacy_tree_at_correction = subprocess.check_output(
        ["git", "rev-parse", f"{CORRECTION_MERGE_SHA}:{LEGACY_ROOT}"],
        cwd=ROOT,
        text=True,
    ).strip()
    legacy_tree_now = subprocess.check_output(
        ["git", "rev-parse", f"{args.prepared_against}:{LEGACY_ROOT}"],
        cwd=ROOT,
        text=True,
    ).strip()
    require(legacy_tree_at_correction == legacy_tree_now,
            "legacy ChatGPT bundle changed after semantic correction")
    require(
        git_bytes(CORRECTION_MERGE_SHA, ".gitattributes")
        == git_bytes(args.prepared_against, ".gitattributes"),
        ".gitattributes rollback metadata changed after ChatGPT correction",
    )

    brand = git_text(args.prepared_against, "packages/vfbrand/brand-tokens.json").replace("\\", "/")
    require(LEGACY_PREFIX not in brand, "brand tokens reintroduced legacy ChatGPT bundle")
    require(
        CANONICAL_PREFIX + "ASSET-MANIFEST-v6.6.4.json" in brand,
        "brand tokens do not use canonical ChatGPT asset manifest",
    )
    registry = git_text(args.prepared_against, "packages/velvetos/policy/sensor-registry.json").replace("\\", "/")
    require(LEGACY_PREFIX not in registry, "sensor registry reintroduced legacy ChatGPT bundle")
    require(registry.count(CANONICAL_PREFIX) == 18,
            "sensor registry canonical ChatGPT binding count drift")

    audit, module, all_rows = snapshot_chatgpt_audit(args.prepared_against)
    require(audit.get("retirement_preflight_clear") is True,
            "ChatGPT semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [],
            "ChatGPT semantic blockers remain")
    classes = audit.get("classes") or {}
    safe_refs: dict[str, str | None] = {}
    for rel, expected_class in EXPECTED_SAFE.items():
        actual_class = module.chatgpt_safe_class(args.prepared_against, rel)
        safe_refs[rel] = actual_class
        require(actual_class == expected_class,
                f"{rel}: ChatGPT safe classification drift ({actual_class!r})")
        require(rel in (classes.get(expected_class) or []),
                f"{rel}: semantic audit missing class {expected_class}")
    require(len(safe_refs) == 6, "ChatGPT safe reference count drift")

    all_clear = all(
        isinstance(row, dict)
        and row.get("retirement_preflight_clear") is True
        and row.get("retirement_preflight_blockers") == []
        for row in all_rows.values()
    )
    require(len(all_rows) == 5 and all_clear,
            "global Stage 8D semantic preflight is not 5/5 clear")

    authority = correction.get("authority") or {}
    policy_sha = csha(policy)
    require(authority.get("active_authority") == "instance:surface:chatgptProject",
            "ChatGPT correction active-authority receipt drift")
    require(policy_sha == authority.get("policy_registry_sha256"),
            "external-effect policy authority changed since ChatGPT correction")
    require(authority.get("external_effect_authority_changed") is False,
            "ChatGPT correction authority state drift")

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
    require(OBSERVATION_RUNS[-1]["sha"] == args.prepared_against,
            "latest observation does not match prepared-against main")

    criteria = {
        "chatgpt_semantic_correction_is_pass": True,
        "active_authority_remains_instance_surface_chatgpt_project": True,
        "legacy_and_instance_distribution_file_sets_are_equal": True,
        "legacy_and_instance_distribution_bytes_are_equal": True,
        "legacy_bundle_tree_is_unchanged_since_correction": True,
        "rollback_git_attributes_are_unchanged_since_correction": True,
        "brand_asset_source_remains_canonical_instance_distribution": True,
        "sensor_registry_keeps_eighteen_canonical_bindings": True,
        "six_remaining_candidate_refs_remain_content_validated_safe": True,
        "chatgpt_semantic_preflight_is_clear": True,
        "all_five_stage8d_semantic_preflights_are_clear": True,
        "external_effect_authority_is_unchanged": True,
        "observation_window_contains_multiple_distinct_downstream_main_heads": True,
        "all_downstream_main_head_verifications_are_successful": True,
        "all_observations_descend_from_chatgpt_correction": True,
        "latest_observation_matches_prepared_against_main": True,
        "closure_is_evidence_based_not_elapsed_time_based": True,
        "legacy_bundle_is_retained_after_closure": True,
        "deletion_requires_a_separate_isolated_gate": True,
    }

    report = {
        "schema": "velvetos.stage8d-chatgpt-rollback-closure.v1",
        "stage": "8D_CHATGPT_ROLLBACK_CLOSURE",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "surface_id": "chatgpt_core_bundle",
        "legacy_root": LEGACY_ROOT,
        "canonical_root": CANONICAL_ROOT,
        "purpose": (
            "Close the ChatGPT Core compatibility rollback observation window using post-correction content "
            "classification, exact distribution parity, legacy-tree immutability, canonical bindings and "
            "downstream-main evidence while retaining the compatibility bundle and keeping deletion unauthorized."
        ),
        "correction": {
            "receipt": CORRECTION.relative_to(ROOT).as_posix(),
            "pull_request": CORRECTION_PR,
            "merge_sha": CORRECTION_MERGE_SHA,
        },
        "current_evidence": {
            "legacy_present": True,
            "runtime_authority": False,
            "active_authority": authority.get("active_authority"),
            "file_count": len(legacy_files),
            "file_sets_equal": True,
            "byte_equal": True,
            "mismatches": [],
            "legacy_tree_unchanged_since_correction": True,
            "rollback_git_attributes_unchanged_since_correction": True,
            "canonical_sensor_binding_count": registry.count(CANONICAL_PREFIX),
            "brand_asset_source_canonical": True,
            "content_validated_safe_references": safe_refs,
            "safe_reference_count": len(safe_refs),
            "semantic_preflight_clear": True,
            "all_stage8d_semantic_preflights_clear": True,
            "external_effect_authority_unchanged": True,
        },
        "observation_window": {
            "basis": "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY",
            "elapsed_time_is_not_closure_authority": True,
            "start_merge_sha": CORRECTION_MERGE_SHA,
            "end_main_sha": args.prepared_against,
            "workflow": "VelvetOS Core Sensors",
            "verified_main_head_run_count": len(OBSERVATION_RUNS),
            "workflow_events": ["push"],
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
                "Active authority remains instance:surface:chatgptProject, the 33-file canonical and compatibility "
                "distributions remain byte-equal, the legacy tree and rollback .gitattributes are unchanged, all "
                "six remaining candidate references retain their content-validated safe roles, semantic preflight "
                "is clear, policy authority is unchanged, and multiple exact-main-head full-suite observations "
                "are green."
            ),
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": True,
        "retirement_ready_for_deletion_gate": True,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "All five Stage 8D rollback windows are now closure-eligible once this receipt is merged. Run separate "
            "isolated deletion gates one surface at a time; each gate must revalidate current main, semantic state, "
            "its closure receipt, parity/immutability requirements and external-effect authority before authorizing "
            "deletion."
        ),
        "authority": {
            "active_authority": authority.get("active_authority"),
            "policy_registry_sha256": policy_sha,
            "chatgpt_correction_policy_registry_sha256": authority.get("policy_registry_sha256"),
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "closure evidence does not itself authorize deletion",
            "legacy ChatGPT bundle remains present in this change",
            "rollback .gitattributes remain in place while compatibility bundle exists",
            "no big-bang delete",
            "retirement must be isolated to chatgpt_core_bundle",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "ChatGPT rollback closure acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_CHATGPT_ROLLBACK_CLOSURE "
        f"assessment={report['repository_assessment']} closed={report['rollback_window_closed']} "
        f"files={len(legacy_files)} safe_refs={len(safe_refs)} runs={len(OBSERVATION_RUNS)} "
        f"delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
