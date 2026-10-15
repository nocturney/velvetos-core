#!/usr/bin/env python3
"""#604 CP069: fixed, no-credential Linux namespace/UID boundary witness.

Selftest is pure. The ONLY live mode runs an operator-authored literal in
the existing disposable Colima LAB guest under UID 65534 and new mount/net/PID
namespaces. It never imports a model output or receives a Git credential.
This is NOT a generally admitted untrusted-code sandbox or a Core lease.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

SCHEMA = "velvetos.office-v2.604.lowpriv-namespace-fixed.v1"
UID = 65534
TOKEN = "VF604_CP069_FIXED_NO_MODEL"
ROOT_PREFIX = "vf604-cp069-fixed-"
KEYS = (
    "uid_nobody", "supplementary_groups_cleared", "no_capabilities",
    "no_new_privileges", "net_namespace_distinct", "mount_namespace_distinct",
    "pid_namespace_distinct", "no_ipv4_routes", "outbound_routing_denied",
    "containerd_socket_denied", "synthetic_canary_denied",
    "credential_environment_empty", "resource_limits_active",
)
# No shell, model-code, filesystem import from untrusted HEAD, or Git calls.
CHILD = r'''
import errno, json, os, pathlib, resource, socket, sys
private=pathlib.Path(sys.argv[1]); host=json.loads(sys.argv[2])
def ns(name):
    return os.readlink("/proc/self/ns/"+name)
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU,(3,4))
resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
resource.setrlimit(resource.RLIMIT_NOFILE,(48,48))
status={}
for line in pathlib.Path("/proc/self/status").read_text().splitlines():
    if line.startswith(("CapEff:","NoNewPrivs:")):
        key,value=line.split(":",1)
        status[key]=value.strip()
cases={}
cases["uid_nobody"]=os.getuid()==65534 and os.geteuid()==65534
cases["supplementary_groups_cleared"]=os.getgroups()==[]
cases["no_capabilities"]=int(status.get("CapEff","1"),16)==0
cases["no_new_privileges"]=status.get("NoNewPrivs")=="1"
for name,key in (("net","net_namespace_distinct"),("mnt","mount_namespace_distinct"),("pid","pid_namespace_distinct")):
    cases[key]=ns(name)!=host[name]
routes=pathlib.Path("/proc/net/route").read_text().splitlines()
cases["no_ipv4_routes"]=len(routes)==0 or (len(routes)==1 and routes[0].startswith("Iface"))
sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
try:
    route_status=sock.connect_ex(("203.0.113.1",443))
finally: sock.close()
cases["outbound_routing_denied"]=route_status in (errno.ENETUNREACH,errno.EHOSTUNREACH)
sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
try:
    err=sock.connect_ex("/run/containerd/containerd.sock")
finally: sock.close()
cases["containerd_socket_denied"]=err in (errno.EACCES,errno.EPERM,errno.ENOENT)
try:
    (private/"synthetic-not-a-secret.txt").read_bytes()
except OSError as err:
    cases["synthetic_canary_denied"]=err.errno in (errno.EACCES,errno.EPERM)
else:
    cases["synthetic_canary_denied"]=False
cases["credential_environment_empty"]=not any(
    key in os.environ for key in ("GH_TOKEN","GITHUB_TOKEN","SSH_AUTH_SOCK",
                                  "GOOGLE_APPLICATION_CREDENTIALS"))
cases["resource_limits_active"]=resource.getrlimit(resource.RLIMIT_AS)[0]==256*1024*1024
print(json.dumps({"schema":"velvetos.office-v2.604.lowpriv-namespace-fixed.v1",
                  "uid":os.getuid(),"cases":cases,
                  "namespaces":{n:ns(n) for n in ("net","mnt","pid")},
                  "fixed_operator_literal":True,
                  "model_source_executed":False,
                  "core_signed_lease":False,
                  "github_write_authority":False},sort_keys=True),flush=True)
raise SystemExit(0 if all(cases.values()) and len(cases)==13 else 2)
'''


class Refuse(Exception):
    pass


def require(value: bool, reason: str) -> None:
    if not value:
        raise Refuse(reason)


def plan(root: str, ns: dict) -> list[str]:
    require(type(root) is str and root.startswith("/tmp/" + ROOT_PREFIX)
            and "\n" not in root and len(root) < 220, "ROOT_NOT_FIXED_LAB")
    require(type(ns) is dict and set(ns) == {"net", "mnt", "pid"}
            and all(type(v) is str and v.startswith(n + ":[")
                    for n, v in ns.items()), "PARENT_NS_INVALID")
    return [
        "/usr/bin/sudo", "-n", "/usr/bin/unshare",
        "--net", "--mount", "--pid", "--fork", "--mount-proc",
        "/usr/bin/setpriv", "--reuid=65534", "--regid=65534",
        "--clear-groups", "--no-new-privs",
        "/usr/bin/python3", "-I", "-B", "-c", CHILD,
        root, json.dumps(ns, sort_keys=True),
    ]


def verify(result: dict) -> None:
    require(type(result) is dict and result.get("schema") == SCHEMA,
            "RECEIPT_SCHEMA_CHANGED")
    require(result.get("uid") == UID and type(result.get("uid")) is int,
            "CHILD_PRINCIPAL_NOT_65534")
    cases = result.get("cases")
    require(type(cases) is dict and set(cases) == set(KEYS)
            and all(cases[k] is True for k in KEYS), "BOUNDARY_NEGATIVE_FAILED")
    require(result.get("fixed_operator_literal") is True
            and result.get("model_source_executed") is False
            and result.get("core_signed_lease") is False
            and result.get("github_write_authority") is False,
            "FALSE_AGENT_AUTHORITY")


def selftest() -> dict:
    import copy
    parent = {n: n + ":[4026531840]" for n in ("net", "mnt", "pid")}
    sample_root = "/tmp/" + ROOT_PREFIX + "synthetic"
    argv = plan(sample_root, parent)
    required = {"--net", "--mount", "--pid", "--fork", "--mount-proc",
                "--reuid=65534", "--regid=65534", "--clear-groups",
                "--no-new-privs", "-I", "-B"}
    require(required <= set(argv) and argv.count("-c") == 1,
            "BOUNDARY_PLAN_MISSING")
    sample = {"schema": SCHEMA, "uid": UID, "cases": {k: True for k in KEYS},
              "fixed_operator_literal": True, "model_source_executed": False,
              "core_signed_lease": False, "github_write_authority": False}
    verify(sample)
    bad = []
    for k in KEYS:
        v = copy.deepcopy(sample)
        v["cases"][k] = False
        bad.append((k, v))
    for k, change in (
            ("fake-root", {"uid": 501}),
            ("fake-source", {"model_source_executed": True}),
            ("fake-lease", {"core_signed_lease": True}),
            ("fake-writer", {"github_write_authority": True})):
        bad.append((k, dict(sample, **change)))
    for k, row in bad:
        try:
            verify(row)
        except Refuse:
            pass
        else:
            raise Refuse("NEGATIVE_MUTATION_ACCEPTED_" + k)
    return {"status": "PASS_CP069_STATIC_NO_LIVE_GUEST",
            "mutation_denials": len(bad), "fixed_case_count": len(KEYS),
            "model_source_executed": False, "core_lease_issued": False,
            "git_write_calls": 0, "production_authority": False}


def run_guest() -> dict:
    require(os.environ.get("VF604_CP069_ALLOWED") == TOKEN,
            "EXPLICIT_DISPOSABLE_LAB_OPT_IN_REQUIRED")
    require(platform.system() == "Linux" and platform.machine() == "aarch64"
            and os.getuid() == 501 and os.geteuid() == 501,
            "REFUSE_UNEXPECTED_LINUX_GUEST_OR_USER")
    require(Path("/run/containerd/containerd.sock").is_socket(),
            "KNOWN_GUEST_SOCKET_NOT_FOUND")
    # This confirms the dangerous ambient socket is reachable by UID501.
    require(os.access("/run/containerd/containerd.sock", os.R_OK | os.W_OK),
            "NOT_THE_EXPECTED_SAME_UID_SOCKET_EXPOSURE")
    parent = {name: os.readlink("/proc/self/ns/" + name)
              for name in ("net", "mnt", "pid")}
    with tempfile.TemporaryDirectory(prefix=ROOT_PREFIX, dir="/tmp") as tmp:
        private = Path(tmp)
        private.chmod(0o700)
        canary = private / "synthetic-not-a-secret.txt"
        canary.write_text("fixed synthetic canary; zero real credentials")
        canary.chmod(0o600)
        cmd = plan(tmp, parent)
        environment = {"PATH": "/usr/bin:/bin", "LANG": "C",
                       "PYTHONDONTWRITEBYTECODE": "1"}
        complete = subprocess.run(cmd, cwd="/tmp", env=environment,
                                  stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True, timeout=15, close_fds=True)
        if complete.returncode:
            debug = json.loads(complete.stdout) if complete.stdout.startswith("{") else {}
            failed = [k for k, v in debug.get("cases", {}).items() if v is not True]
            raise Refuse("FIXED_CHILD_DENIAL_FAILED_" + ",".join(failed) +
                         "_STDERR_" + complete.stderr[-100:])
        row = json.loads(complete.stdout)
        verify(row)
        return {"schema": SCHEMA, "status": "PASS_NATIVE_FIXED_LOWPRIV_NS",
                "child": row, "guest_kernel": platform.release(),
                "guest_arch": platform.machine(),
                "controller_uid": os.getuid(), "controller_socket_risk": True,
                "child_uid": UID,
                "child_stdout_sha256": hashlib.sha256(
                    complete.stdout.encode("utf-8")).hexdigest(),
                "test_count": len(KEYS), "tests_passed": len(KEYS),
                "all_private_temp_cleaned_after_child": True,
                "source_role": "OPERATOR_FIXED_ONLY",
                "admitted_untrusted_executor": False,
                "core_signed_lease": False, "git_sink_writer": False,
                "production_authority": False}


def main() -> None:
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run-guest"),
            "ONLY_SELFTEST_OR_FIXED_GUEST_RUN")
    value = selftest() if sys.argv[1] == "selftest" else run_guest()
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refuse, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(exc)[:220],
                          "model_source_executed": False,
                          "core_signed_lease": False,
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(2)
