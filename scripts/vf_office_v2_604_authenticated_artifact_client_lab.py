#!/usr/bin/env python3
"""Manual two-real-host mTLS #604 scratch receiver client; no live action in CI."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.request

SLUG = "p0-fence604-mtls-fs-receiver-gpt6-20261010"
RECEIVER = "https://192.168.0.217:32581"
SCENARIOS = ("handoff", "expiry", "duplicate", "unknown", "outage")
HOSTS = ("win", "mac")
ROUTES = {"claim":"/v1/claim", "revoke":"/v1/revoke",
          "effect":"/v1/effect", "observe":"/v1/observe"}


class Refused(Exception):
    pass


def required(ok, code):
    if not ok:
        raise Refused(code)


def certs(root, host):
    path = Path(root).resolve()
    required(((path.name == "runtime" and path.parent.name == SLUG) or
              (path.name == "private" and path.parent.name == "runtime" and
               path.parents[1].name == SLUG)) and path.is_dir(),
             "TLS_CREDENTIAL_PATH_NOT_ISOLATED_LAB")
    files = [path/"ca.crt",path/(host+".crt"),path/(host+".key")]
    for f in files:
        required(f.is_file() and not f.is_symlink() and 500 <= f.stat().st_size < 8000,
                 "TEST_CERT_MATERIAL_MISSING_OR_REPLACED")
    ctx = ssl.create_default_context(cafile=str(files[0]))
    ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(files[1]),str(files[2]))
    return ctx


def execute(route, host, scenario, generation, ttl, root):
    required(route in ROUTES and host in HOSTS and scenario in SCENARIOS,
             "LIVE_RECEIVER_PATH_NOT_ALLOWLISTED")
    if route in ("effect","revoke"):
        required(type(generation) is int and 0 < generation < 10**12,
                 "INVALID_FENCING_GENERATION")
    if route=="claim":
        required(type(ttl) is int and 6 <= ttl <=110, "INVALID_LEASE_TTL")
    body={"scenario":scenario}
    if route in ("effect","revoke"):body["generation"]=generation
    if route=="claim":body["ttl"]=ttl
    data=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
    ctx=certs(root,host)
    req=urllib.request.Request(RECEIVER+ROUTES[route],data=data,
                               method="POST",headers={"Content-Type":"application/json"})
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                       urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=10) as resp:
            raw=resp.read(2048)
            required(resp.status==200 and len(raw)<2048,"UNVERIFIED_RECEIVER_HTTP")
            obj=json.loads(raw)
            required(type(obj) is dict and
                     (obj.get("result") in (
                      "GRANTED_BY_REAL_ETCD_PROVIDER",
                      "PROVIDER_ISSUED_LEASE_REVOKED",
                      "EXTERNAL_MAC_FILE_AND_PROVIDER_RECEIPT_VERIFIED",
                      "LAB_INDEPENDENT_STATUS")), "NON_AUTHORITATIVE_RESPONSE")
            return obj,0
    except urllib.error.HTTPError as e:
        raw=e.read(2048)
        try: body=json.loads(raw)
        except (ValueError,UnicodeDecodeError):body={}
        required(type(body) is dict and
                 body.get("result") in ("FAIL_CLOSED","UNKNOWN_OUTCOME")
                 and body.get("blind_retry") is False
                 and body.get("production_authority") is False,
                 "UNKNOWN_HTTP_ERROR_IS_NOT_SAFE_SUCCESS")
        reason=body.get("reason","UNKNOWN")
        return {"result":"REFUSED_BY_AUTHENTICATED_RECEIVER",
                "reason":reason,"http_status":e.code,
                "blind_retry":False}, 4 if reason.startswith("UNKNOWN") else 3
    except (urllib.error.URLError,TimeoutError,OSError,ssl.SSLError):
        return {"result":"RECEIVER_UNAVAILABLE_FAIL_CLOSED",
                "blind_retry":False,"external_effect_claimed":False}, 3


def selftest():
    n=0
    required(len(ROUTES)==4 and len(SCENARIOS)==5 and len(HOSTS)==2,
             "IDENTITY_DRIFT")
    for host in HOSTS:
        for scenario in SCENARIOS:
            required(host in HOSTS and scenario in SCENARIOS,"IDENTITY")
            n+=1
    for malformed in ("../../", "/etc", "", "OTHER"):
        required(malformed not in SCENARIOS, "MALFORMED_SCENARIO")
        n+=1
    required(len(ROUTES)==4,"ROUTE_DRIFT")
    return {"status":"PASS_OFFLINE","tests":n,"receiver_requests":0,
            "filesystem_effects":0,"production_authority":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=tuple(ROUTES)+("selftest",))
    p.add_argument("--host",choices=HOSTS)
    p.add_argument("--scenario",choices=SCENARIOS)
    p.add_argument("--generation",type=int)
    p.add_argument("--ttl",type=int,default=40)
    p.add_argument("--cert-dir")
    a=p.parse_args()
    if a.mode=="selftest":
        print(json.dumps(selftest(),sort_keys=True));return
    required(a.host in HOSTS and a.scenario in SCENARIOS and
             a.cert_dir is not None,"LAB_ONLY_HOST_SCENARIO_CERT_DIR_REQUIRED")
    response,code=execute(a.mode,a.host,a.scenario,a.generation,a.ttl,a.cert_dir)
    print(json.dumps(response,sort_keys=True),flush=True)
    sys.exit(code)


if __name__=="__main__":
    try:main()
    except (Refused, ValueError, KeyError, TypeError) as err:
        print(json.dumps({"result":"FAIL_CLOSED",
                          "reason":str(err)[:130],
                          "blind_retry":False}),flush=True)
        sys.exit(3)
