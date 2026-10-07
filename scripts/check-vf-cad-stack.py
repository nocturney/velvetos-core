#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VELVETOS_PACK = ROOT / "packages" / "velvetos"
if str(VELVETOS_PACK) not in sys.path:
    sys.path.insert(0, str(VELVETOS_PACK))
from tool_status_resolver import compose_tool_status  # noqa: E402

registry_path = ROOT / "packages" / "vfprod" / "CAD-ENGINE-REGISTRY.json"
schema_path = ROOT / "packages" / "vfprod" / "GEOMETRY-IR.schema.json"
patterns_path = ROOT / "packages" / "vfprod" / "EXACT-CAD-PATTERNS.json"
mechanical_path = ROOT / "packages" / "vfprod" / "MECHANICAL-FEATURE-PACKS.json"
reverse_path = (
    ROOT
    / "docs"
    / "implementation"
    / "ai-3d-modeling-engineering-core"
    / "reverse-engineering-scan-to-cad-v1.json"
)
reverse_adapter = ROOT / "scripts" / "ai3d_reverse_engineering.py"
doc_path = ROOT / "packages" / "vfprod" / "CAD-ENGINE-STACK.md"
cli = ROOT / "scripts" / "vf_cad_stack.py"

assert registry_path.is_file(), registry_path
assert schema_path.is_file(), schema_path
assert patterns_path.is_file(), patterns_path
assert mechanical_path.is_file(), mechanical_path
assert reverse_path.is_file(), reverse_path
assert reverse_adapter.is_file(), reverse_adapter
assert doc_path.is_file(), doc_path
assert cli.is_file(), cli

