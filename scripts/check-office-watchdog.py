#!/usr/bin/env python3
"""Office watchdog sensor — files + non-fake IG ready + G004 + CTA."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "vf_office_watchdog.py"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (
        CLI,
        ROOT / "packages" / "vfigos" / "CAPABILITIES.json",
        ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json",
        ROOT / "packages" / "vfgrowth" / "FEED-AUDIT.md",
        ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json",
        ROOT / "constitution" / "RISK.md",
        ROOT / "packages" / "vfops" / "ROUTINE.md",
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    caps = json.loads((ROOT / "packages" / "vfigos" / "CAPABILITIES.json").read_text(encoding="utf-8"))
    if caps.get("currentStatus") == "ready":
        desk = json.loads((ROOT / ".cursor" / "vf-desk.json").read_text(encoding="utf-8"))
        if ((desk.get("tools") or {}).get("instagram") or {}).get("status") != "ready":
            fail("instagram capabilities must not claim ready without desk ready")
    ids = {c["id"] for c in caps.get("capabilities") or []}
    for need in (
        "instagram.profile.read",
        "instagram.profile.update",
        "instagram.media.list",
        "instagram.publish.post",
        "instagram.publish.carousel",
        "instagram.publish.reel",
        "instagram.publish.story",
        "instagram.insights.read",
        "instagram.live.verify",
    ):
        if need not in ids:
            fail(f"capability missing {need}")
    if "Metricool" not in (caps.get("notRequired") or []):
        fail("Metricool must be listed as notRequired")

    audit = json.loads(
        (ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json").read_text(encoding="utf-8")
    )
    if (audit.get("g004Identity") or {}).get("canonicalHe") != "מחזיק טבעות לזמן אימון":
        fail("G004 identity must remain מחזיק טבעות לזמן אימון")
    items = audit.get("items") or []
    if len(items) < 3:
        fail("feed-audit must list baseline + review items")
    if items[0].get("classification") != "QUALITY_REFERENCE":
        fail("post #1 must be QUALITY_REFERENCE")
    if items[2].get("classification") != "REVIEW_REQUIRED":
        fail("post #3+ must be REVIEW_REQUIRED")

    routine = (ROOT / "packages" / "vfops" / "ROUTINE.md").read_text(encoding="utf-8")
    for needle in ("07:00", "Media Intake", "Publish Watch", "Insights", "watchdog"):
        if needle not in routine and needle.lower() not in routine.lower():
            # Hebrew alternatives
            if needle == "Media Intake" and "קליטת מדיה" not in routine:
                fail(f"ROUTINE.md missing {needle}")
            elif needle == "Publish Watch" and "Publish" not in routine and "פרסום" not in routine:
                fail(f"ROUTINE.md missing publish watch")
            elif needle == "watchdog" and "watchdog" not in routine.lower() and "Watchdog" not in routine:
                fail("ROUTINE.md must mention watchdog")
            elif needle in ("07:00", "Insights"):
                if needle not in routine:
                    fail(f"ROUTINE.md missing {needle}")

    proc = subprocess.run(
        [sys.executable, str(CLI), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode not in (0, 2):
        fail(f"watchdog failed: {proc.stderr or proc.stdout}")
    report = json.loads(proc.stdout.split("WROTE")[0] if False else proc.stdout)
    # When --json only, stdout is pure json
    if "summary" not in report:
        # maybe mixed — find json
        fail("watchdog --json must return summary")
    for outcome in report.get("findings") or []:
        if outcome.get("outcome") not in {
            "OK",
            "AUTOFIXED",
            "PREPARED",
            "WAITING_EXTERNAL_TOOL",
            "DEAD_LETTER",
            "RED_BLOCKER",
        }:
            fail(f"unknown outcome {outcome.get('outcome')}")

    print("OK office-watchdog")


if __name__ == "__main__":
    main()
