#!/usr/bin/env python3
"""Build the non-authoritative AI3D CAD Capability Registry v1.

The builder reads current repository authority plus live CreativeCraft/Blender
registries. It never mutates those authorities and never promotes a candidate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CREATIVE = Path(r"D:\Velvet\Runtime\CreativeCraft\creative-craft-registry.json")
DEFAULT_BLENDER = Path(r"D:\Velvet\State\CreativeCraft\blender-provider-registry.json")
DEFAULT_STATIONS = Path(r"D:\Velvet\State\CreativeCraft\blender-station-routing.json")
RESEARCH_01 = "gdrive://1qel9QfKZSjF1eHFh5myL8wvCIJR5WlzY5stm9Uv2sgg"
RESEARCH_02 = "gdrive://1rx__tzqFaMl1fzBxtywbKWjRx3EOny6AfEr0ChByM1I"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def problem_class(capability: str) -> str:
    if capability.startswith("cad.") or capability.startswith("assembly."):
        return "exact_cad"
    if capability.startswith("drawing.") or capability.startswith("vector."):
        return "drawing_vector"
    if capability.startswith("sheetmetal."):
        return "manufacturing"
    if capability.startswith("optimization."):
        return "simulation"
    if capability.startswith("mesh.") or capability.startswith("implicit."):
        return "mesh_geometry"
    if capability.startswith("scan.") or capability.startswith("photogrammetry.") or capability.startswith("reconstruction."):
        return "reconstruction"
    if capability.startswith("geometry."):
        return "mesh_geometry"
    if capability.startswith("ai."):
        return "ai_generation"
    if capability.startswith("print.") or capability.startswith("cam."):
        return "manufacturing"
    if capability.startswith("interchange."):
        return "interchange"
    if capability.startswith("simulation."):
        return "simulation"
    if capability.startswith("electronics."):
        return "electronics"
    if capability.startswith("sculpt.") or capability.startswith("character."):
        return "organic_sculpt"
    return "automation"


def precision_model(capability: str) -> str:
    if capability == "cad.feature.fits":
        return "not_applicable"
    if capability.startswith("sheetmetal."):
        return "exact_brep"
    if capability.startswith("drawing.") or capability.startswith("vector."):
        return "mixed"
    if capability.startswith("assembly.") or capability.startswith("simulation."):
        return "mixed"
    if capability.startswith("cad.") or capability == "cam.toolpath":
        return "exact_brep"
    if capability.startswith("implicit."):
        return "mixed"
    if capability.startswith("mesh.") or capability.startswith("ai.") or capability.startswith("sculpt."):
        return "polygonal_mesh"
    if capability.startswith("scan.") or capability.startswith("photogrammetry."):
        return "point_cloud"
    if capability.startswith("reconstruction."):
        return "mixed"
    if capability.startswith("print."):
        return "process_output"
    if capability.startswith("interchange.") or capability.startswith("electronics."):
        return "mixed"
    return "not_applicable"


def io_types(capability: str) -> tuple[list[str], list[str]]:
    if capability == "cam.toolpath":
        return ["bounded_cam_request"], ["offline_grbl_artifact", "verification_receipt"]
    if capability == "print.prepare.dfam":
        return ["watertight_mesh", "bounded_overhang_angle"], ["dfam_geometry_report", "support_estimate", "verification_receipt"]
    if capability.startswith("print.slice."):
        return ["verified_mesh_or_3mf", "existing_native_printer_profile"], ["offline_gcode", "gcode_validation_report", "verification_receipt"]
    if capability == "assembly.joint.revolute":
        return ["cad_parts", "explicit_joint_contract"], ["assembly_state", "verification_receipt"]
    if capability == "assembly.motion.sweep":
        return ["assembly_state", "motion_contract"], ["sampled_motion_report", "verification_receipt"]
    if capability == "assembly.collision.static":
        return ["cad_parts", "placement_state"], ["collision_report", "verification_receipt"]
    if capability == "assembly.freecad.fixed_joint":
        return ["cad_parts", "joint_connectors"], ["freecad_assembly_artifact", "verification_receipt"]
    if capability == "cad.reverse_engineer":
        return [
            "scan_or_mesh_evidence",
            "engineering_contract",
            "dimension_evidence",
        ], ["cad_artifact", "fit_report", "verification_receipt"]
    if capability == "reconstruction.primitive_fit":
        return [
            "point_cloud_artifact",
            "explicit_segment_ref",
            "explicit_primitive_family",
            "dimension_evidence",
        ], ["geometry_ir", "fit_report", "verification_receipt"]
    if capability == "reconstruction.nurbs_fit":
        return [
            "structured_point_grid",
            "fit_contract",
        ], ["nurbs_surface_evidence", "fit_report", "verification_receipt"]
    if capability == "implicit.signed_distance":
        return ["mesh_artifact", "query_points"], ["signed_distance_field", "verification_receipt"]
    if capability == "implicit.openvdb":
        return ["mesh_or_volume_artifact"], ["vdb_volume_artifact", "verification_receipt"]
    if capability == "simulation.mesh.gmsh_tetra10":
        return ["cad_solid", "explicit_mesh_spec"], ["tetra10_mesh_receipt", "verification_receipt"]
    if capability == "simulation.linear_elastic_static":
        return ["cad_solid", "material_evidence", "load_and_support_contract", "tetra10_mesh"], ["solver_input", "frd_result", "displacement_and_stress_report", "verification_receipt"]
    if capability == "implicit.tpms_gyroid":
        return ["explicit_periodic_cell", "bounded_grid"], ["sampled_level_set_evidence"]
    if capability.startswith("optimization."):
        return ["validated_simulation", "human_review"], ["candidate_only_or_blocked"]
    if capability == "drawing.techdraw.page":
        return ["cad_artifact", "drawing_contract"], ["freecad_drawing_page", "dxf_artifact", "verification_receipt"]
    if capability == "drawing.dxf.roundtrip":
        return ["drawing_or_planar_geometry"], ["dxf_artifact", "roundtrip_report", "verification_receipt"]
    if capability == "vector.text_glyph":
        return ["unicode_text", "font_name", "vector_contract"], ["dxf_artifact", "svg_artifact", "roundtrip_report", "verification_receipt"]
    if capability == "sheetmetal.unfold":
        return ["sheetmetal_solid", "explicit_bend_allowance_contract"], ["unfolded_cad_artifact", "dxf_artifact", "verification_receipt"]
    if capability == "drawing.draftwright":
        return ["cad_artifact", "drawing_contract"], ["technical_drawing_artifact", "verification_receipt"]
    if capability == "cad.feature.fits":
        return ["typed_fit_request"], ["fit_calculation", "verification_receipt"]
    if capability.startswith("cad.feature."):
        return ["typed_mechanical_feature_request"], ["cad_artifact", "verification_receipt"]
    if capability.startswith("cad."):
        return ["typed_cad_request", "cad_artifact_or_geometry_ir"], ["cad_artifact", "verification_receipt"]
    if capability.startswith("mesh."):
        return ["mesh_artifact"], ["mesh_artifact_or_analysis", "verification_receipt"]
    if capability.startswith("scan.") or capability.startswith("photogrammetry."):
        return ["scan_or_point_cloud_artifact"], ["point_cloud_or_mesh_artifact", "verification_receipt"]
    if capability.startswith("print.slice"):
        return ["mesh_or_3mf_artifact", "slice_profile_ref"], ["gcode_or_slice_artifact", "verification_receipt"]
    if capability.startswith("print."):
        return ["mesh_or_3mf_artifact"], ["manufacturing_artifact_or_report", "verification_receipt"]
    if capability == "interchange.3mf":
        return ["geometry_artifact"], ["3mf_artifact", "verification_receipt"]
    if capability.startswith("electronics."):
        return ["pcb_artifact"], ["3d_geometry_artifact", "verification_receipt"]
    if capability.startswith("ai."):
        return ["image_text_or_multiview_evidence"], ["mesh_artifact", "verification_receipt"]
    if capability.startswith("sculpt."):
        return ["mesh_artifact", "bounded_sculpt_request"], ["mesh_artifact", "verification_receipt"]
    return ["typed_request"], ["artifact_or_receipt"]


def constraints(capability: str) -> list[str]:
    values = ["bounded_typed_request"]
    if capability.startswith("cad."):
        values.append("units_and_dimensions")
    if capability.startswith("mesh."):
        values.append("topology_validation")
    if capability == "cad.reverse_engineer":
        values.extend([
            "scan_is_evidence_not_manufacturing_truth",
            "dimension_evidence_required_for_critical_dimensions",
            "no_automatic_semantic_feature_recognition",
        ])
    if capability == "reconstruction.primitive_fit":
        values.extend([
            "explicit_segment_ref",
            "explicit_primitive_family",
            "no_hidden_dimension_inference",
        ])
    if capability == "reconstruction.nurbs_fit":
        values.extend([
            "explicit_fit_error_threshold",
            "surface_evidence_only",
            "separate_exact_cad_contract_required",
        ])
    if capability == "assembly.joint.revolute":
        values.extend(["explicit_joint_axis", "explicit_angle_range", "no_inferred_joint_axis"])
    if capability == "assembly.motion.sweep":
        values.extend(["sampled_motion_only", "no_continuous_collision_guarantee"])
    if capability == "assembly.collision.static":
        values.append("exact_brep_intersection")
    if capability == "assembly.freecad.fixed_joint":
        values.append("explicit_joint_connectors")
    if capability.startswith("electronics."):
        values.append("no_component_complete_claim_when_models_missing")
    if capability == "drawing.techdraw.page":
        values.extend(["template_explicit", "headless_page_fixture"])
    if capability == "drawing.dxf.roundtrip":
        values.extend(["full_dxf_file_required", "reopen_required"])
    if capability == "vector.text_glyph":
        values.extend(["font_name_required", "no_font_file_bundling", "unicode_roundtrip_validation"])
    if capability == "sheetmetal.unfold":
        values.extend(["explicit_thickness", "explicit_bend_radius", "explicit_k_factor", "explicit_k_factor_standard", "dxf_reopen_required"])
    if capability.startswith("simulation.") or capability.startswith("optimization."):
        values.extend(["explicit_material_loads_supports", "bounded_resources", "independent_evidence", "no_automatic_optimization_acceptance"])
    if capability == "implicit.tpms_gyroid":
        values.extend(["research_only", "no_strength_claim", "no_printability_claim"])
    if capability == "drawing.draftwright":
        values.extend(["isolated_eval_only", "no_canonical_runtime_install", "license_review_required", "canonical_build123d_not_downgraded"])
    if capability.startswith("print."):
        values.append("no_printer_network_action")
    if capability == "print.prepare.dfam" or capability.startswith("print.slice."):
        values.extend(["offline_only", "no_auto_print_release", "native_profiles_immutable"])
    if capability == "print.slice.orca_offline":
        values.extend(["reopen_step_stl_3mf_parity", "actual_gcode_header_and_extrusion", "bounded_machine_motion"])
    if capability == "print.slice.h2d_motion_validation":
        values.extend(["native_start_service_move_outside_declared_y_range", "independent_motion_envelope_evidence_required"])
    if capability == "cam.toolpath":
        values.extend(["fixed_promoted_fixture_bounds", "offline_output_only", "no_machine_control"])
    return values


def is_functional(provider: dict | None) -> bool:
    if not provider:
        return False
    probe = str(provider.get("functional_probe") or "").lower()
    return probe == "native" or probe == "passed" or probe.startswith("passed_")


def license_info(provider: dict | None, provenance: list[str]) -> tuple[str, dict]:
    raw = None if not provider else provider.get("license")
    license_text = None if raw is None else str(raw)
    lowered = "" if license_text is None else license_text.lower()
    nc = any(token in lowered for token in ("non-commercial", "noncommercial", "research only", "cc-by-nc"))
    network_reciprocal = "agpl" in lowered
    known_commercial = any(token in lowered for token in ("mit", "bsd", "apache", "mpl", "gpl", "lgpl"))
    if network_reciprocal:
        lane = "review-required"
    elif nc:
        lane = "research-nc"
    elif known_commercial and not any(
        cap.startswith("ai.") for cap in (provider or {}).get("capabilities", [])
    ):
        lane = "commercial-clean"
    else:
        lane = "review-required"
    allowed = (
        "research/personal/showcase only until separately reviewed"
        if lane == "research-nc"
        else "existing routed use only; no new redistribution/bundling until license review is complete"
        if lane == "review-required"
        else "commercial use subject to recorded license obligations and existing authority boundaries"
    )
    return lane, {
        "license_source": provenance[0] if provenance else None,
        "code_license": license_text,
        "data_license": None,
        "allowed_use": allowed,
        "attribution": "follow upstream license/notice requirements; none may be silently stripped",
        "redistribution": "not authorized by this registry beyond the recorded upstream terms",
        "bundle_policy": "prefer separate environment/runtime; review before bundling into reusable deliverables",
        "provenance": provenance,
    }


def version_for(provider: dict | None) -> str | None:
    if not provider:
        return None
    value = provider.get("version")
    return None if value is None else str(value)


def canonical_engine_metadata(engine_id: str) -> dict:
    """Probe the runtime that vf_cad_stack actually executes.

    Blender sidecars may carry a different version of the same library. For
    Fabrication Router authority records, execution-runtime truth wins.
    """
    if engine_id not in {"build123d", "cadquery", "bd_warehouse", "jscad"}:
        return {}
    try:
        import vf_cad_stack as cad_stack
    except Exception:
        return {}

    if engine_id in {"build123d", "cadquery", "bd_warehouse"}:
        runtime_key = "build123d" if engine_id == "bd_warehouse" else engine_id
        runtime = cad_stack.runtime_paths().get(runtime_key)
        if runtime is None:
            return {}
        result = {
            "runtime_id": f"vf-cad-stack:{runtime_key}-venv",
            "evidence_ref": f"runtime:{runtime}",
        }
        if not runtime.is_file():
            return result
        distribution = engine_id
        code = (
            "import importlib.metadata as m,json;"
            f"d=m.metadata({distribution!r});"
            f"print(json.dumps(dict(version=m.version({distribution!r}),"
            "license=d.get('License-Expression') or d.get('License'))))"
        )
        try:
            proc = subprocess.run(
                [str(runtime), "-c", code],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
            if proc.returncode == 0:
                payload = json.loads(proc.stdout.strip().splitlines()[-1])
                result.update(payload)
        except Exception:
            pass
        return result

    package_root = cad_stack.stack_root() / "jscad"
    dependencies = []
    licenses = set()
    for relative in (
        Path("node_modules") / "@jscad" / "modeling" / "package.json",
        Path("node_modules") / "@jscad" / "stl-serializer" / "package.json",
    ):
        path = package_root / relative
        if not path.is_file():
            continue
        payload = load(path)
        dependencies.append(f"{payload.get('name')} {payload.get('version')}")
        if payload.get("license"):
            licenses.add(str(payload["license"]))
    return {
        "runtime_id": "vf-cad-stack:jscad-node",
        "version": " + ".join(dependencies) if dependencies else None,
        "license": " + ".join(sorted(licenses)) if licenses else None,
        "evidence_ref": f"runtime:{package_root}",
    }


def make_record(
    *,
    record_id: str,
    capability_id: str,
    authority_id: str,
    authority_ref: str,
    engine_id: str,
    engine_version: str | None,
    adapter_id: str,
    adapter_ref: str,
    runtime_id: str,
    host_classes: list[str],
    headless: bool,
    verification_state: str,
    validators: list[str],
    evidence_refs: list[str],
    fallbacks: list[dict],
    status: str,
    provider: dict | None = None,
    license_provenance: list[str] | None = None,
) -> dict:
    inputs, outputs = io_types(capability_id)
    provenance = license_provenance or []
    lane, license_record = license_info(provider, provenance)
    return {
        "record_id": record_id,
        "capability_id": capability_id,
        "problem_class": problem_class(capability_id),
        "authority": {"id": authority_id, "source_ref": authority_ref},
        "engine": {"id": engine_id, "version": engine_version},
        "adapter": {"id": adapter_id, "source_ref": adapter_ref},
        "runtime": {"id": runtime_id, "host_classes": host_classes},
        "input_types": inputs,
        "output_types": outputs,
        "precision_model": precision_model(capability_id),
        "constraints_support": constraints(capability_id),
        "headless": headless,
        "license_lane": lane,
        "license": license_record,
        "verification": {
            "state": verification_state,
            "validators": validators,
            "evidence_refs": evidence_refs,
        },
        "fallback": fallbacks,
        "status": status,
    }


def build(repo_root: Path, creative_path: Path, blender_path: Path, station_path: Path) -> dict:
    cad = load(repo_root / "packages" / "vfprod" / "CAD-ENGINE-REGISTRY.json")
    mechanical_path = repo_root / "packages" / "vfprod" / "MECHANICAL-FEATURE-PACKS.json"
    mechanical = load(mechanical_path)
    mesh_specialists_path = (
        repo_root
        / "docs"
        / "implementation"
        / "ai-3d-modeling-engineering-core"
        / "mesh-organic-specialists-v1.json"
    )
    mesh_specialists = load(mesh_specialists_path)
    reverse_engineering_path = (
        repo_root
        / "docs"
        / "implementation"
        / "ai-3d-modeling-engineering-core"
        / "reverse-engineering-scan-to-cad-v1.json"
    )
    reverse_engineering = load(reverse_engineering_path)
    assembly_motion_ecad_path = (
        repo_root
        / "docs"
        / "implementation"
        / "ai-3d-modeling-engineering-core"
        / "assembly-motion-ecad-v1.json"
    )
    assembly_motion_ecad = load(assembly_motion_ecad_path)
    drawings_vectors_sheetmetal_path = (
        repo_root
        / "docs"
        / "implementation"
        / "ai-3d-modeling-engineering-core"
        / "drawings-vectors-sheetmetal-v1.json"
    )
    drawings_vectors_sheetmetal = load(drawings_vectors_sheetmetal_path)
    creative = load(creative_path)
    blender = load(blender_path)
    stations = load(station_path)
    providers = {item["id"]: item for item in blender["providers"]}
    records: list[dict] = []

    host_acceptance_path = (
        repo_root
        / "packages"
        / "vfharness"
        / "state"
        / "cad-engine-stack-host-acceptance-2026-09-27.json"
    )
    host_acceptance = load(host_acceptance_path)
    engine_provider_ids = {
        "build123d": "sidecar_build123d",
        "cadquery": "sidecar_cadquery",
    }
    for engine_id, engine in cad["engines"].items():
        provider = providers.get(engine_provider_ids.get(engine_id, ""))
        canonical = canonical_engine_metadata(engine_id)
        record_provider = dict(provider or {})
        if canonical.get("version"):
            record_provider["version"] = canonical["version"]
        if canonical.get("license"):
            record_provider["license"] = canonical["license"]

        host_row = host_acceptance.get("engines", {}).get(engine_id, {})
        host_proven = host_row.get("status") == "PASS"
        if engine["role"] == "primary":
            status = "ACTIVE_AUTHORITY"
            verify = "PROVEN_PROVIDER" if host_proven else "READY_BOUNDED"
        elif engine["role"] == "secondary":
            status = "PROVEN" if host_proven else "READY_BOUNDED"
            verify = "PROVEN_PROVIDER" if host_proven else "READY_BOUNDED"
        else:
            status, verify = "CANDIDATE", "CANDIDATE"

        evidence_refs = [
            "docs/implementation/ai-3d-modeling-engineering-core/evidence/check-vf-fabrication-router-20261007.log",
            str(host_acceptance_path),
        ]
        license_provenance = []
        if canonical.get("evidence_ref"):
            evidence_refs.append(canonical["evidence_ref"])
            license_provenance.append(canonical["evidence_ref"])
        provider_id = engine_provider_ids.get(engine_id)
        if provider_id:
            provider_ref = f"{blender_path}#provider:{provider_id}"
            evidence_refs.append(provider_ref)
            license_provenance.append(provider_ref)

        records.append(
            make_record(
                record_id=f"cad.solid.parametric--{engine_id}",
                capability_id="cad.solid.parametric",
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id=engine_id,
                engine_version=canonical.get("version") or version_for(provider),
                adapter_id="vf-cad-stack",
                adapter_ref="scripts/vf_cad_stack.py",
                runtime_id=canonical.get("runtime_id")
                or (provider.get("runtime") if provider else str(engine["mode"])),
                host_classes=["windows-primary"],
                headless=str(engine["mode"]) != "local_desktop_workbench",
                verification_state=verify,
                validators=[
                    "check-vf-fabrication-router",
                    "check-vf-3d-router",
                    "check-vf-cad-stack",
                ],
                evidence_refs=evidence_refs,
                fallbacks=[],
                status=status,
                provider=record_provider or None,
                license_provenance=license_provenance,
            )
        )

    bd_warehouse = canonical_engine_metadata("bd_warehouse")
    if bd_warehouse.get("version"):
        bd_provider = {
            "version": bd_warehouse["version"],
            "license": bd_warehouse.get("license"),
            "capabilities": ["cad.primitives.mechanical"],
        }
        records.append(
            make_record(
                record_id="cad.primitives.mechanical--bd_warehouse",
                capability_id="cad.primitives.mechanical",
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id="bd_warehouse",
                engine_version=bd_warehouse["version"],
                adapter_id="vf-cad-stack+bd-warehouse",
                adapter_ref="packages/vfprod/EXACT-CAD-PATTERNS.json",
                runtime_id=bd_warehouse["runtime_id"],
                host_classes=["windows-primary"],
                headless=True,
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase4_exact_cad"],
                evidence_refs=[
                    "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase4-exact-cad-acceptance-20261007.json",
                    "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase4-bd-warehouse-runtime-install-20261007.json",
                    bd_warehouse["evidence_ref"],
                ],
                fallbacks=[
                    {
                        "engine": "build123d",
                        "runtime": "vf-cad-stack:build123d-venv",
                    }
                ],
                status="PROVEN",
                provider=bd_provider,
                license_provenance=[
                    "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase4-bd-warehouse-runtime-install-20261007.json",
                    bd_warehouse["evidence_ref"],
                ],
            )
        )

    build123d_meta = canonical_engine_metadata("build123d")
    for pack_id, pack in mechanical["packs"].items():
        pack_status = str(pack["status"])
        is_proven = pack_status.startswith("PROVEN")
        is_candidate = pack_status.startswith("CANDIDATE")
        if not (is_proven or is_candidate):
            continue

        provider_name = pack.get("provider")
        if isinstance(provider_name, str) and provider_name.startswith("bd_warehouse"):
            metadata = bd_warehouse
            engine_id = "bd_warehouse"
            runtime_id = bd_warehouse.get("runtime_id", "vf-cad-stack:build123d-venv")
            provider_record = {
                "version": bd_warehouse.get("version"),
                "license": bd_warehouse.get("license"),
                "capabilities": [f"cad.feature.{pack_id}"],
            }
        elif provider_name == "build123d.native":
            metadata = build123d_meta
            engine_id = "build123d"
            runtime_id = build123d_meta.get("runtime_id", "vf-cad-stack:build123d-venv")
            provider_record = {
                "version": build123d_meta.get("version"),
                "license": build123d_meta.get("license"),
                "capabilities": [f"cad.feature.{pack_id}"],
            }
        elif provider_name == "velvetos.explicit-fit-calculator":
            metadata = {
                "version": "1.0",
                "license": None,
                "runtime_id": "vf-cad-stack:build123d-venv",
                "evidence_ref": "scripts/ai3d_mechanical_features.py",
            }
            engine_id = "velvetos-explicit-fit-calculator"
            runtime_id = metadata["runtime_id"]
            provider_record = {
                "version": metadata["version"],
                "license": metadata["license"],
                "capabilities": [f"cad.feature.{pack_id}"],
            }
        else:
            metadata = {
                "version": None,
                "license": None,
                "runtime_id": "not-admitted",
                "evidence_ref": str(mechanical_path),
            }
            engine_id = str(provider_name or f"candidate:{pack_id}")
            runtime_id = metadata["runtime_id"]
            provider_record = {
                "version": None,
                "license": None,
                "capabilities": [f"cad.feature.{pack_id}"],
            }

        evidence_refs = [
            "packages/vfprod/MECHANICAL-FEATURE-PACKS.json",
            "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase5-mechanical-feature-acceptance-20261007.json",
        ]
        if metadata.get("evidence_ref"):
            evidence_refs.append(metadata["evidence_ref"])

        records.append(
            make_record(
                record_id=f"cad.feature.{pack_id}--mechanical-pack",
                capability_id=f"cad.feature.{pack_id}",
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id=engine_id,
                engine_version=metadata.get("version"),
                adapter_id="ai3d-mechanical-features",
                adapter_ref="scripts/ai3d_mechanical_features.py",
                runtime_id=runtime_id,
                host_classes=["windows-primary"],
                headless=True,
                verification_state="PROVEN_PROVIDER" if is_proven else "CANDIDATE",
                validators=(
                    ["validate_ai3d_phase5_mechanical"]
                    if is_proven
                    else ["phase5 material/process qualification required"]
                ),
                evidence_refs=evidence_refs,
                fallbacks=[],
                status="PROVEN" if is_proven else "CANDIDATE",
                provider=provider_record,
                license_provenance=evidence_refs,
            )
        )

    evidence_fields = {
        "cad.validate_step": "cad_validate_step_evidence",
        "scan.pointcloud": "scan_pointcloud_evidence",
        "electronics.pcb_import": "pcb_import_evidence",
        "mesh.repair": "mesh_repair_evidence",
        "mesh.analysis": "mesh_analysis_evidence",
        "print.support_generation.support_fins": "support_fins_evidence",
        "interchange.3mf": "interchange_3mf_evidence",
        "mesh.remesh_repair": "mesh_remesh_repair_evidence",
        "mesh.retopology": "mesh_retopology_evidence",
        "scan.pointcloud.las_laz_io": "scan_las_laz_io_evidence",
        "scan.pointcloud.e57_io": "scan_e57_io_evidence",
        "scan.clean": "scan_clean_evidence",
        "print.slice.blender_integrated": "blender_integrated_slice_evidence",
        "cad.export_step": "cad_export_step_evidence",
        "print.format.3mf": "print_format_3mf_evidence",
        "agent.blender.control": "blender_control_readonly_evidence",
        "mesh.boolean_hardsurface": "mesh_boolean_hardsurface_evidence",
        "scan.register": "scan_register_evidence",
        "cam.toolpath": "cam_toolpath_evidence",
    }
    transport = stations["transport"]
    routes = stations["capability_routes"]
    for capability in transport["proven_capabilities"]:
        route = routes.get(capability, {})
        engine_id = route.get("provider", "station-default")
        provider = providers.get(engine_id)
        preferred_station = route.get("preferred_station", "windows-primary")
        fallback_engine = route.get("fallback_provider")
        fallback_station = route.get("fallback_station")
        fallbacks = []
        if fallback_station:
            fallbacks.append(
                {
                    "engine": fallback_engine or f"station-default:{fallback_station}",
                    "runtime": fallback_station,
                }
            )
        evidence = transport.get(evidence_fields.get(capability, ""), transport.get("evidence"))
        records.append(
            make_record(
                record_id=f"{capability}--blender-host",
                capability_id=capability,
                authority_id="blender-capability-host",
                authority_ref=str(creative_path) + "#tools.blender.station_transport",
                engine_id=engine_id,
                engine_version=version_for(provider),
                adapter_id="blender-provider-router",
                adapter_ref=r"D:\Velvet\Runtime\CreativeCraft\BlenderProviderRouter.py",
                runtime_id=preferred_station,
                host_classes=[preferred_station, "windows-primary"],
                headless=True,
                verification_state="PROVEN_TYPED",
                validators=["station-route", "station-health", "execute-typed", "artifact-verify"],
                evidence_refs=[str(evidence), str(station_path)],
                fallbacks=fallbacks,
                status="PROVEN",
                provider=provider,
                license_provenance=[f"{blender_path}#provider:{engine_id}", str(station_path)],
            )
        )

    provider_caps = [
        ("sidecar_triposr", "ai.image_to_3d"),
        ("sidecar_pymeshlab", "ai.image_to_3d.print_cleanup"),
        ("sidecar_trimesh", "automation.geometry"),
        ("sidecar_trimesh", "geometry.variant_batch"),
        ("sidecar_open3d", "scan.reconstruct"),
        ("sidecar_libigl", "simulation.analysis"),
        ("sidecar_colmap", "photogrammetry.sfm"),
        ("sidecar_meshroom", "photogrammetry.object_reconstruct"),
        ("sidecar_gmsh", "simulation.geometry"),
        ("sidecar_freecad", "cad.solid.parametric"),
        ("native_sculpt", "sculpt.organic"),
    ]
    existing_pairs = {(r["capability_id"], r["engine"]["id"]) for r in records}
    for provider_id, capability in provider_caps:
        provider = providers.get(provider_id)
        if not provider or (capability, provider_id) in existing_pairs:
            continue
        verified = is_functional(provider)
        specialist = mesh_specialists.get("specialists", {}).get(provider_id, {})
        phase6_new = capability in specialist.get("new_bounded_capabilities", [])
        validators = ["provider functional probe", "artifact verification"]
        evidence_refs = [f"{blender_path}#provider:{provider_id}"]
        license_provenance = [f"{blender_path}#provider:{provider_id}"]
        if phase6_new:
            validators.append("validate_ai3d_phase6_mesh")
            phase6_refs = [
                "docs/implementation/ai-3d-modeling-engineering-core/mesh-organic-specialists-v1.json",
                "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase6-mesh-organic-acceptance-20261007.json",
            ]
            evidence_refs.extend(phase6_refs)
            license_provenance.extend(phase6_refs)

        records.append(
            make_record(
                record_id=f"{capability}--{provider_id}",
                capability_id=capability,
                authority_id="blender-capability-host",
                authority_ref=str(blender_path),
                engine_id=provider_id,
                engine_version=version_for(provider),
                adapter_id="blender-provider-router",
                adapter_ref=r"D:\Velvet\Runtime\CreativeCraft\BlenderProviderRouter.py",
                runtime_id=str(provider.get("runtime") or "unknown"),
                host_classes=["windows-primary"],
                headless=provider.get("headless_operation") == "available",
                verification_state="PROVEN_PROVIDER" if verified else "READY_BOUNDED",
                validators=validators,
                evidence_refs=evidence_refs,
                fallbacks=[],
                status="PROVEN" if verified else "READY_BOUNDED",
                provider=provider,
                license_provenance=license_provenance,
            )
        )

    phase6_acceptance = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase6-mesh-organic-acceptance-20261007.json"
    )
    phase6_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "mesh-organic-specialists-v1.json"
    )
    sdf_specialist = mesh_specialists["specialists"]["trimesh_sdf"]
    if str(sdf_specialist["status"]).startswith("PROVEN"):
        sdf_provider = {
            "version": sdf_specialist["version"],
            "license": sdf_specialist["license"],
            "capabilities": ["implicit.signed_distance"],
        }
        records.append(
            make_record(
                record_id="implicit.signed_distance--trimesh_sdf",
                capability_id="implicit.signed_distance",
                authority_id="blender-capability-host",
                authority_ref=phase6_config,
                engine_id="trimesh_sdf",
                engine_version=sdf_specialist["version"],
                adapter_id="phase6-trimesh-sdf",
                adapter_ref="scripts/validate_ai3d_phase6_mesh.py",
                runtime_id=sdf_specialist["runtime"],
                host_classes=["windows-primary"],
                headless=True,
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase6_mesh"],
                evidence_refs=[
                    phase6_config,
                    phase6_acceptance,
                    "docs/implementation/ai-3d-modeling-engineering-core/evidence/phase6-rtree-runtime-install-20261007.json",
                ],
                fallbacks=[],
                status="PROVEN",
                provider=sdf_provider,
                license_provenance=[
                    phase6_config,
                    phase6_acceptance,
                ],
            )
        )

    openvdb = mesh_specialists["specialists"]["openvdb"]
    records.append(
        make_record(
            record_id="implicit.openvdb--candidate-openvdb",
            capability_id="implicit.openvdb",
            authority_id="blender-capability-host",
            authority_ref=phase6_config,
            engine_id="openvdb",
            engine_version=openvdb.get("version"),
            adapter_id="not-admitted",
            adapter_ref=phase6_config,
            runtime_id="not-admitted",
            host_classes=["windows-primary"],
            headless=False,
            verification_state="CANDIDATE",
            validators=["reproducible OpenVDB runtime fixture required"],
            evidence_refs=[phase6_config, phase6_acceptance],
            fallbacks=[],
            status="CANDIDATE",
            provider=None,
            license_provenance=[phase6_config, phase6_acceptance],
        )
    )

    phase7_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "reverse-engineering-scan-to-cad-v1.json"
    )
    phase7_acceptance = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase7-reverse-engineering-acceptance-20261007.json"
    )
    phase7_runtime = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase7-geomdl-runtime-install-20261007.json"
    )
    reverse_stages = {
        row["id"]: row for row in reverse_engineering["stages"]
    }

    scan_to_cad_provider = providers.get("pipeline_scan_to_cad")
    if scan_to_cad_provider:
        records.append(
            make_record(
                record_id="cad.reverse_engineer--pipeline_scan_to_cad",
                capability_id="cad.reverse_engineer",
                authority_id="blender-capability-host",
                authority_ref=str(blender_path),
                engine_id="pipeline_scan_to_cad",
                engine_version=version_for(scan_to_cad_provider),
                adapter_id="existing-scan-to-cad-composite",
                adapter_ref=str(blender_path) + "#provider:pipeline_scan_to_cad",
                runtime_id=str(scan_to_cad_provider.get("runtime") or "multi-sidecar"),
                host_classes=["windows-primary"],
                headless=scan_to_cad_provider.get("headless_operation") == "available",
                verification_state="PROVEN_PROVIDER",
                validators=[
                    "existing component probes",
                    "validate_ai3d_phase7_reverse_engineering",
                ],
                evidence_refs=[
                    str(blender_path) + "#provider:pipeline_scan_to_cad",
                    phase7_config,
                    phase7_acceptance,
                ],
                fallbacks=[
                    {
                        "engine": "build123d",
                        "runtime": "vf-cad-stack:build123d-venv",
                    }
                ],
                status="PROVEN",
                provider=scan_to_cad_provider,
                license_provenance=[
                    str(blender_path) + "#provider:pipeline_scan_to_cad",
                    phase7_config,
                ],
            )
        )

    primitive_stage = reverse_stages["primitive_fit"]
    primitive_provider = {
        "version": "1.0",
        "license": None,
        "capabilities": ["reconstruction.primitive_fit"],
    }
    records.append(
        make_record(
            record_id="reconstruction.primitive_fit--phase7-explicit-primitive",
            capability_id="reconstruction.primitive_fit",
            authority_id="fabrication-router",
            authority_ref=phase7_config,
            engine_id="phase7-explicit-primitive",
            engine_version="1.0",
            adapter_id="ai3d-reverse-engineering",
            adapter_ref="scripts/ai3d_reverse_engineering.py",
            runtime_id="repo-python",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase7_reverse_engineering"],
            evidence_refs=[phase7_config, phase7_acceptance],
            fallbacks=[],
            status="PROVEN",
            provider=primitive_provider,
            license_provenance=[phase7_config, phase7_acceptance],
        )
    )

    nurbs_stage = reverse_stages["nurbs_fit"]
    geomdl_provider = {
        "version": nurbs_stage["version"],
        "license": nurbs_stage["license"],
        "capabilities": ["reconstruction.nurbs_fit"],
    }
    records.append(
        make_record(
            record_id="reconstruction.nurbs_fit--geomdl",
            capability_id="reconstruction.nurbs_fit",
            authority_id="blender-capability-host",
            authority_ref=phase7_config,
            engine_id="geomdl",
            engine_version=nurbs_stage["version"],
            adapter_id="ai3d-reverse-engineering",
            adapter_ref="scripts/ai3d_reverse_engineering.py",
            runtime_id=nurbs_stage["runtime"],
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase7_reverse_engineering"],
            evidence_refs=[phase7_config, phase7_acceptance, phase7_runtime],
            fallbacks=[
                {
                    "engine": "phase7-explicit-primitive",
                    "runtime": "repo-python",
                }
            ],
            status="PROVEN",
            provider=geomdl_provider,
            license_provenance=[phase7_config, phase7_runtime],
        )
    )

    nurbsfit = reverse_engineering["research_candidates"]["nurbsfit_2026"]
    nurbsfit_provider = {
        "version": None,
        "license": nurbsfit["license"],
        "capabilities": ["reconstruction.nurbs_fit"],
    }
    records.append(
        make_record(
            record_id="reconstruction.nurbs_fit--candidate-nurbsfit_2026",
            capability_id="reconstruction.nurbs_fit",
            authority_id="blender-capability-host",
            authority_ref=phase7_config,
            engine_id="nurbsfit_2026",
            engine_version=None,
            adapter_id="not-admitted",
            adapter_ref=phase7_config,
            runtime_id="not-admitted",
            host_classes=["windows-primary"],
            headless=False,
            verification_state="CANDIDATE",
            validators=[
                "GoCoPP runtime qualification required",
                "NURBSDiff compatibility qualification required",
                "PyTorch3D CUDA qualification required",
                "reproducible VelvetOS fixture required",
            ],
            evidence_refs=[phase7_config, phase7_acceptance],
            fallbacks=[
                {
                    "engine": "geomdl",
                    "runtime": nurbs_stage["runtime"],
                }
            ],
            status="CANDIDATE",
            provider=nurbsfit_provider,
            license_provenance=[phase7_config, nurbsfit["source"]],
        )
    )

    phase8_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "assembly-motion-ecad-v1.json"
    )
    phase8_acceptance = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase8-assembly-ecad-acceptance-20261007.json"
    )
    phase8_caps = assembly_motion_ecad["capabilities"]

    phase8_build123d = canonical_engine_metadata("build123d")
    build123d_provider = {
        "version": phase8_build123d.get("version"),
        "license": phase8_build123d.get("license"),
        "capabilities": [
            "assembly.joint.revolute",
            "assembly.motion.sweep",
            "assembly.collision.static",
        ],
    }
    for capability_id in (
        "assembly.joint.revolute",
        "assembly.motion.sweep",
        "assembly.collision.static",
    ):
        row = phase8_caps[capability_id]
        assert str(row["status"]).startswith("PROVEN")
        records.append(
            make_record(
                record_id=f"{capability_id}--build123d-phase8",
                capability_id=capability_id,
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id="build123d",
                engine_version=phase8_build123d.get("version"),
                adapter_id="ai3d-assembly-motion-ecad",
                adapter_ref="scripts/ai3d_assembly_motion_ecad.py",
                runtime_id=phase8_build123d.get(
                    "runtime_id", "vf-cad-stack:build123d-venv"
                ),
                host_classes=["windows-primary"],
                headless=True,
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase8_assembly_ecad"],
                evidence_refs=[phase8_config, phase8_acceptance],
                fallbacks=[],
                status="PROVEN",
                provider=build123d_provider,
                license_provenance=[
                    phase8_config,
                    phase8_acceptance,
                    phase8_build123d.get(
                        "evidence_ref", "runtime:build123d-canonical"
                    ),
                ],
            )
        )

    freecad_provider = providers.get("sidecar_freecad")
    if freecad_provider:
        freecad_record = dict(freecad_provider)
        freecad_record["license"] = assembly_motion_ecad["runtime_truth"]["freecad"][
            "license"
        ]
        records.append(
            make_record(
                record_id="assembly.freecad.fixed_joint--sidecar_freecad",
                capability_id="assembly.freecad.fixed_joint",
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id="sidecar_freecad",
                engine_version=version_for(freecad_provider),
                adapter_id="ai3d-assembly-motion-ecad",
                adapter_ref="scripts/ai3d_assembly_motion_ecad.py",
                runtime_id=str(freecad_provider.get("runtime") or "freecad-1.1"),
                host_classes=["windows-primary"],
                headless=freecad_provider.get("headless_operation") == "available",
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase8_assembly_ecad"],
                evidence_refs=[
                    f"{blender_path}#provider:sidecar_freecad",
                    phase8_config,
                    phase8_acceptance,
                ],
                fallbacks=[
                    {
                        "engine": "build123d",
                        "runtime": "vf-cad-stack:build123d-venv",
                    }
                ],
                status="PROVEN",
                provider=freecad_record,
                license_provenance=[
                    phase8_config,
                    f"{blender_path}#provider:sidecar_freecad",
                ],
            )
        )

    kicad_provider = providers.get("sidecar_kicad_cli")
    if kicad_provider:
        records.append(
            make_record(
                record_id="electronics.pcb_step_export--sidecar_kicad_cli-phase8",
                capability_id="electronics.pcb_step_export",
                authority_id="blender-capability-host",
                authority_ref=str(blender_path),
                engine_id="sidecar_kicad_cli",
                engine_version=version_for(kicad_provider),
                adapter_id="ai3d-assembly-motion-ecad",
                adapter_ref="scripts/ai3d_assembly_motion_ecad.py",
                runtime_id=str(kicad_provider.get("runtime") or "kicad-10.0.6"),
                host_classes=["windows-primary"],
                headless=kicad_provider.get("headless_operation") == "available",
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase8_assembly_ecad"],
                evidence_refs=[
                    f"{blender_path}#provider:sidecar_kicad_cli",
                    phase8_config,
                    phase8_acceptance,
                ],
                fallbacks=[],
                status="PROVEN",
                provider=kicad_provider,
                license_provenance=[
                    f"{blender_path}#provider:sidecar_kicad_cli",
                    phase8_config,
                ],
            )
        )

    enclosure_provider = providers.get("pipeline_pcb_to_enclosure")
    if enclosure_provider:
        records.append(
            make_record(
                record_id="electronics.enclosure_fit--pipeline_pcb_to_enclosure-phase8",
                capability_id="electronics.enclosure_fit",
                authority_id="blender-capability-host",
                authority_ref=str(blender_path),
                engine_id="pipeline_pcb_to_enclosure",
                engine_version=version_for(enclosure_provider),
                adapter_id="existing-pcb-to-enclosure+phase8-validation",
                adapter_ref=str(blender_path) + "#provider:pipeline_pcb_to_enclosure",
                runtime_id=str(enclosure_provider.get("runtime") or "multi-provider"),
                host_classes=["windows-primary"],
                headless=enclosure_provider.get("headless_operation") == "available",
                verification_state="PROVEN_PROVIDER",
                validators=[
                    "existing component probes",
                    "validate_ai3d_phase8_assembly_ecad",
                ],
                evidence_refs=[
                    str(blender_path) + "#provider:pipeline_pcb_to_enclosure",
                    phase8_config,
                    phase8_acceptance,
                ],
                fallbacks=[],
                status="PROVEN",
                provider=enclosure_provider,
                license_provenance=[
                    str(blender_path) + "#provider:pipeline_pcb_to_enclosure",
                    phase8_config,
                ],
            )
        )

    records.append(
        make_record(
            record_id="electronics.pcb_step_export_components--candidate-kicad-models",
            capability_id="electronics.pcb_step_export_components",
            authority_id="blender-capability-host",
            authority_ref=phase8_config,
            engine_id="sidecar_kicad_cli",
            engine_version=assembly_motion_ecad["runtime_truth"]["kicad_cli"][
                "version"
            ],
            adapter_id="not-admitted-component-complete",
            adapter_ref="scripts/ai3d_assembly_motion_ecad.py",
            runtime_id="kicad-10.0.6",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="CANDIDATE",
            validators=[
                "component-complete STEP fixture required",
                "all referenced 3D models must resolve",
            ],
            evidence_refs=[phase8_config, phase8_acceptance],
            fallbacks=[
                {
                    "engine": "sidecar_kicad_cli",
                    "runtime": "kicad-10.0.6:board-only",
                }
            ],
            status="CANDIDATE",
            provider=None,
            license_provenance=[phase8_config, phase8_acceptance],
        )
    )

    records.append(
        make_record(
            record_id="robotics.urdf_pinocchio--candidate-pinocchio",
            capability_id="robotics.urdf_pinocchio",
            authority_id="fabrication-router",
            authority_ref=phase8_config,
            engine_id="pinocchio",
            engine_version=None,
            adapter_id="not-admitted",
            adapter_ref=phase8_config,
            runtime_id="not-admitted",
            host_classes=["windows-primary"],
            headless=False,
            verification_state="CANDIDATE",
            validators=[
                "articulated-mechanism use case required",
                "isolated dependency qualification required",
                "license qualification required",
                "positive and negative URDF fixtures required",
            ],
            evidence_refs=[phase8_config, phase8_acceptance],
            fallbacks=[
                {
                    "engine": "build123d",
                    "runtime": "vf-cad-stack:build123d-venv",
                },
                {
                    "engine": "sidecar_freecad",
                    "runtime": "freecad-1.1",
                },
            ],
            status="CANDIDATE",
            provider=None,
            license_provenance=[phase8_config],
        )
    )

    phase9_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "drawings-vectors-sheetmetal-v1.json"
    )
    phase9_acceptance = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase9-drawings-vectors-sheetmetal-acceptance-20261007.json"
    )
    phase9_caps = drawings_vectors_sheetmetal["capabilities"]
    phase9_runtime = drawings_vectors_sheetmetal["runtime_truth"]

    freecad_provider = providers.get("sidecar_freecad")
    if freecad_provider:
        freecad_techdraw_provider = dict(freecad_provider)
        freecad_techdraw_provider["license"] = phase9_runtime["freecad_techdraw"]["license"]
        freecad_techdraw_provider["capabilities"] = ["drawing.techdraw.page"]
        records.append(
            make_record(
                record_id="drawing.techdraw.page--freecad-techdraw",
                capability_id="drawing.techdraw.page",
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id="sidecar_freecad",
                engine_version=phase9_runtime["freecad_techdraw"]["version"],
                adapter_id="ai3d-drawings-vectors-sheetmetal",
                adapter_ref="scripts/ai3d_drawings_vectors_sheetmetal.py",
                runtime_id=str(freecad_provider.get("runtime") or "freecad-1.1"),
                host_classes=["windows-primary"],
                headless=True,
                verification_state="PROVEN_PROVIDER",
                validators=["validate_ai3d_phase9_drawings_vectors_sheetmetal"],
                evidence_refs=[
                    f"{blender_path}#provider:sidecar_freecad",
                    phase9_config,
                    phase9_acceptance,
                ],
                fallbacks=[],
                status="PROVEN",
                provider=freecad_techdraw_provider,
                license_provenance=[
                    f"{blender_path}#provider:sidecar_freecad",
                    phase9_config,
                    phase9_acceptance,
                ],
            )
        )

    dxf_provider = {
        "version": (
            f"FreeCAD {phase9_runtime['freecad_techdraw']['version']} + "
            f"ezdxf {phase9_runtime['ezdxf']['version']}"
        ),
        "license": "LGPL-2.1-or-later + MIT",
        "capabilities": ["drawing.dxf.roundtrip"],
    }
    records.append(
        make_record(
            record_id="drawing.dxf.roundtrip--freecad-techdraw-ezdxf",
            capability_id="drawing.dxf.roundtrip",
            authority_id="fabrication-router",
            authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
            engine_id="freecad-techdraw+ezdxf",
            engine_version=dxf_provider["version"],
            adapter_id="ai3d-drawings-vectors-sheetmetal",
            adapter_ref="scripts/ai3d_drawings_vectors_sheetmetal.py",
            runtime_id="freecad-1.1+vf-cad-stack:build123d-venv",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase9_drawings_vectors_sheetmetal"],
            evidence_refs=[phase9_config, phase9_acceptance],
            fallbacks=[
                {
                    "engine": "build123d",
                    "runtime": "vf-cad-stack:build123d-venv",
                }
            ],
            status="PROVEN",
            provider=dxf_provider,
            license_provenance=[phase9_config, phase9_acceptance],
        )
    )

    phase9_build123d = canonical_engine_metadata("build123d")
    text_provider = {
        "version": phase9_build123d.get("version"),
        "license": phase9_build123d.get("license"),
        "capabilities": ["vector.text_glyph"],
    }
    records.append(
        make_record(
            record_id="vector.text_glyph--build123d-phase9",
            capability_id="vector.text_glyph",
            authority_id="fabrication-router",
            authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
            engine_id="build123d",
            engine_version=phase9_build123d.get("version"),
            adapter_id="ai3d-drawings-vectors-sheetmetal",
            adapter_ref="scripts/ai3d_drawings_vectors_sheetmetal.py",
            runtime_id=phase9_build123d.get(
                "runtime_id", "vf-cad-stack:build123d-venv"
            ),
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase9_drawings_vectors_sheetmetal"],
            evidence_refs=[
                phase9_config,
                phase9_acceptance,
                phase9_build123d.get(
                    "evidence_ref", "runtime:build123d-canonical"
                ),
            ],
            fallbacks=[],
            status="PROVEN",
            provider=text_provider,
            license_provenance=[
                phase9_config,
                phase9_acceptance,
                phase9_build123d.get(
                    "evidence_ref", "runtime:build123d-canonical"
                ),
            ],
        )
    )

    sheetmetal_provider = {
        "version": phase9_runtime["sheetmetal"]["version"],
        "license": phase9_runtime["sheetmetal"]["license"],
        "capabilities": ["sheetmetal.unfold"],
    }
    records.append(
        make_record(
            record_id="sheetmetal.unfold--freecad-sheetmetal-0.8.24",
            capability_id="sheetmetal.unfold",
            authority_id="fabrication-router",
            authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
            engine_id="freecad-sheetmetal",
            engine_version=phase9_runtime["sheetmetal"]["version"],
            adapter_id="ai3d-drawings-vectors-sheetmetal",
            adapter_ref="scripts/ai3d_drawings_vectors_sheetmetal.py",
            runtime_id="phase9-freecad-sheetmetal-0.8.24",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase9_drawings_vectors_sheetmetal"],
            evidence_refs=[phase9_config, phase9_acceptance],
            fallbacks=[
                {
                    "engine": "sidecar_freecad",
                    "runtime": "freecad-1.1",
                }
            ],
            status="PROVEN",
            provider=sheetmetal_provider,
            license_provenance=[phase9_config, phase9_acceptance],
        )
    )

    draftwright_cfg = phase9_runtime["draftwright"]
    draftwright_provider = {
        "version": draftwright_cfg["version"],
        "license": draftwright_cfg["license"],
        "capabilities": ["drawing.draftwright"],
    }
    records.append(
        make_record(
            record_id="drawing.draftwright--candidate-draftwright-0.4.34",
            capability_id="drawing.draftwright",
            authority_id="fabrication-router",
            authority_ref=phase9_config,
            engine_id="draftwright",
            engine_version=draftwright_cfg["version"],
            adapter_id="not-admitted",
            adapter_ref=phase9_config,
            runtime_id="phase9-draftwright-eval",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="CANDIDATE",
            validators=[
                "AGPL product/license decision required",
                "canonical build123d compatibility required",
                "non-alpha release or explicit alpha acceptance required",
                "positive and negative VelvetOS drawing fixtures required before promotion",
            ],
            evidence_refs=[phase9_config, phase9_acceptance],
            fallbacks=[
                {
                    "engine": "sidecar_freecad",
                    "runtime": "freecad-1.1",
                }
            ],
            status="CANDIDATE",
            provider=draftwright_provider,
            license_provenance=[phase9_config, phase9_acceptance],
        )
    )

    # Phase 10 records are admitted only against a complete solver/mesh
    # acceptance proof. This is an extension of existing Fabrication authority,
    # not a FEM, optimizer, or printer-control authority of its own.
    phase10_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "simulation-optimization-v1.json"
    )
    phase10_evidence = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase10-simulation-acceptance-20261008.json"
    )
    phase10 = load(repo_root / phase10_config)
    proof10 = load(repo_root / phase10_evidence)
    assert phase10["schema"] == "velvetos.ai3d.simulation-optimization.v1"
    assert phase10["non_authoritative_staging"] is True
    assert proof10["status"] == "PASS"
    assert proof10["coarse"]["solver"]["returncode"] == 0
    assert proof10["fine"]["solver"]["returncode"] == 0
    assert len(proof10["negative_controls"]) >= 12
    assert proof10["tpms_research"]["status"] == "RESEARCH_ONLY"

    runtime10 = phase10["runtime_truth"]
    for cap_id, engine_id, version, status in (
        ("simulation.mesh.gmsh_tetra10", "freecad-gmsh-cli", runtime10["gmsh"]["bundled_version"], "PROVEN"),
        ("simulation.linear_elastic_static", "freecad-calculix-cli", runtime10["calculix"]["version"], "PROVEN"),
    ):
        source_license = (
            runtime10["gmsh"]["license"]
            if cap_id == "simulation.mesh.gmsh_tetra10"
            else runtime10["calculix"]["license"]
        )
        entry = make_record(
            record_id=f"{cap_id}--phase10-freecad",
            capability_id=cap_id,
            authority_id="fabrication-router",
            authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
            engine_id=engine_id,
            engine_version=version,
            adapter_id="ai3d-phase10-freecad-fem",
            adapter_ref="scripts/ai3d_phase10_freecad_driver.py",
            runtime_id="freecad-1.1:FEM+Gmsh+CalculiX",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="PROVEN_PROVIDER",
            validators=["validate_ai3d_phase10_simulation"],
            evidence_refs=[phase10_config, phase10_evidence],
            fallbacks=[],
            status=status,
            provider={
                "version": version,
                "license": source_license,
                "capabilities": [cap_id],
            },
            license_provenance=[phase10_config, phase10_evidence],
        )
        # GPL solvers are permitted for bounded existing local use, but they
        # must never be silently rebundled into commercial/closed deliverables.
        entry["license_lane"] = "review-required"
        entry["license"]["allowed_use"] = (
            "existing standalone FreeCAD-bundled command-line execution only; "
            "separate legal review before combining or distributing binaries"
        )
        entry["license"]["bundle_policy"] = (
            "no inclusion in a proprietary installer, product, or binary bundle "
            "without a recorded GPL compliance/legal approval"
        )
        records.append(entry)

    records.append(
        make_record(
            record_id="implicit.tpms_gyroid--research-phase10",
            capability_id="implicit.tpms_gyroid",
            authority_id="fabrication-router",
            authority_ref=phase10_config,
            engine_id="numpy-periodic-gyroid",
            engine_version="1.0",
            adapter_id="ai3d-tpms-research",
            adapter_ref="scripts/ai3d_tpms_research.py",
            runtime_id="vf-cad-stack:build123d-venv",
            host_classes=["windows-primary"],
            headless=True,
            verification_state="RESEARCH_ONLY",
            validators=["validate_ai3d_phase10_simulation", "no-mesh-or-strength-claim"],
            evidence_refs=[phase10_config, phase10_evidence],
            fallbacks=[],
            status="RESEARCH_ONLY",
            provider={
                "version": "1.0",
                "license": None,
                "capabilities": ["implicit.tpms_gyroid"],
            },
            license_provenance=[phase10_config, phase10_evidence],
        )
    )

    for cap_id, engine_id, licence in (
        ("simulation.advanced_sfepy", "sfepy", "BSD-3-Clause"),
        ("simulation.advanced_dolfinx", "dolfinx", None),
    ):
        records.append(
            make_record(
                record_id=f"{cap_id}--candidate-{engine_id}",
                capability_id=cap_id,
                authority_id="fabrication-router",
                authority_ref=phase10_config,
                engine_id=engine_id,
                engine_version=None,
                adapter_id="not-admitted",
                adapter_ref=phase10_config,
                runtime_id="not-installed",
                host_classes=["windows-primary"],
                headless=False,
                verification_state="CANDIDATE",
                validators=[
                    "advanced PDE use case and resource need required",
                    "isolated environment and license qualification required",
                    "positive and negative FEM fixtures required",
                ],
                evidence_refs=[phase10_config, phase10_evidence],
                fallbacks=[
                    {
                        "engine": "freecad-calculix-cli",
                        "runtime": "freecad-1.1:FEM+Gmsh+CalculiX",
                    }
                ],
                status="CANDIDATE",
                provider={
                    "version": None,
                    "license": licence,
                    "capabilities": [cap_id],
                },
                license_provenance=[phase10_config],
            )
        )

    records.append(
        make_record(
            record_id="optimization.auto_accept--blocked-phase10",
            capability_id="optimization.auto_accept",
            authority_id="fabrication-router",
            authority_ref=phase10_config,
            engine_id="not-admitted",
            engine_version=None,
            adapter_id="not-admitted",
            adapter_ref=phase10_config,
            runtime_id="not-admitted",
            host_classes=["windows-primary"],
            headless=False,
            verification_state="BLOCKED",
            validators=[
                "no auto-promotion from FEM output",
                "explicit independent structural engineering review required",
                "loads, materials, constraints, safety factors, fatigue and other applicable cases required",
            ],
            evidence_refs=[phase10_config, phase10_evidence],
            fallbacks=[],
            status="BLOCKED",
            provider=None,
            license_provenance=[phase10_config],
        )
    )

    # Phase 11: local DfAM / Orca proof. The canonical vf_cad.py and the
    # existing printer-specific slicer profiles remain the only execution
    # surfaces. This registry is non-authoritative and cannot start a printer.
    phase11_config = (
        "docs/implementation/ai-3d-modeling-engineering-core/"
        "dfam-slicer-v1.json"
    )
    phase11_evidence = (
        "docs/implementation/ai-3d-modeling-engineering-core/evidence/"
        "phase11-dfam-slicer-acceptance-20261008.json"
    )
    dfam_contract = load(repo_root / phase11_config)
    dfam_proof = load(repo_root / phase11_evidence)
    assert dfam_contract["schema"] == "velvetos.ai3d.dfam-slicer.v1"
    assert dfam_contract["non_authoritative_staging"] is True
    assert dfam_proof["status"] == "PASS_BOUNDED_OFFLINE"
    assert dfam_proof["native_profiles_unchanged"] is True
    assert dfam_proof["print_release"] == "NOT_AUTHORIZED"
    assert dfam_proof["quarantined_profiles"]["h2d"]["status"] == "BLOCKED_MOTION_BOUNDS"
    for kind in ("c5_stl", "c5_3mf"):
        assert dfam_proof["verified_offline"][kind]["validation_ok"] is True
        assert dfam_proof["verified_offline"][kind]["reported_layer_count"] > 0
    assert len(dfam_proof["negative_controls"]) >= 4

    phase11_rows = (
        ("print.prepare.dfam", "vf-cad-dfam", "1.0", "PROVEN", "PROVEN_PROVIDER", None),
        ("print.slice.orca_offline", "orcaslicer", "2.4.2", "PROVEN", "PROVEN_PROVIDER", "AGPL-3.0"),
        ("print.slice.h2d_motion_validation", "orcaslicer", "2.4.2", "BLOCKED", "BLOCKED", "AGPL-3.0"),
    )
    for cap_id, engine_id, version, status, verification, license_text in phase11_rows:
        entry = make_record(
            record_id=f"{cap_id}--phase11-vf-cad",
            capability_id=cap_id,
            authority_id="fabrication-router",
            authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
            engine_id=engine_id,
            engine_version=version,
            adapter_id="vf-cad-existing-bridge",
            adapter_ref="scripts/vf_cad.py",
            runtime_id=(
                "vf-cad:OrcaSlicer-2.4.2" if engine_id == "orcaslicer"
                else "vf-cad:dfam-check"
            ),
            host_classes=["windows-primary"],
            headless=True,
            verification_state=verification,
            validators=(
                ["validate_ai3d_phase11_dfam_slicer", "profile-motion-envelope-proof-required"]
                if status == "BLOCKED"
                else ["validate_ai3d_phase11_dfam_slicer", "native-profiles-unchanged"]
            ),
            evidence_refs=[phase11_config, phase11_evidence],
            fallbacks=[],
            status=status,
            provider={
                "version": version,
                "license": license_text,
                "capabilities": [cap_id],
            },
            license_provenance=[phase11_config, phase11_evidence],
        )
        if engine_id == "orcaslicer":
            entry["license_lane"] = "review-required"
            entry["license"]["code_license"] = "AGPL-3.0"
            entry["license"]["license_source"] = (
                "runtime:C:/Users/Chris/Documents/VelvetPrintLab/tools/"
                "OrcaSlicer-2.4.2/LICENSE.txt"
            )
            entry["license"]["bundle_policy"] = (
                "standalone existing local CLI only; no binary, code or hosted "
                "service integration into closed product without AGPL review"
            )
            entry["license"]["allowed_use"] = (
                "bounded offline generation/verification only; no printer control"
            )
        records.append(entry)

    research_candidates = [
        ("ai.image_to_3d", "hunyuan3d-2.1-shape", "ai-generation-local"),
        ("ai.image_to_3d", "triposg", "ai-generation-local"),
        ("ai.image_to_3d", "spar3d", "ai-generation-local"),
        ("reconstruction.geometry-evidence", "vggt-commercial-checkpoint", "reconstruction-local"),
        ("reconstruction.depth-evidence", "moge", "reconstruction-local"),
        ("ai.image_to_3d", "pixal3d", "ai-generation-local"),
    ]
    for capability, engine_id, runtime_id in research_candidates:
        records.append(
            make_record(
                record_id=f"{capability}--candidate-{engine_id}",
                capability_id=capability,
                authority_id="fabrication-router",
                authority_ref="packages/vfprod/FABRICATION-ROUTER.json",
                engine_id=engine_id,
                engine_version=None,
                adapter_id="not-admitted",
                adapter_ref="docs/implementation/ai-3d-modeling-engineering-core/phase1-overlap-gap-map-v0.json",
                runtime_id=runtime_id,
                host_classes=["windows-primary"],
                headless=True,
                verification_state="CANDIDATE",
                validators=["golden fixture required", "license qualification required", "resource qualification required"],
                evidence_refs=[RESEARCH_01, RESEARCH_02],
                fallbacks=[],
                status="CANDIDATE",
                provider=None,
                license_provenance=[RESEARCH_01, RESEARCH_02],
            )
        )

    records.sort(key=lambda row: (row["capability_id"], row["record_id"]))
    return {
        "schema": "velvetos.ai3d.cad-capability-registry.v1",
        "non_authoritative_staging": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority_invariant": (
            "This registry grants no authority. Fabrication Router/vf-3d-router, "
            "CreativeCraft, Blender Capability Host, slicer and production authorities remain unchanged."
        ),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--creative", type=Path, default=DEFAULT_CREATIVE)
    parser.add_argument("--blender", type=Path, default=DEFAULT_BLENDER)
    parser.add_argument("--stations", type=Path, default=DEFAULT_STATIONS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output = args.output or (
        repo_root
        / "docs"
        / "implementation"
        / "ai-3d-modeling-engineering-core"
        / "cad-capability-registry-v1.json"
    )
    registry = build(repo_root, args.creative, args.blender, args.stations)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(registry, indent=2) + "\n")
    states: dict[str, int] = {}
    for record in registry["records"]:
        states[record["status"]] = states.get(record["status"], 0) + 1
    print(f"build-ai3d-capability-registry: wrote {len(registry['records'])} records to {output}")
    print("status_counts=" + json.dumps(states, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
