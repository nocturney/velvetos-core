#!/usr/bin/env python3
"""Validate Phase 3 local reliability pilots and explicit blockers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfharness" / "reliability" / "components.json"

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def load(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> None:
    data = load("packages/vfharness/reliability/components.json")
    rows = {row["id"]: row for row in data.get("components", [])}
    if set(rows) != {"healthchecks", "glitchtip", "changedetection"}:
        fail("reliability component set mismatch")
    health = rows["healthchecks"]
    if health.get("state") != "PILOT" or health.get("scheduler_authority") is not False:
        fail("Healthchecks must remain sensor-only PILOT")
    hp = load(health["receipt"])
    if hp.get("healthy_ping") != "PASS" or hp.get("missed_heartbeat_detection") != "PASS":
        fail("Healthchecks pilot evidence incomplete")
    if hp.get("pilot_job_execution") != "PASS":
        fail("Healthchecks pilot did not wrap a real VelvetOS job")
    if hp.get("incremental_recurring_cost_ils") != 0:
        fail("Healthchecks cost must remain zero")

    change = rows["changedetection"]
    if change.get("state") != "PILOT":
        fail("changedetection must remain PILOT")
    cp = load(change["receipt"])
    if cp.get("baseline_snapshot") != "PASS" or cp.get("change_detection") != "PASS":
        fail("changedetection pilot evidence incomplete")
    if cp.get("browser_fetcher_used") is not False or cp.get("llm_or_ai_feature_used") is not False:
        fail("changedetection pilot used forbidden optional features")
    if cp.get("paid_api_credentials_supplied") is not False:
        fail("changedetection pilot supplied paid-capable credentials")
    if cp.get("incremental_recurring_cost_ils") != 0:
        fail("changedetection cost must remain zero")

    glitch = rows["glitchtip"]
    if glitch.get("canonical") != "https://gitlab.com/glitchtip/glitchtip-backend":
        fail("GlitchTip canonical upstream mismatch")
    if glitch.get("state") != "BLOCKED" or glitch.get("hosted_fallback_allowed") is not False:
        fail("GlitchTip blocker/hosted fallback status mismatch")
    if not glitch.get("blocker"):
        fail("GlitchTip blocker must be concrete")

    for rel in (
        "packages/vfharness/cost-preflight/healthchecks-v4.4.json",
        "packages/vfharness/cost-preflight/glitchtip-v6.2.6.json",
        "packages/vfharness/cost-preflight/changedetection-0.60.7.json",
    ):
        preflight = load(rel)
        if preflight.get("expected_recurring_cost") != "0 ILS/month incremental":
            fail(f"{rel}: expected recurring cost changed")
    print(
        "OK reliability-pilots "
        "healthchecks=PILOT/missed-heartbeat-PASS "
        "changedetection=PILOT/change-PASS "
        "glitchtip=BLOCKED-local-stack cost=0"
    )

if __name__ == "__main__":
    main()
