#!/usr/bin/env python3
"""Generate Reform v2 Stage 4G bounded-cost-envelope repository evidence.

No provider, billing or paid API call is performed. Stage 4G is framework-only
until an explicit owner-approved envelope is created outside this implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4g-cost-envelopes.json"
POLICY = ROOT / "packages" / "vfharness" / "cost-policy.json"
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "cost-envelope-test-vectors.json"
ENV_FIXTURE = ROOT / "packages" / "vfharness" / "cost-envelopes" / "fixtures" / "envelope.json"
USE_FIXTURE = ROOT / "packages" / "vfharness" / "cost-envelopes" / "fixtures" / "use.json"
ACTIVE_DIR = ROOT / "packages" / "vfharness" / "cost-envelopes" / "active"


def run(cmd: list[str], *, env: dict[str, str]) -> dict[str, Any]:
    display_cmd = []
    for index, value in enumerate(cmd):
        text_value = str(value).replace("\\", "/")
        if index == 0:
            text_value = "python"
        display_cmd.append(text_value)
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=90,
        env=env,
    )
    return {
        "command": " ".join(display_cmd),
        "return_code": proc.returncode,
        "stdout_tail": (proc.stdout or "").strip().splitlines()[-10:],
        "stderr_tail": (proc.stderr or "").strip().splitlines()[-10:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    if len(args.prepared_against) != 40 or any(c not in "0123456789abcdef" for c in args.prepared_against.lower()):
        ap.error("--prepared-against must be a full Git SHA")

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
    pyenv = dict(os.environ)
    pyenv["PYTHONPATH"] = str(ROOT / "scripts") + os.pathsep + str(ROOT / "packages")

    checks = [
        run([sys.executable, "scripts/vf_cost_envelope.py", "--self-test"], env=pyenv),
        run([sys.executable, "scripts/vf_action_receipt.py", "--self-test"], env=pyenv),
        run(
            [
                sys.executable,
                "scripts/vf_cost_preflight.py",
                "--allow-fixture-envelope",
                "--at",
                "2030-01-01T10:30:00Z",
                "envelope-use",
                str(ENV_FIXTURE.relative_to(ROOT)),
                str(USE_FIXTURE.relative_to(ROOT)),
            ],
            env=pyenv,
        ),
    ]
    failed = [row for row in checks if row["return_code"] != 0]
    fixture_rejection = run(
        [
            sys.executable,
            "scripts/vf_cost_preflight.py",
            "--at",
            "2030-01-01T10:30:00Z",
            "envelope-use",
            str(ENV_FIXTURE.relative_to(ROOT)),
            str(USE_FIXTURE.relative_to(ROOT)),
        ],
        env=pyenv,
    )
    fixture_rejected_in_production_mode = (
        fixture_rejection["return_code"] != 0
        and any("test-only" in line for line in fixture_rejection["stderr_tail"])
    )

    expected = [row["expected"] for row in vectors["vectors"]]
    counts = {
        decision: sum(1 for row in expected if row["decision"] == decision)
        for decision in ("ALLOW", "REQUIRE_OWNER_APPROVAL", "DENY")
    }
    matching = [
        row for row in vectors["vectors"]
        if row["id"] in {"matching-call-no-repeat-approval", "matching-call-exactly-at-cap"}
    ]
    matching_no_ceremony = all(
        row["expected"]["decision"] == "ALLOW"
        and row["expected"]["owner_prompt_required"] is False
        and row["expected"]["full_preflight_required"] is False
        and row["expected"]["exact_action_receipt_required"] is True
        for row in matching
    )

    active_envelopes = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ACTIVE_DIR.glob("*.json") if ACTIVE_DIR.is_dir() else [])
    )
    bounded = policy.get("boundedEnvelopes") or {}

    report = {
        "schema": "velvetos.stage4g-cost-envelopes.v1",
        "stage": "4G",
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "policy_id": "cost.recurring.new",
        "framework_only": True,
        "active_envelope_count": len(active_envelopes),
        "active_envelopes": active_envelopes,
        "spend_authorized_by_stage4g_implementation": False,
        "external_paid_calls_performed": 0,
        "default_policy": {
            "no_new_recurring_cost": policy.get("defaultRecurringCostIls") == 0,
            "fail_closed": policy.get("failClosed") is True,
            "default_envelope_state": bounded.get("defaultState"),
            "cost_unknown_can_be_enveloped": False,
        },
        "envelope_contract": {
            "schema": bounded.get("schema"),
            "single_decision_entrypoint": bounded.get("decisionEntrypoint"),
            "helper": bounded.get("helper"),
            "allowed_classifications": bounded.get("allowedClassifications"),
            "cap_currency": bounded.get("capCurrency"),
            "overage_behavior": bounded.get("overageBehavior"),
            "requires_hard_cap": bounded.get("requiresHardCap"),
            "requires_fresh_usage_meter": bounded.get("requiresFreshUsageMeter"),
            "invalidates_on": bounded.get("invalidatesOn"),
        },
        "matching_call": {
            "owner_prompt_count": 0,
            "full_preflight_per_call": False,
            "exact_action_receipt_required": True,
            "source_preflight_hash_bound": True,
            "aggregate_cap_guard": "spent_before + projected_incremental_cost <= cap",
            "matching_vectors_all_allow": matching_no_ceremony,
        },
        "vector_summary": {
            "count": len(vectors["vectors"]),
            "decision_counts": counts,
            "allow": counts["ALLOW"],
            "revalidation": counts["REQUIRE_OWNER_APPROVAL"],
            "deny": counts["DENY"],
        },
        "action_receipt_contract": {
            "policy_effect_receipt_mode": "EXACT_ACTION_REQUIRED",
            "matching_call_owner_gate_repeated": False,
            "valid_vector": "cost-envelope-exact-action-valid",
            "missing_binding_vector": "cost-envelope-missing-exact-action-binding-blocked",
        },
        "tests": checks,
        "negative_controls": {
            "fixture_rejected_by_production_entrypoint": fixture_rejected_in_production_mode,
            "fixture_rejection": fixture_rejection,
        },
        "repository_acceptance": (
            "PASS"
            if not failed
            and not active_envelopes
            and fixture_rejected_in_production_mode
            and matching_no_ceremony
            and counts == {"ALLOW": 2, "REQUIRE_OWNER_APPROVAL": 10, "DENY": 10}
            and bounded.get("defaultState") == "NO_ACTIVE_ENVELOPE"
            and bounded.get("decisionEntrypoint") == "scripts/vf_cost_preflight.py"
            and bounded.get("requiresHardCap") is True
            and bounded.get("requiresFreshUsageMeter") is True
            else "FAIL"
        ),
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE4G_COST_ENVELOPES "
        f"acceptance={report['repository_acceptance']} "
        f"active={report['active_envelope_count']} "
        f"vectors={report['vector_summary']['count']} "
        f"decisions={counts} spend_authorized=false"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
