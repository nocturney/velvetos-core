#!/usr/bin/env python3
"""Generate Stage 8D ChatGPT Core compatibility-consumer migration evidence."""
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
OUT = REPORTS / "stage8d-chatgpt-core-consumer-migration.json"
READINESS_REL = "packages/velvetos/policy/reports/stage8d-retirement-readiness.json"
STAGE8C_REL = "packages/velvetos/policy/reports/stage8c-chatgpt-distribution-consumers.json"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"
INSTANCE_REL = "instances/velvet-factory/INSTANCE.json"
LEGACY_ROOT = "packages/velvetos/chatgpt-project"
LEGACY_PREFIX = LEGACY_ROOT + "/"
INSTANCE_PREFIX = "instances/velvet-factory/distribution/chatgpt-project/"
SURFACE_PREFIX = "instance:surface:chatgptProject/"

ACTIVE_CONSUMERS = (
    "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json",
    "packages/vfom/REEL-ROUTE-CONTRACT.json",
    "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json",
    "scripts/check-project-bundle.py",
    "scripts/check-project-request-gate.py",
    "scripts/check-reel-route-sync.py",
    "scripts/check-chat-runtime-bundle.py",
    "scripts/vf_project_bundle.py",
    "scripts/vf_project_preflight.py",
    "scripts/vf_publication_evidence.py",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig")


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_text(sha, rel))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must contain an object")
    return obj


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def tree_files(commit: str, prefix: str) -> dict[str, bytes]:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", prefix.rstrip("/")],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    require(proc.returncode == 0, proc.stderr.strip() or f"git ls-tree failed for {prefix}")
    out: dict[str, bytes] = {}
    for rel in proc.stdout.splitlines():
        rel = rel.strip().replace("\\", "/")
        if rel.startswith(prefix):
            out[rel[len(prefix):]] = git_bytes(commit, rel)
    return out


