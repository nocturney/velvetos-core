#!/usr/bin/env python3
"""Offline E5 network snapshot verdict; never grants runtime admission."""
import json
import sys
from pathlib import Path

PHASES = ("before", "during", "after")
def validate(data):
    if not isinstance(data, dict) or set(data.get("snapshots", {})) != set(PHASES):
        return False, "MISSING_SNAPSHOT"
    if data.get("monitor_complete") is not True or data.get("process_tree_complete") is not True:
        return False, "INCOMPLETE_COVERAGE"
    if data.get("sampling_only") is not True:
        return False, "UNKNOWN_MONITOR_MODE"
    if data.get("enforcement_proven") is not True:
        return False, "ENFORCEMENT_NOT_PROVEN"
    for phase in PHASES:
        snap = data["snapshots"][phase]
        if not isinstance(snap, dict) or snap.get("ok") is not True:
            return False, "INVALID_SNAPSHOT"
        if not isinstance(snap.get("pids"), list) or not snap["pids"]:
            return False, "MISSING_PROCESS_TREE"
        for key in ("tcp", "udp"):
            rows = snap.get(key)
            if not isinstance(rows, list):
                return False, "MISSING_ENDPOINTS"
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("pid"), int) or row["pid"] not in snap["pids"]:
                    return False, "UNATTRIBUTED_ENDPOINT"
                if key == "udp":
                    # Windows UDP endpoints are local bindings; no connection state or remote address.
                    return False, "UDP_ENDPOINT_REFUSED"
                state = str(row.get("state", "")).lower()
                if state in ("listen", "listening"):
                    return False, "LISTENER"
                if not state:
                    return False, "MISSING_STATE"
                remote = row.get("remote_address")
                port = row.get("remote_port")
                if state not in ("bound", "closed", "time_wait", "delete_tcb"):
                    if remote != "127.0.0.1":
                        return False, "REMOTE_NOT_APPROVED"
                    if port != 11435:
                        return False, "WRONG_OLLAMA_PORT"
    return True, "SNAPSHOTS_CONFORM_WITH_ENFORCEMENT"

def selftest():
    def base():
        return {"monitor_complete":True,"process_tree_complete":True,"sampling_only":True,"enforcement_proven":True,
                "snapshots":{p:{"ok":True,"pids":[123],"tcp":[],"udp":[]} for p in PHASES}}
    cases=[]
    cases.append(("empty",base(),True))
    x=base();x["snapshots"]["during"]["tcp"]=[{"pid":123,"state":"Listen","remote_address":"0.0.0.0","remote_port":0}];cases.append(("listen",x,False))
    x=base();x["snapshots"]["during"]["tcp"]=[{"pid":123,"state":"Established","remote_address":"8.8.8.8","remote_port":443}];cases.append(("remote",x,False))
    x=base();x["snapshots"]["during"]["tcp"]=[{"pid":123,"state":"Established","remote_address":"127.0.0.1","remote_port":11434}];cases.append(("wrong_port",x,False))
    x=base();del x["snapshots"]["after"];cases.append(("missing_snapshot",x,False))
    x=base();x["snapshots"]["during"]["udp"]=[{"pid":123,"local_port":777}];cases.append(("udp_bind",x,False))
    x=base();x["enforcement_proven"]=False;cases.append(("no_enforcement",x,False))
    x=base();x["process_tree_complete"]=False;cases.append(("tree_gap",x,False))
    x=base();x["snapshots"]["during"]["tcp"]=[{"pid":456,"state":"Established","remote_address":"127.0.0.1","remote_port":11435}];cases.append(("foreign_pid",x,False))
    x=base();x["snapshots"]["during"]["tcp"]=[{"pid":123,"state":"Established","remote_address":"127.0.0.1","remote_port":11435}];cases.append(("approved",x,True))
    for name,fixture,expected in cases:
        actual,_=validate(fixture)
        if actual != expected: raise AssertionError(name)
    print("OK E5 network fixture cases=%d" % len(cases))

if __name__ == "__main__":
    if len(sys.argv)==1 or sys.argv[1]=="--selftest":
        selftest()
    else:
        try:
            obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
            ok,reason=validate(obj)
        except (OSError,ValueError,TypeError) as exc:
            ok,reason=False,"UNREADABLE_SNAPSHOT"
        print(json.dumps({"pass":ok,"reason":reason},sort_keys=True))
        sys.exit(0 if ok else 1)
