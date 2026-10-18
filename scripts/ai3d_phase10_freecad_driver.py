#!/usr/bin/env python3
"""Headless FreeCAD FEM + Gmsh + CalculiX execution for bounded reference cases.

Must be run by FreeCADCmd, not by the regular Python interpreter. All
geometry/materials/loads are explicit fixture facts; no hidden inference.
This script performs no printer, production or machine-control actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

import FreeCAD as App
import ObjectsFem
from femexamples.meshes import generate_mesh
from femtools import ccxtools

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ai3d_simulation_contract import validated_case  # noqa: E402

FEM_BIN = pathlib.Path(r"C:\Program Files\FreeCAD 1.1\bin")
GMSH = FEM_BIN / "gmsh.exe"
CCX = FEM_BIN / "ccx.exe"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def receipt(path: pathlib.Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}


def face_on_axis(shape: Any, axis: str, value: float) -> str:
    matches: list[int] = []
    for index, face in enumerate(shape.Faces, 1):
        center = face.CenterOfMass
        if abs(float(getattr(center, axis)) - value) <= 1e-7:
            matches.append(index)
    if len(matches) != 1:
        raise RuntimeError(f"ambiguous {axis}={value} face selection: {matches}")
    return f"Face{matches[0]}"


def local_version(binary: pathlib.Path, flag: str) -> str:
    proc = subprocess.run(
        [str(binary), flag],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
    )
    # The bundled CalculiX -v prints "This is Version 2.22" but returns
    # a non-zero process status for version-only invocation on Windows.
    # A nonzero exit remains fatal if no parsable version text exists.
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    import re
    found = re.search(r"(?:Version\s+)?(\d+\.\d+(?:\.\d+)?)", output)
    if not found:
        raise RuntimeError(f"version command failed for {binary}: rc={proc.returncode}, {output[:200]}")
    return found.group(1)


def run(case_path: pathlib.Path, out_dir: pathlib.Path, mesh_size_mm: float) -> dict[str, Any]:
    case = validated_case(case_path)
    allowed_sizes = case["mesh"]["element_sizes_mm"]
    if not any(abs(mesh_size_mm - size) < 1e-9 for size in allowed_sizes):
        raise ValueError(f"mesh size {mesh_size_mm} not one of explicitly approved {allowed_sizes}")
    if not (GMSH.is_file() and CCX.is_file()):
        raise FileNotFoundError("FreeCAD-bundled Gmsh or CalculiX binary missing")
    out_dir.mkdir(parents=True, exist_ok=True)

    os.environ["PATH"] = str(FEM_BIN) + os.pathsep + os.environ.get("PATH", "")
    start = time.monotonic()
    geometry = case["geometry"]
    mat_case = case["material"]
    bc = case["supports"][0]
    load = case["loads"][0]
    length = float(geometry["length_mm"])
    width = float(geometry["width_mm"])
    height = float(geometry["height_mm"])
    young = float(mat_case["youngs_modulus_mpa"])
    pressure = float(load["pressure_mpa"])

    doc = App.newDocument("AI3DPhase10Tension")
    block = doc.addObject("Part::Box", "TensionBar")
    block.Length = length
    block.Width = width
    block.Height = height
    doc.recompute()

    fixed_face = face_on_axis(block.Shape, "x", 0.0)
    loaded_face = face_on_axis(block.Shape, "x", length)
    if fixed_face == loaded_face:
        raise RuntimeError("support and load refer to the same face")

    analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc, "CalculiXCcxTools")
    solver.WorkingDir = str(out_dir)
    solver.AnalysisType = "static"
    solver.GeometricalNonlinearity = "linear"
    solver.ThermoMechSteadyState = False
    solver.MatrixSolverType = "default"
    solver.SplitInputWriter = False
    analysis.addObject(solver)

    material = ObjectsFem.makeMaterialSolid(doc, "MechanicalMaterial")
    material_props = material.Material
    material_props["Name"] = mat_case["name"]
    material_props["YoungsModulus"] = f"{young} MPa"
    material_props["PoissonRatio"] = str(mat_case["poisson_ratio"])
    material_props["Density"] = f"{mat_case['density_kg_m3']} kg/m^3"
    material.Material = material_props
    analysis.addObject(material)

    support = ObjectsFem.makeConstraintFixed(doc, "FixedXMin")
    support.References = [(block, fixed_face)]
    analysis.addObject(support)

    traction = ObjectsFem.makeConstraintPressure(doc, "TractionXMax")
    traction.References = [(block, loaded_face)]
    traction.Pressure = f"{pressure} MPa"
    traction.Reversed = True
    analysis.addObject(traction)

    mesh = analysis.addObject(ObjectsFem.makeMeshGmsh(doc, "Mesh"))[0]
    mesh.Shape = block
    mesh.ElementOrder = "2nd"
    mesh.SecondOrderLinear = False
    mesh.CharacteristicLengthMax = f"{mesh_size_mm} mm"
    mesh.CharacteristicLengthMin = f"{mesh_size_mm * 0.6} mm"
    doc.recompute()
    gmsh_ok = generate_mesh.mesh_from_mesher(mesh, "gmsh")
    nodes_count = int(mesh.FemMesh.NodeCount)
    elements_count = int(mesh.FemMesh.VolumeCount)
    if not gmsh_ok or nodes_count < 10 or elements_count < 2:
        raise RuntimeError("Gmsh tetrahedral volume mesh did not succeed")
    if nodes_count > case["mesh"]["max_nodes"] or elements_count > case["mesh"]["max_elements"]:
        raise RuntimeError("Gmsh result exceeded bounded mesh resource limits")
    doc.recompute()

    fem = ccxtools.FemToolsCcx(analysis, solver)
    fem.update_objects()
    fem.working_dir = str(out_dir)
    fem.set_inp_file_name()
    prerequisite_error = fem.check_prerequisites()
    if prerequisite_error:
        raise RuntimeError(f"FreeCAD FEM prerequisities: {prerequisite_error}")
    fem.write_inp_file()
    inp_path = pathlib.Path(fem.inp_file_name)
    if not inp_path.is_file():
        raise RuntimeError("CalculiX input deck not created")
    deck_text = inp_path.read_text(encoding="utf-8", errors="replace").upper()
    if "*ELEMENT" not in deck_text or "C3D10" not in deck_text:
        raise RuntimeError("expected quadratic solid tetrahedra in CalculiX input deck")
    if "*ELASTIC" not in deck_text or "*BOUNDARY" not in deck_text:
        raise RuntimeError("missing explicit material or boundary section in solver deck")
    if "*DLOAD" not in deck_text:
        raise RuntimeError("missing explicit face pressure load in solver deck")

    fem.setup_ccx()
    if not fem.ccx_binary_present:
        raise RuntimeError("bundled CalculiX binary not available")
    rc = fem.ccx_run()
    if rc != 0:
        raise RuntimeError(f"CalculiX exited with {rc}")
    fem.load_results()

    result = doc.getObject("CCX_Results")
    if result is None or not result.NodeNumbers or not result.DisplacementVectors:
        raise RuntimeError("CalculiX result object lacks displacement field")
    values = dict(zip(result.NodeNumbers, result.DisplacementVectors))
    loaded_nodes = [
        nid for nid, pos in mesh.FemMesh.Nodes.items()
        if abs(float(pos.x) - length) <= 1e-6 and nid in values
    ]
    if len(loaded_nodes) < 4:
        raise RuntimeError(f"loaded face has too few result nodes: {len(loaded_nodes)}")
    loaded_ux = [float(values[nid].x) for nid in loaded_nodes]
    ux_mean = sum(loaded_ux) / len(loaded_ux)
    ux_peak = max(loaded_ux)
    formula = pressure * length / young
    error = abs(ux_mean - formula) / formula
    if not math.isfinite(error) or ux_mean <= 0:
        raise RuntimeError("non-finite or negative tensile displacement result")

    von_mises = [float(x) for x in getattr(result, "vonMises", [])]
    if len(von_mises) != len(result.NodeNumbers):
        raise RuntimeError("missing expected nodal von Mises stress field")
    doc.recompute()
    fcstd_path = out_dir / "tension-bar.FM.FCStd"
    doc.saveAs(str(fcstd_path))

    artifact_paths = [
        inp_path,
        inp_path.with_suffix(".frd"),
        inp_path.with_suffix(".dat"),
        fcstd_path,
    ]
    if not all(p.is_file() for p in artifact_paths):
        raise RuntimeError("solver result artifacts missing")

    summary = {
        "schema": "velvetos.ai3d.phase10-fem-run.v1",
        "status": "PASS",
        "fixture_id": case["fixture_id"],
        "case_sha256": sha256(case_path),
        "source_type": case["model_source"],
        "solver": {"name": "CalculiX ccx", "version": local_version(CCX, "-v"), "returncode": rc},
        "mesher": {"name": "Gmsh", "version": local_version(GMSH, "-version"),
                   "node_count": nodes_count, "volume_elements": elements_count,
                   "element_order": 2, "max_element_size_mm": mesh_size_mm},
        "freecad_version": ".".join(App.Version()[:3]),
        "geometry": geometry,
        "material": mat_case,
        "supports": bc,
        "loads": load,
        "selection": {"fixed": fixed_face, "loaded": loaded_face, "numeric_face_guess": False},
        "mean_free_end_displacement_x_mm": ux_mean,
        "max_free_end_displacement_x_mm": ux_peak,
        "loaded_result_nodes": len(loaded_nodes),
        "analytical_extension_mm": formula,
        "relative_error": error,
        "von_mises_max_mpa": max(von_mises),
        "expected_nominal_axial_stress_mpa": pressure,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "artifacts": [receipt(path) for path in artifact_paths],
        "safety": case["safety"],
    }
    report = out_dir / "fem-result-summary.json"
    with report.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2) + "\n")
    print("AI3D_PHASE10_RESULT", json.dumps({
        "status": "PASS",
        "mesh_size_mm": mesh_size_mm,
        "nodes": nodes_count,
        "elements": elements_count,
        "mean_ux": ux_mean,
        "analytic_ux": formula,
        "relative_error": error,
    }), flush=True)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    # FreeCADCmd consumes unknown command-line flags before Python sees them.
    # Use explicit environment variables when invoked as a headless child process.
    parser.add_argument("--case", type=pathlib.Path, default=os.environ.get("AI3D_PHASE10_CASE"))
    parser.add_argument("--out-dir", type=pathlib.Path, default=os.environ.get("AI3D_PHASE10_OUT_DIR"))
    parser.add_argument("--mesh-size-mm", type=float, default=os.environ.get("AI3D_PHASE10_MESH_MM"))
    args = parser.parse_args()
    if not args.case or not args.out_dir or args.mesh_size_mm is None:
        raise ValueError("FreeCADCmd requires explicit case, output directory and mesh size")
    run(pathlib.Path(args.case).resolve(), pathlib.Path(args.out_dir).resolve(), float(args.mesh_size_mm))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
