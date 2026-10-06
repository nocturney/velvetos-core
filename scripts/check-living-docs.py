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
    # Stage 6D is historical acceptance evidence. Current documentation authority
    # moved after Stage 6D and must not force today's scheduler docs back to the
    # old 07:00/09:00 clock contract.
    stage6d_report = ROOT/'packages/velvetos/policy/reports/stage6d-documentation-authority-cleanup.json'
    if not stage6d_report.is_file():
        errors.append('missing historical Stage 6D documentation-authority receipt')
    else:
        try:
            import json
            stage6d = json.loads(stage6d_report.read_text(encoding='utf-8'))
            if stage6d.get('repository_acceptance') != 'PASS':
                errors.append('historical Stage 6D documentation-authority receipt is not PASS')
        except Exception as exc:
            errors.append('historical Stage 6D documentation-authority receipt unreadable: '+str(exc))

    baseline = ROOT/'automation/grok/current-baseline.json'
    manifest = ROOT/'automation/grok/manifest.json'
    chatgpt = ROOT/'automation/chatgpt/manifest.json'
    routine = ROOT/'packages/vfops/ROUTINE.md'
    if not baseline.is_file() or not chatgpt.is_file():
        errors.append('missing current scheduler cutover baseline/ChatGPT manifest')
    else:
        try:
            import json
            b = json.loads(baseline.read_text(encoding='utf-8'))
            c = json.loads(chatgpt.read_text(encoding='utf-8'))
            if b.get('currentAuthority') != 'automation/chatgpt/manifest.json' or b.get('grokRecurringAuthority') is not False or b.get('grokEnabledRoutineCount') != 0:
                errors.append('Grok retirement baseline drift')
            scheduled = {row.get('logicalId') for row in (c.get('scheduledRoutines') or []) if row.get('enabled') is True}
            expected = {'cognee-memory-sync','velvetos-office-loop','runtime-receipts-refresh'}
            if c.get('provider') != 'chatgpt-automations' or scheduled != expected:
                errors.append('current ChatGPT scheduled routine set drift')
        except Exception as exc:
            errors.append('current scheduler baseline unreadable: '+str(exc))
    if manifest.is_file():
        try:
            import json
            m = json.loads(manifest.read_text(encoding='utf-8'))
            if m.get('productionScheduler') != 'chatgpt-automations' or (m.get('routines') or []):
                errors.append('Grok manifest must remain a zero-routine retirement mirror')
        except Exception as exc:
            errors.append('Grok manifest unreadable: '+str(exc))
    if routine.is_file():
        current = routine.read_text(encoding='utf-8')
        for marker in ('**~11:30** | Cognee Memory Sync','**18:30** | VelvetOS Office Loop','**19:15** | Runtime Receipts Refresh','manual/event-driven'):
            if marker not in current:
                errors.append('current routine documentation missing '+marker)
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print('OK living-doc canonical roles present; Stage 6D documentation authority PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
