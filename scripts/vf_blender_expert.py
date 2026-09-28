#!/usr/bin/env python3
"""Provider-neutral expert planning for the existing VelvetOS Blender route.

This module embeds reusable workflow knowledge distilled from the MIT-licensed
scenario-labs/skills expert tools. It never calls Scenario, never selects a paid
provider, and never controls a physical printer. Execution remains owned by
vf_3d.py + the existing local Blender/design-os stack.
"""
from __future__ import annotations

import argparse
import json
import re

UPSTREAM = {
    "repository": "https://github.com/scenario-labs/skills",
    "release": "skills-v0.48.0",
    "commit": "9624e295fa33168bc1be22a628c23ba132d1c959",
    "license": "MIT",
    "runtime_dependency": "NONE",
    "scenario_mcp_required": False,
}

VENDOR_ROOT = "packages/vfprod/third_party/scenario-labs/blender"

DOMAINS = {
    "expert_protocol": {
        "headless": True,
        "purpose": "brief -> staged build -> measurable gate + review sheet -> repair -> evidence",
        "helpers": [
            f"{VENDOR_ROOT}/scenario-blender-expert/scripts/bx_audit.py",
            f"{VENDOR_ROOT}/scenario-blender-expert/scripts/bx_review.py",
            f"{VENDOR_ROOT}/scenario-blender-expert/scripts/bx_gui.py",
        ],
    },
    "hard_surface": {"headless": True, "purpose": "mechanical-looking mesh form, booleans, bevels, shading audit", "helpers": [f"{VENDOR_ROOT}/scenario-blender-hard-surface/scripts/bx_hardsurface.py"]},
    "sculpting": {"headless": "partial", "purpose": "organic blockout and form; real brush strokes need a live GUI", "helpers": [f"{VENDOR_ROOT}/scenario-blender-sculpting/scripts/bx_sculpt.py"]},
    "retopology": {"headless": True, "purpose": "clean topology, low-poly/game/animation cage, fidelity audit", "helpers": [f"{VENDOR_ROOT}/scenario-blender-retopology/scripts/bx_retopo.py"]},
    "uv_baking": {"headless": True, "purpose": "UVs, texel density, baking, projection/bake QA", "helpers": [f"{VENDOR_ROOT}/scenario-blender-uv-baking/scripts/bx_uvbake.py"]},
    "texturing_shading": {"headless": True, "purpose": "materials and texture/shading setup", "helpers": [f"{VENDOR_ROOT}/scenario-blender-texturing-shading/scripts/bx_materials.py"]},
    "lighting_rendering": {"headless": True, "purpose": "lighting, render, value/color analysis, review renders", "helpers": [f"{VENDOR_ROOT}/scenario-blender-lighting-rendering/scripts/bx_light.py"]},
    "geometry_nodes": {"headless": True, "purpose": "procedural geometry and repeatable node workflows", "helpers": [f"{VENDOR_ROOT}/scenario-blender-geometry-nodes/scripts/bx_gn.py"]},
    "rigging": {"headless": True, "purpose": "rigging, weights/deformation tests where scriptable", "helpers": [f"{VENDOR_ROOT}/scenario-blender-rigging/scripts/bx_rig.py"]},
    "animation": {"headless": True, "purpose": "keyed animation, motion checks and render evidence", "helpers": [f"{VENDOR_ROOT}/scenario-blender-animation/scripts/bx_anim.py"]},
    "previs_storyboard": {"headless": True, "purpose": "camera/shot blocking and deterministic previews", "helpers": [f"{VENDOR_ROOT}/scenario-blender-previs-storyboard/scripts/bx_previs.py"]},
    "hair": {"headless": "partial", "purpose": "hair setup; some curve grooming strokes require live GUI", "helpers": [f"{VENDOR_ROOT}/scenario-blender-hair/scripts/bx_hair.py"]},
    "grease_pencil": {"headless": "partial", "purpose": "Grease Pencil setup; freehand draw strokes require live GUI", "helpers": [f"{VENDOR_ROOT}/scenario-blender-grease-pencil/scripts/bx_gp.py"]},
}

PRINT_GATES = [
    "real_units_and_dimensions_recorded",
    "manifold_and_boundary_audit",
    "self_intersection_and_duplicate_geometry_audit",
    "minimum_feature_and_wall_thickness_checked_against_process_profile",
    "mating_clearance_checked_against_process_profile_when_applicable",
    "build_volume_and_part_split_review",
    "hollowing_drain_and_trapped_volume_review_when_resin_and_requested",
    "export_units_and_part_names_verified",
    "stl_or_3mf_sidecars_materialized",
    "existing_slicer_dry_run_completed",
]

