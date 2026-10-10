#!/usr/bin/env python3
"""#604 manual lab-only TLS client-identity and receiver-owned filesystem effect.

etcd v3.6.15 RBAC/mTLS is the ONLY lease source; workers receive READ-only
etcd roles. Receiver's short-lived mTLS HTTPS endpoint is an effect adapter,
NOT a scheduler or alternative lease provider.

CRITICAL: Etcd transaction and POSIX hard-link are TWO different atomic
domains. After provider reservation, process crash/outage can leave UNKNOWN;
this lab must NEVER claim globally atomic external-effect fencing.
Only manual 'serve' launches a listener. CI uses 'selftest' only.
"""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import ssl
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

LAB_SLUG = "p0-fence604-mtls-fs-receiver-gpt6-20261010"
BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "runtime"
PRIVATE = RUNTIME / "private"
ARTIFACTS = RUNTIME / "artifacts"
ETCD_ENDPOINT = "https://127.0.0.1:32579"
LISTEN = ("192.168.0.217", 32581)
PREFIX = "/velvet-office2/lab604/mtls-fs-20261010"
SCENARIOS = ("handoff", "expiry", "duplicate", "unknown", "outage")
WORKERS = ("vf604-win", "vf604-mac")
ETCD_BINARY_SHA = "05f34d3be92b0ba78dfc5aa9fd5d63224d551a7f8c2eadfbaa7dc2f35ae625ad"
OP_LOCK = threading.RLock()


class Refuse(Exception):
    def __init__(self, code, status=409):
        super().__init__(code)
        self.code = code
        self.status = status


def must(ok, code):
    if not ok:
        raise Refuse(code)


def json_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def encode(obj):
    return base64.b64encode(json_bytes(obj)).decode("ascii")


def decode(value):
    return json.loads(base64.b64decode(value, validate=True))


def scenario_key(scenario, part):
    must(scenario in SCENARIOS and part in ("lease", "intent"), "KEY_OUTSIDE_EXACT_LAB_NAMESPACE")
    return PREFIX + "/" + scenario + "/" + part


def artifact_path(scenario):
    must(scenario in SCENARIOS, "ARTIFACT_OUTSIDE_ALLOWLIST")
    return ARTIFACTS / (scenario + ".json")


def provider_cmd(*words, input_text=None):
    """Pinned local real native gRPC TLS client, no tokens, passwords or shell."""
    command = [
        str(RUNTIME / "etcdctl"),
        "--endpoints=" + ETCD_ENDPOINT,
        "--cacert=" + str(PRIVATE / "ca.crt"),
        "--cert=" + str(PRIVATE / "receiver.crt"),
        "--key=" + str(PRIVATE / "receiver.key"),
        "--write-out=json",
    ] + list(words)
    try:
        p = subprocess.run(command, input=input_text, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           cwd=str(RUNTIME), timeout=9, check=False)
    except (subprocess.SubprocessError, OSError):
        raise Refuse("PROVIDER_UNAVAILABLE_OR_UNKNOWN")
    if p.returncode:
        raise Refuse("PROVIDER_UNAVAILABLE_OR_DENIED")
    try:
        return json.loads(p.stdout)
    except (ValueError, TypeError):
        raise Refuse("PROVIDER_INVALID_JSON")


def kv_get(scenario, part):
    key = scenario_key(scenario, part)
    result = provider_cmd("get", key)
    header = result.get("header")
    must(type(header) is dict and type(header.get("revision")) is int,
         "PROVIDER_REVISION_NOT_AUTHENTICATED")
    rows = result.get("kvs", [])
    must(type(rows) is list and len(rows) <= 1, "PROVIDER_ROW_AMBIGUOUS")
    if not rows:
        return None, header["revision"]
    item = rows[0]
    must(base64.b64decode(item.get("key", ""), validate=True).decode() == key,
         "PROVIDER_RETURNED_WRONG_KEY")
    return {
        "revision": int(item["mod_revision"]),
        "lease_id": int(item.get("lease", 0)),
        "value": base64.b64decode(item["value"], validate=True).decode(),
        "version": int(item["version"]),
    }, header["revision"]


