#!/usr/bin/env python3
"""Read-only single-purpose Mac HTTPS mTLS fixture endpoint for GitHub CAS LAB.

On Mac only; Win is the sole native GitHub writer. No write endpoint, no
scheduler, no Git commands, no credentials from GitHub, no model calls.
Offline selftest does not bind sockets or read any test certificate.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import ssl
import sys

SLUG = "p0-github604-onewriter-macorigin-20261010"
ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "runtime"
PRIVATE = ROOT / "private"
FIXTURES = RUNTIME / "requests"
PORT = 32683
BIND = ("192.168.0.217", PORT)
REF = "refs/heads/office-v2-lab-604-mac-origin-cas-20261010"
REPO = "nocturney/velvetos-core"
BASE = "cc2cccb2770a79424741719795d552fa85d69a81"
PHASES = ("seed", "effect_a", "stale_b", "fresh_b", "stale_a", "cleanup")
CERT_CN = "vf604-win-native-github-cas-sink"
SCHEMA = "vf604.mac-origin-native-git-cas-request.v1"


class Denied(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Denied(message)


def validate_request(phase, v):
    need(phase in PHASES and type(v) is dict and
         set(v) == {"schema", "repo", "ref", "phase", "expected_sha",
                    "candidate", "expected_result", "base_commit"},
         "INVALID_EXACT_MAC_GIT_REQUEST_SHAPE")
    need(v["schema"] == SCHEMA and v["repo"] == REPO and
         v["ref"] == REF and v["phase"] == phase and
         v["base_commit"] == BASE, "WRONG_REPO_REF_OR_BASE")
    candidate = {"seed": "seed", "effect_a": "a", "stale_b": "b",
                 "fresh_b": "b", "stale_a": "a", "cleanup": "none"}[phase]
    result = "denied_stale" if phase in ("stale_b", "stale_a") else "accepted"
    need(v["candidate"] == candidate and v["expected_result"] == result,
         "UNEXPECTED_ACTOR_WRITE_OR_TEST_EXPECTATION")
    old = v["expected_sha"]
    need(type(old) is str and
         (old == "" if phase == "seed" else bool(re.fullmatch("[0-9a-f]{40}", old))),
         "INVALID_GIT_CAS_EXPECTED_SHA")
    return v


class App(BaseHTTPRequestHandler):
    server_version = "VF604-MacFixture/1"
    sys_version = ""
    def log_message(self, *_args):
        return

    def do_GET(self):
        try:
            need(self.path.startswith("/v1/fixture/"),
                 "UNRELATED_HTTP_ENDPOINT")
            phase = self.path.removeprefix("/v1/fixture/")
            need(phase in PHASES, "UNKNOWN_PHASE")
            cert = self.connection.getpeercert()
            sub = dict(p for rd in cert.get("subject", ()) for p in rd)
            need(sub.get("commonName") == CERT_CN,
                 "UNTRUSTED_WINDOWS_CLIENT_CERT")
            path = FIXTURES / (phase + ".json")
            need(path.parent == FIXTURES and path.is_file()
                 and not path.is_symlink() and 30 < path.stat().st_size < 1800,
                 "REQUEST_NOT_ISSUED_OR_UNEXPECTED_BYTES")
            result = validate_request(phase, json.loads(path.read_text()))
            content = json.dumps(result, sort_keys=True,
                                 separators=(",", ":")).encode()
            self.send_response(200)
        except (Denied, ValueError, TypeError, OSError) as err:
            content = json.dumps({"result": "FAIL_CLOSED",
                                  "reason": "REQUEST_NOT_AVAILABLE_OR_UNTRUSTED"}).encode()
            self.send_response(409)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def serve():
    need(ROOT.name == SLUG and PRIVATE.is_dir() and FIXTURES.is_dir(),
         "REFUSE_WRONG_MAC_ONLY_LAB_ROOT")
    pidfile = RUNTIME / "mac-fixture-server.pid"
    need(not pidfile.exists(), "REFUSE_SECOND_LAB_FIXTURE_SERVER")
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(str(PRIVATE / "server.crt"),
                        str(PRIVATE / "server.key"))
    tls.load_verify_locations(str(PRIVATE / "ca.crt"))
    tls.verify_mode = ssl.CERT_REQUIRED
    server = ThreadingHTTPServer(BIND, App)
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    try:
        with pidfile.open("x", encoding="ascii") as f:
            f.write(str(os.getpid()))
        print(json.dumps({"status": "TEMPORARY_MAC_READ_ONLY_MTLS_FIXTURE",
                          "pid": os.getpid(), "port": PORT,
                          "writer": "NATIVE_WINDOWS_GIT_ONLY",
                          "git_requests": 0,
                          "no_scheduler_or_lease_provider": True}), flush=True)
        server.serve_forever(poll_interval=0.15)
    finally:
        server.server_close()


def selftest():
    count = 0
    for phase in PHASES:
        value = {"schema": SCHEMA, "repo": REPO, "ref": REF,
                 "phase": phase, "expected_sha": "" if phase == "seed" else "a"*40,
                 "candidate": {"seed": "seed", "effect_a": "a", "stale_b": "b",
                               "fresh_b": "b", "stale_a": "a", "cleanup": "none"}[phase],
                 "expected_result": "denied_stale" if phase in
                                    ("stale_b", "stale_a") else "accepted",
                 "base_commit": BASE}
        validate_request(phase, value)
        count += 1
        for key, bad in (("repo", "other/other"), ("ref", "refs/heads/main"),
                         ("base_commit", "b"*40), ("phase", "../effect_a"),
                         ("expected_sha", "u"*40), ("candidate", "admin"),
                         ("expected_result", "production")):
            wrong = dict(value)
            wrong[key] = bad
            try:validate_request(phase, wrong)
            except Denied:count += 1
            else:raise AssertionError("INCORRECT_ALLOW_"+phase+key)
    assert count == 48
    return {"result": "PASS_OFFLINE", "cases": count,
            "git_effect_writes": 0, "server_started": False,
            "authenticated_requests": 0,
            "production_authority": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("serve", "selftest"))
    mode = parser.parse_args().mode
    print(json.dumps(selftest(), sort_keys=True)) if mode == "selftest" else serve()


if __name__ == "__main__":
    try:main()
    except (Denied, OSError) as exc:
        print(json.dumps({"result": "FAIL_CLOSED",
                          "reason": str(exc)[:140],
                          "git_effect_writes": 0}), flush=True)
        sys.exit(3)