BASE_GATES = [
    "numeric_brief_or_unknowns_recorded",
    "source_or_reference_lock_recorded",
    "stage_measurements_checked",
    "multi_view_review_sheet_inspected",
    "failed_regions_repaired_before_next_stage",
    "final_geometry_audit_recorded",
]

KEYWORDS = {
    "hard_surface": ("hard surface", "panel", "vent", "boolean", "bevel", "mechanical shell", "מכני", "פאנל", "פתח"),
    "sculpting": ("sculpt", "organic", "figurine", "statue", "creature", "character", "פסל", "פסלון", "דמות", "אורגני"),
    "retopology": ("retopo", "retopology", "remesh", "low poly", "low-poly", "clean topology", "טופולוג", "ריטופו"),
    "uv_baking": ("uv", "unwrap", "bake", "normal map", "ao map", "texture bake"),
    "texturing_shading": ("texture", "material", "shader", "pbr", "טקסטורה", "חומר", "שיידר"),
    "lighting_rendering": ("render", "lighting", "light", "studio shot", "רנדר", "תאורה"),
    "geometry_nodes": ("geometry nodes", "procedural", "node geometry", "גאומטרי נוד", "פרוצדור"),
    "rigging": ("rig", "rigging", "skeleton", "armature", "ריג", "שלד"),
    "animation": ("animate", "animation", "walk cycle", "motion", "אנימצ"),
    "previs_storyboard": ("previs", "storyboard", "shot list", "camera block", "סטוריבורד"),
    "hair": ("hair", "fur", "groom", "שיער", "פרווה"),
    "grease_pencil": ("grease pencil", "2d draw", "story sketch"),
}

PRINT_TERMS = (
    "print", "3d print", "stl", "3mf", "slicer", "fdm", "resin", "sla", "msla",
    "הדפס", "מדפסת", "סלייס", "שרף",
)


def _matches(text: str, terms: tuple[str, ...]) -> bool:
    value = text.casefold()
    return any(term.casefold() in value for term in terms)


def classify(request: str) -> list[str]:
    chosen: list[str] = []
    for name, terms in KEYWORDS.items():
        if _matches(request, terms):
            chosen.append(name)

    if _matches(request, ("bracket", "enclosure", "case", "housing", "תושבת", "מארז")):
        if "hard_surface" not in chosen:
            chosen.append("hard_surface")

    if re.search(r"\b(stl|obj|glb|gltf|mesh|ai[- ]?mesh)\b|מודל קיים|רשת", request, re.I):
        if "retopology" not in chosen:
            chosen.append("retopology")

    if not chosen:
        chosen.append("sculpting")

    order = list(KEYWORDS)
    return sorted(set(chosen), key=lambda item: order.index(item))


def build_plan(request: str) -> dict:
    domains = classify(request)
    printable = _matches(request, PRINT_TERMS)
    gates = list(BASE_GATES)
    if printable:
        gates.extend(PRINT_GATES)
    return {
        "status": "PLANNED",
        "authority": "existing_vf_3d_route",
        "request": request,
        "expert_domains": ["expert_protocol", *domains],
        "execution_policy": {
            "prefer_headless_for": [d for d in domains if DOMAINS[d]["headless"] is True],
            "live_gui_may_be_required_for": [d for d in domains if DOMAINS[d]["headless"] == "partial"],
            "version_policy": "detect installed runtime; gate by capability; version is provenance only",
            "external_generation": "existing approved provider only; 3D AI Studio may supply a candidate mesh",
            "scenario_cloud_runtime": False,
            "physical_printer_control": False,
        },
        "gates": gates,
        "expert_helpers": {
            name: DOMAINS[name].get("helpers", [])
            for name in ["expert_protocol", *domains]
        },
        "helper_execution": "copy/adapt the selected helper logic into the job script and execute through vf_3d.py run-pass; helper presence is not host readiness",
        "handoff": {
            "editable_master": "BLEND unless vf_3d route requires STEP + BLEND hybrid",
            "print_sidecars": ["STL", "3MF"] if printable else [],
            "evidence": ["geometry audit", "review renders", "source/license provenance"]
            + (["slicer dry-run"] if printable else []),
        },
        "upstream_provenance": UPSTREAM,
    }


def capabilities() -> dict:
    return {
        "status": "CAPABILITY_CATALOG",
        "domain_count": len(DOMAINS),
        "domains": DOMAINS,
        "print_gates": PRINT_GATES,
        "upstream_provenance": UPSTREAM,
        "notes": [
            "This catalog is planning/QA knowledge, not proof that a local DCC is installed.",
            "Host readiness is established by the existing vf_3d.py doctor/benchmark path.",
            "Scenario MCP, Scenario credits, Scenario asset storage and Scenario Quality Gate are not dependencies.",
        ],
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    plan = sub.add_parser("plan")
    plan.add_argument("--request", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    result = capabilities() if args.command == "capabilities" else build_plan(args.request)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
