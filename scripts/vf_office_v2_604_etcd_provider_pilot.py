#!/usr/bin/env python3
"""#604 actual temporary two-PHYSICAL-host etcd v3.6.15 LAB ONLY.

Uses etcd provider-side MVCC Txn and TTL leases to prove fencing of an
ETCD-STORED SYNTHETIC effect. It is NOT a scheduler, protected Git writer,
generic external filesystem/Git receiver, production auth, or safe sandbox.
No live command is permitted by the CI contract; selftest alone is offline.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import sys
import time
import urllib.error
import urllib.request

GIT_BASE = "3689168e48f85bd1008421d69f7484a800073adf"
PREFIX = "/velvet-office2/lab604/etcd-revision-20261010"
ENDPOINT = "http://192.168.0.217:32379"
DISCONNECTED = "http://192.168.0.217:32378"
SCENARIOS = ("race", "expiry", "renew", "outage")
HOSTS = ("win", "mac")


class Refuse(Exception):
    pass


def require(ok, cause):
    if not ok:
        raise Refuse(cause)


def b64(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return base64.b64encode(value).decode("ascii")


def request(endpoint, path, obj, timeout=3):
    require(endpoint in (ENDPOINT, DISCONNECTED), "ENDPOINT_NOT_ALLOWLISTED")
    require(path in ("/v3/lease/grant", "/v3/lease/revoke",
                     "/v3/lease/keepalive", "/v3/kv/range", "/v3/kv/txn"),
            "ETCD_METHOD_NOT_ALLOWLISTED")
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    req = urllib.request.Request(
        endpoint + path, data=payload, headers={"Content-Type":"application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as resp:
            if path == "/v3/lease/keepalive":
                raw = resp.readline(16384)
            else:
                raw = resp.read(16384)
            require(resp.status == 200 and len(raw) < 16384, "PROVIDER_HTTP_NOT_SUCCESS")
            out = json.loads(raw)
            require(isinstance(out, dict), "PROVIDER_JSON_NOT_OBJECT")
            return out
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError) as err:
        raise Refuse("PROVIDER_UNAVAILABLE_OR_UNVERIFIED_" + type(err).__name__)


def key(scenario, suffix):
    require(scenario in SCENARIOS and suffix in ("lease", "effect"),
            "OUT_OF_SCOPE_ETCD_KEY")
    return b64(PREFIX + "/" + scenario + "/" + suffix)


def getkv(endpoint, scenario, suffix):
    v = request(endpoint, "/v3/kv/range", {"key": key(scenario, suffix)})
    require("header" in v and "revision" in v["header"],
            "UNVERIFIED_PROVIDER_OBSERVATION")
    rows = v.get("kvs", [])
    require(isinstance(rows, list) and len(rows) <= 1,
            "PROVIDER_AMBIGUOUS_KEY")
    if not rows:
        return None, int(v["header"]["revision"])
    item = rows[0]
    require(item.get("key") == key(scenario, suffix)
            and type(item.get("mod_revision")) is str,
            "PROVIDER_KEY_IDENTITY_MISMATCH")
    return item, int(v["header"]["revision"])


def state_path(args):
    path = Path(args.state)
    require(path.name == "state-" + args.host + "-" + args.scenario + ".json",
            "STATE_FILENAME_NOT_ALLOWLISTED")
    require("p0-etcd604-provider-lab-20261010" in path.parts,
            "STATE_PARENT_NOT_LAB")
    require(path.parent.is_dir() and not path.parent.is_symlink(),
            "STATE_DIR_UNAVAILABLE")
    require(not path.is_symlink(), "STATE_SYMLINK")
    return path


def read_state(args):
    path = state_path(args)
    require(path.is_file() and path.stat().st_size < 4096,
            "OWNED_STATE_MISSING")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(type(data) is dict and data.get("schema") == "office604.etcd.lab.claim.v1"
            and data.get("host") == args.host
            and data.get("scenario") == args.scenario
            and data.get("git_base") == GIT_BASE
            and data.get("task") == "VF604_SYNTHETIC_ETCD_FENCED_JOB"
            and type(data.get("generation")) is int
            and data["generation"] > 0
            and type(data.get("lease_id")) is int
            and data["lease_id"] > 0
            and type(data.get("owner")) is str,
            "CLAIM_FIELDS_NOT_EXACT")
    return data


def claim(args):
    outfile = state_path(args)
    require(not outfile.exists(), "OWNED_STATE_ALREADY_EXISTS")
    owner = {
        "scope": "NON_PRODUCTION_ETCD_LOCAL_KV_EFFECT_ONLY",
        "task": "VF604_SYNTHETIC_ETCD_FENCED_JOB",
        "host": args.host, "scenario": args.scenario, "git_base": GIT_BASE,
        "attempt": secrets.token_hex(16),
    }
    encoded = json.dumps(owner, sort_keys=True, separators=(",", ":"))
    owner_sha = hashlib.sha256(encoded.encode()).hexdigest()
    granted = request(args.endpoint, "/v3/lease/grant", {"TTL": str(args.ttl)})
    lease_id = int(granted["ID"])
    require(lease_id > 0 and int(granted["TTL"]) >= 5, "NO_ACTUAL_ETCD_TTL")
    if args.at_epoch:
        remain = args.at_epoch - time.time()
        require(-3 <= remain <= 45, "RACE_BARRIER_MISSED")
        if remain > 0:
            time.sleep(remain)
    txn = {
        "compare": [{"key": key(args.scenario, "lease"),
                     "result": "EQUAL", "target": "VERSION", "version": "0"}],
        "success": [{"requestPut": {
            "key": key(args.scenario, "lease"), "value": b64(encoded),
            "lease": str(lease_id)}}],
    }
    outcome = request(args.endpoint, "/v3/kv/txn", txn)
    if outcome.get("succeeded") is not True:
        request(args.endpoint, "/v3/lease/revoke", {"ID": str(lease_id)})
        item, revision = getkv(args.endpoint, args.scenario, "lease")
        return {"scenario": args.scenario, "host": args.host,
                "result": "DENIED_COMPETING_CLAIM", "postcondition": "NO_LOCAL_CLAIM",
                "provider_revision": revision, "other_owner_present": item is not None,
                "unused_lease_revoked": True}
    item, observed_rev = getkv(args.endpoint, args.scenario, "lease")
    require(item is not None and int(item["lease"]) == lease_id
            and base64.b64decode(item["value"]) == encoded.encode(),
            "CLAIM_POSTCONDITION_MISMATCH")
    generation = int(item["mod_revision"])
    require(int(outcome["header"]["revision"]) == generation
            and observed_rev >= generation,
            "NOT_MONOTONIC_PROVIDER_REVISION")
    data = {"schema": "office604.etcd.lab.claim.v1", "host":args.host,
            "scenario":args.scenario,"git_base":GIT_BASE,
            "task":"VF604_SYNTHETIC_ETCD_FENCED_JOB",
            "owner": encoded,"owner_sha256":owner_sha,
            "lease_id":lease_id, "generation":generation}
    with outfile.open("x", encoding="utf-8") as output:
        json.dump(data, output,sort_keys=True)
    return {"scenario":args.scenario,"host":args.host,
            "result":"GRANTED_REAL_ETCD_LEASE",
            "generation":generation,"ttl_granted":int(granted["TTL"]),
            "owner_sha256":owner_sha, "readback_exact":True}


def effect(args):
    state = read_state(args)
    generation = state["generation"]
    effect_value = json.dumps({
        "scope":"ETCD_ONLY_SYNTHETIC_ATOMIC_EFFECT",
        "host":args.host,"scenario":args.scenario,
        "generation":generation,"owner_sha256":state["owner_sha256"],
        "payload_digest":hashlib.sha256(
            ("VF604_FENCED_KV_ONLY_" + args.scenario).encode()).hexdigest(),
    },sort_keys=True,separators=(",", ":"))
    txn = {
        "compare": [
            {"key":key(args.scenario,"lease"),"target":"MOD",
             "result":"EQUAL","modRevision":str(generation)},
            {"key":key(args.scenario,"lease"),"target":"VALUE",
             "result":"EQUAL","value":b64(state["owner"])},
            {"key":key(args.scenario,"effect"),"target":"VERSION",
             "result":"EQUAL","version":"0"},
        ],
        "success":[{"requestPut":{"key":key(args.scenario,"effect"),
                                  "value":b64(effect_value)}}],
    }
    outcome = request(args.endpoint,"/v3/kv/txn",txn)
    existing,_ = getkv(args.endpoint,args.scenario,"effect")
    if outcome.get("succeeded") is not True:
        return {"scenario":args.scenario,"host":args.host,
                "result":"DENIED_BY_ATOMIC_ETCD_PROVIDER_FENCE",
                "generation":generation,
                "effect_present":existing is not None,
                "effect_written_by_this_attempt":False}
    require(existing is not None
            and base64.b64decode(existing["value"]) == effect_value.encode(),
            "EFFECT_ATOMIC_COMMIT_READBACK_MISMATCH")
    return {"scenario":args.scenario,"host":args.host,
            "result":"ACCEPTED_PROVIDER_ATOMIC_KV_EFFECT",
            "generation":generation,"effect_exact_readback":True,
            "effect_sha256":hashlib.sha256(effect_value.encode()).hexdigest()}


def observe(args):
    lock, revision = getkv(args.endpoint,args.scenario,"lease")
    effect_row, _ = getkv(args.endpoint,args.scenario,"effect")
    if lock:
        owner = json.loads(base64.b64decode(lock["value"]))
        who=owner["host"]
        gen=int(lock["mod_revision"])
        lease=int(lock["lease"])
    else:
        who=None; gen=None; lease=None
    effect_owner=None
    if effect_row:
        content=json.loads(base64.b64decode(effect_row["value"]))
        effect_owner=content["host"]
    return {"result":"OBSERVED_PROVIDER_LINEARIZABLE",
            "scenario":args.scenario,"revision":revision,
            "owner_host":who,"generation":gen,
            "lease_present":lease is not None,
            "effect_host":effect_owner,
            "effect_count":1 if effect_row else 0}


def revoke(args):
    owner=read_state(args)
    request(args.endpoint,"/v3/lease/revoke",{"ID":str(owner["lease_id"])})
    lock,_=getkv(args.endpoint,args.scenario,"lease")
    if lock is not None:
        require(int(lock["mod_revision"])!=owner["generation"],
                "REVOKED_ORIGINAL_OWNER_STILL_HOLDS_LOCK")
    return {"scenario":args.scenario,"host":args.host,
            "result":"PROVIDER_LEASE_REVOKED","former_generation":owner["generation"],
            "former_lease_absent":True}


def renew(args):
    data=read_state(args)
    r=request(args.endpoint,"/v3/lease/keepalive",{"ID":str(data["lease_id"])},
              timeout=4.5)
    answer=r.get("result",r)
    require(int(answer["ID"])==data["lease_id"]
            and int(answer["TTL"])>=5,"RENEWAL_NOT_CONFIRMED")
    lock,_=getkv(args.endpoint,args.scenario,"lease")
    require(lock is not None and int(lock["mod_revision"])==data["generation"],
            "RENEWAL_OWNER_CHANGED")
    return {"scenario":args.scenario,"host":args.host,
            "result":"PROVIDER_LEASE_RENEWAL_CONFIRMED",
            "generation_unchanged":True,"reported_ttl":int(answer["TTL"])}


def selftest():
    for scenario in SCENARIOS:
        require(key(scenario,"lease")!=key(scenario,"effect"),"KEY_COLLISION")
        require(base64.b64decode(key(scenario,"lease")).decode().startswith(PREFIX+"/"),
                "KEY_ESCAPE")
    tests=8
    for bad in ("invalid","", "../race", "race/../../", "RACE"):
        try:
            key(bad,"lease")
        except Refuse:
            tests+=1
        else:
            raise AssertionError("ALLOWLIST_ACCEPTED_BAD_SCENARIO")
    require(len(SCENARIOS)==4 and len(HOSTS)==2, "SELFTEST_INVARIANT")
    return {"result":"PASS_OFFLINE","tests":tests,
            "live_provider_calls":0,"model_calls":0,"production_effects":0,
            "external_github_writes":0}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("claim","effect","observe","revoke","renew","selftest"))
    parser.add_argument("--host", choices=HOSTS)
    parser.add_argument("--scenario",choices=SCENARIOS)
    parser.add_argument("--state")
    parser.add_argument("--ttl",type=int,default=45)
    parser.add_argument("--at-epoch",type=float,default=0)
    parser.add_argument("--endpoint",default=ENDPOINT)
    args=parser.parse_args()
    if args.mode=="selftest":
        print(json.dumps(selftest(),sort_keys=True));return
    require(args.host in HOSTS and args.scenario in SCENARIOS,
            "LIVE_HOST_SCENARIO_REQUIRED")
    require(args.endpoint in (ENDPOINT,DISCONNECTED),"ENDPOINT_NOT_ALLOWED")
    require(5<=args.ttl<=120, "TTL_OUT_OF_LAB_BOUNDS")
    if args.mode in ("claim","effect","renew","revoke"):
        require(args.state is not None,"EXACT_STATE_REQUIRED")
    actions={"claim":claim,"effect":effect,"observe":observe,
             "revoke":revoke,"renew":renew}
    print(json.dumps(actions[args.mode](args),sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (Refuse,KeyError,ValueError,TypeError,AssertionError,OSError) as err:
        print(json.dumps({"result":"FAIL_CLOSED","reason":str(err)[:140],
                          "external_effects":0,"retry":False},sort_keys=True))
        sys.exit(3)
