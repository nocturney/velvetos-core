#!/usr/bin/env python3
"""Generate Reform v2 Stage 5B harness-consolidation evidence.

Read-only analysis. Historical state/checkpoints and specialized playbooks are
not treated as duplicate global contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5b-harness-consolidation.json"
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"
POLICY_REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
STAGE5A = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5a-context-locality.json"

ACTIVE_SURFACES = [
    "packages/vfharness/LOOP.md",
    "packages/vfharness/AGENTS.md",
    "packages/vfharness/SKILL.md",
    ".cursor/skills/vf-harness/SKILL.md",
    ".cursor/rules/vf-harness.mdc",
    "docs/HARNESS.md",
]
SECONDARY = ACTIVE_SURFACES[1:]
DUPLICATE_SIGNATURES = (
    "retry → fallback → downgrade",
    "retry(step, budget=2)",
    "downgrade_scope(step)",
)


def git_text(ref: str, rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot read {rel} from {ref}: {proc.stderr.strip()}")
    return proc.stdout


def worktree_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def surface_summary(loader) -> dict[str, Any]:
    rows = {}
    for rel in ACTIVE_SURFACES:
        text = loader(rel)
        signatures = [s for s in DUPLICATE_SIGNATURES if s in text]
        rows[rel] = {
            "points_to_loop": "LOOP.md" in text if rel != "packages/vfharness/LOOP.md" else True,
            "duplicate_signatures": signatures,
            "restates_global_loop": bool(signatures) if rel != "packages/vfharness/LOOP.md" else False,
        }
    return {
        "surfaces": rows,
        "secondary_pointer_count": sum(rows[p]["points_to_loop"] for p in SECONDARY),
        "secondary_restating_count": sum(rows[p]["restates_global_loop"] for p in SECONDARY),
        "secondary_restating_surfaces": [p for p in SECONDARY if rows[p]["restates_global_loop"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if len(args.prepared_against) != 40:
        ap.error("--prepared-against must be a full Git SHA")

    layers = json.loads(LAYERS.read_text(encoding="utf-8"))
    execution = layers.get("executionContract") or {}
    before = surface_summary(lambda rel: git_text(args.prepared_against, rel))
    after = surface_summary(worktree_text)

    stage5a = json.loads(STAGE5A.read_text(encoding="utf-8"))
    expected_policy_hash = (
        (stage5a.get("authorization_semantics") or {}).get("current_policy_registry_sha256")
    )
    current_policy_hash = hashlib.sha256(POLICY_REGISTRY.read_bytes()).hexdigest()

    handoff = execution.get("crossToolHandoff") or []
    handoff_exists = all((ROOT / p).is_file() for p in handoff)
    canonical = execution.get("canonical")
    canonical_text = (ROOT / canonical).read_text(encoding="utf-8") if canonical and (ROOT / canonical).is_file() else ""
    canonical_markers = {
        "retry": "retry(step, budget=2)" in canonical_text,
        "fallback": "fallback(step)" in canonical_text,
        "downgrade": "downgrade_scope(step)" in canonical_text,
        "safe_ruling": "safe ruling" in canonical_text.casefold(),
        "skillstate": "skillstate.md" in canonical_text,
        "cross_tool_handoff": all(p in canonical_text for p in handoff),
    }

    report = {
        "schema": "velvetos.stage5b-harness-consolidation.v1",
        "stage": "5B",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "scope": {
            "canonical_global_loop": "packages/vfharness/LOOP.md",
            "historical_state_modified": False,
            "specialized_playbooks_removed": False,
            "second_orchestrator_created": False,
        },
        "before": before,
        "after": after,
        "execution_contract": {
            "canonical": canonical,
            "state": execution.get("state"),
            "secondary_mode": execution.get("secondaryMode"),
            "second_orchestrator": execution.get("secondOrchestrator"),
            "cross_tool_handoff": handoff,
            "handoff_artifacts_exist": handoff_exists,
            "canonical_markers": canonical_markers,
        },
        "authorization_semantics": {
            "stage5a_policy_registry_sha256": expected_policy_hash,
            "current_policy_registry_sha256": current_policy_hash,
            "external_effect_authority_registry_unchanged": (
                bool(expected_policy_hash) and expected_policy_hash == current_policy_hash
            ),
        },
        "acceptance": {
            "secondary_surfaces_pointer_only": (
                after["secondary_pointer_count"] == len(SECONDARY)
                and after["secondary_restating_count"] == 0
            ),
            "duplicate_global_loop_reduced": (
                before["secondary_restating_count"] >= 1
                and after["secondary_restating_count"] == 0
            ),
            "canonical_loop_complete": all(canonical_markers.values()),
            "cross_tool_handoff_preserved": handoff_exists and len(handoff) == 2,
            "no_second_orchestrator": execution.get("secondOrchestrator") == "FORBIDDEN",
            "authorization_semantics_unchanged": (
                bool(expected_policy_hash) and expected_policy_hash == current_policy_hash
            ),
        },
    }
    report["repository_acceptance"] = (
        "PASS" if all(report["acceptance"].values()) else "FAIL"
    )
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE5B_HARNESS "
        f"acceptance={report['repository_acceptance']} "
        f"restating={before['secondary_restating_count']}->{after['secondary_restating_count']} "
        f"pointers={before['secondary_pointer_count']}->{after['secondary_pointer_count']}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
