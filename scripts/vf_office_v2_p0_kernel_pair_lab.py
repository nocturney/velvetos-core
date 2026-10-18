#!/usr/bin/env python3
"""Disposable process-identity pair probe. No model, network, kill or retry."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
import vf_office_v2_p0_kernel_identity as ident

HERE=Path(__file__).resolve().parent
ROOT=None
SOURCE=HERE/"vf_office_v2_p0_kernel_identity.py"


def seal(x):
    return ident.digest(x)


def main():
    import argparse
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    args=ap.parse_args()
    workspace=Path(args.workspace)
    if not workspace.is_absolute() or not workspace.is_dir():
        raise RuntimeError("ABSOLUTE_EXISTING_WORKSPACE_REQUIRED")
    source_root=HERE.parent if (HERE.parent/".git").exists() else HERE
    if workspace.resolve().is_relative_to(source_root):
        raise RuntimeError("WORKSPACE_MUST_BE_OUTSIDE_SOURCE_REPO")
    ROOT=workspace.resolve()/"synthetic-pair-probe"
    if ROOT.exists():
        raise RuntimeError("NO_REUSE_OF_EXISTING_PROBE")
    ROOT.mkdir()
    work=ROOT/"isolated-synthetic-fixture"
    work.mkdir()
    pidfile=ROOT/"ids.json"
    parentfile=ROOT/"synthetic-parent.py"
    parentfile.write_text(
        "import json,os,subprocess,sys,time\n"
        "from pathlib import Path\n"
        "args={'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL}\n"
        "if os.name=='nt':args['creationflags']=subprocess.CREATE_NEW_PROCESS_GROUP\n"
        "else:args['start_new_session']=True\n"
        "child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(22)'],**args)\n"
        "Path(sys.argv[1]).write_text(json.dumps({'worker_pid':os.getpid(),"
        "'aider_role_pid':child.pid}),encoding='utf-8')\n"
        "child.wait(timeout=30)\n"
        "time.sleep(1)\n",
        encoding="utf-8")
    proc=subprocess.Popen([sys.executable,"-B",str(parentfile),str(pidfile)],
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    started=time.monotonic()
    while time.monotonic()-started<5 and not pidfile.exists():
        if proc.poll() is not None:
            raise RuntimeError("SYNTHETIC_PARENT_EXITED_EARLY")
        time.sleep(.05)
    if not pidfile.exists():
        raise RuntimeError("CHILD_IDENTITY_FILE_NOT_WRITTEN")
    ids=json.loads(pidfile.read_text(encoding="utf-8"))
    assert ids["worker_pid"]==proc.pid
    env={
      "schema":ident.ENVELOPE,"authority":ident.AUTHORITY,"issue_url":ident.ISSUE,
      "task_id":"p0-native-process-birth-synthetic-001",
      "host":platform.node(),"worktree_path":str(work),
      "budget":{"max_attempts":1,"max_cost_usd":0},
      "executor":{"kind":ident.KIND,"synthetic_process_only":True},
    }
    envelope=ROOT/"envelope.json"
    envelope.write_text(json.dumps(env,indent=2)+"\n",encoding="utf-8")
    receipt=ROOT/"receipt.json"
    journal=ROOT/"receipt.json.running"
    started_at=datetime.now(timezone.utc).isoformat()
    journal.write_text(json.dumps({
      "state":"RUNNING","unknown_outcome_rule":"NO_BLIND_RETRY",
      "task_id":env["task_id"],"host":env["host"],"kind":ident.KIND,
      "envelope_sha256":seal(env),"started_at":started_at
    },indent=2)+"\n",encoding="utf-8")
    pinned=ROOT/"kernel-pin.json"
    cap=subprocess.run([sys.executable,"-B",str(SOURCE),"capture",
      "--envelope",str(envelope),"--receipt",str(receipt),
      "--worker-pid",str(ids["worker_pid"]),
      "--aider-pid",str(ids["aider_role_pid"]),
      "--output",str(pinned)],capture_output=True,text=True,timeout=18)
    if cap.returncode:
        raise RuntimeError("LIVE_CAPTURE_FAILED:"+cap.stdout[:210]+cap.stderr[:100])
    cap_result=json.loads(cap.stdout)
    assert cap_result["status"]=="PINNED_LAB_EVIDENCE_ONLY"
    def observe():
        p=subprocess.run([sys.executable,"-B",str(SOURCE),"observe",
          "--envelope",str(envelope),"--receipt",str(receipt),
          "--pin",str(pinned)],capture_output=True,text=True,timeout=18)
        if p.returncode:
            raise RuntimeError("OBSERVE_FAILED:"+p.stdout[:230]+p.stderr[:100])
        return json.loads(p.stdout)
    live=observe()
    assert live["historical_processes"]=={
      "worker":"SAME_KERNEL_INSTANCE_AT_SNAPSHOT",
      "aider":"SAME_KERNEL_INSTANCE_AT_SNAPSHOT"
    },live["historical_processes"]
    assert live["original_retry_permitted"] is False
    parent_exit=proc.wait(timeout=37)
    assert parent_exit==0
    ended=observe()
    allowed={"HISTORICAL_PID_ABSENT","PID_REUSED_DIFFERENT_BIRTH"}
    assert set(ended["historical_processes"].values()).issubset(allowed),ended["historical_processes"]
    assert ended["original_retry_permitted"] is False
    assert journal.exists() and not receipt.exists()
    rec={
      "schema":"vf.office-v2.p0-native-process-pair-probe.v1",
      "host":platform.node(),"platform":platform.system(),
      "os_process_birth_backend":ident.read(pinned)["worker"]["source"],
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "pin_sha256":ident.read(pinned)["pin_sha256"],
      "source_of_test_processes":"TWO_SYNTHETIC_PYTHON_PROCESSES_NOT_AIDER",
      "live_worker":live["historical_processes"]["worker"],
      "live_child":live["historical_processes"]["aider"],
      "after_exit_worker":ended["historical_processes"]["worker"],
      "after_exit_child":ended["historical_processes"]["aider"],
      "group_during":live["group_observation"],
      "group_after":ended["group_observation"],
      "historical_journal_preserved":True,
      "no_final_receipt":True,
      "model_invocations":0,"business_effects":0,
      "no_process_signals_or_force_stop":True,
      "safe_to_retry_old":False,
      "automatic_failover_proven":False,
      "all_orphan_descendants_excluded":False,
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "elapsed_seconds":round(time.monotonic()-started,3),
    }
    rec["receipt_sha256"]=seal(rec)
    (ROOT/"lab-evidence.json").write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":"PASS_SCOPED_NATIVE_PROCESS_PAIR_LAB",
      "host":rec["host"],"backend":rec["os_process_birth_backend"],
      "live_worker":rec["live_worker"],"live_child":rec["live_child"],
      "post_worker":rec["after_exit_worker"],"post_child":rec["after_exit_child"],
      "no_auto_retry":True,"receipt_sha256":rec["receipt_sha256"],
      "elapsed_seconds":rec["elapsed_seconds"]
    },sort_keys=True))


if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:280]}))
        raise SystemExit(2)
