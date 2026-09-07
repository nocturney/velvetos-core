#!/usr/bin/env python3
"""Office activation loop — consume every pack into the daily brief.

No network. No send. No invented ₪ or Insights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LOOP_JSON = ROOT / "packages" / "vfops" / "LOOP.json"
MANIFEST = ROOT / "packages" / "manifest.json"
RESEARCH = ROOT / "packages" / "vfops" / "data" / "research.md"
FOLLOWER = ROOT / "packages" / "vfgrowth" / "hq" / "FOLLOWER-GROWTH.md"
WEEK = ROOT / "packages" / "vfsku" / "week.md"
HANDOFF = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
EDIT_GATE = ROOT / "packages" / "vfgrowth" / "EDIT-GATE.md"
PREFLIGHT = ROOT / "packages" / "vfgrowth" / "PREFLIGHT.md"
CAL_OPS = ROOT / "packages" / "vfgrowth" / "CALENDAR-OPS.md"
STATUS = ROOT / "packages" / "vfops" / "hq" / "STATUS-he.md"
STUDIO = ROOT / "constitution" / "STUDIO.md"
INSTANCE = ROOT / "constitution" / "INSTANCE.md"
SKILLS = ROOT / ".cursor" / "skills"
CONNECT_IG = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"
INSIGHTS = ROOT / "packages" / "vfinsights" / "READ.md"
LEARNINGS = ROOT / "packages" / "vfinsights" / "LEARNINGS.md"
BIZ_LOCK = ROOT / "packages" / "vfbiz" / "LOCK.md"
BIZ_WEEK = ROOT / "packages" / "vfbiz" / "out" / "week.md"
FLOOR = ROOT / "packages" / "vfcost" / "FLOOR-CARD.md"
COPY_DIR = ROOT / "packages" / "vfcopy"
STORIES_FIX = COPY_DIR / "G004-STORIES-FIX.md"
VFSKU = ROOT / "scripts" / "vfsku.py"
VFCOST = ROOT / "scripts" / "vfcost.py"
CLI_LOG = ROOT / "packages" / "vfops" / "data" / "cli-runs.jsonl"
TZ = ZoneInfo("Asia/Jerusalem")
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
DAILY_CADENCE = {"daily-07:00", "daily-06:15", "daily-03", "daily-growth"}
AUDIT_PACKS = {
    "vfcopy",
    "vfcovers",
    "vfcanva",
    "vfgrowth",
    "vfcost",
    "vfops",
    "vfbiz",
    "vfsales",
    "vfinsights",
    "vfresearch",
    "vfsku",
}

CAPTION_FILES = (
    STORIES_FIX if STORIES_FIX.is_file() else COPY_DIR / "G004.md",
    COPY_DIR / "G004.md",
    COPY_DIR / "G003.md",
    COPY_DIR / "G005-d12b.md",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_loop() -> dict:
    return json.loads(LOOP_JSON.read_text())


def first_fence(text: str) -> str:
    parts = text.split("```")
    if len(parts) < 2:
        return ""
    body = parts[1]
    if body.startswith("\n"):
        body = body[1:]
    return body.strip()


def fence_after_heading(path: Path, needles: tuple[str, ...]) -> str:
    if not path.is_file():
        return ""
    text = path.read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if any(n in line for n in needles) and line.startswith("#"):
            rest = "\n".join(lines[i:])
            block = first_fence(rest)
            if block:
                return block
    return first_fence(text)


def append_cli_run(name: str, argv: list[str], ok: bool) -> None:
    CLI_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.now(TZ).isoformat(timespec="seconds"),
        "name": name,
        "cmd": " ".join(argv),
        "ok": ok,
    }
    with CLI_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_cmd(args: list[str], *, name: str | None = None) -> str:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    out = (proc.stdout or "").strip()
    ok = proc.returncode == 0
    label = name or (Path(args[1]).name if len(args) > 1 else args[0])
    append_cli_run(label, [str(a) for a in args], ok)
    if not ok:
        err = (proc.stderr or "").strip()
        return f"חסר פלט · {(err or out)[:160]}"
    return out


def cli_runs_last_24h() -> list[str]:
    if not CLI_LOG.is_file():
        return []
    cutoff = datetime.now(TZ).timestamp() - 24 * 3600
    lines: list[str] = []
    seen: set[str] = set()
    for raw in CLI_LOG.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = rec.get("ts") or ""
        try:
            when = datetime.fromisoformat(ts)
            if when.tzinfo is None:
                when = when.replace(tzinfo=TZ)
            if when.timestamp() < cutoff:
                continue
        except ValueError:
            continue
        cmd = rec.get("cmd") or rec.get("name") or ""
        if not cmd or cmd in seen:
            continue
        seen.add(cmd)
        stamp = when.strftime("%H:%M")
        flag = "" if rec.get("ok", True) else " · נכשל"
        lines.append(f"{stamp} · {cmd}{flag}")
    return lines


def gap_lines(invoked: set[str]) -> str:
    data = load_loop()
    rows: list[str] = []
    # on-content / on-inquiry are intentional non-morning cadences — not “failed to run”.
    skip_gap_cadence = {"on-content", "on-inquiry", "weekly", "bi-daily", "daily-eod"}
    for row in data.get("packs") or []:
        pid = row.get("id") or ""
        cadence = row.get("cadence") or ""
        if cadence in skip_gap_cadence:
            continue
        watch = pid in AUDIT_PACKS or cadence in DAILY_CADENCE
        if not watch or pid in invoked:
            continue
        blocked = row.get("blocked")
        extra = f" · {blocked}" if blocked else ""
        rows.append(f"פער: {pid} לא הורץ · {row.get('consume')}{extra}")
    if not rows:
        return ""
    return "פערים (לא הורץ הבוקר)\n" + "\n".join(rows)


def sku_line() -> str:
    line = run_cmd([sys.executable, str(VFSKU), "brief"], name="vfsku.py brief")
    week = fence_after_heading(WEEK, ("בלוק לבריף",))
    if week:
        return f"{line}\n{week}"
    return line


def cost_line() -> str:
    if not VFCOST.is_file():
        fail("vfcost CLI missing — expected scripts/vfcost.py from main")
    return run_cmd([sys.executable, str(VFCOST), "brief"], name="vfcost.py brief")


def growth_line() -> str:
    block = fence_after_heading(FOLLOWER, ("בלוק לבריף",))
    if block:
        return block
    return (
        "היילייטס + וואטסאפ 050-2517000 — לא DM\n"
        "B2B נעול · איסוף שדרות"
    )


def biz_week_line() -> str:
    block = fence_after_heading(BIZ_WEEK, ("בלוק לבריף",))
    if block:
        return block
    return "B2B נעול (`vfbiz`). סגירה: וואטסאפ 050-2517000 · איסוף שדרות."


def captions_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    seen: set[str] = set()
    for path in CAPTION_FILES:
        if not path.is_file():
            continue
        stem = path.stem.split(".")[0]
        if stem in seen:
            continue
        seen.add(stem)
        text = path.read_text()
        hook = fence_after_heading(path, ("להדבקה", "ארבעה פריימים"))
        first = hook.splitlines()[0] if hook else path.stem
        status = "מוכן להדבקה"
        if "משובץ" in text:
            status = "נעול · משובץ"
        if "לא מאושר" in text:
            status = "טיוטה"
        rows.append([stem, first[:48], status])
    if not rows:
        rows.append(["אין", "אין כיתוב מוכן", "חסר"])
    return rows


ROUTINE_BRIEF_CLI = ("vfcost.py brief", "vfsku.py brief")


def office_line(invoked: set[str]) -> str:
    runs = [
        r
        for r in cli_runs_last_24h()
        if not any(tag in r for tag in ROUTINE_BRIEF_CLI)
    ]
    if runs:
        built = "05 · משרד\nמה נבנה / יועל:\n" + "\n".join(f"CLI {r}" for r in runs)
    else:
        built = "05 · משרד\nאין חדש במשרד"
    consumers = consumer_brief_lines()
    built = f"{built}\n{consumers}"
    gaps = gap_lines(invoked)
    if gaps:
        return f"{built}\n{gaps}"
    return built


def insights_line() -> str:
    if LEARNINGS.is_file():
        text = LEARNINGS.read_text(encoding="utf-8").strip()
        if text:
            first = next((l for l in text.splitlines() if l.strip()), "").strip("# ").strip()
            if first:
                return f"Insights: {first} · מקור {LEARNINGS.relative_to(ROOT)}"
    if CONNECT_IG.is_file() and "needsAuth" in CONNECT_IG.read_text():
        return "Insights: אין ספירה · ig-mcp needsAuth עד CONNECT-IG.md (צעד אדם)"
    return "Insights: אין ספירה"




# --- Daily consumers (run ≠ brief ≠ check) ---------------------------------
# run: execute eligible tasks once (no check-all; no auto G005 render)
# brief/assemble: read artifacts + prior CLI runs into the packet
# check: integrity only (may assemble in-memory; must not recurse into run)

INSIGHTS_LOOP = ROOT / "packages" / "vfinsights" / "scripts" / "vf_insights_loop.py"
INSIGHTS_CSV = ROOT / "packages" / "vfinsights" / "data" / "posts.csv"
RESEARCH_DAILY = ROOT / "packages" / "vfresearch" / "DAILY.md"
RESEARCH_MD = ROOT / "packages" / "vfops" / "data" / "research.md"
QUOTE_LADDER = ROOT / "packages" / "vfsales" / "scripts" / "vf_quote_ladder.py"
QUOTE_MD = ROOT / "packages" / "vfsales" / "QUOTE.md"
VELVETOS_CLI = ROOT / "scripts" / "velvetos.py"
CONSUMER_STATE = ROOT / "packages" / "vfops" / "data" / "consumer-runs.jsonl"


@dataclass
class ConsumerSpec:
    id: str
    title: str
    cadence: str
    kind: str  # exec | verify | skip
    argv: list[str] = field(default_factory=list)
    timeout_s: int = 90
    requires: tuple[Path, ...] = ()
    artifact: Path | None = None
    pack: str = ""
    auto_daily: bool = False
    skip_reason: str = ""


def consumer_registry() -> list[ConsumerSpec]:
    """Map LOOP packs onto real entrypoints. Playbooks are not Python commands."""
    return [
        ConsumerSpec(
            id="velvetos-modules",
            title="velvetos modules",
            cadence="on-instance",
            kind="exec",
            argv=[sys.executable, str(VELVETOS_CLI), "modules"],
            timeout_s=60,
            requires=(VELVETOS_CLI,),
            pack="velvetos",
            auto_daily=True,
        ),
        ConsumerSpec(
            id="vfinsights-loop",
            title="vfinsights measurement loop",
            cadence="daily-07:00",
            kind="exec",
            argv=[sys.executable, str(INSIGHTS_LOOP), "--data", str(INSIGHTS_CSV)],
            timeout_s=60,
            requires=(INSIGHTS_LOOP, INSIGHTS_CSV),
            artifact=LEARNINGS,
            pack="vfinsights",
            auto_daily=True,
        ),
        ConsumerSpec(
            id="vfresearch-daily",
            title="vfresearch daily playbook status",
            cadence="daily-06:15",
            kind="verify",
            requires=(RESEARCH_DAILY, RESEARCH_MD),
            artifact=RESEARCH_MD,
            pack="vfresearch",
            auto_daily=True,
            skip_reason="",  # verify only — DAILY.md is a playbook, not scripts/vfresearch.py
        ),
        ConsumerSpec(
            id="vfsales-quote",
            title="vfsales quote ladder",
            cadence="on-inquiry",
            kind="skip",
            argv=[sys.executable, str(QUOTE_LADDER), "--task-id", "vfops-loop-skip"],
            requires=(QUOTE_LADDER, QUOTE_MD),
            pack="vfsales",
            auto_daily=False,
            skip_reason="on-inquiry only — no automatic quote without known fields / lead ILS",
        ),
        ConsumerSpec(
            id="vfcanva-render",
            title="vfcanva studio render",
            cadence="on-content",
            kind="skip",
            requires=(ROOT / "packages" / "vfcanva" / "studio" / "render.py",),
            pack="vfcanva",
            auto_daily=False,
            skip_reason="on-content only — do not auto-render a standing pack (e.g. G005)",
        ),
        ConsumerSpec(
            id="vfcovers-compose",
            title="vfcovers compose",
            cadence="on-content",
            kind="skip",
            requires=(ROOT / "packages" / "vfcovers" / "g005" / "compose_slides.py",),
            pack="vfcovers",
            auto_daily=False,
            skip_reason="on-content only — composing G005 requires an explicit content job",
        ),
        ConsumerSpec(
            id="sensor-suite",
            title="check-all sensor suite",
            cadence="ci/check",
            kind="skip",
            pack="vfharness",
            auto_daily=False,
            skip_reason="integrity belongs to `vfops_loop.py check` / CI — never from run/assemble (recursion)",
        ),
    ]


def _today_key(today: str, consumer_id: str) -> str:
    return f"{today}:{consumer_id}"


def consumer_already_ran(today: str, consumer_id: str) -> bool:
    if not CONSUMER_STATE.is_file():
        return False
    key = _today_key(today, consumer_id)
    for raw in CONSUMER_STATE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if rec.get("key") == key and rec.get("ok") is True:
            return True
    return False


def append_consumer_run(today: str, spec: ConsumerSpec, *, ok: bool, detail: str) -> None:
    CONSUMER_STATE.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.now(TZ).isoformat(timespec="seconds"),
        "key": _today_key(today, spec.id),
        "id": spec.id,
        "pack": spec.pack,
        "ok": ok,
        "detail": detail[:240],
    }
    with CONSUMER_STATE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    append_cli_run(spec.id, spec.argv or [spec.kind, spec.id], ok)


def run_consumer(spec: ConsumerSpec, *, today: str, force: bool = False) -> dict:
    """Run one consumer. Returns a structured result — never claims done on skip/fail."""
    if spec.kind == "skip" or not spec.auto_daily:
        return {
            "id": spec.id,
            "status": "skipped",
            "reason": spec.skip_reason or f"cadence {spec.cadence} not auto-daily",
        }
    if not force and consumer_already_ran(today, spec.id):
        return {"id": spec.id, "status": "skipped", "reason": "already ran successfully today"}
    missing = [str(p.relative_to(ROOT)) for p in spec.requires if not p.is_file()]
    if missing:
        detail = "חסר קלט: " + ", ".join(missing)
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}

    if spec.kind == "verify":
        # Playbook present + research.md readable — not "we tried to run a missing .py"
        detail = f"verified {' · '.join(str(p.relative_to(ROOT)) for p in spec.requires)}"
        append_consumer_run(today, spec, ok=True, detail=detail)
        return {"id": spec.id, "status": "ok", "detail": detail, "pack": spec.pack}

    if spec.kind != "exec":
        detail = f"unknown kind {spec.kind}"
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}

    try:
        proc = subprocess.run(
            spec.argv,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=spec.timeout_s,
        )
    except subprocess.TimeoutExpired:
        detail = f"timeout after {spec.timeout_s}s"
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}
    except FileNotFoundError as exc:
        detail = f"executable missing: {exc}"
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}

    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        detail = (out.splitlines() or ["nonzero exit"])[0][:200]
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}
    if spec.artifact is not None and not spec.artifact.is_file():
        detail = f"expected artifact missing: {spec.artifact.relative_to(ROOT)}"
        append_consumer_run(today, spec, ok=False, detail=detail)
        return {"id": spec.id, "status": "failed", "reason": detail}
    detail = (out.splitlines() or ["ok"])[0][:200]
    append_consumer_run(today, spec, ok=True, detail=detail)
    return {"id": spec.id, "status": "ok", "detail": detail, "pack": spec.pack}


def run_daily_consumers(*, today: str | None = None, force: bool = False) -> list[dict]:
    """Execute eligible daily tasks once. Does not assemble brief. Does not run check-all."""
    day = today or datetime.now(TZ).date().isoformat()
    results: list[dict] = []
    for spec in consumer_registry():
        results.append(run_consumer(spec, today=day, force=force))
    return results


def consumer_brief_lines(results: list[dict] | None = None) -> str:
    if results is None:
        # Summarize today's consumer-runs file for brief assembly
        today = datetime.now(TZ).date().isoformat()
        if not CONSUMER_STATE.is_file():
            return "צרכנים: אין הרצה היום"
        rows = []
        for raw in CONSUMER_STATE.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not str(rec.get("key", "")).startswith(today + ":"):
                continue
            flag = "ok" if rec.get("ok") else "נכשל"
            rows.append(f"{rec.get('id')} · {flag} · {rec.get('detail', '')}")
        if not rows:
            return "צרכנים: אין הרצה היום"
        return "צרכנים היום:\n" + "\n".join(rows[-12:])
    lines = []
    for r in results:
        if r["status"] == "ok":
            lines.append(f"{r['id']} · בוצע · {r.get('detail', '')}")
        elif r["status"] == "skipped":
            lines.append(f"{r['id']} · דולג · {r.get('reason', '')}")
        else:
            lines.append(f"{r['id']} · נכשל · {r.get('reason', '')}")
    return "צרכנים:\n" + "\n".join(lines)


def assemble(today: str) -> dict:
    invoked: set[str] = {"vfops"}
    sku = sku_line()
    invoked.add("vfsku")
    cost = cost_line()
    invoked.add("vfcost")
    growth = growth_line()
    invoked.add("vfgrowth")
    biz = biz_week_line()
    invoked.add("vfbiz")
    insights = insights_line()
    invoked.add("vfinsights")
    captions = captions_rows()
    invoked.add("vfcopy")
    # Packs already consumed by today's successful consumer runs
    if CONSUMER_STATE.is_file():
        for raw in CONSUMER_STATE.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if str(rec.get("key", "")).startswith(today + ":") and rec.get("ok") and rec.get("pack"):
                invoked.add(str(rec["pack"]))
    office = office_line(invoked)
    return {
        "date_line": f"{today} · בריף סוכנות · תצוגה 3",
        "bottom_line": "המשרד רץ. כריסטיאן יכול לשבת רגוע — בלי ₪ מומצא, בלי Insights מומצאים, בלי חצי-עבודה.",
        "footer": "Velvet Factory · סוכנות פנימית · איסוף משדרות",
        "slots": [
            {
                "kicker": "01 · קודם החלטה",
                "title": "החלטות",
                "prose": "מחיר מכירה דחה עד סכום מראש צוות. כיתוב G004 סטוריז = G004-STORIES-FIX.md. שיבוץ בלי לשאול משבצת — אחרי שער עריכה (Canva/vfcovers).",
                "headers": ["החלטה", "כן/לא/דחה", "מועד"],
                "rows": [
                    ["מחיר מכירה", "דחה", "X ₪"],
                    ["כיתוב G004 סטוריז", "כן", "vfcopy/G004-STORIES-FIX.md"],
                    ["ig-mcp Publish", "דחה", "needsAuth"],
                ],
            },
            {
                "kicker": "02 · כסף בעבודה",
                "title": "הזמנות ומעקב",
                "prose": f"פנייה חדשה: אין ספירה. חוב/שולם: אין ספירה.\n{cost}",
                "headers": ["קוד", "שלב", "חסם"],
                "rows": [
                    ["פנייה", "אין", "אין ספירה"],
                    ["ספר", "אין ספירה", "vfbooks"],
                    ["חומר", "vfcost.py brief", "בלי ₪ מכירה"],
                ],
            },
            {
                "kicker": "03 · מה להדפיס ולפרסם",
                "title": "מדף",
                "prose": sku,
            },
            {
                "kicker": "04",
                "title": "איך הסטודיו מרוויח",
                "prose": f"{growth}\n{biz}",
            },
            {
                "kicker": "05 · משרד",
                "title": "מה נבנה / יועל",
                "prose": office,
            },
            {
                "kicker": "06",
                "title": "מה קורה בעמוד",
                "prose": f"{insights} · בלי חדשות רעות מומצאות לבעלים · מדדים חלשים נשארים פער פנימי.",
            },
            {
                "kicker": "07 · פיד בסוף",
                "title": "מה עולה בפיד",
                "prose": "מסירה: vfgrowth/HANDOFF-he.md · PREFLIGHT.md חובה לפני שיבוץ (VOICE + Canva/vfcovers + ציון עצמי + קומפס) · סטוריז G004 = vfcopy/G004-STORIES-FIX.md · שער עריכה קשיח: Canva MCP או vfcovers/vfcanva — לא JPEG גולמי · נכשל-סגור = חסום · פער סוכנות = שורת פער למשרד, לא אשמת בעלים · סטוריז ב-instagram.com · לוח אוטונומי.",
                "headers": ["מזהה", "פתיחה", "מצב"],
                "rows": captions,
            },
        ],
    }


def cmd_inventory(_args: argparse.Namespace) -> int:
    data = load_loop()
    packs = {p["id"] for p in data.get("packs") or []}
    manifest = {p["name"] for p in json.loads(MANIFEST.read_text()).get("packs") or []}
    dirs = {p.name for p in (ROOT / "packages").iterdir() if p.is_dir()}
    missing = sorted(dirs - packs)
    extra = sorted(packs - dirs)
    print("מלאי לולאה · פק | סוג | קצב | חסום")
    for row in data.get("packs") or []:
        blocked = row.get("blocked") or "—"
        print(f"{row['id']:<14}{row['kind']:<16}{row['cadence']:<18}{blocked}")
    print(f"packs={len(packs)} dirs={len(dirs)} manifest={len(manifest)}")
    if missing:
        fail(f"LOOP.json missing dirs: {missing}")
    if extra:
        fail(f"LOOP.json extra ids: {extra}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run eligible daily consumers once. Never runs check-all. Never auto-renders G005."""
    today = args.date or datetime.now(TZ).date().isoformat()
    results = run_daily_consumers(today=today, force=bool(args.force))
    print(consumer_brief_lines(results))
    # Surface failures without claiming the whole office failed on intentional skips
    failed = [r for r in results if r["status"] == "failed"]
    if failed:
        print(f"FAIL consumers failed={len(failed)}", file=sys.stderr)
        return 1
    print("OK daily consumers")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    today = args.date or datetime.now(TZ).date().isoformat()
    brief = assemble(today)
    print("=== בריף לולאה ===")
    print(brief["date_line"])
    for slot in brief["slots"]:
        print(f"\n{slot['kicker']} · {slot['title']}")
        if slot.get("prose"):
            print(slot["prose"])
        for row in slot.get("rows") or []:
            print(" · ".join(row))
    if args.write:
        out = ROOT / "packages" / "vfops" / "hq" / f"brief-{today}.json"
        out.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n")
        print(f"\nנכתב {out.relative_to(ROOT)}")
        write_status(today)
        print(f"נכתב {STATUS.relative_to(ROOT)}")
    return 0


