#!/usr/bin/env python3
"""#612 read-only LAB audit for a *set* of separately issued fresh attempts.

This is a denial-only second fence. It does not dispatch jobs, own #604 leases,
certify absent processes, retry unknown work, or authorize production effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import vf_office_v2_p0_fresh_attempt_lineage as lineage

SCHEMA = "velvetos.office-v2.p0-batch-distinct-attempt-readback.v1"

class Refused(Exception):
    pass

def require(value, reason):
    if not value:
        raise Refused(reason)

def identity_tuple(env):
    return (env["task_id"], env["base_sha"], env["branch"],
            lineage.canonical_path(env["context_checkpoint"]),
            lineage.canonical_path(env["worktree_path"]))

def audit(old_envelope, old_receipt, fresh):
    """Observe only already-existing evidence, never create or enqueue attempts."""
    require(isinstance(fresh, list) and 2 <= len(fresh) <= 16, "BATCH_BOUNDS")
    paths = [Path(old_envelope).absolute(), Path(old_receipt).absolute()]
    for pair in fresh:
        require(isinstance(pair, (list, tuple)) and len(pair) == 2, "PAIR_REQUIRED")
        paths.extend(Path(p).absolute() for p in pair)
    require(len(set(map(str, paths))) == len(paths), "DUPLICATE_EVIDENCE_PATH")
    observed = []
    all_identities = []
    fingerprints_before = {}
    for p in paths:
        require(not p.is_symlink(), "SYMLINK_DENIED")
        if p.is_file():
            fingerprints_before[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            fingerprints_before[str(p)] = None
    old = lineage.reconciliation.checked_envelope(
        lineage.reconciliation.read_optional(paths[0]))
    all_identities.append(identity_tuple(old))
    for i, pair in enumerate(fresh):
        eo, ro = pair
        # Reuse canonical single-pair checker for UNKNOWN, no-retry, LAB authority,
        # negative journaling, integrity and 5 independent identity dimensions.
        verdict = lineage.inspect(old_envelope, old_receipt, eo, ro)
        require(verdict.get("status") ==
                "DISTINCT_MANUAL_ATTEMPT_LINEAGE_ONLY_NOT_ADMISSION" and
                verdict.get("new_task_execution_authorized") is False and
                verdict.get("original_unknown_retry_authorized") is False,
                "PAIR_READBACK_FAILED")
        new = lineage.reconciliation.checked_envelope(
            lineage.reconciliation.read_optional(Path(eo)))
        all_identities.append(identity_tuple(new))
        observed.append({"index":i, "task_id":new["task_id"]})
    # Every dimension MUST be unique among all N+1 attempts, not merely
    # different from the original UNKNOWN.
    for dimension in range(5):
        require(len({item[dimension] for item in all_identities}) ==
                len(all_identities), "FRESH_ATTEMPTS_COLLIDE_DIMENSION_" + str(dimension))
    for p in paths:
        current = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        require(current == fingerprints_before[str(p)], "EVIDENCE_CHANGED_DURING_AUDIT")
    return {"schema":SCHEMA, "status":"PASS_READ_ONLY_BATCH_DISTINCT",
            "fresh_count":len(fresh), "task_ids":[r["task_id"] for r in observed],
            "retry_permitted":False, "all_orphans_excluded":False,
            "scheduler_authority":False, "production_effects":0}

def selftest():
    import copy
    rec = lineage.reconciliation
    checks = []
    with tempfile.TemporaryDirectory(prefix="p0-batch-readonly-") as temp:
        root = Path(temp)
        dirs = [root / label for label in ("old", "fresh1", "fresh2")]
        for directory in dirs:
            directory.mkdir()
        def envelope(i):
            return {"schema": rec.SCHEMA, "authority": rec.AUTHORITY,
                    "issue_url": rec.ISSUE, "task_id": "batch-task-" + str(i),
                    "host": "synthetic-host", "base_sha": hex(i+10)[2:]*40 if i<6 else "a"*40,
                    "branch": "lab-p0-agent-batch-" + str(i),
                    "worktree_path": str(dirs[i] / "worktree"),
                    "context_checkpoint": str(dirs[i] / "checkpoint.json"),
                    "budget": {"max_attempts":1, "max_cost_usd":0},
                    "executor": {"kind":rec.KIND, "model":"qwen3.5:9b",
                                 "model_digest":"b"*64}}
        original = [envelope(i) for i in range(3)]
        def write(index, envs):
            (dirs[index] / "envelope.json").write_text(
                json.dumps(envs[index],sort_keys=True),encoding="utf-8")
        def run(envs):
            for i in range(3):
                write(i, envs)
            journal = {"state":"RUNNING", "task_id":envs[0]["task_id"],
                       "host":envs[0]["host"], "kind":rec.KIND,
                       "envelope_sha256":rec.digest(envs[0]),
                       "started_at":"2026-10-09T18:00:00Z",
                       "unknown_outcome_rule":"NO_BLIND_RETRY"}
            (dirs[0]/"receipt.json.running").write_text(
                json.dumps(journal,sort_keys=True),encoding="utf-8")
            return audit(dirs[0]/"envelope.json",dirs[0]/"receipt.json",
                         [(d/"envelope.json",d/"receipt.json") for d in dirs[1:]])
        valid=run(copy.deepcopy(original))
        assert valid["status"]=="PASS_READ_ONLY_BATCH_DISTINCT"
        assert valid["fresh_count"]==2 and valid["retry_permitted"] is False
        checks.append("two_fresh_attempts_all_distinct")
        fields=("task_id","base_sha","branch","context_checkpoint","worktree_path")
        for idx, field in enumerate(fields):
            for from_idx in (0,1):
                envs=copy.deepcopy(original)
                envs[2][field]=envs[from_idx][field]
                try:
                    run(envs)
                except (Refused,rec.Refused):
                    checks.append("deny_collision_"+field+"_with_"+str(from_idx))
                else:
                    raise AssertionError("BATCH_COLLISION_ADMITTED_"+field)
        # One malformed attempt invalidates the complete readback.
        for field,value in (("authority","PRODUCTION"),
                            ("budget",{"max_attempts":2,"max_cost_usd":0}),
                            ("executor",{"kind":"CODEX_CLI"})):
            envs=copy.deepcopy(original);envs[2][field]=value
            try:
                run(envs)
            except (Refused,rec.Refused):
                checks.append("deny_unsafe_"+field)
            else:
                raise AssertionError("UNSAFE_BATCH_ADMITTED_"+field)
        assert run(copy.deepcopy(original))["production_effects"]==0
        checks.append("valid_batch_after_denials")
    assert len(checks)==15,checks
    return {"status":"PASS_OFFLINE","tests":len(checks),"cases":checks,
            "model_invocations":0,"dispatches":0,"retries":0,"production_effects":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--old-envelope")
    p.add_argument("--old-receipt")
    p.add_argument("--fresh", nargs="*", help="Pairs of envelope.json receipt.json")
    a=p.parse_args()
    try:
        if a.selftest:
            out=selftest()
        else:
            require(a.old_envelope and a.old_receipt and a.fresh and
                    len(a.fresh)%2==0, "ARGUMENTS_REQUIRED")
            out=audit(a.old_envelope,a.old_receipt,
                      [a.fresh[i:i+2] for i in range(0,len(a.fresh),2)])
        print(json.dumps(out,sort_keys=True))
        return 0
    except (Refused,lineage.reconciliation.Refused) as exc:
        print(json.dumps({"status":"REFUSED", "reason":str(exc)},sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
