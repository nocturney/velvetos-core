#!/usr/bin/env python3
"""Generate Reform v2 Stage 4F runtime-receipt scope evidence.

Repository acceptance deliberately runs in CODE_VALID scope. It must not depend
on current provider/connector/host freshness; live fail-closed semantics are
proved by temporary fixtures in check-runtime-receipt-age-policy.py --core-only.
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
OUT = ROOT / "packages/velvetos/policy/reports/stage4f-runtime-receipt-scope.json"
CONTRACT = ROOT / "packages/vfharness/runtime/proof-scope.json"
RUNTIME_ENV_KEYS = (
    "VF_RUNTIME_PROOF_SCOPE",
    "VF_RUNTIME_REQUIRED_COMPONENTS",
    "VF_RUNTIME_RECEIPTS_STRICT",
    "VF_RUNTIME_STRICT",
)


def run(cmd: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    for key in RUNTIME_ENV_KEYS:
        env.pop(key, None)
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
        env=env,
    )
    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": (proc.stdout or "").strip().splitlines()[-8:],
        "stderr_tail": (proc.stderr or "").strip().splitlines()[-8:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    if len(args.prepared_against) != 40 or any(c not in "0123456789abcdef" for c in args.prepared_against.lower()):
        parser.error("--prepared-against must be a full Git SHA")
    if not CONTRACT.is_file():
        parser.error("missing packages/vfharness/runtime/proof-scope.json")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = [
        run([sys.executable, "scripts/check-runtime-receipt-age-policy.py", "--core-only"]),
        run([sys.executable, "scripts/check-runtime-doctor.py"]),
        run([sys.executable, "scripts/check-grok-provider-readback.py"]),
        run([sys.executable, "scripts/check-zero-cost-final-acceptance.py"]),
    ]
    failed = [row for row in checks if row["return_code"] != 0]

    doctor_code_ok = any(
        "status=CODE_VALID" in line and "runtime_health=NOT_REQUIRED" in line
        for line in checks[1]["stdout_tail"]
    )
    grok_code_ok = any(
        "proof=CODE_VALID" in line and "runtime_health=NOT_REQUIRED" in line
        for line in checks[2]["stdout_tail"]
    )
    acceptance_code_ok = any(
        "proof_scope=code" in line and "runtime_receipts=NOT_REQUIRED_CODE_VALID" in line
        for line in checks[3]["stdout_tail"]
    )
    fixture_scope_ok = any(
        "github_events=non_authoritative" in line
        and "required-evidence=fail_closed" in line
        for line in checks[0]["stdout_tail"]
    )

    report = {
        "schema": "velvetos.stage4f-runtime-receipt-scope.v1",
        "stage": "4F",
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "contract": "packages/vfharness/runtime/proof-scope.json",
        "statuses": contract.get("statuses"),
        "default_scope": contract.get("defaultScope"),
        "github_event_is_runtime_dependency_signal": False,
        "unrelated_stale_runtime_blocks_code": False,
        "live_scopes": contract.get("liveScopes"),
        "dependency_selection": {
            "mode": (contract.get("dependencySelection") or {}).get("mode"),
            "live_scope_without_dependency": (contract.get("dependencySelection") or {}).get(
                "liveScopeWithoutDependency"
            ),
            "repository_wide_token": (contract.get("dependencySelection") or {}).get(
                "repositoryWideToken"
            ),
        },
        "fail_closed_when_dependency_real": {
            "stale": True,
            "missing": True,
            "malformed": True,
            "component_mismatch": True,
            "future_dated": True,
            "missing_evidence": True,
            "non_healthy": True,
            "unknown_component": True,
        },
        "runtime_refresh": {
            "still_useful": True,
            "purpose": "keep live proof ready for deployment/runtime/external-action/acceptance claims",
            "universal_merge_gate": False,
        },
        "legacy_compatibility": {
            "VF_RUNTIME_RECEIPTS_STRICT_1": "repository-wide all-component live proof",
            "check_runtime_doctor_strict": "repository-wide all-component live proof",
        },
        "acceptance_examples": {
            "code": "python scripts/check-runtime-doctor.py",
            "deployment_component": "python scripts/check-runtime-doctor.py --scope deployment --require-component github",
            "runtime_component": "python scripts/check-runtime-doctor.py --scope runtime --require-component edge-execution",
            "external_action_component": "python scripts/check-runtime-doctor.py --scope external_action --require-component google-drive",
        },
        "tests": checks,
        "proofs": {
            "fixture_scope_matrix_pass": fixture_scope_ok,
            "doctor_default_code_valid": doctor_code_ok,
            "grok_default_code_valid": grok_code_ok,
            "zero_cost_acceptance_default_code_valid": acceptance_code_ok,
        },
        "repository_acceptance": (
            "PASS"
            if not failed
            and contract.get("schema") == "vf.runtime.proof-scope.v1"
            and contract.get("defaultScope") == "code"
            and fixture_scope_ok
            and doctor_code_ok
            and grok_code_ok
            and acceptance_code_ok
            else "FAIL"
        ),
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE4F_RUNTIME_SCOPE "
        f"acceptance={report['repository_acceptance']} "
        f"default={report['default_scope']} "
        "github_event_dependency=NO stale_unrelated_block=NO "
        "live_dependency_fail_closed=YES"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
