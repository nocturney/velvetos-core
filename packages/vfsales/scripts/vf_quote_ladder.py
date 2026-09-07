#!/usr/bin/env python3
"""
vf_quote_ladder.py — Sales quote drafts through the vfharness escalation ladder.

Never invents ₪. Known fields from --known become the draft; everything else
is marked חסר:. Uses packages/vfharness/scripts/vf_graceful_escalation.run_ladder.

Usage:
    python3 packages/vfsales/scripts/vf_quote_ladder.py \\
        --task-id sensor-check --known "material=PETG"
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE_DIR = ROOT / "packages" / "vfharness" / "state"
QUOTE_MD = ROOT / "packages" / "vfsales" / "QUOTE.md"


def _load_ladder():
    path = ROOT / "packages" / "vfharness" / "scripts" / "vf_graceful_escalation.py"
    spec = importlib.util.spec_from_file_location("vf_graceful_escalation", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


REQUIRED = ("material", "qty", "finish", "when", "weight_g", "slice_ok", "lead_ils")


def parse_known(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not raw:
        return out
    for part in raw.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def build_partial(known: dict[str, str]) -> str:
    lines = [
        "# טיוטת הצעה חלקית (סולם הסלמה)",
        "",
        f"task: sensor / quote ladder · {datetime.now(timezone.utc).date().isoformat()}",
        f"מקור חוקה: `{QUOTE_MD.relative_to(ROOT)}`",
        "",
        "## ידוע מהקלט",
    ]
    if known:
        for k, v in known.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- (אין)")
    lines.append("")
    lines.append("## חסר:")
    missing = [f for f in REQUIRED if f not in known]
    # lead_ils always missing unless explicitly provided — never invent ₪
    if "lead_ils" not in known:
        if "lead_ils" not in missing:
            missing.append("lead_ils")
    for f in missing:
        if f == "lead_ils":
            lines.append("- lead_ils → `X ₪` עד סכום מראש צוות (לא מנחשים)")
        else:
            lines.append(f"- {f}")
    lines.extend(
        [
            "",
            "## טיוטה בטוחה (לא לשלוח)",
            "",
            "פתיחה: בקשת הדפסה" + (f" בחומר {known['material']}" if "material" in known else "") + ".",
            "חיבורים: איסוף שדרות · וואטסאפ 050-2517000.",
            "מחיר: X ₪ — ממתין לראש צוות.",
            "צעד הבא: להשלים שדות חסר: ואז טיוטה מלאה.",
            "",
            "אין שליחה. אין ₪ מומצא. אין ווידג׳ט תשלום.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--known", default="", help='comma pairs e.g. material=PETG,qty=2')
    args = ap.parse_args()
    known = parse_known(args.known)
    ladder = _load_ladder()

    # Full quote needs lead_ils — without it, attempt/fallback fail; downgrade = safe partial
    def attempt():
        if "lead_ils" in known and all(f in known for f in ("material", "qty")):
            return True, build_partial(known)
        return False, None

    def fallback():
        # Still refuse inventing price even if material+qty present
        if "lead_ils" in known:
            return True, build_partial(known)
        return False, None

    def downgrade():
        draft = build_partial(known)
        out = STATE_DIR / f"quote-partial-{args.task_id}.md"
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        out.write_text(draft, encoding="utf-8")
        return True, str(out)

    result = ladder.run_ladder(
        args.task_id,
        pack="vfsales",
        attempt_fn=attempt,
        fallback_fn=fallback,
        downgrade_fn=downgrade,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("result"):
        path = Path(result["result"])
        if path.exists():
            print("\n--- draft ---\n")
            print(path.read_text(encoding="utf-8"))
            if "חסר:" not in path.read_text(encoding="utf-8"):
                print("ERROR: draft missing חסר: marker", file=sys.stderr)
                return 1
            if any(tok in path.read_text(encoding="utf-8") for tok in ("₪150", "₪200", "מחיר: 50")):
                print("ERROR: invented price pattern", file=sys.stderr)
                return 1
    return 0 if result.get("rung") in (ladder.Rung.DOWNGRADE, ladder.Rung.FALLBACK, ladder.Rung.RETRY) else 1


if __name__ == "__main__":
    raise SystemExit(main())
