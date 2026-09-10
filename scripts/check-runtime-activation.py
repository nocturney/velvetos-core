#!/usr/bin/env python3
"""Fail closed on fake activation claims.

Separates implementation/wiring from provider-live proof. CI does not need every
external provider to be live; it does require repository status to remain honest
and live claims to carry durable evidence.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
HARNESS_STATE = ROOT / "packages" / "vfharness" / "state" / "close-operational-gaps-2026-09-10.json"
JOBS_RECEIPT = ROOT / "office" / "ledger" / "live" / "sync-receipt.json"
MEDIA_STATE = ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json"
GMAIL_REQUEST = ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json"
FOUNDRY = ROOT / "packages" / "vfom" / "FOUNDRY.json"


def fail(message: str) -> None:
    print(f"FAIL runtime-activation-truth: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def main() -> None:
    registry = load(REGISTRY)
    registered = list(registry.get("skills") or []) + list(registry.get("livingCapabilities") or [])
    if not registered:
        fail("Living Studio registry has no skills/capabilities")

    states = Counter(str(item.get("status") or "MISSING") for item in registered if isinstance(item, dict))
    partial = [
        str(item.get("id") or item.get("title") or "unknown")
        for item in registered
        if isinstance(item, dict) and "PARTIAL" in str(item.get("status") or "")
    ]

    harness = load(HARNESS_STATE)
    execution = harness.get("execution_state") or {}
    phase = str(execution.get("phase") or "")
    commission = str(execution.get("behavioral_commission") or execution.get("commission") or "")
    live_activation = str(execution.get("live_activation") or "")

    if phase == "commissioned" and commission == "22/22":
        fail("ambiguous 22/22 commissioned claim; use behaviorally_commissioned + live_activation")
    if phase == "behaviorally_commissioned" and not commission:
        fail("behaviorally_commissioned requires behavioral_commission evidence")

    jobs = load(JOBS_RECEIPT)
    jobs_dirty = bool(jobs.get("dirty"))
    jobs_write = str(jobs.get("lastWriteStatus") or "not_recorded")
    jobs_write_proven = (not jobs_dirty) and jobs_write in {
        "written_verified",
        "write_verified",
        "pushed_verified",
    }
    if jobs_dirty or jobs_write in {"write_pending_provider", "conflict", "write_verify_failed"}:
        jobs_activation = "read_proven_write_pending"
    elif jobs_write_proven:
        jobs_activation = "read_write_live_proven"
    else:
        jobs_activation = "read_state_present_write_not_proven"

    full_claims = {"complete", "full", "all", "live_proven", "fully_live", "22/22_live"}
    if live_activation in full_claims and (partial or not jobs_write_proven):
        fail("live_activation claims full/proven while partial capabilities or unproven Jobs write-through remain")

    media = load(MEDIA_STATE)
    media_activation = media.get("activation") or {}
    if media_activation.get("proven") is True:
        if not media_activation.get("evidence") or not media_activation.get("provenAt"):
            fail("vfmedia activation.proven=true requires evidence + provenAt")
        if (media.get("auth") or {}).get("ready") is not True:
            fail("vfmedia activation.proven=true requires auth.ready=true")
        media_state = "live_proven"
    else:
        media_state = "not_live_proven"

    gmail = load(GMAIL_REQUEST)
    gmail_state = "send_requested" if gmail.get("enabled") is True else "configured_not_requested"

    foundry = load(FOUNDRY)
    specialists = foundry.get("specialists") or {}
    if (foundry.get("creativeManifest") or {}).get("enabled") is not True:
        fail("Creative Manifest is not enabled")
    if foundry.get("noSecondRuntime") is not True:
        fail("Foundry must remain policy/orchestration over existing runtime")
    for name, rel in specialists.items():
        path = ROOT / str(rel)
        if not path.is_file():
            fail(f"Foundry specialist {name} missing {rel}")
        agent = path.parent / "agents" / "openai.yaml"
        if not agent.is_file():
            fail(f"Foundry specialist {name} missing agents/openai.yaml")

    print(
        "OK runtime-activation-truth "
        f"registered={len(registered)} "
        f"partial={len(partial)} "
        f"jobs={jobs_activation} "
        f"vfmedia={media_state} "
        f"gmail_gha={gmail_state} "
        f"creative=policy_wired "
        f"states={dict(sorted(states.items()))}"
    )


if __name__ == "__main__":
    main()
