#!/usr/bin/env python3
"""Fail closed if the Windows Grok boot path can launch desktop Grok pre-login."""
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
    failures.append("canonical supervisor missing")
else:
    source = SUPERVISOR.read_text(encoding="utf-8")
    forbidden = [
        "Grok Bot.exe",
        "desktop-status.json",
        "win32ts",
        "interactive_chris",
        "start_s0",
        "--remote-debugging-port=9222",
    ]
    for marker in forbidden:
        require(marker not in source, f"boot supervisor still contains forbidden desktop marker: {marker}")
    require("FAILOVER_WATCH" in source, "boot supervisor no longer supervises failover watcher")
    require("FAILOVER_DISPATCH" in source, "boot supervisor no longer supervises trusted dispatch")

if not INSTALLER.is_file():
    failures.append("canonical Windows installer missing")
else:
    install = INSTALLER.read_text(encoding="utf-8")
    require("-AtStartup" in install, "boot task lost AtStartup trigger")
    require("-UserId 'SYSTEM'" in install, "boot task principal is not SYSTEM")
    require("-LogonType ServiceAccount" in install, "boot task is not ServiceAccount")
    require("S4U" not in install, "boot task still uses S4U")
    require("-LogonType Interactive" in install, "interactive handoff is not explicitly Interactive")
    require("grok_handoff.py" in install, "installer no longer binds interactive handoff")

if not README.is_file():
    failures.append("failover README missing")
else:
    text = README.read_text(encoding="utf-8")
    require("SYSTEM / ServiceAccount" in text, "README does not document the SYSTEM boot principal")
    require("never launches the Grok desktop" in text, "README does not state the no-desktop-launch invariant")

if failures:
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    raise SystemExit(1)

print("PASS grok boot hardening contract")
