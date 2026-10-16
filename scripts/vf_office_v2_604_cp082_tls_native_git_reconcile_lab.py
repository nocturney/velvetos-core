#!/usr/bin/env python3
"""CP082: one disposable REAL TLS/RBAC etcd grant + native LOCAL Git/SQLite effect.

No production credentials, remote GitHub, worker model source, privileged UID,
or live Core issuer. The native Git and journal exercise ONLY isolated scratch
files under a new mode-0700 directory. Security admission must remain RED.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import uuid

import vf_office_v2_604_cp081_mtls_atomic_admission_lab as cp081
import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity
import vf_office_v2_604_native_git_crash_reconcile_offline as offline

SCHEMA = "velvetos.office-v2.604.cp082.authenticated-local-git-unknown-lab.v1"
ENV = "VF604_CP082_DISPOSABLE_GUEST_ONLY"
PERMIT = "VF604_CP082_EXPLICIT_NO_REMOTE_GIT"

def require(condition, label):
    if not condition:
        raise cp081.Denied("CP082_" + label)

def enable_case_sink_read(e, k):
    for name in ("owner", "generation", "intent", "ref"):
        e.ctl_ok("root", "role", "grant-permission", "cp081-sink",
                 "readwrite" if name == "intent" else "read", k[name])

def observe_granted(e, k):
    """Only the sink's genuine restricted mTLS certificate observes the grant."""
    owner = e.cli_range("sink", k["owner"])
    generation = e.cli_range("sink", k["generation"])
    intent = e.cli_range("sink", k["intent"])
    ref = e.cli_range("sink", k["ref"])
    good = bool(
        owner and owner["value"] == "owner-test-1" and owner["lease"] > 0
        and owner["mod_revision"] == k["modrev"]
        and generation and generation["value"] == "COMMIT_ADMITTED"
        and intent and intent["value"] == "COMMIT_ADMITTED" and intent["lease"] == 0
        and ref and ref["value"] == "RESERVED" and ref["lease"] == 0
    )
    return {
        "actor": "worker-a" if good else "",
        "epoch": 7, "phase": "ACTIVE" if good else "NOT_ADMITTED",
        "ttl_seconds": 1 if good else 0,
        "revision": generation["mod_revision"] if generation else 1,
    }

