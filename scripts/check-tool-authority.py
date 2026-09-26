#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"

ACTIVE_SURFACES = [
    ROOT / ".cursor" / "mcp.json",
    ROOT / ".cursor" / "vf-desk.json",
    ROOT / ".cursor" / "rules" / "velvet-factory-desk.mdc",
    ROOT / "AGENTS.md",
    ROOT / "instances" / "velvet-factory" / "AGENTS.md",
    ROOT / "instances" / "velvet-factory" / ".cursor" / "vf-desk.json",
    ROOT / "constitution" / "STUDIO.md",
    ROOT / "constitution" / "SEND.md",
    ROOT / "packages" / "vfigos" / "SEND.md",
    ROOT / "packages" / "vfigos" / "OPENPOST.json",
    ROOT / "packages" / "vfops" / "ROUTINE.md",
    ROOT / "packages" / "vfmcp" / "core-mcp.json",
    ROOT / "automation" / "grok" / "manifest.json",
    ROOT / "automation" / "grok" / "CONTRACT.md",
]

BANNED_ACTIVE = {
    "canva": [r"mcp\.canva\.com", r"packages/vfcanva", r"Canva-first", r"Canva first", r"→\s*Canva", r"use \*\*Canva\*\*"],
    "openpost-routing": [r"OpenPost Release Watch(?!.*retired)", r"OpenPost.*primary-control-plane", r"OpenPost.*queue/schedule/publish", r"refresh OpenPost schedule"],
}

def files_under(p):
    if p.is_file():
        yield p
    elif p.is_dir():
        for x in p.rglob("*"):
            if x.is_file() and x.suffix.lower() in {".md", ".json", ".mdc", ".txt", ".py"}:
                yield x

def main():
    data = json.loads(REG.read_text(encoding="utf-8"))
    assert data["tools"]["canva"]["status"] == "forbidden"
    assert data["tools"]["openpost"]["status"] == "frozen"
    assert data["tools"]["cloudflare-instagram-publisher"]["status"] == "active"

    errors = []
    seen = set()
    for surface in ACTIVE_SURFACES:
        for f in files_under(surface):
            if f in seen:
                continue
            seen.add(f)
            text = f.read_text(encoding="utf-8", errors="ignore")
            rel = f.relative_to(ROOT).as_posix()
            for group, pats in BANNED_ACTIVE.items():
                for pat in pats:
                    if re.search(pat, text, flags=re.I | re.S):
                        errors.append(f"{group}: {rel}: /{pat}/")
    if (ROOT / "packages" / "vfcanva").exists():
        errors.append("forbidden package exists: packages/vfcanva")
    for p in (ROOT / ".cursor" / "skills").glob("*canva*"):
        errors.append(f"forbidden skill exists: {p.relative_to(ROOT).as_posix()}")
    if (ROOT / ".cursor" / "rules" / "vf-canva-instagram.mdc").exists():
        errors.append("forbidden rule exists: .cursor/rules/vf-canva-instagram.mdc")

    if errors:
        print("TOOL AUTHORITY FAIL")
        for e in errors:
            print("-", e)
        return 1
    print("TOOL AUTHORITY PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
