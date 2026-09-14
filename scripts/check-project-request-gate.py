#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "packages/velvetos/PROJECT-REQUEST-GATE.md"
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
CLI = ROOT / "scripts/vf_project_preflight.py"


def fail(msg: str) -> None:
    print(f"FAIL project-request-gate: {msg}", file=sys.stderr)
    raise SystemExit(1)

for path in (GATE, MANIFEST, CLI):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status") != "mandatory" or manifest.get("preflightMode") != "fail_closed":
    fail("manifest is not mandatory fail-closed")
if manifest.get("gateDocument") != "packages/velvetos/PROJECT-REQUEST-GATE.md":
    fail("gateDocument mismatch")
required_domains = {
    "creative_publication", "copywriting", "operations", "production",
    "sales_conversion", "finance", "research", "system_engineering", "instagram_action", "general_business"
}
if not required_domains.issubset(set(manifest.get("domains", {}))):
    fail("required domain coverage missing")

all_paths = list(manifest.get("baselineAuthorities", []))
for cfg in manifest["domains"].values():
    all_paths.extend(cfg.get("authorities", []))
missing = sorted({p for p in all_paths if not (ROOT / p).is_file()})
if missing:
    fail("missing authority path(s): " + ", ".join(missing))

gate = GATE.read_text(encoding="utf-8")
for needle in ("No substantive work starts", "Project Instructions", "route first", "exact-final"):
    if needle.casefold() not in gate.casefold():
        fail(f"gate document missing {needle}")

for rel in ("AGENTS.md", "instances/velvet-factory/AGENTS.md", "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc"):
    body = (ROOT / rel).read_text(encoding="utf-8")
    if "PROJECT-REQUEST-GATE.md" not in body or "PROJECT-AUTHORITY-MANIFEST.json" not in body:
        fail(f"{rel} not bound to project request gate")
for sample, expected in (("תכין פוסט לפרסום", "creative_publication"), ("עדכן סטטוס הזמנה", "operations")):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(f"preflight CLI failed for sample {sample}: {proc.stderr or proc.stdout}")
    receipt = json.loads(proc.stdout)
    if receipt.get("project_preflight") != "PASS" or expected not in receipt.get("request_domain", []):
        fail(f"preflight CLI did not route {sample} to {expected}")

print(f"OK project-request-gate domains={len(manifest['domains'])} authority_paths={len(set(all_paths))} fail_closed")
