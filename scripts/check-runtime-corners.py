#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
BEST = ROOT / "packages" / "vfresearch" / "BEST-SKILLS.json"
JOBS_WF = ROOT / ".github" / "workflows" / "jobs-write-through.yml"
OFFICE_WF = ROOT / ".github" / "workflows" / "office-control-plane.yml"
ACTIVATION = ROOT / "scripts" / "vf_living_studio_activation.py"


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def need_text(path: Path, *tokens: str) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(ROOT)} missing token {token!r}")
    return text


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    partial = []
    for group in ("skills", "livingCapabilities"):
        for item in reg.get(group) or []:
            if item.get("status") == "EXISTING_PARTIAL":
                partial.append(item.get("id"))
    if sorted(partial) != ["order-state-manager"]:
        fail("phase-one partial set must be exactly order-state-manager; got: " + ", ".join(sorted(partial)))

    order = next((x for x in reg.get("skills") or [] if x.get("id") == "order-state-manager"), None)
    if not order or order.get("status") != "EXISTING_PARTIAL":
        fail("order-state-manager must remain PARTIAL until production WIF write/readback proof")
    for key in ("activation", "verification"):
        if not order.get(key):
            fail(f"order-state-manager missing {key}")

    required = {
        "print-engineering": {"EXISTING_COMPLETE", "EXISTING_EQUIVALENT"},
        "failure-museum": {"EXISTING_COMPLETE"},
        "velvet-lab": {"EXISTING_COMPLETE"},
        "commercial-qa": {"EXISTING_COMPLETE", "EXISTING_EQUIVALENT"},
        "opportunity-intelligence": {"EXISTING_COMPLETE"},
        "invisible-work-detector": {"EXISTING_COMPLETE"},
    }
    caps = {x.get("id"): x for x in reg.get("livingCapabilities") or []}
    for cid, allowed in required.items():
        item = caps.get(cid)
        if not item or item.get("status") not in allowed:
            fail(f"{cid} status not closed: {(item or {}).get('status')}")
        for key in ("activation", "verification", "evidencePath"):
            if not item.get(key):
                fail(f"{cid} missing {key}")

    need_text(
        JOBS_WF,
        "google-github-actions/auth@v2",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "velvetos-media-intake@instamcp.iam.gserviceaccount.com",
        "verifiedFrom",
        "VELVET_MACHINE_WRITER_ALLOW",
    )
    need_text(
        OFFICE_WF,
        "vf_living_studio_activation.py sweep --write",
        "check-runtime-corners.py",
        "VELVET_MACHINE_WRITER_ALLOW",
    )
    need_text(ACTIVATION, "failure_museum()", "lab_result", "commercial_qa", "opportunity_intelligence", "invisible_work")

    best = json.loads(BEST.read_text(encoding="utf-8"))
    if best.get("schedulerAuthority") != "Velvet Research Seat":
        fail("Best Skills schedulerAuthority must be Velvet Research Seat")
    freshness = best.get("freshnessContract") or {}
    if freshness.get("targetHours") != 48 or freshness.get("graceHours") != 4:
        fail("Best Skills freshness contract must be 48h + 4h grace")
    if "subscribe_timer" in str(best.get("standingNote") or ""):
        fail("Best Skills still depends on external subscribe_timer renewal")

    print("OK runtime-corners partial=1(jobs commissioning) living=activated best-skills=research-seat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
