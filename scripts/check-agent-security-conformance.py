#!/usr/bin/env python3
"""Validate the OWASP-mapped VelvetOS agent-security conformance evidence."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "packages" / "vfharness" / "security" / "agent-security-conformance.json"
REQUIRED = {
    "mcp", "plugins_connectors", "agents", "control_apis", "browser_automation",
    "memory", "approval_boundaries", "external_content_ingestion", "local_eval_runner",
}
ALLOWED = {"PASS", "PARTIAL", "BLOCKED"}

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def run_sensor(name: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        cwd=ROOT, text=True, capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        fail(f"{name}: {(proc.stderr or proc.stdout).strip()[:800]}")

def main() -> None:
    if not MATRIX.is_file():
        fail("missing conformance matrix")
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    upstream = data.get("upstream") or {}
    if upstream.get("canonical") != "https://github.com/OWASP/secure-agent-playbook":
        fail("OWASP canonical source mismatch")
    if upstream.get("license") != "CC-BY-4.0":
        fail("OWASP license mismatch")
    rows = data.get("surfaces") or []
    ids = {row.get("id") for row in rows}
    if ids != REQUIRED:
        fail("surface set mismatch")
    for row in rows:
        status = row.get("status")
        if status not in ALLOWED:
            fail(f"{row.get('id')}: invalid status")
        controls = row.get("controls") or []
        if not controls:
            fail(f"{row.get('id')}: controls missing")
        for control in controls:
            evidence = control.get("evidence") or []
            if not evidence:
                fail(f"{row.get('id')}: evidence missing")
            for rel in evidence:
                if not (ROOT / rel).exists():
                    fail(f"{row.get('id')}: missing evidence {rel}")
        residual = row.get("residual")
        if not isinstance(residual, list):
            fail(f"{row.get('id')}: residual must be a list")
        if status == "PASS" and residual:
            fail(f"{row.get('id')}: PASS cannot carry unresolved residual findings")
    by_id = {row["id"]: row for row in rows}
    if by_id["browser_automation"]["status"] != "PARTIAL":
        fail("browser automation must remain PARTIAL until isolation is proven")
    if by_id["local_eval_runner"]["status"] != "PARTIAL":
        fail("local eval runner must record its unsandboxed-script residual")

    for sensor in (
        "check-agent-surface-security.py",
        "check-control-api.py",
        "check-behavioral-evals.py",
    ):
        run_sensor(sensor)
    print(f"OK agent-security-conformance surfaces={len(rows)} pass={sum(r['status']=='PASS' for r in rows)} partial={sum(r['status']=='PARTIAL' for r in rows)}")

if __name__ == "__main__":
    main()
