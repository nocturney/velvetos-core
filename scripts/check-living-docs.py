#!/usr/bin/env python3
from __future__ import annotations
import subprocess
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
    stage6d = ROOT/'scripts/generate-stage6d-documentation-authority-cleanup-report.py'
    if not stage6d.is_file():
        errors.append('missing Stage 6D documentation-authority generator')
    else:
        proc = subprocess.run(
            [sys.executable, str(stage6d), '--check'],
            cwd=ROOT,
            text=True,
            encoding='utf-8',
            errors='replace',
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            detail = (proc.stdout.strip() or proc.stderr.strip() or f'exit {proc.returncode}')
            errors.append('Stage 6D documentation-authority gate failed: '+detail)
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print('OK living-doc canonical roles present; Stage 6D documentation authority PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
