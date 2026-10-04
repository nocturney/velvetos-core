#!/usr/bin/env python3
"""Generate Reform v2 Stage 7B memory/learning lifecycle acceptance evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "velvetos" / "policy"
MODEL = POLICY / "memory-learning-lifecycle.json"
OUT = POLICY / "reports" / "stage7b-memory-learning-lifecycle.json"
MEMORY_DECISION = ROOT / "packages" / "vfharness" / "state" / "memory-rationalization-phase7-2026-09-27.json"
COGNEE = ROOT / "packages" / "vfmem" / "cognee.json"
CANDIDATES = ROOT / "packages" / "vfharness" / "state" / "learning-candidates"
POLICY_REGISTRY = POLICY / "policy-registry.json"

LIFECYCLE = [
    "OBSERVATION",
    "CANDIDATE",
    "EVIDENCE_RECURRENCE",
    "PROMOTED_DURABLE",
    "SUPERSEDED_EXPIRED",
]
ROLE_IDS = {
    "office-learning",
    "task-checkpoints",
    "learning-candidates",
    "owner-memory",
    "vfmem",
    "cognee",
    "vfinsights",
    "promoted-domain-sot",
}
ACTIVE_DOCS = [
    ".cursor/rules/velvet-factory-desk.mdc",
    ".cursor/skills/vf-daily-learning/SKILL.md",
    "packages/velvetos/modules/office-learning.md",
    "packages/vfharness/EMBED.md",
    "packages/vfharness/playbooks/learning-lifecycle.md",
    "packages/vfmem/MEMORY-UPDATE.md",
    "packages/vfops/hq/DAILY-RETRO.md",
]
FORBIDDEN_QUOTA_PHRASES = [
    "promotes one durable line",
    "Write **one line minimum**",
    "שורה אחת לפחות ל־`vfops/data/owner-memory.md`",
    "trigger same-day promote",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(len(args.prepared_against) == 40, "--prepared-against must be full SHA")

    model = load(MODEL)
    memory = load(MEMORY_DECISION)
    cognee = load(COGNEE)

    require(model.get("schema_version") == 1, "memory-learning schema drift")
    require(model.get("registry_kind") == "velvetos_memory_learning_lifecycle", "registry kind drift")
    require(model.get("status") == "ACTIVE_STAGE7B", "Stage 7B model not active")
    lifecycle = [x.get("id") for x in model.get("lifecycle", [])]
    require(lifecycle == LIFECYCLE, "canonical learning lifecycle/order drift")

    roles = {x.get("id"): x for x in model.get("roles", []) if isinstance(x, dict)}
    require(set(roles) == ROLE_IDS, "memory/learning role map incomplete")
    require(roles["office-learning"].get("role") == "PROCESS_OWNER" and roles["office-learning"].get("stores_current_fact") is False,
            "office-learning must be process-only")
    require(roles["learning-candidates"].get("role") == "CANDIDATE_STAGING" and roles["learning-candidates"].get("stores_current_fact") is False,
            "learning candidates must remain staging/evidence only")
    require(roles["owner-memory"].get("role") == "OWNER_SPECIFIC_DURABLE_MEMORY",
            "owner-memory role drift")
    require(roles["vfmem"].get("role") == "CANONICAL_MEMORY_ROUTER_VERIFIER" and roles["vfmem"].get("stores_current_fact") is False,
            "vfmem must route/verify canonical sources rather than duplicate them")
    require(roles["cognee"].get("role") == "DERIVED_SEMANTIC_INDEX" and roles["cognee"].get("stores_current_fact") is False,
            "Cognee must remain derived")

    inv = model.get("invariants") or {}
    for key in (
        "no_forced_daily_learning_quota",
        "day_without_durable_learning_may_end_without_memory_write",
        "one_current_authority_per_fact",
        "office_learning_is_not_storage",
        "candidate_store_is_not_durable_fact_authority",
        "vfmem_is_router_verifier_not_duplicate_store",
        "cognee_is_derived_replaceable_no_writeback",
        "promoted_fact_has_one_canonical_destination",
        "superseded_or_expired_records_are_history_only",
        "no_new_memory_database",
        "no_new_always_on_runtime",
        "no_new_recurring_cost",
    ):
        require(inv.get(key) is True, f"Stage 7B invariant disabled: {key}")
    require(inv.get("external_effect_authority_change") is False, "Stage 7B may not alter effect authority")

    gate = model.get("promotion_gate") or {}
    require(gate.get("requires_current_status") == "accepted", "promotion must require accepted candidate")
    require(gate.get("requires_concrete_evidence") is True, "promotion evidence gate missing")
    require(gate.get("requires_exactly_one_promote_to") is True, "promotion destination gate missing")
    require(gate.get("requires_canonical_reread") is True, "canonical reread gate missing")
    require(gate.get("requires_contradiction_scope_check") is True, "contradiction/scope gate missing")
    require(gate.get("automatic_ingest_may_promote") is False, "automatic ingest cannot promote")

    require(memory.get("roles", {}).get("vfmem") == "CANONICAL_DURABLE_MEMORY", "historical memory decision vfmem role changed")
    require(memory.get("roles", {}).get("cognee") == "DERIVED_SEMANTIC_INDEX", "historical memory decision Cognee role changed")
    require(memory.get("newAlwaysOnMemorySystems") == 0, "Stage 7B cannot add an always-on memory system")
    require(memory.get("incrementalRecurringCostIls") == 0, "Stage 7B cannot add recurring memory cost")
    guard = memory.get("guardrails") or {}
    require(guard.get("requiresCanonicalVerification") is True and guard.get("writebackToCanonicalMemory") is False,
            "memory canonical-verification/no-writeback baseline changed")
    require(cognee.get("authority") == "context-only-never-authority", "Cognee authority drift")
    require(cognee.get("canonicalMemory") == "vfmem", "Cognee canonical memory pointer drift")
    require((cognee.get("sync") or {}).get("requiresCanonicalVerification") is True, "Cognee canonical verification disabled")

    combined = "\n".join((ROOT / rel).read_text(encoding="utf-8-sig") for rel in ACTIVE_DOCS)
    for phrase in FORBIDDEN_QUOTA_PHRASES:
        require(phrase not in combined, f"forced daily learning/promotion phrase remains: {phrase}")
    for phrase in (
        "there is no daily learning quota",
        "אין מכסת למידה יומית",
        "אין שורת זיכרון חובה",
        "No daily quota exists.",
    ):
        require(phrase in combined, f"explicit no-quota contract missing: {phrase}")

    learning_code = (ROOT / "scripts" / "vf_learning.py").read_text(encoding="utf-8")
    for marker in (
        "'expired'",
        "promotion requires current status=accepted",
        "ALLOWED_TRANSITIONS",
        "status is never changed here",
    ):
        require(marker in learning_code, f"vf_learning lifecycle marker missing: {marker}")

    records = []
    for path in sorted(CANDIDATES.glob("*.json")):
        row = load(path)
        records.append(row)
        status = row.get("status")
        require(status in {"candidate","accepted","rejected","promoted","superseded","expired","pruned"},
                f"{path.name}: unsupported status")
        if status in {"accepted","promoted"}:
            require(bool(row.get("evidence")), f"{path.name}: accepted/promoted without evidence")
        if status == "promoted":
            require(bool(row.get("promote_to")), f"{path.name}: promoted without canonical destination")
    status_counts = dict(sorted(Counter(str(r.get("status")) for r in records).items()))

    current_policy = POLICY_REGISTRY.read_bytes()
    baseline_policy = git_show(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    require(current_policy == baseline_policy, "Stage 7B must not alter external-effect policy registry")

    criteria = {
        "canonical_lifecycle_is_observation_candidate_evidence_promotion_supersession": lifecycle == LIFECYCLE,
        "memory_learning_roles_have_single_bounded_authority": set(roles) == ROLE_IDS,
        "office_learning_is_process_not_store": roles["office-learning"].get("stores_current_fact") is False,
        "owner_memory_is_bounded_to_owner_specific_durable_facts": roles["owner-memory"].get("role") == "OWNER_SPECIFIC_DURABLE_MEMORY",
        "vfmem_routes_and_verifies_without_duplicate_fact_store": roles["vfmem"].get("stores_current_fact") is False,
        "cognee_is_derived_no_writeback_and_requires_canonical_verification": (
            roles["cognee"].get("stores_current_fact") is False
            and guard.get("writebackToCanonicalMemory") is False
            and (cognee.get("sync") or {}).get("requiresCanonicalVerification") is True
        ),
        "promotion_requires_accepted_evidenced_candidate_and_one_destination": (
            gate.get("requires_current_status") == "accepted"
            and gate.get("requires_concrete_evidence") is True
            and gate.get("requires_exactly_one_promote_to") is True
        ),
        "automatic_ingest_never_promotes": gate.get("automatic_ingest_may_promote") is False,
        "no_forced_daily_learning_quota": inv.get("no_forced_daily_learning_quota") is True,
        "no_new_store_runtime_cost_or_external_effect_authority": (
            inv.get("no_new_memory_database") is True
            and inv.get("no_new_always_on_runtime") is True
            and inv.get("no_new_recurring_cost") is True
            and inv.get("external_effect_authority_change") is False
            and current_policy == baseline_policy
        ),
    }

    report = {
        "schema": "velvetos.stage7b-memory-learning-lifecycle.v1",
        "stage": "7B",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Make learning selective and evidence-gated while keeping one current authority per durable fact and no second memory system.",
        "model": {
            "path": MODEL.relative_to(ROOT).as_posix(),
            "sha256": sha256(MODEL),
            "lifecycle": lifecycle,
            "role_count": len(roles),
        },
        "candidate_state": {
            "path": CANDIDATES.relative_to(ROOT).as_posix(),
            "count": len(records),
            "status_counts": status_counts,
            "automatic_promotion": False,
        },
        "memory_baseline": {
            "decision_path": MEMORY_DECISION.relative_to(ROOT).as_posix(),
            "decision_sha256": sha256(MEMORY_DECISION),
            "cognee_config_path": COGNEE.relative_to(ROOT).as_posix(),
            "cognee_config_sha256": sha256(COGNEE),
            "new_always_on_memory_systems": memory.get("newAlwaysOnMemorySystems"),
            "incremental_recurring_cost_ils": memory.get("incrementalRecurringCostIls"),
        },
        "migration_note": "No data/store migration. Existing candidate records and owner-memory history stay in place; legacy pruned remains terminal compatibility while new lifecycle expiry uses expired.",
        "rollback_note": "Revert the Stage 7B commit. No database, deletion, external-effect authority, or irreversible data migration is introduced.",
        "acceptance": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 7C — Research/Scheduler consolidation" if all(criteria.values()) else None,
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE7B_MEMORY_LEARNING "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"roles={len(roles)} candidates={len(records)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
