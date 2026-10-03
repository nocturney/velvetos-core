#!/usr/bin/env python3
"""Stage 4F tests for dependency-scoped runtime receipt proof.

No network and no repository writes. Temporary fixtures prove:
- GitHub event type never upgrades CODE_VALID into a live-runtime dependency.
- stale/missing/malformed/non-healthy receipts do not block unrelated code proof.
- deployment/runtime/external-action/acceptance claims must name dependencies.
- once a dependency is real, stale/missing/malformed/mismatched/future/no-evidence/
  non-healthy receipts fail closed.
- one healthy member of an explicitly required anyOf component is sufficient.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_runtime_receipt_policy import (  # noqa: E402
    build_runtime_proof_request,
    receipt_age_policy,
)

PROOF_SCOPE_CONTRACT = ROOT / "packages/vfharness/runtime/proof-scope.json"
STAGE4F_REPORT = ROOT / "packages/velvetos/policy/reports/stage4f-runtime-receipt-scope.json"

CONTEXT_KEYS = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "VF_RUNTIME_RECEIPTS_STRICT",
    "VF_RUNTIME_PROOF_SCOPE",
    "VF_RUNTIME_REQUIRED_COMPONENTS",
    "VF_RUNTIME_STRICT",
)


def fail(msg: str) -> None:
    print("FAIL runtime-receipt-age-policy: " + msg, file=sys.stderr)
    raise SystemExit(1)


def load_doctor():
    spec = importlib.util.spec_from_file_location(
        "vf_runtime_doctor_under_test", ROOT / "scripts/check-runtime-doctor.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def receipt(cid: str, hours_ago: float, state: str = "healthy") -> dict:
    return {
        "component_id": cid,
        "state": state,
        "observed_at": iso(hours_ago),
        "evidence": {"source": "fixture"},
    }


def write_receipts(tmp: Path, receipts: dict[str, object]) -> Path:
    rdir = tmp / "receipts"
    rdir.mkdir(parents=True, exist_ok=True)
    for old in rdir.glob("*.json"):
        old.unlink()
    for cid, body in receipts.items():
        text = body if isinstance(body, str) else json.dumps(body)
        (rdir / f"{cid}.json").write_text(text, encoding="utf-8")
    return rdir


def fixture_manifest(tmp: Path) -> Path:
    manifest = tmp / "expected-components.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "vf.runtime.expected.v2",
                "receiptFreshnessDefaultHours": 24,
                "components": [
                    {
                        "id": "alpha",
                        "kind": "service",
                        "required": True,
                        "evidence": "runtime-receipt",
                        "receipt": "alpha",
                        "maxAgeHours": 24,
                    },
                    {
                        "id": "edge",
                        "kind": "host",
                        "required": True,
                        "evidence": "runtime-receipt",
                        "anyOf": ["edge-a", "edge-b"],
                        "maxAgeHours": 24,
                    },
                    {
                        "id": "optional",
                        "kind": "connector",
                        "required": False,
                        "evidence": "runtime-receipt",
                        "receipt": "optional",
                        "maxAgeHours": 24,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


def run_doctor(doctor, tmp: Path, receipts: dict[str, object], request) -> tuple[int, str]:
    doctor.MANIFEST = fixture_manifest(tmp)
    doctor.RECEIPTS = write_receipts(tmp, receipts)
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = doctor.main(request=request)
    return code, out.getvalue() + err.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true", help="run scope/fixture semantics without requiring Stage 4F report")
    args = parser.parse_args()

    if not PROOF_SCOPE_CONTRACT.is_file():
        fail("missing packages/vfharness/runtime/proof-scope.json")
    contract = json.loads(PROOF_SCOPE_CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema") != "vf.runtime.proof-scope.v1" or contract.get("stage") != "4F":
        fail("runtime proof-scope contract schema/stage drift")
    if contract.get("defaultScope") != "code":
        fail("runtime proof-scope default must remain code")
    if contract.get("statuses") != {
        "code": "CODE_VALID",
        "deployment": "DEPLOYMENT_VALID",
        "runtime": "RUNTIME_HEALTHY",
        "external_action": "RUNTIME_HEALTHY",
        "acceptance": "RUNTIME_HEALTHY",
    }:
        fail("runtime proof-scope status mapping drift")
    deps = contract.get("dependencySelection") or {}
    if deps.get("mode") != "explicit_component_ids" or deps.get("liveScopeWithoutDependency") != "FAIL_CLOSED":
        fail("runtime proof-scope dependency semantics drift")

    # GitHub events are no longer proof scopes. Every event defaults to CODE_VALID.
    events = ("pull_request", "push", "schedule", "workflow_dispatch", "merge_group")
    for event in events:
        env = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": event}
        req = build_runtime_proof_request(env)
        if req.scope != "code" or req.runtime_health_required:
            fail(f"{event} must default to CODE_VALID, got {req}")
        strict, _ = receipt_age_policy(env, component_id="alpha")
        if strict:
            fail(f"{event} must not make alpha receipt strict without dependency")

    local = build_runtime_proof_request({})
    if local.scope != "code" or local.status != "CODE_VALID":
        fail(f"local default must be CODE_VALID: {local}")

    deployment_env = {
        "VF_RUNTIME_PROOF_SCOPE": "deployment",
        "VF_RUNTIME_REQUIRED_COMPONENTS": "alpha",
    }
    if not receipt_age_policy(deployment_env, component_id="alpha")[0]:
        fail("deployment alpha dependency must make alpha age strict")
    if receipt_age_policy(deployment_env, component_id="edge")[0]:
        fail("deployment alpha dependency must not make unrelated edge strict")

    implied = {"VF_RUNTIME_PROOF_SCOPE": "runtime"}
    if not receipt_age_policy(implied, component_id="grok-production-scheduler", implied_if_live=True)[0]:
        fail("component-specific live checker must be able to imply its own component")
    if receipt_age_policy(implied, component_id="grok-production-scheduler", implied_if_live=False)[0]:
        fail("generic live scope without dependency must not silently imply global strictness")

    legacy = build_runtime_proof_request({"VF_RUNTIME_RECEIPTS_STRICT": "1"})
    if not legacy.legacy_repository_wide or legacy.required_components != ("*",):
        fail(f"legacy strict override must remain repository-wide: {legacy}")
    legacy_with_stale_narrowing = build_runtime_proof_request({
        "VF_RUNTIME_RECEIPTS_STRICT": "1",
        "VF_RUNTIME_REQUIRED_COMPONENTS": "alpha",
    })
    if legacy_with_stale_narrowing.required_components != ("*",):
        fail("legacy strict must ignore/narrowing component env and remain repository-wide")

    try:
        build_runtime_proof_request({"VF_RUNTIME_PROOF_SCOPE": "nonsense"})
    except ValueError:
        pass
    else:
        fail("invalid runtime proof scope must fail closed")

    doctor = load_doctor()
    fresh = {
        "alpha": receipt("alpha", 1),
        "edge-a": receipt("edge-a", 1),
        "optional": receipt("optional", 1),
    }
    expired = {
        "alpha": receipt("alpha", 30.5),
        "edge-b": receipt("edge-b", 26),
    }

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)

        # CODE_VALID ignores live receipt state entirely because no dependency exists.
        code_request = build_runtime_proof_request(scope="code")
        code_cases = {
            "expired": expired,
            "missing": {},
            "malformed": {"alpha": "{not json"},
            "mismatch": {"alpha": receipt("other", 1)},
            "future": {"alpha": receipt("alpha", -5)},
            "no-evidence": {"alpha": {**receipt("alpha", 1), "evidence": {}}},
            "degraded": {"alpha": receipt("alpha", 1, "degraded")},
        }
        for case, receipts in code_cases.items():
            code, out = run_doctor(doctor, tmp, receipts, code_request)
            if code != 0 or "status=CODE_VALID" not in out or "runtime_health=NOT_REQUIRED" not in out:
                fail(f"{case} unrelated receipts must not block CODE_VALID: {out}")

        # Live scope without named dependency fails closed instead of checking everything.
        no_dep = build_runtime_proof_request(scope="deployment")
        code, out = run_doctor(doctor, tmp, fresh, no_dep)
        if code == 0 or "requires explicit runtime dependencies" not in out:
            fail(f"deployment proof without dependency must fail closed: {out}")

        # One required component is checked; unrelated bad state is ignored.
        dep_alpha = build_runtime_proof_request(scope="deployment", required_components=("alpha",))
        unrelated_bad = {
            "alpha": receipt("alpha", 1),
            "edge-a": "{broken",
            "optional": receipt("optional", 99, "degraded"),
        }
        code, out = run_doctor(doctor, tmp, unrelated_bad, dep_alpha)
        if code != 0 or "status=DEPLOYMENT_VALID" not in out or "required=alpha" not in out:
            fail(f"unrelated runtime evidence must not block alpha deployment proof: {out}")

        # Required stale/missing/malformed/etc. fail in every live claim scope.
        hard_required_cases = {
            "expired": {"alpha": receipt("alpha", 30.5)},
            "missing": {},
            "malformed": {"alpha": "{not json"},
            "component-mismatch": {"alpha": receipt("other", 1)},
            "future": {"alpha": receipt("alpha", -5)},
            "no-evidence": {"alpha": {**receipt("alpha", 1), "evidence": {}}},
            "non-healthy": {"alpha": receipt("alpha", 1, "degraded")},
        }
        for scope in ("deployment", "runtime", "external_action", "acceptance"):
            request = build_runtime_proof_request(scope=scope, required_components=("alpha",))
            for case, receipts in hard_required_cases.items():
                code, out = run_doctor(doctor, tmp, receipts, request)
                if code == 0 or "FAIL alpha:" not in out:
                    fail(f"{case} alpha must fail {scope} dependency proof: {out}")

        # anyOf dependency succeeds with one fresh member even when another is bad/missing.
        edge_req = build_runtime_proof_request(scope="runtime", required_components=("edge",))
        code, out = run_doctor(
            doctor,
            tmp,
            {"edge-b": receipt("edge-b", 1), "alpha": "{broken"},
            edge_req,
        )
        if code != 0 or "status=RUNTIME_HEALTHY" not in out or "required=edge" not in out:
            fail(f"edge fallback should satisfy explicitly required runtime component: {out}")
        if "fallback healthy via edge-b" not in out:
            fail(f"edge fallback detail missing: {out}")

        # Unknown dependencies never silently pass.
        unknown = build_runtime_proof_request(scope="deployment", required_components=("does-not-exist",))
        code, out = run_doctor(doctor, tmp, fresh, unknown)
        if code == 0 or "unknown required runtime component" not in out:
            fail(f"unknown dependency must fail closed: {out}")

        # Repository-wide legacy mode remains available and strict for migration safety.
        all_req = build_runtime_proof_request(
            scope="runtime", required_components=("*",), legacy_repository_wide=True
        )
        code, out = run_doctor(doctor, tmp, fresh, all_req)
        if code != 0 or "status=RUNTIME_HEALTHY" not in out:
            fail(f"fresh repository-wide legacy proof must pass: {out}")
        legacy_optional_missing = {
            "alpha": receipt("alpha", 1),
            "edge-a": receipt("edge-a", 1),
        }
        code, out = run_doctor(doctor, tmp, legacy_optional_missing, all_req)
        if code != 0 or "optional: optional: missing receipt" not in out or "DEGRADED" not in out:
            fail(f"legacy repository-wide proof must preserve required:false as degraded: {out}")
        code, out = run_doctor(doctor, tmp, expired, all_req)
        if code == 0 or "stale age=" not in out:
            fail(f"expired repository-wide legacy proof must fail: {out}")

    if not args.core_only:
        if not STAGE4F_REPORT.is_file():
            fail("missing Stage 4F runtime receipt scope report")
        report = json.loads(STAGE4F_REPORT.read_text(encoding="utf-8"))
        if report.get("schema") != "velvetos.stage4f-runtime-receipt-scope.v1" or report.get("stage") != "4F":
            fail("Stage 4F report schema/stage drift")
        if report.get("prepared_against_main_sha") != "8081bfe62fe6c59e0e22798dda1d2469e5ee3742":
            fail("Stage 4F report base SHA drift")
        if report.get("repository_acceptance") != "PASS":
            fail("Stage 4F report acceptance is not PASS")
        if report.get("default_scope") != "code" or report.get("github_event_is_runtime_dependency_signal") is not False:
            fail("Stage 4F default/event scope semantics drift")
        if report.get("unrelated_stale_runtime_blocks_code") is not False:
            fail("Stage 4F stale unrelated runtime regained code-blocking authority")
        expected_statuses = {
            "code": "CODE_VALID",
            "deployment": "DEPLOYMENT_VALID",
            "runtime": "RUNTIME_HEALTHY",
            "external_action": "RUNTIME_HEALTHY",
            "acceptance": "RUNTIME_HEALTHY",
        }
        if report.get("statuses") != expected_statuses:
            fail("Stage 4F report status vocabulary drift")
        fail_closed = report.get("fail_closed_when_dependency_real") or {}
        if not fail_closed or not all(value is True for value in fail_closed.values()):
            fail("Stage 4F dependency fail-closed matrix incomplete")
        proofs = report.get("proofs") or {}
        if not proofs or not all(value is True for value in proofs.values()):
            fail("Stage 4F report proof matrix incomplete")
        refresh = report.get("runtime_refresh") or {}
        if refresh.get("still_useful") is not True or refresh.get("universal_merge_gate") is not False:
            fail("Stage 4F runtime refresh scope drift")

    print(
        "OK runtime-receipt-scope "
        "default=CODE_VALID github_events=non_authoritative "
        "deployment=component_scoped runtime=component_scoped "
        "external_action=component_scoped acceptance=component_scoped "
        "required-evidence=fail_closed legacy_strict=all_components"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
