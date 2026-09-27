#!/usr/bin/env python3
"""Run every computational HQ sensor. No network. No send."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SKIP = {"check-all.py"}


def git_dirty_state() -> dict[str, bytes] | None:
    """Return {path: current bytes or b''} for git-visible changes, or None without git."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    state: dict[str, bytes] = {}
    for line in proc.stdout.splitlines():
        rel = line[3:].split(" -> ")[-1].strip().strip('"')
        path = ROOT / rel
        try:
            state[rel] = path.read_bytes() if path.is_file() else b""
        except OSError:
            state[rel] = b""
    return state


def main() -> int:
    checks = sorted(
        p
        for p in SCRIPTS.glob("check-*.py")
        if p.name not in SKIP
    )
    if not checks:
        print("FAIL no check-*.py sensors found", file=sys.stderr)
        return 1

    failed: list[str] = []
    dirty_before = git_dirty_state()
    print(f"SENSORS {len(checks)}")
    for path in checks:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode == 0:
            print(f"PASS {path.name}  {out}")
        else:
            failed.append(path.name)
            detail = err or out or f"exit {proc.returncode}"
            print(f"FAIL {path.name}  {detail}", file=sys.stderr)

    # Sensors must only read. Report (do not fail on) any git-visible file the run changed,
    # so a routine never commits sensor side effects by accident.
    dirty_after = git_dirty_state()
    if dirty_before is not None and dirty_after is not None:
        drift = sorted(
            rel for rel, data in dirty_after.items()
            if rel not in dirty_before or dirty_before[rel] != data
        )
        drift += sorted(rel for rel in dirty_before if rel not in dirty_after)
        if drift:
            print(f"WARN sensor side effects on repo files ({len(drift)}): {', '.join(drift[:20])}")
        else:
            print("OK sensor run left repository files unchanged")

    if failed:
        print(f"FAIL suite failed={len(failed)}/{len(checks)}", file=sys.stderr)
        return 1
    print(f"OK suite passed={len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
