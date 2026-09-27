#!/usr/bin/env python3
"""Validate the targeted-batch final acceptance without claiming check-all or a clean parallel worktree."""
from __future__ import annotations

import json
import subprocess
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
    assert receipt.get("decision") == "READY_FOR_OWNER_REVIEW_NO_PUSH"
    assert receipt.get("fullCheckAll", {}).get("status") == "NOT_RUN"
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
    assert diff.get("liveWorkingTree", {}).get("status") == "BLOCKED_BY_UNRELATED_PARALLEL_WORK"

    strict = receipt.get("repositoryWideStrictDeploymentProof") or {}
    assert strict.get("status") == "PARTIAL"
    assert strict.get("command") == "python scripts/check-runtime-doctor.py --strict"
    missing = set(strict.get("missingEvidence") or [])
    assert missing == {
        "mac-office: runtime-receipt",
        "automation-steward: automation-state",
        "morning-brief: automation-state",
        "github: connector-state",
    }

    guards = receipt.get("costAndAuthority") or {}
    assert guards.get("incrementalRecurringCostIls") == 0
    assert guards.get("providerModelPaidCalls") == 0
    assert guards.get("pushPerformed") is False
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
        "3D/HQ/control",
    ):
        assert marker in limitations

    acceptance = receipt.get("acceptance") or {}
    assert acceptance.get("committedScopeReady") is True
    assert acceptance.get("ownerActionRequiredNow") is False
    assert acceptance.get("pushRequiresExplicitOwnerPermission") is True
    print("OK zero-cost final acceptance targeted-batches committed-scope=PASS check-all=NOT_RUN push=NO")


if __name__ == "__main__":
    main()
