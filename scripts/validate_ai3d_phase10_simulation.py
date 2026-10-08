#!/usr/bin/env python3
"""Phase 10: live FreeCAD/Gmsh/CalculiX FEM proof + fail-closed guards.

Runs two independent quadratic tetrahedral meshes, requires a solved
displacement/stress field, checks an analytical elastic benchmark, validates
receipt hashes, and keeps optimization/TPMS results non-authoritative.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CASE = BASE / "fixtures" / "phase10" / "axial-bar-tension.json"
POLICY = BASE / "simulation-optimization-v1.json"
DRIVER = ROOT / "scripts" / "ai3d_phase10_freecad_driver.py"
TPMS = ROOT / "scripts" / "ai3d_tpms_research.py"
DEFAULT_EVIDENCE = BASE / "evidence" / "phase10-simulation-acceptance-20261008.json"
FREECAD = pathlib.Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")

sys.path.insert(0, str(ROOT / "scripts"))
from ai3d_simulation_contract import read_case, validate_case  # noqa: E402
import vf_cad_stack  # noqa: E402


def load(path: pathlib.Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise AssertionError(f"{path}: expected object")
    return result


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preflight_negative_controls(case: dict[str, Any]) -> dict[str, str]:
    variants: dict[str, Any] = {}

    bad = copy.deepcopy(case)
    del bad["material"]["youngs_modulus_mpa"]
    variants["missing_elastic_modulus"] = bad

    bad = copy.deepcopy(case)
    bad["material"]["source"] = "assumed"
    variants["invented_material_source"] = bad

    bad = copy.deepcopy(case)
    bad["material"]["poisson_ratio"] = 0.52
    variants["unstable_poisson_ratio"] = bad

    bad = copy.deepcopy(case)
    bad["loads"] = []
    variants["missing_force_or_pressure"] = bad

    bad = copy.deepcopy(case)
    bad["loads"][0]["direction"] = "unknown"
    variants["unknown_load_direction"] = bad

    bad = copy.deepcopy(case)
    bad["supports"] = []
    variants["missing_support"] = bad

    bad = copy.deepcopy(case)
    bad["mesh"]["max_nodes"] = 10**8
    variants["unbounded_mesh_resources"] = bad

    bad = copy.deepcopy(case)
    bad["solver"]["maximum_seconds"] = 24 * 3600
    variants["unbounded_solver_time"] = bad

    bad = copy.deepcopy(case)
    bad["optimization"]["automatic_acceptance"] = True
    variants["automatic_optimization_acceptance"] = bad

    bad = copy.deepcopy(case)
    bad["safety"]["machine_control_allowed"] = True
    variants["machine_action"] = bad

    bad = copy.deepcopy(case)
    bad["units"]["stress"] = "Pa"
    variants["unit_drift"] = bad

    results = {}
    for name, variant in variants.items():
        errors = validate_case(variant)
        assert errors, f"{name}: invalid contract unexpectedly accepted"
        results[name] = "BLOCKED"
    assert not validate_case(case), "valid explicit fixture unexpectedly blocked"
    return results


def verify_artifacts(root: pathlib.Path, result: dict[str, Any]) -> None:
    required = {"Mesh.inp", "Mesh.frd", "Mesh.dat", "tension-bar.FM.FCStd"}
    receipts = result["artifacts"]
    names = {item["name"] for item in receipts}
    assert names == required, (names, required)
    for item in receipts:
        assert "/" not in item["name"] and "\\" not in item["name"]
        path = root / item["name"]
        assert path.is_file(), f"missing artifact: {path}"
        assert path.stat().st_size == item["bytes"], item
        assert sha256(path) == item["sha256"], item
    assert result["solver"]["returncode"] == 0
    assert result["safety"]["printer_actions_allowed"] is False


def run_fem(
    *,
    launcher: pathlib.Path,
    outdir: pathlib.Path,
    size_mm: float,
    case: dict[str, Any],
) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env["AI3D_PHASE10_CASE"] = str(CASE)
    env["AI3D_PHASE10_OUT_DIR"] = str(outdir)
    env["AI3D_PHASE10_MESH_MM"] = str(size_mm)
    proc = subprocess.run(
        [str(FREECAD), str(launcher)],
        env=env,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=int(case["solver"]["maximum_seconds"]),
    )
    # FreeCADCmd may exit 0 despite a Python exception in an executed script;
    # require the explicit success marker AND a complete validated receipt.
    stdout = (proc.stdout or "") + "\n" + (proc.stderr or "")
    marker = "AI3D_PHASE10_RESULT"
    summary_path = outdir / "fem-result-summary.json"
    if marker not in stdout or not summary_path.is_file():
        raise AssertionError(
            f"FreeCAD/Gmsh/CalculiX failed to produce a verified result: "
            f"rc={proc.returncode}, output={stdout[-4000:]}"
        )
    result = load(summary_path)
    assert result["status"] == "PASS"
    assert result["case_sha256"] == sha256(CASE)
    assert result["mesher"]["node_count"] < case["mesh"]["max_nodes"]
    assert result["mesher"]["volume_elements"] < case["mesh"]["max_elements"]
    assert result["mesher"]["element_order"] == 2
    assert result["loaded_result_nodes"] >= 4
    assert result["selection"]["numeric_face_guess"] is False
    assert result["mesher"]["max_element_size_mm"] == size_mm
    assert result["solver"]["returncode"] == 0
    assert result["mean_free_end_displacement_x_mm"] > 0
    assert result["relative_error"] <= case["verification"]["max_relative_error"]
    assert result["von_mises_max_mpa"] >= case["loads"][0]["pressure_mpa"]
    assert result["elapsed_seconds"] <= case["solver"]["maximum_seconds"]
    verify_artifacts(outdir, result)
    return result


def run_tpms() -> tuple[dict[str, Any], dict[str, str]]:
    python = vf_cad_stack.runtime_paths()["build123d"]
    proc = subprocess.run(
        [str(python), str(TPMS), "--grid", "41", "--size-mm", "20"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr[-1000:]
    evidence = json.loads(proc.stdout)
    assert evidence["status"] == "RESEARCH_ONLY"
    assert evidence["sample_count"] == 41**3
    assert evidence["periodicity_max_boundary_error"] < 1e-12
    assert evidence["mesh_generated"] is False
    assert evidence["strength_claim"] is False
    assert evidence["optimization_accepted"] is False
    assert evidence["printer_actions_allowed"] is False

    bad = subprocess.run(
        [str(python), str(TPMS), "--grid", "10000", "--size-mm", "20"],
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=30,
    )
    assert bad.returncode != 0, "unbounded TPMS memory request was accepted"
    return evidence, {"unbounded_tpms_grid": "BLOCKED"}


def run_suite(*, evidence_out: pathlib.Path, artifacts_root: pathlib.Path | None) -> dict[str, Any]:
    case = read_case(CASE)
    policy = load(POLICY)
    assert policy["schema"] == "velvetos.ai3d.simulation-optimization.v1"
    assert policy["non_authoritative_staging"] is True
    assert policy["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    for flag, value in policy["safety"].items():
        if flag == "optimization_release_requires_human_review":
            continue
        assert value is False, (flag, value)

    negative = preflight_negative_controls(case)
    tpms, tpms_negative = run_tpms()
    negative.update(tpms_negative)

    tmp: tempfile.TemporaryDirectory[str] | None = None
    if artifacts_root is None:
        tmp = tempfile.TemporaryDirectory(prefix="ai3d-phase10-")
        root = pathlib.Path(tmp.name)
    else:
        root = artifacts_root.resolve()
        if root.exists():
            raise FileExistsError(f"refusing overwrite of Phase10 artifacts root: {root}")
        root.mkdir(parents=True, exist_ok=False)

    try:
        launcher = root / "launch.py"
        launcher.write_text(
            "import runpy,sys\n"
            f"target={str(DRIVER)!r}\n"
            "sys.argv=[target]\n"
            "runpy.run_path(target,run_name='__main__')\n",
            encoding="utf-8", newline="\n",
        )
        sizes = case["mesh"]["element_sizes_mm"]
        coarse = run_fem(
            launcher=launcher,
            outdir=root / "coarse",
            size_mm=float(sizes[0]),
            case=case,
        )
        fine = run_fem(
            launcher=launcher,
            outdir=root / "fine",
            size_mm=float(sizes[1]),
            case=case,
        )
        assert fine["mesher"]["node_count"] > coarse["mesher"]["node_count"]
        assert fine["mesher"]["volume_elements"] > coarse["mesher"]["volume_elements"]
        u0 = coarse["mean_free_end_displacement_x_mm"]
        u1 = fine["mean_free_end_displacement_x_mm"]
        difference = abs(u1 - u0) / abs(u1)
        assert difference <= case["verification"]["max_intermesh_relative_difference"]
        assert fine["relative_error"] <= coarse["relative_error"] + 0.005

        proof = {
            "schema": "velvetos.ai3d.phase10-simulation-acceptance.v1",
            "status": "PASS",
            "authority": policy["authority"],
            "fixture_sha256": sha256(CASE),
            "fixture": case["fixture_id"],
            "runtime": policy["runtime_truth"],
            "coarse": coarse,
            "fine": fine,
            "mesh_convergence": {
                "normalized_mean_displacement_difference": difference,
                "coarse_relative_analytic_error": coarse["relative_error"],
                "fine_relative_analytic_error": fine["relative_error"],
                "refinement_increases_volume_elements": True,
                "tolerance": case["verification"]["max_intermesh_relative_difference"],
            },
            "tpms_research": tpms,
            "negative_controls": negative,
            "optimization_acceptance": "BLOCKED_NO_STRUCTURAL_CERTIFICATION",
            "solver_production_scope": "reference-only / not structural certification",
            "artifact_persistence": (
                str(root) if artifacts_root is not None
                else "ephemeral validation; SHA-256, sizes and engine data retained in evidence"
            ),
            "distribution_license_gate": {
                "gmsh": "GPL-2.0-or-later with exception; existing FreeCAD external CLI; no bundling without review",
                "calculix": "GPL-2.0; existing FreeCAD external CLI; no bundling without review",
                "sfepy": "BSD-3-Clause / candidate not installed",
                "dolfinx": "license and platform review required / candidate not installed",
            },
        }
    finally:
        if tmp is not None:
            tmp.cleanup()

    evidence_out.parent.mkdir(parents=True, exist_ok=True)
    with evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(proof, indent=2) + "\n")

    print(
        "validate_ai3d_phase10_simulation: PASS "
        f"coarse_nodes={coarse['mesher']['node_count']} "
        f"fine_nodes={fine['mesher']['node_count']} "
        f"analytic_error={fine['relative_error']:.5f} "
        f"convergence_difference={difference:.6f} "
        f"negative_controls={len(negative)} TPMS=RESEARCH_ONLY"
    )
    return proof


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=pathlib.Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--artifacts-root", type=pathlib.Path)
    args = parser.parse_args()
    run_suite(evidence_out=args.evidence_out, artifacts_root=args.artifacts_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
