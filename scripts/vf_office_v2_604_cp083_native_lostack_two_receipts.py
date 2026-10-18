#!/usr/bin/env python3
"""CP083 #604: two fresh REAL local Git/SQLite fault receipts; SECURITY RED.

Uses the already-reviewed OfflineLab native implementation consumed by CP083.
Every subprocess writes only a temporary, marker-guarded bare Git repository.
The "provider" in this lane is a synthetic file, NOT live etcd/mTLS/UID/Core.
Test-only injected ACK drops and actual process deaths are distinguished.
No GitHub remote, credentials, production writes, privileged actions or retry.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import sqlite3
import subprocess
import sys
import tempfile
import uuid

for name in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_AUTH_SOCK",
             "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ.pop(name, None)
os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
os.environ["GIT_TERMINAL_PROMPT"] = "0"

import vf_office_v2_604_native_git_crash_reconcile_offline as native

SCHEMA = "velvetos.office-v2.604.cp083.nativegit-sqlite-two-fresh.v1"
KEY = "t1"
CASES = (
    ("process_death_before_git", "crash_after_prepare", 91, False, False),
    ("process_death_after_git", "crash_after_native_git", 92, True, False),
    ("injected_ack_drop_before_git", "lost_ack_before_git", 0, False, True),
    ("injected_ack_drop_after_git", "lost_ack_after_git", 0, True, True),
    ("synthetic_revocation_after_git", "provider_revoked_after_git", 0, True, False),
    ("normal_local_cas", "none", 0, True, False),
)


def require(condition, label, checks):
    if condition is not True:
        raise AssertionError(label)
    checks.append(label)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_head(lab):
    command = ["git", "--git-dir", str(lab.repo), "rev-parse",
               "--verify", native.REF]
    p = subprocess.run(command, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, timeout=8,
                       env=native.ENV)
    if p.returncode != 0 or not native.sha(p.stdout.strip()):
        raise RuntimeError("NATIVE_GIT_READBACK_FAILED")
    return p.stdout.strip()


def readback(root):
    lab = native.OfflineLab(root)
    if not lab.verified():
        raise RuntimeError("NOT_ISOLATED_OFFLINE_LAB")
    with lab.connect() as c:
        mode = c.execute("PRAGMA journal_mode").fetchone()[0]
        sync = c.execute("PRAGMA synchronous").fetchone()[0]
        total = c.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    return {
        "git_ref": git_head(lab),
        "sqlite_record": lab.status(KEY),
        "sqlite_attempt_rows": total,
        "sqlite_synchronous_full": sync == 2,
        "sqlite_journal_mode": mode,
        "frozen": lab.frozen(),
    }


def invoke_fresh(mode, root):
    p = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), mode, str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=16, env=os.environ.copy(),
    )
    if p.returncode != 0:
        raise RuntimeError("RESTARTED_PROCESS_FAILED:" + p.stderr[-300:])
    return json.loads(p.stdout)


def case_run(parent, case, fault, expected_exit, wrote, drop_ack, checks):
    lab = native.OfflineLab.create(parent / case)
    seed = git_head(lab)
    intent = lab.candidate(KEY)
    lab.save_request(intent)
    # An actual child interpreter calls the exact existing native OfflineLab
    # code. For drop_ack, the test's stdout boundary discards its reply.
    argv = [sys.executable, str(Path(native.__file__).resolve()),
            "worker", str(lab.root), KEY, fault]
    if drop_ack:
        p = subprocess.run(argv, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, text=True, timeout=15,
                           env=os.environ.copy())
        observed_ack = None
    else:
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, timeout=15,
                           env=os.environ.copy())
        observed_ack = p.stdout.strip()
    require(p.returncode == expected_exit, case + ":expected_exit", checks)
    actual = git_head(lab)
    require(actual == (intent.candidate if wrote else seed),
            case + ":native_ref_truth", checks)
    pre = invoke_fresh("--observe", lab.root)
    require(pre["git_ref"] == actual and pre["sqlite_attempt_rows"] == 1,
            case + ":independent_process_readback", checks)
    require(pre["sqlite_synchronous_full"] is True,
            case + ":sqlite_full_requested", checks)
    if case == "normal_local_cas":
        require(pre["sqlite_record"]["state"] == "COMMITTED_READBACK"
                and pre["frozen"] is False
                and json.loads(observed_ack)["state"] == "COMMITTED_READBACK",
                case + ":commit_only_after_readback", checks)
        stale = lab.git("update-ref", native.REF, seed,
                        seed, allow_error=True)
        require(stale.returncode != 0 and git_head(lab) == actual,
                case + ":native_stale_cas_rejected", checks)
        classification = "NO_PENDING_UNKNOWN"
        post = pre
    else:
        require(pre["sqlite_record"]["state"] in
                ("EFFECT_IN_FLIGHT", "UNKNOWN_EFFECT_RECONCILE"),
                case + ":uncertain_not_success", checks)
        if expected_exit in (91, 92):
            require(observed_ack == "" and
                    pre["sqlite_record"]["state"] == "EFFECT_IN_FLIGHT",
                    case + ":real_child_died_no_ack", checks)
        if drop_ack:
            require(observed_ack is None and
                    pre["sqlite_record"]["state"] == "UNKNOWN_EFFECT_RECONCILE",
                    case + ":injected_ack_blackhole_explicit", checks)
        result = invoke_fresh("--recover", lab.root)
        classification = result["classification"]
        post = result["after"]
        require(classification ==
                ("REMOTE_ADVANCED_REVIEW_REQUIRED" if wrote
                 else "REMOTE_UNCHANGED_REVIEW_REQUIRED"),
                case + ":authoritative_reconciliation_classification", checks)
        require(post["frozen"] is True and
                post["sqlite_record"]["state"] == "UNKNOWN_EFFECT_RECONCILE",
                case + ":durable_unknown_after_restart", checks)
    # Real duplicate attempt from a second process must be refused, without
    # touching the ref or resetting the durable journal.
    duplicate = subprocess.run(
        [sys.executable, str(Path(native.__file__).resolve()),
         "worker", str(lab.root), KEY, "none"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=15, env=os.environ.copy(),
    )
    require(duplicate.returncode == 0 and
            json.loads(duplicate.stdout)["state"] == "NOT_ADMITTED",
            case + ":blind_retry_denied", checks)
    final = invoke_fresh("--observe", lab.root)
    require(final["git_ref"] == actual
            and final["sqlite_attempt_rows"] == 1
            and final["sqlite_record"]["state"] ==
            post["sqlite_record"]["state"],
            case + ":no_second_effect_after_restart", checks)
    return {
        "fault": fault,
        "fault_kind": ("REAL_PROCESS_TERMINATION_NO_ACK"
                       if expected_exit in (91, 92) else
                       "EXPLICIT_INJECTED_ACK_BLACKHOLE"
                       if drop_ack else "SYNTHETIC_PROVIDER_REVOKE"
                       if fault == "provider_revoked_after_git" else
                       "NORMAL_LOCAL_ACK"),
        "worker_exit_code": p.returncode,
        "ack_seen_by_observer": bool(observed_ack),
        "sqlite_journal_mode": final["sqlite_journal_mode"],
        "sqlite_full_requested": final["sqlite_synchronous_full"],
        "seed_sha": seed,
        "intent_sha": intent.candidate,
        "head_after_native": actual,
        "recovery_classification": classification,
        "journal_state_after_new_process": final["sqlite_record"]["state"],
        "frozen_after_new_process": final["frozen"],
        "native_stale_cas_denied": True if case == "normal_local_cas" else None,
        "attempt_rows_after_retry": final["sqlite_attempt_rows"],
    }


def run(label):
    checks = []
    observed = {}
    with tempfile.TemporaryDirectory(prefix="vf604-cp083-native-only-") as t:
        base = Path(t)
        for case in CASES:
            observed[case[0]] = case_run(base, *case, checks)
    require(len(checks) == 53, "exact_53_named_assertions", checks)
    return {
        "schema": SCHEMA,
        "run_id": uuid.uuid4().hex,
        "declared_device": label,
        "os_host_observed": socket.gethostname(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "git_version": subprocess.run(["git", "--version"],
                        capture_output=True, text=True, timeout=8).stdout.strip(),
        "driver_source_sha256": sha_file(__file__),
        "native_implementation_sha256": sha_file(native.__file__),
        "security_admission": "RED",
        "production_authority": False,
        "synthetic_provider_only": True,
        "etcd_mtls_not_executed": True,
        "guest_uid_gate_not_executed": True,
        "native_local_bare_git_executed": True,
        "sqlite_durable_journal_executed": True,
        "github_remote_writes": 0,
        "signed_host_attestation": False,
        "check_count": len(checks),
        "checks": checks,
        "observations": observed,
        "status": "PASS_NATIVE_LOCAL_ONLY",
    }


def main(argv):
    if len(argv) == 2 and argv[0] == "--run":
        print(json.dumps(run(argv[1]), sort_keys=True, separators=(",", ":")))
        return 0
    if len(argv) == 2 and argv[0] in ("--observe", "--recover"):
        lab = native.OfflineLab(argv[1])
        if argv[0] == "--observe":
            out = readback(argv[1])
        else:
            classification = lab.reconcile(KEY, process_terminated=True)
            out = {"classification": classification,
                   "after": readback(argv[1])}
        print(json.dumps(out, sort_keys=True, separators=(",", ":")))
        return 0
    print("CP083 native-local lab only: --run DEVICE", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (AssertionError, RuntimeError, OSError, ValueError,
            sqlite3.Error, subprocess.TimeoutExpired) as exc:
        print("FAIL_CLOSED_NATIVE_LOCAL_PROOF:" + str(exc), file=sys.stderr)
        raise SystemExit(2)
