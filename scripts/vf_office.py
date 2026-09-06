#!/usr/bin/env python3
"""Velvet Factory office bridge: ledger, WhatsApp drafts, STL preflight.

No send. No invented ₪. WhatsApp stays human 050-2517000.
Printers stay on the floor. 3D AI Studio is the mesh desk when OAuth is on.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
LEDGER_DIR = ROOT / "office" / "ledger" / "live"
TEMPLATES_DIR = ROOT / "office" / "ledger" / "templates"
STUDIO_PHONE = "050-2517000"
STUDIO_E164 = "972502517000"

JOB_FIELDS = [
    "job_id",
    "opened",
    "channel",
    "client_label",
    "phone",
    "what_asked",
    "sku",
    "qty",
    "size",
    "color",
    "material",
    "file_status",
    "modeling",
    "due",
    "stage",
    "price",
    "notes",
]

STAGES = (
    "פנייה",
    "חסר פרט",
    "בדיקה",
    "ממתין לסכום",
    "הצעה",
    "אושר",
    "ייצור",
    "מוכן",
    "נאסף",
)

DRAFTS = {
    "פנייה": (
        "היי, הגעתם לסטודיו Velvet Factory.\n"
        "קיבלנו את הפנייה ({job_id}).\n"
        "כדי לבדוק ולהציע מחיר מדויק נשמח ל: קובץ STL/STEP או תיאור, מידות, חומר/צבע, וכמות.\n"
        "איסוף עצמי משדרות בלבד."
    ),
    "חסר פרט": (
        "היי, לגבי {job_id} — חסר לנו כדי להמשיך:\n"
        "{missing}\n"
        "בלי זה אין הצעת מחיר. איסוף משדרות."
    ),
    "ממתין לסכום": (
        "היי, {job_id} בבדיקה אצלנו (קובץ/סלייס).\n"
        "נחזור עם סכום אחרי שראש צוות מאשר. אין מחיר בינתיים."
    ),
    "הצעה": (
        "היי, הצעה ל־{job_id}: {sku_line}{qty_line}.\n"
        "מחיר: {price} ₪.\n"
        "לאישור תגיבו «אושר». איסוף משדרות."
    ),
    "אושר": (
        "היי, {job_id} אושר ונכנס לייצור.\n"
        "עדכון כשיהיה מוכן לאיסוף משדרות."
    ),
    "מוכן": (
        "היי, {job_id} מוכן לאיסוף משדרות.\n"
        "וואטסאפ הסטודיו: 050-2517000."
    ),
    "נאסף": "רשום אצלנו שנאסף ({job_id}). תודה.",
}

PHONE_RE = re.compile(r"[^\d+]")


class OfficeError(ValueError):
    pass


def fail(msg: str, code: int = 1) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(code)


def _need(ok: bool, msg: str) -> None:
    if not ok:
        raise OfficeError(msg)


def ensure_live() -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "jobs.csv"
    if not path.is_file():
        tmpl = TEMPLATES_DIR / "jobs.csv"
        if tmpl.is_file():
            path.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            with path.open("w", encoding="utf-8", newline="") as fh:
                csv.DictWriter(fh, fieldnames=JOB_FIELDS).writeheader()
    return path


def read_jobs(path: Path | None = None) -> list[dict[str, str]]:
    path = path or ensure_live()
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        cleaned = {k: (row.get(k) or "").strip() for k in JOB_FIELDS}
        if cleaned["job_id"]:
            out.append(cleaned)
    return out


def write_jobs(rows: list[dict[str, str]], path: Path | None = None) -> None:
    path = path or ensure_live()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=JOB_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in JOB_FIELDS})


def next_job_id(rows: list[dict[str, str]], today: date | None = None) -> str:
    day = (today or date.today()).strftime("%Y%m%d")
    prefix = f"VF-{day}-"
    n = 0
    for row in rows:
        jid = row.get("job_id") or ""
        if jid.startswith(prefix):
            try:
                n = max(n, int(jid[len(prefix) :]))
            except ValueError:
                continue
    return f"{prefix}{n + 1:03d}"


def jobs_csv_text(rows: list[dict[str, str]] | None = None) -> str:
    rows = rows if rows is not None else read_jobs()
    from io import StringIO

    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=JOB_FIELDS)
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in JOB_FIELDS})
    return buf.getvalue()


def add_job(fields: dict[str, str], path: Path | None = None) -> dict[str, str]:
    path = path or ensure_live()
    rows = read_jobs(path)
    row = {k: "" for k in JOB_FIELDS}
    row.update({k: str(v).strip() for k, v in fields.items() if k in JOB_FIELDS and v is not None})
    if not row["job_id"]:
        row["job_id"] = next_job_id(rows)
    if not row["opened"]:
        row["opened"] = datetime.now(timezone.utc).date().isoformat()
    if not row["stage"]:
        row["stage"] = "פנייה"
    _need(row["stage"] in STAGES, f"bad stage {row['stage']!r}")
    if row["price"] and row["price"].strip() in {"0", "0₪", "0 ₪"}:
        raise OfficeError("do not invent a sale ₪ — leave price empty until lead seat names it")
    rows.append(row)
    write_jobs(rows, path)
    return row


def set_stage(job_id: str, stage: str, path: Path | None = None, price: str = "") -> dict[str, str]:
    _need(stage in STAGES, f"bad stage {stage!r}")
    path = path or ensure_live()
    rows = read_jobs(path)
    found = None
    for row in rows:
        if row["job_id"] == job_id:
            row["stage"] = stage
            if price:
                row["price"] = price.strip()
            found = row
            break
    if not found:
        raise OfficeError(f"unknown job {job_id}")
    if stage == "הצעה" and not (found.get("price") or "").strip():
        raise OfficeError("stage הצעה needs a lead-seat price — otherwise use ממתין לסכום")
    write_jobs(rows, path)
    return found


def missing_fields(row: dict[str, str]) -> list[str]:
    need = []
    if not row.get("what_asked") and not row.get("sku"):
        need.append("מק״ט / תיאור")
    if not row.get("qty"):
        need.append("כמות")
    if not row.get("material"):
        need.append("חומר")
    if not row.get("due"):
        need.append("מועד איסוף (שדרות)")
    if (row.get("file_status") or "") in {"", "חסר"}:
        need.append("קובץ STL/STEP")
    return need


def to_e164(phone: str) -> str | None:
    raw = PHONE_RE.sub("", phone or "")
    if not raw:
        return None
    if raw.startswith("+"):
        raw = raw[1:]
    if raw.startswith("972"):
        return raw
    if raw.startswith("0"):
        return "972" + raw[1:]
    if len(raw) == 9:
        return "972" + raw
    return raw if raw.isdigit() else None


def wa_me(phone: str, text: str) -> str:
    e164 = to_e164(phone)
    if not e164:
        raise OfficeError("need a customer phone for wa.me (digits)")
    return f"https://wa.me/{e164}?text={quote(text)}"


def draft_whatsapp(row: dict[str, str], stage: str | None = None) -> dict[str, Any]:
    stage = stage or row.get("stage") or "פנייה"
    if stage == "הצעה" and not (row.get("price") or "").strip():
        raise OfficeError("no quote draft without a lead-seat ₪ — use ממתין לסכום")
    if stage not in DRAFTS:
        raise OfficeError(f"no WhatsApp template for stage {stage!r}")
    missing = missing_fields(row)
    sku_line = row.get("sku") or row.get("what_asked") or "העבודה"
    qty_line = f" × {row['qty']}" if row.get("qty") else ""
    text = DRAFTS[stage].format(
        job_id=row.get("job_id") or "VF-?",
        missing="\n".join(f"- {m}" for m in missing) or "- (ראש צוות אמר להמשיך)",
        sku_line=sku_line,
        qty_line=qty_line,
        price=(row.get("price") or "").strip(),
    )
    if "₪" in text and stage != "הצעה":
        raise OfficeError("draft leaked a ₪ outside a lead-seat quote")
    payload: dict[str, Any] = {
        "job_id": row.get("job_id"),
        "stage": stage,
        "send": False,
        "studio_phone": STUDIO_PHONE,
        "rule": "human taps send on 050-2517000 — HQ never sends WhatsApp",
        "text": text,
        "missing": missing,
    }
    customer = (row.get("phone") or "").strip()
    if customer:
        payload["wa_me"] = wa_me(customer, text)
        payload["to"] = customer
    else:
        payload["wa_me"] = None
        payload["paste"] = "open the existing chat on 050-2517000 and paste"
    return payload


def _bbox_from_points(pts: list[tuple[float, float, float]]) -> dict[str, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
        "size_x": max(xs) - min(xs),
        "size_y": max(ys) - min(ys),
        "size_z": max(zs) - min(zs),
    }


def preflight_stl(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise OfficeError(f"missing file {path}")
    data = path.read_bytes()
    suffix = path.suffix.lower()
    report: dict[str, Any] = {
        "file": path.name,
        "bytes": len(data),
        "units": "mm assumed unless the customer said otherwise",
        "price": None,
        "print_hours": None,
        "hq_prints": False,
        "checklist": {
            "file_present": True,
            "license": "run vlicense separately",
            "slicer": "human on the floor",
            "material_on_roll": "human on the floor",
        },
    }
    if suffix in {".step", ".stp"}:
        report["kind"] = "step"
        report["ok"] = True
        report["note"] = "STEP present — open in CAD / 3D AI Studio. HQ does not slice."
        return report
    if suffix == ".3mf":
        report["kind"] = "3mf"
        report["ok"] = True
        report["note"] = "3MF present — slicer on the floor. HQ does not print."
        return report
    if suffix != ".stl" and not data[:5].lower().startswith(b"solid") and len(data) < 84:
        raise OfficeError(f"unsupported print file {path.suffix}")

    if data[:5].lower().startswith(b"solid") and b"facet" in data[:2000].lower():
        report["kind"] = "stl-ascii"
        pts: list[tuple[float, float, float]] = []
        tris = 0
        for line in data.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                parts = line.split()
                pts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("endfacet"):
                tris += 1
        report["triangles"] = tris
        if len(pts) < 3:
            raise OfficeError("ascii STL has no vertices")
        report["bbox_mm"] = _bbox_from_points(pts)
    else:
        if len(data) < 84:
            raise OfficeError("binary STL too short")
        n = struct.unpack_from("<I", data, 80)[0]
        expect = 84 + n * 50
        if len(data) < expect:
            raise OfficeError(f"binary STL truncated: need {expect} bytes, got {len(data)}")
        pts = []
        off = 84
        for _ in range(n):
            # skip normal (3f), read 3 vertices
            off += 12
            for _v in range(3):
                x, y, z = struct.unpack_from("<fff", data, off)
                pts.append((x, y, z))
                off += 12
            off += 2
        report["kind"] = "stl-binary"
        report["triangles"] = n
        if not pts:
            raise OfficeError("binary STL has zero triangles")
        report["bbox_mm"] = _bbox_from_points(pts)

    bbox = report["bbox_mm"]
    report["ok"] = all(bbox[k] >= 0 for k in ("size_x", "size_y", "size_z")) and report["triangles"] > 0
    report["note"] = (
        "preflight only — no ₪, no hours. "
        "Next: vlicense + slicer + lead seat. 3DAI if the mesh still needs repair."
    )
    return report


def _run(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except OfficeError as exc:
        fail(str(exc))
        return None


def cmd_jobs_add(args: argparse.Namespace) -> int:
    row = _run(
        add_job,
        {
            "channel": args.channel,
            "client_label": args.client or "",
            "phone": args.phone or "",
            "what_asked": args.what or "",
            "sku": args.sku or "",
            "qty": args.qty or "",
            "size": args.size or "",
            "color": args.color or "",
            "material": args.material or "",
            "file_status": args.file_status or "חסר",
            "modeling": args.modeling or "לא",
            "due": args.due or "",
            "notes": args.notes or "",
        },
    )
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def cmd_jobs_list(_args: argparse.Namespace) -> int:
    rows = read_jobs()
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_jobs_stage(args: argparse.Namespace) -> int:
    row = _run(set_stage, args.job_id, args.stage, price=args.price or "")
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def cmd_jobs_csv(_args: argparse.Namespace) -> int:
    sys.stdout.write(jobs_csv_text())
    return 0


def cmd_convert_draft(args: argparse.Namespace) -> int:
    rows = {r["job_id"]: r for r in read_jobs()}
    row = rows.get(args.job_id)
    if not row:
        fail(f"unknown job {args.job_id}")
    payload = _run(draft_whatsapp, row, stage=args.stage)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_print_preflight(args: argparse.Namespace) -> int:
    report = _run(preflight_stl, Path(args.file))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vf-office", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    jobs = sub.add_parser("jobs")
    jsub = jobs.add_subparsers(dest="jobs_cmd", required=True)
    add_p = jsub.add_parser("add")
    add_p.add_argument("--channel", default="WhatsApp")
    add_p.add_argument("--client", default="")
    add_p.add_argument("--phone", default="")
    add_p.add_argument("--what", default="")
    add_p.add_argument("--sku", default="")
    add_p.add_argument("--qty", default="")
    add_p.add_argument("--size", default="")
    add_p.add_argument("--color", default="")
    add_p.add_argument("--material", default="")
    add_p.add_argument("--file-status", default="חסר")
    add_p.add_argument("--modeling", default="לא")
    add_p.add_argument("--due", default="")
    add_p.add_argument("--notes", default="")
    add_p.set_defaults(func=cmd_jobs_add)
    jsub.add_parser("list").set_defaults(func=cmd_jobs_list)
    jsub.add_parser("csv").set_defaults(func=cmd_jobs_csv)
    st = jsub.add_parser("stage")
    st.add_argument("job_id")
    st.add_argument("stage")
    st.add_argument("--price", default="")
    st.set_defaults(func=cmd_jobs_stage)

    conv = sub.add_parser("convert")
    csub = conv.add_subparsers(dest="convert_cmd", required=True)
    d = csub.add_parser("draft")
    d.add_argument("job_id")
    d.add_argument("--stage", default=None)
    d.set_defaults(func=cmd_convert_draft)

    pr = sub.add_parser("print")
    psub = pr.add_subparsers(dest="print_cmd", required=True)
    pf = psub.add_parser("preflight")
    pf.add_argument("file")
    pf.set_defaults(func=cmd_print_preflight)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