def run(etcd: Path, ctl: Path) -> dict:
    # Reuse the exact CP081 lab OS, credential and official binary checks.
    cp081.configuration_guard(etcd, ctl)
    require(platform.machine() == "aarch64" and os.geteuid() != 0,
            "ROOTLESS_ARM64_REQUIRED")
    require(os.getenv(ENV) == PERMIT, "EXPLICIT_CP082_PERMISSION_REQUIRED")
    require(sys.platform == "linux", "DISPOSABLE_LINUX_ONLY")
    identity.PINNED_ETCD, identity.PINNED_CTL = cp081.PIN_ETCD, cp081.PIN_CTL
    os.umask(0o077)
    checks = []
    def yes(label, ok):
        require(ok is True, "CHECK_FAILED_" + label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix="vf604-cp082-", dir="/tmp") as td:
        root = Path(td)
        root.chmod(0o700)
        provider_root = root / "tls-provider"
        provider_root.mkdir(mode=0o700)
        fixture = identity.AuthenticatedEtcd(provider_root, etcd, ctl)
        fixture.start()
        try:
            prefix = "/vf604/cp082/synthetic/" + uuid.uuid4().hex + "/"
            def setup(which):
                k = cp081.prepare(fixture, prefix, which, ttl=90)
                if which == "normal":
                    cp081.init_roles(fixture,k["owner"],k["generation"],k["intent"],k["ref"])
                else:
                    enable_case_sink_read(fixture,k)
                yes(which + "_real_root_committed_admission",cp081.admit(fixture,k))
                # Deliberately split: etcd is real TLS/RBAC, Git is native
                # scratch under the SAME unprivileged UID, NOT a GitHub sink.
                lab = offline.OfflineLab.create(root / ("local-" + which))
                lab.observe = lambda: observe_granted(fixture,k)
                value=lab.observe()
                yes(which + "_real_mtls_sink_grant_visible",
                    value["phase"] == "ACTIVE" and value["ttl_seconds"] > 0)
                intent=lab.candidate(which)
                return k,lab,intent

            k,lab,candidate = setup("normal")
            yes("normal_local_native_git_cas_with_durable_sqlite_readback",
                lab.attempt(candidate) == "COMMITTED_READBACK"
                and lab.remote_sha() == candidate.candidate
                and lab.status(candidate.key)["state"] == "COMMITTED_READBACK")
            yes("normal_revoke_transitions_to_drain_not_release",
                cp081.revoke_admitted(fixture,k)
                and fixture.cli_range("root",k["generation"])["value"] ==
                    "DRAINING_ADMITTED"
                and fixture.cli_range("root",k["ref"])["value"] == "RESERVED")
            yes("already_granted_drain_refuses_any_new_local_effect",
                lab.attempt(lab.candidate("drain-next")) == "DENIED_STALE")

            k,lab,candidate = setup("revoke-before")
            before=lab.remote_sha()
            yes("revocation_committed_before_local_effect",
                cp081.revoke_admitted(fixture,k))
            yes("revoke_before_native_git_ref_fails_closed",
                lab.attempt(candidate) == "DENIED_STALE"
                and lab.remote_sha() == before)

            k,lab,candidate = setup("revoke-mid")
            native_git = lab.git
            call_count = [0]
            def native_then_revoke(*args,**kwargs):
                outcome=native_git(*args,**kwargs)
                if args and args[0] == "update-ref":
                    call_count[0] += 1
                    require(outcome.returncode == 0,"LOCAL_GIT_WRITE_FAILED")
                    require(cp081.revoke_admitted(fixture,k),
                            "REAL_REVOKE_BETWEEN_GIT_AND_READBACK")
                return outcome
            lab.git=native_then_revoke
            response=lab.attempt(candidate)
            yes("post_local_git_revoke_forces_unknown_not_safe_success",
                response == "UNKNOWN_EFFECT_RECONCILE" and
                lab.remote_sha() == candidate.candidate and
                lab.frozen() and call_count[0] == 1)
            yes("durable_recovery_classifies_remote_advanced_without_retry",
                lab.reconcile(candidate.key, process_terminated=True) ==
                    "REMOTE_ADVANCED_REVIEW_REQUIRED")
            yes("unknown_persists_and_blocks_second_request",
                lab.attempt(lab.candidate("other-mid")) == "NOT_ADMITTED" and
                lab.frozen())

            k,lab,candidate = setup("ack-after")
            yes("ack_lost_after_local_git_freezes_durable_journal",
                lab.attempt(candidate,fault="lost_ack_after_git") ==
                    "UNKNOWN_EFFECT_RECONCILE"
                and lab.remote_sha() == candidate.candidate and lab.frozen())
            yes("ack_after_reconciliation_requires_explicit_review",
                lab.reconcile(candidate.key,process_terminated=True) ==
                    "REMOTE_ADVANCED_REVIEW_REQUIRED")
            yes("ack_after_no_blind_retry",lab.attempt(candidate) ==
                "NOT_ADMITTED")
            restarted = offline.OfflineLab(lab.root)
            restarted.observe = lab.observe
            yes("ack_after_new_SQLite_reader_cannot_unfreeze",
                restarted.frozen() and
                restarted.attempt(restarted.candidate("next-after")) == "NOT_ADMITTED")

            k,lab,candidate = setup("ack-before")
            original = lab.remote_sha()
            yes("ack_lost_before_git_freezes_without_effect",
                lab.attempt(candidate,fault="lost_ack_before_git") ==
                    "UNKNOWN_EFFECT_RECONCILE" and
                lab.remote_sha() == original and lab.frozen())
            yes("ack_before_reconciliation_requires_explicit_review",
                lab.reconcile(candidate.key,process_terminated=True) ==
                    "REMOTE_UNCHANGED_REVIEW_REQUIRED")
            yes("ack_before_no_blind_retry",lab.attempt(candidate) ==
                "NOT_ADMITTED")
            restarted = offline.OfflineLab(lab.root)
            restarted.observe = lab.observe
            yes("ack_before_new_SQLite_reader_cannot_unfreeze",
                restarted.frozen() and
                restarted.attempt(restarted.candidate("next-before")) == "NOT_ADMITTED")
        finally:
            fixture.stop()
    return {
        "schema":SCHEMA,
        "status":"PASS_REAL_ETCD_TLS_RBAC_LOCAL_GIT_SQLITE_UNKNOWN_LAB_ONLY",
        "security_admission":"RED",
        "scenarios":checks,
        "scenario_count":len(checks),
        "disposable_prefix_sha256":hashlib.sha256(prefix.encode()).hexdigest(),
        "real_etcd_tls_rbac":True,"native_local_git_cas":True,
        "durable_sqlite_unknown_reconciliation":True,
        "mid_effect_revoke_reported_unknown":True,
        "remote_github_writes":0,"remote_github_credentials_used":False,
        "worker_generated_source_executed":False,
        "os_separate_sink_proven":False,
        "real_protected_core_issuer_proven":False,
        "cross_store_atomicity_proven":False,
        "production_authority":False,
    }

def main(args):
    if args == ["--selftest"]:
        print(json.dumps({"schema":SCHEMA,"status":"OFFLINE_STATIC_ONLY",
            "security_admission":"RED","provider_started":False,
            "remote_github_writes":0,"production_authority":False},
            sort_keys=True))
        return 0
    if len(args) != 3 or args[0] != "--provider-lab":
        raise cp081.Denied("EXPLICIT_MODE_REQUIRED")
    print(json.dumps(run(Path(args[1]),Path(args[2])),sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (cp081.Denied,ValueError,RuntimeError,OSError,KeyError) as e:
        print(json.dumps({"status":"FAIL_CLOSED","reason":type(e).__name__,
            "security_admission":"RED","remote_github_writes":0}))
        raise SystemExit(2)
