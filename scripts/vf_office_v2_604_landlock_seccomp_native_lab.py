#!/usr/bin/env python3
"""CP055: benign Linux aarch64 Landlock v4 + seccomp boundary probe.

LAB/QA ONLY. Does not execute LLM-generated code, issue a Core lease, or
grant production permission. Run once as an unprivileged Colima guest user.
"""
import ctypes
import datetime
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys

SCHEMA = "velvetos.office2.cp055.landlock-seccomp-native-lab.v1"
ROOT = Path("/tmp/office-p0-landlock-cp055-metadata-green")
SANDBOX = ROOT / "only-writable"
FIXTURE = SANDBOX / "fixed-synthetic-fixture.py"
OUTSIDE = ROOT / "outside-sentinel.txt"
RECEIPT = ROOT / "receipt.json"
SYSCALL_CREATE, SYSCALL_ADD, SYSCALL_RESTRICT = 444, 445, 446
O_PATH = 0o10000000
FS_EXEC, FS_WRITE, FS_READ, FS_DIR = (1 << 0), (1 << 1), (1 << 2), (1 << 3)
FS_MAKE_REG, FS_REMOVE_FILE, FS_TRUNCATE = (1 << 8), (1 << 5), (1 << 14)
FS_HANDLED = (1 << 15) - 1
NET_HANDLED = (1 << 0) | (1 << 1)
ARCH_AARCH64 = 0xC00000B7

FIXTURE_TEXT = '''import ctypes, errno, json, os, socket, subprocess, sys
from pathlib import Path
allowed=Path(sys.argv[1])
outside=Path(sys.argv[2])
cases={}
def denial(label, fn):
    try:
        fn()
        cases[label]=False
    except OSError as err:
        cases[label]=err.errno in (errno.EACCES,errno.EPERM)
def make_inside():
    p=allowed/"fixture-result.txt"
    p.write_text("synthetic CP055 fixed-only",encoding="utf8")
    return p.read_text(encoding="utf8")=="synthetic CP055 fixed-only"
cases["allowed_scratch_read_write"]=make_inside()
denial("denied_outside_sentinel_read",lambda:outside.read_text())
denial("denied_outside_chmod",lambda:os.chmod(outside,0o600))
denial("denied_outside_utime",lambda:os.utime(outside,None))
denial("denied_outside_tmp_write",lambda:(outside.parent/"outside-new.txt").write_text("DENY"))
denial("denied_rootful_containerd_directory",lambda:os.listdir("/run/containerd"))
denial("denied_unlisted_dev_file",lambda:open("/dev/urandom","rb").read(1))
denial("denied_proc_version",lambda:open("/proc/version","rb").read(1))
denial("denied_unix_socket_creation",lambda:socket.socket(socket.AF_UNIX,socket.SOCK_STREAM))
denial("denied_tcp_socket_creation",lambda:socket.socket(socket.AF_INET,socket.SOCK_STREAM))
denial("denied_udp_socket_creation",lambda:socket.socket(socket.AF_INET,socket.SOCK_DGRAM))
denial("denied_untrusted_child_spawn",lambda:subprocess.run(["/usr/bin/true"],check=True))
denial("denied_signal_even_to_self",lambda:os.kill(os.getpid(),0))
libc=ctypes.CDLL(None,use_errno=True)
cases["prctl_no_new_privs_set"]=libc.prctl(39,0,0,0,0)==1
cases["prctl_seccomp_filter_set"]=libc.prctl(21,0,0,0,0)==2
cases["allowed_read_only_python_binary"]=Path("/usr/bin/python3").open("rb").read(4)==bytes((127,69,76,70))
print(json.dumps({"cases":cases,"all_pass":all(cases.values()),"guest_id":os.getuid(),"fixture_only":True},sort_keys=True),flush=True)
raise SystemExit(0 if all(cases.values()) else 2)
'''

class RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs",ctypes.c_uint64),
                ("handled_access_net",ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _fields_ = [("allowed_access",ctypes.c_uint64),("parent_fd",ctypes.c_int32)]
class SockFilter(ctypes.Structure):
    _fields_ = [("code",ctypes.c_ushort),("jt",ctypes.c_ubyte),
                ("jf",ctypes.c_ubyte),("k",ctypes.c_uint32)]
class SockFprog(ctypes.Structure):
    _fields_ = [("len",ctypes.c_ushort),
                ("filter",ctypes.POINTER(SockFilter))]

def native(name, result):
    if result < 0:
        err=ctypes.get_errno()
        raise OSError(err,name+": "+os.strerror(err))
    return result

def confine():
    if platform.machine()!="aarch64" or os.geteuid()==0:
        raise RuntimeError("REQUIRES_NONROOT_AARCH64")
    libc=ctypes.CDLL(None,use_errno=True)
    abi=native("landlock_version",libc.syscall(SYSCALL_CREATE,ctypes.c_void_p(),0,1))
    if abi<4:raise RuntimeError("LANDLOCK_ABI_4_REQUIRED")
    # ABI v4: deny-by-default filesystem + TCP bind/connect actions.
    a=RulesetAttr(FS_HANDLED,NET_HANDLED)
    fd=native("landlock_create_ruleset",libc.syscall(
        SYSCALL_CREATE,ctypes.byref(a),ctypes.sizeof(a),0))
    try:
        permissions=[
          ("/usr",FS_READ|FS_DIR|FS_EXEC),
          (str(SANDBOX),FS_READ|FS_DIR|FS_WRITE|FS_MAKE_REG|FS_REMOVE_FILE|FS_TRUNCATE),
          ("/dev/null",FS_READ|FS_WRITE)]
        for name,bits in permissions:
            path_fd=os.open(name,O_PATH|os.O_CLOEXEC)
            try:
                rule=PathRule(bits,path_fd)
                native("landlock_add_rule:"+name,libc.syscall(
                    SYSCALL_ADD,fd,1,ctypes.byref(rule),0))
            finally:os.close(path_fd)
        native("PR_SET_NO_NEW_PRIVS",libc.prctl(38,1,0,0,0))
        native("landlock_restrict_self",libc.syscall(SYSCALL_RESTRICT,fd,0))
    finally:os.close(fd)

    # Native ARM64 syscall numbers; deny sockets (including UNIX path sockets
    # not covered by Landlock ABI4), process spawning/signals and io_uring.
    denied={
      39,40,41,97,117,129,130,131,198,199,200,201,202,203,204,205,
      206,207,208,209,210,211,212,220,241,242,268,270,271,
      280,282,424,425,426,427,428,429,430,431,432,433,434,435,438}
    # ABI4 Landlock cannot block these same-UID metadata mutations; explicitly
    # deny them in seccomp, including fchmodat2 and prlimit64 on other PIDs.
    denied.update({5,6,7,14,15,16,52,53,54,55,88,119,122,140,261,452})
    # Userland syscalls unrelated to the policy are allowed only within
    # this one-shot LAB. This is NOT a hardened production seccomp profile.
    filters=[SockFilter(0x20,0,0,4),SockFilter(0x15,1,0,ARCH_AARCH64),
             SockFilter(0x06,0,0,0x80000000),SockFilter(0x20,0,0,0)]
    for number in sorted(denied):
        filters.append(SockFilter(0x15,0,1,number))
        filters.append(SockFilter(0x06,0,0,0x00050000|errno.EPERM))
    filters.append(SockFilter(0x06,0,0,0x7fff0000))
    buf=(SockFilter*len(filters))(*filters)
    p=SockFprog(len(filters),buf)
    resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(3,4))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    native("PR_SET_SECCOMP_FILTER",libc.prctl(22,2,ctypes.byref(p),0,0))
    # No subprocess/tool executor. Fixed source, no model output.
    env={"PATH":"/usr/bin","LANG":"C","PYTHONNOUSERSITE":"1",
         "PYTHONDONTWRITEBYTECODE":"1"}
    os.execve("/usr/bin/python3",["/usr/bin/python3","-B",str(FIXTURE),
             str(SANDBOX),str(OUTSIDE)],env)

def parent():
    if platform.machine()!="aarch64" or os.geteuid()==0 or not ROOT.is_dir():
        raise SystemExit("REFUSE_WRONG_GUEST_OR_ROOT")
    if RECEIPT.exists() or OUTSIDE.exists() or SANDBOX.exists():
        raise SystemExit("REFUSE_EXPERIMENT_COLLISION")
    if os.stat(ROOT).st_uid!=os.getuid():
        raise SystemExit("REFUSE_NONOWNED_ROOT")
    SANDBOX.mkdir(mode=0o700)
    FIXTURE.write_text(FIXTURE_TEXT,encoding="utf-8")
    OUTSIDE.write_text("DO_NOT_ALLOW",encoding="utf-8")
    try:
        run=subprocess.run(["/usr/bin/python3","-B",str(Path(__file__)),
              "--child"],cwd=str(SANDBOX),env={"PATH":"/usr/bin","LANG":"C"},
              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,text=True,timeout=10,close_fds=True)
        parsed=json.loads(run.stdout) if run.stdout.startswith("{") else {}
        results=parsed.get("cases",{})
        receipt={"schema":SCHEMA,"host":platform.node(),"abi":4,
             "kernel":platform.release(),"uid":os.getuid(),
             "status":"PASS_NATIVE_BOUNDARY_ONLY" if
               run.returncode==0 and parsed.get("all_pass") and
               len(results)==16 else "FAIL_CLOSED",
             "child_exit":run.returncode,"fixture_sha256":
                 hashlib.sha256(FIXTURE_TEXT.encode()).hexdigest(),
             "case_count":len(results),"passed":sum(x is True for x in results.values()),
             "cases":results,
             "landlock_runtime":"ABI4_FS_AND_TCP_DENY",
             "seccomp_runtime":"ARM64_CLASSIC_BPF_DENY_SOCKET_FORK_SIGNALS_IOURING",
             "rootful_containerd_socket_used":False,
             "model_generated_code_executed":False,"core_signed_lease":False,
             "production_sandbox_admitted":False,
             "missing_controls":["LANDLOCK_ABI4_UNIX_AND_SIGNAL_SCOPES",
               "FULL_SECCOMP_AUDIT","DEDICATED_OS_UID",
               "CORE_LEASE_FENCING","RECOVERY"]}
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:receipt[k] for k in
              ("status","case_count","passed","abi","uid")},sort_keys=True))
        print("RECEIPT_SHA256="+hashlib.sha256(RECEIPT.read_bytes()).hexdigest())
        if receipt["status"]!="PASS_NATIVE_BOUNDARY_ONLY":
            print("FAILURE_CHILD_STDERR="+run.stderr[-900:])
            raise SystemExit(2)
    finally:
        if OUTSIDE.exists():OUTSIDE.unlink()

if __name__=="__main__":
    if sys.argv[1:]==["--child"]:confine()
    elif not sys.argv[1:]:parent()
    else:raise SystemExit("NO_OTHER_MODES")
