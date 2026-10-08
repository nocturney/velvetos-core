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
assembly_ecad_path = (
    ROOT
    / "docs"
    / "implementation"
    / "ai-3d-modeling-engineering-core"
    / "assembly-motion-ecad-v1.json"
)
assembly_ecad_adapter = ROOT / "scripts" / "ai3d_assembly_motion_ecad.py"
drawings_sheetmetal_path = (
    ROOT
    / "docs"
    / "implementation"
    / "ai-3d-modeling-engineering-core"
    / "drawings-vectors-sheetmetal-v1.json"
)
drawings_sheetmetal_adapter = ROOT / "scripts" / "ai3d_drawings_vectors_sheetmetal.py"
simulation_path = (
    ROOT / "docs" / "implementation" /
    "ai-3d-modeling-engineering-core" / "simulation-optimization-v1.json"
)
simulation_driver = ROOT / "scripts" / "ai3d_phase10_freecad_driver.py"
simulation_validator = ROOT / "scripts" / "validate_ai3d_phase10_simulation.py"
dfam_slicer_path = (
    ROOT / "docs" / "implementation" /
    "ai-3d-modeling-engineering-core" / "dfam-slicer-v1.json"
)
dfam_slicer_validator = ROOT / "scripts" / "validate_ai3d_phase11_dfam_slicer.py"
printer_profile_audit_path = (
    ROOT / "docs" / "implementation" /
    "ai-3d-modeling-engineering-core" / "printer-profile-audit-v1.json"
)
printer_profile_audit_validator = ROOT / "scripts" / "validate_ai3d_phase14_printer_profiles.py"
printer_profile_audit_receipt = (
    ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
    / "evidence" / "phase14-printer-profiles-acceptance-20261008.json"
)
cam_validation_path = (
    ROOT / "docs" / "implementation" /
    "ai-3d-modeling-engineering-core" / "cam-toolpath-v1.json"
)
cam_validation_script = ROOT / "scripts" / "validate_ai3d_phase12_cam.py"
cam_validation_post = ROOT / "scripts" / "ai3d_phase12_freecad_post.py"
cam_validation_parser = ROOT / "scripts" / "ai3d_cam_gcode_validator.py"
doc_path = ROOT / "packages" / "vfprod" / "CAD-ENGINE-STACK.md"
cli = ROOT / "scripts" / "vf_cad_stack.py"

assert registry_path.is_file(), registry_path
assert schema_path.is_file(), schema_path
assert patterns_path.is_file(), patterns_path
assert mechanical_path.is_file(), mechanical_path
assert reverse_path.is_file(), reverse_path
assert reverse_adapter.is_file(), reverse_adapter
assert assembly_ecad_path.is_file(), assembly_ecad_path
assert assembly_ecad_adapter.is_file(), assembly_ecad_adapter
assert drawings_sheetmetal_path.is_file(), drawings_sheetmetal_path
assert drawings_sheetmetal_adapter.is_file(), drawings_sheetmetal_adapter
assert simulation_path.is_file(), simulation_path
assert simulation_driver.is_file(), simulation_driver
assert simulation_validator.is_file(), simulation_validator
assert dfam_slicer_path.is_file(), dfam_slicer_path
assert dfam_slicer_validator.is_file(), dfam_slicer_validator
assert printer_profile_audit_path.is_file(), printer_profile_audit_path
assert printer_profile_audit_validator.is_file(), printer_profile_audit_validator
assert printer_profile_audit_receipt.is_file(), printer_profile_audit_receipt
assert cam_validation_path.is_file(), cam_validation_path
assert cam_validation_script.is_file(), cam_validation_script
assert cam_validation_post.is_file(), cam_validation_post
assert cam_validation_parser.is_file(), cam_validation_parser
assert doc_path.is_file(), doc_path
assert cli.is_file(), cli

