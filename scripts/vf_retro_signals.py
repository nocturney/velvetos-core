#!/usr/bin/env python3
"""Scan office retro/memory/state for operational signals. No network. No send.

Writes packages/vfops/data/retro-signals.json for morning brief slots 01/05.
Never invents ₪, Insights, or blocked bodies. Christian lock: no owner shame.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "packages" / "vfops" / "data" / "owner-memory.md"
RETRO = ROOT / "packages" / "vfops" / "hq" / "DAILY-RETRO.md"
RESEARCH = ROOT / "packages" / "vfops" / "data" / "research.md"
STATE = ROOT / "packages" / "vfharness" / "state"
OUT = ROOT / "packages" / "vfops" / "data" / "retro-signals.json"
TZ = ZoneInfo("Asia/Jerusalem")

FAIL_PAT = re.compile(
    r"(סנסור\s*אדום|sensor\s*fail|FAIL\s+check-|נכשל|needsAuth|failover|Degraded|"
    r"חסר\s+מפתח|אין\s+MCP|צוואר\s*בקבוק|לא\s+נסגר|פניות?\s+פתוח|"
    r"ingest|bottleneck)",
    re.I,
)
SENSOR_NAME = re.compile(r"check-[\w-]+\.py|vf_\w+\.py|[A-Za-z]+ MCP|Canva|Gmail|Drive", re.I)
FAILOVER_LINE = re.compile(r"failover\s*[:：]\s*(\S+)\s*→\s*(\S+)", re.I)
DAY_BLOCK = re.compile(
    r"(?m)^### (\d{4}-\d{2}-\d{2})\b[^\n]*\n(.*?)(?=^### \d{4}-\d{2}-\d{2}\b|\Z)",
    re.S,
)


def today_local() -> date:
    return datetime.now(TZ).date()


def parse_day(s: str) -> date | None:
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def window_days(n: int = 7) -> set[str]:
    end = today_local()
    return {(end - timedelta(days=i)).isoformat() for i in range(n)}


def scan_memory(days: set[str]) -> list[dict]:
    if not MEMORY.is_file():
        return []
    text = MEMORY.read_text(encoding="utf-8")
    hits: list[dict] = []
    for day, body in DAY_BLOCK.findall(text):
        if day not in days:
            continue
        if not FAIL_PAT.search(body):
            continue
        sensors = SENSOR_NAME.findall(body)
        kind = "sensor_repeat_fail" if sensors else "ingest_bottleneck"
        if re.search(r"פניות?|לא\s+נסגר|inquiry", body, re.I):
            kind = "inquiry_lag"
        hits.append(
            {
                "kind": kind,
                "evidence": f"owner-memory/{day}",
                "briefSlot": "01" if kind in {"sensor_repeat_fail", "inquiry_lag"} else "05",
                "detail": body.strip().splitlines()[0][:160] if body.strip() else day,
                "sensors": sorted({s for s in sensors}),
            }
        )
    return hits


def scan_retro() -> list[dict]:
    if not RETRO.is_file():
        return []
    text = RETRO.read_text(encoding="utf-8")
    hits: list[dict] = []
    # Look at trailing log sections with today's or recent date in heading
    for m in re.finditer(r"(?m)^## לוג · (\d{4}-\d{2}-\d{2}).*?\n(.*?)(?=^## |\Z)", text, re.S):
        day, body = m.group(1), m.group(2)
        if day not in window_days(7):
            continue
        if "מה לא" in body or FAIL_PAT.search(body):
            hits.append(
                {
                    "kind": "sensor_repeat_fail" if SENSOR_NAME.search(body) else "ingest_bottleneck",
                    "evidence": f"DAILY-RETRO.md#{day}",
                    "briefSlot": "05",
                    "detail": next(
                        (ln.strip() for ln in body.splitlines() if ln.strip().startswith("מה לא")),
                        body.strip().splitlines()[0][:160] if body.strip() else day,
                    ),
                    "sensors": sorted({s for s in SENSOR_NAME.findall(body)}),
                }
            )
    return hits


def scan_research() -> list[dict]:
    if not RESEARCH.is_file():
        return []
    text = RESEARCH.read_text(encoding="utf-8")
    hits: list[dict] = []
    for line in text.splitlines():
        m = FAILOVER_LINE.search(line)
        if m:
            hits.append(
                {
                    "kind": "failover_streak",
                    "evidence": "research.md",
                    "briefSlot": "05",
                    "detail": line.strip()[:160],
                    "sensors": [m.group(1), m.group(2)],
                }
            )
    return hits


def scan_state() -> list[dict]:
    if not STATE.is_dir():
        return []
    hits: list[dict] = []
    for path in sorted(STATE.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        cs = data.get("component_state")
        unresolved = data.get("unresolved") or []
        if cs == "Degraded" or any(
            isinstance(u, str) and FAIL_PAT.search(u) for u in unresolved
        ):
            hits.append(
                {
                    "kind": "failover_streak" if cs == "Degraded" else "sensor_repeat_fail",
                    "evidence": f"vfharness/state/{path.name}",
                    "briefSlot": "01",
                    "detail": f"task={data.get('task_id')} component_state={cs}",
                    "sensors": [],
                }
            )
    return hits


def consolidate(raw: list[dict]) -> list[dict]:
    """Collapse repeats; promote sensor_repeat_fail when same sensor appears ≥2."""
    sensor_counter: Counter[str] = Counter()
    for row in raw:
        for s in row.get("sensors") or []:
            sensor_counter[s] += 1

    out: list[dict] = []
    seen: set[tuple] = set()
    for row in raw:
        key = (row["kind"], row["evidence"], row.get("detail", "")[:80])
        if key in seen:
            continue
        seen.add(key)
        sensors = row.get("sensors") or []
        if row["kind"] != "sensor_repeat_fail" and any(sensor_counter[s] >= 2 for s in sensors):
            row = {**row, "kind": "sensor_repeat_fail", "briefSlot": "01"}
        # Drop one-off failover unless streak (≥2 failover lines) — keep for now if ≥2 total failover hits
        out.append(
            {
                "kind": row["kind"],
                "evidence": row["evidence"],
                "briefSlot": row["briefSlot"],
                "detail": row.get("detail", ""),
                "event": "retro.anomaly",
            }
        )

    failover_n = sum(1 for r in out if r["kind"] == "failover_streak")
    if failover_n < 2:
        out = [r for r in out if r["kind"] != "failover_streak"]

    # Cap noise
    return out[:12]


def build() -> dict:
    raw = scan_memory(window_days(7)) + scan_retro() + scan_research() + scan_state()
    signals = consolidate(raw)
    return {
        "generatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
        "timezone": "Asia/Jerusalem",
        "rule": "Operational signals for office brief only. No invented ₪/Insights. No owner shame.",
        "catalogEvent": "retro.anomaly",
        "signals": signals,
        "summary": {
            "count": len(signals),
            "kinds": sorted({s["kind"] for s in signals}),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help=f"Write {OUT.relative_to(ROOT)}")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()
    report = build()
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty or args.write else None)
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text + "\n", encoding="utf-8")
        print(f"OK wrote {OUT.relative_to(ROOT)} signals={report['summary']['count']}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
