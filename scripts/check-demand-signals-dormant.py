#!/usr/bin/env python3
"""Dormant guard for the structured demand-signals adapter (2026-09-26).

Unlike the frozen legacy handoff CLI, this adapter stays RUNNABLE for a
legitimate manual call. It is dormant because no provider feeds it. Fails if:
- the adapter loses its DORMANT header, or the docs/README lose the dormant marker,
- anything wires it as an active feed: a workflow, a shell/PowerShell runner, a
  scheduler/routine config, or any Python outside its own test/sensors imports
  or invokes it or consumes DemandSignalPacket,
- it stops being runnable (`--self-test` must still pass).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
NAME = "demand-signals-dormant"
TOKEN = "vf_demand" + "_signals"
PACKET = "DemandSignal" + "Packet"
SCRIPT = ROOT / "scripts" / f"{TOKEN}.py"
# Files allowed to name the adapter in executable/config form.
ALLOW = {
    f"scripts/{TOKEN}.py",
    f"scripts/test_{TOKEN}.py",
    "scripts/check-vfresearch.py",
    "scripts/check-demand-signals-dormant.py",
}
DOC_MARKERS = {
    "packages/vfresearch/DEMAND-SIGNALS.md": "**DORMANT",
    "packages/vfresearch/SKILL.md": "**DORMANT:**",
    "packages/vfresearch/HQ-ROUTINE.md": "**DORMANT:**",
    "packages/vfresearch/hq/PRINT-DEMAND.md": "**DORMANT:**",
}
WIRING_SUFFIXES = (".py", ".sh", ".ps1", ".yml", ".yaml", ".json", ".toml", ".timer", ".service", ".cron")


def fail(msg: str) -> None:
    print(f"FAIL {NAME}: {msg}", file=sys.stderr)
    raise SystemExit(1)


def tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            [*GIT, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout.decode("utf-8", "replace")
        files = [f for f in out.split("\0") if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def is_active_wiring(rel: str, text: str) -> bool:
    """True if a non-allowed executable/config file wires the dormant adapter."""
    if rel in ALLOW or not rel.endswith(WIRING_SUFFIXES):
        return False
    # Historical harness evidence records are not wiring.
    if rel.startswith("packages/vfharness/state/"):
        return False
    if rel.endswith(".json") and rel.endswith(".schema.json"):
        return False
    return TOKEN in text or (rel.endswith((".py", ".sh", ".ps1", ".yml", ".yaml")) and PACKET in text)


def main() -> int:
    if not SCRIPT.is_file():
        fail(f"missing adapter scripts/{TOKEN}.py (dormant, keep it runnable)")
    if "DORMANT" not in SCRIPT.read_text(encoding="utf-8")[:800]:
        fail(f"scripts/{TOKEN}.py must keep its DORMANT header")
    for rel, marker in DOC_MARKERS.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if marker not in text:
            fail(f"{rel} must carry the dormant marker {marker!r}")
    head = (ROOT / "packages/vfresearch/DEMAND-SIGNALS.md").read_text(encoding="utf-8")[:900]
    if "No provider feeds" not in head:
        fail("DEMAND-SIGNALS.md banner must say no provider feeds it")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = [l for l in readme.splitlines() if l.startswith("<tr><td><strong>Structured Demand Signals</strong>")]
    if len(rows) != 2 or any("DORMANT / NO PROVIDER" not in r for r in rows):
        fail("README Structured Demand Signals rows (he/en) must say DORMANT / NO PROVIDER")
    if any("IMPLEMENTED" in r.split("</td>")[1] for r in rows):
        fail("README must not present the dormant adapter as IMPLEMENTED/active")

    offenders = []
    for rel in tracked_files():
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if is_active_wiring(rel, text):
            offenders.append(rel)
    if offenders:
        fail(f"dormant adapter must not be wired as an active feed: {', '.join(sorted(offenders))}")

    # Negative controls for the wiring detector.
    probes = [
        (".github/workflows/demand.yml", f"run: python3 scripts/{TOKEN}.py normalize"),
        ("office/control/routine.json", f'{{"cmd": "{TOKEN}"}}'),
        ("scripts/build_brief.py", f"from x import {PACKET}"),
    ]
    for rel, text in probes:
        if not is_active_wiring(rel, text):
            fail(f"negative control not caught: {rel}")
    if is_active_wiring("packages/vfresearch/DEMAND-SIGNALS.md", TOKEN):
        fail("docs mentioning the dormant adapter must not count as wiring")

    proc = subprocess.run([sys.executable, str(SCRIPT), "--self-test"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(f"dormant adapter must stay runnable (--self-test exit {proc.returncode}): {proc.stderr[-400:]}")

    print(f"OK {NAME} header=DORMANT docs=4 readme=DORMANT wiring=0 runnable=self-test-pass negative_controls={len(probes) + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
