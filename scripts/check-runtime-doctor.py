#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'packages/vfharness/runtime/expected-components.json'
RECEIPTS=ROOT/'packages/vfharness/state/runtime'
STRICT=os.environ.get('VF_RUNTIME_STRICT')=='1' or '--strict' in sys.argv

def main():
    if not MANIFEST.exists():
        print('FAIL missing expected-components.json', file=sys.stderr); return 1
    try: data=json.loads(MANIFEST.read_text())
    except Exception as e:
        print(f'FAIL invalid manifest: {e}', file=sys.stderr); return 1
    if data.get('schema')!='vf.runtime.expected.v1':
        print('FAIL unsupported runtime manifest schema', file=sys.stderr); return 1
    errors=[]; degraded=[]; seen=set()
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    components=data.get('components',[])
    if not components: errors.append('manifest has no components')
    for c in components:
        cid=c.get('id'); kind=c.get('kind'); required=bool(c.get('required'))
        if not cid or not kind: errors.append('component missing id/kind'); continue
        if cid in seen: errors.append(f'duplicate component id {cid}')
        seen.add(cid)
        if not c.get('evidence'): errors.append(f'{cid}: missing evidence type')
        receipt=RECEIPTS/f'{cid}.json'
        if not STRICT: continue
        if kind=='git' and cid=='repo-main': continue
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
    if STRICT:
        if degraded: print('DEGRADED '+'; '.join(degraded))
        else: print('OK runtime strict receipts healthy')
    else:
        print(f'OK runtime contract components={len(components)}; strict proof requires --strict or VF_RUNTIME_STRICT=1')
    return 0

if __name__=='__main__': raise SystemExit(main())
