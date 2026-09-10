#!/usr/bin/env python3
"""Render/check the generated VelvetOS System Pulse block in README.md.

The pulse is derived from committed canonical repository state. It does not call
external providers and therefore never upgrades a provider claim beyond the last
verification evidence stored in the repo.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
MANIFEST = ROOT / "packages" / "manifest.json"
WORKFLOWS = ROOT / ".github" / "workflows"
SCRIPTS = ROOT / "scripts"
HANDOFF = ROOT / "office" / "control" / "HANDOFF.json"
IG_CAPS = ROOT / "packages" / "vfigos" / "CAPABILITIES.json"
MEDIA_RUNNER = ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json"
BINDINGS = ROOT / "office" / "ledger" / "bindings.json"
CHANGELOG = ROOT / "CHANGELOG.md"

START = "<!-- OPERATIONAL-SNAPSHOT:START -->"
END = "<!-- OPERATIONAL-SNAPSHOT:END -->"


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.is_file():
        return default or {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default or {}
    return data if isinstance(data, dict) else (default or {})


def esc(value: object) -> str:
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def latest_change() -> str:
    if not CHANGELOG.is_file():
        return "No changelog evidence"
    in_unreleased = False
    for raw in CHANGELOG.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "## [Unreleased]":
            in_unreleased = True
            continue
        if in_unreleased and line.startswith("## "):
            break
        if in_unreleased and line.startswith("- "):
            item = line[2:].strip()
            return item[:210] + ("…" if len(item) > 210 else "")
    return "No unreleased change recorded"


def parse_dt(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def newest_verification(*values: object) -> str:
    parsed = [(parse_dt(v), str(v)) for v in values if parse_dt(v)]
    if not parsed:
        return "unknown"
    parsed.sort(key=lambda pair: pair[0].timestamp())
    return parsed[-1][1]


def bilingual_label(en: str, he: str) -> str:
    return f'<span dir="ltr">{esc(en)}</span><br><span dir="rtl">{esc(he)}</span>'


def render() -> str:
    registry = load_json(REGISTRY)
    manifest = load_json(MANIFEST)
    handoff = load_json(HANDOFF)
    ig_caps = load_json(IG_CAPS)
    media = load_json(MEDIA_RUNNER)
    bindings = load_json(BINDINGS)

    skills = len(registry.get("skills") or [])
    packs = len(manifest.get("packs") or [])
    sensors = len([p for p in SCRIPTS.glob("check-*.py") if p.name != "check-all.py"])
    workflows = len(list(WORKFLOWS.glob("*.yml"))) + len(list(WORKFLOWS.glob("*.yaml")))

    failed = len(handoff.get("failed") or [])
    owner_blocked = len(handoff.get("owner_blocked") or [])
    degraded = len(handoff.get("tools_degraded") or [])
    waiting = len(handoff.get("waiting") or [])
    attention = failed + owner_blocked + degraded
    health = "HEALTHY" if attention == 0 else "ATTENTION"

    ig_verify = ig_caps.get("remoteVerify") or {}
    ig_insights = ig_verify.get("insightsGraphCompat") or {}
    ig_live = bool(
        ig_caps.get("currentStatus") == "ready"
        and ig_caps.get("auth") == "ready"
        and ig_caps.get("remote_access") == "ready"
        and ig_verify.get("liveCheckOk") is True
    )
    insights_live = bool(ig_insights.get("deployed") is True)
    media_activation = media.get("activation") or {}
    media_live = bool(
        (media.get("auth") or {}).get("ready") is True
        and media_activation.get("proven") is True
        and not media.get("lastError")
        and not media.get("persistError")
    )
    jobs_bound = bool((bindings.get("canonical") or {}).get("jobs") == "google_sheet")

    live_integrations = sum([ig_live, insights_live, media_live, jobs_bound])
    gated = 0
    if (ig_verify.get("chatgptSmoke") or {}).get("publish") != "live_verified":
        gated += 1
    if any((c.get("status") == "supported_gated") for c in (ig_caps.get("capabilities") or [])):
        gated += 1

    last_verified = newest_verification(
        ig_verify.get("chatgptVerifiedAt"),
        ig_insights.get("verifiedAt"),
        media_activation.get("provenAt"),
        handoff.get("updatedAt"),
    )

    changes = handoff.get("changed_today") or []
    recent_ops = " · ".join(str(x) for x in changes[:3]) if changes else "No committed handoff delta"

    return f'''{START}
<table>
<tr>
<td align="center"><strong>{health}</strong><br><sub>{bilingual_label("System Health", "בריאות מערכת")}</sub></td>
<td align="center"><strong>{live_integrations}</strong><br><sub>{bilingual_label("Live / Bound Paths", "נתיבים חיים / מחוברים")}</sub></td>
<td align="center"><strong>{gated}</strong><br><sub>{bilingual_label("Gated Actions", "פעולות מבוקרות")}</sub></td>
<td align="center"><strong>{attention}</strong><br><sub>{bilingual_label("Needs Attention", "דורש טיפול")}</sub></td>
</tr>
<tr>
<td align="center"><strong>{skills}</strong><br><sub>{bilingual_label("Living Studio Skills", "יכולות")}</sub></td>
<td align="center"><strong>{sensors}</strong><br><sub>{bilingual_label("Sensors", "חיישנים")}</sub></td>
<td align="center"><strong>{workflows}</strong><br><sub>{bilingual_label("Workflows", "אוטומציות")}</sub></td>
<td align="center"><strong>{packs}</strong><br><sub>{bilingual_label("Packs", "חבילות")}</sub></td>
</tr>
</table>

| Pulse | Current committed evidence |
|---|---|
| **Instagram MCP** | {'LIVE / VERIFIED' if ig_live else 'NOT VERIFIED'} |
| **Instagram Insights** | {'LIVE / VERIFIED' if insights_live else 'NOT VERIFIED'} |
| **Media Intake / Drive** | {'LIVE / VERIFIED' if media_live else 'NOT VERIFIED'} |
| **Jobs source of truth** | {'Google Sheet bound' if jobs_bound else 'Not bound'} |
| **Waiting work** | {waiting} |
| **Owner blocked** | {owner_blocked} |
| **Degraded tools** | {degraded} |
| **Last verified / refreshed evidence** | `{esc(last_verified)}` |

<div dir="rtl"><strong>מה השתנה:</strong> {esc(recent_ops)}</div>
<div dir="ltr"><strong>What changed:</strong> {esc(recent_ops)}</div>

<div dir="rtl"><strong>שינוי הטמעה אחרון:</strong> {esc(latest_change())}</div>
<div dir="ltr"><strong>Latest implementation change:</strong> {esc(latest_change())}</div>

<div dir="rtl"><strong>חוזה הפולס:</strong> הבלוק מציג את הראיות האחרונות שנשמרו בריפו. הוא לא מבצע קריאת ספק חיה בזמן טעינת GitHub ולא הופך “מוגדר” ל“מאומת”.</div>
<div dir="ltr"><strong>Pulse contract:</strong> this block reports the latest evidence committed to the repository. It never performs a live provider call while rendering GitHub, and never turns “configured” into “verified”.</div>
{END}'''


def apply(text: str, block: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit("README missing operational snapshot markers")
    return pattern.sub(block, text, count=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    current = README.read_text(encoding="utf-8")
    expected = apply(current, render())
    if args.check:
        if current != expected:
            print("FAIL README System Pulse is stale. Run: python3 scripts/update-readme-snapshot.py")
            return 1
        print("OK README System Pulse is current")
        return 0

    README.write_text(expected, encoding="utf-8")
    print("OK README System Pulse updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
