#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[
    ROOT/'AGENTS.md',
    ROOT/'README.md',
    ROOT/'packages/vfharness/LIVING-DOCS.md',
    ROOT/'packages/vfharness/runtime/expected-components.json',
]

def main():
    errors=[]
    for p in REQUIRED:
        if not p.exists(): errors.append(f'missing canonical doc: {p.relative_to(ROOT)}')
        elif not p.read_text(errors='ignore').strip(): errors.append(f'empty canonical doc: {p.relative_to(ROOT)}')
    coord=ROOT/'docs/SHARED-WORK-COORDINATION.md'
    if coord.exists():
        txt=coord.read_text(errors='ignore').lower()
        if 'main' in txt and 'what runs on the machine' in txt and 'receipt' not in txt:
            errors.append('SHARED-WORK-COORDINATION.md discusses runtime drift without linking runtime receipts')
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print('OK living-doc canonical roles present')
    return 0
if __name__=='__main__': raise SystemExit(main())
