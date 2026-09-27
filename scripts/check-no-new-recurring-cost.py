#!/usr/bin/env python3
"""Enforce NO_NEW_RECURRING_COST authority and fail-closed preflight semantics."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAW = ROOT / "constitution" / "NO_NEW_RECURRING_COST.md"
CONTRACT = ROOT / "packages" / "vfharness" / "cost-policy.json"
TEMPLATE = ROOT / "packages" / "vfharness" / "cost-preflight" / "TEMPLATE.json"
README = ROOT / "packages" / "vfharness" / "cost-preflight" / "README.md"
CLI = ROOT / "scripts" / "vf_cost_preflight.py"
AGENTS = ROOT / "AGENTS.md"
CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
OFFICE_POLICY = ROOT / "office" / "control" / "POLICY.md"
RISK_MIRROR = ROOT / "packages" / "vfops" / "risk-policy.json"
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def run(doc: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
        json.dump(doc, fh)
        name = fh.name
    try:
        return subprocess.run([sys.executable, str(CLI), "validate", name], cwd=ROOT, text=True, capture_output=True)
    finally:
        Path(name).unlink(missing_ok=True)


def base(classification: str) -> dict:
    return {
        "schema": 1,
        "component": "sensor-fixture",
        "classification": classification,
        "license": "MIT",
        "commercial_use_allowed": True,
        "self_hosting_restriction": "none",
        "deployment_model": "local",
        "api_dependencies": [],
        "billing_risk": "none",
        "selected_mode": "free/local",
        "expected_recurring_cost": "0 ILS/month",
        "runtime_cost_notes": "local CPU only",
        "api_cost_notes": "no API calls",
        "subscription_notes": "no subscription",
        "hidden_secondary_cost_notes": "none identified",
        "quota_controls": "not applicable",
        "pricing_verified_at": "2026-09-26",
        "evidence": ["local-only fixture"],
        "approval": None,
    }


def main() -> None:
    for p in (LAW, CONTRACT, TEMPLATE, README, CLI, AGENTS, CONSTITUTION, ORCHESTRA, OFFICE_POLICY, RISK_MIRROR, LAYERS):
        if not p.is_file():
            fail(f"missing {p.relative_to(ROOT)}")

    law = LAW.read_text(encoding="utf-8")
    for needle in (
        "אפס עלות חדשה חוזרת",
        "VERIFY COST BEFORE INSTALLATION",
        "VERIFY COST BEFORE FIRST PAID-CAPABLE CALL",
        "NEVER CREATE A CHARGE WITHOUT EXPLICIT OWNER APPROVAL",
        "FAIL CLOSED ON COST",
        "BLOCKED_BY_NO_NEW_RECURRING_COST",
        "PAID_REQUIRED",
        "COST_UNKNOWN",
    ):
        if needle not in law:
            fail(f"canonical law missing {needle}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("sourceOfTruth") != "constitution/NO_NEW_RECURRING_COST.md":
        fail("cost-policy sourceOfTruth mismatch")
    if contract.get("defaultRecurringCostIls") != 0 or contract.get("failClosed") is not True:
        fail("cost-policy must default to 0 ILS and fail closed")
    if set(contract.get("blockedWithoutExplicitApproval") or []) != {"PAID_REQUIRED", "COST_UNKNOWN"}:
        fail("blocked classifications mismatch")

    for path in (AGENTS, CONSTITUTION, ORCHESTRA, OFFICE_POLICY):
        if "NO_NEW_RECURRING_COST" not in path.read_text(encoding="utf-8"):
            fail(f"{path.relative_to(ROOT)} must bind NO_NEW_RECURRING_COST")

    risk = json.loads(RISK_MIRROR.read_text(encoding="utf-8"))
    only = (risk.get("levels") or {}).get("RED", {}).get("onlyWhen") or []
    for need in ("new-recurring-cost", "paid-api-call", "billing-capable-resource"):
        if need not in only:
            fail(f"risk-policy RED.onlyWhen missing {need}")

    ok = base("FREE_LOCAL")
    if run(ok).returncode != 0:
        fail("FREE_LOCAL valid preflight must pass")

    unknown = base("COST_UNKNOWN")
    if run(unknown).returncode == 0 or "BLOCKED_BY_NO_NEW_RECURRING_COST" not in run(unknown).stderr:
        fail("COST_UNKNOWN must fail closed without explicit approval")

    paid = base("PAID_REQUIRED")
    if run(paid).returncode == 0:
        fail("PAID_REQUIRED must fail without explicit approval")

    existing = base("EXISTING_PAID_CAPABILITY")
    existing["incremental_cost_possible"] = False
    if run(existing).returncode != 0:
        fail("existing paid capability with proven no incremental cost should pass")

    free_tier = base("FREE_TIER_LIMITED")
    free_tier["automatic_paid_overage_possible"] = True
    if run(free_tier).returncode == 0:
        fail("free tier with automatic overage and no hard cap must fail closed")

    optional = base("PAID_OPTIONAL")
    optional["paid_features_enabled"] = False
    if run(optional).returncode != 0:
        fail("PAID_OPTIONAL locked to free features should pass")

    for rel in (
        "packages/vfharness/state/fabrication-cost-text-to-cad-2026-09-27.json",
        "packages/vfharness/state/fabrication-cost-step-parts-2026-09-27.json",
        "packages/vfharness/state/fabrication-cost-sendcutsend-2026-09-27.json",
    ):
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing compact preflight {rel}")
        proc = subprocess.run([sys.executable, str(CLI), str(path)], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            fail(f"compact preflight must pass: {rel}: {proc.stderr.strip()}")

    layers = json.loads(LAYERS.read_text(encoding="utf-8"))
    scripts = {r.get("script") for r in layers.get("sensors", [])}
    if "scripts/check-no-new-recurring-cost.py" not in scripts:
        fail("layers.json must register cost policy sensor")

    if "check-no-new-recurring-cost.py" not in AGENTS.read_text(encoding="utf-8"):
        fail("AGENTS sensors table must list cost policy sensor")

    print("OK NO_NEW_RECURRING_COST canonical + fail-closed cost preflight")


if __name__ == "__main__":
    main()
