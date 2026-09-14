#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEARCH_ROOTS=[ROOT/'packages', ROOT/'.agents', ROOT/'.claude', ROOT/'.codex', ROOT/'.cursor'/'skills']


def _description(frontmatter: str) -> str | None:
    """Read single-line or folded YAML description without pulling in a YAML runtime."""
    lines=frontmatter.splitlines()
    for i,line in enumerate(lines):
        m=re.match(r'^description:\s*(.*)$',line,re.I)
        if not m: continue
        first=m.group(1).strip().strip('"\'')
        if first not in {'>', '>-', '|', '|-'}:
            return first or None
        parts=[]
        for nxt in lines[i+1:]:
            if nxt.startswith((' ', '\t')):
                parts.append(nxt.strip())
            else:
                break
        return ' '.join(p for p in parts if p).strip() or None
    return None


def _reference_skill(rel: Path) -> bool:
    s='/' + rel.as_posix().lower() + '/'
    return '/vendor/' in s or '/third_party/' in s or '/reference/' in s


def _expected_router_pair(paths: list[Path]) -> bool:
    rels=[p.relative_to(ROOT).as_posix() for p in paths]
    return len(paths)==2 and any(r.startswith('.cursor/skills/') for r in rels) and any(r.startswith('packages/') for r in rels)


def main():
    files=[]
    for base in SEARCH_ROOTS:
        if base.exists(): files.extend(base.rglob('SKILL.md'))
    errors=[]; active_warnings=[]; reference_warnings=[]; names=defaultdict(list)
    for p in sorted(set(files)):
        rel=p.relative_to(ROOT)
        reference=_reference_skill(rel)
        warnings=reference_warnings if reference else active_warnings
        if p.is_symlink() and not p.exists():
            errors.append(f'broken symlink: {rel}'); continue
        txt=p.read_text(errors='ignore')
        if not txt.strip(): errors.append(f'empty skill: {rel}'); continue
        lines=txt.splitlines()
        if len(txt.strip()) < 80: warnings.append(f'thin skill: {rel}')
        if len(lines) > 500: warnings.append(f'context-heavy skill ({len(lines)} lines): {rel}')

        frontmatter=re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|$)',txt,re.S)
        if frontmatter:
            desc=_description(frontmatter.group(1))
            if not desc:
                warnings.append(f'missing description frontmatter: {rel}')
            elif len(desc.strip()) < 24:
                warnings.append(f'weak/short description: {rel}')

        m=re.search(r'(?im)^name:\s*["\']?([^"\'\n]+)',txt)
        name=(m.group(1).strip() if m else p.parent.name).lower()
        names[name].append(p)
        if re.search(r'(?im)\b(TODO|TBD|concept only|not implemented)\b',txt):
            warnings.append(f'concept marker: {rel}')
        if 'verify' not in txt.lower() and 'test' not in txt.lower() and 'check-' not in txt.lower() and 'proof' not in txt.lower() and 'evidence' not in txt.lower():
            warnings.append(f'no verification language: {rel}')
    for name,paths in {k:v for k,v in names.items() if len(v)>1}.items():
        if _expected_router_pair(paths):
            continue
        bucket=reference_warnings if all(_reference_skill(p.relative_to(ROOT)) for p in paths) else active_warnings
        bucket.append('possible overlap '+name+': '+', '.join(str(p.relative_to(ROOT)) for p in paths))
    if errors:
        for e in errors: print('FAIL '+e,file=sys.stderr)
        return 1
    print(f'OK skills={len(files)} structural_errors=0 active_warnings={len(active_warnings)} reference_warnings={len(reference_warnings)}')
    for w in active_warnings[:50]: print('WARN active '+w)
    for w in reference_warnings[:25]: print('INFO reference '+w)
    if active_warnings:
        print('FAIL active first-party skill warnings must be fixed or explicitly moved to vendor/reference', file=sys.stderr)
        return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
