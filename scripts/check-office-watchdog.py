#!/usr/bin/env python3
"""Office watchdog sensor — wrapper + vf_control_plane outcomes. No network."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "vf_office_watchdog.py"
PLANE_CLI = ROOT / "scripts" / "vf_control_plane.py"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (
        WRAPPER,
        PLANE_CLI,
        ROOT / "packages" / "vfigos" / "CAPABILITIES.json",
        ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json",
        ROOT / "packages" / "vfgrowth" / "FEED-AUDIT.md",
        ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json",
        ROOT / "constitution" / "RISK.md",
        ROOT / "office" / "control" / "POLICY.md",
        ROOT / "packages" / "vfops" / "ROUTINE.md",
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    wrapper_src = WRAPPER.read_text(encoding="utf-8")
    if "vf_control_plane" not in wrapper_src or "cmd_watchdog" not in wrapper_src:
        fail("vf_office_watchdog.py must be a thin wrapper around vf_control_plane.cmd_watchdog")

    caps = json.loads((ROOT / "packages" / "vfigos" / "CAPABILITIES.json").read_text(encoding="utf-8"))
    desk = json.loads((ROOT / ".cursor" / "vf-desk.json").read_text(encoding="utf-8"))
    desk_ig_status = ((desk.get("tools") or {}).get("instagram") or {}).get("status")
    ready_like = {"ready", "ready-codespace", "ready-local"}
    if caps.get("currentStatus") in ready_like:
        if desk_ig_status not in ready_like:
            fail("instagram capabilities must not claim ready* without desk ready*")
        if caps.get("currentStatus") == "ready" and desk_ig_status != "ready":
            fail("instagram capabilities ready must match desk ready")
    if caps.get("currentStatus") == "needsAuth" and desk_ig_status in ready_like:
        fail("CAPABILITIES currentStatus still needsAuth while desk is ready*")
    if "adelaidasofia" not in json.dumps(caps).lower() and "adelaidasofia" not in (
        ((desk.get("tools") or {}).get("instagram") or {}).get("mcp") or ""
    ).lower():
        fail("capabilities/desk must reference adelaidasofia Instagram MCP")
    if "jlbadano" in (caps.get("providerPreference") or "").lower():
        fail("CAPABILITIES providerPreference must not be jlbadano")
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
            if needle == "Media Intake" and "קליטת מדיה" not in routine:
                fail(f"ROUTINE.md missing {needle}")
            elif needle == "Publish Watch" and "Publish" not in routine and "פרסום" not in routine:
                fail("ROUTINE.md missing publish watch")
            elif needle == "watchdog" and "watchdog" not in routine.lower():
                fail("ROUTINE.md must mention watchdog")
            elif needle in ("07:00", "Insights"):
                if needle not in routine:
                    fail(f"ROUTINE.md missing {needle}")

    tw_path = ROOT / "packages" / "vfigos" / "data" / "token-watch.json"
    if not tw_path.is_file():
        fail("missing packages/vfigos/data/token-watch.json")
    plane_src = (ROOT / "scripts" / "vf_control_plane.py").read_text(encoding="utf-8")
    if "ig_token_watch_issues" not in plane_src:
        fail("vf_control_plane.py must define ig_token_watch_issues")
    if "run_token_watch_behavior_tests" not in plane_src:
        fail("vf_control_plane.py must define run_token_watch_behavior_tests")
    # In-memory behavior tests (unknown / none / limited same-day / bad input)
    import importlib.util

    spec = importlib.util.spec_from_file_location("vf_control_plane", ROOT / "scripts" / "vf_control_plane.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    beh_errors = mod.run_token_watch_behavior_tests()
    if beh_errors:
        fail("token-watch behavior: " + "; ".join(beh_errors))
    tw = json.loads(tw_path.read_text(encoding="utf-8"))
    if (tw.get("expiryMode") or "") == "none":
        issues = mod.ig_token_watch_issues()
        if any(i.get("code") == "ig_token_expiry_unverified" for i in issues):
            fail("expiryMode=none with owner evidence must not raise ig_token_expiry_unverified")
        if any("חסר מועד פקיעה" in str(i.get("detail")) for i in issues):
            fail("none mode must not alert חסר מועד פקיעה")

    # Wrapper --json
    proc = subprocess.run(
        [sys.executable, str(WRAPPER), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode not in (0, 1, 2):
        fail(f"watchdog wrapper failed: {proc.stderr or proc.stdout}")
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        fail(f"watchdog --json must return JSON, got: {proc.stdout[:400]}")
    if "summary" not in report:
        fail("watchdog --json must return summary")
    if report["summary"] not in {
        "OK",
        "AUTOFIXED",
        "PREPARED",
        "WAITING_EXTERNAL_TOOL",
        "DEAD_LETTER",
        "RED_BLOCKER",
    }:
        fail(f"unknown summary outcome {report['summary']}")
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
    if report.get("spamChristian") is True:
        fail("watchdog must not spam Christian (Don't Bother Christian)")

    # Control-plane watchdog text form
    proc2 = subprocess.run(
        [sys.executable, str(PLANE_CLI), "watchdog"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc2.returncode not in (0, 1):
        fail(f"vf_control_plane watchdog failed: {proc2.stderr or proc2.stdout}")
    if "WATCHDOG " not in (proc2.stdout or ""):
        fail("vf_control_plane watchdog must print WATCHDOG <WORST>")

    print("OK office-watchdog")


if __name__ == "__main__":
    main()
