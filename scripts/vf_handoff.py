#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "packages/vfharness/state/handoffs"
VALID_STATUS = {"offered","acknowledged","consumed","rejected","superseded"}
REQUIRED = {"schema","handoff_id","task_id","source_harness","target_harness","status","trust","summary","artifacts","links","verification","created_at","acknowledged_at","supersedes"}

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def path_for(hid: str): return HANDOFFS / f"{hid}.json"
def write_record(data):
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    path=path_for(data["handoff_id"])
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    return path

def load_one(hid):
    path=path_for(hid)
    if not path.exists(): raise SystemExit(f"missing handoff: {hid}")
    return path,json.loads(path.read_text())

def load_all():
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    errors=[]; records=[]; ids=set()
    for path in sorted(HANDOFFS.glob("*.json")):
        try: data=json.loads(path.read_text())
        except Exception as e:
            errors.append(f"{path.name}: invalid json: {e}"); continue
        missing=REQUIRED-set(data)
        if missing: errors.append(f"{path.name}: missing {sorted(missing)}")
        hid=data.get("handoff_id")
        if hid in ids: errors.append(f"{path.name}: duplicate handoff_id {hid}")
        ids.add(hid)
        if data.get("schema") != "vf.handoff.v1": errors.append(f"{path.name}: unsupported schema")
        if data.get("status") not in VALID_STATUS: errors.append(f"{path.name}: invalid status")
        if data.get("status") in {"acknowledged","consumed"} and not data.get("acknowledged_at"):
            errors.append(f"{path.name}: {data.get('status')} without acknowledged_at")
        if data.get("status") == "consumed" and data.get("trust") == "unreviewed":
            errors.append(f"{path.name}: consumed while trust=unreviewed")
        records.append((path,data))
    idset={d.get("handoff_id") for _,d in records}
    for path,data in records:
        sup=data.get("supersedes")
        if sup and sup not in idset: errors.append(f"{path.name}: missing supersedes target {sup}")
        for link in data.get("links",[]):
            if isinstance(link,str) and link.startswith("handoff:") and link.split(":",1)[1] not in idset:
                errors.append(f"{path.name}: broken handoff link {link}")
    return records,errors

def cmd_new(a):
    if path_for(a.handoff_id).exists(): raise SystemExit(f"handoff exists: {a.handoff_id}")
    data={"schema":"vf.handoff.v1","handoff_id":a.handoff_id,"task_id":a.task_id,"source_harness":a.source,
          "target_harness":a.target,"status":"offered","trust":"unreviewed","summary":a.summary,
          "artifacts":a.artifact or [],"links":a.link or [],"supersedes":a.supersedes,"verification":a.verification,
          "created_at":now(),"acknowledged_at":None}
    print(write_record(data)); return 0

def cmd_ack(a):
    path,data=load_one(a.handoff_id)
    if data.get("status") != "offered": raise SystemExit(f"cannot acknowledge from {data.get('status')}")
    data["status"]="acknowledged"; data["trust"]="reviewed"; data["acknowledged_at"]=now()
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n"); print(path); return 0

def cmd_consume(a):
    path,data=load_one(a.handoff_id)
    if data.get("status") != "acknowledged": raise SystemExit(f"cannot consume from {data.get('status')}")
    data["status"]="consumed"; path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n"); print(path); return 0

def cmd_reject(a):
    path,data=load_one(a.handoff_id)
    if data.get("status") not in {"offered","acknowledged"}: raise SystemExit(f"cannot reject from {data.get('status')}")
    data["status"]="rejected"; path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n"); print(path); return 0

def doctor():
    records,errors=load_all()
    if errors:
        for e in errors: print(f"FAIL {e}", file=sys.stderr)
        return 1
    print(f"OK handoffs={len(records)}")
    return 0

def parser():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    n=sub.add_parser("new"); n.add_argument("handoff_id"); n.add_argument("--task-id",required=True); n.add_argument("--source",required=True); n.add_argument("--target",required=True); n.add_argument("--summary",required=True); n.add_argument("--verification",default="UNPROVEN"); n.add_argument("--artifact",action="append"); n.add_argument("--link",action="append"); n.add_argument("--supersedes"); n.set_defaults(fn=cmd_new)
    for name,fn in (("ack",cmd_ack),("consume",cmd_consume),("reject",cmd_reject)):
        q=sub.add_parser(name); q.add_argument("handoff_id"); q.set_defaults(fn=fn)
    d=sub.add_parser("doctor"); d.set_defaults(fn=lambda a:doctor())
    return p

if __name__ == "__main__":
    args=parser().parse_args(); raise SystemExit(args.fn(args))
