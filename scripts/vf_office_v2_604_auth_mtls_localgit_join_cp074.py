#!/usr/bin/env python3
"""#604 CP074: independently authenticated etcd lease + local Git effect, LAB.

Real loopback etcd 3.6.15 with client-cert identities and RBAC + real
lease/txn/restart, then git update-ref compare-and-swap in a newly created
NO-REMOTE bare repository. Fixed synthetic task only; NO GitHub write token,
no model code, no signed Core lease, no safe effect-time cross-store fence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity
import vf_office_v2_604_etcd_pending_intent_native_localgit_lab as gitlab

SCHEMA = "velvetos.office-v2.604.cp074-authenticated-lease-localgit.v1"
TASK = "vf604-cp074-fixed-public-synthetic-task"
HOST = "MacMiniOffice.local"
WORKER = "worker-a"
SOURCE = hashlib.sha256(b"FIXED_CP074_PUBLIC_SOURCE_ONLY").hexdigest()
PREFIX = "/vf604/cp074/loopback-only/"
PENDING = "EFFECT_IN_FLIGHT_DO_NOT_REPLAY"
COMMITTED = "COMMITTED_LOCAL_ONLY:"
EXPECTED = {
    "schema": SCHEMA, "task_id": TASK, "host": HOST, "worker": WORKER,
    "effect": "LOCAL_BARE_GIT_REF_ONLY", "source_sha256": SOURCE,
    "lease_epoch": 7, "retry": False, "github_write": False,
    "production_authority": False,
}
LIVE_NAMES = (
    "pinned_binary_hashes_checked",
    "loopback_tls_server_started",
    "real_certificate_cn_rbac_enabled",
    "worker_cannot_write_owner",
    "worker_cannot_read_intent",
    "out_of_scope_sink_write_denied",
    "lease_backed_owner_key_verified",
    "owner_bound_exact_claim_checked",
    "modrev_plus_missing_intent_atomic_txn",
    "unleased_durable_pending_intent_verified",
    "ref_effect_local_cas_success",
    "provider_owner_still_current_at_ack",
    "committed_ack_transaction_exact_modrevs",
    "duplicate_effect_denied",
    "wrong_epoch_denied",
    "expired_lease_key_disappeared",
    "inflight_pending_survives_owner_expiry",
    "expired_epoch_write_blocked",
    "provider_crash_restart_pending_survived",
    "next_owner_blocked_until_reconciliation",
    "old_writer_never_changed_local_ref",
    "no_git_remote_or_credential_or_generated_code",
)


class Refuse(Exception):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise Refuse(message)


def claim_exact(row: dict) -> None:
    need(type(row) is dict and set(row) == set(EXPECTED),
         "UNEXPECTED_TASK_CLAIM_FIELDS")
    for key, expected in EXPECTED.items():
        need(type(row[key]) is type(expected) and row[key] == expected,
             "UNEXPECTED_TASK_CLAIM_" + key)


def gate(owner: dict | None, expected_owner: str,
         expected_revision: int, pending: dict | None = None) -> None:
    need(type(owner) is dict
         and owner.get("value") == expected_owner
         and type(owner.get("mod_revision")) is int
         and owner["mod_revision"] == expected_revision
         and type(owner.get("lease")) is int and owner["lease"] > 0,
         "NOT_CURRENT_REAL_PROVIDER_LEASE_EPOCH")
    if pending is not None:
        need(type(pending) is dict and pending.get("value") == PENDING
             and pending.get("lease") == 0,
             "NO_DURABLE_EXACT_EFFECT_INTENT")


def selftest() -> dict:
    claim_exact(copy.deepcopy(EXPECTED))
    negative = []
    for key,value in EXPECTED.items():
        altered=copy.deepcopy(EXPECTED)
        altered[key] = (not value if type(value) is bool
                        else value + 1 if type(value) is int
                        else value + "_wrong")
        negative.append((key,altered))
    negative.extend([
        ("unknown_field",dict(EXPECTED, token="should_never_accept")),
        ("missing_worker",{k:v for k,v in EXPECTED.items() if k!="worker"}),
        ("bool_epoch",dict(EXPECTED, lease_epoch=True)),
        ("github_grant",dict(EXPECTED, github_write=True)),
        ("prod_grant",dict(EXPECTED, production_authority=True)),
    ])
    for name, row in negative:
        try:claim_exact(row)
        except Refuse:pass
        else:raise Refuse("FALSE_CLAIM_ADMITTED_"+name)
    owner={"mod_revision":13,"value":"task-x-epoch7","lease":100}
    pending={"value":PENDING,"lease":0,"mod_revision":14}
    gate(owner, "task-x-epoch7", 13, pending)
    invalid=[
        (None, "absent_owner"),
        (dict(owner, value="wrong-host"),"wrong_host"),
        (dict(owner, mod_revision=14),"stale_generation"),
        (dict(owner, lease=0),"detached_owner"),
        (dict(owner, lease=True),"bool_lease"),
        (dict(owner, mod_revision=True),"bool_revision"),
    ]
    for changed, name in invalid:
        try:gate(changed,"task-x-epoch7",13,pending)
        except Refuse:pass
        else:raise Refuse("FALSE_EXPIRED_OR_WRONG_OWNER_"+name)
    for changed,name in (
        (dict(pending,value=COMMITTED+"123"),"completed_not_inflight"),
        (dict(pending,lease=100),"not_durable"),
        (None,"no_intent"),
    ):
        try:gate(owner,"task-x-epoch7",13,changed if changed is not None else {"value":"NONE","lease":0})
        except Refuse:pass
        else:raise Refuse("FALSE_INTENT_"+name)
    need(len(negative)==15 and len(invalid)==6,"STATIC_TEST_COUNT_DRIFT")
    return {"schema":SCHEMA,"status":"PASS_CP074_STATIC_NO_PROVIDER_NO_GIT",
            "claim_mutations_denied":len(negative),
            "owner_and_intent_mutations_denied":len(invalid)+3,
            "native_expected_checks":len(LIVE_NAMES),
            "signed_core_provider":False,"model_source_executed":False,
            "github_credentials":False,"remote_git_writes":0,
            "live_provider_started":False,"production_authority":False}


def path_owner(root: str) -> Path:
    raw=Path(root)
    need(raw.is_absolute() and not raw.is_symlink(),
         "ROOT_MUST_BE_LITERAL_ABSOLUTE_NOT_SYMLINK")
    p=raw.resolve()
    need(p==raw and p.is_dir() and not p.is_symlink()
         and p.name=="p0-604-auth-mtls-localgit-cp074-20261015"
         and p.parent.name=="AgentEnvelopeLab"
         and p.stat().st_mode & 0o077 == 0,
         "ROOT_MUST_BE_NEW_EXCLUSIVE_0700_AGENTENVELOPE_LAB")
    need(not any(p.iterdir()), "OWNED_ROOT_NOT_EMPTY")
    return p


def test_native(etcd_binary: str, ctl_binary: str, root: str) -> dict:
    home=path_owner(root)
    need(not any(os.environ.get(key) for key in (
         "GITHUB_TOKEN","GH_TOKEN","GIT_ASKPASS","SSH_ASKPASS")),
         "CREDENTIAL_FREE_PROCESS_REQUIRED_BEFORE_LOCAL_LAB")
    etcd=identity.pinned_executable(etcd_binary,identity.PINNED_ETCD)
    ctl=identity.pinned_executable(ctl_binary,identity.PINNED_CTL)
    # Never attach to historical lab/service data dirs, not even to read them.
    tests=[]
    def proof(name:str,ok:bool)->None:
        need(name==LIVE_NAMES[len(tests)] and ok is True,
             "ACTUAL_NATIVE_PROOF_FAILED_"+name)
        tests.append(name)
        print("CP074_REAL_CHECK_"+name,flush=True)
    proof("pinned_binary_hashes_checked",True)
    with tempfile.TemporaryDirectory(prefix="vf604-cp074-auth-git-",dir=home) as temp:
        area=Path(temp)
        area.chmod(0o700)
        provider_dir=area/"provider"
        provider_dir.mkdir(mode=0o700)
        service=identity.AuthenticatedEtcd(provider_dir,etcd,ctl)
        repository=gitlab.LocalGit.initialize(area/"bare-git")
        need(repository.verified(),"GIT_MUST_HAVE_NO_REMOTE")
        initial=repository.head()
        expected_owner=TASK+"|"+HOST+"|"+WORKER+"|"+SOURCE+"|epoch7"
        prefix=PREFIX+uuid.uuid4().hex+"/"
        owner=prefix+"owner"
        intent=prefix+"intent"
        oldowner=prefix+"expired/owner"
        oldintent=prefix+"expired/intent"
        ref_after=None
        try:
            service.start()
            proof("loopback_tls_server_started",service.url.startswith("https://127.0.0.1:"))
            identity.setup_rbac(service,prefix,owner)
            proof("real_certificate_cn_rbac_enabled",
                  bool(service.ctl_ok("root","auth","status")))
            identity.assert_cli_denied(service,"worker","put",owner,"forged")
            proof("worker_cannot_write_owner",True)
            identity.assert_cli_denied(service,"worker","get",intent)
            proof("worker_cannot_read_intent",True)
            identity.assert_cli_denied(service,"sink","put",
                 "/vf604/cp074/foreign","forged")
            proof("out_of_scope_sink_write_denied",True)
            claim_exact(EXPECTED)
            lease=int(json.loads(service.ctl_ok("sink","lease","grant","24"))["ID"])
            need(lease>0,"REAL_LEASE_NOT_ISSUED")
            service.ctl_ok("sink","put",owner,expected_owner,
                           "--lease="+format(lease,"x"))
            actual=service.cli_range("sink",owner)
            proof("lease_backed_owner_key_verified",
                  actual is not None and actual["lease"]==lease)
            rev=actual["mod_revision"]
            gate(actual,expected_owner,rev)
            proof("owner_bound_exact_claim_checked",True)
            started=service.cli_txn("sink",[
                f'mod("{owner}") = "{rev}"',
                f'version("{intent}") = "0"'
            ],[f'put "{intent}" "{PENDING}"'])
            proof("modrev_plus_missing_intent_atomic_txn",started is True)
            pending=service.cli_range("sink",intent)
            gate(service.cli_range("sink",owner),expected_owner,rev,pending)
            proof("unleased_durable_pending_intent_verified",
                  pending["lease"]==0 and pending["value"]==PENDING)
            candidate=repository.candidate(initial,"cp074synthetic","worker-a",7)
            # This is a native Git compare-and-swap, NEVER a GitHub push.
            # The last provider read precedes the Git update by a short
            # non-atomic interval: not a certified effect-time fence.
            gate(service.cli_range("sink",owner),expected_owner,rev,
                 service.cli_range("sink",intent))
            need(repository.head()==initial,"GIT_BASE_CHANGED")
            committed=repository.cas(initial,candidate)
            proof("ref_effect_local_cas_success",
                  committed is True and repository.head()==candidate)
            ref_after=repository.head()
            current=service.cli_range("sink",owner)
            proof("provider_owner_still_current_at_ack",
                  current is not None and current["mod_revision"]==rev
                  and current["value"]==expected_owner
                  and current["lease"]==lease)
            acked=service.cli_txn("sink",[
                f'mod("{owner}") = "{rev}"',
                f'mod("{intent}") = "{pending["mod_revision"]}"'
            ],[f'put "{intent}" "{COMMITTED+candidate}"'])
            proof("committed_ack_transaction_exact_modrevs",
                  acked is True
                  and service.cli_range("sink",intent)["value"]==COMMITTED+candidate)
            duplicate=service.cli_txn("sink",[
                f'mod("{owner}") = "{rev}"',
                f'version("{intent}") = "0"'
            ],[f'put "{intent}" "{PENDING}"'])
            proof("duplicate_effect_denied",
                  duplicate is False and repository.head()==candidate)
            try:gate(current,expected_owner.replace("epoch7","epoch8"),rev)
            except Refuse:wrong_epoch=True
            else:wrong_epoch=False
            proof("wrong_epoch_denied",wrong_epoch)
            # Now deliberately expire a SEPARATE historical owner AFTER a
            # durable intent; no Git operation is attempted after expiry.
            exp_lease=int(json.loads(service.ctl_ok("sink","lease","grant","4"))["ID"])
            oldval=TASK+"|"+HOST+"|"+WORKER+"|"+SOURCE+"|epoch6"
            service.ctl_ok("sink","put",oldowner,oldval,
                           "--lease="+format(exp_lease,"x"))
            older=service.cli_range("sink",oldowner)
            need(older is not None and older["lease"]==exp_lease,
                 "EXPIRED_FIXTURE_LEASE_MISSING")
            pend_start=service.cli_txn("sink",[
                f'mod("{oldowner}") = "{older["mod_revision"]}"',
                f'version("{oldintent}") = "0"'
            ],[f'put "{oldintent}" "{PENDING}"'])
            need(pend_start,"EXPIRED_FIXTURE_PENDING_NOT_STORED")
            until=time.monotonic()+12
            while service.cli_range("sink",oldowner) is not None and time.monotonic()<until:
                time.sleep(0.15)
            proof("expired_lease_key_disappeared",
                  service.cli_range("sink",oldowner) is None)
            frozen=service.cli_range("sink",oldintent)
            proof("inflight_pending_survives_owner_expiry",
                  frozen is not None and frozen["value"]==PENDING
                  and frozen["lease"]==0)
            try:gate(service.cli_range("sink",oldowner),oldval,older["mod_revision"],frozen)
            except Refuse:blocked=True
            else:blocked=False
            proof("expired_epoch_write_blocked",blocked and repository.head()==ref_after)
            service.crash_restart()
            again=service.cli_range("sink",oldintent)
            proof("provider_crash_restart_pending_survived",
                  again==frozen and service.cli_range("sink",oldowner) is None)
            new_owner_without_reconciliation=service.cli_txn("sink",[
                f'version("{oldowner}") = "0"',
                f'version("{oldintent}") = "0"'
            ],[f'put "{oldowner}" "newer-epoch8"'])
            proof("next_owner_blocked_until_reconciliation",
                  new_owner_without_reconciliation is False)
            proof("old_writer_never_changed_local_ref",
                  repository.head()==ref_after)
            proof("no_git_remote_or_credential_or_generated_code",
                  repository.verified()
                  and os.environ.get("GITHUB_TOKEN") is None
                  and os.environ.get("GH_TOKEN") is None)
            need(len(tests)==len(LIVE_NAMES),"INCOMPLETE_REAL_NATIVE_CHECKS")
            return {"schema":SCHEMA,"status":"PASS_ACTUAL_MTLS_LEASE_LOCAL_GIT_JOIN_FIXED_ONLY",
                    "live_checks":len(tests),"live_passes":len(tests),
                    "certificate_CN_RBAC_real":True,
                    "provider_live_lease_real":True,
                    "etcd_SIGKILL_crash_restart_WAL_real":True,
                    "native_local_git_CAS_real":True,
                    "stale_old_writer_effect_denied_in_lab":True,
                    "provider_identity_dedicated_OS_principal":False,
                    "provider_issuer_is_canonical_core604":False,
                    "cross_store_effect_time_atomicity_proven":False,
                    "github_git_writer_authorized":False,
                    "model_authored_source_executed":False,
                    "production_authority":False,"paid_model_calls":0,
                    "main_repo_changed":False,"new_scheduler":False,
                    "remote_git_writes":0,
                    "host":HOST,"provider":"ephemeral-loopback-etcd-mtls-rbac",
                    "git":"no-remote-temporary-bare-cas",
                    "first_local_head":initial,
                    "committed_local_head":ref_after}
        finally:
            service.stop()


def main(argv: list[str]) -> dict:
    need(len(argv)>=2,"MODE_REQUIRED")
    if argv[1]=="selftest" and len(argv)==2:
        return selftest()
    if argv[1]=="integration" and len(argv)==5:
        return test_native(argv[2],argv[3],argv[4])
    raise Refuse("UNAUTHORIZED_MODE_OR_UNBOUNDED_LAB_ARGUMENTS")


if __name__=="__main__":
    try:
        print(json.dumps(main(sys.argv),sort_keys=True),flush=True)
    except (Refuse,ValueError,RuntimeError,OSError,subprocess.SubprocessError,
            KeyError,TypeError,AssertionError) as exc:
        # Never report the private CA/client key material to output.
        print(json.dumps({"status":"FAIL_CLOSED",
                          "reason":type(exc).__name__+":"+str(exc)[:120],
                          "production_authority":False,
                          "remote_git_writes":0},sort_keys=True))
        raise SystemExit(2)
