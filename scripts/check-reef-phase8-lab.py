#!/usr/bin/env python3
"""Validate the Reef Phase 8 lab remains zero-cost, removable and non-authoritative."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "packages/vfharness/state/reef-phase8-lab-2026-09-27.json"
OVERLAY = ROOT / "packages/vfharness/devtools/reef-windows-import-overlay.patch"
REEF_COST = ROOT / "packages/vfharness/cost-preflight/reef-5de976b-lab.json"
UV_COST = ROOT / "packages/vfharness/cost-preflight/uv-0.12.18-phase8.json"
PIN = "5de976be90c0676c60694e55499255a81913f8fd"
OVERLAY_SHA = "e6bfafd1a84b064a783715274453f1edd66ce70cf88853ef3d559ac584dc7147"


def load(path: Path) -> dict:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    state = load(STATE)
    reef_cost = load(REEF_COST)
    uv_cost = load(UV_COST)
    assert state.get("status") == "COMPLETE_LAB_ONLY"
    assert state.get("decision") == "LAB_ONLY_NOT_PROMOTED"
    assert state.get("incrementalRecurringCostIls") == 0
    assert state.get("newAlwaysOnSystems") == 0
    assert state.get("source", {}).get("commit") == PIN
    assert state.get("source", {}).get("uv") == "0.12.18"

    authority = state.get("authority") or {}
    for key in ("productionAuthority", "controlPlaneAuthority", "schedulerAuthority", "memoryAuthority", "releaseAuthority"):
        assert authority.get(key) is False, f"authority leaked: {key}"

    overlay = state.get("windowsOverlay") or {}
    assert overlay.get("path") == "packages/vfharness/devtools/reef-windows-import-overlay.patch"
    assert overlay.get("sha256") == OVERLAY_SHA == sha256(OVERLAY)
    patch = OVERLAY.read_text(encoding="utf-8", errors="strict")
    for marker in ("except ModuleNotFoundError", "resource is None", "ThreadingUnixStreamServer", "Windows is import-only"):
        assert marker in patch, f"overlay marker missing: {marker}"

    tests = state.get("tests") or {}
    assert tests.get("harnessExample", {}).get("passed") == 88
    assert tests.get("harnessExample", {}).get("failed") == 0
    assert tests.get("harnessContractsAndRender", {}).get("passed") == 56
    assert tests.get("harnessContractsAndRender", {}).get("failed") == 0
    assert tests.get("localExecutorSubset", {}).get("passed") == 5
    assert tests.get("localExecutorSubset", {}).get("failed") == 1
    assert tests.get("broaderHarnessDiagnostic", {}).get("passed") == 116
    assert tests.get("broaderHarnessDiagnostic", {}).get("failed") == 63
    assert tests.get("failClosedProbes") == {"sandbox": "PASS", "nativeServe": "PASS"}

    capability = state.get("capability") or {}
    assert capability.get("windowsHermeticEvaluation") == "PARTIAL"
    assert capability.get("untrustedProposerExecution") == "BLOCKED_LINUX_SANDBOX_REQUIRED"
    assert capability.get("harnessEvolution") == "NOT_RUN_NO_MODEL_ENDPOINT"
    assert capability.get("productionIntegration") == "NOT_PROMOTED"

    linux = state.get("linuxDecision") or {}
    assert linux.get("wslAction") == "DEFER"
    assert linux.get("ownerActionRequiredNow") is False

    assert reef_cost.get("classification") == "FREE_LOCAL"
    assert "LAB_PREFLIGHT_ONLY" in str(reef_cost.get("selected_mode"))
    assert reef_cost.get("api_dependencies") == []
    assert uv_cost.get("classification") == "FREE_LOCAL"
    assert str(uv_cost.get("component", "")).startswith("uv@0.12.18")
    assert state.get("cost", {}).get("modelApiCalls") == 0
    print("OK reef-phase8 lab-only windows-partial cost=0 authority=none wsl=defer")


if __name__ == "__main__":
    main()
