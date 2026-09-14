#!/usr/bin/env python3
"""Fail-closed audit for every Velvet Factory visual/content execution surface."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "vfom" / "VISUAL-STANDARD-ENFORCEMENT.json"
MARKER = "VF_VISUAL_STANDARD_GATE"
STD = "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md"
VIS = "packages/vfom/VISUAL-OS.md"
DNA = "packages/vfom/VISUAL-DNA.json"
ASSET = "MAHVJjCCKQA"
SHA = "707edde3f4d43cffea090bf90ed2418c160db2f8d90d104e4920b44697a014c0"

def fail(message: str) -> None:
    print(f"FAIL visual-surface-enforcement: {message}", file=sys.stderr)
    raise SystemExit(1)

def load_json(path: Path) -> dict:
    if not path.is_file(): fail(f"missing {path.relative_to(ROOT)}")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict): fail(f"{path.relative_to(ROOT)} must be object")
    return value

def main() -> None:
    policy = load_json(POLICY)
    expected = {
        "mode": "fail_closed", "standard": STD, "visualAuthority": VIS,
        "visualDNA": DNA, "canvaAssetId": ASSET, "artifactSha256": SHA,
        "hardFailure": "visual_standard_unavailable",
        "genericFallbackAllowed": False, "productTruthOverridesStyle": True,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            fail(f"policy {key} mismatch")
    required_evidence = set(policy.get("requiredEvidence") or [])
    expected_evidence = {
        "visual_standard_gate=PASS", "visual_standard_canva_asset_id",
        "visual_standard_artifact_sha256", "product_truth_source_refs",
        "exact_final_artifact_digest",
    }
    if not expected_evidence.issubset(required_evidence):
        fail(f"missing evidence contract {sorted(expected_evidence-required_evidence)}")

    surfaces = list(policy.get("vfCreativeSurfaces") or []) + list(policy.get("conditionalCanvaSurfaces") or [])
    if len(surfaces) < 18:
        fail("creative surface inventory unexpectedly small")
    for rel in surfaces:
        path = ROOT / rel
        if not path.is_file(): fail(f"missing creative surface {rel}")
        body = path.read_text(encoding="utf-8")
        for needle in (MARKER, STD, VIS, DNA, ASSET, SHA, "visual_standard_unavailable"):
            if needle not in body:
                fail(f"{rel} missing enforcement marker {needle}")

    runtime_gates = list(policy.get("runtimeGates") or [])
    if "scripts/vf_send_preflight.py" not in runtime_gates:
        fail("runtime gate inventory must include vf_send_preflight.py")
    runtime = (ROOT / "scripts/vf_send_preflight.py").read_text(encoding="utf-8")
    for needle in ("visual_standard_gate", "VELVET_VISUAL_STANDARD_ASSET", "VELVET_VISUAL_STANDARD_SHA256", "product_truth_source_refs", "visual_standard_unavailable"):
        if needle not in runtime:
            fail(f"vf_send_preflight.py missing runtime visual enforcement {needle}")

    foundry = load_json(ROOT / "packages/vfom/FOUNDRY.json")
    binding = foundry.get("visualStandardEnforcement") or {}
    if binding.get("policy") != "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json":
        fail("FOUNDRY visualStandardEnforcement policy binding mismatch")
    if binding.get("required") is not True or binding.get("mode") != "fail_closed":
        fail("FOUNDRY visual-standard enforcement must be required/fail_closed")
    if binding.get("genericFallbackAllowed") is not False:
        fail("FOUNDRY must forbid generic creative fallback")

    for rel in (
        "packages/vfgrowth/GATE.md", "packages/vfgrowth/PREFLIGHT.md",
        "packages/vfcanva/jobs/TEMPLATE.md", ".cursor/skills/vf-canva-instagram/SKILL.md",
    ):
        body = (ROOT / rel).read_text(encoding="utf-8")
        if "visual_standard_gate" not in body:
            fail(f"{rel} must require visual_standard_gate evidence")

    embedded = ROOT / "instances/velvet-factory"
    for rel in ("AGENTS.md", ".cursor/rules/velvetos-instance-desk.mdc", ".cursor/vf-desk.json"):
        path = embedded / rel
        if not path.is_file(): fail(f"missing embedded instance surface {rel}")
        body = path.read_text(encoding="utf-8")
        for needle in ("OWNER-APPROVED-GRID-STANDARD-2026-09-14.md", ASSET):
            if needle not in body:
                fail(f"embedded instance {rel} missing {needle}")
        lower = body.lower()
        if rel == ".cursor/rules/velvetos-instance-desk.mdc" and not ("stop" in lower and "generic" in lower):
            fail(f"embedded instance {rel} missing stop/generic-fallback semantics")
        if rel == ".cursor/vf-desk.json" and "fail_closed" not in lower:
            fail(f"embedded instance {rel} missing fail_closed machine binding")

    print(f"OK visual-standard enforced surfaces={len(surfaces)} fail_closed generic_fallback=forbidden")

if __name__ == "__main__":
    main()
