#!/usr/bin/env python3
"""Generate Reform v2 Stage 8B canonical-instance-config acceptance evidence.

Stage 8B establishes canonical instance-owned values and generic Core contracts.
It does not migrate legacy readers; that belongs to Stage 8C.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
OUT = POLICY_DIR / "reports" / "stage8b-canonical-instance-config.json"
FOUNDATION = POLICY_DIR / "reports" / "stage8b-instance-resolver-foundation.json"
INVENTORY = POLICY_DIR / "reports" / "stage8a-core-instance-inventory.json"
POLICY = POLICY_DIR / "policy-registry.json"
CORE = ROOT / "packages" / "velvetos" / "CORE.json"
MANIFEST = ROOT / "instances" / "velvet-factory" / "INSTANCE.json"
PROFILE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
DESK = ROOT / "instances" / "velvet-factory" / ".cursor" / "vf-desk.json"
FLEET = ROOT / "instances" / "velvet-factory" / "instance" / "fleet.json"
LEGACY_FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
TOOL_CONTRACT = ROOT / "packages" / "velvetos" / "tool-status-contract.json"
TOOL_STATE = ROOT / "instances" / "velvet-factory" / "instance" / "tool-status.json"
LEGACY_TOOL_STATUS = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"
TOOL_RESOLVER = ROOT / "packages" / "velvetos" / "tool_status_resolver.py"

DIRECT_LEGACY_READERS = (
    "scripts/check-upstream-watch.py",
    "scripts/check-tool-authority.py",
    "scripts/check-vf-cad-stack.py",
    "scripts/check-vf-fabrication-router.py",
    "scripts/check-vfmcp.py",
    "scripts/vf_reel_candidates.py",
)
SENSITIVE_KEYS = {
    "token", "secret", "password", "apikey", "api_key", "access_token",
    "refresh_token", "client_secret", "private_key", "credential",
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


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must be a JSON object")
    return obj


def load_tool_resolver():
    spec = importlib.util.spec_from_file_location("stage8b_tool_status_resolver", TOOL_RESOLVER)
    require(spec is not None and spec.loader is not None, "cannot load tool-status resolver")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sensitive_key_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).casefold() in SENSITIVE_KEYS:
                found.append(path)
            found.extend(sensitive_key_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(sensitive_key_paths(child, f"{prefix}[{index}]"))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    foundation = load(FOUNDATION)
    inventory = load(INVENTORY)
    core = load(CORE)
    manifest = load(MANIFEST)
    profile = load(PROFILE)
    desk = load(DESK)
    fleet = load(FLEET)
    legacy_fleet = load(LEGACY_FLEET)
    contract = load(TOOL_CONTRACT)
    state = load(TOOL_STATE)
    legacy_tool = load(LEGACY_TOOL_STATUS)

    require(foundation.get("repository_acceptance") == "PASS",
            "Stage 8B resolver foundation is not PASS")
    require(inventory.get("repository_acceptance") == "PASS",
            "Stage 8A inventory is not PASS")

    waves = (inventory.get("summary") or {}).get("migration_waves") or {}
    expected_config_wave = {
        "canonical-instance-desk",
        "canonical-instance-profile",
        "tool-status-mixed-registry",
        "vfprod-fleet-registry",
    }
    expected_resolver_wave = {
        "core-reference-profile-metadata",
        "policy-registry-explicit-instance-pointers",
    }
    require(set(waves.get("8B_CANONICAL_INSTANCE_CONFIG") or []) == expected_config_wave,
            "Stage 8A canonical-config wave drift")
    require(set(waves.get("8B_RESOLVER_FOUNDATION") or []) == expected_resolver_wave,
            "Stage 8A resolver-foundation wave drift")

    surfaces = manifest.get("surfaces") or {}
    require(surfaces == {
        "profile": "instance/velvet-factory.json",
        "toolDesk": ".cursor/vf-desk.json",
        "fleet": "instance/fleet.json",
        "toolStatus": "instance/tool-status.json",
    }, "Velvet Factory canonical surface map drift")
    require(profile.get("id") == "velvet-factory", "canonical profile identity drift")
    require(desk.get("instanceId") == "velvet-factory", "canonical desk identity drift")

    fleet_parity = canonical_json_sha256(fleet) == canonical_json_sha256(legacy_fleet)
    require(fleet_parity, "canonical fleet differs from legacy compatibility fleet")

    require(contract.get("schema") == "velvetos.tool-status-contract.v1",
            "tool-status contract schema drift")
    require(contract.get("role") == "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM",
            "tool-status contract role drift")
    contract_text = json.dumps(contract, ensure_ascii=False).casefold()
    for forbidden in ("velvet-factory", "sderot", "velvets_cloud", "workers.dev"):
        require(forbidden not in contract_text, f"generic tool-status contract contains instance value: {forbidden}")
    require(set(state) == {"schema", "instanceId", "updated_at", "authority", "tools", "contract"},
            "instance tool-status must contain instance state only")
    require(state.get("instanceId") == "velvet-factory", "instance tool-status identity drift")
    require(not sensitive_key_paths(state), "instance tool-status contains secret-bearing key names")

    resolver = load_tool_resolver()
    composed = resolver.compose_tool_status(ROOT, instance_id="velvet-factory", env={})
    tool_parity = canonical_json_sha256(composed) == canonical_json_sha256(legacy_tool)
    require(tool_parity and composed == legacy_tool,
            "Core contract + instance tool state does not exactly compose legacy TOOL-STATUS")

    try:
        resolver.compose_tool_status(ROOT, env={})
    except resolver.ToolStatusResolutionError:
        missing_instance_fails_closed = True
    else:
        missing_instance_fails_closed = False
    require(missing_instance_fails_closed, "tool-status resolver silently selected a business instance")

    resolution = core.get("toolStatusResolution") or {}
    require(resolution == {
        "contract": "packages/velvetos/tool-status-contract.json",
        "resolver": "packages/velvetos/tool_status_resolver.py",
        "instanceSurface": "toolStatus",
        "legacyCompatibilityPath": "packages/velvetos/TOOL-STATUS.json",
        "consumerCutover": False,
        "silentBusinessDefaultForbidden": True,
    }, "Core tool-status resolution metadata drift")

    legacy_now = canonical_json_sha256(legacy_tool)
    legacy_base = canonical_json_sha256(
        git_json(args.prepared_against, "packages/velvetos/TOOL-STATUS.json")
    )
    require(legacy_now == legacy_base, "legacy TOOL-STATUS changed during placement split")

    reader_evidence: dict[str, dict[str, Any]] = {}
    for rel in DIRECT_LEGACY_READERS:
        current = (ROOT / rel).read_bytes()
        baseline = git_bytes(args.prepared_against, rel)
        reader_evidence[rel] = {
            "unchanged": current == baseline,
            "still_reads_legacy_composite": "TOOL-STATUS.json" in current.decode("utf-8", errors="ignore"),
        }
    require(all(row["unchanged"] and row["still_reads_legacy_composite"] for row in reader_evidence.values()),
            "a Stage 8C reader cutover leaked into Stage 8B")

    policy_now = canonical_json_sha256(load(POLICY))
    policy_base = canonical_json_sha256(
        git_json(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    )
    require(policy_now == policy_base, "external-effect policy registry changed in Stage 8B")

    config_items = {
        "canonical-instance-profile": {
            "path": PROFILE.relative_to(ROOT).as_posix(),
            "ready": profile.get("id") == "velvet-factory",
        },
        "canonical-instance-desk": {
            "path": DESK.relative_to(ROOT).as_posix(),
            "ready": desk.get("instanceId") == "velvet-factory",
        },
        "vfprod-fleet-registry": {
            "path": FLEET.relative_to(ROOT).as_posix(),
            "legacy": LEGACY_FLEET.relative_to(ROOT).as_posix(),
            "ready": fleet_parity,
        },
        "tool-status-mixed-registry": {
            "core_contract": TOOL_CONTRACT.relative_to(ROOT).as_posix(),
            "instance_state": TOOL_STATE.relative_to(ROOT).as_posix(),
            "legacy": LEGACY_TOOL_STATUS.relative_to(ROOT).as_posix(),
            "ready": tool_parity,
        },
    }

    criteria = {
        "all_stage8b_inventory_items_have_canonical_placement": all(row["ready"] for row in config_items.values()),
        "generic_core_tool_contract_has_no_vf_business_values": all(
            value not in contract_text for value in ("velvet-factory", "sderot", "velvets_cloud", "workers.dev")
        ),
        "instance_tool_state_contains_tools_not_generic_rules": "rules" not in state and isinstance(state.get("tools"), dict),
        "tool_status_split_exactly_composes_legacy_compatibility_document": tool_parity,
        "tool_status_resolution_requires_explicit_instance_from_core": missing_instance_fails_closed,
        "fleet_canonical_copy_remains_exactly_equal_to_legacy": fleet_parity,
        "all_known_direct_legacy_readers_are_unchanged_and_still_on_compatibility_surface": all(
            row["unchanged"] and row["still_reads_legacy_composite"] for row in reader_evidence.values()
        ),
        "resolver_foundation_is_passed_and_bound": foundation.get("repository_acceptance") == "PASS",
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
        "no_legacy_path_delete_or_consumer_cutover_in_stage8b": (
            LEGACY_TOOL_STATUS.is_file()
            and LEGACY_FLEET.is_file()
            and resolution.get("consumerCutover") is False
        ),
    }

    report = {
        "schema": "velvetos.stage8b-canonical-instance-config.v1",
        "stage": "8B",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Close canonical instance placement before Stage 8C reader migration; preserve compatibility composites and authority semantics.",
        "inventory_binding": {
            "stage8a_path": INVENTORY.relative_to(ROOT).as_posix(),
            "canonical_config_items": sorted(expected_config_wave),
            "resolver_foundation_items": sorted(expected_resolver_wave),
        },
        "resolver_foundation": {
            "path": FOUNDATION.relative_to(ROOT).as_posix(),
            "repository_acceptance": foundation.get("repository_acceptance"),
        },
        "canonical_instance_surfaces": surfaces,
        "canonical_config_items": config_items,
        "tool_status_split": {
            "core_contract": TOOL_CONTRACT.relative_to(ROOT).as_posix(),
            "instance_state": TOOL_STATE.relative_to(ROOT).as_posix(),
            "legacy_composite": LEGACY_TOOL_STATUS.relative_to(ROOT).as_posix(),
            "tool_count": len(state.get("tools") or {}),
            "exact_composition_parity": tool_parity,
            "legacy_composite_unchanged_from_prepared_against": legacy_now == legacy_base,
            "consumer_cutover": False,
            "sensitive_key_paths": sensitive_key_paths(state),
        },
        "legacy_reader_evidence": reader_evidence,
        "authority_baseline": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "unchanged": policy_now == policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 8C — Consumer Migration" if all(criteria.values()) else None,
        "stage8c_constraints": [
            "migrate readers domain-by-domain through generic resolvers",
            "prove semantic parity before each consumer cutover",
            "keep legacy compatibility files through a rollback window",
            "retire legacy only after clean consumer scan",
            "Control API and Living Studio remain projections, never source of truth",
            "no external-effect authority change",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8B_CANONICAL_INSTANCE_CONFIG "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"tools={len(state.get('tools') or {})} readers={len(reader_evidence)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
