#!/usr/bin/env python3
"""#612: read-only evidence comparison for an explicitly NEW P0 model LAB attempt.

A preserved UNKNOWN attempt is NEVER retried. This tool only checks identity
separation and integrity of two already-existing Task Envelopes. Even a PASS
cannot admit work, mint an owner lease, infer orphan absence, verify a model
success, or serve as a fleet scheduler / recovery controller.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import posixpath
import tempfile

import vf_office_v2_p0_unknown_reconcile as reconciliation

SCHEMA = "velvetos.office-v2.p0-manual-new-attempt-lineage.v0"
OLD_STATE = "UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY"
NEW_STATES = {"NO_EVIDENCE_NOT_PROVEN_UNSTARTED",
              "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY"}


def require(ok, why):
    if not ok:
        raise reconciliation.Refused(why)


def canonical_path(value):
    """Compare normalized identities even when Windows evidence is checked on Mac."""
    require(isinstance(value, str) and bool(value) and "\x00" not in value,
            "ABSOLUTE_DISTINCT_PATH_REQUIRED")
    is_win = len(value) >= 2 and value[1] == ":"
    if is_win:
        require(ntpath.isabs(value) and ".." not in value.replace("/", "\\").split("\\"),
                "NON_CANONICAL_WIN_LAB_PATH")
        return ("win", ntpath.normcase(ntpath.normpath(value)))
    require(posixpath.isabs(value) and ".." not in value.split("/"),
            "NON_CANONICAL_POSIX_LAB_PATH")
    return ("posix", posixpath.normpath(value))


def locations(*pairs):
    result = []
    for label, value in pairs:
        result.append((label, canonical_path(value)))
    require(len({item for _, item in result}) == len(result),
            "ENVELOPE_OR_RECEIPT_PATH_ALIAS")
    return result


def fingerprint(path):
    p = Path(path)
    obj = reconciliation.read_optional(p)
    if obj is None:
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inspect(old_envelope, old_receipt, new_envelope, new_receipt):
    """Never creates, edits, dispatches or authorizes any task."""
    paths = [Path(p).absolute() for p in
             (old_envelope, old_receipt, new_envelope, new_receipt)]
    require(all(p.name == ("envelope.json" if i % 2 == 0 else "receipt.json")
                for i, p in enumerate(paths)), "CANONICAL_ENVELOPE_RECEIPT_NAMES")
    oep, orp, nep, nrp = paths
    ojp = orp.with_suffix(".json.running")
    njp = nrp.with_suffix(".json.running")
    # No IO until path-alias and collision review, then one stable readback.
    locations(*[(str(i), str(p)) for i, p in
                enumerate((oep, orp, ojp, nep, nrp, njp))])
    before = tuple(fingerprint(p) for p in (oep, ojp, orp, nep, njp, nrp))
    old_status = reconciliation.reconcile(oep, orp)
    require(old_status["status"] == OLD_STATE and
            old_status["journal_present"] is True and
            old_status["receipt_present"] is False and
            old_status["automatic_retry_allowed"] is False,
            "OLD_ATTEMPT_NOT_PRESERVED_UNKNOWN")
    old = reconciliation.checked_envelope(reconciliation.read_optional(oep))
    new = reconciliation.checked_envelope(reconciliation.read_optional(nep))
    latest = reconciliation.reconcile(nep, nrp)
    require(latest["status"] in NEW_STATES and
            latest["journal_present"] is False and
            latest["automatic_retry_allowed"] is False,
            "NEW_ATTEMPT_CLAIM_NOT_INDEPENDENT_OR_UNSTARTED")
    for label, key in (("task_id", "task_id"), ("git_base", "base_sha"),
                       ("branch", "branch"), ("checkpoint", "context_checkpoint"),
                       ("worktree", "worktree_path")):
        old_val, new_val = old[key], new[key]
        if key in {"context_checkpoint", "worktree_path"}:
            old_val, new_val = canonical_path(old_val), canonical_path(new_val)
        require(old_val != new_val, "NOT_NEW_DISTINCT_" + label.upper())
    # Reconciliation validates LAB authority, executor type, one attempt, zero
    # extra spend. This checker does not assert original/new process liveness.
    require(old["budget"]["max_attempts"] == new["budget"]["max_attempts"] == 1
            and old["budget"]["max_cost_usd"] == new["budget"]["max_cost_usd"] == 0,
            "RETRY_OR_SPEND_BUDGET_DRIFT")
    require(old["authority"] == new["authority"] ==
            reconciliation.AUTHORITY, "NON_LAB_AUTHORITY")
    locations(("original_worktree", old["worktree_path"]),
              ("new_worktree", new["worktree_path"]),
              ("original_checkpoint", old["context_checkpoint"]),
              ("new_checkpoint", new["context_checkpoint"]))
    after = tuple(fingerprint(p) for p in (oep, ojp, orp, nep, njp, nrp))
    require(before == after and before[1] is not None,
            "EVIDENCE_MUTATED_DURING_READBACK")
    return {
        "schema": SCHEMA,
        "status": "DISTINCT_MANUAL_ATTEMPT_LINEAGE_ONLY_NOT_ADMISSION",
        "original_task_id": old["task_id"], "new_task_id": new["task_id"],
        "original_state": OLD_STATE, "new_state": latest["status"],
        "original_envelope_sha256": reconciliation.digest(old),
        "new_envelope_sha256": reconciliation.digest(new),
        "original_running_journal_raw_sha256": before[1],
        "distinct_task_ids_branches_git_bases_worktrees_checkpoints": True,
        "new_task_success_independently_verified_here": False,
        "original_unknown_retry_authorized": False,
        "new_task_execution_authorized": False,
        "autonomous_recovery_proven": False, "all_orphan_descendants_excluded": False,
        "fleet_lease_or_scheduler_authority": False,
        "production_writer_authority": False,
        "model_invocations": 0, "api_spend_usd": 0,
        "read_only": True,
        "next_gate": "INDEPENDENT_WORKER_QA_AND_OWNER_PROCESS_FENCING_MANUAL_REVIEW",
    }


def selftest():
    passed = []
    with tempfile.TemporaryDirectory(prefix="p0-fresh-lineage-") as t:
        root = Path(t)
        old = root / "old"; new = root / "new"
        old.mkdir(); new.mkdir()
        oep, orp = old / "envelope.json", old / "receipt.json"
        nep, nrp = new / "envelope.json", new / "receipt.json"
        ojp, njp = old / "receipt.json.running", new / "receipt.json.running"
        def env(task, base, directory):
            return {"schema": reconciliation.SCHEMA,
                    "authority": reconciliation.AUTHORITY,
                    "issue_url": reconciliation.ISSUE,
                    "task_id": task, "host": "fixture-host",
                    "base_sha": base, "branch": "lab-p0-agent-" + task,
                    "worktree_path": str(directory / "worktree"),
                    "context_checkpoint": str(directory / "checkpoint.json"),
                    "budget": {"max_attempts": 1, "max_cost_usd": 0},
                    "executor": {"kind": reconciliation.KIND,
                                 "model": "qwen3.5:9b", "model_digest": "b" * 64}}
        original = env("old-manual-unknown-001", "a"*40, old)
        candidate = env("new-manual-task-002", "c"*40, new)
        def write(p, value):
            p.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        def setup(*, change_old=None, change_new=None, old_journal_change=None,
                  old_receipt=False, new_receipt=False, new_journal=False):
            for p in (orp, ojp, nrp, njp):
                if p.exists() or p.is_symlink():
                    p.unlink()
            a, b = copy.deepcopy(original), copy.deepcopy(candidate)
            if change_old:
                change_old(a)
            if change_new:
                change_new(b)
            write(oep, a)
            write(nep, b)
            journal = {"state": "RUNNING", "task_id": a["task_id"],
                       "host": a["host"], "kind": reconciliation.KIND,
                       "envelope_sha256": reconciliation.digest(a),
                       "started_at": "2026-10-09T18:00:00Z",
                       "unknown_outcome_rule": "NO_BLIND_RETRY"}
            if old_journal_change:
                old_journal_change(journal)
            write(ojp, journal)
            def receipt(e, p):
                r = {"schema": reconciliation.RECEIPT_SCHEMA,
                     "task_id": e["task_id"], "host": e["host"],
                     "envelope_sha256": reconciliation.digest(e),
                     "base_sha": e["base_sha"], "branch": e["branch"],
                     "model": e["executor"]["model"],
                     "model_digest": e["executor"]["model_digest"],
                     "state": "SUCCEEDED", "exit_code": 0,
                     "model_invocations_min": 1, "exact_model_calls": None,
                     "receipt_directory": str(p.parent.resolve()),
                     "additional_api_spend_usd": 0,
                     "production_authority": "NONE",
                     "autonomous_retry": False, "scheduler_proven": False,
                     "independent_qa": {"pass": True},
                     "artifact_sha256": "d" * 64}
                r["receipt_sha256"] = reconciliation.digest(r)
                return r
            if old_receipt:
                write(orp, receipt(a, orp))
            if new_receipt:
                write(nrp, receipt(b, nrp))
            if new_journal:
                write(njp, {"state": "RUNNING", "task_id": b["task_id"],
                            "host": b["host"], "kind": reconciliation.KIND,
                            "envelope_sha256": reconciliation.digest(b),
                            "started_at": "2026-10-09T18:20:00Z",
                            "unknown_outcome_rule": "NO_BLIND_RETRY"})
        def snapshots():
            return {str(p): p.read_bytes() for p in (oep, orp, ojp, nep, nrp, njp)
                    if p.is_file() and not p.is_symlink()}
        def expect(label, *, accepted=False, **kwargs):
            setup(**kwargs)
            initial = snapshots()
            try:
                result = inspect(oep, orp, nep, nrp)
            except reconciliation.Refused as exc:
                if accepted:
                    raise AssertionError("EXPECTED_VALID_LINEAGE_REJECTED:" + label) from exc
            else:
                if not accepted:
                    raise AssertionError("UNSAFE_LINEAGE_ACCEPTED:" + label)
                if not (
                    result["status"] == "DISTINCT_MANUAL_ATTEMPT_LINEAGE_ONLY_NOT_ADMISSION"
                    and result["original_unknown_retry_authorized"] is False
                    and result["new_task_execution_authorized"] is False
                    and result["autonomous_recovery_proven"] is False
                    and result["all_orphan_descendants_excluded"] is False
                    and result["model_invocations"] == 0
                ):
                    raise AssertionError("FALSE_LINEAGE_AUTHORITY:" + label)
            if snapshots() != initial:
                raise AssertionError("LINEAGE_TEST_MUTATED_EVIDENCE:" + label)
            passed.append(label)
        expect("positive_distinct_unstarted_not_admission", accepted=True)
        expect("positive_new_success_claim_needs_worker_QA", accepted=True,
               new_receipt=True)
        expect("same_task_id_denied",
               change_new=lambda d: d.update(task_id=original["task_id"]))
        expect("same_git_base_denied",
               change_new=lambda d: d.update(base_sha=original["base_sha"]))
        expect("same_branch_denied",
               change_new=lambda d: d.update(branch=original["branch"]))
        expect("same_worktree_denied",
               change_new=lambda d: d.update(worktree_path=original["worktree_path"]))
        expect("same_checkpoint_denied",
               change_new=lambda d: d.update(context_checkpoint=original["context_checkpoint"]))
        expect("relative_checkpoint_denied",
               change_new=lambda d: d.update(context_checkpoint="checkpoint.json"))
        expect("parent_path_traversal_denied",
               change_new=lambda d: d.update(context_checkpoint=str(new / ".." / "checkpoint.json")))
        expect("forbidden_codex_denied",
               change_new=lambda d: d["executor"].update(kind="CODEX_CLI"))
        expect("paid_api_denied",
               change_new=lambda d: d["budget"].update(max_cost_usd=1))
        expect("multi_attempt_denied",
               change_new=lambda d: d["budget"].update(max_attempts=2))
        expect("non_lab_authority_denied",
               change_new=lambda d: d.update(authority="PRODUCTION"))
        expect("old_journal_tamper_denied",
               old_journal_change=lambda j: j.update(unknown_outcome_rule="RETRY"))
        expect("old_journal_wrong_task_denied",
               old_journal_change=lambda j: j.update(task_id="different"))
        expect("original_conflicting_receipt_denied", old_receipt=True)
        expect("new_receipt_journal_conflict_denied", new_receipt=True,
               new_journal=True)
        expect("new_journal_open_denied", new_journal=True)
        setup(new_receipt=True)
        fake = json.loads(nrp.read_text(encoding="utf-8"))
        fake["receipt_sha256"] = "0" * 64
        write(nrp, fake)
        pre = snapshots()
        try:
            inspect(oep, orp, nep, nrp)
        except reconciliation.Refused:
            require(snapshots() == pre, "TAMPER_TEST_CHANGED_FILES")
            passed.append("tampered_new_receipt_denied")
        else:
            raise AssertionError("TAMPERED_NEW_RECEIPT_ACCEPTED")
        setup()
        ojp.unlink()
        try:
            inspect(oep, orp, nep, nrp)
        except reconciliation.Refused:
            passed.append("missing_original_unknown_journal_denied")
        else:
            raise AssertionError("MISSING_ORIGINAL_JOURNAL_ACCEPTED")
        setup()
        nep.unlink()
        nep.symlink_to(oep)
        try:
            inspect(oep, orp, nep, nrp)
        except reconciliation.Refused:
            passed.append("symlinked_new_envelope_denied")
        else:
            raise AssertionError("SYMLINKED_NEW_ENVELOPE_ACCEPTED")
        nep.unlink()
        require(len(passed) == 21, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS_OFFLINE", "tests": len(passed),
            "cases": passed, "model_invocations": 0, "files_modified_externally": 0,
            "auto_retry_authorized": False, "new_task_execution_authorized": False,
            "all_orphan_descendants_excluded": False, "fleet_authority": False}


def main():
    p = argparse.ArgumentParser(description="Pure read-only P0 manual new-attempt lineage audit")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    check = sub.add_parser("inspect")
    for opt in ("old-envelope", "old-receipt", "new-envelope", "new-receipt"):
        check.add_argument("--" + opt, required=True)
    args = p.parse_args()
    data = selftest() if args.cmd == "selftest" else inspect(
        args.old_envelope, args.old_receipt,
        args.new_envelope, args.new_receipt)
    print(json.dumps(data, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (reconciliation.Refused, ValueError, OSError,
            KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:190],
                          "original_unknown_retry_authorized": False,
                          "new_task_execution_authorized": False}, sort_keys=True))
        raise SystemExit(2)
