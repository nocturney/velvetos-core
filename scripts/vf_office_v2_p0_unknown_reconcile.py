#!/usr/bin/env python3
"""Office #612: read-only, fail-closed reconciliation of local-model LAB evidence.

This does not run models, independently verify purported success, enumerate/kill
processes, or schedule/retry tasks. A RUNNING journal is NOT proof of liveness.
The existing local-model worker's separate verify command remains the ONLY
way to verify a successful source edit, log, checkpoint, and fresh-clone QA.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import platform
import re
import stat
import tempfile

SCHEMA = "velvetos.office-v2.p0-local-model-envelope.v1"
RECEIPT_SCHEMA = "velvetos.office-v2.p0-local-model-receipt.v1"
RECONCILE_SCHEMA = "velvetos.office-v2.p0-unknown-readback.v1"
AUTHORITY = "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT"
KIND = "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,95}\Z")
MAX_INPUT_BYTES = 1024 * 1024


class Refused(Exception):
    """An observation that cannot be trusted must never be treated as success."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def read_optional(path):
    """Read only regular JSON, refuse symlinks and concurrent file replacement."""
    p = pathlib.Path(path)
    require(not p.is_symlink(), "SYMLINK_INPUT_DENIED")
    if not p.exists():
        return None
    before = p.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_INPUT_BYTES,
            "UNSAFE_OR_OVERSIZED_EVIDENCE")
    raw = p.read_bytes()
    after = p.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "EVIDENCE_CHANGED_DURING_READ")
    require(len(raw) <= MAX_INPUT_BYTES, "OVERSIZED_EVIDENCE")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise Refused("EVIDENCE_JSON_INVALID")
    require(isinstance(obj, dict), "EVIDENCE_OBJECT_REQUIRED")
    return obj


def checked_envelope(env):
    require(env is not None, "ENVELOPE_REQUIRED")
    require(env.get("schema") == SCHEMA and env.get("authority") == AUTHORITY and
            env.get("issue_url") == ISSUE, "ENVELOPE_IDENTITY_DRIFT")
    task_id = env.get("task_id")
    require(isinstance(task_id, str) and bool(TASK_ID.fullmatch(task_id)), "TASK_ID_INVALID")
    host = env.get("host")
    require(isinstance(host, str) and 1 <= len(host) <= 150, "HOST_ID_INVALID")
    base, branch = env.get("base_sha"), env.get("branch")
    require(isinstance(base, str) and bool(SHA1.fullmatch(base)), "BASE_SHA_INVALID")
    require(isinstance(branch, str) and branch.startswith("lab-p0-agent-") and
            len(branch) <= 160, "NON_LAB_BRANCH")
    executor = env.get("executor")
    require(isinstance(executor, dict) and executor.get("kind") == KIND,
            "NON_LAB_MODEL_EXECUTOR")
    model, pin = executor.get("model"), executor.get("model_digest")
    require(model in ("qwen3.5:4b", "qwen3.5:9b") and
            isinstance(pin, str) and bool(SHA256.fullmatch(pin)), "MODEL_PIN_INVALID")
    budget = env.get("budget")
    require(isinstance(budget, dict) and budget.get("max_attempts") == 1 and
            type(budget.get("max_cost_usd")) in (int, float) and
            budget["max_cost_usd"] == 0, "RETRY_OR_PAID_BUDGET_DENIED")
    require(isinstance(env.get("worktree_path"), str) and env["worktree_path"] and
            isinstance(env.get("context_checkpoint"), str) and env["context_checkpoint"],
            "MISSING_CODE_OR_STATE_REFERENCE")
    return env


def check_journal(journal, env):
    expected = {
        "state": "RUNNING", "unknown_outcome_rule": "NO_BLIND_RETRY",
        "task_id": env["task_id"], "host": env["host"],
        "kind": KIND, "envelope_sha256": digest(env),
    }
    faults = ["JOURNAL_" + key.upper() + "_DRIFT"
              for key, value in expected.items() if journal.get(key) != value]
    if not isinstance(journal.get("started_at"), str) or not journal["started_at"]:
        faults.append("JOURNAL_START_MISSING")
    return faults


