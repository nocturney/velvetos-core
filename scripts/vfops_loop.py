#!/usr/bin/env python3
"""Office activation loop — consume every pack into the daily brief.

No network. No send. No invented ₪ or Insights.
"""
from __future__ import annotations

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
CAL_OPS = ROOT / "packages" / "vfgrowth" / "CALENDAR-OPS.md"
STATUS = ROOT / "packages" / "vfops" / "hq" / "STATUS-he.md"
STUDIO = ROOT / "constitution" / "STUDIO.md"
INSTANCE = ROOT / "constitution" / "INSTANCE.md"
SKILLS = ROOT / ".cursor" / "skills"
CONNECT_IG = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"
INSIGHTS = ROOT / "packages" / "vfinsights" / "READ.md"
BIZ_LOCK = ROOT / "packages" / "vfbiz" / "LOCK.md"
FLOOR = ROOT / "packages" / "vfcost" / "FLOOR-CARD.md"
COPY_DIR = ROOT / "packages" / "vfcopy"
VFSKU = ROOT / "scripts" / "vfsku.py"
VFCOST = ROOT / "scripts" / "vfcost.py"
TZ = ZoneInfo("Asia/Jerusalem")
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")

CAPTION_FILES = (
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


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        return f"חסר פלט · {(err or out)[:160]}"
    return out


def sku_line() -> str:
    line = run_cmd([sys.executable, str(VFSKU), "brief"])
    week = fence_after_heading(WEEK, ("בלוק לבריף",))
    if week:
        return f"{line}\n{week}"
    return line


def cost_line() -> str:
    if not VFCOST.is_file():
        fail("vfcost CLI missing — expected scripts/vfcost.py from main")
    return run_cmd([sys.executable, str(VFCOST), "brief"])


def growth_line() -> str:
    block = fence_after_heading(FOLLOWER, ("בלוק לבריף",))
    if block:
        return block
    return (
        "היילייטס + וואטסאפ 050-2517000 — לא DM\n"
        "B2B נעול · איסוף שדרות"
    )


def captions_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for path in CAPTION_FILES:
        if not path.is_file():
            continue
        text = path.read_text()
        hook = fence_after_heading(path, ("להדבקה",))
        first = hook.splitlines()[0] if hook else path.stem
        status = "מוכן להדבקה"
        if "משובץ" in text:
            status = "נעול · משובץ"
        if "לא מאושר" in text:
            status = "טיוטה"
        rows.append([path.stem.split(".")[0], first[:48], status])
    if not rows:
        rows.append(["אין", "אין כיתוב מוכן", "חסר"])
    return rows


def office_line() -> str:
    block = fence_after_heading(RESEARCH, ("05", "מה נבנה"))
    if block:
        return block
    text = RESEARCH.read_text() if RESEARCH.is_file() else ""
    if "אין חדש במשרד" in text:
        return "05 · משרד\nאין חדש במשרד"
    return "05 · משרד\nאין חדש במשרד"


def insights_line() -> str:
    if CONNECT_IG.is_file() and "needsAuth" in CONNECT_IG.read_text():
        return "Insights: אין ספירה · ig-mcp needsAuth עד CONNECT-IG.md (צעד אדם)"
    return "Insights: אין ספירה"


def assemble(today: str) -> dict:
    sku = sku_line()
    cost = cost_line()
    growth = growth_line()
    office = office_line()
    insights = insights_line()
    captions = captions_rows()
    return {
        "date_line": f"{today} · בריף סוכנות · תצוגה 3",
        "bottom_line": "המשרד רץ. כריסטיאן יכול לשבת רגוע — בלי ₪ מומצא, בלי Insights מומצאים, בלי חצי-עבודה.",
        "footer": "Velvet Factory · סוכנות פנימית · איסוף משדרות",
        "slots": [
            {
                "kicker": "01 · קודם החלטה",
                "title": "החלטות",
                "prose": "מחיר מכירה דחה עד סכום מראש צוות. כיתוב G004 מוכן. שיבוץ בלי לשאול משבצת — אחרי שער עריכה.",
                "headers": ["החלטה", "כן/לא/דחה", "מועד"],
                "rows": [
                    ["מחיר מכירה", "דחה", "X ₪"],
                    ["כיתוב G004 לסטודיו", "כן", "vfcopy/G004.md"],
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
                "prose": f"{growth}\nB2B נעול (`vfbiz`). סגירה: וואטסאפ 050-2517000 · איסוף שדרות.",
            },
            {
                "kicker": "05 · משרד",
                "title": "מה נבנה / יועל",
                "prose": office,
            },
            {
                "kicker": "06",
                "title": "מה קורה בעמוד",
                "prose": insights,
            },
            {
                "kicker": "07 · פיד בסוף",
                "title": "מה עולה בפיד",
                "prose": "מסירה: vfgrowth/HANDOFF-he.md · שער עריכה (Canva/vfcovers) לפני שיבוץ — לא JPEG גולמי · סטוריז ב-instagram.com · לוח אוטונומי.",
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
        "- כיתובי vfcopy (G003/G004/G005)",
        "- מסירת סטודיו + שער עריכה + לוח אוטונומי",
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
    print("חבילה: G004 קטלבל-מחזיק · vfcopy/G004.md")
    print("שער עריכה: Canva / vfcovers / vfcanva — לא JPEG גולמי")
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
    for needle in ("050-2517000", "אין ספירה", "X ₪", "G004", "needsAuth", "סוכנות", "שער עריכה", "עלות חומר"):
        if needle not in blob:
            fail(f"assembled brief missing {needle!r}")
    for m in ILS_NUMBER.finditer(blob):
        snippet = blob[max(0, m.start() - 12) : m.end() + 8]
        if "X ₪" in snippet or "בלי ₪" in snippet:
            continue
        fail(f"possible invented ILS in brief: {snippet!r}")
    if "שלחו DM" in blob and "לא DM" not in blob:
        fail("brief must not instruct שלחו DM")
    for path in (EDIT_GATE, CAL_OPS, STUDIO, INSTANCE, HANDOFF):
        text = path.read_text()
        if "רף סוכנות" not in text and path in (STUDIO, INSTANCE):
            fail(f"{path.relative_to(ROOT)} missing רף סוכנות")
        if path == EDIT_GATE and "JPEG גולמי" not in text:
            fail("EDIT-GATE.md must forbid JPEG גולמי")
        if path == CAL_OPS and "לא שואלים" not in text:
            fail("CALENDAR-OPS.md must lock autonomous slots")
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
