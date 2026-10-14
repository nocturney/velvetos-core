#!/usr/bin/env python3
"""#604 CP055 read-only historical Landlock+Seccomp LAB evidence verifier.

No runtime sandbox setup, no model invocation, no Core lease, no filesystem
mutation except standard Python output. A PASS is a content/hash check ONLY.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
NATIVE=ROOT/"scripts/vf_office_v2_604_landlock_seccomp_native_lab.py"
EVIDENCE=ROOT/"docs/implementation/office-v2/phase2/p0-604-landlock-seccomp-boundary-cp055-2026-10-14.json"
SCHEMA="velvetos.office-v2.604.landlock-seccomp-boundary-lab.v1"
EXPECTED_NATIVE_SHA="362b77b0b64c1da40ea875fb38126a3039ece658fe81710f35dd7aeb527ad45e"
CASES={
 "allowed_scratch_read_write","denied_outside_sentinel_read",
 "denied_outside_chmod","denied_outside_utime","denied_outside_tmp_write",
 "denied_rootful_containerd_directory","denied_unlisted_dev_file",
 "denied_proc_version","denied_unix_socket_creation",
 "denied_tcp_socket_creation","denied_udp_socket_creation",
 "denied_untrusted_child_spawn","denied_signal_even_to_self",
 "prctl_no_new_privs_set","prctl_seccomp_filter_set",
 "allowed_read_only_python_binary"}
NEGATIVES={
 "model_called","model_generated_code_executed",
 "rootful_containerd_socket_used","new_guest_created",
 "host_global_security_settings_changed","core_signed_lease",
 "protected_git_writer_admitted","production_sandbox_admitted",
 "receipt_cryptographically_attested",
 "independent_cgroup_memory_enforcement_proven"}
ROOT_KEYS={
 "schema","date","owner_issue","consumer_issue","scope","status",
 "main_base_sha","physical_host","guest","guest_kernel","guest_arch",
 "guest_uid","landlock_abi","mechanism","native_source_sha256",
 "expected_cases","red","green","negative_context",
 "required_before_runtime","evidence_kind"}
RUN_KEYS={"source_sha256","receipt_sha256","status","exit_code",
          "case_count","passed","unexpectedly_allowed"}
REQUIRED_GATES={
 "DEDICATED_PRINCIPAL_OR_GUEST_SEPARATION",
 "LANDLOCK_ABI4_UNIX_SIGNAL_AND_METADATA_COVERAGE_AUDIT",
 "SECCOMP_SYSCALL_COVERAGE_AND_KERNEL_BYPASS_REVIEW",
 "MOUNT_AND_PREOPENED_FD_IPC_REVIEW",
 "CORE_604_SIGNED_TASK_HOST_RESOURCE_LEASE_FENCING",
 "INDEPENDENT_MODEL_AUTHORED_PATCH_QA_AND_GIT_EFFECT_RECONCILE"}

class Denied(Exception):
    pass
def require(condition, reason):
    if not condition:raise Denied(reason)
def pin_sha(value):
    return type(value) is str and len(value)==64 and all(x in "0123456789abcdef" for x in value)
def exact_parts(record, native_bytes=None):
    require(type(record) is dict and set(record)==ROOT_KEYS,"TOP_LEVEL_SHAPE")
    require(record["schema"]==SCHEMA and record["date"]=="2026-10-14","IDENTITY")
    require(record["owner_issue"]==604 and type(record["owner_issue"]) is int
       and record["consumer_issue"]==612 and type(record["consumer_issue"]) is int,
       "WRONG_CANONICAL_OWNER")
    require(record["scope"]=="NONPRODUCTION_FIXED_SYNTHETIC_LINUX_ARM64_NATIVE_BOUNDARY_TEST"
       and record["status"]=="LAB_ONLY_RED_TO_GREEN_NO_WORKER_ADMISSION",
       "FALSE_RUNTIME_PROMOTION")
    require(record["main_base_sha"]=="f7995aff4569ca14224c6cef4b5004f7a38d54b7",
       "BASE_SHA_DRIFT")
    require(record["physical_host"]=="MacMiniOffice2.local"
       and record["guest"]=="colima-velvet-qa"
       and record["guest_kernel"]=="6.8.0-117-generic"
       and record["guest_arch"]=="aarch64"
       and type(record["guest_uid"]) is int and record["guest_uid"]==501
       and type(record["landlock_abi"]) is int and record["landlock_abi"]==4,
       "HOST_OR_ABI_DRIFT")
    require(type(record["expected_cases"]) is list
       and len(record["expected_cases"])==16
       and set(record["expected_cases"])==CASES
       and all(type(c) is str for c in record["expected_cases"]), "CASES_CHANGED")
    require(type(record["mechanism"]) is list
       and len(record["mechanism"])==4
       and all(type(c) is str and c for c in record["mechanism"]),
       "MECHANISM_SHAPE")
    require(record["native_source_sha256"]==EXPECTED_NATIVE_SHA
       and pin_sha(record["native_source_sha256"]),
       "NATIVE_SOURCE_MISMATCH")
    if native_bytes is not None:
        require(hashlib.sha256(native_bytes).hexdigest()==EXPECTED_NATIVE_SHA,
                "SOURCE_BYTES_UNVERIFIED")
    for name,expected_status,expected_exit,expected_pass,expected_sha,expected_receipt in (
        ("red","FAIL_CLOSED",2,14,
         "8822b072d0dab3c235f2f4b27f2a6456d6343eda1e6947d1fe29f7c322642fbb",
         "ff126e5fd88384156306e54a4e824f982d8311ba0186c3392ea6578bf8ce9b67"),
        ("green","PASS_NATIVE_BOUNDARY_ONLY",0,16,EXPECTED_NATIVE_SHA,
         "374ec43fc3bd9bfeab56e16746d4c65ad9e862abb04a64ad45f8f0b0e1965262")):
        row=record[name]
        require(type(row) is dict and set(row)==RUN_KEYS,"RUN_SHAPE_"+name)
        require(row["status"]==expected_status
             and type(row["exit_code"]) is int and row["exit_code"]==expected_exit
             and type(row["case_count"]) is int and row["case_count"]==16
             and type(row["passed"]) is int and row["passed"]==expected_pass,
             "RUN_RESULT_"+name)
        require(row["source_sha256"]==expected_sha
             and row["receipt_sha256"]==expected_receipt
             and pin_sha(row["source_sha256"]) and pin_sha(row["receipt_sha256"]),
             "RUN_PIN_"+name)
        expected_fail={"denied_outside_chmod","denied_outside_utime"} if name=="red" else set()
        require(type(row["unexpectedly_allowed"]) is list
           and all(type(x) is str for x in row["unexpectedly_allowed"])
           and set(row["unexpectedly_allowed"])==expected_fail
           and len(row["unexpectedly_allowed"])==len(expected_fail),
           "RUN_DENIED_CASES_"+name)
    flags=record["negative_context"]
    require(type(flags) is dict and set(flags)==NEGATIVES
       and all(type(flags[k]) is bool and flags[k] is False for k in NEGATIVES),
       "AUTHORITY_OR_EFFECT_FABRICATION")
    require(type(record["required_before_runtime"]) is list
       and set(record["required_before_runtime"])==REQUIRED_GATES
       and len(record["required_before_runtime"])==len(REQUIRED_GATES),
       "RUNTIME_GATES_MISSING")
    require(record["evidence_kind"]=="OPERATOR_HASHES_AND_SYNTHETIC_RECEIPT_CLAIMS_NOT_SIGNED_ATTESTATION",
       "FALSE_SIGNATURE_CLAIM")
    return {"status":"PASS_EVIDENCE_STRUCTURE_ONLY_NOT_AUTHORITY",
        "case_count":16,"red_passed":14,"green_passed":16,
        "model_executed":False,"core_lease_admitted":False,
        "real_guest_boundary_native_trace_authenticated":False}

def mutate_fixture(doc,field,value):
    copydoc=copy.deepcopy(doc)
    if type(field) is tuple:
        target=copydoc
        for item in field[:-1]:target=target[item]
        target[field[-1]]=value
    else:copydoc[field]=value
    return copydoc

def selftest(doc,native):
    results=[]
    def deny(tag,mutation):
        trial=mutation()
        try:exact_parts(trial,native)
        except Denied:
            results.append((tag,True));return
        results.append((tag,False))
    for field,value in [
       ("schema","FAKE"),("date","2026-10-13"),
       ("owner_issue",612),("consumer_issue",604),
       ("status","READY_FOR_PRODUCTION"),("scope","AUTONOMOUS_WORKER"),
       ("main_base_sha","0"*40),("guest","unknown"),
       ("guest_kernel","0"),("guest_arch","x86_64"),
       ("guest_uid",0),("landlock_abi",True),
       ("native_source_sha256","0"*64),
       ("expected_cases",["allowed_scratch_read_write"]),
       ("mechanism",[]),("required_before_runtime",[]),
       ("evidence_kind","SIGNED_LEASE"),
       (("red","status"),"PASS_NATIVE_BOUNDARY_ONLY"),
       (("red","passed"),16),(("red","case_count"),15),
       (("red","source_sha256"),"0"*64),
       (("red","receipt_sha256"),"0"*64),
       (("red","unexpectedly_allowed"),[]),
       (("green","exit_code"),2),(("green","passed"),15),
       (("green","receipt_sha256"),"0"*64),
       (("green","unexpectedly_allowed"),["denied_outside_chmod"]),
       (("negative_context","core_signed_lease"),True),
       (("negative_context","production_sandbox_admitted"),True),
       (("negative_context","model_generated_code_executed"),True),
       (("negative_context","receipt_cryptographically_attested"),True),
       (("negative_context","rootful_containerd_socket_used"),True)]:
        deny(str(field),lambda k=field,v=value:mutate_fixture(doc,k,v))
    deny("unknown_promotion_field",lambda:dict(doc,admitted=True))
    deny("bool_red_pass_count",lambda:mutate_fixture(doc,("red","passed"),True))
    try:exact_parts(doc,b"not-the-pinned-source")
    except Denied:results.append(("source_bytes_modified",True))
    else:results.append(("source_bytes_modified",False))
    total=len(results);passed=sum(x[1] for x in results)
    require(passed==total,"NEGATIVE_FIXTURE_ESCAPE")
    return {"status":"PASS_OFFLINE_ONLY","negative_denials_passed":passed,
            "negative_denials_total":total,
            "native_execution":False,"authority_admitted":False}

def main():
    try:
        doc=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        native=NATIVE.read_bytes()
        result=exact_parts(doc,native)
        if sys.argv[1:]==["--selftest"]:
            result=selftest(doc,native)
        elif sys.argv[1:] not in ([],["--check"]):
            raise Denied("UNSUPPORTED_MODE")
        print(json.dumps(result,sort_keys=True))
    except (Denied,ValueError,OSError,TypeError,KeyError) as e:
        print(json.dumps({"status":"DENIED","reason":type(e).__name__,
             "authority_admitted":False},sort_keys=True))
        raise SystemExit(2)
if __name__=="__main__":main()
