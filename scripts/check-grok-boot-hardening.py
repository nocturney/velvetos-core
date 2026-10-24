#!/usr/bin/env python3
"""Fail closed if retired OpenPost failover is restored in active source."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    "packages/vfigos/failover/windows/grok_boot_supervisor.py",
    "packages/vfigos/failover/failover_watch.py",
    "packages/vfigos/failover/grok_instagram_failover.py",
    "packages/vfigos/failover/trusted_dispatch.py",
    "packages/vfigos/failover/instagram_mcp_remote.py",
    "packages/vfigos/failover/openpost_failover_state.py",
)
errors = [f"retired OpenPost runner reappeared: {rel}" for rel in RETIRED if (ROOT / rel).exists()]
installer = ROOT / "packages/vfigos/failover/windows/install_grok_boot.ps1"
if not installer.is_file():
    errors.append("GrokBot interactive handoff installer missing")
else:
    source = installer.read_text(encoding="utf-8")
    for marker in ("grok_handoff.py", "GrokBot Interactive Handoff", "Disable-ScheduledTask -TaskName $legacyBoot"):
        if marker not in source:
            errors.append(f"GrokBot fail-closed handoff marker missing: {marker}")
    for marker in ("Register-ScheduledTask -TaskName $legacyBoot", "Start-ScheduledTask -TaskName $legacyBoot"):
        if marker in source:
            errors.append(f"Legacy supervisor re-arm marker: {marker}")
if errors:
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    raise SystemExit(1)
print("PASS retired OpenPost boot and failover runners absent")
