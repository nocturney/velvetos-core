#!/usr/bin/env python3
"""Host acceptance for AI3D Phase 5 mechanical feature packs."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packages" / "vfprod" / "MECHANICAL-FEATURE-PACKS.json"
FEATURE_CLI = ROOT / "scripts" / "ai3d_mechanical_features.py"

import sys

sys.path.insert(0, str(ROOT / "scripts"))
import vf_cad_stack  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def run_feature(
    runtime: Path,
    temp: Path,
    feature_id: str,
    params: dict[str, Any],
    *,
    expect: int = 0,
    geometry: bool = True,
) -> dict[str, Any]:
    safe = feature_id.replace(".", "_")
    params_file = temp / f"{safe}-params.json"
    params_file.write_text(json.dumps(params) + "\n", encoding="utf-8")
    command = [
        str(runtime),
        str(FEATURE_CLI),
        "build",
        "--feature",
        feature_id,
        "--params-file",
        str(params_file),
    ]
    if geometry:
        command.extend(["--out-dir", str(temp / safe)])
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=240,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"{feature_id}: rc={proc.returncode} expected={expect}\n"
            f"stdout={proc.stdout[-4000:]}\nstderr={proc.stderr[-4000:]}"
        )
    payload = json.loads(proc.stdout)
    assert payload["printer_actions_allowed"] is False
    return payload


def approx(value: float, expected: float, tolerance: float = 1e-5) -> None:
    assert abs(float(value) - expected) <= tolerance, (value, expected, tolerance)


def sanitized(payload: dict[str, Any]) -> dict[str, Any]:
    if payload["status"] != "PASS":
        return {
            "status": payload["status"],
            "reason": payload.get("reason"),
        }
    row: dict[str, Any] = {
        "status": "PASS",
        "kind": payload["kind"],
        "runtime": payload["runtime"],
    }
    if payload["kind"] == "geometry":
        row["metrics"] = payload["metrics"]
        row["artifact_hashes"] = {
            item["format"]: item["sha256"] for item in payload["artifacts"]
        }
    else:
        row["result"] = payload["result"]
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()

    packs = load(PACKS)
    assert packs["schema"] == "velvetos.ai3d.mechanical-feature-packs.v1"
    assert packs["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    assert packs["upstream"]["build123d"]["version"] == "0.11.1"
    assert packs["upstream"]["bd_warehouse"]["version"] == "0.3.0"
    assert packs["upstream"]["bd_warehouse"]["license"] == "Apache-2.0"
    for key in ("snap_fit", "living_hinge", "sheet_metal"):
        assert packs["packs"][key]["status"].startswith("CANDIDATE")
        assert packs["packs"][key]["blockers"]

    runtime = vf_cad_stack.runtime_paths()["build123d"]
    assert runtime.is_file(), runtime

    positive_cases = {
        "fastener.socket_head_cap_screw": (
            {"size": "M4-0.7", "length_mm": 16, "standard": "iso4762", "simple": True},
            True,
        ),
        "fastener.hex_nut": (
            {"size": "M4-0.7", "standard": "iso4032", "simple": True},
            True,
        ),
        "fastener.plain_washer": (
            {"size": "M4", "standard": "iso7089"},
            True,
        ),
        "thread.iso": (
            {
                "major_diameter_mm": 4,
                "pitch_mm": 0.7,
                "length_mm": 8,
                "external": True,
                "hand": "right",
                "interference_mm": 0.2,
                "simple": False,
            },
            True,
        ),
        "gear.spur": (
            {
                "module_mm": 1.0,
                "tooth_count": 20,
                "pressure_angle_deg": 20,
                "thickness_mm": 5,
            },
            True,
        ),
        "bearing.deep_groove": (
            {"size": "M8-22-7", "bearing_type": "SKT"},
            True,
        ),
        "insert.heat_set": (
            {
                "size": "M4-0.7-Standard",
                "fastener_type": "McMaster-Carr",
                "simple": True,
            },
            True,
        ),
        "magnet.cylindrical_pocket": (
            {
                "magnet_diameter_mm": 6,
                "magnet_height_mm": 3,
                "radial_clearance_mm": 0.15,
                "axial_clearance_mm": 0.2,
            },
            True,
        ),
        "enclosure.rect_open_top": (
            {
                "outer_x_mm": 60,
                "outer_y_mm": 40,
                "outer_z_mm": 20,
                "wall_mm": 2,
                "floor_mm": 2,
            },
            True,
        ),
        "fit.clearance_cylindrical": (
            {"shaft_diameter_mm": 4, "radial_clearance_mm": 0.1},
            False,
        ),
        "fit.interference_cylindrical": (
            {"hole_diameter_mm": 4, "radial_interference_mm": 0.025},
            False,
        ),
    }

    evidence_positive: dict[str, Any] = {}
    evidence_negative: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="ai3d-phase5-") as temp_name:
        temp = Path(temp_name)
        results: dict[str, dict[str, Any]] = {}
        for feature_id, (params, geometry) in positive_cases.items():
            payload = run_feature(
                runtime, temp, feature_id, params, geometry=geometry
            )
            assert payload["status"] == "PASS", payload
            if geometry:
                assert payload["kind"] == "geometry"
                assert payload["metrics"]["volume"] > 0
                assert all(value > 0 for value in payload["metrics"]["bbox_size"])
                assert {row["format"] for row in payload["artifacts"]} == {"STEP", "STL"}
                assert all(row["bytes"] > 0 and len(row["sha256"]) == 64 for row in payload["artifacts"])
            else:
                assert payload["kind"] == "calculation"
            results[feature_id] = payload
            evidence_positive[feature_id] = sanitized(payload)

        gear = results["gear.spur"]["metrics"]
        approx(gear["bbox_size"][0], 22.0, 1e-3)
        approx(gear["bbox_size"][1], 22.0, 1e-3)
        approx(gear["bbox_size"][2], 5.0, 1e-3)

        bearing = results["bearing.deep_groove"]["metrics"]
        approx(bearing["bbox_size"][0], 22.0, 1e-3)
        approx(bearing["bbox_size"][1], 22.0, 1e-3)
        approx(bearing["bbox_size"][2], 7.0, 1e-6)

        thread = results["thread.iso"]["metrics"]
        approx(thread["bbox_size"][0], 4.0, 1e-3)
        approx(thread["bbox_size"][1], 4.0, 1e-3)
        assert 8.0 <= thread["bbox_size"][2] <= 9.0

        magnet = results["magnet.cylindrical_pocket"]["metrics"]
        approx(magnet["bbox_size"][0], 6.3, 1e-6)
        approx(magnet["bbox_size"][1], 6.3, 1e-6)
        approx(magnet["bbox_size"][2], 3.2, 1e-6)

        enclosure = results["enclosure.rect_open_top"]["metrics"]
        assert enclosure["bbox_size"] == [60.0, 40.0, 20.0]
        approx(enclosure["volume"], 11712.0, 1e-6)

        clearance = results["fit.clearance_cylindrical"]["result"]
        approx(clearance["hole_diameter_mm"], 4.2)
        approx(clearance["diametral_clearance_mm"], 0.2)

        interference = results["fit.interference_cylindrical"]["result"]
        approx(interference["shaft_diameter_mm"], 4.05)
        approx(interference["diametral_interference_mm"], 0.05)

        negative_cases = [
            (
                "fastener.zero_length",
                "fastener.socket_head_cap_screw",
                {"size": "M4-0.7", "length_mm": 0, "standard": "iso4762"},
                True,
            ),
            (
                "fastener.invalid_size",
                "fastener.hex_nut",
                {"size": "M999-1", "standard": "iso4032"},
                True,
            ),
            (
                "thread.simple_no_solid",
                "thread.iso",
                {
                    "major_diameter_mm": 4,
                    "pitch_mm": 0.7,
                    "length_mm": 8,
                    "interference_mm": 0.2,
                    "simple": True,
                },
                True,
            ),
            (
                "thread.zero_pitch",
                "thread.iso",
                {
                    "major_diameter_mm": 4,
                    "pitch_mm": 0,
                    "length_mm": 8,
                    "interference_mm": 0.2,
                    "simple": False,
                },
                True,
            ),
            (
                "gear.too_few_teeth",
                "gear.spur",
                {
                    "module_mm": 1,
                    "tooth_count": 5,
                    "pressure_angle_deg": 20,
                    "thickness_mm": 5,
                },
                True,
            ),
            (
                "gear.invalid_pressure",
                "gear.spur",
                {
                    "module_mm": 1,
                    "tooth_count": 20,
                    "pressure_angle_deg": 45,
                    "thickness_mm": 5,
                },
                True,
            ),
            (
                "bearing.invalid_size",
                "bearing.deep_groove",
                {"size": "M99-99-99", "bearing_type": "SKT"},
                True,
            ),
            (
                "insert.invalid_size",
                "insert.heat_set",
                {"size": "M99-Invalid", "fastener_type": "McMaster-Carr"},
                True,
            ),
            (
                "magnet.negative_clearance",
                "magnet.cylindrical_pocket",
                {
                    "magnet_diameter_mm": 6,
                    "magnet_height_mm": 3,
                    "radial_clearance_mm": -0.1,
                    "axial_clearance_mm": 0.2,
                },
                True,
            ),
            (
                "fit.negative_clearance",
                "fit.clearance_cylindrical",
                {"shaft_diameter_mm": 4, "radial_clearance_mm": -0.01},
                False,
            ),
            (
                "fit.negative_interference",
                "fit.interference_cylindrical",
                {"hole_diameter_mm": 4, "radial_interference_mm": -0.01},
                False,
            ),
            (
                "enclosure.wall_consumes_cavity",
                "enclosure.rect_open_top",
                {
                    "outer_x_mm": 20,
                    "outer_y_mm": 20,
                    "outer_z_mm": 20,
                    "wall_mm": 10,
                    "floor_mm": 2,
                },
                True,
            ),
            (
                "enclosure.floor_too_thick",
                "enclosure.rect_open_top",
                {
                    "outer_x_mm": 20,
                    "outer_y_mm": 20,
                    "outer_z_mm": 20,
                    "wall_mm": 2,
                    "floor_mm": 20,
                },
                True,
            ),
            (
                "candidate.snap_fit_not_executable",
                "snap_fit",
                {},
                True,
            ),
            (
                "candidate.living_hinge_not_executable",
                "living_hinge",
                {},
                True,
            ),
            (
                "candidate.sheet_metal_not_executable",
                "sheet_metal",
                {},
                True,
            ),
        ]

        for case_id, feature_id, params, geometry in negative_cases:
            payload = run_feature(
                runtime,
                temp,
                feature_id,
                params,
                expect=2,
                geometry=geometry,
            )
            assert payload["status"] == "BLOCKED", (case_id, payload)
            assert payload["reason"], case_id
            evidence_negative[case_id] = sanitized(payload)

    evidence = {
        "schema": "velvetos.ai3d.phase5-mechanical-feature-acceptance.v1",
        "status": "PASS",
        "authority": "packages/vfprod/FABRICATION-ROUTER.md",
        "runtime": str(runtime),
        "positive_cases": evidence_positive,
        "adversarial_cases": evidence_negative,
        "candidate_only": {
            key: packs["packs"][key]
            for key in ("snap_fit", "living_hinge", "sheet_metal")
        },
        "safety": packs["safety"],
    }
    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        with args.evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print(
        "validate_ai3d_phase5_mechanical: PASS "
        f"positive={len(evidence_positive)} adversarial={len(evidence_negative)} "
        "candidates=snap_fit,living_hinge,sheet_metal"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
