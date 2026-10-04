#!/usr/bin/env python3
"""Fail-closed audit for every Velvet Factory visual/content execution surface."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VELVETOS_PACK = ROOT / "packages" / "velvetos"
POLICY = ROOT / "packages" / "vfom" / "VISUAL-STANDARD-ENFORCEMENT.json"
MARKER = "VF_VISUAL_STANDARD_GATE"
STD = "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md"
VIS = "packages/vfom/VISUAL-OS.md"
DNA = "packages/vfom/VISUAL-DNA.json"
SHA = "df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897"

def fail(message: str) -> None:
    print(f"FAIL visual-surface-enforcement: {message}", file=sys.stderr)
    raise SystemExit(1)

def load_json(path: Path) -> dict:
    if not path.is_file(): fail(f"missing {path.relative_to(ROOT)}")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict): fail(f"{path.relative_to(ROOT)} must be object")
    return value


def canonical_tool_desk() -> Path:
    if str(VELVETOS_PACK) not in sys.path:
        sys.path.insert(0, str(VELVETOS_PACK))
    from instance_resolver import resolve_surface  # type: ignore
    try:
        return resolve_surface(ROOT, "toolDesk", instance_id="velvet-factory", env={})
    except Exception as exc:
        fail(f"cannot resolve canonical VF tool desk: {exc}")
    raise AssertionError("unreachable")


def main() -> None:
    policy = load_json(POLICY)
    expected = {
        "mode": "fail_closed", "standard": STD, "visualAuthority": VIS,
        "hardFailure": "visual_standard_unavailable",
        "genericFallbackAllowed": False, "productTruthOverridesStyle": True,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            fail(f"policy {key} mismatch")
    required_evidence = set(policy.get("requiredEvidence") or [])
    expected_evidence = {
        "visual_standard_gate=PASS", "creative_manifest_ref",
        "visual_standard_artifact_sha256", "product_truth_source_refs",
        "exact_final_artifact_digest",
    }
    if not expected_evidence.issubset(required_evidence):
        fail(f"missing evidence contract {sorted(expected_evidence-required_evidence)}")

    surfaces = list(policy.get("vfCreativeSurfaces") or [])
    if len(surfaces) < 12:
        fail("creative surface inventory unexpectedly small")
    parameterized_core_surfaces = {"packages/velvetos/modules/expert-media-director.md"}
    for rel in surfaces:
        path = ROOT / rel
        if not path.is_file(): fail(f"missing creative surface {rel}")
        body = path.read_text(encoding="utf-8")
        if rel in parameterized_core_surfaces:
            for needle in (
                MARKER,
                "creativeAutonomy.ownerApprovedVisualStandard",
                "artifact digest",
                "visual_standard_unavailable",
                "generic visual fallback is forbidden",
            ):
                if needle not in body:
                    fail(f"{rel} missing parameterized enforcement marker {needle}")
            for leaked in (STD, SHA):
                if leaked in body:
                    fail(f"{rel} must not embed instance visual-standard value {leaked}")
            continue
        for needle in (MARKER, STD, VIS, DNA, SHA, "visual_standard_unavailable"):
            if needle not in body:
                fail(f"{rel} missing enforcement marker {needle}")

    runtime_gates = list(policy.get("runtimeGates") or [])
    if "scripts/vf_send_preflight.py" not in runtime_gates:
        fail("runtime gate inventory must include vf_send_preflight.py")
    runtime = (ROOT / "scripts/vf_send_preflight.py").read_text(encoding="utf-8")
    for needle in ("visual_standard_gate", "VELVET_VISUAL_STANDARD_SHA256", "product_truth_source_refs", "visual_standard_unavailable"):
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
    ):
        body = (ROOT / rel).read_text(encoding="utf-8")
        if "visual_standard_gate" not in body:
            fail(f"{rel} must require visual_standard_gate evidence")

    embedded = ROOT / "instances/velvet-factory"
    embedded_surfaces = (
        ("AGENTS.md", embedded / "AGENTS.md"),
        ("instance-desk-rule", embedded / ".cursor" / "rules" / "velvetos-instance-desk.mdc"),
        ("toolDesk", canonical_tool_desk()),
    )
    for label, path in embedded_surfaces:
        if not path.is_file(): fail(f"missing embedded instance surface {label}")
        body = path.read_text(encoding="utf-8")
        for needle in ("OWNER-APPROVED-GRID-STANDARD-2026-09-14.md",):
            if needle not in body:
                fail(f"embedded instance {label} missing {needle}")
        lower = body.lower()
        if label == "instance-desk-rule" and not ("stop" in lower and "generic" in lower):
            fail(f"embedded instance {label} missing stop/generic-fallback semantics")
        if label == "toolDesk" and "fail_closed" not in lower:
            fail(f"embedded instance {label} missing fail_closed machine binding")

    print(f"OK visual-standard enforced surfaces={len(surfaces)} fail_closed generic_fallback=forbidden")

if __name__ == "__main__":
    main()
