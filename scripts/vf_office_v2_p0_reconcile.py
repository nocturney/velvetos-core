#!/usr/bin/env python3
"""Read-only #612 P0 local-model journal and receipt reconciliation.

Never launches, retries, terminates, migrates or requeues workers. A self-hash
is not independent evidence of execution success; PID sightings without a
pinned start identity cannot establish process ownership. No business effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

TASK_SCHEMA = "velvetos.office-v2.p0-local-model-envelope.v1"
RECEIPT_SCHEMA = "velvetos.office-v2.p0-local-model-receipt.v1"
AUTHORITY = "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,95}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA1 = re.compile(r"[0-9a-f]{40}\Z")


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def read_obj(path):
    path = pathlib.Path(path)
    if path.is_symlink():
        raise ValueError("SYMLINK_EVIDENCE_DENIED")
    if path.stat().st_size > 1048576:
        raise ValueError("OVERSIZED_EVIDENCE")
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError("EVIDENCE_OBJECT_REQUIRED")
    return value


def parsed_time(text):
    if not isinstance(text, str):
        return None
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


def reconcile(envelope, journal=None, receipt=None, independent_verifier=None):
    """Conservative immutable observation. A verifier must replay full QA.

    The existing v1 RUNNING journal does not pin PID plus process start time.
    Hence even a process scan cannot prove that its owner is alive or dead.
    """
    output = {
        "schema": "vf.office-v2.p0-unknown-reconciliation.v1",
        "state": "BLOCKED_INVALID_EVIDENCE", "reason": "INVALID_TASK_ENVELOPE",
        "task_id": None, "automatic_retry_allowed": False,
        "new_attempt_authorized": False, "cross_host_failover_proven": False,
        "external_effects_reconciled": False, "success_proven": False,
        "ownership_proven": False, "journal_process_identity": "NOT_RECORDED_IN_V1",
        "process_liveness_checked": False, "model_invoked_during_inspection": False,
        "original_journal_preserved": journal is not None,
    }
    if (type(envelope) is not dict or envelope.get("schema") != TASK_SCHEMA
            or envelope.get("authority") != AUTHORITY or envelope.get("issue_url") != ISSUE
            or not isinstance(envelope.get("task_id"), str)
            or not TASK_ID.fullmatch(envelope["task_id"])
            or not isinstance(envelope.get("host"), str) or not envelope["host"]
            or not isinstance(envelope.get("base_sha"), str)
            or not SHA1.fullmatch(envelope["base_sha"])
            or not isinstance(envelope.get("branch"), str) or not envelope["branch"]):
        return output
    task_id = envelope["task_id"]
    output["task_id"] = task_id
    if journal is not None:
        if (type(journal) is not dict or journal.get("state") != "RUNNING"
                or journal.get("task_id") != task_id
                or journal.get("host") != envelope["host"]
                or journal.get("envelope_sha256") != digest(envelope)
                or journal.get("unknown_outcome_rule") != "NO_BLIND_RETRY"
                or journal.get("kind") != "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1"
                or parsed_time(journal.get("started_at")) is None):
            output["reason"] = "JOURNAL_IDENTITY_OR_SHAPE_DRIFT"
            return output
    if receipt is None:
        if journal is None:
            output.update(state="NOT_STARTED_UNVERIFIED", reason="NO_JOURNAL_OR_RECEIPT")
        else:
            output.update(state="UNKNOWN_OUTCOME", reason="DURABLE_JOURNAL_NO_TERMINAL_RECEIPT")
        return output
    if type(receipt) is not dict:
        output["reason"] = "RECEIPT_OBJECT_REQUIRED"
        return output
    if (receipt.get("schema") != RECEIPT_SCHEMA
            or receipt.get("task_id") != task_id
            or receipt.get("host") != envelope["host"]
            or receipt.get("base_sha") != envelope["base_sha"]
            or receipt.get("branch") != envelope["branch"]
            or receipt.get("envelope_sha256") != digest(envelope)
            or not isinstance(receipt.get("receipt_sha256"), str)
            or not SHA256.fullmatch(receipt["receipt_sha256"])
            or receipt["receipt_sha256"] != digest({
                k: v for k, v in receipt.items() if k != "receipt_sha256"
            })
            or parsed_time(receipt.get("started_at")) is None
            or parsed_time(receipt.get("finished_at")) is None):
        output["reason"] = "RECEIPT_IDENTITY_OR_HASH_DRIFT"
        return output
    if parsed_time(receipt["finished_at"]) < parsed_time(receipt["started_at"]):
        output["reason"] = "RECEIPT_TIME_ORDER_INVALID"
        return output
    if journal is not None:
        output.update(state="UNKNOWN_OUTCOME",
                      reason="JOURNAL_AND_TERMINAL_RECEIPT_CONFLICT")
        return output
    if receipt.get("state") != "SUCCEEDED":
        output.update(state="TERMINAL_NON_SUCCESS", reason="RECEIPT_NON_SUCCESS_NO_RETRY")
        return output
    qa = receipt.get("independent_qa")
    if (type(qa) is not dict or receipt.get("exit_code") != 0
            or receipt.get("model_invocations_min") != 1
            or receipt.get("exact_model_calls", "NOT_RECORDED") is not None
            or receipt.get("production_authority") != "NONE"
            or receipt.get("additional_api_spend_usd") != 0
            or receipt.get("autonomous_retry") is not False
            or receipt.get("scheduler_proven") is not False
            or qa.get("pass") is not True):
        output["reason"] = "FALSE_SUCCESS_FIELDS"
        return output
    if independent_verifier is None:
        output.update(state="SUCCESS_CLAIM_UNVERIFIED",
                      reason="INDEPENDENT_REPLAY_REQUIRED")
        return output
    try:
        verified = independent_verifier(envelope, receipt)
    except Exception:
        output["reason"] = "INDEPENDENT_REPLAY_FAILED"
        return output
    if (type(verified) is not dict or verified.get("status") != "PASS"
            or verified.get("task_id") != task_id
            or verified.get("real_local_model_min_invocations") != 1
            or verified.get("offline_fixture") is not False):
        output["reason"] = "INDEPENDENT_REPLAY_NOT_PASS"
        return output
    output.update(state="VERIFIED_TERMINAL_SUCCESS",
                  reason="INDEPENDENT_REPLAY_PASS", success_proven=True)
    return output


def selftest():
    env = {
        "schema": TASK_SCHEMA, "authority": AUTHORITY, "issue_url": ISSUE,
        "task_id": "local-model-reconcile-01", "host": "MacMiniOffice.local",
        "base_sha": "a" * 40, "branch": "lab-p0-agent-local-model-reconcile-01",
    }
    journal = {
        "state": "RUNNING", "task_id": env["task_id"],
        "envelope_sha256": digest(env), "host": env["host"],
        "started_at": "2026-10-09T01:00:00+00:00",
        "unknown_outcome_rule": "NO_BLIND_RETRY",
        "kind": "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1",
    }
    receipt = {
        "schema": RECEIPT_SCHEMA, "task_id": env["task_id"],
        "envelope_sha256": digest(env), "base_sha": env["base_sha"],
        "branch": env["branch"], "host": env["host"],
        "started_at": "2026-10-09T01:00:00+00:00",
        "finished_at": "2026-10-09T01:00:25+00:00",
        "state": "SUCCEEDED", "exit_code": 0, "model_invocations_min": 1,
        "exact_model_calls": None, "production_authority": "NONE",
        "additional_api_spend_usd": 0, "autonomous_retry": False,
        "scheduler_proven": False, "independent_qa": {"pass": True},
    }

    def seal(value):
        result = dict(value)
        result["receipt_sha256"] = digest(result)
        return result

    receipt = seal(receipt)

    def good(e, r):
        return {"status": "PASS", "task_id": e["task_id"],
                "real_local_model_min_invocations": 1, "offline_fixture": False}

    cases = []

    def check(name, e=env, j=None, r=None, verifier=None, state=None):
        result = reconcile(e, j, r, verifier)
        assert result["state"] == state, (name, result)
        assert result["automatic_retry_allowed"] is False
        assert result["new_attempt_authorized"] is False
        assert result["cross_host_failover_proven"] is False
        assert result["ownership_proven"] is False
        assert result["model_invoked_during_inspection"] is False
        cases.append(name)

    check("no_evidence", state="NOT_STARTED_UNVERIFIED")
    check("unknown_journal", j=journal, state="UNKNOWN_OUTCOME")
    check("self_hash_unverified", r=receipt, state="SUCCESS_CLAIM_UNVERIFIED")
    check("independent_replay", r=receipt, verifier=good, state="VERIFIED_TERMINAL_SUCCESS")
    check("journal_receipt_conflict", j=journal, r=receipt, state="UNKNOWN_OUTCOME")
    check("verifier_raises", r=receipt,
          verifier=lambda e, r: (_ for _ in ()).throw(ValueError()),
          state="BLOCKED_INVALID_EVIDENCE")
    check("lying_verifier", r=receipt, verifier=lambda e, r: {"status": "PASS"},
          state="BLOCKED_INVALID_EVIDENCE")
    check("foreign_journal", j=dict(journal, host="Chris"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("stale_journal", j=dict(journal, envelope_sha256="0" * 64),
          state="BLOCKED_INVALID_EVIDENCE")
    check("unsafe_retry_marker", j=dict(journal, unknown_outcome_rule="AUTO_RETRY"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("bad_receipt_hash", r=dict(receipt, receipt_sha256="0" * 64),
          state="BLOCKED_INVALID_EVIDENCE")

    def changed(**kwargs):
        value = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        value.update(kwargs)
        return seal(value)

    check("resealed_cross_host", r=changed(host="Chris"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("resealed_paid", r=changed(additional_api_spend_usd=1),
          state="BLOCKED_INVALID_EVIDENCE")
    check("resealed_bad_qa", r=changed(independent_qa={"pass": False}),
          state="BLOCKED_INVALID_EVIDENCE")
    check("malformed_qa_none", r=changed(independent_qa=None),
          state="BLOCKED_INVALID_EVIDENCE")
    check("terminal_failure", r=changed(state="EXECUTOR_NONZERO"),
          state="TERMINAL_NON_SUCCESS")
    check("invented_exact_model_count", r=changed(exact_model_calls=1),
          state="BLOCKED_INVALID_EVIDENCE")
    check("production_envelope", e=dict(env, authority="PRODUCTION"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("invalid_journal_time", j=dict(journal, started_at="yesterday"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("inverted_receipt_time", r=changed(started_at="2026-10-10T01:00:00Z"),
          state="BLOCKED_INVALID_EVIDENCE")
    check("mixed_timezone_correct", r=changed(
        started_at="2026-10-09T03:00:00+02:00",
        finished_at="2026-10-09T01:30:00Z"),
        state="SUCCESS_CLAIM_UNVERIFIED")
    return {
        "status": "PASS", "tests": len(cases), "read_only": True,
        "model_invocations": 0, "automatic_retry": False,
        "automatic_failover_proven": False, "production_authority": "NONE",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("selftest", "inspect"))
    ap.add_argument("--envelope", type=pathlib.Path)
    ap.add_argument("--receipt", type=pathlib.Path)
    ap.add_argument("--journal", type=pathlib.Path)
    ap.add_argument("--independent-replay", action="store_true",
                    help="same-host canonical QA replay, never a model invocation")
    args = ap.parse_args()
    if args.action == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return 0
    if not args.envelope or not args.receipt:
        ap.error("inspect requires --envelope and --receipt")
    try:
        env = read_obj(args.envelope)
        jpath = args.journal or args.receipt.with_suffix(args.receipt.suffix + ".running")
        journal = read_obj(jpath) if jpath.exists() or jpath.is_symlink() else None
        receipt = read_obj(args.receipt) if args.receipt.exists() or args.receipt.is_symlink() else None
        verifier = None
        if args.independent_replay:
            import vf_office_v2_p0_local_model_worker as worker
            verifier = worker.check_run
        result = reconcile(env, journal, receipt, verifier)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema": "vf.office-v2.p0-unknown-reconciliation.v1",
            "state": "BLOCKED_INVALID_EVIDENCE", "reason": type(exc).__name__,
            "automatic_retry_allowed": False, "success_proven": False,
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {
        "NOT_STARTED_UNVERIFIED", "UNKNOWN_OUTCOME", "TERMINAL_NON_SUCCESS",
        "VERIFIED_TERMINAL_SUCCESS", "SUCCESS_CLAIM_UNVERIFIED"
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
