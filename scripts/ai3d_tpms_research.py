#!/usr/bin/env python3
"""Bounded TPMS gyroid field experiment; never a manufacturing-ready mesh.

Samples a periodic implicit level-set and reports periodicity, symmetry and
porosity proxy. Strength, stiffness and printability are NOT inferred.
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Any

import numpy as np


def sample(*, grid: int = 41, size_mm: float = 20.0) -> dict[str, Any]:
    if type(grid) is not int or not 17 <= grid <= 65:
        raise ValueError("grid must be an explicitly bounded integer 17..65")
    if not 1 <= size_mm <= 100:
        raise ValueError("cell size must be between 1 and 100 mm")

    coords = np.linspace(0.0, 2.0 * math.pi, grid, dtype=np.float64)
    x, y, z = np.meshgrid(coords, coords, coords, indexing="ij")
    f = np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)
    # Periodic field: opposite faces represent the same physical coordinates.
    boundary_error = max(
        float(np.max(np.abs(f[0, :, :] - f[-1, :, :]))),
        float(np.max(np.abs(f[:, 0, :] - f[:, -1, :]))),
        float(np.max(np.abs(f[:, :, 0] - f[:, :, -1]))),
    )
    if boundary_error > 1e-12:
        raise AssertionError(f"gyroid boundary is not periodic: {boundary_error}")

    # Exclude the duplicated periodic end-plane for volume sampling.
    interior = f[:-1, :-1, :-1]
    occupancy = {
        "threshold_minus_0_3": float(np.mean(interior < -0.3)),
        "threshold_zero": float(np.mean(interior < 0.0)),
        "threshold_plus_0_3": float(np.mean(interior < 0.3)),
    }
    if not (
        occupancy["threshold_minus_0_3"]
        < occupancy["threshold_zero"]
        < occupancy["threshold_plus_0_3"]
    ):
        raise AssertionError("threshold-vs-occupancy monotonicity failed")
    if not 0.45 <= occupancy["threshold_zero"] <= 0.55:
        raise AssertionError("gyroid zero-threshold occupancy symmetry failed")
    return {
        "schema": "velvetos.ai3d.tpms-gyroid-sampling.v1",
        "status": "RESEARCH_ONLY",
        "model": "sin(x)cos(y)+sin(y)cos(z)+sin(z)cos(x)",
        "cell_size_mm": float(size_mm),
        "grid_per_axis": grid,
        "sample_count": int(grid**3),
        "periodicity_max_boundary_error": boundary_error,
        "level_set_min": float(f.min()),
        "level_set_max": float(f.max()),
        "occupancy_proxies": occupancy,
        "mesh_generated": False,
        "strength_claim": False,
        "printability_claim": False,
        "optimization_accepted": False,
        "printer_actions_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=int, default=41)
    parser.add_argument("--size-mm", type=float, default=20.0)
    args = parser.parse_args()
    print(json.dumps(sample(grid=args.grid, size_mm=args.size_mm), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
