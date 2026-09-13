#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'packages/vfharness/state/learning-candidates'
VALID_STATUS={'candidate','accepted','rejected','promoted','superseded','pruned'}
VALID_SCOPE={'task','project','owner'}
REQ={'schema','candidate_id','trigger','action','scope','confidence','status','evidence','first_seen','last_seen','owner_correction','promote_to','supersedes'}

def main():
    DIR.mkdir(parents=True,exist_ok=True)
    errors=[]; ids=set(); records=[]
    for p in sorted(DIR.glob('*.json')):
        try:d=json.loads(p.read_text())
        except Exception as e: errors.append(f'{p.name}: invalid json: {e}'); continue
        missing=REQ-set(d)
        if missing: errors.append(f'{p.name}: missing {sorted(missing)}')
        cid=d.get('candidate_id')
        if cid in ids: errors.append(f'{p.name}: duplicate candidate_id {cid}')
        ids.add(cid); records.append((p,d))
        if d.get('schema')!='vf.learning-candidate.v1': errors.append(f'{p.name}: unsupported schema')
        if d.get('status') not in VALID_STATUS: errors.append(f'{p.name}: invalid status')
        if d.get('scope') not in VALID_SCOPE: errors.append(f'{p.name}: invalid scope')
        conf=d.get('confidence')
        if not isinstance(conf,(int,float)) or not 0 <= conf <= 1: errors.append(f'{p.name}: confidence must be 0..1')
        if d.get('status') in {'accepted','promoted'} and not d.get('evidence'): errors.append(f'{p.name}: accepted/promoted without evidence')
        if d.get('status')=='promoted' and not d.get('promote_to'): errors.append(f'{p.name}: promoted without promote_to')
    known={d.get('candidate_id') for _,d in records}
    for p,d in records:
        sup=d.get('supersedes')
        if sup and sup not in known: errors.append(f'{p.name}: missing supersedes target {sup}')
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print(f'OK learning candidates={len(records)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
