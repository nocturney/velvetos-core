#!/usr/bin/env python3
"""Generate Reform v2 Stage 8C Living Studio business-rule projection evidence.

Removes embedded Velvet Factory values from AUTONOMY.json while preserving the
legacy rule shape exactly through read-only instance resolution. No action
engine, control-plane authority, store, queue, or external-effect policy changes.
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
OUT = POLICY_DIR / "reports" / "stage8c-living-studio-rules.json"
INVENTORY = POLICY_DIR / "reports" / "stage8a-core-instance-inventory.json"
POLICY = POLICY_DIR / "policy-registry.json"
AUTONOMY = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
RESOLVER = ROOT / "packages" / "velvetos" / "living_studio_rules.py"
PROFILE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
ACTION_ENGINE_REL = "scripts/vf_autonomy.py"
CONTROL_PLANE_REL = "office/control-plane.json"
AUTONOMY_REL = "packages/velvetos/living-studio/AUTONOMY.json"

EXPECTED_RESOLUTION = {
    "resolver": "packages/velvetos/living_studio_rules.py",
    "instanceSurface": "profile",
    "instanceIdEnvironment": "VELVETOS_INSTANCE_ID",
    "requireExplicitInstanceIdWhenRunningFromCore": True,
    "projectionOnly": True,
    "legacyShape": "businessRules",
    "sourceOfTruth": "selected instance profile + generic safety semantics",
}


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
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
        raise SystemExit(f"{rel}@{sha} must contain a JSON object")
    return obj


def load_resolver():
    spec = importlib.util.spec_from_file_location("stage8c_living_studio_rules", RESOLVER)
    require(spec is not None and spec.loader is not None, "cannot load Living Studio rule resolver")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    inventory = load(INVENTORY)
    require(inventory.get("repository_acceptance") == "PASS", "Stage 8A inventory is not PASS")
    wave = ((inventory.get("summary") or {}).get("migration_waves") or {}).get("8C_CONSUMER_MIGRATION") or []
    require("living-studio-embedded-business-rules" in wave,
            "Stage 8A no longer assigns Living Studio embedded business rules to Stage 8C")

    cfg = load(AUTONOMY)
    require("businessRules" not in cfg, "AUTONOMY still embeds businessRules values")
    require(cfg.get("businessRulesResolution") == EXPECTED_RESOLUTION,
            "AUTONOMY businessRulesResolution contract drift")

    baseline_cfg = git_json(args.prepared_against, AUTONOMY_REL)
    baseline_rules = baseline_cfg.get("businessRules")
    require(isinstance(baseline_rules, dict) and len(baseline_rules) == 7,
            "prepared-against AUTONOMY businessRules baseline missing")

    resolver = load_resolver()
    effective = resolver.effective_business_rules(ROOT, instance_id="velvet-factory", env={})
    require(effective == baseline_rules,
            "instance-resolved Living Studio business rules differ from pre-cutover legacy rules")

    try:
        resolver.effective_business_rules(ROOT, env={})
    except resolver.LivingStudioRuleResolutionError:
        missing_instance_rejected = True
    else:
        missing_instance_rejected = False
    require(missing_instance_rejected, "Living Studio rule resolver silently selected a business instance")

    resolver_text = RESOLVER.read_text(encoding="utf-8").casefold()
    cfg_text = AUTONOMY.read_text(encoding="utf-8").casefold()
    for forbidden in ("velvet-factory", "sderot", "@velvets_cloud", "050-2517000"):
        require(forbidden not in resolver_text, f"generic Living Studio resolver embeds VF value: {forbidden}")
        require(forbidden not in cfg_text, f"AUTONOMY config embeds VF value: {forbidden}")

    profile = load(PROFILE)
    fulfillment = profile.get("fulfillment") or {}
    compliance = profile.get("compliance") or {}
    whatsapp = ((profile.get("mcpBind") or {}).get("whatsapp") or {})
    projection_sources = {
        "pickupOnly": "profile.where when fulfillment.mode=pickup",
        "nationwideShipping": "profile.fulfillment.nationalShipping",
        "publicCTA": "profile.cta.channel projected to legacy label",
        "customerWhatsAppSend": "profile.mcpBind.whatsapp.send projected to human/tool",
        "inventSaleILS": "inverse profile.compliance.noInventedPrices",
        "inventInsights": "inverse profile.compliance.noInventedInsights",
        "destructiveAutonomy": "generic Core safety invariant false",
    }
    require(effective.get("pickupOnly") == (
                profile.get("where") if fulfillment.get("mode") == "pickup" else None
            ),
            "pickup projection source drift")
    require(effective.get("nationwideShipping") == fulfillment.get("nationalShipping"),
            "shipping projection source drift")
    require(effective.get("customerWhatsAppSend") == (
                "tool" if whatsapp.get("send") is True else "human"
            ),
            "customer send projection source drift")
    require(effective.get("inventSaleILS") == (not bool(compliance.get("noInventedPrices"))),
            "price invention projection source drift")
    require(effective.get("inventInsights") == (not bool(compliance.get("noInventedInsights"))),
            "Insights invention projection source drift")
    require(effective.get("destructiveAutonomy") is False,
            "destructive autonomy generic safety invariant drift")

    action_engine_unchanged = (ROOT / ACTION_ENGINE_REL).read_bytes() == git_bytes(
        args.prepared_against, ACTION_ENGINE_REL
    )
    control_plane_unchanged = (ROOT / CONTROL_PLANE_REL).read_bytes() == git_bytes(
        args.prepared_against, CONTROL_PLANE_REL
    )
    require(action_engine_unchanged, "vf_autonomy action engine changed in projection-only slice")
    require(control_plane_unchanged, "office control plane changed in projection-only slice")

    policy_now = canonical_json_sha256(load(POLICY))
    policy_base = canonical_json_sha256(
        git_json(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    )
    require(policy_now == policy_base, "external-effect policy registry changed")

    criteria = {
        "stage8a_living_studio_debt_is_bound_to_this_slice": (
            "living-studio-embedded-business-rules" in wave
        ),
        "autonomy_config_contains_resolution_contract_not_vf_business_values": (
            "businessRules" not in cfg and cfg.get("businessRulesResolution") == EXPECTED_RESOLUTION
        ),
        "effective_business_rules_exactly_match_pre_cutover_legacy_shape_and_values": (
            effective == baseline_rules
        ),
        "effective_business_rules_derive_instance_values_from_canonical_profile": (
            effective.get("pickupOnly") == (
                profile.get("where") if fulfillment.get("mode") == "pickup" else None
            )
            and effective.get("nationwideShipping") == fulfillment.get("nationalShipping")
        ),
        "generic_living_studio_resolver_has_no_vf_business_default_or_values": all(
            value not in resolver_text
            for value in ("velvet-factory", "sderot", "@velvets_cloud", "050-2517000")
        ),
        "core_checkout_requires_explicit_instance_for_business_rule_projection": missing_instance_rejected,
        "vf_autonomy_action_engine_is_byte_unchanged": action_engine_unchanged,
        "office_control_plane_is_byte_unchanged": control_plane_unchanged,
        "no_new_store_queue_or_canonical_write_is_introduced": (
            cfg.get("businessRulesResolution", {}).get("projectionOnly") is True
        ),
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8c-living-studio-rules.v1",
        "stage": "8C_LIVING_STUDIO_RULES",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Remove embedded VF business values from Living Studio AUTONOMY config and resolve an exact legacy-compatible projection from canonical instance config.",
        "inventory_binding": {
            "surface_id": "living-studio-embedded-business-rules",
            "wave": "8C_CONSUMER_MIGRATION",
        },
        "configuration": {
            "path": AUTONOMY_REL,
            "embedded_business_rules_removed": "businessRules" not in cfg,
            "resolution": cfg.get("businessRulesResolution"),
        },
        "legacy_parity": {
            "prepared_against_rules": baseline_rules,
            "effective_rules": effective,
            "exact": effective == baseline_rules,
        },
        "projection_sources": projection_sources,
        "runtime_isolation": {
            "vf_autonomy_byte_unchanged": action_engine_unchanged,
            "office_control_plane_byte_unchanged": control_plane_unchanged,
            "projection_only": True,
            "new_store": False,
            "new_queue": False,
        },
        "authority_baseline": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "unchanged": policy_now == policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 8C — Remaining consumer domains" if all(criteria.values()) else None,
        "next_domains": [
            "root-vf-desk-reference-bind",
            "control-api-instance-and-fleet-resolution",
            "chatgpt-project-vf-distribution",
            "expert-modules-with-vf-values",
            "windows-host-binding-document",
        ],
        "constraints": [
            "Living Studio remains a projection/router, never source of truth",
            "no external-effect authority change",
            "no new runtime, queue, database or store",
            "remaining domains migrate independently with parity proof and rollback window",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8C_LIVING_STUDIO_RULES "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"legacy_parity={str(effective == baseline_rules).lower()}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