def check_receipt(receipt, env, receipt_path):
    # SHA-256 self-seals detect accidental alteration, not re-sealed forgery.
    defects = []
    seal = receipt.get("receipt_sha256")
    if not isinstance(seal, str) or not SHA256.fullmatch(seal) or seal != digest({
            key: value for key, value in receipt.items() if key != "receipt_sha256"}):
        defects.append("RECEIPT_SELF_HASH_DRIFT")
    expected = {
        "schema": RECEIPT_SCHEMA, "task_id": env["task_id"],
        "host": env["host"], "envelope_sha256": digest(env),
        "base_sha": env["base_sha"], "branch": env["branch"],
        "model": env["executor"]["model"],
        "model_digest": env["executor"]["model_digest"],
        "production_authority": "NONE", "additional_api_spend_usd": 0,
        "autonomous_retry": False, "scheduler_proven": False,
        "exact_model_calls": None,
    }
    for key, value in expected.items():
        actual = receipt.get(key, object())
        if actual != value or (type(value) is bool and type(actual) is not bool) or (value == 0 and type(value) is int and type(actual) is not int):
            defects.append("RECEIPT_" + key.upper() + "_DRIFT")
    if receipt.get("receipt_directory") != str(receipt_path.parent.resolve()):
        defects.append("RECEIPT_DIRECTORY_DRIFT")
    state = receipt.get("state")
    if not isinstance(state, str) or state not in {
            "SUCCEEDED", "EXECUTOR_NONZERO", "TIMED_OUT_UNKNOWN_OUTCOME",
            "EXECUTOR_LAUNCH_OR_CLEANUP_ERROR", "INDEPENDENT_QA_FAILED",
            "NO_VALID_TARGET_EDIT", "CONTINUITY_FAILED", "UNKNOWN_OUTCOME"}:
        defects.append("RECEIPT_UNKNOWN_STATE")
    if state == "SUCCEEDED":
        # These fields are CLAIMS only, until full original worker verify.
        if (receipt.get("exit_code") != 0 or
                receipt.get("model_invocations_min") != 1 or
                not isinstance(receipt.get("independent_qa"), dict) or
                receipt["independent_qa"].get("pass") is not True or
                not isinstance(receipt.get("artifact_sha256"), str) or
                not SHA256.fullmatch(receipt["artifact_sha256"])):
            defects.append("FALSE_SUCCESS_CLAIM")
    return defects


def reconcile(envelope_path, receipt_path):
    """Never perform work on the task; only classify exact disk evidence."""
    ep = pathlib.Path(envelope_path).absolute()
    rp = pathlib.Path(receipt_path).absolute()
    jp = rp.with_suffix(rp.suffix + ".running")
    require(len({str(ep), str(rp), str(jp)}) == 3, "EVIDENCE_PATH_COLLISION")
    env = checked_envelope(read_optional(ep))
    require(not rp.is_relative_to(pathlib.Path(env["worktree_path"]).absolute()) and
            not jp.is_relative_to(pathlib.Path(env["worktree_path"]).absolute()),
            "RECEIPT_INSIDE_WORKTREE_DENIED")
    journal = read_optional(jp)
    receipt = read_optional(rp)
    faults = []
    if journal is not None:
        faults += check_journal(journal, env)
    if receipt is not None:
        faults += check_receipt(receipt, env, rp)
    if faults:
        status = "CONFLICT_OR_TAMPER_REFUSE"
    elif journal is not None and receipt is not None:
        status = "JOURNAL_RECEIPT_CONFLICT_REVIEW"
    elif journal is not None:
        status = "UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY"
    elif receipt is None:
        status = "NO_EVIDENCE_NOT_PROVEN_UNSTARTED"
    elif receipt["state"] == "SUCCEEDED":
        status = "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY"
    else:
        status = "NON_SUCCESS_RECEIPT_REVIEW_REQUIRED"
    return {
        "schema": RECONCILE_SCHEMA, "status": status, "task_id": env["task_id"],
        "envelope_sha256": digest(env), "host": env["host"],
        "journal_present": journal is not None, "receipt_present": receipt is not None,
        "reason_codes": sorted(set(faults)), "model_calls_during_reconciliation": 0,
        "verified_success": False, "original_worker_liveness_attested": False,
        "journal_contains_worker_pid": False,  # v1 journal has no PID or process start identity.
        "owner_process_state": "UNKNOWN_NOT_ATTESTED",
        "automatic_retry_allowed": False, "new_task_authorized": False,
        "autonomous_failover_proven": False, "production_effects": "NONE",
        "read_only": True,
        "next_gate": "OPERATOR_REVIEW_AND_SEPARATE_WORKER_VERIFY_NO_AUTO_RESUME",
    }


