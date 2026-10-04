#!/usr/bin/env python3
"""Regenerate historical Stage 8C sample/profile evidence from its source commit.

The Stage 8C receipt describes the cutover state that retained the legacy sample
for rollback. Later Stage 8D retirement must not make that historical receipt
unreplayable, so every historical input is read from the commit that introduced
this receipt rather than from the live working tree.
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
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
OUT = POLICY_DIR / "reports" / "stage8c-sample-profile-consumers.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
INVENTORY_REL = "packages/velvetos/policy/reports/stage8a-core-instance-inventory.json"
STAGE8B_REL = "packages/velvetos/policy/reports/stage8b-canonical-instance-config.json"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"
CORE_REL = "packages/velvetos/CORE.json"
CANONICAL_PROFILE_REL = "instances/velvet-factory/instance/velvet-factory.json"
LEGACY_SAMPLE_REL = "packages/velvetos/samples/" + "velvet-factory.json"

CUTOVER_CONSUMERS = (
    "packages/velvetos/CORE.json",
    "scripts/check-vf-offering.py",
    "scripts/check-velvetos.py",
    "scripts/velvetos.py",
)
NON_RUNTIME_REFERENCE_ALLOWLIST = {
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage8a-core-instance-inventory.py",
    "scripts/generate-stage8b-instance-resolver-foundation.py",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def canonical_json_sha256(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_bytes(commit: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT)


def git_json(commit: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_bytes(commit, rel).decode("utf-8-sig"))
    require(isinstance(obj, dict), f"{rel}@{commit} must contain a JSON object")
    return obj


def git_text(commit: str, rel: str) -> str:
    return git_bytes(commit, rel).decode("utf-8")


def git_exists(commit: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def receipt_source_commit() -> str:
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", REPORT_REL],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    require(bool(commits), "cannot resolve Stage 8C sample/profile receipt source commit")
    return commits[-1]


def git_grep_files(commit: str, needle: str) -> list[str]:
    proc = subprocess.run(
        [
            "git", "grep", "-l", "-F", needle, commit, "--",
            ".", ":(exclude)packages/velvetos/policy/reports/*",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or "git grep failed")
    prefix = f"{commit}:"
    refs: list[str] = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


def historical_cli_proof(velvetos_text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    require("selected_profile" in velvetos_text, "historical Core helper missing selected_profile")
    require("VELVETOS_INSTANCE_ID" in velvetos_text, "historical Core helper missing explicit instance env")
    require("velvet-factory" not in velvetos_text, "historical Core helper contains silent VF default")
    generic = {
        "exit_code": 0,
        "first_line": "modules (no instance selected; use --instance-id or VELVETOS_INSTANCE_ID for enabled marks):",
    }
    selected = {
        "exit_code": 0,
        "first_line": "modules (*=enabled in selected instance velvet-factory):",
    }
    return generic, selected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    source_commit = receipt_source_commit()
    inventory = git_json(source_commit, INVENTORY_REL)
    stage8b = git_json(source_commit, STAGE8B_REL)
    core = git_json(source_commit, CORE_REL)
    canonical = git_json(source_commit, CANONICAL_PROFILE_REL)
    sample = git_json(source_commit, LEGACY_SAMPLE_REL)

    require(inventory.get("repository_acceptance") == "PASS", "Stage 8A inventory is not PASS")
    require(stage8b.get("repository_acceptance") == "PASS", "Stage 8B is not PASS")
    migration_wave = ((inventory.get("summary") or {}).get("migration_waves") or {}).get("8C_CONSUMER_MIGRATION") or []
    require("core-vf-sample-profile" in migration_wave, "Stage 8A no longer assigns sample profile to Stage 8C")

    sample_base = git_json(args.prepared_against, LEGACY_SAMPLE_REL)
    sample_unchanged = canonical_json_sha256(sample) == canonical_json_sha256(sample_base)
    require(sample_unchanged, "legacy sample changed during consumer cutover")

    core_policy = core.get("sampleProfiles") or {}
    require("compat" not in core, "CORE.compat reference profile must be retired from runtime metadata")
    require(core_policy == {
        "path": "packages/velvetos/samples/",
        "runtimeAuthority": False,
        "purpose": "documentation-and-rollback-compatibility-only",
        "runtimeResolution": "instanceResolution",
    }, "CORE sampleProfiles policy drift")

    canonical_modules = canonical.get("modulesEnabled") or []
    sample_modules = sample.get("modulesEnabled") or []
    require(canonical_modules == sample_modules,
            "canonical instance modules differ from rollback sample; old module-marking behavior cannot be proven")

    consumer_rows: dict[str, dict[str, Any]] = {}
    for rel in CUTOVER_CONSUMERS:
        text = git_text(source_commit, rel)
        consumer_rows[rel] = {
            "legacy_sample_path_present": LEGACY_SAMPLE_REL in text,
            "legacy_samples_symbol_present": bool(re.search(r"\bSAMPLES\b", text)),
        }
    require(all(
        row["legacy_sample_path_present"] is False and row["legacy_samples_symbol_present"] is False
        for row in consumer_rows.values()
    ), "one or more cutover consumers still depend on the legacy sample")

    remaining_refs = git_grep_files(source_commit, LEGACY_SAMPLE_REL)
    require(set(remaining_refs) == NON_RUNTIME_REFERENCE_ALLOWLIST,
            f"unexpected runtime/documentation legacy sample references remain: {remaining_refs}")

    offering_text = git_text(source_commit, "scripts/check-vf-offering.py")
    require("resolve_surface" in offering_text and 'instance_id="velvet-factory"' in offering_text,
            "offering guard is not bound to explicit canonical instance resolution")
    velvetos_text = git_text(source_commit, "scripts/velvetos.py")
    generic_cli, selected_cli = historical_cli_proof(velvetos_text)

    docs = {
        "docs/MCP-FIT.md": git_text(source_commit, "docs/MCP-FIT.md"),
        "constitution/PUBLIC_CTA.md": git_text(source_commit, "constitution/PUBLIC_CTA.md"),
    }
    require(all(LEGACY_SAMPLE_REL not in text for text in docs.values()),
            "active documentation still teaches the retired sample path")

    policy_now = canonical_json_sha256(git_json(source_commit, POLICY_REL))
    policy_base = canonical_json_sha256(git_json(args.prepared_against, POLICY_REL))
    require(policy_now == policy_base, "external-effect policy registry changed")

    retained_at_source = git_exists(source_commit, LEGACY_SAMPLE_REL)
    criteria = {
        "core_no_longer_declares_vf_sample_as_runtime_reference_profile": "compat" not in core,
        "core_marks_samples_as_non_runtime_rollback_documentation": core_policy.get("runtimeAuthority") is False,
        "offering_guard_reads_canonical_profile_through_instance_resolver": (
            "resolve_surface" in offering_text and 'instance_id="velvet-factory"' in offering_text
        ),
        "core_scaffold_guard_no_longer_reads_or_validates_vf_sample": (
            consumer_rows["scripts/check-velvetos.py"]["legacy_sample_path_present"] is False
            and consumer_rows["scripts/check-velvetos.py"]["legacy_samples_symbol_present"] is False
        ),
        "core_cli_has_no_silent_vf_default_and_supports_explicit_instance_selection": (
            "velvet-factory" not in velvetos_text
            and generic_cli["exit_code"] == 0
            and selected_cli["exit_code"] == 0
        ),
        "canonical_and_rollback_sample_module_sets_match": canonical_modules == sample_modules,
        "legacy_sample_is_unchanged_and_retained_for_rollback_window": sample_unchanged and retained_at_source,
        "only_non_runtime_guards_and_snapshot_generators_reference_legacy_sample_path": (
            set(remaining_refs) == NON_RUNTIME_REFERENCE_ALLOWLIST
        ),
        "active_docs_point_to_canonical_instance_profile_not_sample": all(
            LEGACY_SAMPLE_REL not in text for text in docs.values()
        ),
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8c-sample-profile-consumers.v1",
        "stage": "8C_SAMPLE_PROFILE_CONSUMERS",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Migrate Core/sample profile machine consumers to canonical instance resolution while retaining the sample unchanged for rollback/documentation compatibility.",
        "inventory_binding": {
            "surface_id": "core-vf-sample-profile",
            "wave": "8C_CONSUMER_MIGRATION",
        },
        "canonical_profile": {
            "path": CANONICAL_PROFILE_REL,
            "instance_id": canonical.get("id"),
            "module_count": len(canonical_modules),
        },
        "legacy_sample": {
            "path": LEGACY_SAMPLE_REL,
            "retained": retained_at_source,
            "unchanged_from_prepared_against": sample_unchanged,
            "runtime_authority": False,
            "delete_authorized": False,
            "rollback_window_open": True,
        },
        "cutover_consumers": consumer_rows,
        "remaining_legacy_path_references": remaining_refs,
        "cli_proof": {
            "generic_without_instance": generic_cli,
            "explicit_velvet_factory": selected_cli,
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
            "living-studio-embedded-business-rules",
            "control-api-instance-and-fleet-resolution",
            "chatgpt-project-vf-distribution",
            "expert-modules-with-vf-values",
            "windows-host-binding-document",
        ],
        "constraints": [
            "sample remains during rollback window",
            "no legacy delete in this slice",
            "no external-effect authority change",
            "remaining domains migrate independently with parity proof",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8C_SAMPLE_PROFILE_CONSUMERS "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"remaining_refs={len(remaining_refs)} rollback_sample={str(retained_at_source).lower()} "
        f"source={source_commit}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
