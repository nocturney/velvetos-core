#!/usr/bin/env python3
"""Generate Reform v2 Stage 8B resolver-foundation acceptance evidence.

This slice establishes a generic fail-closed instance resolver and a canonical
Velvet Factory fleet surface while keeping all legacy consumers in place.
It does not cut over Control API/Living Studio/vfprod/root-desk readers and
does not retire compatibility files.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage8b-instance-resolver-foundation.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
CORE = ROOT / "packages" / "velvetos" / "CORE.json"
RESOLVER = ROOT / "packages" / "velvetos" / "instance_resolver.py"
SCHEMA = ROOT / "packages" / "velvetos" / "schema" / "instance-manifest.schema.json"
VF_ROOT = ROOT / "instances" / "velvet-factory"
VF_MANIFEST = VF_ROOT / "INSTANCE.json"
VF_FLEET = VF_ROOT / "instance" / "fleet.json"
LEGACY_FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
LEGACY_SAMPLE = ROOT / "packages" / "velvetos" / "samples" / "velvet-factory.json"
LEGACY_AUTONOMY = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
ROOT_DESK = ROOT / ".cursor" / "vf-desk.json"

LEGACY_JSON_PATHS = {
    "fleet": "packages/vfprod/FLEET.json",
    "sample": "packages/velvetos/samples/velvet-factory.json",
    "autonomy": "packages/velvetos/living-studio/AUTONOMY.json",
    "root_desk": ".cursor/vf-desk.json",
    "policy_registry": "packages/velvetos/policy/policy-registry.json",
}


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must be a JSON object")
    return obj


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def canonical_json_sha256(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_json(sha: str, rel: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)
    obj = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must be a JSON object")
    return obj


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"],
        cwd=ROOT,
        capture_output=True,
    ).returncode == 0


def receipt_source_commit() -> str:
    rel = OUT.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    require(bool(commits), "cannot resolve Stage 8B resolver-foundation source commit")
    return commits[-1]


def load_resolver(sha: str):
    rel = RESOLVER.relative_to(ROOT).as_posix()
    source = git_bytes(sha, rel).decode("utf-8-sig")
    name = "stage8b_instance_resolver_snapshot"
    module = types.ModuleType(name)
    module.__file__ = f"{rel}@{sha}"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module, source


def snapshot_resolution_proof(resolver, manifest: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        fake_core = Path(td)
        inst = fake_core / "instances" / "velvet-factory"
        inst.mkdir(parents=True)
        (inst / "INSTANCE.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
        for rel in (manifest.get("surfaces") or {}).values():
            path = inst / str(rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")

        explicit = resolver.resolve_instance(fake_core, instance_id="velvet-factory", env={})
        require(explicit.mode == "core-explicit-instance", "explicit Core resolution mode drift")
        require(explicit.instance_root == inst.resolve(), "explicit VF root resolution drift")
        require(explicit.surface("fleet") == (inst / "instance/fleet.json").resolve(),
                "VF fleet surface resolution drift")

        via_env = resolver.resolve_instance(fake_core, env={"VELVETOS_INSTANCE_ID": "velvet-factory"})
        require(via_env.instance_id == "velvet-factory", "environment instance resolution drift")
        current = resolver.resolve_instance(inst, env={})
        require(current.mode == "current-instance-workspace", "current instance workspace mode drift")

        try:
            resolver.resolve_instance(fake_core, env={})
        except resolver.InstanceResolutionError:
            missing_id_rejected = True
        else:
            missing_id_rejected = False
        require(missing_id_rejected, "Core resolver silently selected a business instance")
        return {"core_mode": explicit.mode, "missing_id_rejected": missing_id_rejected}


def generic_fixture_proof(resolver) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        fake_core = Path(td)
        inst = fake_core / "instances" / "fixture"
        inst.mkdir(parents=True)
        (inst / "profile.json").write_text("{}\n", encoding="utf-8")
        manifest = {
            "product": "VelvetOS",
            "role": "instance",
            "displayName": "Fixture Instance",
            "instanceId": "fixture",
            "profile": "profile.json",
            "surfaceContractVersion": 1,
            "surfaces": {"profile": "profile.json"},
            "core": {
                "github": "example/core",
                "vendorPath": "vendor/core",
                "attach": "scripts/attach-core.sh",
            },
        }
        (inst / "INSTANCE.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        resolved = resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        require(resolved.instance_id == "fixture", "generic fixture instance id mismatch")
        require(resolved.mode == "core-explicit-instance", "generic fixture mode mismatch")
        require(set(resolved.surfaces) == {"profile"}, "generic resolver requires a domain-specific surface")

        bad = dict(manifest)
        bad["surfaceContractVersion"] = 2
        (inst / "INSTANCE.json").write_text(json.dumps(bad) + "\n", encoding="utf-8")
        try:
            resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        except resolver.InstanceResolutionError:
            bad_version_rejected = True
        else:
            bad_version_rejected = False

        outside = fake_core / "outside.json"
        outside.write_text("{}\n", encoding="utf-8")
        traversal = dict(manifest)
        traversal["surfaces"] = {"profile": "profile.json", "escape": "../../outside.json"}
        (inst / "INSTANCE.json").write_text(json.dumps(traversal) + "\n", encoding="utf-8")
        try:
            resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        except resolver.InstanceResolutionError:
            traversal_rejected = True
        else:
            traversal_rejected = False

        return {
            "instance_id": resolved.instance_id,
            "mode": resolved.mode,
            "surfaces": sorted(resolved.surfaces),
            "bad_surface_contract_version_rejected": bad_version_rejected,
            "parent_traversal_rejected": traversal_rejected,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    source_commit = receipt_source_commit()
    core = git_json(source_commit, CORE.relative_to(ROOT).as_posix())
    manifest = git_json(source_commit, VF_MANIFEST.relative_to(ROOT).as_posix())
    schema = git_json(source_commit, SCHEMA.relative_to(ROOT).as_posix())
    fleet = git_json(source_commit, VF_FLEET.relative_to(ROOT).as_posix())
    legacy_fleet = git_json(source_commit, LEGACY_FLEET.relative_to(ROOT).as_posix())
    resolver, resolver_source = load_resolver(source_commit)
    resolution_proof = snapshot_resolution_proof(resolver, manifest)

    require("velvet-factory" not in resolver_source.lower(),
            "generic resolver contains Velvet Factory default")
    require("sderot" not in resolver_source.lower(),
            "generic resolver contains VF location default")

    resolution = core.get("instanceResolution") or {}
    require(resolution.get("resolver") == "packages/velvetos/instance_resolver.py",
            "Core resolver binding drift")
    require(resolution.get("instanceIdEnvironment") == "VELVETOS_INSTANCE_ID",
            "Core instance-id environment drift")
    require(resolution.get("requireExplicitInstanceIdWhenRunningFromCore") is True,
            "Core must require explicit instance id")
    require(resolution.get("silentBusinessDefaultForbidden") is True,
            "Core must forbid silent business defaults")

    required = set(schema.get("required") or [])
    require(required == {
        "product", "role", "displayName", "instanceId", "profile",
        "surfaceContractVersion", "surfaces", "core"
    }, "instance manifest schema required fields drift")
    surface_schema = ((schema.get("properties") or {}).get("surfaces") or {})
    require(surface_schema.get("required") == ["profile"],
            "generic instance schema must require profile only")
    require(set(((surface_schema.get("properties") or {}).keys())) >= {"profile", "toolDesk", "fleet"},
            "instance schema surface vocabulary drift")

    vf_surfaces = manifest.get("surfaces") or {}
    require(manifest.get("surfaceContractVersion") == 1, "VF surface contract version drift")
    require(vf_surfaces == {
        "profile": "instance/velvet-factory.json",
        "toolDesk": ".cursor/vf-desk.json",
        "fleet": "instance/fleet.json",
    }, "VF surface map drift")
    require(manifest.get("profile") == vf_surfaces.get("profile"),
            "VF legacy profile alias must match surfaces.profile")

    missing_id_rejected = bool(resolution_proof["missing_id_rejected"])
    fixture = generic_fixture_proof(resolver)
    require(fixture["bad_surface_contract_version_rejected"] is True,
            "generic resolver accepted unsupported surface contract version")
    require(fixture["parent_traversal_rejected"] is True,
            "generic resolver accepted parent traversal")

    fleet_parity = canonical_json_sha256(fleet) == canonical_json_sha256(legacy_fleet)
    require(fleet_parity, "canonical instance fleet is not parity-equal to legacy vfprod fleet")
    require(len(fleet.get("printers") or []) == 4, "VF canonical fleet printer count drift")

    legacy_unchanged: dict[str, bool] = {}
    for name, rel in LEGACY_JSON_PATHS.items():
        source_obj = git_json(source_commit, rel)
        baseline_obj = git_json(args.prepared_against, rel)
        legacy_unchanged[name] = canonical_json_sha256(source_obj) == canonical_json_sha256(baseline_obj)
    require(all(legacy_unchanged.values()), "8B resolver foundation changed a legacy consumer/authority source")

    criteria = {
        "generic_resolver_has_no_vf_business_default": (
            "velvet-factory" not in resolver_source.lower()
            and "sderot" not in resolver_source.lower()
        ),
        "core_requires_explicit_instance_selection": missing_id_rejected,
        "modern_manifest_contract_is_fail_closed": (
            fixture["bad_surface_contract_version_rejected"] is True
            and fixture["parent_traversal_rejected"] is True
        ),
        "generic_instance_does_not_require_fleet_or_vf_surfaces": fixture["surfaces"] == ["profile"],
        "vf_manifest_declares_profile_tooldesk_and_fleet_surfaces": set(vf_surfaces) == {"profile", "toolDesk", "fleet"},
        "canonical_instance_fleet_matches_legacy_fleet": fleet_parity,
        "legacy_consumers_and_external_effect_policy_are_unchanged": all(legacy_unchanged.values()),
        "no_legacy_path_is_deleted_in_resolver_foundation": all(git_exists(source_commit, rel) for rel in LEGACY_JSON_PATHS.values()),
        "consumer_cutover_is_deferred_until_parity_migration": True,
    }

    report = {
        "schema": "velvetos.stage8b-instance-resolver-foundation.v1",
        "stage": "8B_RESOLVER_FOUNDATION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Add generic fail-closed instance/surface resolution and canonical VF fleet placement without cutting over legacy consumers.",
        "resolver": {
            "path": RESOLVER.relative_to(ROOT).as_posix(),
            "core_mode": resolution_proof["core_mode"],
            "environment_variable": "VELVETOS_INSTANCE_ID",
            "silent_business_default": False,
            "generic_fixture": fixture,
        },
        "manifest_contract": {
            "schema": SCHEMA.relative_to(ROOT).as_posix(),
            "surface_contract_version": manifest.get("surfaceContractVersion"),
            "generic_required_surfaces": surface_schema.get("required"),
            "vf_surfaces": vf_surfaces,
        },
        "fleet": {
            "canonical_instance_path": VF_FLEET.relative_to(ROOT).as_posix(),
            "legacy_compatibility_path": LEGACY_FLEET.relative_to(ROOT).as_posix(),
            "canonical_json_sha256": canonical_json_sha256(fleet),
            "legacy_json_sha256": canonical_json_sha256(legacy_fleet),
            "parity": fleet_parity,
            "printer_count": len(fleet.get("printers") or []),
            "consumer_cutover": False,
        },
        "legacy_baseline": {
            "unchanged": legacy_unchanged,
            "all_unchanged": all(legacy_unchanged.values()),
            "legacy_delete_authorized": False,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 8B — Canonical Instance Config continuation" if all(criteria.values()) else None,
        "constraints": [
            "no Control API/Living Studio/vfprod/root-desk consumer cutover in this slice",
            "no legacy delete",
            "no external-effect authority change",
            "generic Core cannot silently assume Velvet Factory",
            "continue instance-owned tool/runtime bindings before Stage 8C consumer migration",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8B_INSTANCE_RESOLVER_FOUNDATION "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"fleet_parity={str(fleet_parity).lower()} generic_surfaces={','.join(fixture['surfaces'])}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