def accept_independent_worker_proof(readback, proof):
    """Only a separate trusted worker check_run result can close a claimed success."""
    correct = (
        readback.get("status") == "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY"
        and isinstance(proof, dict) and proof.get("status") == "PASS"
        and proof.get("task_id") == readback.get("task_id")
        and proof.get("real_local_model_min_invocations") == 1
        and proof.get("model_calls_exact") is None
        and proof.get("offline_fixture") is False
        and proof.get("scheduler_proven") is False
    )
    result = dict(readback)
    result["verified_success"] = bool(correct)
    result["status"] = ("VERIFIED_TERMINAL_SUCCESS_NO_RETRY" if correct
                        else "INDEPENDENT_VERIFICATION_REFUSED_HOLD")
    result["independent_source_log_checkpoint_qa"] = "PASS" if correct else "NOT_PROVEN"
    # Even fully checked success does not confer any authority to run again.
    result["automatic_retry_allowed"] = False
    result["new_task_authorized"] = False
    result["autonomous_failover_proven"] = False
    result["original_worker_liveness_attested"] = False
    result["next_gate"] = ("TERMINAL_VERIFIED_CLOSE_ONLY_NO_NEW_TASK_AUTHORITY" if correct
                            else "OPERATOR_REVIEW_NO_BLIND_RETRY")
    return result


def verify_success(envelope_path, receipt_path):
    """Explicit host-local independent readback; NO inference/model execution."""
    baseline = reconcile(envelope_path, receipt_path)
    if baseline["status"] != "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY":
        return accept_independent_worker_proof(baseline, None)
    if baseline["host"] != platform.node():
        denied = accept_independent_worker_proof(baseline, None)
        denied["status"] = "WRONG_HOST_INDEPENDENT_VERIFY_DENIED"
        return denied
    ep, rp = pathlib.Path(envelope_path).absolute(), pathlib.Path(receipt_path).absolute()
    env, rec = read_optional(ep), read_optional(rp)
    original_env, original_receipt = digest(env), digest(rec)
    try:
        # Imported ONLY for explicit verify-success on the originating host.
        # check_run replays pinned Git/source diff, log hashes, continuity, and
        # fresh-clone unit + hidden QA. It never invokes Ollama/Aider.
        import vf_office_v2_p0_local_model_worker as worker
        if (worker.SCHEMA != SCHEMA or worker.RECEIPT != RECEIPT_SCHEMA
                or worker.AUTHORITY != AUTHORITY):
            raise Refused("WORKER_CONTRACT_DRIFT")
        proof = worker.check_run(env, rec)
    except Exception:
        refused = accept_independent_worker_proof(baseline, None)
        refused["status"] = "INDEPENDENT_WORKER_READBACK_FAILED_HOLD"
        return refused
    # Detect concurrent journal/receipt or envelope changes during QA replay.
    refreshed = reconcile(ep, rp)
    if (refreshed["status"] != "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY"
            or digest(read_optional(ep)) != original_env
            or digest(read_optional(rp)) != original_receipt):
        refused = accept_independent_worker_proof(refreshed, None)
        refused["status"] = "EVIDENCE_CHANGED_DURING_INDEPENDENT_QA_HOLD"
        return refused
    return accept_independent_worker_proof(refreshed, proof)