def write_status(today: str) -> None:
    data = load_loop()
    lines = [
        f"# סטטוס לולאת משרד · {today}",
        "",
        "רף: סוכנות פרסום+תפעול יקרה. הבעלים יושב רגוע.",
        "",
        "## רץ אוטומטית עכשיו",
        "",
        "- `vfops_loop.py brief` — בריף סוכנות מפקים חיים",
        "- `vfcost.py brief` — עלות חומר חיה בחריץ 02 (בלי ₪ מכירה)",
        "- מדף `vfsku.py brief` + `week.md`",
        "- FOLLOWER-GROWTH · היילייטס + וואטסאפ",
        "- כיתובי vfcopy (G003/G004 + G004-STORIES-FIX / G005)",
        "- חריץ 05 = CLI מ-24ש או אין חדש · פער לפק שלא הורץ",
        "- מסירת סטודיו + שער עריכה קשיח (אין סטוריז בלי Canva/vfcovers) + לוח אוטונומי",
        "- Canva MCP ready · Gmail/Calendar/Drive ready",
        "",
        "## חסום על אדם / לוגין",
        "",
        "- ig-mcp **needsAuth** עד טוקן Meta (`CONNECT-IG.md` צעד אדם)",
        "- Insights = אין ספירה",
        "- סטוריז = instagram.com (ig-mcp ≠ stories)",
        "- מדף MakerWorld 0/5 עד GATE+רישיון+סלייס",
        "- מדיית G004 בתיבת Grok (Cloud לא רואה) + שער עריכה",
        "- B2B נעול · וואטסאפ לקוח = אדם 050-2517000",
        "",
        "## מלאי פקים",
        "",
        "| פק | סוג | קצב | חסום |",
        "|---|---|---|---|",
    ]
    for row in data.get("packs") or []:
        blocked = row.get("blocked") or "—"
        lines.append(f"| `{row['id']}` | {row['kind']} | {row['cadence']} | {blocked} |")
    lines.append("")
    STATUS.write_text("\n".join(lines) + "\n")


