#!/usr/bin/env python3
"""Fail closed if legacy OpenPost failover can be re-armed at Windows boot."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "packages" / "vfigos" / "failover" / "windows"
SUPERVISOR = WINDOWS / "grok_boot_supervisor.py"
INSTALLER = WINDOWS / "install_grok_boot.ps1"
README = ROOT / "packages" / "vfigos" / "failover" / "README.md"

failures: list[str] = []

def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)

if not SUPERVISOR.is_file():
    failures.append("canonical legacy supervisor missing")
else:
    source = SUPERVISOR.read_text(encoding="utf-8")
    require("no-op after Cloudflare Publisher cutover" in source, "legacy supervisor is not fail-closed")
    for marker in ("FAILOVER_WATCH", "FAILOVER_DISPATCH", "subprocess.Popen", "trusted-dispatch.py", "failover-watch.py"):
        require(marker not in source, f"legacy supervisor can still arm failover: {marker}")

if not INSTALLER.is_file():
    failures.append("canonical Windows installer missing")
else:
    install = INSTALLER.read_text(encoding="utf-8")
    require("Disable-ScheduledTask -TaskName $legacyBoot" in install, "installer does not disable legacy boot task")
    require("Register-ScheduledTask -TaskName $legacyBoot" not in install, "installer still recreates legacy boot supervisor")
    require("Start-ScheduledTask -TaskName $legacyBoot" not in install, "installer still starts legacy boot supervisor")
    require("-LogonType Interactive" in install, "interactive handoff is not explicitly Interactive")
    require("grok_handoff.py" in install, "installer no longer binds interactive handoff")

if not README.is_file():
    failures.append("failover README missing")
else:
    text = README.read_text(encoding="utf-8")
    require("Not armed for Cloudflare Publisher jobs" in text, "README does not mark failover as legacy")
    require("2026-09-24" in text, "README does not record cutover")

if failures:
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    raise SystemExit(1)

print("PASS legacy OpenPost boot failover is disabled by contract")