def selftest():
    """Fresh temporary synthetic cases. No model, network, scheduler or business state."""
    checks = []
    with tempfile.TemporaryDirectory(prefix="office-p0-unknown-readback-") as td:
        root = pathlib.Path(td)
        ep, rp = root / "envelope.json", root / "receipt.json"
        jp = root / "receipt.json.running"
        env = {
            "schema": SCHEMA, "authority": AUTHORITY, "issue_url": ISSUE,
            "task_id": "p0-lab-synthetic-001", "host": "test-host",
            "base_sha": "a" * 40, "branch": "lab-p0-agent-synthetic-test",
            "worktree_path": str(root / "fixture-repo"),
            "context_checkpoint": str(root / "checkpoint.json"),
            "budget": {"max_attempts": 1, "max_cost_usd": 0},
            "executor": {"kind": KIND, "model": "qwen3.5:4b",
                         "model_digest": "b" * 64},
        }
        journal = {
            "state": "RUNNING", "task_id": env["task_id"],
            "envelope_sha256": digest(env), "host": env["host"],
            "started_at": "2026-10-09T09:00:00Z", "unknown_outcome_rule": "NO_BLIND_RETRY",
            "kind": KIND,
        }
        receipt = {
            "schema": RECEIPT_SCHEMA, "task_id": env["task_id"],
            "envelope_sha256": digest(env), "base_sha": env["base_sha"],
            "branch": env["branch"], "host": env["host"],
            "model": env["executor"]["model"],
            "model_digest": env["executor"]["model_digest"],
            "state": "SUCCEEDED", "exit_code": 0,
            "model_invocations_min": 1, "exact_model_calls": None,
            "receipt_directory": str(root.resolve()),
            "additional_api_spend_usd": 0, "production_authority": "NONE",
            "autonomous_retry": False, "scheduler_proven": False,
            "independent_qa": {"pass": True}, "artifact_sha256": "c" * 64,
        }
        def write(path, obj):
            path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
        def reseal(data):
            val = copy.deepcopy(data)
            val.pop("receipt_sha256", None)
            val["receipt_sha256"] = digest(val)
            return val
        def clear():
            for path in (jp, rp):
                if path.is_file() or path.is_symlink():
                    path.unlink()
        def check(label, expected, *, env_update=None, journal_update=None,
                  receipt_update=None, use_journal=False, use_receipt=False):
            clear()
            e = copy.deepcopy(env)
            if env_update: env_update(e)
            write(ep, e)
            if use_journal:
                j = copy.deepcopy(journal)
                if journal_update: journal_update(j)
                write(jp, j)
            if use_receipt:
                r = copy.deepcopy(receipt)
                if receipt_update: receipt_update(r)
                write(rp, reseal(r))
            snapshot = {str(p): p.read_bytes() for p in (ep, jp, rp) if p.is_file()}
            result = reconcile(ep, rp)
            assert result["status"] == expected, (label, result["status"], expected)
            assert result["verified_success"] is False and not result["automatic_retry_allowed"]
            assert result["owner_process_state"] == "UNKNOWN_NOT_ATTESTED"
            assert snapshot == {str(p): p.read_bytes() for p in (ep, jp, rp) if p.is_file()}
            checks.append(label)
        check("absent_evidence_is_unknown", "NO_EVIDENCE_NOT_PROVEN_UNSTARTED")
        check("orphan_running_journal", "UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY", use_journal=True)
        check("success_claim_requires_real_verify", "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY", use_receipt=True)
        check("concurrent_journal_receipt", "JOURNAL_RECEIPT_CONFLICT_REVIEW", use_journal=True, use_receipt=True)
        check("non_success_receipt", "NON_SUCCESS_RECEIPT_REVIEW_REQUIRED", use_receipt=True,
              receipt_update=lambda r: r.update(state="INDEPENDENT_QA_FAILED", exit_code=2))
        check("failed_plus_journal_conflict", "JOURNAL_RECEIPT_CONFLICT_REVIEW", use_journal=True,
              use_receipt=True, receipt_update=lambda r: r.update(state="EXECUTOR_NONZERO", exit_code=2))
        for label, field, val in (
            ("resealed_wrong_task", "task_id", "other-task-001"),
            ("resealed_wrong_host", "host", "other-host"),
            ("resealed_wrong_base", "base_sha", "d" * 40),
            ("resealed_wrong_branch", "branch", "lab-p0-agent-other"),
            ("resealed_wrong_model", "model", "qwen3.5:9b"),
            ("resealed_wrong_model_pin", "model_digest", "d" * 64),
            ("resealed_wrong_envelope", "envelope_sha256", "d" * 64),
            ("resealed_false_positive_qa", "independent_qa", {"pass": False}),
            ("resealed_model_not_called", "model_invocations_min", 0),
            ("resealed_wrong_receipt_dir", "receipt_directory", "/wrong"),
            ("resealed_paid_spend", "additional_api_spend_usd", 10),
            ("resealed_prod_authority", "production_authority", "PRODUCTION"),
            ("resealed_retry_enabled", "autonomous_retry", True),
            ("resealed_false_as_numeric_spend", "additional_api_spend_usd", False),
            ("resealed_numeric_instead_of_false", "scheduler_proven", 0),
            ("resealed_fleet_authority", "scheduler_proven", True),
            ("resealed_unknown_receipt_state", "state", "COMPLETE"),
        ):
            check(label, "CONFLICT_OR_TAMPER_REFUSE", use_receipt=True,
                  receipt_update=lambda r, f=field, v=val: r.update({f: v}))
        for label, field, val in (
            ("journal_wrong_task", "task_id", "wrong"),
            ("journal_wrong_host", "host", "wrong"),
            ("journal_wrong_envelope", "envelope_sha256", "d" * 64),
            ("journal_wrong_executor", "kind", "WRONG"),
            ("journal_wrong_state", "state", "SUCCEEDED"),
            ("journal_allows_blind_retry", "unknown_outcome_rule", "RETRY"),
        ):
            check(label, "CONFLICT_OR_TAMPER_REFUSE", use_journal=True,
                  journal_update=lambda j, f=field, v=val: j.update({f: v}))
        # A structurally valid self-hash with a forbidden executor is not admitted.
        clear()
        evil = copy.deepcopy(env)
        evil["executor"]["kind"] = "CODEX_CLI"
        write(ep, evil)
        try:
            reconcile(ep, rp)
        except Refused as exc:
            assert str(exc) == "NON_LAB_MODEL_EXECUTOR"
        else:
            raise AssertionError("FORBIDDEN_EXECUTOR_ACCEPTED")
        checks.append("forbidden_executor_rejected")
        # An existing symlink in place of a journal is never followed.
        clear()
        write(ep, env)
        jp.symlink_to(ep)
        try:
            reconcile(ep, rp)
        except Refused as exc:
            assert str(exc) == "SYMLINK_INPUT_DENIED"
        else:
            raise AssertionError("SYMLINK_JOURNAL_ACCEPTED")
        checks.append("symlink_journal_rejected")
        jp.unlink()
        # Integrity check is separate from identity and rejects a raw tamper.
        check("unsealed_changed_receipt", "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY", use_receipt=True)
        changed = json.loads(rp.read_text(encoding="utf-8"))
        changed["receipt_sha256"] = "0" * 64
        write(rp, changed)
        bad = reconcile(ep, rp)
        assert bad["status"] == "CONFLICT_OR_TAMPER_REFUSE"
        checks.append("unsealed_raw_receipt_tamper")
        # Verification promotion is a distinct explicitly requested readback.
        raw = {"status": "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY",
               "task_id": env["task_id"], "host": env["host"],
               "verified_success": False, "automatic_retry_allowed": False}
        proof = {"status": "PASS", "task_id": env["task_id"],
                 "real_local_model_min_invocations": 1,
                 "model_calls_exact": None, "offline_fixture": False,
                 "scheduler_proven": False}
        granted = accept_independent_worker_proof(raw, proof)
        assert granted["status"] == "VERIFIED_TERMINAL_SUCCESS_NO_RETRY"
        assert granted["verified_success"] is True
        assert granted["automatic_retry_allowed"] is False
        assert granted["new_task_authorized"] is False
        assert granted["next_gate"] == "TERMINAL_VERIFIED_CLOSE_ONLY_NO_NEW_TASK_AUTHORITY"
        checks.append("independent_readback_accepts_exact_proof_only")
        for key, value in (
            ("status", "ERROR"),
            ("task_id", "other-task-99"),
            ("real_local_model_min_invocations", 0),
            ("model_calls_exact", 9),
            ("offline_fixture", True),
            ("scheduler_proven", True),
        ):
            wrong = copy.deepcopy(proof)
            wrong[key] = value
            denied = accept_independent_worker_proof(raw, wrong)
            assert denied["status"] == "INDEPENDENT_VERIFICATION_REFUSED_HOLD"
            assert denied["verified_success"] is False
            checks.append("independent_proof_" + key + "_denied")
        raw_bad = dict(raw, status="UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY")
        assert not accept_independent_worker_proof(raw_bad, proof)["verified_success"]
        checks.append("journal_cannot_be_upgraded_to_success")
        assert len(checks) >= 41, len(checks)
    return {"status": "PASS", "tests": len(checks), "checks": checks,
            "model_invocations": 0, "automatic_retries": 0,
            "production_effects": 0, "external_processes_inspected": 0,
            "success_promotion_allowed": False}


def main():
    parser = argparse.ArgumentParser(description="Read-only P0 local-agent UNKNOWN reconciler")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    scan = sub.add_parser("inspect")
    scan.add_argument("--envelope", required=True)
    scan.add_argument("--receipt", required=True)
    verify = sub.add_parser("verify-success")
    verify.add_argument("--envelope", required=True)
    verify.add_argument("--receipt", required=True)
    args = parser.parse_args()
    result = (selftest() if args.command == "selftest" else
              verify_success(args.envelope, args.receipt) if args.command == "verify-success" else
              reconcile(args.envelope, args.receipt))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if args.command != "verify-success" or result.get("verified_success") is True else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refused, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "automatic_retry_allowed": False,
                          "verified_success": False}, sort_keys=True))
        raise SystemExit(2)
