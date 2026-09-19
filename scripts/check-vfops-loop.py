#!/usr/bin/env python3
"""Validate the office activation loop. No network. No send."""
from __future__ import annotations

import json
import os
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

# Child Python tools emit UTF-8; decode them explicitly even on cp1252 Windows.
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (LOOP, CLI, PLAY, ORCHESTRA, INSTANCE, STUDIO, ROUTINE, HANDOFF, EDIT, PREFLIGHT, CAL_OPS, STORIES, STORIES_FIX, GAP):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(LOOP.read_text(encoding="utf-8"))
    if data.get("name") != "vfops-loop":
        fail("LOOP.json name must be vfops-loop")
    ids = [p["id"] for p in data.get("packs") or []]
    if len(ids) != len(set(ids)):
        fail("LOOP.json duplicate pack ids")
    if "vfcost" not in ids or "vfsku" not in ids or "vfgrowth" not in ids:
        fail("LOOP.json must include vfcost, vfsku, vfgrowth")
    if "vfbooks" not in ids:
        fail("LOOP.json must include vfbooks")
    books = next(p for p in data["packs"] if p["id"] == "vfbooks")
    if "vfbooks.py brief" not in (books.get("consume") or ""):
        fail("vfbooks consume must be vfbooks.py brief")
    if books.get("briefSlot") != "02":
        fail("vfbooks briefSlot must be 02")
    cost = next(p for p in data["packs"] if p["id"] == "vfcost")
    if cost.get("consumeOptional"):
        fail("vfcost CLI is on main — consume must be live, not optional")
    if "vfcost.py brief" not in (cost.get("consume") or ""):
        fail("vfcost consume must be vfcost.py brief")
    if cost.get("briefSlot") != "02":
        fail("vfcost briefSlot must be 02")
    if not (ROOT / "scripts" / "vfcost.py").is_file():
        fail("scripts/vfcost.py missing after rebase onto main")

    orch = ORCHESTRA.read_text(encoding="utf-8")
    for needle in ("vfops_loop.py", "07:00", "FOLLOWER-GROWTH", "רף סוכנות", "אין חדש במשרד", "פער", "PREFLIGHT.md", "רמה נמוכה", "נכשל-סגור"):
        if needle not in orch:
            fail(f"ORCHESTRA.md must mention {needle}")
    if "VF_PUBLICATION_ROUTE_V1" not in orch or "Canva/vfcanva are forbidden" not in orch:
        fail("ORCHESTRA.md must bind current VF publication route and forbid Canva/vfcanva")
    send = (ROOT / "constitution" / "SEND.md").read_text(encoding="utf-8")
    for needle in ("PREFLIGHT.md", "רמה נמוכה", "נכשל-סגור", "החלטה"):
        if needle not in send:
            fail(f"SEND.md must mention Christian-lock needle {needle}")
    for path, needles in (
        (INSTANCE, ("רף סוכנות", "חצי-פק", "עברית", "PREFLIGHT.md")),
        (STUDIO, ("רף סוכנות", "JPEG גולמי", "לא שואלים", "VOICE.md", "VF_PUBLICATION_ROUTE_V1", "Canva/vfcanva are forbidden", "G004-STORIES-FIX", "PREFLIGHT.md", "רמה נמוכה")),
        (EDIT, ("JPEG גולמי", "VF_PUBLICATION_ROUTE_V1", "publicationRoute.deniedTools", "source-grounded", "publication evidence", "G004-STORIES-FIX", "PREFLIGHT.md", "VOICE.md")),
        (PREFLIGHT, ("VOICE.md", "VOICE-RESEARCH", "VOICE-CHART", "ציון עצמי", "נכשל-סגור", "2–3", "CONTENT-RUBRIC")),
        (CAL_OPS, ("לא שואלים", "Google Calendar", "Instagram")),
        (STORIES, ("VF_PUBLICATION_ROUTE_V1", "Canva/vfcanva אסורים", "source-grounded", "publication evidence", "סיפור-מוצר", "הודעה")),
        (STORIES_FIX, ("LEGACY / STALE", "audit only", "VF_PUBLICATION_ROUTE_V1", "סיפור-מוצר", "הודעה")),
        (GAP, ("vfcopy", "vfcanva", "vfcovers", "פער", "7.9")),
    ):
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                if needle == "הודעה" and ("הודעת" in text or "אינסטגרם" in text or "Instagram" in text):
                    continue
                fail(f"{path.name} must mention {needle}")
        # Public CTA must not require WhatsApp phone alone
        if path in (STORIES, STORIES_FIX, CAL_OPS):
            if "050-2517000" in text and "CTA" in text:
                if not any(n in text for n in ("הודעה", "הודעת", "אינסטגרם", "Instagram")):
                    fail(f"{path.name} still requires WhatsApp phone as public CTA")

    stories_active = STORIES.read_text(encoding="utf-8").split("## LEGACY / provenance only", 1)[0]
    for forbidden in ("edit_url", "compose_slides.py", "studio/render.py", "נגזרת Canva/vfcovers", "failover Canva"):
        if forbidden in stories_active:
            fail(f"STORIES.md active route still contains denied provider directive {forbidden!r}")

    handoff_active = HANDOFF.read_text(encoding="utf-8").split("> LEGACY / provenance only", 1)[0]
    for forbidden in ("Canva MCP או vfcovers/vfcanva", "אחרי Canva/vfcovers", "עד Canva/vfcovers"):
        if forbidden in handoff_active:
            fail(f"HANDOFF-he.md active route still contains legacy provider directive {forbidden!r}")

    routine = ROUTINE.read_text(encoding="utf-8")
    if "vfops_loop.py" not in routine:
        fail("ROUTINE.md must bind the canonical vfops_loop.py brief producer")
    brief_persist_cmd = "python3 scripts/vfops_loop.py brief --write --date <YYYY-MM-DD>"
    if routine.count(brief_persist_cmd) < 2:
        fail("ROUTINE.md must bind both Morning Brief and Delivery Guard recovery to the canonical same-day brief artifact producer")
    if "backfill artifact is not a delivery receipt" not in routine:
        fail("ROUTINE.md must keep brief artifact persistence separate from Gmail delivery proof")
    if "vfops_loop.py" not in HANDOFF.read_text(encoding="utf-8"):
        fail("HANDOFF-he.md must point at vfops_loop.py")
    handoff = HANDOFF.read_text(encoding="utf-8")
    if "G004" not in handoff or "vfcopy/G004.md" not in handoff:
        fail("HANDOFF-he.md must open G004 pack")
    if "G004-STORIES-FIX.md" not in handoff:
        fail("HANDOFF-he.md must point Stories at G004-STORIES-FIX.md")
    if "VF_PUBLICATION_ROUTE_V1" not in handoff or "Canva/vfcanva אסורים" not in handoff:
        fail("HANDOFF-he.md must bind current VF publication route and forbid Canva/vfcanva")
    if "אל תפנה לכריסטיאן על מדדים חלשים" not in handoff:
        fail("HANDOFF-he.md must lock אל תפנה לכריסטיאן על מדדים חלשים")
    if "PREFLIGHT.md" not in handoff or "preflight/G004.md" not in handoff:
        fail("HANDOFF-he.md must require PREFLIGHT artifact path")

    if "check-vfops-loop.py" not in AGENTS.read_text(encoding="utf-8"):
        fail("AGENTS.md sensor table must list check-vfops-loop.py")

    # --- owner-memory day-block contract (Markdown, no Pydantic) ---
    import re

    memory_path = ROOT / "packages" / "vfops" / "data" / "owner-memory.md"
    memory_update = ROOT / "packages" / "vfmem" / "MEMORY-UPDATE.md"
    daily_retro = ROOT / "packages" / "vfops" / "hq" / "DAILY-RETRO.md"
    for path in (memory_path, memory_update, daily_retro):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    mem_upd = memory_update.read_text(encoding="utf-8")
    for needle in ("**מושב:**", "**למדנו:**", "**מקור:**", "fail-closed", "check-vfops-loop.py"):
        if needle not in mem_upd:
            fail(f"MEMORY-UPDATE.md must lock day-block contract needle {needle}")
    retro_txt = daily_retro.read_text(encoding="utf-8")
    if "חוזה יום" not in retro_txt or "MEMORY-UPDATE.md" not in retro_txt:
        fail("DAILY-RETRO.md must point at owner-memory day-block contract")
    if "לולאת פרנסה" not in retro_txt:
        fail("DAILY-RETRO.md must include לולאת פרנסה (inquiries↔models↔materials)")
    if "print.done" not in retro_txt:
        fail("DAILY-RETRO.md must mention print.done handoff in seat checklist/loop")

    retro_signals = ROOT / "packages" / "vfops" / "hq" / "RETRO-SIGNALS.md"
    if not retro_signals.is_file():
        fail("missing RETRO-SIGNALS.md")
    rs_txt = retro_signals.read_text(encoding="utf-8")
    for needle in ("model_demand", "material_signal"):
        if needle not in rs_txt:
            fail(f"RETRO-SIGNALS.md must list kind {needle}")

    print_done = ROOT / "packages" / "vfprod" / "PRINT-DONE.md"
    if not print_done.is_file():
        fail("missing packages/vfprod/PRINT-DONE.md")
    pd_txt = print_done.read_text(encoding="utf-8")
    for needle in ("print.done", "PREFLIGHT", "אוטו־DM", "hybrid-reel", "vfprod.py print-done"):
        if needle not in pd_txt:
            fail(f"PRINT-DONE.md must mention {needle}")
    if "WATCHTOWER.md" not in pd_txt:
        fail("PRINT-DONE.md must point at WATCHTOWER.md Edge farm bind")

    watchtower = ROOT / "packages" / "vfprod" / "WATCHTOWER.md"
    floor = ROOT / "packages" / "vfprod" / "FLOOR.md"
    if not watchtower.is_file():
        fail("missing packages/vfprod/WATCHTOWER.md")
    wt_txt = watchtower.read_text(encoding="utf-8")
    for needle in ("Edge", "print.done", "אין Print", "Watchtower", "runtime שני"):
        if needle not in wt_txt:
            fail(f"WATCHTOWER.md must mention {needle}")
    floor_txt = floor.read_text(encoding="utf-8")
    if "WATCHTOWER.md" not in floor_txt:
        fail("FLOOR.md must point at WATCHTOWER.md")
    if "ROUTING.md" not in floor_txt:
        fail("FLOOR.md must point at ROUTING.md")

    gates_json = ROOT / "packages" / "vfops" / "hq" / "GATES.json"
    gates_md = ROOT / "packages" / "vfops" / "hq" / "GATES.md"
    orders = ROOT / "packages" / "vfbooks" / "data" / "orders.json"
    inv4u = ROOT / "packages" / "vfbooks" / "data" / "invoice4u-snapshot.json"
    offering = ROOT / "packages" / "vfbiz" / "OFFERING.md"
    vfprod_cli = ROOT / "scripts" / "vfprod.py"
    for path in (gates_json, gates_md, orders, inv4u, offering, vfprod_cli):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    gates = json.loads(gates_json.read_text(encoding="utf-8"))
    if gates.get("name") != "vfops-gates":
        fail("GATES.json name must be vfops-gates")
    if "no-zero-touch-close" not in (gates.get("locks") or []):
        fail("GATES.json must lock no-zero-touch-close")
    if gates.get("items") not in ([], None) and not isinstance(gates.get("items"), list):
        fail("GATES.json items must be a list")
    offering_txt = offering.read_text(encoding="utf-8")
    for needle in ("מוצרים מוכנים", "התאמה אישית", "כמות", "מאפיין"):
        if needle not in offering_txt:
            fail(f"OFFERING.md must mention {needle}")

    brief_md = ROOT / "packages" / "vfops" / "BRIEF.md"
    if "GATES.json" not in brief_md.read_text(encoding="utf-8"):
        fail("BRIEF.md must hook slot 01 to GATES.json")
    if "vfprod.py" not in brief_md.read_text(encoding="utf-8"):
        fail("BRIEF.md must hook slot 03 to vfprod.py")

    for rel, needles in (
        ("packages/vfresearch/hq/MAKERWORLD-SCAN.md", ("ראשון", "רביעי", "vfsku.py scan", "NC")),
        ("packages/vfgrowth/hq/PROFILE-TO-WHATSAPP.md", ("הודעה", "VOICE.md", "אין ספירה", "BUSINESS_CONTACT")),
        ("packages/vfbooks/INTEGRITY.md", ("Invoice4U", "vfbooks.py brief", "decision_gate")),
        ("scripts/vfbooks.py", ("brief", "אין ספירה", "Invoice4U")),
        ("scripts/vfprod.py", ("print-done", "PREFLIGHT")),
        ("scripts/vf_organic_growth.py", ("approved_for_manual_posting", "אין ספירה")),
        ("constitution/ORGANIC_GROWTH.md", ("print.done", "posted_manually", "pending_ops", "PUBLIC_CURRENT_CTA")),
    ):
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing {rel}")
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{rel} must mention {needle!r}")
    for needle in ("RETRO-SIGNALS.md", "vf_retro_signals.py", "retro-signals.json"):
        if needle not in retro_txt:
            fail(f"DAILY-RETRO.md must wire retro→signal needle {needle!r}")

    signals_doc = ROOT / "packages" / "vfops" / "hq" / "RETRO-SIGNALS.md"
    signals_cli = ROOT / "scripts" / "vf_retro_signals.py"
    brief_slots = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"
    for path in (signals_doc, signals_cli, brief_slots):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    sig_doc = signals_doc.read_text(encoding="utf-8")
    for needle in ("retro.anomaly", "briefSlot", "Christian", "vf_retro_signals.py"):
        if needle not in sig_doc:
            fail(f"RETRO-SIGNALS.md missing {needle!r}")
    slots = brief_slots.read_text(encoding="utf-8")
    if "retro-signals.json" not in slots:
        fail("BRIEF-SLOTS.md must consume retro-signals.json")
    if "vf_organic_growth.py" not in slots:
        fail("BRIEF-SLOTS.md must consume vf_organic_growth.py Decision Pack")

    proc_sig = subprocess.run(
        [sys.executable, str(signals_cli), "--write"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if proc_sig.returncode != 0:
        fail(f"vf_retro_signals.py --write: {proc_sig.stderr or proc_sig.stdout}")
    out_sig = ROOT / "packages" / "vfops" / "data" / "retro-signals.json"
    if not out_sig.is_file():
        fail("vf_retro_signals.py did not write retro-signals.json")
    sig_data = json.loads(out_sig.read_text(encoding="utf-8"))
    if "signals" not in sig_data or "generatedAt" not in sig_data:
        fail("retro-signals.json missing signals/generatedAt")
    if sig_data.get("catalogEvent") != "retro.anomaly":
        fail("retro-signals.json catalogEvent must be retro.anomaly")

    memory = memory_path.read_text(encoding="utf-8")
    # Split on dated day headers; skip catch-up prose that uses other headings.
    day_pat = re.compile(r"(?m)^### (\d{4}-\d{2}-\d{2})\b[^\n]*\n(.*?)(?=^### \d{4}-\d{2}-\d{2}\b|\Z)", re.S)
    blocks = day_pat.findall(memory)
    if len(blocks) < 3:
        fail(f"owner-memory.md expected >=3 dated day blocks, got {len(blocks)}")
    for date, body in blocks:
        for field in ("**מושב:**", "**למדנו:**", "**מקור:**"):
            if field not in body:
                fail(f"owner-memory day {date} missing required field {field}")

    proc = subprocess.run(
        [sys.executable, str(CLI), "check"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"vfops_loop.py check: {proc.stderr or proc.stdout}")


    # --- behavioral consumers: run ≠ brief ≠ check ---
    import vfops_loop as loop

    # Windows regression: parent locale may be cp1252 while Python children emit UTF-8.
    utf8_proc, utf8_stdout, utf8_stderr = loop._run_captured(
        [sys.executable, "-c", "print('\\u05e2\\u05d1\\u05e8\\u05d9\\u05ea \\U0001f600')"]
    )
    if (
        utf8_proc.returncode != 0
        or utf8_stderr
        or utf8_stdout.strip() != "\u05e2\u05d1\u05e8\u05d9\u05ea \U0001f600"
    ):
        fail(f"UTF-8 subprocess capture corrupted output: {utf8_stdout!r} {utf8_stderr!r}")
    legacy_proc, legacy_stdout, legacy_stderr = loop._run_captured(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([99,97,102,233]))"]
    )
    if legacy_proc.returncode != 0 or legacy_stderr or legacy_stdout != "caf\u00e9":
        fail(f"legacy-codepage subprocess fallback corrupted output: {legacy_stdout!r} {legacy_stderr!r}")

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

    with tempfile.TemporaryDirectory(prefix="vfops-freshness-") as fixture_name:
        fixture = P(fixture_name)
        week = fixture / "week.md"
        old_week = loop.BIZ_WEEK
        loop.BIZ_WEEK = week
        try:
            block = "## בלוק לבריף\n```\nSHOULD_NOT_SURFACE\n```\n"
            week.write_text(block, encoding="utf-8")
            if "ללא תאריך עדכון תקין" not in loop.biz_week_line("2026-09-17"):
                fail("biz_week_line must fail closed when update date is missing")
            week.write_text("עודכן: **2026-09-18**\n" + block, encoding="utf-8")
            if "מתוארך לעתיד" not in loop.biz_week_line("2026-09-17"):
                fail("biz_week_line must fail closed on future update date")
            week.write_text("עודכן: **2026-13-40**\n" + block, encoding="utf-8")
            if "תאריך עדכון לא תקין" not in loop.biz_week_line("2026-09-17"):
                fail("biz_week_line must fail closed on invalid update date")
            week.write_text("עודכן: **2026-09-17**\n" + block.replace("SHOULD_NOT_SURFACE", "FRESH_WEEK"), encoding="utf-8")
            if loop.biz_week_line("2026-09-17") != "FRESH_WEEK":
                fail("biz_week_line must allow a valid current dated block")
        finally:
            loop.BIZ_WEEK = old_week

    with tempfile.TemporaryDirectory(prefix="vfops-ledger-") as fixture_name:
        ledger = P(fixture_name) / "LEDGER.md"
        ledger.write_text("| **G003** | x | KEEP_LIVE_BASELINE |\n| **G004** | x | stale |\n| **G005** | x | HISTORICAL_NOT_LIVE |\n", encoding="utf-8")
        old_ledger = loop.GROWTH_LEDGER
        loop.GROWTH_LEDGER = ledger
        try:
            statuses = {row[0]: row[2] for row in loop.captions_rows()}
            if statuses.get("G003") != "חי · KEEP_LIVE_BASELINE":
                fail("captions_rows must derive G003 live state from current growth ledger")
            if not statuses.get("G004-STORIES-FIX", "").startswith("STALE"):
                fail("captions_rows must derive G004 stale state from current growth ledger")
        finally:
            loop.GROWTH_LEDGER = old_ledger

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
        if "VOICE + Canva/vfcovers" in blob or "Canva MCP או vfcovers/vfcanva" in blob:
            fail("assemble brief must not emit legacy Canva/vfcanva publication route")
        if "Canva/vfcanva אסורים בפרסום VF" not in blob:
            fail("assemble brief must surface current no-Canva VF publication route")
        if "מקור vfbiz/out/week.md מיושן" not in blob:
            fail("assemble brief must label stale weekly business source instead of presenting it as current")
        if "growth-brief מיושן" not in blob:
            fail("assemble brief must label stale growth-brief source instead of presenting it as current")
        # check path must not call run_daily_consumers — ensure state line count stable across check
        before = fake_state.read_text(encoding="utf-8") if fake_state.is_file() else ""
        proc2 = subprocess.run(
            [sys.executable, str(CLI), "check"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
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

    gmail_cli = ROOT / "packages" / "vfops" / "gmail_brief_send.py"
    gmail_init = ROOT / "packages" / "vfops" / "__init__.py"
    send_brief_doc = ROOT / "docs" / "SEND-BRIEF-MCP.md"
    for path in (gmail_cli, gmail_init, send_brief_doc):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    send_brief = send_brief_doc.read_text(encoding="utf-8")
    for needle in (
        "create_draft",
        "update_draft",
        "send_message",
        "draftId",
        "LOAD_FROM_FILE",
        "python -m vfops.gmail_brief_send",
        "no token",
    ):
        if needle not in send_brief:
            fail(f"SEND-BRIEF-MCP.md must mention {needle!r}")
    if "LOAD_FROM_FILE" in send_brief and "דולף" not in send_brief and "leak" not in send_brief.lower():
        fail("SEND-BRIEF-MCP.md must warn that LOAD_FROM_FILE leaks")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "packages") + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("GOOGLE_TOKEN", None)
    env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    help_proc = subprocess.run(
        [sys.executable, "-m", "vfops.gmail_brief_send", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if help_proc.returncode != 0:
        fail(f"gmail_brief_send --help: {help_proc.stderr or help_proc.stdout}")
    for flag in ("--html", "--images", "--to", "--subject"):
        if flag not in (help_proc.stdout or ""):
            fail(f"gmail_brief_send --help must list {flag}")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html = tmp_path / "brief.html"
        html.write_text('<html><img src="cid:cover.jpg" alt=""></html>', encoding="utf-8")
        images = tmp_path / "images"
        images.mkdir()
        # 1×1 JPEG — MIME test only, not a price or Insights source.
        images.joinpath("cover.jpg").write_bytes(
            b"\xff\xd8\xff\xdb\x00C\x00"
            + (b"\x08" * 64)
            + b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            + b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\xff\xd9"
        )
        isolated = env.copy()
        isolated["HOME"] = str(tmp_path)
        no_token = subprocess.run(
            [
                sys.executable,
                "-m",
                "vfops.gmail_brief_send",
                "--html",
                str(html),
                "--images",
                str(images),
                "--to",
                "nocturney@gmail.com",
                "--subject",
                "brief send check",
            ],
            cwd=ROOT,
            env=isolated,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        if no_token.returncode != 2:
            fail(
                "gmail_brief_send must exit 2 without token: "
                f"{no_token.returncode} {no_token.stderr or no_token.stdout}"
            )
        if "no token" not in (no_token.stderr or "").lower():
            fail("gmail_brief_send must print no token on stderr when creds are missing")

        sys.path.insert(0, str(ROOT / "packages"))
        from vfops.gmail_brief_send import build_mime, iter_images

        parts = iter_images(images)
        if [p.name for p in parts] != ["cover.jpg"]:
            fail(f"iter_images should pick cover.jpg, got {[p.name for p in parts]}")
        mime = build_mime(
            html=html.read_text(encoding="utf-8"),
            images=parts,
            to="nocturney@gmail.com",
            subject="cid check",
        )
        blob = mime.as_string()
        if "Content-ID: <cover.jpg>" not in blob:
            fail("MIME Content-ID must equal the image filename")
        if "multipart/related" not in blob:
            fail("MIME must be multipart/related")
        html_payload = mime.get_payload()[0].get_payload(decode=True) or b""
        if b'<img src="cid:cover.jpg"' not in html_payload:
            fail("HTML cid: must survive into the MIME HTML part")

    print("OK vfops-loop wired into orchestra+brief+handoff + consumers")


if __name__ == "__main__":
    main()