registry = json.loads(registry_path.read_text(encoding="utf-8"))
assert registry["schema"] == "velvetos.cad-engines.v1"
assert registry["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert registry["printer_actions_allowed"] is False
assert registry["max_repair_iterations"] == 2
assert registry["exact_cad_patterns"] == "packages/vfprod/EXACT-CAD-PATTERNS.json"
assert registry["mechanical_feature_packs"] == "packages/vfprod/MECHANICAL-FEATURE-PACKS.json"
assert (
    registry["assembly_motion_ecad"]
    == "docs/implementation/ai-3d-modeling-engineering-core/assembly-motion-ecad-v1.json"
)
assert (
    registry["drawings_vectors_sheetmetal"]
    == "docs/implementation/ai-3d-modeling-engineering-core/drawings-vectors-sheetmetal-v1.json"
)
assert (
    registry["simulation_optimization"]
    == "docs/implementation/ai-3d-modeling-engineering-core/simulation-optimization-v1.json"
)
simulation = json.loads(simulation_path.read_text(encoding="utf-8"))
assert simulation["schema"] == "velvetos.ai3d.simulation-optimization.v1"
assert simulation["non_authoritative_staging"] is True
assert simulation["safety"]["auto_optimization_acceptance"] is False
assert simulation["safety"]["assume_unknown_material"] is False
assert simulation["safety"]["assume_unknown_load"] is False
assert simulation["safety"]["assume_unknown_constraints"] is False
assert simulation["safety"]["printer_actions_allowed"] is False
assert simulation["safety"]["machine_control_allowed"] is False
assert (
    registry["dfam_slicer"]
    == "docs/implementation/ai-3d-modeling-engineering-core/dfam-slicer-v1.json"
)
dfam_slicer = json.loads(dfam_slicer_path.read_text(encoding="utf-8"))
assert dfam_slicer["schema"] == "velvetos.ai3d.dfam-slicer.v1"
assert dfam_slicer["non_authoritative_staging"] is True
assert dfam_slicer["existing_slicer_authority"] == "scripts/vf_cad.py"
assert dfam_slicer["slicer"]["verified_profiles"]["h2d"]["state"] == "BLOCKED_MOTION_BOUNDS"
assert dfam_slicer["slicer"]["verified_profiles"]["c5"]["state"] == "PROVEN_OFFLINE_ONLY"
assert all(v is False for v in dfam_slicer["prohibitions"].values())
assert registry["printer_profile_audit"] == (
    "docs/implementation/ai-3d-modeling-engineering-core/printer-profile-audit-v1.json"
)
printer_audit = json.loads(printer_profile_audit_path.read_text(encoding="utf-8"))
printer_proof = json.loads(printer_profile_audit_receipt.read_text(encoding="utf-8"))
assert printer_audit["schema"] == "velvetos.ai3d.printer-profile-audit.v1"
assert printer_audit["non_authoritative_staging"] is True
assert printer_audit["existing_slicer_authority"] == "scripts/vf_cad.py"
assert all(v is False for v in printer_audit["prohibitions"].values())
assert printer_proof["status"] == "PASS_OFFLINE_AUDIT_WITH_EXPLICIT_BLOCKERS"
assert printer_proof["native_profiles_unchanged"] is True
assert printer_proof["printer_actions_executed"] is False
assert printer_proof["production_release_authorized"] is False
assert printer_proof["machine_firmware_commands_verified"] is False
assert printer_proof["profiles"]["u1"]["state"] == "OFFLINE_GCODE_VERIFIED_DIALECT_REVIEW"
assert printer_proof["profiles"]["c5pro"]["state"] == "OFFLINE_GCODE_VERIFIED_DIALECT_REVIEW"
assert printer_proof["profiles"]["ecc2"]["state"] == "BLOCKED_MOTION_BOUNDS"
assert printer_proof["h2d_motion"] == "BLOCKED_MOTION_BOUNDS"
phase14_receipt_check = subprocess.run(
    [sys.executable, str(printer_profile_audit_validator), "--verify-recorded"],
    cwd=ROOT, text=True, capture_output=True, timeout=25,
)
assert phase14_receipt_check.returncode == 0, phase14_receipt_check.stdout + phase14_receipt_check.stderr
assert (
    registry["cam_toolpath_validation"]
    == "docs/implementation/ai-3d-modeling-engineering-core/cam-toolpath-v1.json"
)
cam_contract = json.loads(cam_validation_path.read_text(encoding="utf-8"))
assert cam_contract["schema"] == "velvetos.ai3d.cam-toolpath.v1"
assert cam_contract["non_authoritative_staging"] is True
assert cam_contract["toolpath_provider"]["reuse_not_duplicate"] is True
assert cam_contract["freecad_post"]["no_native_job_strategy_claim"] is True
assert all(v is False for v in cam_contract["safety"].values())
assert cam_contract["existing_capability"] == "cam.toolpath"

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

assembly_ecad = json.loads(assembly_ecad_path.read_text(encoding="utf-8"))
assert assembly_ecad["schema"] == "velvetos.ai3d.assembly-motion-ecad.v1"
assert assembly_ecad["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert assembly_ecad["runtime_truth"]["build123d"]["version"] == "0.11.1"
assert assembly_ecad["runtime_truth"]["freecad"]["version"] == "1.1.3"
assert assembly_ecad["runtime_truth"]["kicad_cli"]["version"] == "10.0.6"
assert assembly_ecad["capabilities"]["assembly.joint.revolute"]["status"].startswith("PROVEN")
assert assembly_ecad["capabilities"]["assembly.freecad.fixed_joint"]["status"].startswith("PROVEN")
assert assembly_ecad["capabilities"]["electronics.enclosure_fit"]["status"].startswith("PROVEN")
assert (
    assembly_ecad["capabilities"]["electronics.pcb_step_export_components"]["status"]
    == "CANDIDATE_BLOCKED_FIXTURE"
)
assert (
    assembly_ecad["capabilities"]["robotics.urdf_pinocchio"]["status"]
    == "CANDIDATE_NOT_INSTALLED"
)
assert assembly_ecad["safety"]["printer_actions_allowed"] is False
assert assembly_ecad["safety"]["machine_control_allowed"] is False
assert assembly_ecad["safety"]["invent_joint_axes_or_limits"] is False

drawings_sheetmetal = json.loads(drawings_sheetmetal_path.read_text(encoding="utf-8"))
assert drawings_sheetmetal["schema"] == "velvetos.ai3d.drawings-vectors-sheetmetal.v1"
assert drawings_sheetmetal["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
for capability_id in (
    "drawing.techdraw.page",
    "drawing.dxf.roundtrip",
    "vector.text_glyph",
    "sheetmetal.unfold",
):
    assert drawings_sheetmetal["capabilities"][capability_id]["status"].startswith("PROVEN")
assert drawings_sheetmetal["capabilities"]["drawing.draftwright"]["status"] == "CANDIDATE_ISOLATED_EVAL"
assert drawings_sheetmetal["runtime_truth"]["sheetmetal"]["version"] == "0.8.24"
assert drawings_sheetmetal["runtime_truth"]["draftwright"]["version"] == "0.4.34"
assert drawings_sheetmetal["runtime_truth"]["draftwright"]["license"] == "AGPL-3.0"
assert drawings_sheetmetal["safety"]["printer_actions_allowed"] is False
assert drawings_sheetmetal["safety"]["machine_control_allowed"] is False
assert drawings_sheetmetal["safety"]["invent_k_factor"] is False
assert drawings_sheetmetal["safety"]["accept_unparseable_dxf"] is False
assert drawings_sheetmetal["safety"]["copy_or_bundle_font_files"] is False
assert drawings_sheetmetal["safety"]["draftwright_in_canonical_runtime"] is False

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
assert (
    contract["assembly_motion_ecad"]
    == "docs/implementation/ai-3d-modeling-engineering-core/assembly-motion-ecad-v1.json"
)
assert (
    contract["drawings_vectors_sheetmetal"]
    == "docs/implementation/ai-3d-modeling-engineering-core/drawings-vectors-sheetmetal-v1.json"
)
assert (
    contract["simulation_optimization"]
    == "docs/implementation/ai-3d-modeling-engineering-core/simulation-optimization-v1.json"
)
assert (
    contract["dfam_slicer"]
    == "docs/implementation/ai-3d-modeling-engineering-core/dfam-slicer-v1.json"
)
assert (
    contract["printer_profile_audit"]
    == "docs/implementation/ai-3d-modeling-engineering-core/printer-profile-audit-v1.json"
)
assert (
    contract["cam_toolpath_validation"]
    == "docs/implementation/ai-3d-modeling-engineering-core/cam-toolpath-v1.json"
)
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
