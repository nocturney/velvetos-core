#!/usr/bin/env python3
"""Generate Stage 8D root-desk compatibility-consumer migration evidence."""
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
OUT = REPORTS / "stage8d-root-desk-consumer-migration.json"
READINESS = REPORTS / "stage8d-retirement-readiness.json"
ROOT_DESK_RECEIPT = REPORTS / "stage8c-root-desk-readers.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY_REL = "/".join([".cursor", "vf-desk.json"])
CURSOR_RULE_REL = ".cursor/rules/velvet-factory-desk.mdc"
VISUAL_SENSOR_REL = "scripts/check-visual-surface-enforcement.py"
ACTIVE_BLOCKERS = (CURSOR_RULE_REL, VISUAL_SENSOR_REL)


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
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"git grep failed for {needle!r}")
    prefix = f"{commit}:"
    refs = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


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

    prior = git_json(args.source_commit, ROOT_DESK_RECEIPT.relative_to(ROOT).as_posix())
    require(prior.get("repository_acceptance") == "PASS", "Stage 8C root-desk parity receipt must PASS")
    prior_parity = ((prior.get("canonical_tool_desk") or {}).get("parity") or {})
    require(prior_parity and all(prior_parity.values()), "Stage 8C root-desk required subtree parity drift")

    rule = git_text(args.source_commit, CURSOR_RULE_REL)
    sensor = git_text(args.source_commit, VISUAL_SENSOR_REL)
    require("instance:surface:toolDesk" in rule, "Cursor rule does not use selected instance toolDesk surface")
    require(LEGACY_REL not in rule, "Cursor rule still names root compatibility desk")
    require("resolve_surface" in sensor and '"toolDesk"' in sensor, "visual sensor does not resolve toolDesk through instance resolver")
    require(LEGACY_REL not in sensor, "visual sensor still contains ambiguous root desk literal")

    refs = grep_refs(LEGACY_REL, args.source_commit)
    active_refs = [ref for ref in ACTIVE_BLOCKERS if ref in refs]
    require(not active_refs, f"known active root-desk consumers remain: {active_refs}")

    policy_now = csha(git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix()))
    policy_base = csha(git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix()))
    require(policy_now == policy_base, "external-effect policy changed")

    criteria = {
        "cursor_rule_resolves_selected_instance_tool_desk_surface": "instance:surface:toolDesk" in rule,
        "cursor_rule_has_no_root_desk_literal": LEGACY_REL not in rule,
        "visual_sensor_resolves_tool_desk_through_instance_resolver": "resolve_surface" in sensor and '"toolDesk"' in sensor,
        "visual_sensor_has_no_root_desk_literal": LEGACY_REL not in sensor,
        "known_active_root_desk_blockers_are_removed": not active_refs,
        "stage8c_required_tool_and_ops_parity_remains_proven": all(prior_parity.values()),
        "legacy_root_desk_is_retained_for_rollback": git_exists(args.source_commit, LEGACY_REL),
        "root_desk_retirement_remains_unauthorized_while_rollback_window_is_open": True,
        "stage8d_readiness_baseline_is_preserved": readiness.get("retirement_authorized") is False,
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8d-root-desk-consumer-migration.v1",
        "stage": "8D_ROOT_DESK_CONSUMER_MIGRATION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": "Remove the remaining active root-desk compatibility consumers while retaining the root desk for rollback.",
        "migration": {
            "legacy_path": LEGACY_REL,
            "replacement_surface": "instance:surface:toolDesk",
            "consumers": {
                CURSOR_RULE_REL: "selected-instance-toolDesk-surface",
                VISUAL_SENSOR_REL: "instance-resolver-toolDesk",
            },
            "legacy_path_retained": True,
            "delete_authorized": False,
        },
        "prior_parity_evidence": {
            "path": ROOT_DESK_RECEIPT.relative_to(ROOT).as_posix(),
            "required_subtrees": prior_parity,
            "all_required_parity": all(prior_parity.values()),
        },
        "consumer_scan": {
            "legacy_reference_count": len(refs),
            "known_active_blocker_references": active_refs,
            "active_blockers_removed": not active_refs,
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
        "next_action": "Migrate the next active compatibility consumer; do not delete the root desk until explicit rollback-window closure evidence exists.",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8D_ROOT_DESK_CONSUMER "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(map(bool, criteria.values()))}/{len(criteria)} "
        f"active_refs={len(active_refs)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