def cmd_status(_args: argparse.Namespace) -> int:
    today = datetime.now(TZ).date().isoformat()
    write_status(today)
    print(STATUS.read_text())
    return 0


def cmd_weekly(_args: argparse.Namespace) -> int:
    data = load_loop()
    print("=== צריכה שבועית / דו-יומית ===")
    weekly = ("weekly", "bi-daily", "daily-eod")
    for row in data.get("packs") or []:
        if row.get("cadence") in weekly or row["id"] in {"vfresearch", "vfbooks", "vfmakers"}:
            print(f"{row['id']:<12} {row['cadence']:<16} {row['consume']}")
    print("קישורים: packages/vfresearch/WEEKLY.md")
    print("best-skills: packages/vfresearch/BEST-SKILLS.md")
    print("דופק הכנסה: packages/vfops/playbooks/WEEKLY-REVENUE-PULSE.md")
    return 0


def cmd_handoff(_args: argparse.Namespace) -> int:
    print("=== מסירה לסטודיו · פתח כל בוקר ===")
    print("רף: סוכנות יקרה · לא חצי-עבודה")
    print("קובץ: packages/vfgrowth/HANDOFF-he.md")
    print("חבילה: G004 קטלבל-מחזיק · vfcopy/G004-STORIES-FIX.md")
    print("שער עריכה: Canva MCP או vfcovers/vfcanva — לא JPEG גולמי · אין סטוריז בלי מעבר")
    print("פריפלייט חובה: packages/vfgrowth/PREFLIGHT.md + preflight/<id>.md")
    print("בלי ארטיפקט עבור = נכשל-סגור · לא משבצים")
    print("אל תפנה לכריסטיאן על מדדים חלשים")
    print("לוח: אוטונומי · לא שואלים משבצת · Calendar-OPS")
    print("CTA: וואטסאפ 050-2517000 · היילייטס · איסוף שדרות · לא DM")
    print("סטוריז: instagram.com · ig-mcp ≠ stories")
    print("מחיר: X ₪")
    if CONNECT_IG.is_file():
        print("IG: needsAuth · CONNECT-IG.md צעד אדם")
    print()
    if HANDOFF.is_file():
        print(HANDOFF.read_text().split("## קופי")[0].strip()[:1400])
    return 0


