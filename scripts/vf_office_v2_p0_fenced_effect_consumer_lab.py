#!/usr/bin/env python3
"""#612 consumer-side lease/fencing contract: strictly synthetic, denial-only.

#604 alone owns the *real* authoritative fleet provider and lease minting.
This script NEVER grants a writer, dispatch, retry or process-kill permission.
It checks a fake atomic provider snapshot at the intended effect boundary;
a future real sink must enforce its own generation CAS atomically with writes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json

import vf_office_v2_p0_unknown_reconcile as rec
from vf_office_v2_p0_fresh_attempt_lineage import canonical_path

CLAIM_SCHEMA = "velvetos.office-v2.p0-synthetic-fence-claim.v0"
OBS_SCHEMA = "velvetos.office-v2.p0-synthetic-provider-observation.v0"
SOURCE = "SYNTHETIC_FAKE_PROVIDER_ONLY_NOT_CANONICAL"
STATUS = "CONSISTENT_SYNTHETIC_READBACK_NO_WRITE_AUTHORITY"
MAX_TTL_US = 15 * 60 * 1000000
CLAIM_KEYS = {"schema", "source", "envelope_sha256", "resource_key",
              "lease_id", "generation", "task_id", "attempt_id",
              "host", "worker_id", "base_sha", "branch", "worktree_path"}
OBS_KEYS = {"schema", "source", "revision", "provider_time_us", "lease"}
LEASE_KEYS = {"resource_key", "lease_id", "generation", "task_id",
              "attempt_id", "host", "worker_id", "base_sha", "branch",
              "worktree_path", "expires_at_provider_us", "state"}

class Refused(Exception):
    pass

def require(value, reason):
    if not value:
        raise Refused(reason)

def positive_int(value):
    return type(value) is int and value > 0

def text_id(value):
    return isinstance(value, str) and bool(value) and len(value) < 200 and "\x00" not in value

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

def inspect(envelope, claim, observation):
    """Read-only structural test. A passing result IS NOT a valid live owner lease."""
    rec.checked_envelope(envelope)
    require(isinstance(claim, dict) and set(claim) == CLAIM_KEYS and
            claim["schema"] == CLAIM_SCHEMA and claim["source"] == SOURCE,
            "CLAIM_SCHEMA_OR_AUTHORITY")
    require(isinstance(observation, dict) and set(observation) == OBS_KEYS and
            observation["schema"] == OBS_SCHEMA and observation["source"] == SOURCE,
            "PROVIDER_OBSERVATION_UNTRUSTED")
    require(claim["envelope_sha256"] == rec.digest(envelope),
            "CLAIM_NOT_BOUND_TO_TASK_ENVELOPE")
    for field in ("resource_key", "lease_id", "attempt_id", "worker_id"):
        require(text_id(claim[field]), "CLAIM_ID_INVALID_" + field.upper())
    require(claim["attempt_id"] == envelope["task_id"] + ":attempt-1",
            "ATTEMPT_ID_DRIFT")
    require(positive_int(claim["generation"]), "CLAIM_GENERATION_INVALID")
    for key in ("task_id", "host", "base_sha", "branch"):
        require(claim[key] == envelope[key], "CLAIM_ENVELOPE_MISMATCH_" + key.upper())
    require(canonical_path(claim["worktree_path"]) ==
            canonical_path(envelope["worktree_path"]),
            "CLAIM_WORKTREE_DRIFT")
    require(positive_int(observation["revision"]) and
            positive_int(observation["provider_time_us"]),
            "PROVIDER_CLOCK_OR_REVISION_MISSING")
    lease = observation["lease"]
    require(isinstance(lease, dict) and set(lease) == LEASE_KEYS,
            "NO_ATOMIC_SINGLE_LEASE_READ")
    require(lease["state"] == "ACTIVE", "LEASE_NOT_ACTIVE")
    require(positive_int(lease["generation"]) and
            positive_int(lease["expires_at_provider_us"]),
            "LEASE_CLOCK_OR_GENERATION_INVALID")
    ttl = lease["expires_at_provider_us"] - observation["provider_time_us"]
    require(0 < ttl <= MAX_TTL_US, "LEASE_EXPIRED_OR_UNBOUNDED_TTL")
    for key in sorted(CLAIM_KEYS & LEASE_KEYS):
        if key == "worktree_path":
            require(canonical_path(lease[key]) == canonical_path(claim[key]),
                    "LEASE_OWNER_MISMATCH_WORKTREE_PATH")
        else:
            require(lease[key] == claim[key], "LEASE_OWNER_MISMATCH_" + key.upper())
    return {
        "status": STATUS, "task_id": envelope["task_id"],
        "resource_key": claim["resource_key"],
        "observed_generation": claim["generation"],
        "observed_revision": observation["revision"],
        "provider_clock_only": True,
        "no_real_provider_integrated": True,
        "write_authorized": False, "worker_dispatch_authorized": False,
        "retry_authorized": False, "orphan_exclusion_proven": False,
        "effect_commit_atomicity_proven": False,
    }

def effect_boundary(envelope, claim, prior, latest):
    """Fake latest-read *comparison* only; does not commit any real effect."""
    inspect(envelope, claim, prior)
    require(isinstance(latest, dict), "PROVIDER_UNREACHABLE_OR_PARTITIONED")
    inspect(envelope, claim, latest)
    require(latest["revision"] == prior["revision"] and
            digest(latest) == digest(prior),
            "PROVIDER_MOVED_BETWEEN_READ_AND_EFFECT")
    return {"status":"SYNTHETIC_COMPARE_ONLY_NO_EFFECT_COMMITTED",
            "write_authorized":False, "effect_committed":False,
            "requeue_authorized":False, "needs_atomic_provider_side_cas":True}

def selftest():
    checks=[]
    def deny(name, code, env, claim, prior, latest):
        try:
            effect_boundary(env, claim, prior, latest)
        except (Refused, rec.Refused) as exc:
            if str(exc) != code:
                raise AssertionError(name + ": WRONG_REFUSAL " + str(exc) +
                                     ", expected " + code) from exc
            checks.append(name)
        else:
            raise AssertionError("UNSAFE_SYNTHETIC_FENCE_ACCEPTED:" + name)
    env={"schema":rec.SCHEMA, "authority":rec.AUTHORITY, "issue_url":rec.ISSUE,
         "task_id":"p0-fenced-synthetic-task001", "host":"Chris",
         "base_sha":"a"*40, "branch":"lab-p0-agent-fenced001",
         "worktree_path":"C:\\Velvet\\Lab\\Fenced001",
         "context_checkpoint":"C:\\Velvet\\Lab\\Fenced001\\checkpoint.json",
         "budget":{"max_attempts":1,"max_cost_usd":0},
         "executor":{"kind":rec.KIND,"model":"qwen3.5:9b","model_digest":"b"*64}}
    claim={"schema":CLAIM_SCHEMA,"source":SOURCE,
           "envelope_sha256":rec.digest(env), "resource_key":"lab://shared-git-mutation-slot",
           "lease_id":"synthetic-lease-41", "generation":41,
           "task_id":env["task_id"],"attempt_id":env["task_id"]+":attempt-1",
           "host":env["host"],"worker_id":"win-worker-1",
           "base_sha":env["base_sha"],"branch":env["branch"],
           "worktree_path":env["worktree_path"]}
    lease={key:copy.deepcopy(claim[key]) for key in CLAIM_KEYS & LEASE_KEYS}
    lease.update({"state":"ACTIVE","expires_at_provider_us":300_000_000})
    observation={"schema":OBS_SCHEMA,"source":SOURCE,"revision":11,
                 "provider_time_us":200_000_000,"lease":lease}
    result=effect_boundary(env,claim,observation,copy.deepcopy(observation))
    require(result["effect_committed"] is False and
            result["needs_atomic_provider_side_cas"] is True,"FALSE_GREEN")
    checks.append("exact_owner_observed_but_no_write_authority")
    # Enforce a real provider-clock-based TTL rather than the customer's clock.
    shifted=copy.deepcopy(observation)
    shifted["provider_time_us"]=299_000_000
    require(inspect(env,claim,shifted)["write_authorized"] is False, "CLOCK_POSITIVE_FALSE_GREEN")
    checks.append("provider_clock_drives_expiry_not_local_wall_clock")
    for key in ("task_id","attempt_id","host","worker_id","base_sha",
                "branch","worktree_path","resource_key","lease_id","generation"):
        altered=copy.deepcopy(observation)
        altered["lease"][key]=(43 if key=="generation" else
                             "C:\\Velvet\\Lab\\FOREIGN" if key=="worktree_path" else
                             "foreign-" + key)
        deny("reject_foreign_"+key,"LEASE_OWNER_MISMATCH_"+key.upper(),
             env,claim,observation,altered)
    for key in ("task_id","attempt_id","host","worker_id","base_sha",
                "branch","worktree_path","resource_key","lease_id","generation"):
        altered=copy.deepcopy(claim)
        altered[key]=(43 if key=="generation" else
                      "C:\\Velvet\\Lab\\FOREIGN" if key=="worktree_path" else
                      "foreign-" + key)
        # Classify changed owner fields on the first independent inspection.
        if key=="task_id":
            code="CLAIM_ENVELOPE_MISMATCH_TASK_ID"
        elif key=="attempt_id":
            code="ATTEMPT_ID_DRIFT"
        elif key in ("host","base_sha","branch"):
            code="CLAIM_ENVELOPE_MISMATCH_"+key.upper()
        elif key=="worktree_path":
            code="CLAIM_WORKTREE_DRIFT"
        else:
            code="LEASE_OWNER_MISMATCH_"+key.upper()
        deny("reject_claim_"+key,code,env,altered,observation,observation)
    for name, key, value, code in (
       ("deny_expired","provider_time_us",300_000_000,"LEASE_EXPIRED_OR_UNBOUNDED_TTL"),
       ("deny_clock_snapshot_drift","provider_time_us",1,"PROVIDER_MOVED_BETWEEN_READ_AND_EFFECT"),
       ("deny_missing_provider_time","provider_time_us",None,"PROVIDER_CLOCK_OR_REVISION_MISSING"),
       ("deny_bool_provider_time","provider_time_us",True,"PROVIDER_CLOCK_OR_REVISION_MISSING"),
       ("deny_missing_revision","revision",None,"PROVIDER_CLOCK_OR_REVISION_MISSING"),
       ("deny_bool_revision","revision",True,"PROVIDER_CLOCK_OR_REVISION_MISSING"),
       ("deny_replayed_revision","revision",10,"PROVIDER_MOVED_BETWEEN_READ_AND_EFFECT"),
       ("deny_changed_revision","revision",12,"PROVIDER_MOVED_BETWEEN_READ_AND_EFFECT"),
       ("deny_source_spoof","source","USER_SUPPLIED","PROVIDER_OBSERVATION_UNTRUSTED"),
    ):
        altered=copy.deepcopy(observation);altered[key]=value
        deny(name,code,env,claim,observation,altered)
    for name,key,value,code in (
       ("deny_revocation","state","REVOKED","LEASE_NOT_ACTIVE"),
       ("deny_lease_expiry","expires_at_provider_us",200_000_000,"LEASE_EXPIRED_OR_UNBOUNDED_TTL"),
       ("deny_bool_generation","generation",True,"LEASE_CLOCK_OR_GENERATION_INVALID"),
       ("deny_zero_generation","generation",0,"LEASE_CLOCK_OR_GENERATION_INVALID"),
       ("deny_unbounded_expiry","expires_at_provider_us",2_000_000_000,"LEASE_EXPIRED_OR_UNBOUNDED_TTL"),
    ):
        altered=copy.deepcopy(observation);altered["lease"][key]=value
        deny(name,code,env,claim,observation,altered)
    for name,key,value,code in (
       ("deny_bool_claim_generation","generation",True,"CLAIM_GENERATION_INVALID"),
       ("deny_zero_claim_generation","generation",0,"CLAIM_GENERATION_INVALID"),
       ("deny_missing_worker","worker_id",None,"CLAIM_ID_INVALID_WORKER_ID"),
       ("deny_paid_worker","source","PRODUCTION","CLAIM_SCHEMA_OR_AUTHORITY"),
       ("deny_wrong_digest","envelope_sha256","0"*64,"CLAIM_NOT_BOUND_TO_TASK_ENVELOPE"),
    ):
        altered=copy.deepcopy(claim);altered[key]=value
        deny(name,code,env,altered,observation,observation)
    deny("deny_partition","PROVIDER_UNREACHABLE_OR_PARTITIONED",
         env,claim,observation,None)
    for name, field, value, code in (
       ("deny_split_brain_multi_lease","leases",[lease,lease],"PROVIDER_OBSERVATION_UNTRUSTED"),
       ("deny_surprise_write_authorization","write_authorized",True,"PROVIDER_OBSERVATION_UNTRUSTED"),
    ):
        altered=copy.deepcopy(observation);altered[field]=value
        deny(name,code,env,claim,observation,altered)
    # Even a formerly valid observation loses at effect-time if #604 rotates
    # the same shared resource's fence to an independently owned Mac worker.
    successor=copy.deepcopy(observation)
    successor["revision"]=12
    successor["lease"].update(generation=42,host="MacMiniOffice.local",
                              worker_id="mac-worker-2",lease_id="synthetic-lease-42")
    deny("old_windows_owner_loses_after_mac_claim",
         "LEASE_OWNER_MISMATCH_GENERATION",env,claim,observation,successor)
    # The new owner can only get structural consistency; it still cannot write.
    mac_env=copy.deepcopy(env)
    mac_env.update(task_id="p0-fenced-synthetic-mac002",
                   host="MacMiniOffice.local",base_sha="c"*40,
                   branch="lab-p0-agent-fenced002",
                   worktree_path="/Users/chris/Velvet/Lab/Fenced002",
                   context_checkpoint="/Users/chris/Velvet/Lab/Fenced002/checkpoint.json")
    mac_claim=copy.deepcopy(claim)
    mac_claim.update(task_id=mac_env["task_id"],
                     attempt_id=mac_env["task_id"]+":attempt-1",host=mac_env["host"],
                     worker_id="mac-worker-2",base_sha=mac_env["base_sha"],
                     branch=mac_env["branch"],worktree_path=mac_env["worktree_path"],
                     envelope_sha256=rec.digest(mac_env),
                     lease_id="synthetic-lease-42",generation=42)
    successor["lease"]={key:copy.deepcopy(mac_claim[key]) for key in
                        CLAIM_KEYS & LEASE_KEYS}
    successor["lease"].update(state="ACTIVE",expires_at_provider_us=300_000_000)
    require(effect_boundary(mac_env,mac_claim,successor,copy.deepcopy(successor))[
        "write_authorized"] is False, "MAC_OWNER_FALSE_WRITE_AUTHORITY")
    checks.append("new_mac_owner_still_requires_atomic_real_provider_commit")
    denied_env=copy.deepcopy(env)
    denied_env["budget"]["max_attempts"]=2
    deny("deny_second_attempt","RETRY_OR_PAID_BUDGET_DENIED",
         denied_env,claim,observation,observation)
    require(len(checks)==47, "WRONG_NEGATIVE_CASE_COUNT:" + str(len(checks)))
    return {"status":"PASS_OFFLINE", "tests":len(checks), "cases":checks,
            "synthetic_provider_only":True, "real_lease_issued":False,
            "model_invocations":0, "dispatches":0, "production_effects":0,
            "retries":0, "writes_authorized":0, "effects_committed":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("selftest",))
    a=p.parse_args()
    print(json.dumps(selftest(),sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