def transaction(compares, operations):
    """No shell, only exact call/grammar created from fixed scenario keys."""
    must(type(compares) is list and compares and type(operations) is list,
         "TXN_EXPECTED_ATOMIC_COMPARE_AND_PUT")
    message = "\n".join(compares) + "\n\n" + "\n".join(operations) + "\n\n\n"
    result = provider_cmd("txn", input_text=message)
    must(type(result) is dict and type(result.get("succeeded")) is bool and
         type((result.get("header") or {}).get("revision")) is int,
         "TRANSACTION_POSTCONDITION_UNVERIFIED")
    return result


def compare_mod(key, generation):
    must(type(generation) is int and generation > 0, "INVALID_GENERATION")
    return 'mod("' + key + '") = "' + str(generation) + '"'


def compare_value(key, value):
    must(type(value) is str and len(value) < 1500 and value.isascii() and
         '"' not in value and "\n" not in value, "UNSAFE_ETCD_VALUE_COMPARE")
    return 'value("' + key + '") = "' + value + '"'


def compare_empty(key):
    return 'version("' + key + '") = "0"'


def leased_owner(scenario):
    row, global_rev = kv_get(scenario, "lease")
    if row is None:
        return None, global_rev
    owner = decode(row["value"])
    must(type(owner) is dict and
         owner.get("identity") in WORKERS and
         owner.get("scenario") == scenario and
         owner.get("kind") == "VF604_SYNTHETIC_EXTERNAL_FILE_REQUEST" and
         len(owner.get("attempt", "")) == 32 and
         row["lease_id"] > 0 and
         row["revision"] > 0, "OWNERSHIP_RECORD_UNVERIFIED")
    return (row, owner), global_rev


def guard_reassignment_on_intent(intent):
    """No new owner admission while a previous effect is unresolved or exists."""
    if intent is None:
        return
    must(type(intent) is dict and type(intent.get("value")) is str,
         "UNVERIFIED_EFFECT_INTENT")
    value = decode(intent["value"])
    must(type(value) is dict and type(value.get("state")) is str,
         "INVALID_PERSISTED_EFFECT_INTENT")
    if value["state"] == "PENDING_EXTERNAL_WRITE":
        raise Refuse("DENIED_UNKNOWN_OUTCOME_RECONCILIATION_REQUIRED")
    if value["state"] == "COMMITTED_FILE_READBACK":
        raise Refuse("DENIED_ALREADY_COMMITTED_EFFECT")
    raise Refuse("DENIED_UNRECOGNIZED_EFFECT_INTENT")


def grant(identity, scenario, ttl):
    must(identity in WORKERS and scenario in SCENARIOS, "UNVERIFIED_ACTOR_OR_JOB")
    must(type(ttl) is int and 6 <= ttl <= 110, "TTL_NOT_IN_BOUND")
    # This receiver is the ONLY scoped worker-facing lease grantor; etcd
    # itself remains the sole authoritative lease clock + revision store.
    if artifact_path(scenario).exists():
        raise Refuse("DESTINATION_ALREADY_FINAL")
    intent, _ = kv_get(scenario, "intent")
    guard_reassignment_on_intent(intent)
    old, _ = leased_owner(scenario)
    if old is not None:
        raise Refuse("DENIED_ACTIVE_OWNER")
    lease = provider_cmd("lease", "grant", str(ttl))
    lease_id = int(lease["ID"])
    must(lease_id > 0 and int(lease["TTL"]) >= 6, "PROVIDER_LEASE_NOT_GRANTED")
    value = encode({
        "attempt": secrets.token_hex(16),
        "identity": identity,
        "kind": "VF604_SYNTHETIC_EXTERNAL_FILE_REQUEST",
        "scenario": scenario,
    })
    key = scenario_key(scenario, "lease")
    command = "put " + key + " " + value + " --lease=" + format(lease_id, "x")
    try:
        result = transaction([compare_empty(key)], [command])
        if not result["succeeded"]:
            provider_cmd("lease", "revoke", format(lease_id, "x"))
            raise Refuse("DENIED_COMPETING_OWNER")
        (row, owner), _ = leased_owner(scenario)
        generation = row["revision"]
        must(row["value"] == value and row["lease_id"] == lease_id and
             int(result["header"]["revision"]) == generation,
             "GRANT_REVISION_OR_OWNER_MISMATCH")
    except Exception:
        # Never claim that a failed/ambiguous provider transaction succeeded.
        # In an unknown outcome, do not blindly retry the claim.
        raise
    return {"result":"GRANTED_BY_REAL_ETCD_PROVIDER",
            "owner":identity, "scenario":scenario,
            "generation":generation, "ttl":int(lease["TTL"])}


