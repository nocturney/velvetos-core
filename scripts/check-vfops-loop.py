#!/usr/bin/env python3
"""Validate the office activation loop. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
CLI = ROOT / "scripts" / "vfops_loop.py"
PLAY = ROOT / "packages" / "vfops" / "hq" / "LOOP.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
INSTANCE = ROOT / "constitution" / "INSTANCE.md"
STUDIO = ROOT / "constitution" / "STUDIO.md"
ROUTINE = ROOT / "packages" / "vfops" / "ROUTINE.md"
HANDOFF = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
EDIT = ROOT / "packages" / "vfgrowth" / "EDIT-GATE.md"
PREFLIGHT = ROOT / "packages" / "vfgrowth" / "PREFLIGHT.md"
CAL_OPS = ROOT / "packages" / "vfgrowth" / "CALENDAR-OPS.md"
STORIES = ROOT / "packages" / "vfgrowth" / "STORIES.md"
STORIES_FIX = ROOT / "packages" / "vfcopy" / "G004-STORIES-FIX.md"
GAP = ROOT / "packages" / "vfops" / "hq" / "TOOL-USE-GAP-2026-09-07.md"
AGENTS = ROOT / "AGENTS.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (LOOP, CLI, PLAY, ORCHESTRA, INSTANCE, STUDIO, ROUTINE, HANDOFF, EDIT, PREFLIGHT, CAL_OPS, STORIES, STORIES_FIX, GAP):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(LOOP.read_text())
    if data.get("name") != "vfops-loop":
        fail("LOOP.json name must be vfops-loop")
    ids = [p["id"] for p in data.get("packs") or []]
    if len(ids) != len(set(ids)):
        fail("LOOP.json duplicate pack ids")
    if "vfcost" not in ids or "vfsku" not in ids or "vfgrowth" not in ids:
        fail("LOOP.json must include vfcost, vfsku, vfgrowth")
    cost = next(p for p in data["packs"] if p["id"] == "vfcost")
    if cost.get("consumeOptional"):
        fail("vfcost CLI is on main — consume must be live, not optional")
    if "vfcost.py brief" not in (cost.get("consume") or ""):
        fail("vfcost consume must be vfcost.py brief")
    if cost.get("briefSlot") != "02":
        fail("vfcost briefSlot must be 02")
    if not (ROOT / "scripts" / "vfcost.py").is_file():
        fail("scripts/vfcost.py missing after rebase onto main")

    orch = ORCHESTRA.read_text()
    for needle in ("vfops_loop.py", "07:00", "FOLLOWER-GROWTH", "רף סוכנות", "אין חדש במשרד", "פער", "PREFLIGHT.md", "רמה נמוכה", "נכשל-סגור"):
        if needle not in orch:
            fail(f"ORCHESTRA.md must mention {needle}")
    if "אין סטוריז" not in orch and "אין סטוריז ואין פיד" not in orch:
        fail("ORCHESTRA.md must hard-gate Stories without Canva/vfcovers")
    send = (ROOT / "constitution" / "SEND.md").read_text()
    for needle in ("PREFLIGHT.md", "רמה נמוכה", "נכשל-סגור", "החלטה"):
        if needle not in send:
            fail(f"SEND.md must mention Christian-lock needle {needle}")
    for path, needles in (
        (INSTANCE, ("רף סוכנות", "חצי-פק", "עברית", "PREFLIGHT.md")),
        (STUDIO, ("רף סוכנות", "JPEG גולמי", "לא שואלים", "VOICE.md", "Canva MCP", "G004-STORIES-FIX", "PREFLIGHT.md", "רמה נמוכה")),
        (EDIT, ("JPEG גולמי", "Canva", "vfcovers", "G004-STORIES-FIX", "PREFLIGHT.md", "VOICE.md")),
        (PREFLIGHT, ("VOICE.md", "VOICE-RESEARCH", "VOICE-CHART", "ציון עצמי", "נכשל-סגור", "2–3", "CONTENT-RUBRIC")),
        (CAL_OPS, ("לא שואלים", "Google Calendar", "050-2517000")),
        (STORIES, ("נייבי", "סיפור-מוצר", "050-2517000", "Canva MCP")),
        (STORIES_FIX, ("סיפור-מוצר", "050-2517000", "DAHUaUo3bAk", "X ₪")),
        (GAP, ("vfcopy", "vfcanva", "vfcovers", "פער", "7.9")),
    ):
        text = path.read_text()
        for needle in needles:
            if needle not in text:
                fail(f"{path.name} must mention {needle}")

    if "vfops_loop.py" not in ROUTINE.read_text():
        fail("ROUTINE.md must run vfops_loop.py at 07:00")
    if "vfops_loop.py" not in HANDOFF.read_text():
        fail("HANDOFF-he.md must point at vfops_loop.py")
    handoff = HANDOFF.read_text()
    if "G004" not in handoff or "vfcopy/G004.md" not in handoff:
        fail("HANDOFF-he.md must open G004 pack")
    if "G004-STORIES-FIX.md" not in handoff:
        fail("HANDOFF-he.md must point Stories at G004-STORIES-FIX.md")
    if "אין סטוריז בלי מעבר" not in handoff:
        fail("HANDOFF-he.md must hard-gate Stories without Canva/vfcovers")
    if "אל תפנה לכריסטיאן על מדדים חלשים" not in handoff:
        fail("HANDOFF-he.md must lock אל תפנה לכריסטיאן על מדדים חלשים")
    if "PREFLIGHT.md" not in handoff or "preflight/G004.md" not in handoff:
        fail("HANDOFF-he.md must require PREFLIGHT artifact path")

    if "check-vfops-loop.py" not in AGENTS.read_text():
        fail("AGENTS.md sensor table must list check-vfops-loop.py")

    proc = subprocess.run(
        [sys.executable, str(CLI), "check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"vfops_loop.py check: {proc.stderr or proc.stdout}")


    # --- behavioral consumers: run ≠ brief ≠ check ---
    import vfops_loop as loop

    specs = {s.id: s for s in loop.consumer_registry()}
    if "sensor-suite" not in specs:
        fail("consumer registry must list sensor-suite as explicit skip")
    if specs["sensor-suite"].auto_daily or specs["sensor-suite"].kind != "skip":
        fail("check-all must never be an auto-daily consumer (recursion)")
    if specs["vfcovers-compose"].auto_daily or specs["vfcanva-render"].auto_daily:
        fail("vfcanva/vfcovers must not auto-run standing packs")
    if specs["vfsales-quote"].auto_daily:
        fail("vfsales quote is on-inquiry only")

    # Fixture isolation: do not pollute live consumer-runs during sensor
    import tempfile
    from pathlib import Path as P
    tmp = tempfile.TemporaryDirectory()
    fake_state = P(tmp.name) / "consumer-runs.jsonl"
    old_state = loop.CONSUMER_STATE
    loop.CONSUMER_STATE = fake_state
    try:
        day = "2099-01-01"
        first = loop.run_daily_consumers(today=day, force=False)
        by_id = {r["id"]: r for r in first}
        if by_id.get("velvetos-modules", {}).get("status") != "ok":
            fail(f"velvetos-modules should run once: {by_id.get('velvetos-modules')}")
        if by_id.get("vfcovers-compose", {}).get("status") != "skipped":
            fail("vfcovers-compose must skip without content job")
        if by_id.get("sensor-suite", {}).get("status") != "skipped":
            fail("sensor-suite must skip inside run")
        second = loop.run_daily_consumers(today=day, force=False)
        if second and {r["id"]: r for r in second}.get("velvetos-modules", {}).get("status") != "skipped":
            fail("second run must skip already-ok consumer (no overwrite thrash)")
        brief = loop.assemble(day)
        blob = json.dumps(brief, ensure_ascii=False)
        if "velvetos-modules" not in blob and "צרכנים" not in blob:
            fail("assemble brief must surface consumer results")
        # check path must not call run_daily_consumers — ensure state line count stable across check
        before = fake_state.read_text(encoding="utf-8") if fake_state.is_file() else ""
        proc2 = subprocess.run(
            [sys.executable, str(CLI), "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if proc2.returncode != 0:
            fail(f"vfops_loop.py check after run: {proc2.stderr or proc2.stdout}")
        after = fake_state.read_text(encoding="utf-8") if fake_state.is_file() else ""
        # check uses live CONSUMER_STATE path inside subprocess — cannot see fake_state.
        # Prove in-process: assemble alone does not append runs
        n_before = len(before.splitlines())
        loop.assemble(day)
        n_after = len(fake_state.read_text(encoding="utf-8").splitlines()) if fake_state.is_file() else 0
        if n_after != n_before:
            fail("assemble must not append consumer-runs (side effect)")
    finally:
        loop.CONSUMER_STATE = old_state
        tmp.cleanup()

    print("OK vfops-loop wired into orchestra+brief+handoff + consumers")


if __name__ == "__main__":
    main()
