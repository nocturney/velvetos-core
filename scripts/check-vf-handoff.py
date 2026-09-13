#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
proc=subprocess.run([sys.executable,str(ROOT/'scripts/vf_handoff.py'),'doctor'],cwd=ROOT,text=True,capture_output=True)
if proc.returncode:
    print((proc.stderr or proc.stdout).strip(), file=sys.stderr)
    raise SystemExit(proc.returncode)
print((proc.stdout or '').strip())
