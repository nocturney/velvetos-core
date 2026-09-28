#!/usr/bin/env python3
"""Regression sensor for the provider-neutral scenario-labs capability graft."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "scripts" / "vf_blender_expert.py"
BLENDER = ROOT / "packages" / "vfprod" / "BLENDER-MCP.md"
EXPERT = ROOT / "packages" / "vfprod" / "experts" / "3D-MODEL.md"
GRAFT = ROOT / "packages" / "vfprod" / "SCENARIO-EXPERT-CAPABILITIES.md"
CREATIVE = ROOT / "packages" / "vfom" / "CREATIVE-REFINE-LOOP.md"
VFOM_SKILL = ROOT / "packages" / "vfom" / "SKILL.md"
CONTENT_SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
THREED_SKILL = ROOT / ".cursor" / "skills" / "vf-3d-router" / "SKILL.md"
EDIT_GATE = ROOT / "packages" / "vfgrowth" / "EDIT-GATE.md"
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"
SOURCE = ROOT / "packages" / "vfresearch" / "sources" / "2026-09-28-scenario-labs-skills.md"
LICENSE = ROOT / "packages" / "vfprod" / "third_party" / "scenario-labs" / "LICENSE"
VENDOR_ROOT = ROOT / "packages" / "vfprod" / "third_party" / "scenario-labs" / "blender"
VENDOR_MANIFEST = VENDOR_ROOT / "VENDOR-MANIFEST.json"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def need(path: Path, tokens: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(ROOT)} missing contract: {token}")


def load_planner():
    spec = importlib.util.spec_from_file_location("vf_blender_expert", PLANNER)
    if spec is None or spec.loader is None:
        fail("cannot load vf_blender_expert")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    need(GRAFT, ("skills-v0.48.0", "3D AI Studio", "Scenario MCP", "Provider-neutral print-prep"))
    need(CREATIVE, ("Product-shot baseline", "Baseline + delta", "Never use a drifted product render",
                    "Freeze MASTER", "comparison-only", "Scenario MCP"))
    need(BLENDER, ("SCENARIO-EXPERT-CAPABILITIES.md", "vf_blender_expert.py"))
    need(EXPERT, ("SCENARIO-EXPERT-CAPABILITIES.md", "3D AI Studio"))
    need(VFOM_SKILL, ("CREATIVE-REFINE-LOOP.md",))
    need(CONTENT_SKILL, ("CREATIVE-REFINE-LOOP.md",))
    need(THREED_SKILL, ("vf_blender_expert.py plan",))
    need(EDIT_GATE, ("CREATIVE-REFINE-LOOP.md",))
    need(SOURCE, ("scenario-labs/skills", "MIT", "9624e295fa33168bc1be22a628c23ba132d1c959"))
    need(LICENSE, ("MIT License", "Copyright (c) 2026 Scenario"))

    vendor = json.loads(VENDOR_MANIFEST.read_text(encoding="utf-8"))
    vendor_scripts = vendor.get("scripts") or []
    if len(vendor_scripts) != 15:
        fail("vendored Blender helper inventory must contain 15 scripts")
    for rel in vendor_scripts:
        if not (VENDOR_ROOT / rel).is_file():
            fail(f"missing vendored helper: {rel}")
    if list(VENDOR_ROOT.rglob("*.md")):
        fail("upstream normative Markdown must not be vendored as VelvetOS authority")

    data = json.loads(LINKS.read_text(encoding="utf-8"))
    row = next((x for x in data.get("links", []) if x.get("id") == "scenario-labs-skills"), None)
    if not row:
        fail("scenario-labs-skills missing from weekly source registry")
    if row.get("verdict") != "embedded-capabilities-only":
        fail("scenario source registry must say embedded-capabilities-only")
    if "Scenario MCP" not in row.get("note", ""):
        fail("scenario source registry must reject Scenario MCP runtime")

    module = load_planner()
    caps = module.capabilities()
    if caps.get("domain_count") != 13:
        fail("expected 13 Blender expert capability domains")
    if caps["upstream_provenance"].get("scenario_mcp_required") is not False:
        fail("planner must not require Scenario MCP")

    hard = module.build_plan("precision mechanical enclosure for printing STL")
    if "hard_surface" not in hard.get("expert_domains", []) or "retopology" not in hard.get("expert_domains", []):
        fail("printable hard-surface file must keep both form and mesh-cleanup domains")

    p = module.build_plan("פסלון אורגני להדפסה 3MF, תיקון mesh וריטופולוגיה")
    if "retopology" not in p.get("expert_domains", []):
        fail("printable mesh plan did not select retopology")
    if "existing_slicer_dry_run_completed" not in p.get("gates", []):
        fail("printable plan missing existing slicer dry-run")
    if p["execution_policy"].get("scenario_cloud_runtime") is not False:
        fail("planner enabled Scenario cloud runtime")
    if p["execution_policy"].get("physical_printer_control") is not False:
        fail("planner enabled printer control")
    helper_paths = [item for values in p.get("expert_helpers", {}).values() for item in values]
    if not helper_paths or not all((ROOT / item).is_file() for item in helper_paths):
        fail("planner did not bind real local helper files")

    source = PLANNER.read_text(encoding="utf-8")
    for forbidden in ("mcp.scenario.com", "scenario_tool_execute", "model_run(", "requests.post("):
        if forbidden in source:
            fail(f"planner contains Scenario/cloud execution dependency: {forbidden}")

    print("check-scenario-capability-graft: PASS")


if __name__ == "__main__":
    main()
