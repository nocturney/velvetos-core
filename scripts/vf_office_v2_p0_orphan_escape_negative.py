#!/usr/bin/env python3
"""#612: controlled detached-child negative proof for the P0 local-model LAB.

No models, user files, network, scheduler, signals, or recovery authority.
The real POSIX demonstration starts two temporary Python processes that exit
naturally; it must NEVER infer that an empty process group excludes orphans.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_kernel_identity as kernel

SCHEMA = "vf.office-v2.p0-detached-descendant-negative.v0"
OWNER = "https://github.com/nocturney/velvetos-core/issues/612"
OUTCOMES = {
    "GROUP_EMPTY_ESCAPED_CHILD_STILL_LIVE",
    "GROUP_NONEMPTY_ESCAPED_CHILD_STILL_LIVE",
    "GROUP_SCAN_INCOMPLETE_ESCAPED_CHILD_STILL_LIVE",
}


class Refused(Exception):
    pass


def check(ok, reason):
    if not ok:
        raise Refused(reason)


def digest(data):
    return hashlib.sha256(json.dumps(
        data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def seal(data):
    value = copy.deepcopy(data)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = digest(value)
    return value


def assert_safe_receipt(value):
    check(isinstance(value, dict) and value.get("schema") == SCHEMA, "SCHEMA_DRIFT")
    check(value.get("receipt_sha256") == digest(
        {key: val for key, val in value.items() if key != "receipt_sha256"}
    ), "SEALED_EVIDENCE_DRIFT")
    check(value.get("owner_issue") == OWNER and
          value.get("scope") == "EPHEMERAL_PYTHON_LAB_ONLY", "SCOPE_DRIFT")
    check(value.get("result") in OUTCOMES, "FALSE_ORPHAN_EXCLUSION")
    for name, expected in (
        ("escaped_child_alive_at_snapshot", True),
        ("original_group_owner_exited", True),
        ("all_orphans_excluded", False),
        ("original_attempt_retry_permitted", False),
        ("new_task_authorized", False),
        ("production_writer", False),
        ("fleet_scheduler_authority", False),
        ("model_invocations", 0),
        ("additional_api_spend_usd", 0),
    ):
        check(type(value.get(name)) is type(expected) and
              value.get(name) == expected, "FALSE_SAFETY_ASSERTION_" + name)
    parent, child = value.get("original_parent"), value.get("escaped_child_at_spawn")
    observed = value.get("escaped_child_at_snapshot")
    for row in (parent, child, observed):
        try:
            kernel.require_row(row)
        except kernel.Refused as exc:
            raise Refused("UNTRUSTED_KERNEL_IDENTITY:" + str(exc))
    check(parent["source"] == child["source"] == observed["source"] ==
          "PSUTIL_OS_CREATE_TIME", "NOT_POSIX_BIRTH_PIN")
    check(parent["pid"] != child["pid"] and
          child["pid"] == observed["pid"] and
          child["birth_us"] == observed["birth_us"] and
          child["ppid"] == parent["pid"] and
          parent["birth_us"] <= child["birth_us"], "NOT_ORIGINAL_CHILD_INSTANCE")
    check(parent["pgid"] == parent["pid"] and
          child["pgid"] == child["pid"] and
          child["pgid"] != parent["pgid"] and
          observed["pgid"] == child["pgid"], "ESCAPED_SESSION_NOT_PROVEN")
    group = value.get("original_group_at_snapshot")
    check(isinstance(group, dict), "MISSING_GROUP_OBSERVATION")
    state = group.get("status")
    count = group.get("candidate_count")
    if state == "NO_GROUP_MEMBERS_SEEN":
        check(type(count) is int and count == 0 and
              value["result"] == "GROUP_EMPTY_ESCAPED_CHILD_STILL_LIVE",
              "FALSE_EMPTY_GROUP_CONCLUSION")
    elif state == "POSSIBLE_GROUP_MEMBERS":
        check(type(count) is int and count > 0 and
              value["result"] == "GROUP_NONEMPTY_ESCAPED_CHILD_STILL_LIVE",
              "FALSE_NONEMPTY_GROUP_CONCLUSION")
    else:
        check(state in ("GROUP_SCAN_INCOMPLETE", "GROUP_SCAN_CAP_EXCEEDED",
                        "GROUP_SCAN_NOT_AVAILABLE") and count is None and
              value["result"] == "GROUP_SCAN_INCOMPLETE_ESCAPED_CHILD_STILL_LIVE",
              "INCOMPLETE_GROUP_ASSUMED_SAFE")
    return True


def proof(parent, child, observed, group):
    if group["status"] == "NO_GROUP_MEMBERS_SEEN":
        result = "GROUP_EMPTY_ESCAPED_CHILD_STILL_LIVE"
    elif group["status"] == "POSSIBLE_GROUP_MEMBERS":
        result = "GROUP_NONEMPTY_ESCAPED_CHILD_STILL_LIVE"
    else:
        result = "GROUP_SCAN_INCOMPLETE_ESCAPED_CHILD_STILL_LIVE"
    value = seal({
        "schema": SCHEMA,
        "owner_issue": OWNER,
        "scope": "EPHEMERAL_PYTHON_LAB_ONLY",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_parent": parent,
        "escaped_child_at_spawn": child,
        "escaped_child_at_snapshot": observed,
        "original_group_at_snapshot": group,
        "result": result,
        "escaped_child_alive_at_snapshot": True,
        "original_group_owner_exited": True,
        "all_orphans_excluded": False,
        "original_attempt_retry_permitted": False,
        "new_task_authorized": False,
        "production_writer": False,
        "fleet_scheduler_authority": False,
        "model_invocations": 0,
        "additional_api_spend_usd": 0,
    })
    assert_safe_receipt(value)
    return value


def selftest():
    parent = {"pid": 22001, "ppid": 3, "birth_us": 1700000000000000,
              "pgid": 22001, "source": "PSUTIL_OS_CREATE_TIME"}
    child = {"pid": 22002, "ppid": 22001, "birth_us": 1700000000000050,
             "pgid": 22002, "source": "PSUTIL_OS_CREATE_TIME"}
    observed = dict(child, ppid=1)
    cases = []
    for group in (
        {"status": "NO_GROUP_MEMBERS_SEEN", "candidate_count": 0},
        {"status": "POSSIBLE_GROUP_MEMBERS", "candidate_count": 1},
        {"status": "GROUP_SCAN_INCOMPLETE", "candidate_count": None},
    ):
        assert_safe_receipt(proof(parent, child, observed, group))
        cases.append("valid_fail_closed_" + group["status"])
    safe = proof(parent, child, observed, {
        "status": "NO_GROUP_MEMBERS_SEEN", "candidate_count": 0
    })
    corruptions = (
        ("claim_orphans_excluded", lambda x: x.update(all_orphans_excluded=True)),
        ("claim_original_retry", lambda x: x.update(original_attempt_retry_permitted=True)),
        ("claim_new_task", lambda x: x.update(new_task_authorized=True)),
        ("claim_production", lambda x: x.update(production_writer=True)),
        ("claim_fleet_authority", lambda x: x.update(fleet_scheduler_authority=True)),
        ("fake_group_members", lambda x: x["original_group_at_snapshot"].update(candidate_count=2)),
        ("fake_escaped_group", lambda x: x["escaped_child_at_spawn"].update(pgid=22001)),
        ("fake_escaped_birth", lambda x: x["escaped_child_at_snapshot"].update(birth_us=33)),
        ("fake_parent_link", lambda x: x["escaped_child_at_spawn"].update(ppid=42)),
        ("fake_host_os_source", lambda x: x["original_parent"].update(source="WINDOWS_CIM_CREATION_DATE", pgid=None)),
        ("claim_no_escape", lambda x: x.update(escaped_child_alive_at_snapshot=False)),
        ("unbounded_model", lambda x: x.update(model_invocations=1)),
    )
    for name, change in corruptions:
        fake = copy.deepcopy(safe)
        change(fake)
        fake = seal(fake)  # maliciously RE-SEALED: self-hash is not authority
        try:
            assert_safe_receipt(fake)
        except (Refused, kernel.Refused):
            cases.append(name + "_denied")
        else:
            raise AssertionError("RESEALED_FALSE_EVIDENCE_ACCEPTED:" + name)
    bad = copy.deepcopy(safe)
    bad["receipt_sha256"] = "0" * 64
    try:
        assert_safe_receipt(bad)
    except Refused:
        cases.append("tampered_unsealed_denied")
    else:
        raise AssertionError("BROKEN_HASH_ACCEPTED")
    check(len(cases) == 16, "NEGATIVE_CASES_MISSING")
    return {"status": "PASS", "tests": len(cases), "cases": cases,
            "live_processes_launched": 0, "model_invocations": 0,
            "original_attempt_retry_permitted": False,
            "all_orphans_excluded": False}


def _escape(root):
    stop = Path(root) / "stop"
    end = time.monotonic() + 12.0
    while time.monotonic() < end:
        if stop.exists():
            return
        time.sleep(0.045)


def _owner(root):
    root = Path(root)
    parent = kernel.sample(os.getpid())
    check(parent is not None and parent["pgid"] == parent["pid"],
          "LAB_OWNER_IS_NOT_ISOLATED_GROUP")
    child_proc = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve()), "_escape", str(root)],
        cwd=str(root), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    child = kernel.sample(child_proc.pid)
    check(child is not None and child["ppid"] == parent["pid"] and
          child["pgid"] == child["pid"], "NO_TRUE_DETACHED_CHILD")
    marker = root / "pinned-child.json"
    with marker.open("x", encoding="utf-8") as fp:
        json.dump({"parent": parent, "child": child}, fp, sort_keys=True)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    time.sleep(0.2)  # controller must observe this parent's natural exit


def live(output_path):
    check(os.name != "nt", "WINDOWS_REQUIRES_DISTINCT_NATIVE_JOB_OBJECT_GATE")
    output = Path(output_path).absolute()
    check(not output.exists() and not output.is_symlink(),
          "NEVER_OVERWRITE_OR_FOLLOW_OUTPUT")
    with tempfile.TemporaryDirectory(prefix="p0-orphan-escape-negative-") as td:
        root = Path(td)
        stop = root / "stop"
        owner = None
        escaped_pid = None
        cleanup_seen = False
        try:
            owner = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "_owner", td],
                cwd=td, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True,
            )
            marker = root / "pinned-child.json"
            deadline = time.monotonic() + 5
            while not marker.is_file() and time.monotonic() < deadline:
                if owner.poll() is not None:
                    raise Refused("OWNER_EXITED_BEFORE_CHILD_EVIDENCE")
                time.sleep(0.025)
            check(marker.is_file(), "OWNED_CHILD_NOT_OBSERVED")
            rows = json.loads(marker.read_text(encoding="utf-8"))
            original_parent, original_child = rows["parent"], rows["child"]
            escaped_pid = original_child["pid"]
            stdout, stderr = owner.communicate(timeout=5)
            check(owner.returncode == 0 and not stdout and not stderr,
                  "OWNER_DID_NOT_EXIT_CLEANLY")
            child_at_snapshot = kernel.sample(escaped_pid)
            check(child_at_snapshot is not None and
                  child_at_snapshot["birth_us"] == original_child["birth_us"],
                  "ESCAPED_CHILD_NOT_SAME_LIVE_KERNEL_INSTANCE")
            group = kernel.group_members(original_parent["pgid"])
            report = proof(original_parent, original_child, child_at_snapshot, group)
            with output.open("x", encoding="utf-8") as fp:
                json.dump(report, fp, sort_keys=True, indent=2)
                fp.write("\n")
                fp.flush()
                os.fsync(fp.fileno())
            return report
        finally:
            stop.touch()  # instruct ONLY this fixture's child to exit normally
            if owner is not None and owner.poll() is None:
                try:
                    owner.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    pass  # no signals or uncontrolled process termination
            if escaped_pid is not None:
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    try:
                        row = kernel.sample(escaped_pid)
                    except kernel.Refused:
                        row = None  # zombie isn't a live owner
                    if row is None:
                        cleanup_seen = True
                        break
                    time.sleep(0.04)
                if not cleanup_seen:
                    print(json.dumps({"cleanup_warning":
                          "OWNED_DETACHED_CHILD_UNCONFIRMED_STOP; SELF_EXITS_WITHIN_12S"}),
                          file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("selftest")
    modes.add_parser("_owner", help=argparse.SUPPRESS).add_argument("root")
    modes.add_parser("_escape", help=argparse.SUPPRESS).add_argument("root")
    actual = modes.add_parser("live", help="One-time isolated POSIX negative fixture")
    actual.add_argument("--output", required=True)
    audit = modes.add_parser("verify", help="Pure offline independent receipt verification")
    audit.add_argument("--evidence", required=True)
    args = parser.parse_args()
    if args.mode == "verify":
        evidence_path = Path(args.evidence)
        check(not evidence_path.is_symlink() and evidence_path.is_file(),
              "EVIDENCE_NOT_A_REGULAR_FILE")
        raw = evidence_path.read_bytes()
        check(1 <= len(raw) <= 65536, "EVIDENCE_OVERSIZED_OR_EMPTY")
        evidence = json.loads(raw.decode("utf-8"))
        assert_safe_receipt(evidence)
        print(json.dumps({"status": "PASS", "independent_offline_verify": True,
                          "result": evidence["result"],
                          "no_auto_retry": True,
                          "model_invocations": 0,
                          "receipt_sha256": evidence["receipt_sha256"]}, sort_keys=True))
        return
    if args.mode == "_escape":
        _escape(args.root)
        return
    if args.mode == "_owner":
        _owner(args.root)
        return
    report = selftest() if args.mode == "selftest" else live(args.output)
    print(json.dumps({k: report[k] for k in (
        ("status", "tests", "cases", "live_processes_launched", "model_invocations",
         "original_attempt_retry_permitted", "all_orphans_excluded")
        if args.mode == "selftest" else
        ("schema", "result", "escaped_child_alive_at_snapshot",
         "all_orphans_excluded", "original_attempt_retry_permitted",
         "receipt_sha256")
    )}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, kernel.Refused, ValueError, OSError,
            KeyError, TypeError, AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:170],
                          "original_attempt_retry_permitted": False,
                          "all_orphans_excluded": False}))
        raise SystemExit(2)
