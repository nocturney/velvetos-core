#!/usr/bin/env python3
"""Validate non-normative Context Continuity preparation artifacts.

This checker is intentionally not wired into runtime or CI by this prep branch.
It detects design drift against the canonical Stage 7A semantic roles and the
existing vfharness continuation surfaces before future integration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs" / "implementation" / "context-continuity-prep"

FILES = {
    "contract": PREP / "context-continuity-contract-v0.json",
    "manifest": PREP / "state-manifest-v0.schema.json",
    "policy": PREP / "compaction-policy-v0.json",
    "vectors": PREP / "acceptance-vectors-v0.json",
    "state_model": ROOT / "packages" / "velvetos" / "policy" / "state-evidence-model.json",
}

EXPECTED_VECTORS = {
    "research-to-planning",
    "planning-to-execution",
    "mid-execution-unpersisted",
    "debugging-resolved",
    "exact-action-in-flight",
    "open-human-gate",
    "large-tool-dump",
    "unknown-runtime-health",
    "missing-resume-id",
    "post-compact-authority-drift",
    "cross-harness-resume",
    "sensitive-transcript-material",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    for path in FILES.values():
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    contract = load(FILES["contract"])
    manifest = load(FILES["manifest"])
    policy = load(FILES["policy"])
    vectors = load(FILES["vectors"])
    state_model = load(FILES["state_model"])

    require(contract.get("status") == "NON_NORMATIVE_REFORM_PREPARATION", "contract status drift")
    require(contract.get("authority") is False, "contract may not have authority")
    require(contract.get("runtime_enabled") is False, "contract runtime must remain disabled in prep")
    require(contract.get("production_integration") is False, "prep may not claim production integration")

    require(policy.get("status") == "NON_NORMATIVE_REFORM_PREPARATION", "policy status drift")
    require(policy.get("authority") is False, "draft compaction policy may not have authority")
    require(policy.get("runtime_enabled") is False, "draft compaction runtime must remain disabled")
    require(policy.get("mode") == "DESIGN_ONLY", "prep compaction policy must remain DESIGN_ONLY")

    categories = state_model.get("categories") or []
    canonical_roles = {row.get("id") for row in categories if isinstance(row, dict)}
    require(
        canonical_roles == {
            "CANONICAL_STATE",
            "EVIDENCE_RECEIPT",
            "AUTHORIZATION_DECISION",
            "AUDIT_HISTORY",
        },
        f"Stage 7A role set drift: {sorted(str(x) for x in canonical_roles)}",
    )

    try:
        manifest_roles = set(
            manifest["properties"]["sources"]["items"]["properties"]["role"]["enum"]
        )
    except (KeyError, TypeError) as exc:
        raise SystemExit(f"manifest role schema malformed: {exc}") from exc
    require(manifest_roles == canonical_roles, "continuation manifest must reuse exactly the Stage 7A roles")
    require(
        "RECENT_OBSERVATION" not in manifest_roles,
        "ephemeral observation may not become a fifth persistent semantic role",
    )

    deps = contract.get("canonical_dependencies") or {}
    require(isinstance(deps, dict) and deps, "canonical dependency map is missing")
    missing = [rel for rel in deps.values() if not (ROOT / str(rel)).exists()]
    require(not missing, f"canonical dependency paths do not resolve: {missing}")

    hard_blocks = set(policy.get("hard_blocks") or [])
    for required in {
        "uncommitted_or_unpersisted_execution_state",
        "exact_external_action_in_flight",
        "required_artifact_or_identifier_exists_only_in_chat",
        "pre_compaction_manifest_unproven",
        "compaction_would_replace_a_canonical_source_with_summary_prose",
    }:
        require(required in hard_blocks, f"missing hard block: {required}")

    rollout = policy.get("rollout") or []
    require(rollout and rollout[0] == "DESIGN_ONLY", "rollout must begin at DESIGN_ONLY")
    require("SHADOW_BUILD" in rollout and "SHADOW_COMPARE" in rollout, "shadow stages are required")
    require(rollout[-1] == "ACTIVE_WITH_KILL_SWITCH", "active rollout must retain a kill switch")

    rows = vectors.get("vectors") or []
    ids = {row.get("id") for row in rows if isinstance(row, dict)}
    require(ids == EXPECTED_VECTORS, f"acceptance vector set drift: {sorted(str(x) for x in ids)}")

    by_id = {row["id"]: row for row in rows if isinstance(row, dict) and "id" in row}
    require(by_id["mid-execution-unpersisted"].get("expected") == "COMPACT_BLOCKED",
            "mid-execution unpersisted state must block compaction")
    require(by_id["exact-action-in-flight"].get("expected") == "COMPACT_BLOCKED",
            "in-flight exact action must block compaction")
    require(by_id["post-compact-authority-drift"].get("expected") == "COMPACT_REJECTED_RECOVER",
            "authority drift must reject compacted context")

    globals_ = set(vectors.get("global_pass_conditions") or [])
    require("zero authority widening" in globals_, "global acceptance must require zero authority widening")
    require("zero invented state" in globals_, "global acceptance must require zero invented state")

    print(
        "CONTEXT_CONTINUITY_PREP PASS "
        f"roles={len(canonical_roles)} vectors={len(ids)} "
        f"canonical_dependencies={len(deps)} runtime_enabled=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
