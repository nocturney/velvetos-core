#!/usr/bin/env python3
"""Assemble an office report draft from existing artifacts.

Never invents ₪ or Insights. Missing fields stay «אין ספירה».
Demo/fixture mode writes under packages/vfops/out/fixtures/ and labels clearly.
Does not send mail or WhatsApp.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")
LEARNINGS = ROOT / "packages" / "vfinsights" / "LEARNINGS.md"
LAST30 = ROOT / "packages" / "vfresearch" / "hq" / "LAST30.md"
RESEARCH = ROOT / "packages" / "vfops" / "data" / "research.md"
WEEKLY_LOAD = ROOT / "packages" / "vfops" / "hq" / "WEEKLY-LOAD.md"
TEMPLATE = ROOT / "packages" / "vfops" / "hq" / "CLIENT-REPORT-TEMPLATE.md"
OUT = ROOT / "packages" / "vfops" / "out"
FIXTURES = OUT / "fixtures"


def read_or_missing(path: Path, limit: int = 1200) -> str:
    if not path.is_file():
        return "אין ספירה"
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return "אין ספירה"
    return text[:limit]


def assemble(*, fixture: bool = False, client_id: str = "internal-office") -> dict:
    today = datetime.now(TZ).date().isoformat()
    learnings = read_or_missing(LEARNINGS)
    last30 = read_or_missing(LAST30, 800)
    research = read_or_missing(RESEARCH, 800)
    load = read_or_missing(WEEKLY_LOAD, 400)
    report = {
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "client_id": client_id,
        "fixture": fixture,
        "template": str(TEMPLATE.relative_to(ROOT)),
        "sections": {
            "01_summary": "טיוטה פנימית ממקורות קיימים — בעלים מאשר לפני שליחה.",
            "02_outputs": research if research != "אין ספירה" else "אין ספירה",
            "03_numbers": learnings,
            "03_community": last30,
            "04_load": load,
            "05_next": "חסר עד החלטת בעלים / ראש צוות",
        },
        "missing": [
            k
            for k, v in {
                "LEARNINGS": learnings,
                "LAST30": last30,
                "research": research,
            }.items()
            if v == "אין ספירה"
        ],
    }
    return report


def render_md(report: dict) -> str:
    flag = "\n\n> **FIXTURE / DEMO — לא תוצר חי**\n" if report.get("fixture") else "\n"
    s = report["sections"]
    lines = [
        f"# דוח משרד · {report['client_id']} · {report['generated_at'][:10]}",
        flag.strip(),
        "",
        "## 01 · סיכום",
        s["01_summary"],
        "",
        "## 02 · מה יצא (מ־research.md)",
        s["02_outputs"],
        "",
        "## 03 · מספרים (LEARNINGS — בלי המצאה)",
        s["03_numbers"],
        "",
        "## 03ב · קהילה (LAST30)",
        s["03_community"],
        "",
        "## 04 · עומס (WEEKLY-LOAD)",
        s["04_load"],
        "",
        "## 05 · הצעד הבא",
        s["05_next"],
        "",
        "## חסר",
        ("- " + "\n- ".join(report["missing"])) if report["missing"] else "- (אין רשימת חסר)",
        "",
        "מקור תבנית: `packages/vfops/hq/CLIENT-REPORT-TEMPLATE.md`. אין שליחה אוטומטית.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", action="store_true", help="write under fixtures/ and label DEMO")
    ap.add_argument("--client-id", default="internal-office")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    report = assemble(fixture=bool(args.fixture), client_id=args.client_id)
    md = render_md(report)
    print(md[:2000])
    if args.write:
        dest_dir = FIXTURES if args.fixture else OUT
        dest_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(TZ).strftime("%Y-%m-%d")
        prefix = "FIXTURE-" if args.fixture else ""
        md_path = dest_dir / f"{prefix}report-{args.client_id}-{stamp}.md"
        json_path = dest_dir / f"{prefix}report-{args.client_id}-{stamp}.json"
        md_path.write_text(md, encoding="utf-8")
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {md_path.relative_to(ROOT)}")
        print(f"wrote {json_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
