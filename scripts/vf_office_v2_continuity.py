#!/usr/bin/env python3
"""Office v2 Continuous Conversation Runtime v0 helper.

Scope: durable project-continuity state only.
No network, no provider mutation, no business-truth write and no policy authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "velvetos.office-v2.project-state.v0"

REQUIRED = [
    "schema_version", "project_id", "checkpoint_id", "parent_checkpoint_id",
    "current_goal", "scope_and_constraints", "completed_work", "decisions",
    "unresolved_questions", "active_tasks", "blockers", "artifact_document_refs",
    "important_links", "receipt_refs", "production_snapshot_refs", "migration_phase",
    "gate_status", "active_experiments", "rollback_point", "prohibited_actions",
    "runtime_refs", "business_entity_refs", "assumptions", "risks",
    "resume_instructions", "content_hash", "authority_refs",
    "active_external_effects", "code_baseline", "context", "verifier", "updated_at",
]

CRITICAL_EXACT = [
    "current_goal",
    "active_tasks",
    "blockers",
    "authority_refs",
    "active_external_effects",
    "artifact_document_refs",
    "migration_phase",
    "gate_status",
    "rollback_point",
    "prohibited_actions",
]

NONCRITICAL_REFERENCE_FIELDS = [
    "scope_and_constraints",
    "completed_work",
    "unresolved_questions",
    "important_links",
    "receipt_refs",
    "production_snapshot_refs",
    "active_experiments",
    "runtime_refs",
    "business_entity_refs",
    "assumptions",
    "risks",
    "resume_instructions",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_without_hash(manifest: dict[str, Any]) -> bytes:
    payload = copy.deepcopy(manifest)
    payload.pop("content_hash", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_hash(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_without_hash(manifest)).hexdigest()


def seal(manifest: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(manifest)
    out["content_hash"] = compute_hash(out)
    return out


def verify_hash(manifest: dict[str, Any]) -> bool:
    value = manifest.get("content_hash")
    return isinstance(value, str) and len(value) == 64 and value == compute_hash(manifest)


def required_shape(m: dict[str, Any]) -> list[str]:
    problems = [f"missing:{key}" for key in REQUIRED if key not in m]
    if m.get("schema_version") != SCHEMA:
        problems.append("schema_version")
    if not m.get("current_goal"):
        problems.append("current_goal_empty")
    if not m.get("scope_and_constraints"):
        problems.append("scope_and_constraints_empty")
    if not m.get("resume_instructions"):
        problems.append("resume_instructions_empty")
    if not m.get("authority_refs"):
        problems.append("authority_refs_empty")
    if not m.get("prohibited_actions"):
        problems.append("prohibited_actions_empty")
    if not isinstance(m.get("active_tasks"), list):
        problems.append("active_tasks_not_list")
    if not isinstance(m.get("active_external_effects"), list):
        problems.append("active_external_effects_not_list")
    if not verify_hash(m):
        problems.append("content_hash_invalid")
    return problems


def frozen_decisions(m: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [row for row in (m.get("decisions") or []) if row.get("status") == "FROZEN"],
        key=lambda row: str(row.get("decision_id")),
    )


def normalized(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compact_manifest(before: dict[str, Any], pressure_score: float | None = None) -> dict[str, Any]:
    """Compact only conversational working context; preserve project truth/references."""
    after = copy.deepcopy(before)
    ctx = after.setdefault("context", {})
    generation = int(ctx.get("compaction_generation", 0)) + 1

    if pressure_score is not None:
        ctx["pressure_score"] = max(0.0, min(1.0, float(pressure_score)))
        if ctx.get("pressure_basis") in {None, "UNKNOWN"}:
            ctx["pressure_basis"] = "HEURISTIC"

    observations = list(ctx.get("recent_observations") or [])
    working_set = list(ctx.get("working_set") or [])
    ctx["recent_observations"] = observations[-8:]

    seen: set[str] = set()
    compact_working: list[str] = []
    for item in reversed(working_set):
        item = str(item)
        if item not in seen:
            seen.add(item)
            compact_working.append(item)
    ctx["working_set"] = list(reversed(compact_working[:20]))
    ctx["compaction_generation"] = generation

    old_checkpoint = str(before.get("checkpoint_id") or "checkpoint")
    after["parent_checkpoint_id"] = old_checkpoint
    after["checkpoint_id"] = f"{old_checkpoint}-c{generation}"
    after["updated_at"] = now_iso()
    after["verifier"] = {
        "last_status": "NOT_RUN",
        "verified_at": None,
        "receipt_ref": None,
    }
    return seal(after)


def verify(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    blockers.extend("before_" + x for x in required_shape(before))
    blockers.extend("after_" + x for x in required_shape(after))

    if before.get("project_id") != after.get("project_id"):
        blockers.append("project_id_changed")

    for key in ("repo", "base_sha", "branch", "worktree_path"):
        if (before.get("code_baseline") or {}).get(key) != (after.get("code_baseline") or {}).get(key):
            blockers.append(f"code_baseline_{key}_changed")

    if after.get("parent_checkpoint_id") != before.get("checkpoint_id"):
        blockers.append("parent_checkpoint_not_previous_checkpoint")

    if normalized(frozen_decisions(before)) != normalized(frozen_decisions(after)):
        blockers.append("frozen_decisions_changed")

    for key in CRITICAL_EXACT:
        if normalized(before.get(key)) != normalized(after.get(key)):
            blockers.append(f"critical_state_changed:{key}")

    for key in NONCRITICAL_REFERENCE_FIELDS:
        before_value = before.get(key)
        after_value = after.get(key)
        if isinstance(before_value, list) and isinstance(after_value, list):
            before_set = {normalized(x) for x in before_value}
            after_set = {normalized(x) for x in after_value}
            if before_set - after_set:
                warnings.append(f"noncritical_references_lost:{key}")
        elif normalized(before_value) != normalized(after_value):
            warnings.append(f"noncritical_state_changed:{key}")

    before_generation = int((before.get("context") or {}).get("compaction_generation", 0))
    after_generation = int((after.get("context") or {}).get("compaction_generation", 0))
    if after_generation <= before_generation:
        warnings.append("compaction_generation_not_advanced")

    if blockers:
        status = "FAIL_CLOSED"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    return {
        "schema": "velvetos.office-v2.post-compaction-verifier.v0",
        "status": status,
        "verified_at": now_iso(),
        "before_checkpoint_id": before.get("checkpoint_id"),
        "after_checkpoint_id": after.get("checkpoint_id"),
        "blockers": blockers,
        "warnings": warnings,
        "external_effect_gate": "BLOCK_NEW_EXTERNAL_EFFECTS" if any(
            "authority_refs" in x
            or "active_external_effects" in x
            or "rollback_point" in x
            or "prohibited_actions" in x
            for x in blockers
        ) else "UNCHANGED",
        "unknown_outcome_rule": "UNKNOWN_OUTCOME is preserved and never blind-retried",
    }


def self_test_manifest() -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": SCHEMA,
        "project_id": "self-test",
        "checkpoint_id": "cp0",
        "parent_checkpoint_id": None,
        "updated_at": now_iso(),
        "current_goal": "prove checkpoint compact verify resume",
        "scope_and_constraints": ["no production writes", "single authority"],
        "completed_work": [{"item": "baseline", "evidence_refs": ["evidence://baseline"]}],
        "decisions": [
            {
                "decision_id": "d1",
                "decision": "No parallel production writer",
                "status": "FROZEN",
                "rationale": "single-authority gate",
            }
        ],
        "unresolved_questions": ["drive write authority"],
        "active_tasks": [
            {
                "task_id": "t1",
                "owner": "office-v2-execution",
                "status": "IN_PROGRESS",
                "next_action": "verify",
            }
        ],
        "blockers": ["drive write authority unresolved"],
        "artifact_document_refs": ["docs://phase0"],
        "important_links": ["gdrive://start-here"],
        "receipt_refs": ["evidence://baseline"],
        "production_snapshot_refs": ["state://capabilities"],
        "migration_phase": "PHASE_0",
        "gate_status": {"phase": "PHASE_0", "verdict": "PARTIAL", "reasons": ["self-test"]},
        "active_experiments": [],
        "rollback_point": {
            "available": True,
            "reference": "git://base",
            "instructions": "drop isolated branch",
        },
        "prohibited_actions": ["production-writer", "blind-retry"],
        "runtime_refs": ["runtime://test"],
        "business_entity_refs": ["business://jobs"],
        "assumptions": ["fixture only"],
        "risks": ["fixture risk"],
        "resume_instructions": ["read manifest", "verify", "continue"],
        "content_hash": "",
        "authority_refs": ["policy-registry", "state-evidence-model"],
        "active_external_effects": [
            {
                "intent_id": "intent-1",
                "effect_class": "test-effect",
                "status": "UNKNOWN_OUTCOME",
                "receipt_ref": "receipt-unknown-1",
            }
        ],
        "code_baseline": {
            "repo": "velvetos-core",
            "base_sha": "a" * 40,
            "branch": "office-v2/test",
            "worktree_path": "D:/test",
        },
        "context": {
            "summary": "self test",
            "working_set": ["a", "b", "a"],
            "recent_observations": [str(i) for i in range(12)],
            "pressure_score": None,
            "pressure_basis": "MANUAL_TRIGGER",
            "pressure_signals": {"manual_trigger": True},
            "compaction_generation": 0,
        },
        "verifier": {"last_status": "NOT_RUN", "verified_at": None, "receipt_ref": None},
    }
    return seal(base)


def self_test() -> dict[str, Any]:
    base = self_test_manifest()
    compacted = compact_manifest(base)
    good = verify(base, compacted)

    bad = copy.deepcopy(compacted)
    bad["prohibited_actions"] = ["production-writer"]
    bad["active_external_effects"] = []
    bad = seal(bad)
    negative = verify(base, bad)

    ok = (
        good["status"] == "PASS"
        and negative["status"] == "FAIL_CLOSED"
        and negative["external_effect_gate"] == "BLOCK_NEW_EXTERNAL_EFFECTS"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "positive_control": good["status"],
        "negative_control": negative["status"],
        "negative_blockers": negative["blockers"],
        "external_effect_gate": negative["external_effect_gate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Office v2 continuity helper")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command")

    p_seal = sub.add_parser("seal")
    p_seal.add_argument("--input", required=True)
    p_seal.add_argument("--output", required=True)

    p_compact = sub.add_parser("compact")
    p_compact.add_argument("--input", required=True)
    p_compact.add_argument("--output", required=True)
    p_compact.add_argument("--pressure-score", type=float)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--before", required=True)
    p_verify.add_argument("--after", required=True)
    p_verify.add_argument("--receipt-out")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--manifest", required=True)

    args = parser.parse_args()

    if args.self_test:
        payload = self_test()
        print(json.dumps(payload, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "PASS" else 1

    if args.command == "seal":
        manifest = load(Path(args.input))
        manifest["updated_at"] = manifest.get("updated_at") or now_iso()
        sealed = seal(manifest)
        write(Path(args.output), sealed)
        payload = {"status": "PASS", "output": str(Path(args.output)), "content_hash": sealed["content_hash"]}
    elif args.command == "compact":
        before = load(Path(args.input))
        problems = required_shape(before)
        if problems:
            payload = {"status": "FAIL_CLOSED", "problems": problems}
            print(json.dumps(payload, ensure_ascii=False))
            return 2
        after = compact_manifest(before, args.pressure_score)
        write(Path(args.output), after)
        payload = {"status": "PASS", "output": str(Path(args.output)), "checkpoint_id": after["checkpoint_id"]}
    elif args.command == "verify":
        payload = verify(load(Path(args.before)), load(Path(args.after)))
        if args.receipt_out:
            write(Path(args.receipt_out), payload)
    elif args.command == "validate":
        problems = required_shape(load(Path(args.manifest)))
        payload = {"status": "PASS" if not problems else "FAIL_CLOSED", "problems": problems}
    else:
        parser.print_help()
        return 2

    print(json.dumps(payload, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
