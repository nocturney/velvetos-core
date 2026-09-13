#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEARCH_ROOTS=[ROOT/'packages', ROOT/'.agents', ROOT/'.claude', ROOT/'.codex', ROOT/'.cursor'/'skills']

def main():
    files=[]
    for base in SEARCH_ROOTS:
        if base.exists(): files.extend(base.rglob('SKILL.md'))
    errors=[]; warnings=[]; names=defaultdict(list)
    for p in sorted(set(files)):
        rel=p.relative_to(ROOT)
        if p.is_symlink() and not p.exists():
            errors.append(f'broken symlink: {rel}'); continue
        txt=p.read_text(errors='ignore')
        if not txt.strip(): errors.append(f'empty skill: {rel}'); continue
        lines=txt.splitlines()
        if len(txt.strip()) < 80: warnings.append(f'thin skill: {rel}')
        if len(lines) > 500: warnings.append(f'context-heavy skill ({len(lines)} lines): {rel}')

        frontmatter=re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|$)',txt,re.S)
        if frontmatter:
            fm=frontmatter.group(1)
            desc=re.search(r'(?im)^description:\s*["\']?([^"\'\n]+)',fm)
            if not desc:
                warnings.append(f'missing description frontmatter: {rel}')
            elif len(desc.group(1).strip()) < 24:
                warnings.append(f'weak/short description: {rel}')

        m=re.search(r'(?im)^name:\s*["\']?([^"\'\n]+)',txt)
        name=(m.group(1).strip() if m else p.parent.name).lower()
        names[name].append(p)
        if re.search(r'(?im)\b(TODO|TBD|concept only|not implemented)\b',txt):
            warnings.append(f'concept marker: {rel}')
        if 'verify' not in txt.lower() and 'test' not in txt.lower() and 'check-' not in txt.lower() and 'proof' not in txt.lower() and 'evidence' not in txt.lower():
            warnings.append(f'no verification language: {rel}')
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
