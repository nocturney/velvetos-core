#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "packages/vfharness/state/handoffs"
VALID_STATUS = {"offered","acknowledged","consumed","rejected","superseded"}
REQUIRED = {"schema","handoff_id","task_id","source_harness","target_harness","status","trust","summary","artifacts","links","verification","created_at","acknowledged_at"}


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


def doctor():
    records,errors=load_all()
    if errors:
        for e in errors: print(f"FAIL {e}", file=sys.stderr)
        return 1
    print(f"OK handoffs={len(records)}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "doctor":
        print("usage: vf_handoff.py doctor", file=sys.stderr); raise SystemExit(2)
    raise SystemExit(doctor())