def cmd_check(_args: argparse.Namespace) -> int:
    data = load_loop()
    packs = {p["id"] for p in data.get("packs") or []}
    dirs = {p.name for p in (ROOT / "packages").iterdir() if p.is_dir()}
    if packs != dirs:
        fail(f"LOOP.json/dirs mismatch missing={sorted(dirs-packs)} extra={sorted(packs-dirs)}")
    for row in data.get("packs") or []:
        consume = row.get("consume") or ""
        optional = row.get("consumeOptional")
        if consume.startswith("python3 "):
            script = consume.split()[1]
            path = ROOT / script
            if not path.is_file() and not optional:
                fail(f"{row['id']} consume missing {script}")
        elif consume.startswith("packages/") or consume.startswith("scripts/"):
            path = ROOT / consume.split()[0]
            if not path.is_file() and not optional:
                fail(f"{row['id']} consume missing {consume}")
        if row["id"] == "vfcost" and VFCOST.is_file():
            # Other agent landed CLI — consume it, do not rewrite.
            pass
    for guide in data.get("guides") or []:
        path = ROOT / guide["path"]
        if not path.is_file():
            fail(f"guide missing {guide['path']}")
    today = datetime.now(TZ).date().isoformat()
    brief = assemble(today)
    blob = json.dumps(brief, ensure_ascii=False)
    if not VFCOST.is_file():
        fail("scripts/vfcost.py must exist for live consume")
    for needle in (
        "050-2517000",
        "אין ספירה",
        "X ₪",
        "G004",
        "needsAuth",
        "סוכנות",
        "שער עריכה",
        "עלות חומר",
        "פער",
        "G004-STORIES-FIX",
        "PREFLIGHT.md",
    ):
        if needle not in blob:
            fail(f"assembled brief missing {needle!r}")
    if "רמה נמוכה" in blob:
        fail("assembled brief must not surface רמה נמוכה to the owner")
    if "אין חדש במשרד" not in blob and "CLI " not in blob:
        fail("slot 05 must list real CLI runs or אין חדש במשרד")
    if "מה נבנה / יועל: קול פיד" in blob:
        fail("slot 05 must not paste catalog activity as a build")
    for m in ILS_NUMBER.finditer(blob):
        snippet = blob[max(0, m.start() - 12) : m.end() + 8]
        if "X ₪" in snippet or "בלי ₪" in snippet:
            continue
        fail(f"possible invented ILS in brief: {snippet!r}")
    if "שלחו DM" in blob and "לא DM" not in blob:
        fail("brief must not instruct שלחו DM")
    for path in (EDIT_GATE, PREFLIGHT, CAL_OPS, STUDIO, INSTANCE, HANDOFF):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        text = path.read_text()
        if "רף סוכנות" not in text and path in (STUDIO, INSTANCE):
            fail(f"{path.relative_to(ROOT)} missing רף סוכנות")
        if path == EDIT_GATE and "JPEG גולמי" not in text:
            fail("EDIT-GATE.md must forbid JPEG גולמי")
        if path == CAL_OPS and "לא שואלים" not in text:
            fail("CALENDAR-OPS.md must lock autonomous slots")
    preflight = PREFLIGHT.read_text()
    for needle in ("VOICE.md", "VOICE-RESEARCH", "נכשל-סגור", "רמה נמוכה", "ציון עצמי", "2–3"):
        if needle not in preflight:
            fail(f"PREFLIGHT.md must mention {needle}")
    if "אל תפנה לכריסטיאן על מדדים חלשים" not in HANDOFF.read_text():
        fail("HANDOFF-he.md must lock אל תפנה לכריסטיאן על מדדים חלשים")
    guide_paths = {g["path"] for g in data.get("guides") or []}
    if SKILLS.is_dir():
        for skill in sorted(SKILLS.iterdir()):
            if not skill.name.startswith("vf-"):
                continue
            rel = f".cursor/skills/{skill.name}/SKILL.md"
            if rel not in guide_paths:
                fail(f"LOOP.json guides missing skill {rel}")
    print("OK vfops-loop inventory+brief+agency-bar")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Velvet Factory office activation loop")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory", help="list every pack kind/cadence").set_defaults(func=cmd_inventory)
    run_p = sub.add_parser("run", help="run eligible daily consumers once (no check-all, no auto G005)")
    run_p.add_argument("--date")
    run_p.add_argument("--force", action="store_true", help="re-run even if already ok today")
    run_p.set_defaults(func=cmd_run)
    brief = sub.add_parser("brief", help="assemble 07:00 packet from live packs")
    brief.add_argument("--write", action="store_true")
    brief.add_argument("--date")
    brief.set_defaults(func=cmd_brief)
    sub.add_parser("handoff", help="Studio daily open path").set_defaults(func=cmd_handoff)
    sub.add_parser("status", help="Hebrew auto-vs-blocked board").set_defaults(func=cmd_status)
    sub.add_parser("weekly", help="weekly consume steps").set_defaults(func=cmd_weekly)
    sub.add_parser("check", help="sensor").set_defaults(func=cmd_check)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
