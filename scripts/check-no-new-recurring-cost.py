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
AGENTS = ROOT / "AGENTS.md"  # global NO_NEW_RECURRING_COST pointer only
CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
OFFICE_POLICY = ROOT / "office" / "control" / "POLICY.md"
RISK_MIRROR = ROOT / "packages" / "vfops" / "risk-policy.json"
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"
ENVELOPE_SCHEMA = ROOT / "packages" / "velvetos" / "policy" / "schema" / "cost-envelope.schema.json"
ENVELOPE_VECTORS = ROOT / "packages" / "velvetos" / "policy" / "cost-envelope-test-vectors.json"
ENVELOPE_HELPER = ROOT / "scripts" / "vf_cost_envelope.py"
ENVELOPE_README = ROOT / "packages" / "vfharness" / "cost-envelopes" / "README.md"
ENVELOPE_TEMPLATE = ROOT / "packages" / "vfharness" / "cost-envelopes" / "TEMPLATE.json"
ENVELOPE_FIXTURE_PREFLIGHT = ROOT / "packages" / "vfharness" / "cost-envelopes" / "fixtures" / "preflight.json"
ENVELOPE_FIXTURE = ROOT / "packages" / "vfharness" / "cost-envelopes" / "fixtures" / "envelope.json"
ENVELOPE_USE_FIXTURE = ROOT / "packages" / "vfharness" / "cost-envelopes" / "fixtures" / "use.json"
ACTION_RECEIPT_VECTORS = ROOT / "packages" / "velvetos" / "policy" / "action-receipt-test-vectors.json"
STAGE4G_REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4g-cost-envelopes.json"
STAGE4G_GENERATOR = ROOT / "scripts" / "generate-stage4g-cost-envelope-report.py"


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
    for p in (LAW, CONTRACT, TEMPLATE, README, CLI, AGENTS, CONSTITUTION, ORCHESTRA, OFFICE_POLICY, RISK_MIRROR, LAYERS,
              ENVELOPE_SCHEMA, ENVELOPE_VECTORS, ENVELOPE_HELPER, ENVELOPE_README, ENVELOPE_TEMPLATE,
              ENVELOPE_FIXTURE_PREFLIGHT, ENVELOPE_FIXTURE, ENVELOPE_USE_FIXTURE, ACTION_RECEIPT_VECTORS,
              STAGE4G_REPORT, STAGE4G_GENERATOR):
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
        "Bounded Cost Envelopes",
        "Stage 4G installs the framework only",
        "spent_before + projected_incremental_cost <= cap",
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
    if contract.get("version") != 2:
        fail("cost-policy version must be 2 for Stage 4G")
    envelopes = contract.get("boundedEnvelopes") or {}
    expected_classes = {"EXISTING_PAID_CAPABILITY", "FREE_TIER_LIMITED", "PAID_REQUIRED"}
    if envelopes.get("schema") != "velvetos.cost-envelope.v1" or envelopes.get("defaultState") != "NO_ACTIVE_ENVELOPE":
        fail("bounded cost envelope schema/default state drift")
    if envelopes.get("decisionEntrypoint") != "scripts/vf_cost_preflight.py" or envelopes.get("helper") != "scripts/vf_cost_envelope.py":
        fail("bounded cost envelope must keep vf_cost_preflight.py as the single decision entrypoint")
    if set(envelopes.get("allowedClassifications") or []) != expected_classes or envelopes.get("cannotEnvelope") != ["COST_UNKNOWN"]:
        fail("bounded cost envelope classifications drift")
    if envelopes.get("capCurrency") != "ILS" or envelopes.get("overageBehavior") != "BLOCK_AT_CAP":
        fail("bounded cost envelope cap/overage contract drift")
    if envelopes.get("requiresHardCap") is not True or envelopes.get("requiresFreshUsageMeter") is not True:
        fail("bounded cost envelope must require hard cap + fresh usage meter")
    per_call = envelopes.get("perMatchingCall") or {}
    if per_call != {"ownerApprovalRequired": False, "fullPreflightRequired": False, "exactActionReceiptRequired": True}:
        fail(f"bounded cost envelope per-call contract drift: {per_call}")
    for required in ("provider_change", "plan_change", "billing_model_change", "usage_model_change", "scope_change", "cap_change", "automatic_overage_change", "overage_behavior_change", "expiry"):
        if required not in (envelopes.get("invalidatesOn") or []):
            fail(f"bounded cost envelope invalidation missing {required}")

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

    free_conflict = base("FREE_LOCAL")
    free_conflict["incremental_cost_possible"] = True
    if run(free_conflict).returncode == 0:
        fail("FREE_LOCAL conflicting with incremental_cost_possible=true must require approval")

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

    misleading_cap = base("FREE_TIER_LIMITED")
    misleading_cap["automatic_paid_overage_possible"] = True
    misleading_cap["hard_cap_enforced"] = False
    misleading_cap["hard_cap"] = "monitoring only, not enforced"
    if run(misleading_cap).returncode == 0:
        fail("descriptive hard_cap text must not bypass hard_cap_enforced=false")

    optional = base("PAID_OPTIONAL")
    optional["paid_features_enabled"] = False
    if run(optional).returncode != 0:
        fail("PAID_OPTIONAL locked to free features should pass")

    fixture_preflight = subprocess.run(
        [sys.executable, str(CLI), "validate", str(ENVELOPE_FIXTURE_PREFLIGHT)],
        cwd=ROOT, text=True, capture_output=True,
    )
    if fixture_preflight.returncode != 0:
        fail(f"Stage 4G source preflight fixture must validate: {fixture_preflight.stderr.strip()}")

    envelope_selftest = subprocess.run(
        [sys.executable, str(ENVELOPE_HELPER), "--self-test"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if envelope_selftest.returncode != 0:
        fail("cost envelope vectors failed: " + (envelope_selftest.stderr.strip() or envelope_selftest.stdout.strip()))
    if "OK cost-envelope vectors=22 allow=2 revalidate=10 deny=10 matching_call_owner_prompts=0 full_preflight_per_call=NO" not in envelope_selftest.stdout:
        fail("cost envelope vector summary drift")

    envelope_entrypoint = subprocess.run(
        [
            sys.executable, str(CLI), "--allow-fixture-envelope", "--at", "2030-01-01T10:30:00Z", "envelope-use",
            str(ENVELOPE_FIXTURE), str(ENVELOPE_USE_FIXTURE),
        ],
        cwd=ROOT, text=True, capture_output=True,
    )
    if envelope_entrypoint.returncode != 0:
        fail("canonical cost entrypoint must ALLOW matching bounded-envelope fixture: " + envelope_entrypoint.stderr.strip())
    envelope_result = json.loads(envelope_entrypoint.stdout)
    expected_projection = {
        "decision": "ALLOW",
        "authorization_basis": "BOUNDED_COST_ENVELOPE",
        "owner_prompt_required": False,
        "full_preflight_required": False,
        "exact_action_receipt_required": True,
        "source_preflight_status": "PASS",
        "source_preflight_revalidated_locally": True,
    }
    for key, value in expected_projection.items():
        if envelope_result.get(key) != value:
            fail(f"canonical cost envelope entrypoint drift: {key} expected {value!r}, got {envelope_result.get(key)!r}")

    fixture_without_test_flag = subprocess.run(
        [
            sys.executable, str(CLI), "--at", "2030-01-01T10:30:00Z", "envelope-use",
            str(ENVELOPE_FIXTURE), str(ENVELOPE_USE_FIXTURE),
        ],
        cwd=ROOT, text=True, capture_output=True,
    )
    if fixture_without_test_flag.returncode == 0 or "test-only" not in fixture_without_test_flag.stderr:
        fail("fixture envelope must be rejected by the production entrypoint without explicit test flag")

    active_dir = ROOT / (envelopes.get("activeEnvelopeDirectory") or "")
    if active_dir.is_dir() and any(active_dir.glob("*.json")):
        fail("Stage 4G framework PR must not create an active spend envelope")

    action_vectors = json.loads(ACTION_RECEIPT_VECTORS.read_text(encoding="utf-8"))
    action_ids = {row.get("id") for row in action_vectors.get("vectors") or []}
    for vector_id in ("cost-envelope-exact-action-valid", "cost-envelope-missing-exact-action-binding-blocked"):
        if vector_id not in action_ids:
            fail(f"action receipt contract missing Stage 4G vector {vector_id}")

    envelope_schema = json.loads(ENVELOPE_SCHEMA.read_text(encoding="utf-8"))
    if envelope_schema.get("$id") != "velvetos.cost-envelope.v1":
        fail("cost envelope JSON schema id drift")

    stage4g = json.loads(STAGE4G_REPORT.read_text(encoding="utf-8"))
    if stage4g.get("schema") != "velvetos.stage4g-cost-envelopes.v1" or stage4g.get("stage") != "4G":
        fail("Stage 4G report schema/stage drift")
    if stage4g.get("prepared_against_main_sha") != "f0df1c7ea28aad1cbaa9d4752bb84bc6035735d5":
        fail("Stage 4G report base SHA drift")
    if stage4g.get("repository_acceptance") != "PASS":
        fail("Stage 4G repository acceptance is not PASS")
    if stage4g.get("active_envelope_count") != 0 or stage4g.get("spend_authorized_by_stage4g_implementation") is not False:
        fail("Stage 4G framework must ship with zero active spend envelopes")
    matching = stage4g.get("matching_call") or {}
    if matching.get("owner_prompt_count") != 0 or matching.get("full_preflight_per_call") is not False or matching.get("exact_action_receipt_required") is not True:
        fail("Stage 4G matching-call ceremony/safety contract drift")
    summary = stage4g.get("vector_summary") or {}
    if summary.get("count") != 22 or summary.get("decision_counts") != {"ALLOW": 2, "REQUIRE_OWNER_APPROVAL": 10, "DENY": 10}:
        fail("Stage 4G vector distribution drift")

    with tempfile.TemporaryDirectory() as td:
        regenerated = Path(td) / "stage4g.json"
        proc = subprocess.run(
            [
                sys.executable, str(STAGE4G_GENERATOR),
                "--prepared-against", stage4g["prepared_against_main_sha"],
                "--captured-at", stage4g["captured_at"],
                "--output", str(regenerated),
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            fail("Stage 4G report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
        if regenerated.read_bytes() != STAGE4G_REPORT.read_bytes():
            fail("Stage 4G report is not reproducible")

    detailed_preflights = 0
    for path in sorted(TEMPLATE.parent.glob("*.json")):
        if path == TEMPLATE:
            continue
        proc = subprocess.run(
            [sys.executable, str(CLI), "validate", str(path)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            fail(f"detailed cost preflight must validate: {path.relative_to(ROOT)}: {proc.stderr.strip()}")
        detailed_preflights += 1
    if detailed_preflights == 0:
        fail("no active detailed cost preflights found")

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

    print("OK NO_NEW_RECURRING_COST canonical + fail-closed cost preflight")


if __name__ == "__main__":
    main()
