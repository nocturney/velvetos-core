#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "packages" / "vfharness" / "state" / "learning-candidates"
MODEL = ROOT / "packages" / "velvetos" / "policy" / "memory-learning-lifecycle.json"
REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage7b-memory-learning-lifecycle.json"
GENERATOR = ROOT / "scripts" / "generate-stage7b-memory-learning-lifecycle.py"

VALID_STATUS = {"candidate","accepted","rejected","promoted","superseded","expired","pruned"}
VALID_SCOPE = {"task","project","owner"}
REQ = {"schema","candidate_id","trigger","action","scope","confidence","status","evidence","first_seen","last_seen","owner_correction","promote_to","supersedes"}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def fail(msg: str) -> int:
    print("FAIL " + msg, file=sys.stderr)
    return 1


# Historical Stage 7B acceptance is immutable. Live learning-candidates
# are explicitly MUTABLE: CI ingestion adds evidence, candidates and statuses.
# Freeze the original Oct 5 receipt snapshot, but independently validate
# current candidate records and compare every other generated receipt byte.
STAGE7B_HISTORIC_CANDIDATES = {
    "path": "packages/vfharness/state/learning-candidates",
    "count": 4,
    "status_counts": {"accepted": 4},
    "automatic_promotion": False,
}
STAGE7B_CANDIDATE_KEYS = set(STAGE7B_HISTORIC_CANDIDATES)


