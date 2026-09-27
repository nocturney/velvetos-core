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
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def token_offenders() -> list[str]:
    """Find TOKEN references without byte-scanning the whole repository."""
    offenders: set[str] = set()
    try:
        tracked = subprocess.run(
            [*GIT, "grep", "-l", "-F", TOKEN, "--", "."],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if tracked.returncode not in {0, 1}:
            raise subprocess.CalledProcessError(tracked.returncode, tracked.args, tracked.stdout, tracked.stderr)
        for rel in tracked.stdout.splitlines():
            rel = rel.replace("\\", "/").strip()
            if rel and rel not in ALLOW:
                offenders.add(rel)

        untracked = subprocess.run(
            [*GIT, "ls-files", "-z", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout.decode("utf-8", "replace")
        for rel in (f for f in untracked.split("\0") if f):
            rel = rel.replace("\\", "/")
            if rel in ALLOW:
                continue
            path = ROOT / rel
            try:
                if TOKEN.encode() in path.read_bytes():
                    offenders.add(rel)
            except OSError:
                continue
        return sorted(offenders)
    except (OSError, subprocess.CalledProcessError):
        # Git unavailable: preserve the original fail-safe semantics.
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            if rel in ALLOW:
                continue
            try:
                if TOKEN.encode() in path.read_bytes():
                    offenders.add(rel)
            except OSError:
                continue
        return sorted(offenders)


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

    offenders = token_offenders()
    if offenders:
        fail(f"{TOKEN} is frozen; remove references from: {', '.join(sorted(offenders))}")

    print("OK legacy handoff CLI frozen (header, writers refuse, 0 references outside script+CHANGELOG)")


if __name__ == "__main__":
    main()
