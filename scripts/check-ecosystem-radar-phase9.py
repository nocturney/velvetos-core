#!/usr/bin/env python3
"""Validate the Phase 9 ecosystem radar closes without a redundant dev lab."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "packages/vfharness/state/ecosystem-radar-phase9-2026-09-27.json"
BEST = ROOT / "packages/vfresearch/BEST-SKILLS.json"


def load(path: Path) -> dict:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    state, best = load(STATE), load(BEST)
    assert state.get("status") == "COMPLETE"
    assert state.get("decision") == "NO_ADDITIONAL_DEV_LAB_JUSTIFIED"
    research = state.get("researchSeat") or {}
    assert research.get("lastPass") == best.get("lastPass") == "2026-09-27"
    assert research.get("observedDataDate") == best.get("dataDate") == "2026-09-26"
    assert research.get("newSchedulerCreated") is False
    artifact = ROOT / research.get("artifact", "")
    assert artifact.is_file() and artifact.stat().st_size > 500
    text = artifact.read_text(encoding="utf-8-sig")
    for marker in ("agent-browser", "ui-taste", "gh-cli-readonly-agent", "INSTALL_NOTHING_NEW"):
        if marker == "INSTALL_NOTHING_NEW":
            assert state.get("conclusion", {}).get("action") == marker
        else:
            assert marker in text

    guards = state.get("costAndAuthority") or {}
    assert guards.get("incrementalRecurringCostIls") == 0
    assert guards.get("newInstalledDevLabs") == 0
    assert guards.get("newAlwaysOnSystems") == 0
    for key in ("newControlPlaneAuthority", "newMemoryAuthority", "newReleaseAuthority"):
        assert guards.get(key) == 0

    verdicts = {row.get("id"): row.get("verdict") for row in state.get("candidates", [])}
    assert verdicts.get("google-agents-cli") == "SKIP_LOCKED_RUNTIME"
    assert verdicts.get("twitter-automation") == "SKIP_POLICY_LOCK"
    assert verdicts.get("ui-taste") == "NO_LAB_EXISTING_COVERAGE"
    assert verdicts.get("gh-cli-readonly-agent") == "WATCH_EXISTING_GITHUB_PATH"
    print("OK ecosystem-radar phase9 no-new-lab cost=0 authority=none research-seat=fresh")


if __name__ == "__main__":
    main()