def verify_stage7b_projection(pinned_bytes: bytes, generated_bytes: bytes,
                              live_counts: dict[str, int]) -> None:
    pinned = json.loads(pinned_bytes.decode("utf-8"))
    generated = json.loads(generated_bytes.decode("utf-8"))
    if pinned.get("candidate_state") != STAGE7B_HISTORIC_CANDIDATES:
        raise ValueError("HISTORIC_STAGE7B_SNAPSHOT_CHANGED")
    dynamic = generated.get("candidate_state")
    if not isinstance(dynamic, dict) or set(dynamic) != STAGE7B_CANDIDATE_KEYS:
        raise ValueError("DYNAMIC_CANDIDATE_SCHEMA_DRIFT")
    if dynamic["path"] != STAGE7B_HISTORIC_CANDIDATES["path"] or dynamic["automatic_promotion"] is not False:
        raise ValueError("DYNAMIC_CANDIDATE_AUTHORITY_DRIFT")
    count, states = dynamic["count"], dynamic["status_counts"]
    if (type(count) is not int or count < 0
            or not isinstance(states, dict)
            or any(not isinstance(k, str) or k not in VALID_STATUS
                   or type(v) is not int or v < 0 for k, v in states.items())
            or sum(states.values()) != count):
        raise ValueError("DYNAMIC_CANDIDATE_COUNTS_INVALID")
    if states != live_counts or count != sum(live_counts.values()):
        raise ValueError("DYNAMIC_CANDIDATES_NOT_MATCHING_VALIDATED_RECORDS")
    generated["candidate_state"] = STAGE7B_HISTORIC_CANDIDATES
    reproduced = (json.dumps(generated, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if reproduced != pinned_bytes:
        raise ValueError("STAGE7B_IMMUTABLE_RECEIPT_NOT_REPRODUCIBLE")


def test_stage7b_projection() -> dict:
    import copy
    source = REPORT.read_bytes()
    original = json.loads(source.decode("utf-8"))
    def encoded(obj):
        return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    checks = []
    verify_stage7b_projection(source, encoded(copy.deepcopy(original)),
                              {"accepted": 4})
    checks.append("historic_snapshot_exact")
    for label, statuses in (
        ("new_candidate_created", {"accepted": 4, "candidate": 1}),
        ("candidate_rejected", {"accepted": 4, "rejected": 2}),
        ("promoted_candidate_count_projection", {"accepted": 3, "promoted": 1}),
        ("all_candidates_pruned", {}),
    ):
        candidate = copy.deepcopy(original)
        candidate["candidate_state"]["status_counts"] = statuses
        candidate["candidate_state"]["count"] = sum(statuses.values())
        verify_stage7b_projection(source, encoded(candidate), statuses)
        checks.append(label)
    def must_refuse(label, mutation, reason, *, pinned_mutation=False, live=None):
        baseline = copy.deepcopy(original)
        generated = copy.deepcopy(original)
        if pinned_mutation:
            mutation(baseline)
        else:
            mutation(generated)
        try:
            verify_stage7b_projection(
                encoded(baseline) if pinned_mutation else source,
                encoded(generated),
                {"accepted": 4} if live is None else live,
            )
        except ValueError as exc:
            if str(exc) != reason:
                raise AssertionError(label + ": WRONG_REFUSAL " + str(exc)) from exc
            checks.append(label)
        else:
            raise AssertionError("UNSAFE_STAGE7B_PROJECTION_ACCEPTED:" + label)
    must_refuse("deny_rewrite_original_snapshot",
                lambda x: x["candidate_state"].update(count=5),
                "HISTORIC_STAGE7B_SNAPSHOT_CHANGED", pinned_mutation=True)
    must_refuse("deny_rewrite_original_promotion_authority",
                lambda x: x["candidate_state"].update(automatic_promotion=True),
                "HISTORIC_STAGE7B_SNAPSHOT_CHANGED", pinned_mutation=True)
    must_refuse("deny_dynamic_promotion",
                lambda x: x["candidate_state"].update(automatic_promotion=True),
                "DYNAMIC_CANDIDATE_AUTHORITY_DRIFT")
    must_refuse("deny_dynamic_path_drift",
                lambda x: x["candidate_state"].update(path="shadow-store"),
                "DYNAMIC_CANDIDATE_AUTHORITY_DRIFT")
    must_refuse("deny_surprise_state_field",
                lambda x: x["candidate_state"].update(scheduler_authority=True),
                "DYNAMIC_CANDIDATE_SCHEMA_DRIFT")
    must_refuse("deny_boolean_candidate_count",
                lambda x: x["candidate_state"].update(count=True),
                "DYNAMIC_CANDIDATE_COUNTS_INVALID")
    must_refuse("deny_disagreeing_candidate_count",
                lambda x: x["candidate_state"].update(count=5),
                "DYNAMIC_CANDIDATE_COUNTS_INVALID")
    must_refuse("deny_unknown_candidate_status",
                lambda x: x["candidate_state"]["status_counts"].update(WRITER=True),
                "DYNAMIC_CANDIDATE_COUNTS_INVALID")
    must_refuse("deny_bogus_live_candidate_counts",
                lambda x: x["candidate_state"].update(
                    count=5, status_counts={"accepted": 4, "candidate": 1}),
                "DYNAMIC_CANDIDATES_NOT_MATCHING_VALIDATED_RECORDS")
    must_refuse("deny_immutable_model_digest_drift",
                lambda x: x["model"].update(sha256="0"*64),
                "STAGE7B_IMMUTABLE_RECEIPT_NOT_REPRODUCIBLE")
    must_refuse("deny_immutable_acceptance_drift",
                lambda x: x.update(repository_acceptance="FAIL"),
                "STAGE7B_IMMUTABLE_RECEIPT_NOT_REPRODUCIBLE")
    must_refuse("deny_immutable_effect_authority_drift",
                lambda x: x["acceptance"].update(
                    no_new_store_runtime_cost_or_external_effect_authority=False),
                "STAGE7B_IMMUTABLE_RECEIPT_NOT_REPRODUCIBLE")
    if len(checks) != 17:
        raise AssertionError("STAGE7B_NEGATIVE_COUNT_DRIFT:" + str(len(checks)))
    return {"status": "PASS_OFFLINE", "tests": len(checks),
            "cases": checks, "production_effects": 0, "candidate_writes": 0}


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    errors = []
    ids = set()
    records = []
    for p in sorted(DIR.glob("*.json")):
        try:
            d = load(p)
        except Exception as exc:
            errors.append(f"{p.name}: invalid json: {exc}")
            continue
        missing = REQ - set(d)
        if missing:
            errors.append(f"{p.name}: missing {sorted(missing)}")
        cid = d.get("candidate_id")
        if cid in ids:
            errors.append(f"{p.name}: duplicate candidate_id {cid}")
        ids.add(cid)
        records.append((p, d))
        if d.get("schema") != "vf.learning-candidate.v1":
            errors.append(f"{p.name}: unsupported schema")
        if d.get("status") not in VALID_STATUS:
            errors.append(f"{p.name}: invalid status")
        if d.get("scope") not in VALID_SCOPE:
            errors.append(f"{p.name}: invalid scope")
        conf = d.get("confidence")
        if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
            errors.append(f"{p.name}: confidence must be 0..1")
        if d.get("status") in {"accepted","promoted"} and not d.get("evidence"):
            errors.append(f"{p.name}: accepted/promoted without evidence")
        if d.get("status") == "promoted" and not d.get("promote_to"):
            errors.append(f"{p.name}: promoted without promote_to")

    known = {d.get("candidate_id") for _, d in records}
    for p, d in records:
        sup = d.get("supersedes")
        if sup and sup not in known:
            errors.append(f"{p.name}: missing supersedes target {sup}")
    if errors:
        for e in errors:
            print("FAIL " + e, file=sys.stderr)
        return 1

    try:
        model = load(MODEL)
        report = load(REPORT)
    except Exception as exc:
        return fail(str(exc))

    lifecycle = [row.get("id") for row in model.get("lifecycle", [])]
    if lifecycle != ["OBSERVATION","CANDIDATE","EVIDENCE_RECURRENCE","PROMOTED_DURABLE","SUPERSEDED_EXPIRED"]:
        return fail("Stage 7B canonical lifecycle/order drift")
    roles = {row.get("id"): row for row in model.get("roles", []) if isinstance(row, dict)}
    if roles.get("office-learning", {}).get("role") != "PROCESS_OWNER":
        return fail("office-learning must remain process owner only")
    if roles.get("office-learning", {}).get("stores_current_fact") is not False:
        return fail("office-learning cannot become a memory store")
    if roles.get("learning-candidates", {}).get("stores_current_fact") is not False:
        return fail("learning-candidates cannot become durable fact authority")
    if roles.get("owner-memory", {}).get("role") != "OWNER_SPECIFIC_DURABLE_MEMORY":
        return fail("owner-memory role drift")
    if roles.get("vfmem", {}).get("role") != "CANONICAL_MEMORY_ROUTER_VERIFIER":
        return fail("vfmem role drift")
    if roles.get("cognee", {}).get("role") != "DERIVED_SEMANTIC_INDEX":
        return fail("Cognee must remain derived semantic index")

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
        if inv.get(key) is not True:
            return fail(f"Stage 7B invariant disabled: {key}")
    if inv.get("external_effect_authority_change") is not False:
        return fail("Stage 7B may not alter external-effect authority")

    gate = model.get("promotion_gate") or {}
    if gate.get("requires_current_status") != "accepted":
        return fail("promotion must require accepted current status")
    if gate.get("requires_concrete_evidence") is not True or gate.get("requires_exactly_one_promote_to") is not True:
        return fail("promotion evidence/destination gates missing")
    if gate.get("automatic_ingest_may_promote") is not False:
        return fail("automatic ingest cannot promote")

    learning_code = (ROOT / "scripts" / "vf_learning.py").read_text(encoding="utf-8")
    for needle in (
        "ALLOWED_TRANSITIONS",
        "'expired'",
        "promotion requires current status=accepted",
        "--promote-to is only valid with status=promoted",
        "status is never changed here",
    ):
        if needle not in learning_code:
            return fail(f"vf_learning lifecycle enforcement missing {needle}")

    st = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_learning.py"), "selftest"],
        capture_output=True, text=True
    )
    if st.returncode != 0:
        return fail("vf_learning selftest: " + (st.stderr or st.stdout)[-500:])

    if report.get("schema") != "velvetos.stage7b-memory-learning-lifecycle.v1":
        return fail("Stage 7B acceptance receipt schema drift")
    if report.get("stage") != "7B" or report.get("repository_acceptance") != "PASS":
        return fail("Stage 7B acceptance receipt is not PASS")
    if report.get("behavior_change") is not True:
        return fail("Stage 7B must declare behavior change")
    if report.get("next_stage") != "Stage 7C — Research/Scheduler consolidation":
        return fail("Stage 7B next-stage handoff drift")
    if not all((report.get("acceptance") or {}).values()):
        return fail("Stage 7B acceptance criteria incomplete")

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "stage7b.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--prepared-against",
                str(report.get("prepared_against_main_sha") or ""),
                "--captured-at",
                str(report.get("captured_at") or ""),
                "--output",
                str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return fail("Stage 7B acceptance generator failed: " + (proc.stderr or proc.stdout)[-700:])
        live_counts = dict(sorted(Counter(d["status"] for _, d in records).items()))
        try:
            verify_stage7b_projection(REPORT.read_bytes(), out.read_bytes(), live_counts)
        except (ValueError, TypeError, KeyError) as exc:
            return fail("Stage 7B static receipt / live candidate projection: " + str(exc))

    wf = (ROOT / ".github" / "workflows" / "office-control-plane.yml").read_text(encoding="utf-8")
    for need in ("vf_learning.py ingest-ci", "packages/vfharness/state/learning-candidates"):
        if need not in wf:
            return fail(f"office-control-plane.yml must wire learning ingest ({need})")
    if "actions: read" not in wf and "actions: write" not in wf:
        return fail("office-control-plane.yml must grant explicit actions read/write permission")

    try:
        projection_tests = test_stage7b_projection()
    except (ValueError, AssertionError, TypeError, KeyError) as exc:
        return fail("Stage 7B projection negative tests: " + str(exc))
    print(
        f"OK learning candidates={len(records)} lifecycle=5 roles={len(roles)} "
        "no_daily_quota=true promotion=accepted+evidence+one-target "
        f"projection_tests={projection_tests['tests']} "
        "selftest=ingest-ci wired=office-control-plane actions_permission=explicit"
    )
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        print(json.dumps(test_stage7b_projection(), sort_keys=True))
        raise SystemExit(0)
    raise SystemExit(main())