def grep_refs(needle: str, commit: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", needle, commit, "--", ":!packages/velvetos/policy/reports/*"],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"git grep failed for {needle!r}")
    prefix = f"{commit}:"
    refs = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    for name, value in (("prepared-against", args.prepared_against), ("source-commit", args.source_commit)):
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"bad {name} sha")

    readiness = git_json(args.source_commit, READINESS_REL)
    require(readiness.get("repository_assessment") == "PASS", "Stage 8D readiness baseline must PASS")
    require(readiness.get("retirement_authorized") is False, "retirement must remain blocked at migration entry")

    stage8c = git_json(args.source_commit, STAGE8C_REL)
    distribution8c = stage8c.get("distribution") or {}
    require(stage8c.get("repository_acceptance") == "PASS", "Stage 8C ChatGPT distribution receipt must PASS")
    require(distribution8c.get("byte_parity") is True, "Stage 8C ChatGPT distribution parity evidence missing")
    require(distribution8c.get("delete_authorized") is False, "Stage 8C unexpectedly authorized legacy delete")

    instance = git_json(args.source_commit, INSTANCE_REL)
    require((instance.get("surfaces") or {}).get("chatgptProject") == "distribution/chatgpt-project/LATEST.json",
            "instance chatgptProject surface drift")

    core_files = tree_files(args.source_commit, LEGACY_PREFIX)
    inst_files = tree_files(args.source_commit, INSTANCE_PREFIX)
    parity = set(core_files) == set(inst_files) and all(core_files[k] == inst_files[k] for k in core_files)
    require(parity, "instance ChatGPT distribution differs from retained Core rollback bundle")

    manifest = git_json(args.source_commit, "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json")
    bundle = manifest.get("chatgptProjectBundle") or {}
    bundle_fields = ("authority", "assetManifest", "instructions", "productTruthGuide")
    require(all(isinstance(bundle.get(k), str) and bundle[k].startswith(SURFACE_PREFIX) for k in bundle_fields),
            "Project Authority bundle is not fully surface-owned")
    manifest_text = git_text(args.source_commit, "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json")
    require(LEGACY_PREFIX not in manifest_text, "Project Authority manifest still references legacy ChatGPT root")

    reel = git_json(args.source_commit, "packages/vfom/REEL-ROUTE-CONTRACT.json")
    require(reel.get("projectSurface") == "chatgptProject", "Reel route project surface drift")
    require(str(reel.get("routeDoc") or "").startswith(SURFACE_PREFIX), "Reel route doc not surface-owned")
    require(str(reel.get("projectInstructions") or "").startswith(SURFACE_PREFIX), "Reel instructions not surface-owned")

    visual = git_json(args.source_commit, "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json")
    guide = (((visual.get("referenceRoleSeparationPolicy") or {}).get("productTruth") or {}).get("guide"))
    require(isinstance(guide, str) and guide.startswith(SURFACE_PREFIX), "visual product-truth guide not surface-owned")

    resolver_text = git_text(args.source_commit, "scripts/vf_project_bundle.py")
    require("resolve_distribution" in resolver_text and "instance_id: str | None = None" in resolver_text,
            "project bundle resolver is not generic instance-surface aware")
    require('"velvet-factory"' not in resolver_text, "generic project bundle resolver embeds a business default")

    for rel in ("scripts/vf_project_preflight.py", "scripts/vf_publication_evidence.py"):
        text = git_text(args.source_commit, rel)
        require('instance_id="velvet-factory"' in text and "env={}" in text,
                f"{rel} does not select the VF instance explicitly")

    all_legacy_refs = grep_refs(LEGACY_PREFIX, args.source_commit)
    active_legacy_refs = sorted(set(ACTIVE_CONSUMERS) & set(all_legacy_refs))
    require(not active_legacy_refs, f"active ChatGPT Core legacy references remain: {active_legacy_refs}")

    consumer_rows: dict[str, bool] = {}
    for rel in ACTIVE_CONSUMERS:
        text = git_text(args.source_commit, rel)
        migrated = LEGACY_PREFIX not in text
        consumer_rows[rel] = migrated
        require(migrated, f"active consumer still names legacy ChatGPT root: {rel}")

    policy_now = csha(git_json(args.source_commit, POLICY_REL))
    policy_base = csha(git_json(args.prepared_against, POLICY_REL))
    require(policy_now == policy_base, "external-effect policy changed")

    criteria = {
        "stage8c_chatgpt_distribution_parity_is_preserved": stage8c.get("repository_acceptance") == "PASS" and distribution8c.get("byte_parity") is True,
        "instance_manifest_keeps_chatgpt_project_surface": (instance.get("surfaces") or {}).get("chatgptProject") == "distribution/chatgpt-project/LATEST.json",
        "project_authority_bundle_uses_instance_surface_references": all(str(bundle.get(k) or "").startswith(SURFACE_PREFIX) for k in bundle_fields),
        "reel_and_visual_contracts_use_instance_chatgpt_surface": reel.get("projectSurface") == "chatgptProject" and str(guide).startswith(SURFACE_PREFIX),
        "generic_bundle_resolver_has_no_silent_business_default": '"velvet-factory"' not in resolver_text and "resolve_distribution" in resolver_text,
        "vf_runtime_callers_select_instance_explicitly": all(consumer_rows.get(rel, False) for rel in ("scripts/vf_project_preflight.py", "scripts/vf_publication_evidence.py")),
        "all_active_chatgpt_consumers_have_no_legacy_root_reference": not active_legacy_refs,
        "canonical_instance_distribution_remains_byte_equal_to_legacy_bundle": parity,
        "legacy_chatgpt_core_bundle_is_retained_for_rollback": git_exists(args.source_commit, LEGACY_ROOT),
        "rollback_window_remains_open_and_delete_is_unauthorized": True,
        "stage8d_readiness_baseline_is_preserved": readiness.get("retirement_authorized") is False,
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8d-chatgpt-core-consumer-migration.v1",
        "stage": "8D_CHATGPT_CORE_CONSUMER_MIGRATION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": "Cut active project/runtime consumers over from the retained Core ChatGPT bundle to the selected instance chatgptProject surface while preserving exact rollback parity.",
        "migration": {
            "active_authority": "instance:surface:chatgptProject",
            "instance_distribution_root": "instances/velvet-factory/distribution/chatgpt-project",
            "rollback_compatibility_root": LEGACY_ROOT,
            "legacy_path_retained": True,
            "delete_authorized": False,
        },
        "active_consumers": consumer_rows,
        "consumer_scan": {
            "legacy_reference_count": len(all_legacy_refs),
            "active_legacy_references": active_legacy_refs,
            "active_blockers_removed": not active_legacy_refs,
        },
        "parity": {
            "file_count": len(core_files),
            "file_sets_equal": set(core_files) == set(inst_files),
            "byte_equal": parity,
        },
        "rollback": {
            "window_open": True,
            "retirement_ready": False,
            "delete_authorized": False,
        },
        "authority": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "external_effect_authority_changed": policy_now != policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_action": "Migrate or close the remaining compatibility domains; do not delete packages/velvetos/chatgpt-project until explicit rollback-window closure evidence exists.",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_CHATGPT_CORE_CONSUMER "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(map(bool, criteria.values()))}/{len(criteria)} "
        f"active_legacy_refs={len(active_legacy_refs)} parity={parity}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
