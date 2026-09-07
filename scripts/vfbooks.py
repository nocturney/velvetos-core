#!/usr/bin/env python3
"""Verified books line for morning brief slot 02.

No network. No send. No invented ₪. No customer PII in the brief.
Invoice4U stays. Collection stays human WhatsApp.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "office" / "ledger" / "live" / "jobs.csv"
NEED_INVOICE = {"אושר", "ייצור", "מוכן", "נאסף"}
INVOICE_MARKS = ("invoice4u", "חשבונית", "invoice=yes", "יש חשבונית")


def _has_invoice(notes: str) -> bool:
    blob = (notes or "").lower()
    return any(m in blob for m in INVOICE_MARKS)


def load_jobs(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if any((v or "").strip() for k, v in r.items() if k != "job_id") or (r.get("job_id") or "").strip()]


def cmd_brief(_args: argparse.Namespace) -> int:
    jobs = load_jobs(LIVE)
    if not jobs:
        print(
            "חוב פתוח: אין ספירה · חשבונית חסרה: אין ספירה\n"
            "Invoice4U נשאר · בלי מייל גבייה מ-HQ · decision_gate = ₪ לראש צוות"
        )
        return 0
    missing: list[str] = []
    for row in jobs:
        stage = (row.get("stage") or "").strip()
        job_id = (row.get("job_id") or "").strip() or "—"
        notes = row.get("notes") or ""
        if stage in NEED_INVOICE and not _has_invoice(notes):
            missing.append(job_id)
    if missing:
        ids = ", ".join(missing[:8])
        extra = "…" if len(missing) > 8 else ""
        inv_line = f"חשבונית חסרה: {len(missing)} עבודות פנימי ({ids}{extra}) · בלי מייל ללקוח"
    else:
        inv_line = "חשבונית חסרה: אין בשלב אושר/ייצור/מוכן/נאסף"
    print(
        f"יומן עבודות: {len(jobs)} שורות מאומתות · בלי ₪ מכירה מכאן\n"
        f"{inv_line}\n"
        "Invoice4U נשאר · decision_gate = ₪ לראש צוות"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Velvet Factory books integrity (slot 02)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("brief", help="one Hebrew block for morning brief slot 02").set_defaults(func=cmd_brief)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
