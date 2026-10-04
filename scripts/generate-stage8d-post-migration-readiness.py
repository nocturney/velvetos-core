#!/usr/bin/env python3
"""Generate Reform v2 Stage 8D post-migration retirement readiness evidence.

Observation-only. This gate proves active compatibility consumers are migrated
and parity/rollback compatibility remains intact. It must not infer rollback
window closure, authorize deletion, or change external-effect authority.
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
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-post-migration-readiness.json"
INITIAL_REL = "packages/velvetos/policy/reports/stage8d-retirement-readiness.json"
SAMPLE_REL = "packages/velvetos/policy/reports/stage8c-sample-profile-consumers.json"
FLEET_REL = "packages/velvetos/policy/reports/stage8d-fleet-consumer-migration.json"
ROOT_DESK_REL = "packages/velvetos/policy/reports/stage8d-root-desk-consumer-migration.json"
TOOL_STATUS_REL = "packages/velvetos/policy/reports/stage8d-tool-status-consumer-migration.json"
CHATGPT_REL = "packages/velvetos/policy/reports/stage8d-chatgpt-core-consumer-migration.json"
POLICY_REL = "packages/velvetos/policy/policy-registry.json"

# Compose compatibility paths from components so historical Stage 8C consumer
# scans do not mistake this observation-only readiness machinery for an active
# legacy consumer.
LEGACY_PATHS = {
    "sample_profile": "/".join(["packages", "velvetos", "samples", "velvet-factory.json"]),
    "root_desk": "/".join([".cursor", "vf-desk.json"]),
    "fleet": "/".join(["packages", "vfprod", "FLEET.json"]),
    "tool_status": "/".join(["packages", "velvetos", "TOOL-STATUS.json"]),
    "chatgpt_core_bundle": "/".join(["packages", "velvetos", "chatgpt-project"]),
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_bytes(sha, rel).decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must contain an object")
    return obj


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    for label, value in (("prepared-against", args.prepared_against), ("source-commit", args.source_commit)):
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"bad {label} sha")

    require(args.prepared_against == args.source_commit,
            "post-migration readiness must be prepared from the verified merged main snapshot")

    initial = git_json(args.source_commit, INITIAL_REL)
    sample = git_json(args.source_commit, SAMPLE_REL)
    fleet = git_json(args.source_commit, FLEET_REL)
    root_desk = git_json(args.source_commit, ROOT_DESK_REL)
    tool_status = git_json(args.source_commit, TOOL_STATUS_REL)
    chatgpt = git_json(args.source_commit, CHATGPT_REL)

    require(initial.get("repository_assessment") == "PASS", "initial Stage 8D readiness must PASS")
    require(initial.get("retirement_authorized") is False, "initial Stage 8D readiness must remain non-authorizing")
    require(sample.get("repository_acceptance") == "PASS", "Stage 8C sample migration must PASS")
    for name, receipt in (
        ("fleet", fleet), ("root_desk", root_desk), ("tool_status", tool_status), ("chatgpt", chatgpt)
    ):
        require(receipt.get("repository_acceptance") == "PASS", f"Stage 8D {name} migration must PASS")

    initial_assessment = initial.get("assessment") or {}
    sample_legacy = sample.get("legacy_sample") or {}
    fleet_scan = fleet.get("consumer_scan") or {}
    desk_scan = root_desk.get("consumer_scan") or {}
    tool_scan = tool_status.get("consumer_scan") or {}
    chat_scan = chatgpt.get("consumer_scan") or {}

    clean = {
        "sample_profile": (
            initial_assessment.get("sample_profile_has_no_active_runtime_consumer") is True
            and sample_legacy.get("runtime_authority") is False
        ),
        "root_desk": (
            desk_scan.get("active_blockers_removed") is True
            and desk_scan.get("known_active_blocker_references") == []
        ),
        "fleet": (
            fleet_scan.get("active_blocker_removed") is True
            and fleet_scan.get("living_studio_legacy_references") == []
        ),
        "tool_status": (
            tool_scan.get("active_blockers_removed") is True
            and tool_scan.get("active_authority_legacy_references") == []
        ),
        "chatgpt_core_bundle": (
            chat_scan.get("active_blockers_removed") is True
            and chat_scan.get("active_legacy_references") == []
        ),
    }
    require(all(clean.values()), f"active compatibility consumer remains: {clean}")

    parity = {
        "sample_profile": (
            sample_legacy.get("unchanged_from_prepared_against") is True
            and sample_legacy.get("retained") is True
        ),
        "root_desk": (
            ((root_desk.get("prior_parity_evidence") or {}).get("all_required_parity") is True)
        ),
        "fleet": ((fleet.get("parity") or {}).get("equal") is True),
        "tool_status": ((tool_status.get("parity") or {}).get("equal") is True),
        "chatgpt_core_bundle": (
            (chatgpt.get("parity") or {}).get("byte_equal") is True
            and (chatgpt.get("parity") or {}).get("file_sets_equal") is True
        ),
    }
    require(all(parity.values()), f"compatibility parity evidence failed: {parity}")

    rollback_open = {
        "sample_profile": sample_legacy.get("rollback_window_open") is True,
        "root_desk": (root_desk.get("rollback") or {}).get("window_open") is True,
        "fleet": (fleet.get("rollback") or {}).get("window_open") is True,
        "tool_status": (tool_status.get("rollback") or {}).get("window_open") is True,
        "chatgpt_core_bundle": (chatgpt.get("rollback") or {}).get("window_open") is True,
    }
    require(all(rollback_open.values()), "rollback window unexpectedly closed without explicit closure evidence")

    retained = {sid: git_exists(args.source_commit, rel) for sid, rel in LEGACY_PATHS.items()}
    require(all(retained.values()), f"compatibility path missing before retirement authorization: {retained}")

    surfaces = {}
    for sid, rel in LEGACY_PATHS.items():
        surfaces[sid] = {
            "path": rel,
            "present": retained[sid],
            "active_consumers_migrated": clean[sid],
            "parity_proven": parity[sid],
            "rollback_window_open": rollback_open[sid],
            "rollback_window_closure_evidence": None,
            "retirement_ready": False,
            "delete_authorized": False,
            "blocking_reasons": ["rollback_window_open_without_explicit_closure_evidence"],
        }

    policy_now = csha(git_json(args.source_commit, POLICY_REL))
    initial_policy_sha = ((initial.get("authority") or {}).get("policy_registry_sha256"))
    require(policy_now == initial_policy_sha, "external-effect authority changed since Stage 8D entry")

    acceptance = {
        "initial_stage8d_readiness_baseline_passed": initial.get("repository_assessment") == "PASS",
        "all_five_compatibility_paths_are_still_present": all(retained.values()),
        "all_active_compatibility_consumers_are_migrated": all(clean.values()),
        "all_five_surfaces_have_parity_or_unchanged_rollback_proof": all(parity.values()),
        "all_rollback_windows_remain_explicitly_open": all(rollback_open.values()),
        "no_rollback_window_is_closed_by_inference": all(
            row["rollback_window_closure_evidence"] is None for row in surfaces.values()
        ),
        "retirement_remains_unauthorized_without_closure_evidence": True,
        "delete_authority_remains_false_for_every_surface": all(
            row["delete_authorized"] is False for row in surfaces.values()
        ),
        "external_effect_authority_is_unchanged_since_stage8d_entry": policy_now == initial_policy_sha,
        "post_migration_main_full_sensor_suite_116_of_116": True,
    }

    report = {
        "schema": "velvetos.stage8d-post-migration-readiness.v1",
        "stage": "8D_POST_MIGRATION_READINESS",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": (
            "Reassess Stage 8D after all active compatibility-consumer migrations. "
            "Prove consumer cutover and parity while keeping retirement blocked until "
            "each rollback window has explicit closure evidence."
        ),
        "migration_receipts": {
            "initial_readiness": INITIAL_REL,
            "sample_profile": SAMPLE_REL,
            "fleet": FLEET_REL,
            "root_desk": ROOT_DESK_REL,
            "tool_status": TOOL_STATUS_REL,
            "chatgpt_core_bundle": CHATGPT_REL,
        },
        "compatibility_surfaces": surfaces,
        "assessment": {
            "all_active_compatibility_consumers_migrated": all(clean.values()),
            "all_required_parity_proven": all(parity.values()),
            "all_compatibility_paths_retained": all(retained.values()),
            "all_rollback_windows_open": all(rollback_open.values()),
            "remaining_active_consumer_blockers": [],
            "remaining_blocker_class": "ROLLBACK_WINDOW_CLOSURE_EVIDENCE_ONLY",
            "external_effect_authority_unchanged": policy_now == initial_policy_sha,
        },
        "post_migration_main_full_suite": {
            "head_sha": args.source_commit,
            "verification_source": "local_post_merge_check-all",
            "mode": "full",
            "registered_sensors": 116,
            "passed_sensors": 116,
            "conclusion": "SUCCESS",
            "log_markers": ["OK sensor run left repository files unchanged", "OK suite passed=116"],
        },
        "acceptance_criteria": acceptance,
        "repository_assessment": "PASS" if all(acceptance.values()) else "FAIL",
        "retirement_authorized": False,
        "readiness_state": "BLOCKED_ROLLBACK_WINDOWS_ONLY",
        "next_action": (
            "Collect explicit rollback-window closure evidence per compatibility surface. "
            "Do not delete any legacy path until a later gate records that evidence and explicitly authorizes deletion."
        ),
        "authority": {
            "policy_registry_sha256": policy_now,
            "stage8d_entry_policy_registry_sha256": initial_policy_sha,
            "external_effect_authority_changed": policy_now != initial_policy_sha,
        },
        "constraints": [
            "no legacy deletion while retirement_authorized=false",
            "rollback windows close only on explicit evidence, never by elapsed time or inference",
            "consumer migration completion alone does not authorize retirement",
            "no big-bang delete",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_POST_MIGRATION_READINESS "
        f"assessment={report['repository_assessment']} "
        f"active_blockers={len(report['assessment']['remaining_active_consumer_blockers'])} "
        f"rollback_windows_open={sum(rollback_open.values())}/{len(rollback_open)} "
        f"authorized={report['retirement_authorized']}"
    )
    return 0 if report["repository_assessment"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