def revoke(identity, scenario, generation):
    owner, _ = leased_owner(scenario)
    must(owner is not None and
         owner[0]["revision"] == generation and
         owner[1]["identity"] == identity, "DENIED_STALE_OWNER")
    result = provider_cmd("lease", "revoke", format(owner[0]["lease_id"], "x"))
    current, _ = leased_owner(scenario)
    must(current is None or current[0]["revision"] != generation,
         "REVOKE_NOT_CONFIRMED")
    return {"result":"PROVIDER_ISSUED_LEASE_REVOKED", "scenario":scenario,
            "former_generation":generation}


def write_exact_exclusive(final, data):
    """Actual external Mac filesystem effect, NO overwrite or unsafe paths."""
    must(final.parent == ARTIFACTS and not final.is_symlink()
         and not final.exists(), "EXTERNAL_FILE_ALREADY_PRESENT")
    temp = ARTIFACTS / (".owned-" + secrets.token_hex(12) + ".tmp")
    must(temp.parent == ARTIFACTS and not temp.exists(), "BAD_STAGING_PATH")
    try:
        with temp.open("xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(str(temp), str(final))  # atomic no-replace create (same filesystem)
        fd = os.open(str(ARTIFACTS), os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    except (OSError, FileExistsError):
        raise Refuse("UNKNOWN_OUTCOME_EXTERNAL_FS_WRITE")
    finally:
        if temp.exists():
            temp.unlink()
    must(final.is_file() and final.read_bytes() == data,
         "UNKNOWN_OUTCOME_EXTERNAL_FILE_READBACK")
    return hashlib.sha256(data).hexdigest()


def effect(identity, scenario, generation):
    existing, _ = leased_owner(scenario)
    must(existing is not None and
         existing[0]["revision"] == generation and
         existing[1]["identity"] == identity,
         "DENIED_STALE_OWNER_OR_EXPIRED")
    key_lease = scenario_key(scenario, "lease")
    key_intent = scenario_key(scenario, "intent")
    intent_row, _ = kv_get(scenario, "intent")
    if intent_row is not None:
        raise Refuse("UNKNOWN_OR_ALREADY_COMMITTED_NO_BLIND_RETRY")
    must(not artifact_path(scenario).exists(),
         "EXTERNAL_FILE_ALREADY_PRESENT")
    payload = {
        "scenario": scenario,
        "host_identity": identity,
        "generation": generation,
        "attempt": existing[1]["attempt"],
        "effect_kind": "MAC_NATIVE_REAL_FILESYSTEM_LAB_ONLY",
        "fixture_digest": hashlib.sha256(("VF604_EXACT_SYNTHETIC_"+scenario).encode()).hexdigest(),
    }
    raw = json_bytes(payload)
    sha = hashlib.sha256(raw).hexdigest()
    pending = encode({"state": "PENDING_EXTERNAL_WRITE",
                      "sha256":sha, "identity":identity,
                      "generation":generation})
    compares = [compare_mod(key_lease, generation),
                compare_value(key_lease, existing[0]["value"]),
                compare_empty(key_intent)]
    approved = transaction(compares, ["put "+key_intent+" "+pending])
    must(approved["succeeded"], "DENIED_ATOMIC_PROVIDER_EFFECT_RESERVATION")
    # Explicit intentional fault-injection yields a REAL durable pending
    # provider intent and NO filesystem artifact. Never replay blindly.
    if scenario == "unknown":
        raise Refuse("UNKNOWN_OUTCOME_INTENT_COMMITTED_NO_EXTERNAL_WRITE")
    # Recheck owner after reservation. NOT atomic with the following link:
    # concurrent TTL expiration or disconnection still creates uncertainty.
    changed, _ = leased_owner(scenario)
    if changed is None or changed[0]["revision"] != generation or \
            changed[0]["value"] != existing[0]["value"]:
        raise Refuse("UNKNOWN_OUTCOME_PROVIDER_CHANGED_BEFORE_FS_EFFECT")
    digest = write_exact_exclusive(artifact_path(scenario), raw)
    complete = encode({"state":"COMMITTED_FILE_READBACK",
                       "sha256":sha,"identity":identity,
                       "generation":generation})
    final = transaction([compare_mod(key_lease, generation),
                         compare_value(key_lease, existing[0]["value"]),
                         compare_value(key_intent, pending)],
                        ["put "+key_intent+" "+complete])
    must(final["succeeded"], "UNKNOWN_OUTCOME_AFTER_EXTERNAL_FS_EFFECT")
    committed, _ = kv_get(scenario, "intent")
    must(committed is not None and committed["value"] == complete
         and artifact_path(scenario).read_bytes() == raw,
         "UNKNOWN_OUTCOME_POST_COMMIT_READBACK")
    return {"result":"EXTERNAL_MAC_FILE_AND_PROVIDER_RECEIPT_VERIFIED",
            "scenario":scenario,"generation":generation,
            "owner":identity,"sha256":digest,
            "file_readback_exact":True,
            "cross_store_global_atomicity_proven":False}


def observe(identity, scenario):
    owner, revision = leased_owner(scenario)
    intent, _ = kv_get(scenario, "intent")
    file = artifact_path(scenario)
    must(not file.is_symlink(), "EXTERNAL_FS_SYMLINK_REFUSED")
    if file.exists():
        must(file.is_file() and file.stat().st_size < 2048,
             "EXTERNAL_FS_UNEXPECTED_SIZE")
        data = json.loads(file.read_text(encoding="utf-8"))
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        accepted_host = data.get("host_identity")
        final_gen = data.get("generation")
    else:
        sha = accepted_host = final_gen = None
    return {"result":"LAB_INDEPENDENT_STATUS",
            "scenario":scenario,"observer":identity,
            "provider_revision":revision,
            "owner":owner[1]["identity"] if owner else None,
            "owner_generation":owner[0]["revision"] if owner else None,
            "intent":decode(intent["value"])["state"] if intent else None,
            "external_file_exists":file.exists(),
            "external_file_sha256":sha,
            "external_file_actor":accepted_host,
            "external_file_generation":final_gen}


def bounded(body):
    must(type(body) is dict and set(body).issubset(
        {"scenario", "generation", "ttl"}),
        "REQUEST_UNKNOWN_FIELDS")
    scenario = body.get("scenario")
    must(type(scenario) is str and scenario in SCENARIOS,
         "SCENARIO_NOT_ALLOWLISTED")
    if "generation" in body:
        must(type(body["generation"]) is int and
             0 < body["generation"] < 1000000000000,
             "BAD_INTEGER_FENCING_GENERATION")
    if "ttl" in body:
        must(type(body["ttl"]) is int and 6 <= body["ttl"] <= 110,
             "TTL_NOT_ALLOWED")
    return scenario


class Receiver(BaseHTTPRequestHandler):
    server_version = "VF604-LAB-receiver/1"
    sys_version = ""
    def log_message(self, fmt, *args):
        # Do not emit authentication or client payloads to service log.
        return

    def do_POST(self):
        code = 200
        payload = {}
        try:
            must(self.path in ("/v1/claim", "/v1/revoke", "/v1/effect",
                               "/v1/observe"), "UNKNOWN_RECEIVER_ACTION")
            cert = self.connection.getpeercert()
            subject = dict(item for row in cert.get("subject", ()) for item in row)
            identity = subject.get("commonName")
            must(identity in WORKERS, "CLIENT_CERT_IDENTITY_NOT_ALLOWED")
            must(self.headers.get("Content-Type") == "application/json",
                 "EXPECTED_JSON")
            n = self.headers.get("Content-Length", "")
            must(n.isdigit() and 0 < int(n) < 512, "BAD_PAYLOAD_SIZE")
            raw = self.rfile.read(int(n))
            body = json.loads(raw)
            scenario = bounded(body)
            with OP_LOCK:
                if self.path == "/v1/claim":
                    payload = grant(identity, scenario, body.get("ttl", 45))
                elif self.path == "/v1/revoke":
                    payload = revoke(identity, scenario, body["generation"])
                elif self.path == "/v1/effect":
                    payload = effect(identity, scenario, body["generation"])
                else:
                    payload = observe(identity, scenario)
        except Refuse as e:
            code = e.status
            payload = {"result":"FAIL_CLOSED", "reason":e.code,
                       "blind_retry":False,"production_authority":False}
        except (ValueError, TypeError, KeyError, OSError, UnicodeError,
                json.JSONDecodeError):
            code = 503
            payload = {"result":"UNKNOWN_OUTCOME", "reason":"INTERNAL_OR_PROVIDER_UNVERIFIED",
                       "blind_retry":False, "production_authority":False}
        content = json_bytes(payload)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def serve():
    must(BASE.name == LAB_SLUG, "REFUSE_NON_ISOLATED_LAB_RUNTIME")
    must(ARTIFACTS.is_dir() and PRIVATE.is_dir() and
         (RUNTIME / "etcdctl").is_file(), "EXACT_LAB_FILES_MISSING")
    must(hashlib.sha256((RUNTIME/"etcdctl").read_bytes()).hexdigest()
         == ETCD_BINARY_SHA, "NATIVE_ETCDCTL_BINARY_NOT_PINNED")
    must(not (RUNTIME/"receiver-owned.pid").exists(),
         "RECEIVER_ALREADY_OWNED")
    server = ThreadingHTTPServer(LISTEN, Receiver)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(PRIVATE/"server.crt"), str(PRIVATE/"server.key"))
    ctx.load_verify_locations(cafile=str(PRIVATE/"ca.crt"))
    ctx.verify_mode = ssl.CERT_REQUIRED
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    try:
        (RUNTIME/"receiver-owned.pid").write_text(str(os.getpid()), encoding="ascii")
        print(json.dumps({"status":"MANUAL_LAB_RECEIVER_SERVING",
                          "pid":os.getpid(),"tls_client_cert_required":True,
                          "etcd_rbac_cn_identity":"vf604-receiver",
                          "provider_is_single_source_of_lease":True,
                          "external_cross_store_atomicity":False}),flush=True)
        server.serve_forever(poll_interval=0.15)
    finally:
        server.server_close()


def selftest():
    tests=0
    for v in SCENARIOS:
        must(scenario_key(v,"lease") != scenario_key(v,"intent"),"KEY_COLLISION");tests+=1
        must(artifact_path(v).name == v+".json","ARTIFACT_IDENTITY");tests+=1
    for malformed in ("../x","x/y","", "race", "LPT1"):
        try:scenario_key(malformed,"lease")
        except Refuse:tests+=1
        else:raise AssertionError("ACCEPTED_BAD_SCENARIO")
    for bad in ({"scenario":"handoff","generation":True},
                {"scenario":"handoff","ttl":False},
                {"scenario":"handoff","ttl":120},
                {"scenario":"handoff","path":"/tmp"},
                {"scenario":"handoff","generation":-1},
                {"scenario":"handoff","generation":"4"}):
        try:bounded(bad)
        except Refuse:tests+=1
        else:raise AssertionError("ACCEPTED_MALFORMED_REQUEST")
    guard_reassignment_on_intent(None)
    tests += 1
    for state in ("PENDING_EXTERNAL_WRITE", "COMMITTED_FILE_READBACK",
                  "CORRUPTED_UNKNOWN_PROVIDER_INTENT"):
        try:
            guard_reassignment_on_intent({"value": encode({"state":state})})
        except Refuse:
            tests += 1
        else:
            raise AssertionError("REASSIGNMENT_ALLOWED_WITH_UNRESOLVED_EFFECT")
    must(len(WORKERS)==2 and len(SCENARIOS)==5, "SELFTEST_IDENTITY")
    return {"status":"PASS_OFFLINE","tests":tests,
            "provider_requests":0,"filesystem_effect_writes":0,
            "server_started":False,"model_calls":0,
            "production_authority":False,"external_atomicity_claimed":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("serve","selftest"))
    args=p.parse_args()
    if args.mode=="selftest":
        print(json.dumps(selftest(),sort_keys=True))
    else:
        serve()


if __name__=="__main__":
    try:main()
    except Refuse as e:
        print(json.dumps({"status":"FAIL_CLOSED","reason":e.code,
                          "blind_retry":False}),flush=True)
        sys.exit(3)
