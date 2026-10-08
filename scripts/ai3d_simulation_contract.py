#!/usr/bin/env python3
"""Fail-closed preflight for bounded AI3D simulation fixtures.

This is not a solver, optimizer or production authority. It rejects unknown
materials, loads, supports and non-explicit safety assumptions before FEM.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_case(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("simulation case must be a JSON object")
    return value


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < 1e12


def validate_case(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def need(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    need(case.get("schema") == "velvetos.ai3d.simulation.case.v1", "schema_missing_or_unknown")
    need(case.get("purpose") == "internal-validation-only", "purpose_must_be_internal_validation_only")
    need(bool(case.get("fixture_id")), "fixture_id_required")
    need(bool(case.get("model_source")), "model_source_required")

    units = case.get("units") or {}
    need(
        units == {"length": "mm", "force": "N", "stress": "MPa", "density": "kg/m^3"},
        "unit_contract_requires_mm_N_MPa_kg_per_m3",
    )

    geometry = case.get("geometry") or {}
    need(geometry.get("kind") == "rectangular_bar", "geometry_kind_unsupported")
    for key in ("length_mm", "width_mm", "height_mm"):
        need(_positive(geometry.get(key)), f"geometry.{key}_required_positive")
    need(bool(geometry.get("source")), "geometry_source_required")

    material = case.get("material") or {}
    need(_positive(material.get("youngs_modulus_mpa")), "material.youngs_modulus_mpa_required_positive")
    poisson = material.get("poisson_ratio")
    need(
        isinstance(poisson, (int, float)) and not isinstance(poisson, bool) and 0 <= poisson < 0.5,
        "material.poisson_ratio_outside_stable_isotropic_range",
    )
    need(_positive(material.get("density_kg_m3")), "material.density_kg_m3_required_positive")
    need(bool(material.get("name")), "material.name_required")
    need(bool(material.get("source")) and "assumed" not in str(material.get("source", "")).lower(), "material.source_must_be_explicit")

    supports = case.get("supports")
    need(
        isinstance(supports, list) and len(supports) == 1
        and isinstance(supports[0], dict)
        and supports[0].get("face") == "x_min"
        and supports[0].get("condition") == "all_translations_fixed"
        and bool(supports[0].get("source")),
        "supports.explicit_x_min_full_fixation_required",
    )

    loads = case.get("loads")
    need(
        isinstance(loads, list) and len(loads) == 1
        and isinstance(loads[0], dict)
        and loads[0].get("face") == "x_max"
        and loads[0].get("type") == "surface_pressure"
        and loads[0].get("direction") == "outward"
        and _positive(loads[0].get("pressure_mpa"))
        and bool(loads[0].get("source")),
        "loads.explicit_positive_outward_x_max_pressure_required",
    )

    solver = case.get("solver") or {}
    need(solver.get("engine") == "FreeCAD.FEM+CalculiX.ccx", "solver_requires_canonical_freecad_calculix")
    need(solver.get("analysis") == "static_linear" and solver.get("geometrical_nonlinearity") is False, "solver_requires_linear_static")
    need(_positive(solver.get("maximum_seconds")) and solver.get("maximum_seconds", 10**20) <= 300, "solver_time_must_be_bounded")

    mesh = case.get("mesh") or {}
    sizes = mesh.get("element_sizes_mm")
    need(mesh.get("engine") == "FreeCAD.Gmsh" and mesh.get("element_order") == 2, "mesh_requires_gmsh_second_order")
    need(
        isinstance(sizes, list) and len(sizes) == 2 and all(_positive(s) for s in sizes)
        and sizes[0] > sizes[1] and 0.5 <= sizes[1] and sizes[0] <= 20,
        "mesh_requires_two_bounded_coarse_and_fine_sizes",
    )
    need(_positive(mesh.get("max_nodes")) and mesh.get("max_nodes", 10**20) <= 20000, "mesh_max_nodes_unbounded")
    need(_positive(mesh.get("max_elements")) and mesh.get("max_elements", 10**20) <= 20000, "mesh_max_elements_unbounded")

    verification = case.get("verification") or {}
    need(
        verification.get("analytical_formula")
        == "delta_x_mm=pressure_mpa*length_mm/youngs_modulus_mpa",
        "verification_analytic_reference_required",
    )
    for field in ("max_relative_error", "max_intermesh_relative_difference"):
        value = verification.get(field)
        need(
            isinstance(value, (float, int)) and not isinstance(value, bool) and 0 < value <= 0.05,
            f"verification.{field}_must_be_strict",
        )
    need(verification.get("require_positive_displacement") is True, "verification_positive_displacement_required")
    need(verification.get("require_solver_zero_exit") is True, "verification_solver_zero_exit_required")

    optimization = case.get("optimization") or {}
    need(optimization.get("automatic_acceptance") is False, "optimization_auto_acceptance_forbidden")
    need(optimization.get("requires_independent_validation") is True, "optimization_independent_validation_required")
    need(optimization.get("candidate_only") is True, "optimization_candidate_only")

    safety = case.get("safety") or {}
    for key in ("printer_actions_allowed", "machine_control_allowed", "invent_hidden_loads",
                "invent_material_properties", "invent_constraints"):
        need(safety.get(key) is False, f"safety.{key}_must_be_false")
    return failures


def validated_case(path: Path) -> dict[str, Any]:
    case = read_case(path)
    failures = validate_case(case)
    if failures:
        raise ValueError("simulation case BLOCKED: " + "; ".join(failures))
    return case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args()
    try:
        case = validated_case(args.case)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "errors": [str(exc)]}, indent=2))
        return 2
    print(json.dumps({
        "status": "PASS",
        "schema": case["schema"],
        "fixture_id": case["fixture_id"],
        "safety": case["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
