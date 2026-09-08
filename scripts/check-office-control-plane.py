#!/usr/bin/env python3
"""Validate Office Control Plane — unify existing SoT. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANE = ROOT / "office" / "control-plane.json"
CONTROL = ROOT / "office" / "control"
CLI = ROOT / "scripts" / "vf_control_plane.py"
AGENTS = ROOT / "AGENTS.md"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
LEDGER_README = ROOT / "office" / "ledger" / "README.md"
LOOP_MD = ROOT / "packages" / "vfops" / "hq" / "LOOP.md"

REQUIRED_CONTROL = (
    "inbox.json",
    "dead-letter.json",
    "followups.json",
    "decisions.jsonl",
    "POLICY.md",
    "README.md",
)

REQUIRED_SOT_KEYS = (
    "policy",
    "jobs",
    "media",
    "content_calendar",
    "content_approval",
    "production_completion",
    "office_loop",
    "manager_handoff",
    "decisions",
    "dead_letter",
    "followups",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not PLANE.is_file():
        fail("missing office/control-plane.json")
    if not CLI.is_file():
        fail("missing scripts/vf_control_plane.py")
    for name in REQUIRED_CONTROL:
        path = CONTROL / name
        if not path.is_file():
            fail(f"missing office/control/{name}")

    plane = json.loads(PLANE.read_text(encoding="utf-8"))
    if plane.get("name") != "velvetos-office-control-plane":
        fail("control-plane.json name mismatch")
    sot = plane.get("sourcesOfTruth") or {}
    for key in REQUIRED_SOT_KEYS:
        if key not in sot:
            fail(f"sourcesOfTruth missing {key}")

    # Authoritative paths must exist (globs excluded). Live jobs.csv is gitignored — bootstrap header.
    jobs_live = ROOT / "office" / "ledger" / "live" / "jobs.csv"
    jobs_tmpl = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
    if not jobs_live.is_file():
        if not jobs_tmpl.is_file():
            fail("missing office/ledger/templates/jobs.csv")
        jobs_live.parent.mkdir(parents=True, exist_ok=True)
        jobs_live.write_text(jobs_tmpl.read_text(encoding="utf-8"), encoding="utf-8")

    must_exist = [
        ROOT / "constitution" / "CONSTITUTION.md",
        ROOT / "constitution" / "ORCHESTRA.md",
        jobs_live,
        ROOT / "packages" / "vfmedia" / "catalog.json",
        ROOT / "docs" / "MEDIA-VAULT.md",
        ROOT / "packages" / "vfgrowth" / "CALENDAR.md",
        ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json",
        ROOT / "packages" / "vfops" / "LOOP.json",
        CONTROL / "dead-letter.json",
        CONTROL / "followups.json",
        CONTROL / "decisions.jsonl",
    ]
    for path in must_exist:
        if not path.exists():
            fail(f"authoritative path missing: {path.relative_to(ROOT)}")

    # No parallel SoT maps
    for rogue in (
        ROOT / "office" / "sources-of-truth.json",
        ROOT / "packages" / "vfops" / "control-plane.json",
        CONTROL / "sources.json",
    ):
        if rogue.is_file():
            fail(f"duplicate source-of-truth map: {rogue.relative_to(ROOT)}")

    # One media catalog
    cat = json.loads((ROOT / "packages" / "vfmedia" / "catalog.json").read_text(encoding="utf-8"))
    if cat.get("oneCatalog") is not True:
        fail("vfmedia catalog must set oneCatalog true")

    # Inbox buckets
    inbox = json.loads((CONTROL / "inbox.json").read_text(encoding="utf-8"))
    for bucket in ("content", "production", "sales", "admin", "approvals", "blocked", "unknown"):
        if bucket not in (inbox.get("buckets") or {}):
            fail(f"inbox missing bucket {bucket}")

    # Docs / constitution pointers
    for path, needle in (
        (CONSTITUTION, "office/control-plane.json"),
        (ORCHESTRA, "vf_control_plane.py"),
        (LOOP_MD, "vf_control_plane.py"),
        (LEDGER_README, "control-plane"),
    ):
        text = path.read_text(encoding="utf-8")
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} must mention {needle}")

    agents = AGENTS.read_text(encoding="utf-8")
    if "check-office-control-plane.py" not in agents:
        fail("AGENTS.md sensor table must list check-office-control-plane.py")

    loop = json.loads(LOOP.read_text(encoding="utf-8"))
    guide_paths = {g.get("path") for g in loop.get("guides") or []}
    if "office/control-plane.json" not in guide_paths:
        fail("LOOP.json guides must include office/control-plane.json")

    # CLI smoke
    for cmd in ("status", "gaps", "followups", "memory-hygiene", "review", "handoff", "simulate"):
        argv = [sys.executable, str(CLI), cmd]
        if cmd == "simulate":
            argv += ["--scenario", "owner_surface"]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            fail(f"vf_control_plane.py {cmd}: {proc.stderr or proc.stdout}")

    proc_w = subprocess.run(
        [sys.executable, str(CLI), "watchdog"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc_w.returncode != 0:
        fail(f"watchdog: {proc_w.stderr or proc_w.stdout}")

    proc_t = subprocess.run(
        [sys.executable, str(CLI), "selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc_t.returncode != 0:
        fail(f"selftest: {proc_t.stderr or proc_t.stdout}")

    if not (CONTROL / "HANDOFF.json").is_file():
        fail("handoff did not write HANDOFF.json")
    if not (CONTROL / "HANDOFF-he.md").is_file():
        fail("handoff did not write HANDOFF-he.md")

    # Locks present
    locks = set(plane.get("locks") or [])
    for need in (
        "no-duplicate-sources-of-truth",
        "no-invented-prices",
        "no-auto-dm",
        "scheduling-is-not-publication",
    ):
        if need not in locks:
            fail(f"control-plane locks missing {need}")

    print("OK office control plane")


if __name__ == "__main__":
    main()
