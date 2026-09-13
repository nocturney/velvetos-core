#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'packages/vfharness/state/reviews'
REQ={'schema','review_id','risk','rounds','reviewer_a','reviewer_b','deterministic_proof','state'}

def main():
    DIR.mkdir(parents=True,exist_ok=True)
    errors=[]; count=0
    for p in sorted(DIR.glob('*.json')):
        count+=1
        try:d=json.loads(p.read_text())
        except Exception as e: errors.append(f'{p.name}: invalid json: {e}'); continue
        missing=REQ-set(d)
        if missing: errors.append(f'{p.name}: missing {sorted(missing)}')
        if d.get('schema')!='vf.review.v1': errors.append(f'{p.name}: unsupported schema')
        if d.get('risk') not in {'standard','high'}: errors.append(f'{p.name}: invalid risk')
        rounds=d.get('rounds')
        if not isinstance(rounds,int) or rounds < 1 or rounds > 3: errors.append(f'{p.name}: rounds must be 1..3')
        if d.get('risk')=='high':
            for k in ('reviewer_a','reviewer_b'):
                r=d.get(k) or {}
                if not r.get('independent'): errors.append(f'{p.name}: {k} not marked independent')
                if r.get('state') not in {'pass','fail'}: errors.append(f'{p.name}: {k} invalid state')
        if d.get('state')=='pass':
            if (d.get('reviewer_a') or {}).get('state')!='pass' or (d.get('reviewer_b') or {}).get('state')!='pass': errors.append(f'{p.name}: pass without both reviewer passes')
            if (d.get('deterministic_proof') or {}).get('state')!='pass': errors.append(f'{p.name}: pass without deterministic proof')
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print(f'OK review receipts={count}')
    return 0
if __name__=='__main__': raise SystemExit(main())
