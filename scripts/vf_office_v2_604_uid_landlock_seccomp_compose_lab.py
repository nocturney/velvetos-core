#!/usr/bin/env python3
"""CP071 fixed-only native ARM64 isolation composition (NO model/lease/Git).

A pre-written synthetic fixture runs with real UID65534 in private net/mount/pid
namespaces, plus Linux Landlock ABI4 and classic ARM64 Seccomp. The parent
starts a fixed command in an existing disposable Linux guest. This is NOT an
admitted general-purpose agent executor, hardened VM or Core #604 lease.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

SCHEMA = "velvetos.office-v2.604.uid-landlock-seccomp-composed.v1"
PREFIX = "vf604-cp071-fixed-"
CONSENT = "VF604_CP071_FIXED_GUEST_ONLY"
UID = 65534
KEYS = (
    "lowpriv_uid", "groups_empty", "capabilities_zero", "no_new_privs",
    "different_netns", "different_mountns", "different_pidns",
    "no_ipv4_routes", "no_inherited_containerd_fd",
    "containerd_dac_denied", "private_synthetic_canary_denied",
    "outside_world_readable_before_policy",
    "outside_world_writable_before_policy",
    "landlock_abi4", "seccomp_filter_active", "read_usr_python_allowed",
    "inside_scratch_rw_allowed", "outside_read_landlock_denied",
    "outside_write_landlock_denied", "outside_chmod_seccomp_denied",
    "outside_utime_seccomp_denied", "proc_version_read_denied",
    "tcp_socket_seccomp_denied", "unix_socket_seccomp_denied",
    "fork_seccomp_denied", "execve_seccomp_denied",
    "execveat_seccomp_denied", "signal_seccomp_denied",
    "no_credential_environment", "limits_active",
    "prlimit_query_seccomp_denied",
)
CHILD = r'''
import ctypes, errno, json, os, pathlib, platform, resource, socket, subprocess, sys
scratch=pathlib.Path(sys.argv[1])
outside=pathlib.Path(sys.argv[2])
private=pathlib.Path(sys.argv[3])
parent=json.loads(sys.argv[4])
cases={}
def check(name, result):
    cases[name]=(result is True)
def ns(name):
    return os.readlink("/proc/self/ns/"+name)
check("lowpriv_uid",os.getuid()==65534 and os.geteuid()==65534)
check("groups_empty",os.getgroups()==[])
st={}
for line in pathlib.Path("/proc/self/status").read_text().splitlines():
    if line.startswith(("CapEff:", "NoNewPrivs:")):
        key, value=line.split(":",1)
        st[key]=value.strip()
check("capabilities_zero",int(st.get("CapEff","1"),16)==0)
check("no_new_privs",st.get("NoNewPrivs")=="1")
for name,key in (("net","different_netns"),("mnt","different_mountns"),("pid","different_pidns")):
    check(key,ns(name)!=parent[name])
routes=pathlib.Path("/proc/net/route").read_text().splitlines()
check("no_ipv4_routes",len(routes)==0 or
      (len(routes)==1 and routes[0].startswith("Iface")))
fds=[]
for fid in os.listdir("/proc/self/fd"):
    try: fds.append(os.readlink("/proc/self/fd/"+fid))
    except OSError: pass
check("no_inherited_containerd_fd",not any("containerd" in target for target in fds))
def denied(label, action):
    try: action()
    except OSError as exc:
        check(label,exc.errno in (errno.EACCES,errno.EPERM,errno.ENOENT))
    else: check(label,False)
sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
try:
    err=sock.connect_ex("/run/containerd/containerd.sock")
finally: sock.close()
check("containerd_dac_denied",err in (errno.EACCES,errno.EPERM,errno.ENOENT))
denied("private_synthetic_canary_denied",lambda: (private/"private-canary").read_bytes())
# Prove this is NOT a mere POSIX file permission denial.
check("outside_world_readable_before_policy",
      outside.read_text()=="FIXED_PUBLIC_SYNTHETIC_OUTSIDE")
check("outside_world_writable_before_policy",
      os.access(outside,os.R_OK|os.W_OK))
libc=ctypes.CDLL(None,use_errno=True)
def sysok(name,val):
    if val<0:
        e=ctypes.get_errno()
        raise OSError(e,name+": "+os.strerror(e))
    return val
abi=sysok("landlock_abi",libc.syscall(444,ctypes.c_void_p(),0,1))
check("landlock_abi4",abi>=4)
if abi<4: raise SystemExit("LANDLOCK_ABI4_REQUIRED")
class Rules(ctypes.Structure):
    _fields_=[("fs",ctypes.c_uint64),("net",ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _fields_=[("allowed",ctypes.c_uint64),("fd",ctypes.c_int32)]
class F(ctypes.Structure):
    _fields_=[("code",ctypes.c_ushort),("jt",ctypes.c_ubyte),
              ("jf",ctypes.c_ubyte),("k",ctypes.c_uint32)]
class Prog(ctypes.Structure):
    _fields_=[("length",ctypes.c_ushort),("filter",ctypes.POINTER(F))]
READ,WRITE,EXEC,DIR=4,2,1,8
MAKE,REMOVE,TRUNC=(1<<8),(1<<5),(1<<14)
ruleset=Rules((1<<15)-1,3)
fd=sysok("landlock_create_ruleset",libc.syscall(
    444,ctypes.byref(ruleset),ctypes.sizeof(ruleset),0))
try:
    grants=(("/usr",READ|DIR|EXEC),
            (str(scratch),READ|DIR|WRITE|MAKE|REMOVE|TRUNC),
            ("/dev/null",READ|WRITE))
    for path,mask in grants:
        pathfd=os.open(path,0o10000000|os.O_CLOEXEC)
        try:
            rule=PathRule(mask,pathfd)
            sysok("landlock_add_path",libc.syscall(
                445,fd,1,ctypes.byref(rule),0))
        finally:
            os.close(pathfd)
    sysok("landlock_no_new_privileges",libc.prctl(38,1,0,0,0))
    sysok("landlock_restrict_self",libc.syscall(446,fd,0))
finally:
    os.close(fd)
# Fixed ARM64 system call denial policy from CP055/CP056 red-green.
# Explicitly blocks execve, execveat, socket, clone/fork, signals, io_uring
# and metadata chmod/utime syscall variants missing from Landlock ABI4.
deny={
    39,40,41,97,117,129,130,131,198,199,200,201,202,203,204,205,
    206,207,208,209,210,211,212,220,241,242,268,270,271,280,282,
    424,425,426,427,428,429,430,431,432,433,434,435,438,
    5,6,7,14,15,16,52,53,54,55,88,119,122,140,221,261,281,452
}
filters=[F(0x20,0,0,4),F(0x15,1,0,0xC00000B7),
         F(0x06,0,0,0x80000000),F(0x20,0,0,0)]
for n in sorted(deny):
    filters.append(F(0x15,0,1,n))
    filters.append(F(0x06,0,0,0x00050000|errno.EPERM))
filters.append(F(0x06,0,0,0x7fff0000))
buf=(F*len(filters))(*filters)
prog=Prog(len(filters),buf)
resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU,(3,4))
resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
limits_confirmed=resource.getrlimit(resource.RLIMIT_AS)[0]==384*1024*1024
sysok("seccomp_install",libc.prctl(22,2,ctypes.byref(prog),0,0))
check("seccomp_filter_active",libc.prctl(21,0,0,0,0)==2)
check("read_usr_python_allowed",
      pathlib.Path("/usr/bin/python3").open("rb").read(4)==bytes((127,69,76,70)))
inside=scratch/"scratch-result.txt"
inside.write_text("CP071_FIXED_ONLY")
check("inside_scratch_rw_allowed",inside.read_text()=="CP071_FIXED_ONLY")
denied("outside_read_landlock_denied",lambda:outside.read_bytes())
denied("outside_write_landlock_denied",lambda:outside.write_text("SHOULD_NOT_WRITE"))
denied("outside_chmod_seccomp_denied",lambda:os.chmod(outside,0o600))
denied("outside_utime_seccomp_denied",lambda:os.utime(outside,None))
denied("proc_version_read_denied",lambda:pathlib.Path("/proc/version").read_bytes())
denied("tcp_socket_seccomp_denied",lambda:socket.socket(socket.AF_INET,socket.SOCK_STREAM))
denied("unix_socket_seccomp_denied",lambda:socket.socket(socket.AF_UNIX,socket.SOCK_STREAM))
denied("fork_seccomp_denied",lambda:subprocess.run(["/usr/bin/true"],check=True))
denied("execve_seccomp_denied",
       lambda:os.execve("/usr/bin/true",["/usr/bin/true"],{"PATH":"/usr/bin"}))
def execveat():
    argv=(ctypes.c_char_p*2)(b"/usr/bin/true",None)
    envp=(ctypes.c_char_p*1)(None)
    outcome=libc.syscall(281,ctypes.c_int(-100),
            ctypes.c_char_p(b"/usr/bin/true"),
            ctypes.byref(argv),ctypes.byref(envp),ctypes.c_int(0))
    if outcome<0: raise OSError(ctypes.get_errno(),"execveat")
denied("execveat_seccomp_denied",execveat)
denied("signal_seccomp_denied",lambda:os.kill(os.getpid(),0))
check("no_credential_environment",not any(
    k in os.environ for k in ("GH_TOKEN","GITHUB_TOKEN","SSH_AUTH_SOCK",
                              "GOOGLE_APPLICATION_CREDENTIALS")))
check("limits_active",limits_confirmed)
denied("prlimit_query_seccomp_denied",lambda:resource.getrlimit(resource.RLIMIT_AS))
print(json.dumps({"cases":cases,"kernel":platform.release(),
                  "arch":platform.machine(),"uid":os.getuid(),
                  "landlock_abi":abi,
                  "source_role":"FIXED_OPERATOR_LITERAL",
                  "model_source_executed":False,
                  "core_signed_lease":False,
                  "git_write_authority":False},sort_keys=True),flush=True)
raise SystemExit(0 if all(cases.values()) and len(cases)==31 else 2)
'''


class Refuse(Exception):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise Refuse(reason)


def plan(root: str, parent: dict) -> list[str]:
    need(type(root) is str and root.startswith("/tmp/" + PREFIX)
         and len(root)<200 and "\n" not in root, "UNOWNED_OR_UNSAFE_TEMP_ROOT")
    need(type(parent) is dict and set(parent)=={"net","mnt","pid"}
         and all(type(x) is str and x.startswith(k+":[")
                 for k,x in parent.items()), "PARENT_NAMESPACE_NOT_PINNED")
    return [
        "/usr/bin/sudo", "-n", "/usr/bin/unshare",
        "--net","--mount","--pid","--fork","--mount-proc",
        "/usr/bin/setpriv","--reuid=65534","--regid=65534",
        "--clear-groups","--no-new-privs",
        "/usr/bin/python3","-I","-B","-c",CHILD,
        root+"/allow",root+"/outside/public-canary",
        root+"/private",json.dumps(parent,sort_keys=True)
    ]


def verify(row: dict) -> None:
    need(type(row) is dict and row.get("uid")==UID
         and type(row.get("uid")) is int, "NOT_SEPARATE_UID")
    cases=row.get("cases")
    need(type(cases) is dict and set(cases)==set(KEYS)
         and all(cases[k] is True for k in KEYS),
         "NATIVE_UID_FS_NET_SYSCALL_NEGATIVE_FAILED")
    need(type(row.get("landlock_abi")) is int and row["landlock_abi"]>=4
         and row.get("arch")=="aarch64"
         and row.get("source_role")=="FIXED_OPERATOR_LITERAL"
         and row.get("model_source_executed") is False
         and row.get("core_signed_lease") is False
         and row.get("git_write_authority") is False,
         "FALSE_GENERAL_AGENT_OR_LEASE_ADMISSION")


def selftest() -> dict:
    sample={"uid":UID,"arch":"aarch64","landlock_abi":4,
            "source_role":"FIXED_OPERATOR_LITERAL",
            "cases":{k:True for k in KEYS},
            "model_source_executed":False,
            "core_signed_lease":False,"git_write_authority":False}
    verify(sample)
    neg=[]
    for key in KEYS:
        altered=copy.deepcopy(sample)
        altered["cases"][key]=False
        neg.append((key,altered))
    for name,fields in (
        ("root_uid",{"uid":0}),
        ("unknown_arch",{"arch":"x86_64"}),
        ("abi3",{"landlock_abi":3}),
        ("generated_code",{"model_source_executed":True}),
        ("core_lease_claim",{"core_signed_lease":True}),
        ("git_writer_claim",{"git_write_authority":True}),
        ("bad_source_role",{"source_role":"ARBITRARY_MODEL"})):
        neg.append((name,dict(sample,**fields)))
    for name,row in neg:
        try: verify(row)
        except Refuse: pass
        else: raise Refuse("UNSAFE_MUTANT_ADMITTED_"+name)
    command=plan("/tmp/"+PREFIX+"static",{
        n:n+":[4026531840]" for n in ("net","mnt","pid")})
    for flag in ("--net","--mount","--pid","--fork","--mount-proc",
                 "--reuid=65534","--regid=65534","--clear-groups",
                 "--no-new-privs","-I","-B"):
        need(flag in command,"MISSING_NAMESPACE_OR_LOWPRIV_"+flag)
    need(command.count("-c")==1, "UNBOUNDED_GUEST_ENTRY")
    return {"status":"PASS_CP071_COMPOSED_STATIC_ONLY",
            "negative_mutations":len(neg),"native_cases":len(KEYS),
            "fixed_literal_sha256":hashlib.sha256(CHILD.encode()).hexdigest(),
            "model_source_executed":False,"core_signed_lease":False,
            "git_write_calls":0,"production_authority":False}


def run_guest() -> dict:
    need(os.environ.get("VF604_CP071_ALLOWED")==CONSENT,
         "DISPOSABLE_FIXED_GUEST_OPT_IN_MISSING")
    need(platform.system()=="Linux" and platform.machine()=="aarch64"
         and os.getuid()==501 and os.geteuid()==501,
         "REFUSE_NOT_EXISTING_501_ARM64_LAB_GUEST")
    need(Path("/run/containerd/containerd.sock").is_socket()
         and os.access("/run/containerd/containerd.sock",os.R_OK|os.W_OK),
         "EXPECTED_ROOTFUL_SOCKET_RISK_NOT_GROUNDED")
    namespace={name:os.readlink("/proc/self/ns/"+name)
               for name in ("net","mnt","pid")}
    with tempfile.TemporaryDirectory(prefix=PREFIX,dir="/tmp") as temp:
        root=Path(temp)
        root.chmod(0o755)
        allowed=root/"allow"
        allowed.mkdir(mode=0o777)
        allowed.chmod(0o777)
        public=root/"outside"
        public.mkdir(mode=0o777)
        public.chmod(0o777)
        outside=public/"public-canary"
        outside.write_text("FIXED_PUBLIC_SYNTHETIC_OUTSIDE")
        outside.chmod(0o666)
        priv=root/"private"
        priv.mkdir(mode=0o700)
        (priv/"private-canary").write_text("SYNTHETIC_NEVER_SECRET")
        cmd=plan(temp,namespace)
        environment={"PATH":"/usr/bin:/bin","LANG":"C",
                     "PYTHONDONTWRITEBYTECODE":"1"}
        proc=subprocess.run(cmd,env=environment,cwd="/tmp",
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                            text=True,timeout=18,close_fds=True)
        parsed=json.loads(proc.stdout) if proc.stdout.startswith("{") else {}
        if proc.returncode:
            failures=[k for k,v in parsed.get("cases",{}).items() if v is not True]
            raise Refuse("COMPOSED_NATIVE_CHILD_FAILED_"+
                         str(proc.returncode)+"_"+
                         ",".join(failures)+"_"+
                         proc.stderr[-130:])
        verify(parsed)
        need(outside.read_text()=="FIXED_PUBLIC_SYNTHETIC_OUTSIDE",
             "OUTSIDE_CHANGED_WHILE_CONFINED")
        return {
          "schema":SCHEMA,"status":"PASS_NATIVE_UID_LL_SECCOMP_COMPOSED",
          "live_checks":len(KEYS),"live_passes":len(KEYS),
          "native_guest":platform.node(),"kernel":platform.release(),
          "parent_uid":os.getuid(),"child_uid":UID,
          "source_role":"OPERATOR_FIXED_ONLY",
          "child_stdout_sha256":hashlib.sha256(
              proc.stdout.encode()).hexdigest(),
          "child":parsed,
          "ambient_rootful_socket_present_parent":True,
          "model_source_executed":False,
          "core_exclusive_signed_lease_issued":False,
          "github_sink_effect":False,
          "general_sandbox_admitted":False,
          "production_authority":False,
          "only_owned_synthetic_temp_files":True
        }


def main() -> None:
    need(len(sys.argv)==2 and sys.argv[1] in ("selftest","run-guest"),
         "ONLY_FIXED_SOURCE_MODES")
    result=selftest() if sys.argv[1]=="selftest" else run_guest()
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refuse,OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:240],
             "model_source_executed":False,
             "production_authority":False},sort_keys=True))
        raise SystemExit(2)
