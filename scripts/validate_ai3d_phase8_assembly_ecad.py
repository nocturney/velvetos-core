#!/usr/bin/env python3
"""Validate AI3D Phase 8 assembly, motion, collision, and ECAD/MCAD paths."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONFIG = BASE / "assembly-motion-ecad-v1.json"
CLI = ROOT / "scripts" / "ai3d_assembly_motion_ecad.py"
DEFAULT_EVIDENCE = BASE / "evidence" / "phase8-assembly-ecad-acceptance-20261007.json"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    assert isinstance(value, dict)
    return value


def run_suite(out_dir: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "all",
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def approx(value: float, expected: float, tol: float) -> None:
    assert abs(float(value) - float(expected)) <= tol, (value, expected, tol)


def artifact_ok(row: dict[str, Any]) -> None:
    assert row["bytes"] > 0
    assert len(row["sha256"]) == 64


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()

    config = load(CONFIG)
    assert config["schema"] == "velvetos.ai3d.assembly-motion-ecad.v1"
    assert config["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    assert config["runtime_truth"]["build123d"]["version"] == "0.11.1"
    assert config["runtime_truth"]["freecad"]["version"] == "1.1.3"
    assert config["runtime_truth"]["kicad_cli"]["version"] == "10.0.6"

    capabilities = config["capabilities"]
    for capability in (
        "assembly.joint.revolute",
        "assembly.motion.sweep",
        "assembly.collision.static",
        "assembly.freecad.fixed_joint",
        "electronics.pcb_step_export",
        "electronics.enclosure_fit",
    ):
        assert str(capabilities[capability]["status"]).startswith("PROVEN"), capability
    assert capabilities["electronics.pcb_step_export_components"]["status"] == "CANDIDATE_BLOCKED_FIXTURE"
    assert capabilities["robotics.urdf_pinocchio"]["status"] == "CANDIDATE_NOT_INSTALLED"

    safety = config["safety"]
    assert safety["printer_actions_allowed"] is False
    assert safety["machine_control_allowed"] is False
    assert safety["continuous_motion_claim_without_sampling"] is False
    assert safety["component_complete_ecad_claim_when_models_missing"] is False
    assert safety["invent_joint_axes_or_limits"] is False

    with tempfile.TemporaryDirectory(prefix="ai3d-phase8-") as temp_name:
        suite = run_suite(Path(temp_name))

    assert suite["schema"] == "velvetos.ai3d.phase8-fixture-suite.v1"
    assert suite["status"] == "PASS"
    assert suite["authority"] == config["authority"]

    motion = suite["motion"]
    assert motion["status"] == "PASS"
    assert motion["joint_type"] == "RevoluteJoint"
    assert motion["axis_origin_mm"] == [0, 0, 5]
    assert motion["axis_direction"] == [0, 0, 1]
    assert motion["angular_range_deg"] == [0, 180]
    assert motion["sampling_step_deg"] == 15
    assert len(motion["samples"]) == 13
    by_angle = {row["angle_deg"]: row for row in motion["samples"]}
    for angle in (0, 15, 75, 90, 105, 120, 135, 150, 165, 180):
        approx(by_angle[angle]["collision_volume_mm3"], 0.0, 1e-9)
    assert by_angle[30]["collision_volume_mm3"] > 0.0
    assert by_angle[45]["collision_volume_mm3"] > by_angle[30]["collision_volume_mm3"]
    assert by_angle[60]["collision_volume_mm3"] > 0.0
    approx(by_angle[45]["collision_volume_mm3"], 199.52900397563428, 1e-6)
    assert motion["range_negative_control"]["angle_deg"] == 181
    assert motion["range_negative_control"]["blocked"] is True
    for row in motion["artifacts"].values():
        artifact_ok(row)

    freecad = suite["freecad"]
    assert freecad["status"] == "PASS"
    assert freecad["freecad_version"] == "1.1.3"
    assert freecad["assembly_type"] == "Assembly::AssemblyObject"
    assert freecad["joint_group_type"] == "Assembly::JointGroup"
    assert freecad["joint_type"] == "Fixed"
    assert freecad["grounded_object"] == "FixedBox"
    assert freecad["placement_match"] is True
    for row in freecad["artifacts"].values():
        artifact_ok(row)

    ecad = suite["ecad"]
    assert ecad["status"] == "PASS"
    bbox = ecad["board_bbox_mm"]
    approx(bbox[0], 43.18, 1e-6)
    approx(bbox[1], 17.78, 1e-6)
    approx(bbox[2], 1.51, 1e-6)
    approx(ecad["good_collision_volume_mm3"], 0.0, 1e-9)
    assert ecad["negative_collision_volume_mm3"] > 100.0
    approx(ecad["negative_collision_volume_mm3"], 165.26329318508624, 1e-6)
    assert ecad["board_solids"] == 1
    component = ecad["component_complete_attempt"]
    assert component["status"] == "CANDIDATE_BLOCKED_FIXTURE"
    assert component["returncode"] == 0
    assert len(component["missing_model_messages"]) >= 2
    assert any("KICAD9_3DMODEL_DIR" in line for line in component["missing_model_messages"])
    for row in ecad["artifacts"].values():
        artifact_ok(row)

    evidence = {
        "schema": "velvetos.ai3d.phase8-assembly-ecad-acceptance.v1",
        "status": "PASS",
        "authority": config["authority"],
        "capabilities": capabilities,
        "motion": motion,
        "freecad": freecad,
        "ecad": ecad,
        "limitations": {
            "motion": "sampled 15-degree sweep; no continuous-collision guarantee",
            "ecad_components": (
                "component-complete Arduino Nano fixture remains blocked by installed "
                "template/model-reference mismatch; board-only STEP path is proven"
            ),
            "robotics": "URDF/Pinocchio remains optional candidate and is not installed",
        },
        "safety": safety,
    }
    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    with args.evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print(
        "validate_ai3d_phase8_assembly_ecad: PASS "
        "motion=build123d-revolute+collision freecad=Assembly-fixed "
        "ecad=KiCad-board-STEP+enclosure-fit components=CANDIDATE robotics=CANDIDATE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
