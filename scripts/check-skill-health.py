#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEARCH_ROOTS=[ROOT/'packages', ROOT/'.agents', ROOT/'.claude', ROOT/'.codex']

def main():
    files=[]
    for base in SEARCH_ROOTS:
        if base.exists(): files.extend(base.rglob('SKILL.md'))
    errors=[]; warnings=[]; names=defaultdict(list)
    for p in sorted(set(files)):
        if p.is_symlink() and not p.exists():
            errors.append(f'broken symlink: {p.relative_to(ROOT)}'); continue
        txt=p.read_text(errors='ignore')
        if not txt.strip(): errors.append(f'empty skill: {p.relative_to(ROOT)}'); continue
        if len(txt.strip()) < 80: warnings.append(f'thin skill: {p.relative_to(ROOT)}')
        m=re.search(r'(?im)^name:\s*["\']?([^"\'\n]+)',txt)
        name=(m.group(1).strip() if m else p.parent.name).lower()
        names[name].append(p)
        if re.search(r'(?im)\b(TODO|TBD|concept only|not implemented)\b',txt):
            warnings.append(f'concept marker: {p.relative_to(ROOT)}')
        if 'verify' not in txt.lower() and 'test' not in txt.lower() and 'check-' not in txt.lower():
            warnings.append(f'no verification language: {p.relative_to(ROOT)}')
    duplicates={k:v for k,v in names.items() if len(v)>1}
    for name,paths in duplicates.items():
        warnings.append('possible overlap '+name+': '+', '.join(str(p.relative_to(ROOT)) for p in paths))
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print(f'OK skills={len(files)} structural_errors=0 warnings={len(warnings)}')
    for w in warnings[:25]: print('WARN '+w)
    if len(warnings)>25: print(f'WARN ... {len(warnings)-25} more')
    return 0
if __name__=='__main__': raise SystemExit(main())
