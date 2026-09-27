#!/usr/bin/env python3
"""Validate zero-cost final acceptance, including the completed monolithic check-all proof."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "packages/vfharness/state/zero-cost-final-acceptance-2026-09-27.json"
PROGRAM = ROOT / "packages/vfharness/state/zero-cost-agent-stack-2026-09-27.json"


def load(path: Path) -> dict:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def main() -> None:
    receipt, program = load(RECEIPT), load(PROGRAM)
    assert receipt.get("status") == "PASS_DECLARED_SCOPE_WITH_KNOWN_LIMITATIONS"
    assert receipt.get("decision") == "PUSHED_FOR_DRAFT_PR_REVIEW_NO_MERGE"
    full = receipt.get("fullCheckAll") or {}
    assert full.get("status") == "PASS"
    assert full.get("command") == "python scripts/check-all.py"
    assert full.get("observedExitCode") == 0
    assert full.get("sensorCount") == 106
    assert full.get("terminalLine") == "OK suite passed=106"
    assert "CREATE_NEW_PROCESS_GROUP" in str(full.get("windowsProcessIsolation", ""))
    head = receipt.get("acceptedCodeHead")
    assert isinstance(head, str) and len(head) == 40
    assert git("merge-base", "--is-ancestor", head, "HEAD").returncode == 0
    assert git("diff", "--check", f"bb54b0a7^..{head}").returncode == 0

    batches = {row.get("id"): row for row in receipt.get("targetedBatches", [])}
    assert set(batches) == {
        "policy-security",
        "observability-reliability-engineering",
        "cad-laya",
        "memory-labs-research",
    }
    for row in batches.values():
        assert str(row.get("status", "")).startswith("PASS")
    diff = receipt.get("diffChecks") or {}
    assert diff.get("committedProgramRange", {}).get("status") == "PASS"
    assert diff.get("liveWorkingTree", {}).get("status") == "PASS_CLEAN"

    runtime_manifest = load(ROOT / "packages/vfharness/runtime/expected-components.json")
    assert runtime_manifest.get("schema") == "vf.runtime.expected.v2"

    strict = receipt.get("repositoryWideStrictDeploymentProof") or {}
    assert strict.get("status") == "PASS"
    assert strict.get("contractSchema") == "vf.runtime.expected.v2"
    assert strict.get("command") == "python scripts/check-runtime-doctor.py --strict"
    assert strict.get("observedExitCode") == 0
    assert strict.get("blockingEvidence") == []
    assert strict.get("providerReadbackArtifact") == "automation/grok/provider-readback-2026-09-27.json"

    doctor_env = dict(os.environ)
    doctor_env["PYTHONUTF8"] = "1"

    grok = subprocess.run(
        [sys.executable, "scripts/check-grok-provider-readback.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=doctor_env,
    )
    grok_output = grok.stdout + "\n" + grok.stderr
    assert grok.returncode == 0
    assert "GROK PROVIDER READBACK PASS" in grok_output

    doctor = subprocess.run(
        [sys.executable, "scripts/check-runtime-doctor.py", "--strict"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=doctor_env,
    )
    doctor_output = doctor.stdout + "\n" + doctor.stderr
    assert doctor.returncode == 0
    assert "FAIL grok-production-scheduler" not in doctor_output
    assert "fallback healthy via sderot-windows" in doctor_output
    assert "FAIL github" not in doctor_output
    assert "FAIL google-drive" not in doctor_output
    assert "edge-execution: no healthy member" not in doctor_output

    guards = receipt.get("costAndAuthority") or {}
    assert guards.get("incrementalRecurringCostIls") == 0
    assert guards.get("providerModelPaidCalls") == 0
    assert guards.get("pushPerformed") is True
    assert guards.get("productionPublicationPerformed") is False
    for key in (
        "newControlPlaneAuthority",
        "newSchedulerAuthority",
        "newMemoryAuthority",
        "newReleaseAuthority",
        "newAlwaysOnProductionRuntime",
    ):
        assert guards.get(key) == 0
    assert program.get("status") == "complete"
    assert program.get("component_state") == "Verified"
    assert program.get("pulse") == "idle"
    assert "owner review" in str(program.get("next_step", "")).lower()

    limitations = "\n".join(receipt.get("knownLimitations", []))
    for marker in (
        "PARTIAL",
        "GlitchTip",
        "Laya",
        "Cognee",
        "Reef",
        "07:00 cutoff",
    ):
        assert marker in limitations

    acceptance = receipt.get("acceptance") or {}
    assert acceptance.get("committedScopeReady") is True
    assert acceptance.get("ownerActionRequiredNow") is False
    assert acceptance.get("pushRequiresExplicitOwnerPermission") is True
    assert acceptance.get("pushWasExplicitlyAuthorized") is True
    assert acceptance.get("pullRequestState") == "DRAFT"
    assert acceptance.get("mergePerformed") is False
    print("OK zero-cost final acceptance targeted-batches committed-scope=PASS check-all=PASS sensors=106 push=YES pr=DRAFT merge=NO")


if __name__ == "__main__":
    main()
