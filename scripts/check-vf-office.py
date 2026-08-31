#!/usr/bin/env python3
"""Sensors for the office bridge: ledger, WhatsApp drafts, STL preflight. No network. No send."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_office import (  # noqa: E402
    STUDIO_PHONE,
    OfficeError,
    add_job,
    draft_whatsapp,
    jobs_csv_text,
    next_job_id,
    preflight_stl,
    read_jobs,
    set_stage,
    to_e164,
    wa_me,
    write_jobs,
)

SHEETS = ROOT / "packages" / "vfbooks" / "SHEETS.md"
CONVERT = ROOT / "packages" / "vfconvert" / "WHATSAPP.md"
PREFLIGHT = ROOT / "packages" / "vfprod" / "PREFLIGHT.md"
FIT = ROOT / "docs" / "MCP-FIT.md"
BINDINGS = ROOT / "office" / "ledger" / "bindings.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def tiny_stl(tmp: Path) -> Path:
    """1-triangle binary STL: 10×20×30 mm right triangle."""
    path = tmp / "cube.stl"
    header = b"VF-TEST" + b"\x00" * (80 - 7)
    n = 1
    buf = bytearray(header)
    buf += struct.pack("<I", n)
    # normal
    buf += struct.pack("<fff", 0.0, 0.0, 1.0)
    buf += struct.pack("<fff", 0.0, 0.0, 0.0)
    buf += struct.pack("<fff", 10.0, 0.0, 0.0)
    buf += struct.pack("<fff", 0.0, 20.0, 30.0)
    buf += struct.pack("<H", 0)
    path.write_bytes(bytes(buf))
    return path


def main() -> None:
    for path in (SHEETS, CONVERT, PREFLIGHT, FIT, BINDINGS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw) / "jobs.csv"
        write_jobs([], tmp)
        if next_job_id([], today=__import__("datetime").date(2026, 8, 31)) != "VF-20260831-001":
            fail("job id sequence broken")

        row = add_job(
            {
                "channel": "WhatsApp",
                "client_label": "לקוח-בדיקה",
                "phone": "0501234567",
                "what_asked": "מעמד לטלפון",
                "qty": "1",
                "material": "PLA",
                "file_status": "חסר",
            },
            path=tmp,
        )
        if not row["job_id"].startswith("VF-"):
            fail("job_id missing")
        if row["price"]:
            fail("new job must not invent a ₪")
        if row["stage"] != "פנייה":
            fail("new job stage must be פנייה")

        d = draft_whatsapp(row, "פנייה")
        if d["send"] is not False:
            fail("WhatsApp draft must set send=false")
        if d["studio_phone"] != STUDIO_PHONE:
            fail("studio phone must stay 050-2517000")
        if "₪" in d["text"]:
            fail("intake draft must not include ₪")
        if "wa.me/972501234567" not in (d.get("wa_me") or ""):
            fail("wa.me must use customer e164")
        if "מעמד" not in d["text"] and row["job_id"] not in d["text"]:
            fail("draft should name the job")

        try:
            draft_whatsapp(row, "הצעה")
            fail("quote draft without price must fail")
        except OfficeError:
            pass

        wait = draft_whatsapp(row, "ממתין לסכום")
        if "₪" in wait["text"]:
            fail("waiting-for-price draft must not include ₪")

        priced = dict(row)
        priced["price"] = "120"
        q = draft_whatsapp(priced, "הצעה")
        if "120 ₪" not in q["text"]:
            fail("quote draft must use the lead-seat amount")

        try:
            set_stage(row["job_id"], "הצעה", path=tmp)
            fail("stage הצעה without price must fail")
        except OfficeError:
            pass

        set_stage(row["job_id"], "ממתין לסכום", path=tmp)
        rows = read_jobs(tmp)
        if rows[0]["stage"] != "ממתין לסכום":
            fail("stage did not persist")

        csv_text = jobs_csv_text(rows)
        if "job_id" not in csv_text.splitlines()[0]:
            fail("csv export missing header")

        if to_e164("050-2517000") != "972502517000":
            fail("studio number e164")
        link = wa_me("0502517000", "שלום")
        if not link.startswith("https://wa.me/972502517000?text="):
            fail("wa.me encoding")

        stl = tiny_stl(Path(raw))
        report = preflight_stl(stl)
        if report["triangles"] != 1:
            fail("stl triangle count")
        bbox = report["bbox_mm"]
        if abs(bbox["size_x"] - 10) > 0.01 or abs(bbox["size_y"] - 20) > 0.01:
            fail("stl bbox")
        if report["price"] is not None or report["print_hours"] is not None:
            fail("preflight must not invent ₪ or hours")
        if report["hq_prints"] is not False:
            fail("HQ must not print")

    bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
    jobs_id = ((bindings.get("workbooks") or {}).get("jobs") or {}).get("spreadsheetId")
    if not jobs_id:
        fail("bindings.json must name the jobs spreadsheetId")
    if "₪" in json.dumps(bindings, ensure_ascii=False) and "no invented" not in json.dumps(bindings).lower():
        fail("bindings.json must not invent a ₪")

    sheets = SHEETS.read_text(encoding="utf-8")
    for needle in ("vf_office.py", "exportMimeType", "חסר גיליון", "לא ממציאים", jobs_id, "CONNECT-SHEETS.md"):
        if needle not in sheets:
            fail(f"SHEETS.md must mention {needle}")
    if "X ₪" not in sheets:
        fail("SHEETS.md must keep X ₪ rule")

    wa = CONVERT.read_text(encoding="utf-8")
    for needle in ("050-2517000", "wa.me", "send=false", "vf_office.py", "CONNECT-WHATSAPP.md"):
        if needle not in wa:
            fail(f"WHATSAPP.md must mention {needle}")

    pf = PREFLIGHT.read_text(encoding="utf-8")
    for needle in ("STL", "vf_office.py", "אין ₪", "3DAISTUDIO.md"):
        if needle not in pf:
            fail(f"PREFLIGHT.md must mention {needle}")

    fit = FIT.read_text(encoding="utf-8")
    if "vf_office.py" not in fit:
        fail("MCP-FIT.md must point at the office bridge")

    print("OK vf-office ledger+whatsapp-draft+stl-preflight")


if __name__ == "__main__":
    main()
