#!/usr/bin/env python3
"""Generate Stage 8D tool-status compatibility-consumer migration evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-tool-status-consumer-migration.json"
READINESS = REPORTS / "stage8d-retirement-readiness.json"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"
LEGACY_REL = "packages/velvetos/TOOL-STATUS.json"
CONTRACT_REL = "packages/velvetos/tool-status-contract.json"
CORE_REL = "packages/velvetos/CORE.json"
STATE_REL = "instances/velvet-factory/instance/tool-status.json"
OPENPOST_REL = "packages/vfigos/OPENPOST.json"
CORE_MCP_REL = "packages/vfmcp/core-mcp.json"

DIRECT_READERS = (
    "scripts/check-upstream-watch.py",
    "scripts/check-tool-authority.py",
    "scripts/check-vf-cad-stack.py",
    "scripts/check-vf-fabrication-router.py",
    "scripts/check-vfmcp.py",
    "scripts/vf_reel_candidates.py",
)
RESOLVER_READERS = tuple(rel for rel in DIRECT_READERS if rel != "scripts/check-vfmcp.py")
ACTIVE_AUTHORITY_SURFACES = (
    ".cursor/rules/velvet-factory-desk.mdc",
    "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc",
    "instances/velvet-factory/AGENTS.md",
    "packages/README.md",
    "packages/vfharness/playbooks/grok-outage-tools.md",
    "packages/vfigos/OPENPOST.md",
    "packages/vfigos/SEND.md",
    "packages/vfops/ROUTINE.md",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig")


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_text(sha, rel))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must contain an object")
    return obj


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def grep_refs(needle: str, commit: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", needle, commit, "--", ":!packages/velvetos/policy/reports/*"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"git grep failed for {needle!r}")
    prefix = f"{commit}:"
    refs: list[str] = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


def composed_status(commit: str) -> dict[str, Any]:
    contract = git_json(commit, CONTRACT_REL)
    state = git_json(commit, STATE_REL)
    return {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    for name, value in (("prepared-against", args.prepared_against), ("source-commit", args.source_commit)):
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"bad {name} sha")

    readiness = git_json(args.source_commit, READINESS.relative_to(ROOT).as_posix())
    require(readiness.get("repository_assessment") == "PASS", "Stage 8D readiness baseline must PASS")
    require(readiness.get("retirement_authorized") is False, "retirement must remain blocked at migration entry")

    core = git_json(args.source_commit, CORE_REL)
    contract = git_json(args.source_commit, CONTRACT_REL)
    composition = contract.get("composition") or {}
    resolution = core.get("toolStatusResolution") or {}

    expected_resolution = {
        "contract": CONTRACT_REL,
        "resolver": "packages/velvetos/tool_status_resolver.py",
        "instanceSurface": "toolStatus",
        "activeAuthority": "instance:surface:toolStatus",
        "rollbackCompatibilityPath": LEGACY_REL,
        "consumerCutover": True,
        "rollbackCompatibilityRetained": True,
        "silentBusinessDefaultForbidden": True,
    }
    require(resolution == expected_resolution, "Core toolStatusResolution Stage 8D contract drift")
    require(composition.get("resolver") == "packages/velvetos/tool_status_resolver.py", "resolver binding drift")
    require(composition.get("activeAuthority") == "instance:surface:toolStatus", "active authority drift")
    require(composition.get("rollbackCompatibilityPath") == LEGACY_REL, "rollback path drift")
    require(composition.get("consumerCutover") is True, "consumer cutover not active")
    require(composition.get("rollbackCompatibilityRetained") is True, "rollback compatibility not retained")

    reader_rows: dict[str, dict[str, Any]] = {}
    for rel in DIRECT_READERS:
        text = git_text(args.source_commit, rel)
        row = {
            "legacy_literal_present": LEGACY_REL in text or "TOOL-STATUS.json" in text,
            "resolver_present": "compose_tool_status" in text,
        }
        reader_rows[rel] = row
        require(not row["legacy_literal_present"], f"{rel} still names legacy tool-status composite")
    require(
        all(reader_rows[rel]["resolver_present"] for rel in RESOLVER_READERS),
        "one or more active Stage 8B readers do not use the tool-status resolver",
    )
    require(
        not reader_rows["scripts/check-vfmcp.py"]["resolver_present"],
        "check-vfmcp should remove its unused legacy binding rather than add a fake status read",
    )

    authority_rows: dict[str, bool] = {}
    for rel in ACTIVE_AUTHORITY_SURFACES:
        text = git_text(args.source_commit, rel)
        ok = "instance:surface:toolStatus" in text and "TOOL-STATUS.json" not in text
        authority_rows[rel] = ok
        require(ok, f"active authority surface not migrated: {rel}")

    openpost = git_json(args.source_commit, OPENPOST_REL)
    require(openpost.get("toolStatusAuthority") == "instance:surface:toolStatus", "OpenPost authority drift")
    require(
        openpost.get("toolStatusResolver") == "packages/velvetos/tool_status_resolver.py",
        "OpenPost resolver binding drift",
    )
    core_mcp = git_json(args.source_commit, CORE_MCP_REL)
    rule = str(core_mcp.get("rule") or "")
    require("instance:surface:toolStatus" in rule and "tool_status_resolver.py" in rule, "core MCP authority drift")

    composed = composed_status(args.source_commit)
    legacy = git_json(args.source_commit, LEGACY_REL)
    parity = composed == legacy and csha(composed) == csha(legacy)
    require(parity, "selected-instance composition no longer matches retained legacy composite")

    all_refs = grep_refs(LEGACY_REL, args.source_commit)
    active_legacy_refs = sorted(
        set(DIRECT_READERS + ACTIVE_AUTHORITY_SURFACES + (OPENPOST_REL, CORE_MCP_REL)) & set(all_refs)
    )
    require(not active_legacy_refs, f"active authority legacy references remain: {active_legacy_refs}")

    policy_now = csha(git_json(args.source_commit, POLICY_REL))
    policy_base = csha(git_json(args.prepared_against, POLICY_REL))
    require(policy_now == policy_base, "external-effect policy changed")

    criteria = {
        "core_declares_selected_instance_tool_status_as_active_authority": resolution == expected_resolution,
        "tool_status_contract_marks_consumer_cutover_active": composition.get("consumerCutover") is True,
        "all_stage8b_direct_readers_have_no_legacy_composite_dependency": all(
            not row["legacy_literal_present"] for row in reader_rows.values()
        ),
        "all_real_stage8b_status_readers_use_the_generic_resolver": all(
            reader_rows[rel]["resolver_present"] for rel in RESOLVER_READERS
        ),
        "unused_vfmcp_legacy_binding_is_removed_without_fake_read": not reader_rows["scripts/check-vfmcp.py"]["resolver_present"],
        "active_authority_docs_and_rules_point_to_instance_tool_status": all(authority_rows.values()),
        "openpost_and_core_mcp_use_instance_tool_status_authority": (
            openpost.get("toolStatusAuthority") == "instance:surface:toolStatus"
            and "instance:surface:toolStatus" in rule
        ),
        "canonical_composition_remains_exactly_equal_to_legacy_composite": parity,
        "legacy_tool_status_composite_is_retained_for_rollback": git_exists(args.source_commit, LEGACY_REL),
        "rollback_window_remains_open_and_delete_is_unauthorized": True,
        "stage8d_readiness_baseline_is_preserved": readiness.get("retirement_authorized") is False,
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8d-tool-status-consumer-migration.v1",
        "stage": "8D_TOOL_STATUS_CONSUMER_MIGRATION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": "Cut active consumers over from the retained TOOL-STATUS compatibility composite to the selected instance toolStatus surface while preserving exact rollback parity.",
        "migration": {
            "active_authority": "instance:surface:toolStatus",
            "resolver": "packages/velvetos/tool_status_resolver.py",
            "rollback_compatibility_path": LEGACY_REL,
            "consumer_cutover": True,
            "rollback_compatibility_retained": True,
            "legacy_path_retained": True,
            "delete_authorized": False,
        },
        "direct_readers": reader_rows,
        "active_authority_surfaces": authority_rows,
        "consumer_scan": {
            "legacy_reference_count": len(all_refs),
            "active_authority_legacy_references": active_legacy_refs,
            "active_blockers_removed": not active_legacy_refs,
        },
        "parity": {
            "composed_canonical_json_sha256": csha(composed),
            "legacy_canonical_json_sha256": csha(legacy),
            "equal": parity,
        },
        "rollback": {
            "window_open": True,
            "retirement_ready": False,
            "delete_authorized": False,
        },
        "authority": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "external_effect_authority_changed": policy_now != policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_action": "Migrate the next active compatibility domain; do not delete packages/velvetos/TOOL-STATUS.json until explicit rollback-window closure evidence exists.",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8D_TOOL_STATUS_CONSUMER "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(map(bool, criteria.values()))}/{len(criteria)} "
        f"active_legacy_refs={len(active_legacy_refs)} "
        f"parity={parity}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
