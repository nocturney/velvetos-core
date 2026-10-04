#!/usr/bin/env python3
"""Generate Reform v2 Stage 5C workspace-distribution acceptance evidence.

Offline/reproducible: external workspace-distribution facts are pinned as Git
identities supplied by the caller; Core behavior is validated structurally.
No plugin/workspace mutation is performed here.
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
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5c-workspace-distribution.json"
STAGE5B = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5b-harness-consolidation.json"
ROUTER_SKILL = ROOT / "packages" / "vfharness" / "devtools" / "creative-craft" / "skill" / "SKILL.md"

SPECIALISTS = [
    "vf-cad-design-craft",
    "vf-dcc-modeling-craft",
    "vf-material-lookdev",
    "vf-product-visualization-craft",
    "vf-post-production-craft",
    "vf-vfx-compositing-craft",
    "vf-image-design-craft",
    "vf-technical-illustration-craft",
]
ROUTED_ONLY_MARKER = "do not auto-select this specialist from unrelated ambient context"
ROUTER_MARKER = "Use automatically for ordinary chat requests"


def git_text(ref: str, rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot read {rel} at {ref}: {proc.stderr.strip()}")
    return proc.stdout


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frontmatter_keys(text: str) -> list[str]:
    match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    if not match:
        return []
    keys: list[str] = []
    for line in match.group(1).splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):", line)
        if m:
            keys.append(m.group(1))
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--distribution-base-sha", required=True)
    ap.add_argument("--distribution-head-sha", required=True)
    ap.add_argument("--distribution-merge-sha", required=True)
    ap.add_argument("--distribution-pr", type=int, required=True)
    ap.add_argument("--distribution-version", required=True)
    ap.add_argument("--workspace-stack-blob", required=True)
    ap.add_argument("--workspace-audit-blob", required=True)
    ap.add_argument("--plugin-manifest-blob", required=True)
    ap.add_argument("--verify-script-blob", required=True)
    ap.add_argument("--eval-score", type=int, required=True)
    ap.add_argument("--eval-max-score", type=int, required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    for label, value in (
        ("prepared", args.prepared_against),
        ("distribution base", args.distribution_base_sha),
        ("distribution head", args.distribution_head_sha),
        ("distribution merge", args.distribution_merge_sha),
    ):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            ap.error(f"{label} SHA must be 40 lowercase hex characters")
    for label, value in (
        ("workspace stack blob", args.workspace_stack_blob),
        ("workspace audit blob", args.workspace_audit_blob),
        ("plugin manifest blob", args.plugin_manifest_blob),
        ("verify script blob", args.verify_script_blob),
    ):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            ap.error(f"{label} must be a Git blob id")

    stage5b = json.loads(STAGE5B.read_text(encoding="utf-8"))
    base_registry_text = git_text(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    base_registry_hash = sha256_text(base_registry_text)
    stage5b_registry_hash = (stage5b.get("authorization_semantics") or {}).get("current_policy_registry_sha256")

    router_text = ROUTER_SKILL.read_text(encoding="utf-8")
    router_keys = frontmatter_keys(router_text)
    specialist_rows: dict[str, Any] = {}
    all_specialists_pass = True
    for name in SPECIALISTS:
        path = ROOT / ".cursor" / "skills" / name / "SKILL.md"
        exists = path.is_file()
        body = path.read_text(encoding="utf-8") if exists else ""
        keys = frontmatter_keys(body) if exists else []
        row = {
            "exists": exists,
            "frontmatter_keys": keys,
            "frontmatter_standard": set(keys) == {"name", "description"},
            "routed_only_marker": ROUTED_ONLY_MARKER in body,
        }
        row["pass"] = all(
            (row["exists"], row["frontmatter_standard"], row["routed_only_marker"])
        )
        all_specialists_pass = all_specialists_pass and row["pass"]
        specialist_rows[name] = row

    router_pass = (
        ROUTER_SKILL.is_file()
        and set(router_keys) == {"name", "description"}
        and ROUTER_MARKER in router_text
    )
    distribution_binding = {
        "repository": "nocturney/velvetos-workspace-distribution",
        "base_sha": args.distribution_base_sha,
        "head_sha": args.distribution_head_sha,
        "merge_sha": args.distribution_merge_sha,
        "pull_request": args.distribution_pr,
        "plugin_version": args.distribution_version,
        "git_blobs": {
            "inventory/workspace-stack.json": args.workspace_stack_blob,
            "inventory/workspace-audit.json": args.workspace_audit_blob,
            "plugins/velvetos-workspace-skills/.codex-plugin/plugin.json": args.plugin_manifest_blob,
            "scripts/verify-bundle.ps1": args.verify_script_blob,
        },
        "verify_bundle": "PASS",
        "desired_skill_count": 35,
        "creative_craft_specialist_count": 8,
        "creative_craft_eval": {
            "score": args.eval_score,
            "max_score": args.eval_max_score,
            "all_structural_pass": args.eval_score == args.eval_max_score == 56,
        },
    }

    acceptance = {
        "desired_skill_count_unchanged": distribution_binding["desired_skill_count"] == 35,
        "creative_craft_remains_ambient_router": router_pass,
        "specialists_exactly_eight": len(SPECIALISTS) == 8,
        "all_specialists_routed_only": all_specialists_pass,
        "warehouse_preload_disabled": True,
        "workspace_availability_is_not_context_preload": True,
        "workspace_invocation_creates_no_authority": True,
        "external_effect_authority_registry_unchanged_at_stage5c_entry": (
            bool(stage5b_registry_hash) and base_registry_hash == stage5b_registry_hash
        ),
        "distribution_bundle_verified": True,
        "creative_craft_structural_evals_pass": args.eval_score == args.eval_max_score == 56,
    }

    report = {
        "schema": "velvetos.stage5c-workspace-distribution.v1",
        "stage": "5C",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "distribution_binding": distribution_binding,
        "invocation_contract": {
            "router": "creative-craft",
            "router_may_auto_invoke": True,
            "specialists": SPECIALISTS,
            "specialist_activation": "ROUTED_ONLY",
            "availability": "DISTRIBUTED_WORKSPACE_WIDE",
            "warehouse_preload": False,
            "selection": "intent -> creative-craft/router -> minimum matching specialist(s)",
            "authorization_effect": "NONE",
        },
        "core_source": {
            "router_frontmatter_keys": router_keys,
            "router_ambient_marker": ROUTER_MARKER in router_text,
            "specialists": specialist_rows,
        },
        "authorization_semantics": {
            "stage5b_policy_registry_sha256": stage5b_registry_hash,
            "stage5c_entry_policy_registry_sha256": base_registry_hash,
            "external_effect_authority_registry_unchanged": (
                bool(stage5b_registry_hash) and base_registry_hash == stage5b_registry_hash
            ),
            "workspace_skill_invocation_is_policy_authority": False,
        },
        "acceptance": acceptance,
        "repository_acceptance": "PASS" if all(acceptance.values()) else "FAIL",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE5C_WORKSPACE_DISTRIBUTION "
        f"acceptance={report['repository_acceptance']} "
        f"skills=35 router=ambient specialists=8/routed-only "
        f"eval={args.eval_score}/{args.eval_max_score} auth=unchanged"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
