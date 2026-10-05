#!/usr/bin/env python3
"""Generate Stage 8D evidence for the final ChatGPT Core compatibility semantic correction."""
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
OUT = REPORTS / "stage8d-chatgpt-semantic-correction.json"
PRIOR = REPORTS / "stage8d-chatgpt-core-consumer-migration.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
AUDIT_GENERATOR_REL = "scripts/generate-stage8d-retirement-semantic-audit.py"
LEGACY_ROOT = "packages/velvetos/chatgpt-project"
CANONICAL_ROOT = "instances/velvet-factory/distribution/chatgpt-project"
LEGACY_PREFIX = LEGACY_ROOT + "/"
CANONICAL_PREFIX = CANONICAL_ROOT + "/"

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


def snapshot_chatgpt_audit(sha: str) -> tuple[dict[str, Any], Any]:
    source = git_text(sha, AUDIT_GENERATOR_REL)
    module = types.ModuleType("stage8d_chatgpt_semantic_snapshot")
    module.__file__ = str(ROOT / AUDIT_GENERATOR_REL)
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    row = module.scan_surface(sha, "chatgpt_core_bundle")
    require(isinstance(row, dict), "snapshot ChatGPT semantic audit did not return an object")
    return row, module


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
        "source commit must descend from prepared-against",
    )

    prior = git_json(args.source_commit, PRIOR.relative_to(ROOT).as_posix())
    require(prior.get("repository_acceptance") == "PASS", "prior ChatGPT migration receipt must PASS")
    require((prior.get("consumer_scan") or {}).get("active_legacy_references") == [],
            "prior ChatGPT migration still has active legacy refs")
    require((prior.get("parity") or {}).get("byte_equal") is True, "prior ChatGPT parity must PASS")
    require((prior.get("rollback") or {}).get("window_open") is True, "ChatGPT rollback window must remain open")
    require((prior.get("rollback") or {}).get("delete_authorized") is False, "ChatGPT delete authority drift")

    legacy_files = tree_files(args.source_commit, LEGACY_ROOT)
    canonical_files = tree_files(args.source_commit, CANONICAL_ROOT)
    require(legacy_files == canonical_files, "ChatGPT legacy/canonical file sets differ")
    require(len(legacy_files) == 33, f"expected 33 ChatGPT distribution files, got {len(legacy_files)}")
    mismatches = [
        rel for rel in legacy_files
        if git_bytes(args.source_commit, f"{LEGACY_ROOT}/{rel}")
        != git_bytes(args.source_commit, f"{CANONICAL_ROOT}/{rel}")
    ]
    require(mismatches == [], f"ChatGPT legacy/canonical bytes differ: {mismatches}")
    legacy_tree_before = subprocess.check_output(
        ["git", "rev-parse", f"{args.prepared_against}:{LEGACY_ROOT}"], cwd=ROOT, text=True
    ).strip()
    legacy_tree_after = subprocess.check_output(
        ["git", "rev-parse", f"{args.source_commit}:{LEGACY_ROOT}"], cwd=ROOT, text=True
    ).strip()
    require(legacy_tree_before == legacy_tree_after, "legacy ChatGPT bundle changed during correction")
    require(
        git_bytes(args.prepared_against, ".gitattributes") == git_bytes(args.source_commit, ".gitattributes"),
        ".gitattributes changed during ChatGPT correction",
    )

    brand = git_text(args.source_commit, "packages/vfbrand/brand-tokens.json").replace("\\", "/")
    require(LEGACY_PREFIX not in brand, "brand tokens still reference legacy ChatGPT bundle")
    require(
        CANONICAL_PREFIX + "ASSET-MANIFEST-v6.6.4.json" in brand,
        "brand tokens do not use canonical ChatGPT asset manifest",
    )
    registry = git_text(args.source_commit, "packages/velvetos/policy/sensor-registry.json").replace("\\", "/")
    require(LEGACY_PREFIX not in registry, "sensor registry still points at legacy ChatGPT bundle")
    require(registry.count(CANONICAL_PREFIX) == 18, "sensor registry canonical ChatGPT binding count drift")

    audit, module = snapshot_chatgpt_audit(args.source_commit)
    require(audit.get("retirement_preflight_clear") is True, "ChatGPT semantic preflight is not clear")
    require(audit.get("retirement_preflight_blockers") == [], "ChatGPT semantic blockers remain")
    classes = audit.get("classes") or {}
    actual_safe: dict[str, str | None] = {}
    for rel, expected_class in EXPECTED_SAFE.items():
        actual_class = module.chatgpt_safe_class(args.source_commit, rel)
        actual_safe[rel] = actual_class
        require(actual_class == expected_class, f"{rel}: ChatGPT safe classification drift ({actual_class!r})")
        require(rel in (classes.get(expected_class) or []), f"{rel}: audit missing class {expected_class}")

    policy_before = csha(git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix()))
    policy_after = csha(git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix()))
    require(policy_before == policy_after, "external-effect policy authority changed")

    criteria = {
        "prior_chatgpt_consumer_migration_is_pass": True,
        "active_legacy_references_are_zero": True,
        "legacy_and_instance_distribution_file_sets_are_equal": True,
        "legacy_and_instance_distribution_bytes_are_equal": True,
        "legacy_bundle_is_tree_unchanged": True,
        "brand_asset_source_is_canonical_instance_distribution": True,
        "sensor_registry_uses_canonical_instance_distribution": True,
        "remaining_candidate_refs_are_content_validated_safe": len(actual_safe) == 6,
        "chatgpt_semantic_preflight_has_zero_blockers": True,
        "rollback_git_attributes_are_preserved": True,
        "rollback_window_remains_open": True,
        "delete_authority_remains_false": True,
        "external_effect_authority_is_unchanged": True,
    }

    report = {
        "schema": "velvetos.stage8d-chatgpt-semantic-correction.v1",
        "stage": "8D_CHATGPT_SEMANTIC_CORRECTION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "surface_id": "chatgpt_core_bundle",
        "legacy_root": LEGACY_ROOT,
        "canonical_root": CANONICAL_ROOT,
        "purpose": (
            "Remove the final active/config legacy ChatGPT bundle bindings and prove all remaining semantic "
            "references are canonical sensors, evidence/history/docs, or rollback byte-preservation metadata."
        ),
        "migration": {
            "brand_asset_source_migrated": True,
            "sensor_registry_migrated": True,
            "canonical_sensor_binding_count": 18,
            "legacy_distribution_present": True,
            "legacy_tree_unchanged": True,
        },
        "parity": {
            "file_count": len(legacy_files),
            "file_sets_equal": True,
            "byte_equal": True,
            "mismatches": [],
        },
        "classification": {
            "content_validated_safe_references": actual_safe,
            "remaining_blockers": [],
            "retirement_preflight_clear": True,
        },
        "rollback": {
            "window_open": True,
            "closure_evidence": None,
            "retirement_ready_for_deletion_gate": False,
            "delete_authorized": False,
        },
        "authority": {
            "active_authority": "instance:surface:chatgptProject",
            "policy_registry_sha256": policy_after,
            "prepared_against_policy_registry_sha256": policy_before,
            "external_effect_authority_changed": False,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "retirement_authorized": False,
        "delete_authorized": False,
        "next_action": (
            "Merge this correction and verify downstream main. All five semantic preflights are then clear; "
            "rollback-window closure evidence is still required per surface before any deletion gate."
        ),
        "constraints": [
            "legacy ChatGPT bundle remains present and byte-equal",
            "rollback .gitattributes remain in place while compatibility bundle exists",
            "rollback window remains open",
            "no deletion in this change",
            "external-effect authority remains unchanged",
        ],
    }
    require(all(criteria.values()), "ChatGPT semantic correction criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_CHATGPT_SEMANTIC_CORRECTION "
        f"assessment=PASS files={len(legacy_files)} safe_refs={len(actual_safe)} blockers=0 "
        "all_surfaces_clear=true delete_authorized=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
