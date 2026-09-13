#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'packages/vfharness/runtime/expected-components.json'
RECEIPTS=ROOT/'packages/vfharness/state/runtime'

def main():
    if not MANIFEST.exists():
        print('FAIL missing expected-components.json', file=sys.stderr); return 1
    try: data=json.loads(MANIFEST.read_text())
    except Exception as e:
        print(f'FAIL invalid manifest: {e}', file=sys.stderr); return 1
    if data.get('schema')!='vf.runtime.expected.v1':
        print('FAIL unsupported runtime manifest schema', file=sys.stderr); return 1
    errors=[]; degraded=[]
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    for c in data.get('components',[]):
        cid=c.get('id'); kind=c.get('kind'); required=bool(c.get('required'))
        if not cid or not kind: errors.append('component missing id/kind'); continue
        receipt=RECEIPTS/f'{cid}.json'
        if kind=='git' and cid=='repo-main':
            # Repository integrity is proven by source checkout itself; deployment parity needs receipts.
            continue
        if not receipt.exists():
            msg=f'{cid}: missing {c.get("evidence","receipt")}'
            (errors if required else degraded).append(msg); continue
        try: r=json.loads(receipt.read_text())
        except Exception as e:
            errors.append(f'{cid}: invalid receipt: {e}'); continue
        if r.get('component_id')!=cid: errors.append(f'{cid}: receipt component_id mismatch')
        if r.get('state') not in {'healthy','degraded','blocked'}: errors.append(f'{cid}: invalid state')
        if r.get('state')!='healthy': (errors if required else degraded).append(f'{cid}: state={r.get("state")}')
        if not r.get('observed_at'): errors.append(f'{cid}: missing observed_at')
        if not r.get('evidence'): errors.append(f'{cid}: missing evidence')
    if errors:
        for e in errors: print('FAIL '+e, file=sys.stderr)
        return 1
    if degraded:
        print('DEGRADED '+'; '.join(degraded))
    else: print('OK runtime manifest/receipts healthy')
    return 0

if __name__=='__main__': raise SystemExit(main())