registry = json.loads(registry_path.read_text(encoding="utf-8"))
assert registry["schema"] == "velvetos.cad-engines.v1"
assert registry["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert registry["printer_actions_allowed"] is False
assert registry["max_repair_iterations"] == 2
assert registry["exact_cad_patterns"] == "packages/vfprod/EXACT-CAD-PATTERNS.json"
assert registry["mechanical_feature_packs"] == "packages/vfprod/MECHANICAL-FEATURE-PACKS.json"

patterns = json.loads(patterns_path.read_text(encoding="utf-8"))
assert patterns["schema"] == "velvetos.exact-cad-patterns.v1"
assert patterns["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert patterns["coordinate_frame"]["primitive_local_origin"] == "xy_center_z_min"
assert patterns["coordinate_frame"]["hidden_transform_inference"] is False
assert patterns["semantic_selection"]["numeric_face_index_fallback"] is False
assert patterns["semantic_selection"]["ambiguous_selection"] == "BLOCKED"
assert patterns["curated_primitives"]["bd_warehouse"]["version"] == "0.3.0"
assert patterns["curated_primitives"]["bd_warehouse"]["license"] == "Apache-2.0"
assert patterns["safety"]["printer_actions_allowed"] is False
assert patterns["safety"]["machine_control_allowed"] is False

cli_source = cli.read_text(encoding="utf-8")
assert "semantic top-face selection found no +Z planar face" in cli_source
assert "semantic top-face selection ambiguous" in cli_source
assert "face.center().Z-top_z" in cli_source

mechanical = json.loads(mechanical_path.read_text(encoding="utf-8"))
assert mechanical["schema"] == "velvetos.ai3d.mechanical-feature-packs.v1"
assert mechanical["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert mechanical["upstream"]["bd_warehouse"]["version"] == "0.3.0"
assert mechanical["upstream"]["bd_warehouse"]["license"] == "Apache-2.0"
for pack_id in (
    "fasteners",
    "threads",
    "gears",
    "bearings",
    "inserts",
    "magnets",
    "fits",
    "enclosure",
):
    assert mechanical["packs"][pack_id]["status"].startswith("PROVEN"), pack_id
for pack_id in ("snap_fit", "living_hinge", "sheet_metal"):
    assert mechanical["packs"][pack_id]["status"].startswith("CANDIDATE"), pack_id
    assert mechanical["packs"][pack_id]["blockers"], pack_id

reverse = json.loads(reverse_path.read_text(encoding="utf-8"))
assert reverse["schema"] == "velvetos.ai3d.reverse-engineering-scan-to-cad.v1"
assert reverse["non_authoritative_staging"] is True
assert reverse["existing_composite_provider"] == "pipeline_scan_to_cad"
assert reverse["authorities"]["scan_mesh"] == "blender-capability-host"
assert reverse["authorities"]["exact_cad"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert reverse["epistemic_policy"]["scan_is_evidence_not_manufacturing_truth"] is True
assert reverse["epistemic_policy"]["automatic_semantic_feature_recognition_claimed"] is False
assert reverse["epistemic_policy"]["hidden_dimensions_may_be_invented"] is False
assert reverse["safety"]["duplicate_scan_router"] is False
assert reverse["safety"]["duplicate_cad_router"] is False
assert reverse["safety"]["printer_actions_allowed"] is False

engines = registry["engines"]
assert set(engines) == {"build123d", "cadquery", "jscad", "cad-cae-copilot", "forgent3d"}
assert engines["build123d"]["role"] == "primary"
assert engines["build123d"]["default_artifact_formats"] == ["STEP", "STL"]
assert {"STEP", "STL", "3MF", "GLB", "DXF", "SVG"} <= set(
    engines["build123d"]["artifact_formats"]
)
assert engines["cadquery"]["role"] == "secondary"
assert engines["jscad"]["role"] == "secondary"
assert engines["cad-cae-copilot"]["role"] == "pilot"
assert engines["forgent3d"]["role"] == "pilot"
for row in engines.values():
    assert row["paid_provider_required"] is False
    assert row["printer_control"] is False

assert registry["patterns"]["graph_cad"] == "IR_INSPIRATION_ONLY"
assert registry["patterns"]["multi_agent_cad"] == "BOUNDED_WORKFLOW_PATTERN_ONLY"
assert registry["radar"]["awesome-cad"]["runtime"] is False
assert registry["rejected_runtime"]["cadam"] is True

router = json.loads((ROOT / "packages" / "vfprod" / "FABRICATION-ROUTER.json").read_text(encoding="utf-8"))
assert router["engine_registry"] == "packages/vfprod/CAD-ENGINE-REGISTRY.json"
assert router["engine_stack_cli"] == "scripts/vf_cad_stack.py"

tool_status = compose_tool_status(ROOT, instance_id="velvet-factory", env={})
tts = tool_status["tools"]["text-to-cad"]
assert tts["engine_registry"] == "packages/vfprod/CAD-ENGINE-REGISTRY.json"
assert tts["engine_stack_cli"] == "scripts/vf_cad_stack.py"

links = json.loads((ROOT / "packages" / "vfresearch" / "LINKS.json").read_text(encoding="utf-8"))
awesome = [x for x in links["links"] if x.get("id") == "awesome-cad"]
assert len(awesome) == 1
assert "radar" in awesome[0]["note"].lower()

host = json.loads((ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-host-acceptance-2026-09-27.json").read_text(encoding="utf-8"))
assert host["printer_actions_allowed"] is False
assert host["paid_provider_calls_performed"] is False
assert all(host["engines"][name]["status"] == "PASS" for name in ("build123d","cadquery","jscad"))
assert host["chat_build_acceptance"]["status"] == "PASS"
assert host["chat_build_acceptance"]["auto_engine"] == "build123d"
assert host["chat_build_acceptance"]["printer_actions_performed"] is False
assert host["pilots"]["cad-cae-copilot"]["status"] == "PASS_LOCAL_SMOKE"
assert host["pilots"]["forgent3d"]["status"] == "SOURCE_CLONED_RUNTIME_UNVERIFIED"
assert host["rejected"]["cadam_runtime_installed"] is False

for cost_name in (
    "fabrication-cost-cadquery-2026-09-27.json",
    "fabrication-cost-jscad-2026-09-27.json",
    "fabrication-cost-cad-cae-copilot-2026-09-27.json",
    "fabrication-cost-forgent3d-2026-09-27.json",
):
    cost = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_cost_preflight.py"),
         str(ROOT / "packages" / "vfharness" / "state" / cost_name)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert cost.returncode == 0, cost.stdout + cost.stderr
    assert json.loads(cost.stdout)["status"] == "PASS"

proc = subprocess.run([sys.executable, str(cli), "contract"], cwd=ROOT, text=True, capture_output=True)
assert proc.returncode == 0, proc.stdout + proc.stderr
contract = json.loads(proc.stdout)
assert contract["status"] == "PASS"
assert contract["max_repair_iterations"] == 2
assert contract["exact_cad_patterns"] == "packages/vfprod/EXACT-CAD-PATTERNS.json"
assert contract["mechanical_feature_packs"] == "packages/vfprod/MECHANICAL-FEATURE-PACKS.json"
assert contract["coordinate_frame"] == "xy_center_z_min"

sample = ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-20260927" / "geometry-ir-sample.json"
proc = subprocess.run([sys.executable, str(cli), "ir-validate", "--input", str(sample)], cwd=ROOT, text=True, capture_output=True)
assert proc.returncode == 0, proc.stdout + proc.stderr
assert json.loads(proc.stdout)["status"] == "PASS"

plan_out = ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-20260927" / "plan-only-output"
proc = subprocess.run(
    [sys.executable, str(cli), "build", "--input", str(sample), "--engine", "build123d",
     "--out-dir", str(plan_out), "--plan-only"],
    cwd=ROOT, text=True, capture_output=True,
)
assert proc.returncode == 0, proc.stdout + proc.stderr
plan = json.loads(proc.stdout)
assert plan["status"] == "PASS"
assert plan["engine"] == "build123d"
assert plan["engine_version"] is None
assert plan["coordinate_frame"] == "xy_center_z_min"
assert plan["formats"] == ["step", "stl"]
assert plan["plan_only"] is True
assert len(plan["input_sha256"]) == 64
assert plan["artifacts"] == ["model.step", "model.stl"]

proc = subprocess.run(
    [
        sys.executable,
        str(cli),
        "build",
        "--input",
        str(sample),
        "--engine",
        "build123d",
        "--formats",
        "step,stl,3mf,dxf,svg",
        "--out-dir",
        str(plan_out),
        "--plan-only",
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
assert proc.returncode == 0, proc.stdout + proc.stderr
expanded_plan = json.loads(proc.stdout)
assert expanded_plan["formats"] == ["step", "stl", "3mf", "dxf", "svg"]
assert expanded_plan["artifacts"] == [
    "model.step",
    "model.stl",
    "model.3mf",
    "model-top.dxf",
    "model-top.svg",
]

proc = subprocess.run(
    [
        sys.executable,
        str(cli),
        "build",
        "--input",
        str(sample),
        "--engine",
        "build123d",
        "--formats",
        "step,unknown-format",
        "--out-dir",
        str(plan_out),
        "--plan-only",
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
assert proc.returncode == 2, proc.stdout + proc.stderr
blocked = json.loads(proc.stdout)
assert blocked["status"] == "BLOCKED"
assert blocked["reason"].startswith("unsupported_formats:build123d:")

state = ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-20260927" / "repair-state-test.json"
if state.exists():
    state.unlink()
for expected in ("REPAIR_ALLOWED", "REPAIR_ALLOWED", "FALLBACK_REQUIRED"):
    proc = subprocess.run([sys.executable, str(cli), "repair-next", "--state", str(state), "--failure", "geometry_check_failed"], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["decision"] == expected, payload
if state.exists():
    state.unlink()

print("check-vf-cad-stack: PASS")
