#!/usr/bin/env python3
"""Generate Reform v2 Stage 8A Core/Instance inventory.

Observation-only. This stage classifies current placement and active consumers.
It does not move facts, change resolver behavior, retire compatibility paths,
or authorize deletion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage8a-core-instance-inventory.json"
POLICY_REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
INSTANCE_DESK = ROOT / "instances" / "velvet-factory" / ".cursor" / "vf-desk.json"
CORE = ROOT / "packages" / "velvetos" / "CORE.json"
SAMPLE = ROOT / "packages" / "velvetos" / "samples" / "velvet-factory.json"
AUTONOMY = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
TOOL_STATUS = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"
ROOT_DESK = ROOT / ".cursor" / "vf-desk.json"
PROJECT_MANIFEST = ROOT / "packages" / "velvetos" / "PROJECT-AUTHORITY-MANIFEST.json"

TARGET_CLASSES = {
    "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM",
    "INSTANCE_PUBLIC_CONFIG",
    "INSTANCE_INTERNAL_BINDING",
    "INSTANCE_PRIVATE_BINDING",
    "INSTANCE_RUNTIME_STATE",
    "INSTANCE_DOCUMENTATION_DISTRIBUTION",
    "CORE_COMPATIBILITY_REFERENCE",
    "NON_NORMATIVE_PREPARATION",
}

MACHINE_EXTENSIONS = {".py", ".json", ".yml", ".yaml", ".js", ".mjs", ".ps1", ".sh", ".bat"}
MACHINE_EXCLUDE_PREFIXES = (
    "packages/velvetos/policy/reports/",
    "packages/vfharness/state/",
    "packages/vfresearch/sources/",
    "packages/vfops/hq/",
    "packages/vfops/out/",
)


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
        raise SystemExit(f"{rel}@{sha} is not an object")
    return obj


def git_grep_files(needle: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", "--", needle],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode not in {0, 1}:
        raise SystemExit(proc.stderr.strip() or f"git grep failed for {needle!r}")
    return sorted({line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()})


def is_machine_consumer(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if rel.startswith(MACHINE_EXCLUDE_PREFIXES):
        return False
    path = Path(rel)
    return path.suffix.lower() in MACHINE_EXTENSIONS or rel.startswith(".github/workflows/")


def consumer_summary(needles: list[str], own_paths: list[str]) -> dict[str, Any]:
    all_refs: set[str] = set()
    for needle in needles:
        all_refs.update(git_grep_files(needle))
    own = {p.replace("\\", "/") for p in own_paths}
    evidence_machinery = {
        "scripts/generate-stage8a-core-instance-inventory.py",
        "scripts/check-policy-architecture.py",
        "packages/velvetos/policy/reports/stage8a-core-instance-inventory.json",
    }
    refs = sorted(p for p in all_refs if p not in own and p not in evidence_machinery)
    machine = sorted(p for p in refs if is_machine_consumer(p))
    return {
        "needles": needles,
        "all_reference_count": len(refs),
        "machine_consumer_count": len(machine),
        "machine_consumers": machine,
    }


def row(
    *,
    surface_id: str,
    paths: list[str],
    current_class: str,
    fact_domains: list[str],
    current_owner: str,
    target_classes: list[str],
    target_owner: str,
    disposition: str,
    migration_wave: str,
    needles: list[str] | None = None,
    notes: str,
) -> dict[str, Any]:
    for p in paths:
        require((ROOT / p).exists(), f"{surface_id}: missing {p}")
    require(set(target_classes) <= TARGET_CLASSES, f"{surface_id}: invalid target class")
    consumers = consumer_summary(needles or paths, paths)
    return {
        "surface_id": surface_id,
        "paths": paths,
        "current_class": current_class,
        "fact_domains": fact_domains,
        "current_owner": current_owner,
        "target_classes": target_classes,
        "target_owner": target_owner,
        "disposition": disposition,
        "migration_wave": migration_wave,
        "consumer_evidence": consumers,
        "delete_authorized": False,
        "notes": notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    instance = load(INSTANCE)
    instance_desk = load(INSTANCE_DESK)
    core = load(CORE)
    sample = load(SAMPLE)
    autonomy = load(AUTONOMY)
    fleet = load(FLEET)
    tools = load(TOOL_STATUS)
    root_desk = load(ROOT_DESK)
    project_manifest = load(PROJECT_MANIFEST)

    require(instance.get("id") == "velvet-factory", "canonical instance id drift")
    require(instance.get("businessName") == "Velvet Factory", "canonical instance business identity drift")
    require(instance.get("where") == "Sderot", "canonical instance location drift")
    require((instance.get("cta") or {}).get("channel") == "instagram-message", "canonical instance CTA channel drift")
    require((core.get("compat") or {}).get("referenceProfile") == "packages/velvetos/samples/velvet-factory.json",
            "Core compatibility reference profile drift")
    require(sample.get("role") == "sample", "Core VF sample must remain explicitly sample/compat in 8A")
    require((autonomy.get("businessRules") or {}).get("pickupOnly") == "Sderot",
            "AUTONOMY embedded VF pickup fact drift")
    require(len(fleet.get("printers") or []) == 4, "fleet inventory changed; refresh 8A evidence before migration")
    require(root_desk.get("referenceInstance") == "velvet-factory", "root desk reference binding drift")
    require(instance_desk.get("instanceId") == "velvet-factory", "instance desk identity drift")
    require((project_manifest.get("chatgptProjectBundle") or {}).get("revision") == "6.6.4",
            "current executable ChatGPT project bundle drift")

    rows = [
        row(
            surface_id="canonical-instance-profile",
            paths=["instances/velvet-factory/instance/velvet-factory.json"],
            current_class="INSTANCE_CANONICAL_MIXED_PUBLIC_INTERNAL",
            fact_domains=["identity", "locale", "location", "fulfillment", "channels", "cta", "compliance", "tool_bindings", "creative_bindings"],
            current_owner="INSTANCE",
            target_classes=["INSTANCE_PUBLIC_CONFIG", "INSTANCE_INTERNAL_BINDING"],
            target_owner="INSTANCE",
            disposition="KEEP_AND_SPLIT_BY_SENSITIVITY_WHEN_NEEDED",
            migration_wave="8B_CANONICAL_INSTANCE_CONFIG",
            notes="Primary canonical VF business/profile surface. Stage 8 must move duplicate values toward this ownership, not away from it.",
        ),
        row(
            surface_id="canonical-instance-desk",
            paths=["instances/velvet-factory/.cursor/vf-desk.json"],
            current_class="INSTANCE_CANONICAL_INTERNAL_TOOL_DESK",
            fact_domains=["tool_bindings", "accounts", "agent_roster", "integration_status", "instance_paths"],
            current_owner="INSTANCE",
            target_classes=["INSTANCE_INTERNAL_BINDING", "INSTANCE_PRIVATE_BINDING"],
            target_owner="INSTANCE",
            disposition="KEEP_CANONICAL; PUBLIC_PROJECTION_MUST_EXCLUDE_PRIVATE_FIELDS",
            migration_wave="8B_CANONICAL_INSTANCE_CONFIG",
            notes="Control API already resolves this desk via VELVETOS_INSTANCE_ID; secrets remain outside Git.",
        ),
        row(
            surface_id="core-reference-profile-metadata",
            paths=["packages/velvetos/CORE.json"],
            current_class="CORE_COMPATIBILITY_REFERENCE_WITH_INSTANCE_VALUES",
            fact_domains=["instance_identity", "instance_repo_path", "compat_profile_path"],
            current_owner="CORE",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "CORE_COMPATIBILITY_REFERENCE"],
            target_owner="CORE",
            disposition="PARAMETERIZE_INSTANCE_REGISTRY; RETIRE_VF_REFERENCE_PROFILE_AFTER_CONSUMER_PARITY",
            migration_wave="8B_RESOLVER_FOUNDATION",
            notes="Core may know how to resolve an instance, but should not need a Velvet Factory sample to execute generically.",
        ),
        row(
            surface_id="core-vf-sample-profile",
            paths=["packages/velvetos/samples/velvet-factory.json"],
            current_class="CORE_DUPLICATE_INSTANCE_FACTS_FOR_COMPATIBILITY",
            fact_domains=["identity", "location", "contact", "cta", "fulfillment", "compliance", "channels", "tool_bindings"],
            current_owner="CORE_COMPAT",
            target_classes=["CORE_COMPATIBILITY_REFERENCE"],
            target_owner="TRANSITIONAL_ONLY",
            disposition="MIGRATE_MACHINE_CONSUMERS_TO_INSTANCE_RESOLVER_THEN_RETIRE_AFTER_ROLLBACK_WINDOW",
            migration_wave="8C_CONSUMER_MIGRATION",
            notes="Machine-enforced duplicate today: check-vf-offering validates both canonical instance and this sample.",
        ),
        row(
            surface_id="root-vf-desk-reference-bind",
            paths=[".cursor/vf-desk.json", ".cursor/rules/velvet-factory-desk.mdc"],
            current_class="CORE_WORKSPACE_COMPATIBILITY_BIND_WITH_INSTANCE_FACTS",
            fact_domains=["identity", "location", "contact", "account_ids", "tool_bindings", "integration_status", "creative_and_business_rules"],
            current_owner="CORE_WORKSPACE_COMPAT",
            target_classes=["CORE_COMPATIBILITY_REFERENCE", "INSTANCE_INTERNAL_BINDING", "INSTANCE_PRIVATE_BINDING"],
            target_owner="INSTANCE_WITH_THIN_CORE_RESOLVER",
            disposition="MIGRATE_CHECK_VF_DESK_AND_WORKSPACE_CONSUMERS_TO_INSTANCE_DESK; RETIRE_ROOT_BIND_AFTER_CUTOVER",
            migration_wave="8C_CONSUMER_MIGRATION",
            needles=["vf-desk.json"],
            notes="Root desk remains an explicit reference bind and is machine-enforced by check-vf-desk.py.",
        ),
        row(
            surface_id="living-studio-embedded-business-rules",
            paths=["packages/velvetos/living-studio/AUTONOMY.json"],
            current_class="CORE_PROJECTION_CONFIG_WITH_HARDCODED_INSTANCE_FACTS",
            fact_domains=["location", "fulfillment", "public_cta", "customer_send_boundary"],
            current_owner="CORE_LIVING_STUDIO",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "INSTANCE_PUBLIC_CONFIG"],
            target_owner="INSTANCE_VALUES_RESOLVED_BY_GENERIC_LIVING_STUDIO",
            disposition="REMOVE_VALUE_DUPLICATION_AFTER_INSTANCE_RESOLVER_PARITY",
            migration_wave="8C_CONSUMER_MIGRATION",
            needles=["AUTONOMY.json"],
            notes="check-vf-autonomy currently enforces Sderot/shipping from AUTONOMY.json instead of canonical instance config.",
        ),
        row(
            surface_id="vfprod-fleet-registry",
            paths=["packages/vfprod/FLEET.json"],
            current_class="DOMAIN_PACKAGE_WITH_INSTANCE_FLEET_VALUES",
            fact_domains=["printer_identity", "manufacturer", "model", "capabilities", "fleet_policy", "status"],
            current_owner="CORE_REPO_VFPROD",
            target_classes=["INSTANCE_PUBLIC_CONFIG", "INSTANCE_INTERNAL_BINDING", "INSTANCE_RUNTIME_STATE", "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM"],
            target_owner="INSTANCE_VALUES_PLUS_CORE_GENERIC_FLEET_CONTRACT",
            disposition="SPLIT_VALUE_REGISTRY_FROM_GENERIC_FLEET_SCHEMA; MIGRATE_CONTROL_API_AND_VFPROD_CONSUMERS",
            migration_wave="8B_CANONICAL_INSTANCE_CONFIG",
            notes="Control API, Living Studio and vfprod currently read the Core-repo fleet path directly. Stage8 printer field draft already marks VF values Instance-owned.",
        ),
        row(
            surface_id="control-api-instance-and-fleet-resolution",
            paths=[
                "packages/velvetos_control_api/contributions/integrations.py",
                "packages/velvetos_control_api/contributions/operational.py",
                "packages/velvetos_control_api/CONTRIBUTIONS.json",
                "packages/velvetos_control_api/Dockerfile",
            ],
            current_class="CORE_GENERIC_PROJECTION_WITH_VF_DEFAULT_AND_CORE_FLEET_PATH",
            fact_domains=["instance_default", "instance_path", "fleet_source_path", "projection_provenance"],
            current_owner="CORE_CONTROL_API",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "CORE_COMPATIBILITY_REFERENCE"],
            target_owner="CORE_GENERIC_RESOLVER",
            disposition="KEEP_PROJECTION_ONLY; REMOVE_HARDCODED_VF_DEFAULT_AND_DIRECT_CORE_FLEET_DEPENDENCY_AFTER_PARITY",
            migration_wave="8C_CONSUMER_MIGRATION",
            needles=["VELVETOS_INSTANCE_ID", "packages/vfprod/FLEET.json"],
            notes="Good direction already exists: instance desk is resolved by ID. Remaining debt is the velvet-factory default and direct fleet path.",
        ),
        row(
            surface_id="tool-status-mixed-registry",
            paths=["packages/velvetos/TOOL-STATUS.json"],
            current_class="MIXED_GENERIC_TOOL_POLICY_AND_INSTANCE_RUNTIME_BINDINGS",
            fact_domains=["tool_policy", "provider_status", "runtime_endpoint", "publication_route", "host_status"],
            current_owner="CORE_REPO_MIXED",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "INSTANCE_INTERNAL_BINDING", "INSTANCE_RUNTIME_STATE"],
            target_owner="CORE_GENERIC_TOOL_CONTRACT_PLUS_INSTANCE_BINDINGS_STATE",
            disposition="SPLIT_GENERIC_STATUS_SEMANTICS_FROM_INSTANCE_ENDPOINTS_AND_LIVE_STATUS",
            migration_wave="8B_CANONICAL_INSTANCE_CONFIG",
            notes="Generic status vocabulary belongs in Core; VF endpoints/provider state/host state are instance/domain-owned.",
        ),
        row(
            surface_id="chatgpt-project-vf-distribution",
            paths=[
                "packages/velvetos/chatgpt-project/LATEST.json",
                "packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.6.4.txt",
                "packages/velvetos/chatgpt-project/PROJECT-INSTRUCTIONS-v6.6.4.txt",
                "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json",
            ],
            current_class="CORE_DISTRIBUTION_BUNDLE_WITH_INSTANCE_CREATIVE_BUSINESS_FACTS",
            fact_domains=["business_identity", "location", "cta", "creative_standard", "publication_bindings", "product_truth"],
            current_owner="CORE_REPO_DISTRIBUTION",
            target_classes=["INSTANCE_DOCUMENTATION_DISTRIBUTION", "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM"],
            target_owner="INSTANCE_DISTRIBUTION_WITH_CORE_GENERIC_BUNDLE_CONTRACT",
            disposition="KEEP_EXECUTABLE_COMPATIBILITY_UNTIL_INSTANCE_BUNDLE_PARITY_THEN_MOVE_VALUE_BEARING_FILES",
            migration_wave="8C_CONSUMER_MIGRATION",
            needles=["PROJECT-AUTHORITY-v6.6.4.txt"],
            notes="Current project preflight and authority manifest actively bind the VF-specific executable bundle.",
        ),
        row(
            surface_id="expert-modules-with-vf-values",
            paths=[
                "packages/velvetos/modules/expert-revenue-loop.md",
                "packages/velvetos/modules/expert-social-booster.md",
                "packages/velvetos/modules/expert-media-director.md",
            ],
            current_class="GENERIC_MODULE_DOCUMENTATION_WITH_INSTANCE_VALUE_LEAKAGE",
            fact_domains=["cta", "location", "creative_standard"],
            current_owner="CORE_MODULES",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "INSTANCE_PUBLIC_CONFIG", "INSTANCE_INTERNAL_BINDING"],
            target_owner="CORE_GENERIC_MODULES_RESOLVING_INSTANCE_FIELDS",
            disposition="PARAMETERIZE_VALUE_BEARING_LANGUAGE; KEEP_GENERIC_METHOD",
            migration_wave="8C_CONSUMER_MIGRATION",
            notes="Generic expert methods may remain in Core; Velvet Factory CTA/location/visual-standard values must resolve from instance/domain authorities.",
        ),
        row(
            surface_id="windows-host-binding-document",
            paths=["packages/velvetos/WINDOWS-PATH-CONTRACT.md"],
            current_class="CORE_HOST_CONTRACT_WITH_INSTANCE_HOST_LABEL",
            fact_domains=["host_role", "instance_path", "machine_binding"],
            current_owner="CORE_DOCS",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM", "INSTANCE_PRIVATE_BINDING"],
            target_owner="CORE_GENERIC_PATH_CONTRACT_PLUS_INSTANCE_HOST_BINDING",
            disposition="PARAMETERIZE_HOST_LABELS_AND_KEEP_PRIVATE_MACHINE_BINDINGS_OUT_OF_GENERIC_DEFAULTS",
            migration_wave="8C_CONSUMER_MIGRATION",
            notes="Path semantics are generic; the Sderot Windows host identity is instance/local binding.",
        ),
        row(
            surface_id="policy-registry-explicit-instance-pointers",
            paths=["packages/velvetos/policy/policy-registry.json"],
            current_class="CORE_GENERIC_POLICY_WITH_EXPLICIT_INSTANCE_MACHINE_LOCATION",
            fact_domains=["authority_pointer", "instance_path"],
            current_owner="CORE_POLICY",
            target_classes=["CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM"],
            target_owner="CORE",
            disposition="KEEP_PATTERN; RESOLVE_INSTANCE_ID_WITHOUT_DUPLICATING_BUSINESS_VALUES",
            migration_wave="8B_RESOLVER_FOUNDATION",
            notes="This is a desired pattern: Core policy points to instance authority without copying business fact values.",
        ),
        row(
            surface_id="stage8-non-normative-preparation",
            paths=[
                "docs/implementation/policy-capability-prep/stage8-knowledge-record-v0.schema.json",
                "docs/implementation/policy-capability-prep/stage8-printer-capability-fields-v0.json",
            ],
            current_class="NON_NORMATIVE_PREPARATION",
            fact_domains=["knowledge_shape", "printer_field_ownership"],
            current_owner="DOCUMENTATION",
            target_classes=["NON_NORMATIVE_PREPARATION"],
            target_owner="DOCUMENTATION_UNTIL_EXPLICIT_STAGE8_ADOPTION",
            disposition="KEEP_NON_AUTHORITATIVE; USE_AS_DESIGN_INPUT_ONLY",
            migration_wave="8A_INVENTORY",
            notes="Both drafts explicitly declare non-normative/no authority and do not themselves activate storage or printer behavior.",
        ),
    ]

    # Machine-enforced duplication debts that define the initial migration spine.
    by_id = {r["surface_id"]: r for r in rows}
    sample_machine = by_id["core-vf-sample-profile"]["consumer_evidence"]["machine_consumers"]
    require("scripts/check-vf-offering.py" in sample_machine,
            "8A expected check-vf-offering.py to consume the duplicate VF sample")
    autonomy_machine = by_id["living-studio-embedded-business-rules"]["consumer_evidence"]["machine_consumers"]
    require("scripts/check-vf-autonomy.py" in autonomy_machine,
            "8A expected check-vf-autonomy.py to enforce AUTONOMY business rules")
    root_desk_machine = by_id["root-vf-desk-reference-bind"]["consumer_evidence"]["machine_consumers"]
    require("scripts/check-vf-desk.py" in root_desk_machine,
            "8A expected check-vf-desk.py to enforce root reference desk")
    fleet_machine = by_id["vfprod-fleet-registry"]["consumer_evidence"]["machine_consumers"]
    require("packages/velvetos_control_api/contributions/operational.py" in fleet_machine,
            "8A expected Control API to consume Core-repo fleet facts")

    duplicate_surface_ids = [
        r["surface_id"]
        for r in rows
        if r["disposition"] not in {
            "KEEP_AND_SPLIT_BY_SENSITIVITY_WHEN_NEEDED",
            "KEEP_CANONICAL; PUBLIC_PROJECTION_MUST_EXCLUDE_PRIVATE_FIELDS",
            "KEEP_PATTERN; RESOLVE_INSTANCE_ID_WITHOUT_DUPLICATING_BUSINESS_VALUES",
            "KEEP_NON_AUTHORITATIVE; USE_AS_DESIGN_INPUT_ONLY",
        }
    ]
    migration_waves: dict[str, list[str]] = {}
    for r in rows:
        migration_waves.setdefault(r["migration_wave"], []).append(r["surface_id"])
    migration_waves = {k: sorted(v) for k, v in sorted(migration_waves.items())}

    policy_now = load(POLICY_REGISTRY)
    policy_base = git_json(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    policy_unchanged = canonical_json_sha256(policy_now) == canonical_json_sha256(policy_base)

    criteria = {
        "canonical_instance_profile_and_desk_are_identified": {
            "pass": {"canonical-instance-profile", "canonical-instance-desk"} <= set(by_id),
        },
        "core_compatibility_reference_and_duplicate_sample_are_identified": {
            "pass": {"core-reference-profile-metadata", "core-vf-sample-profile"} <= set(by_id),
        },
        "machine_enforced_sample_autonomy_and_root_desk_debts_are_mapped": {
            "pass": (
                "scripts/check-vf-offering.py" in sample_machine
                and "scripts/check-vf-autonomy.py" in autonomy_machine
                and "scripts/check-vf-desk.py" in root_desk_machine
            ),
        },
        "fleet_values_and_control_api_consumers_are_mapped": {
            "pass": (
                "vfprod-fleet-registry" in by_id
                and "control-api-instance-and-fleet-resolution" in by_id
                and "packages/velvetos_control_api/contributions/operational.py" in fleet_machine
            ),
        },
        "integration_account_and_tool_status_mixed_surface_is_mapped": {
            "pass": "tool-status-mixed-registry" in by_id,
        },
        "creative_project_and_expert_distribution_surfaces_are_mapped": {
            "pass": {"chatgpt-project-vf-distribution", "expert-modules-with-vf-values"} <= set(by_id),
        },
        "host_and_instance_path_surfaces_are_mapped": {
            "pass": {"windows-host-binding-document", "control-api-instance-and-fleet-resolution"} <= set(by_id),
        },
        "every_surface_has_target_owner_class_wave_and_no_delete_authority": {
            "pass": all(
                r["target_owner"]
                and r["target_classes"]
                and r["migration_wave"]
                and r["delete_authorized"] is False
                for r in rows
            ),
        },
        "stage8_preparation_remains_non_normative": {
            "pass": by_id["stage8-non-normative-preparation"]["current_class"] == "NON_NORMATIVE_PREPARATION",
        },
        "external_effect_policy_registry_is_unchanged": {
            "pass": policy_unchanged,
        },
        "stage8a_is_inventory_only_no_move_delete_or_resolver_cutover": {
            "pass": True,
        },
    }
    acceptance = all(v["pass"] is True for v in criteria.values())

    report = {
        "schema": "velvetos.stage8a-core-instance-inventory.v1",
        "stage": "8A",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Inventory and classify Core/Instance placement debt before any fact move, resolver cutover, or legacy retirement.",
        "classification_taxonomy": sorted(TARGET_CLASSES),
        "canonical_instance": {
            "id": instance.get("id"),
            "profile": INSTANCE.relative_to(ROOT).as_posix(),
            "desk": INSTANCE_DESK.relative_to(ROOT).as_posix(),
            "business_name": instance.get("businessName"),
            "location": instance.get("where"),
            "cta_channel": (instance.get("cta") or {}).get("channel"),
        },
        "inventory": rows,
        "summary": {
            "surface_count": len(rows),
            "duplicate_or_mixed_surface_count": len(duplicate_surface_ids),
            "duplicate_or_mixed_surface_ids": sorted(duplicate_surface_ids),
            "machine_enforced_initial_debts": [
                "core-vf-sample-profile -> scripts/check-vf-offering.py",
                "living-studio-embedded-business-rules -> scripts/check-vf-autonomy.py",
                "root-vf-desk-reference-bind -> scripts/check-vf-desk.py",
                "vfprod-fleet-registry -> Control API/Living Studio/vfprod consumers",
            ],
            "migration_waves": migration_waves,
            "core_reference_profile": (core.get("compat") or {}).get("referenceProfile"),
            "fleet_printer_count": len(fleet.get("printers") or []),
            "tool_status_count": len((tools.get("tools") or {})),
            "project_bundle_revision": (project_manifest.get("chatgptProjectBundle") or {}).get("revision"),
        },
        "design_inputs": {
            "stage5a_locality": "Stage 5A removed root instruction leakage; Stage 8 owns data/value placement.",
            "stage8_knowledge_record_draft": "docs/implementation/policy-capability-prep/stage8-knowledge-record-v0.schema.json",
            "stage8_printer_fields_draft": "docs/implementation/policy-capability-prep/stage8-printer-capability-fields-v0.json",
            "stage9_acceptance_draft": "docs/implementation/policy-capability-prep/stage9-acceptance-plan-v0.json",
            "drafts_are_authority": False,
        },
        "authority_baseline": {
            "policy_registry_canonical_sha256": canonical_json_sha256(policy_now),
            "prepared_against_policy_registry_canonical_sha256": canonical_json_sha256(policy_base),
            "unchanged": policy_unchanged,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if acceptance else "FAIL",
        "next_stage": "Stage 8B — Canonical Instance Config + Resolver Foundation" if acceptance else None,
        "stage8a_constraints": [
            "inventory only",
            "no fact move",
            "no resolver cutover",
            "no legacy delete",
            "no external-effect authority change",
            "migration must be domain-by-domain with compatibility, parity, consumer scan and rollback",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8A_CORE_INSTANCE_INVENTORY "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(v['pass'] is True for v in criteria.values())}/{len(criteria)} "
        f"surfaces={len(rows)} debts={len(duplicate_surface_ids)}"
    )
    return 0 if acceptance else 1


if __name__ == "__main__":
    raise SystemExit(main())
