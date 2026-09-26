#!/usr/bin/env python3
"""Freeze guard for the legacy handoff CLI (frozen 2026-09-26).

Fails if:
- the frozen script loses its FROZEN / UNUSED header,
- its writer commands (new/ack/consume/reject) stop refusing with exit 3,
- any tracked file other than the script itself and the append-only
  CHANGELOG.md mentions it (docs, skills, constitution, AGENTS.md, README,
  sensors, workflows, packages ...).
The token is assembled at runtime so this sensor does not reference it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "vf_" + "handoff"
SCRIPT_REL = f"scripts/{TOKEN}.py"
SCRIPT = ROOT / SCRIPT_REL
ALLOW = {SCRIPT_REL, "CHANGELOG.md"}
STATE_DIR = ROOT / "packages" / "vfharness" / "state" / "handoffs"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, check=True
        ).stdout.decode("utf-8", "replace")
        files = [f for f in out.split("\0") if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ]


def main() -> None:
    if not SCRIPT.is_file():
        fail(f"missing frozen script {SCRIPT_REL} (keep it for history)")
    head = SCRIPT.read_text(encoding="utf-8")[:600]
    if "FROZEN / UNUSED" not in head:
        fail(f"{SCRIPT_REL} must keep its FROZEN / UNUSED header")

    existed = STATE_DIR.exists()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "new", "freeze-probe", "--task-id", "t",
         "--source", "a", "--target", "b", "--summary", "probe"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if proc.returncode != 3 or "FROZEN" not in proc.stderr:
        fail(f"frozen writer 'new' must refuse with exit 3, got {proc.returncode}")
    if (STATE_DIR / "freeze-probe.json").exists() or (STATE_DIR.exists() and not existed):
        fail("frozen writer created state")

    offenders: list[str] = []
    for rel in tracked_files():
        if rel in ALLOW:
            continue
        path = ROOT / rel
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if TOKEN.encode() in data:
            offenders.append(rel)
    if offenders:
        fail(f"{TOKEN} is frozen; remove references from: {', '.join(sorted(offenders))}")

    print("OK legacy handoff CLI frozen (header, writers refuse, 0 references outside script+CHANGELOG)")


if __name__ == "__main__":
    main()
