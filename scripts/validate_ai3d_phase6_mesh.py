#!/usr/bin/env python3
"""Host acceptance for AI3D Phase 6 mesh/organic/implicit specialists.

The validator exercises the existing Blender Capability Host sidecar runtimes.
It never creates a second mesh router and does not mutate the live provider or
station registries.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
SPECIALISTS = BASE / "mesh-organic-specialists-v1.json"
LIVE_PROVIDER_REGISTRY = Path(
    r"D:\Velvet\State\CreativeCraft\blender-provider-registry.json"
)
LIVE_CREATIVE_REGISTRY = Path(
    r"D:\Velvet\Runtime\CreativeCraft\creative-craft-registry.json"
)
GEOMETRY_PROBE = Path(r"D:\Velvet\BlenderStack\probe_geometry_sidecars.py")
SCAN_PROBE = Path(r"D:\Velvet\BlenderStack\probe_scan_sidecar.py")


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def run(
    command: list[str],
    *,
    expect: int = 0,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"command failed rc={proc.returncode} expected={expect}: {command}\n"
            f"stdout={proc.stdout[-4000:]}\nstderr={proc.stderr[-4000:]}"
        )
    return proc


def prefixed_json(stdout: str, prefix: str) -> dict[str, Any]:
    rows = [line for line in stdout.splitlines() if line.startswith(prefix)]
    assert len(rows) == 1, (prefix, stdout[-3000:])
    return json.loads(rows[0][len(prefix) :])


def json_command(python: Path, code: str) -> dict[str, Any]:
    proc = run([str(python), "-c", code])
    rows = [line for line in proc.stdout.splitlines() if line.strip().startswith("{")]
    assert rows, proc.stdout
    return json.loads(rows[-1])


def provider_by_id(registry: dict[str, Any], provider_id: str) -> dict[str, Any]:
    rows = [
        provider
        for provider in registry.get("providers", [])
        if provider.get("id") == provider_id
    ]
    assert len(rows) == 1, provider_id
    return rows[0]


def functional_pass(provider: dict[str, Any]) -> bool:
    value = str(
        provider.get("functional_probe_verdict")
        or provider.get("functional_probe")
        or ""
    ).lower()
    return value == "native" or value == "passed" or value.startswith("passed_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()

    specialists = load(SPECIALISTS)
    providers = load(LIVE_PROVIDER_REGISTRY)
    creative = load(LIVE_CREATIVE_REGISTRY)

    assert specialists["schema"] == "velvetos.ai3d.mesh-organic-specialists.v1"
    assert specialists["non_authoritative_staging"] is True
    assert specialists["authority"]["id"] == "blender-capability-host"
    assert specialists["policy"] == {
        "no_second_mesh_router": True,
        "reuse_existing_typed_operations": True,
        "provider_proof_does_not_equal_typed_promotion": True,
        "candidate_requires_fixture_before_promotion": True,
    }

    geometry_python = Path(
        specialists["runtimes"]["geometry-core-py312"]["path"]
    )
    scan_python = Path(
        specialists["runtimes"]["scan-reconstruction-py312"]["path"]
    )
    assert geometry_python.is_file(), geometry_python
    assert scan_python.is_file(), scan_python
    assert GEOMETRY_PROBE.is_file(), GEOMETRY_PROBE
    assert SCAN_PROBE.is_file(), SCAN_PROBE

    expected = {
        "sidecar_trimesh": ("5.1.1", "geometry-core-py312"),
        "sidecar_manifold3d": ("3.5.4", "geometry-core-py312"),
        "sidecar_pymeshlab": ("2025.7.post1", "geometry-core-py312"),
        "sidecar_libigl": ("2.6.3", "geometry-core-py312"),
        "sidecar_open3d": ("0.20.0", "scan-reconstruction-py312"),
        "native_sculpt": ("5.2.2", "blender-5.2.2-main"),
        "native_voxel_remesh": ("5.2.2", "blender-5.2.2-main"),
    }
    live_provider_evidence: dict[str, Any] = {}
    for provider_id, (version, runtime) in expected.items():
        provider = provider_by_id(providers, provider_id)
        assert provider["version"] == version, provider_id
        assert provider["runtime"] == runtime, provider_id
        assert provider["installed"] is True, provider_id
        assert provider["enabled"] is True, provider_id
        assert provider["startup_probe"] == "passed", provider_id
        assert provider["background_startup"] == "passed", provider_id
        assert provider["headless_operation"] == "available", provider_id
        assert functional_pass(provider), provider_id
        live_provider_evidence[provider_id] = {
            "version": provider["version"],
            "runtime": provider["runtime"],
            "state": provider["state"],
            "functional_probe": (
                provider.get("functional_probe_verdict")
                or provider.get("functional_probe")
            ),
            "capabilities": provider["capabilities"],
        }

    transport = creative["tools"]["blender"]["station_transport"]
    proven_typed = set(transport["proven_capabilities"])
    reused = set(specialists["existing_typed_capabilities_reused"])
    assert reused <= proven_typed
    assert "sculpt.organic" not in proven_typed
    assert "scan.reconstruct" not in proven_typed
    assert "implicit.signed_distance" not in proven_typed
    assert "implicit.openvdb" not in proven_typed

    geometry_proc = run([str(geometry_python), str(GEOMETRY_PROBE)])
    geometry_fixture = prefixed_json(
        geometry_proc.stdout, "VF_GEOMETRY_FIXTURE "
    )
    assert all(row["success"] for row in geometry_fixture.values())
    assert geometry_fixture["manifold3d"]["watertight"] is True
    assert abs(geometry_fixture["manifold3d"]["volume"] - 12.0) < 1e-6
    assert geometry_fixture["pymeshlab"]["before_vertices"] == 4
    assert geometry_fixture["pymeshlab"]["after_vertices"] == 3
    assert geometry_fixture["libigl"]["adjacency_nnz"] == 12
    assert geometry_fixture["trimesh"]["faces"] == 320

    scan_proc = run([str(scan_python), str(SCAN_PROBE)])
    scan_fixture = prefixed_json(scan_proc.stdout, "VF_SCAN_FIXTURE ")
    assert all(row["success"] for row in scan_fixture.values())
    assert scan_fixture["open3d_downsample"]["before"] == 900
    assert 0 < scan_fixture["open3d_downsample"]["after"] < 900
    assert scan_fixture["open3d_icp"]["fitness"] > 0.99
    assert scan_fixture["open3d_icp"]["rmse"] < 1e-9

    versions = json_command(
        geometry_python,
        (
            "import importlib.metadata as m,json;"
            "names=['trimesh','manifold3d','pymeshlab','libigl','rtree'];"
            "print(json.dumps({n:m.version(n) for n in names}))"
        ),
    )
    assert versions == {
        "trimesh": "5.1.1",
        "manifold3d": "3.5.4",
        "pymeshlab": "2025.7.post1",
        "libigl": "2.6.3",
        "rtree": "1.4.1",
    }

    sdf = json_command(
        geometry_python,
        (
            "import trimesh,numpy as np,json;"
            "mesh=trimesh.creation.box(extents=[2,2,2]);"
            "pts=np.array([[0,0,0],[0.9,0,0],[1.1,0,0],[2,0,0]],dtype=float);"
            "print(json.dumps({'signed_distance':"
            "trimesh.proximity.signed_distance(mesh,pts).tolist(),"
            "'contains':mesh.contains(pts).tolist()}))"
        ),
    )
    expected_distance = [1.0, 0.1, -0.1, -1.0]
    for actual, expected_value in zip(sdf["signed_distance"], expected_distance):
        assert abs(float(actual) - expected_value) < 1e-9
    assert sdf["contains"] == [True, True, False, False]

    variant_batch = json_command(
        geometry_python,
        (
            "import trimesh,json;"
            "rows=[];"
            "\nfor size in (1,2,3):"
            "\n m=trimesh.creation.box(extents=[size,size,size]);"
            "\n rows.append({'size':size,'volume':float(m.volume),"
            "'watertight':bool(m.is_watertight),'faces':int(len(m.faces))});"
            "\nprint(json.dumps({'rows':rows}))"
        ),
    )
    assert [row["volume"] for row in variant_batch["rows"]] == [1.0, 8.0, 27.0]
    assert all(row["watertight"] for row in variant_batch["rows"])

    openvdb_import = json_command(
        geometry_python,
        (
            "import importlib.util,json;"
            "print(json.dumps({'pyopenvdb':bool(importlib.util.find_spec('pyopenvdb')),"
            "'openvdb':bool(importlib.util.find_spec('openvdb'))}))"
        ),
    )
    assert openvdb_import == {"pyopenvdb": False, "openvdb": False}
    openvdb = specialists["specialists"]["openvdb"]
    assert openvdb["status"] == "CANDIDATE_RUNTIME_GAP"
    assert openvdb["blockers"]

    assert specialists["specialists"]["trimesh_sdf"]["status"] == "PROVEN_BOUNDED"
    assert specialists["specialists"]["sidecar_pymeshlab"]["benchmark"]
    assert specialists["safety"] == {
        "printer_actions_allowed": False,
        "machine_control_allowed": False,
        "silent_unit_conversion": False,
        "duplicate_typed_operation_promotion": False,
    }

    evidence = {
        "schema": "velvetos.ai3d.phase6-mesh-organic-acceptance.v1",
        "status": "PASS",
        "authority": "blender-capability-host",
        "provider_registry": str(LIVE_PROVIDER_REGISTRY),
        "creative_craft_registry": str(LIVE_CREATIVE_REGISTRY),
        "geometry_runtime": str(geometry_python),
        "scan_runtime": str(scan_python),
        "live_providers": live_provider_evidence,
        "reused_typed_capabilities": sorted(reused),
        "geometry_fixture": geometry_fixture,
        "scan_fixture": scan_fixture,
        "runtime_versions": versions,
        "sdf_fixture": sdf,
        "variant_batch_fixture": variant_batch,
        "openvdb": {
            "status": openvdb["status"],
            "import_probe": openvdb_import,
            "blockers": openvdb["blockers"],
        },
        "safety": specialists["safety"],
    }

    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        with args.evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print(
        "validate_ai3d_phase6_mesh: PASS "
        "geometry=trimesh,manifold3d,pymeshlab,libigl "
        "scan=open3d sdf=trimesh+rtree openvdb=CANDIDATE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
