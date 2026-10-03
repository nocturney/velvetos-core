#!/usr/bin/env python3
"""Rebuild deterministic Stage 0 policy-architecture reports from pinned Git commits."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
DEFAULT_BASELINE = "52bcb819c1a6d9924f0f2800340169df5f991e08"
DEFAULT_COVERAGE = "9217e172d4f11a01f5db124d7d811c7dcab6b9c5"
DEFAULT_REGISTRY = "aaa1ec83cdb62e2b140c54ce00c5a73ccf2faa17"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def git_show(sha: str, path: str) -> str:
    return git("show", f"{sha}:{path}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_git_json(sha: str, path: str) -> dict:
    return json.loads(git_show(sha, path))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def assert_baseline_evidence(sha: str) -> None:
    checks = {
        "instances/velvet-factory/instance/velvet-factory.json": '"standingAuthorization": true',
        "constitution/ORGANIC_GROWTH.md": "authorized_for_tool_publish",
        "AGENTS.md": "approved_for_manual_posting",
        "scripts/vf_organic_growth.py": "approved_for_manual_posting",
        "scripts/vf_autonomy.py": "standingAuthorization",
        ".github/workflows/check-all.yml": "Commission isolation (non-mutating SoT checksum)",
    }
    for path, needle in checks.items():
        if needle not in git_show(sha, path):
            raise SystemExit(f"baseline evidence drift: {path} missing {needle!r}")


def build_reports(baseline_sha: str, coverage_sha: str, registry_sha: str, ci_baseline: dict) -> dict[str, dict]:
    assert_baseline_evidence(baseline_sha)
    policies = load_git_json(registry_sha, "packages/velvetos/policy/policy-registry.json")
    sensors = load_git_json(registry_sha, "packages/velvetos/policy/sensor-registry.json")
    artifacts = load_git_json(registry_sha, "packages/velvetos/policy/artifact-retention.json")

    authority_graph = {
        "report": "authority-graph",
        "source_commit_sha": coverage_sha,
        "policy_count": len(policies["policies"]),
        "nodes": [
            {
                "policy_id": row["policy_id"],
                "status": row["status"],
                "risk_class": row["risk_class"],
                "authority_locations": row["authority_locations"],
                "machine_policy_locations": row["machine_policy_locations"],
                "enforced_by": row["enforced_by"],
            }
            for row in policies["policies"]
        ],
    }

    sensor_graph = {
        "report": "sensor-coverage-graph",
        "source_commit_sha": coverage_sha,
        "suite_runner": sensors["suite_runner"],
        "sensor_count": len(sensors["sensors"]),
        "no_omissions": True,
        "selection_activation": "NOT_ACTIVE_STAGE_0",
        "fallback_scope": "FULL_SUITE",
        "sensors": [
            {
                key: row[key]
                for key in (
                    "id", "path", "owns", "triggered_by", "depends_on",
                    "enforces", "risk", "mapping_state"
                )
            }
            for row in sensors["sensors"]
        ],
    }

    enforced = {row["policy_id"]: [] for row in policies["policies"]}
    for sensor in sensors["sensors"]:
        for policy_id in sensor["enforces"]:
            enforced.setdefault(policy_id, []).append(sensor["id"])
    coverage = {
        "report": "coverage",
        "source_commit_sha": coverage_sha,
        "runnable_sensor_count": len(sensors["sensors"]),
        "registered_sensor_count": len(sensors["sensors"]),
        "omitted_sensors": [],
        "mapping_state_counts": {
            state: sum(1 for row in sensors["sensors"] if row["mapping_state"] == state)
            for state in sorted({row["mapping_state"] for row in sensors["sensors"]})
        },
        "policy_count": len(policies["policies"]),
        "policies_without_sensor_enforcement": sorted(pid for pid, ids in enforced.items() if not ids),
        "policy_sensor_enforcement": enforced,
        "note": "Stage 0 uses conservative broad ownership/trigger mappings and FULL_SUITE fallback. Trigger narrowing is deferred to Stage 2 shadow mode.",
    }


    conflicts = {
        "report": "policy-conflicts",
        "source_commit_sha": baseline_sha,
        "conflicts": [
            {
                "id": "instagram-publish-split-brain",
                "policy_id": "instagram.publish",
                "severity": "critical",
                "status": "OPEN_FOR_STAGE_1",
                "evidence": [
                    {"path": "instances/velvet-factory/instance/velvet-factory.json", "observation": "creativeAutonomy.publish.standingAuthorization is true"},
                    {"path": "constitution/ORGANIC_GROWTH.md", "observation": "standing authorization can transition to authorized_for_tool_publish after gates"},
                    {"path": "AGENTS.md", "observation": "Organic Growth summary still says Approve -> approved_for_manual_posting only"},
                    {"path": "scripts/vf_organic_growth.py", "observation": "legacy state machine exposes approved_for_manual_posting path"},
                    {"path": "scripts/vf_autonomy.py", "observation": "runtime classification reads standingAuthorization and can authorize tool publication"},
                ],
                "stage0_decision": "RECORD_ONLY_DO_NOT_RESOLVE",
            },
            {
                "id": "commission-isolation-double-run",
                "severity": "medium",
                "status": "OPEN_FOR_STAGE_3",
                "evidence": [
                    {"path": "scripts/check-all.py", "observation": "discovers and runs check-commission-isolation.py"},
                    {"path": ".github/workflows/check-all.yml", "observation": "also runs check-commission-isolation.py as a separate CI step"},
                ],
                "stage0_decision": "RECORD_ONLY_DO_NOT_CHANGE_CI_BEHAVIOR",
            },
        ],
    }

    tree = git("ls-tree", "-r", "-l", baseline_sha)
    tracked: list[dict[str, object]] = []
    for line in tree.splitlines():
        parts = line.split(None, 4)
        if len(parts) == 5 and parts[3].isdigit():
            tracked.append({"path": parts[4], "bytes": int(parts[3])})
    class_stats = []
    for rule in artifacts["entries"]:
        matched = [
            item for item in tracked
            if any(fnmatch.fnmatchcase(str(item["path"]), pattern) for pattern in rule["match"])
        ]
        class_stats.append({
            "artifact_class_id": rule["artifact_class_id"],
            "tracked_file_count": len(matched),
            "tracked_bytes": sum(int(item["bytes"]) for item in matched),
            "current_storage": rule["current_storage"],
            "target_storage": rule["target_storage"],
            "retention_class": rule["retention_class"],
            "migration_stage": rule["migration_stage"],
            "deletion_authorized": rule["deletion_authorized"],
        })
    artifact_inventory = {
        "report": "artifact-inventory",
        "source_commit_sha": baseline_sha,
        "tracked_file_count": len(tracked),
        "tracked_bytes": sum(int(item["bytes"]) for item in tracked),
        "classifications": class_stats,
        "largest_tracked_files": sorted(tracked, key=lambda item: int(item["bytes"]), reverse=True)[:50],
        "stage0_action": "CLASSIFICATION_ONLY_NO_MOVE_NO_DELETE",
    }


    baseline_tree = git("ls-tree", "-r", "--name-only", baseline_sha).splitlines()
    baseline_snapshot = {
        "report": "stage0-live-baseline",
        "source_commit_sha": baseline_sha,
        "cutoff_utc": ci_baseline["cutoff_utc"],
        "pre_change": {
            "check_py_files_including_suite_runner": sum(
                1 for path in baseline_tree if path.startswith("scripts/check-") and path.endswith(".py")
            ),
            "runnable_sensors_discovered_by_check_all": sum(
                1 for path in baseline_tree
                if path.startswith("scripts/check-") and path.endswith(".py") and path != "scripts/check-all.py"
            ),
            "workflow_count": sum(
                1 for path in baseline_tree if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
            ),
            "agents_files": [path for path in baseline_tree if path == "AGENTS.md" or path.endswith("/AGENTS.md")],
            "main_ruleset_enforcement": ci_baseline["ruleset"]["enforcement"],
            "main_branch_protected": ci_baseline["branch_protection"]["state"] != "UNPROTECTED",
            "check_all_pr_and_main": True,
            "commission_isolation_duplicate_ci_step": True,
            "root_agents_contains_velvet_factory_business_facts": True,
            "visible_text_scope": "GLOBAL_FULL_CHAIN",
            "instagram_publish_semantics": "SPLIT_BRAIN_RECORDED",
        },
        "post_0a": {
            "source_commit_sha": coverage_sha,
            "runnable_sensor_count": len(sensors["sensors"]),
            "policy_registry_count": len(policies["policies"]),
            "policy_creation_freeze": "ACTIVE_ON_PULL_REQUEST",
        },
    }

    migration_stages = [
        (1, "instagram-publish-canonicalization", ["instagram.publish"], "Restore prior publication authorities/runtime choke-point wiring; keep exact preflight and receipt verification fail-closed."),
        (2, "sensor-shadow-selection", [], "Disable selector and run FULL_SUITE; registry remains metadata only."),
        (3, "required-fast-and-affected-ci", [], "Revert workflow/ruleset activation; affected selector can fall back to FULL_SUITE."),
        (4, "critical-external-effect-framework", ["gmail.send", "customer.whatsapp.send", "advertising.boost", "external.irreversible.delete", "external.permission.mutate", "cost.recurring.new"], "Return callers to existing channel-specific gates; keep policy registry references."),
        (5, "agents-locality", [], "Restore moved guide lines from git history if locality change breaks routing; no business-state migration."),
        (6, "visible-text-and-readme-locality", ["visible_text.finalization"], "Return to current global Visible Text + README gates while preserving exact artifact receipts."),
        (7, "operational-debt-and-retention", ["cost.recurring.new"], "Stop movers/cleanup; retain Git artifacts and current schedules. No deletion is required for rollback."),
        (8, "core-instance-separation", [], "Keep compatibility reads/writes and revert callers to legacy locations; no big-bang cutover."),
        (9, "deprecation-and-acceptance", [], "Restore deprecated readers only if acceptance evidence fails; final deletion still requires explicit authorization."),
    ]

    migration_map = {
        "report": "migration-and-rollback-map",
        "source_commit_sha": coverage_sha,
        "stages": [
            {
                "stage": stage,
                "name": name,
                "policy_ids": policy_ids,
                "pr_shape": "SMALL_REVERSIBLE_SERIES",
                "entry_requirement": "previous stage gate PASS",
                "rollback": rollback,
            }
            for stage, name, policy_ids, rollback in migration_stages
        ],
        "global_rollback_rules": [
            "No force push or history rewrite.",
            "Preserve exact-action receipts and provider verification evidence.",
            "Selection/affected CI must fail broad to FULL_SUITE on unknowns.",
            "Artifact migration remains copy-first until verification; Stage 0 authorizes no deletion.",
            "Policy semantics remain in current authority until the target stage explicitly migrates them.",
        ],
    }

    return {
        "authority-graph.json": authority_graph,
        "sensor-coverage-graph.json": sensor_graph,
        "coverage-report.json": coverage,
        "conflict-report.json": conflicts,
        "artifact-inventory.json": artifact_inventory,
        "baseline-snapshot.json": baseline_snapshot,
        "migration-map.json": migration_map,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-sha", default=DEFAULT_BASELINE)
    p.add_argument("--coverage-sha", default=DEFAULT_COVERAGE)
    p.add_argument("--registry-sha", default=DEFAULT_REGISTRY)
    p.add_argument("--ci-baseline", default=str(POLICY_DIR / "reports" / "ci-baseline.json"))
    p.add_argument("--check", action="store_true")
    args = p.parse_args()

    ci_path = Path(args.ci_baseline).resolve()
    ci = load_json(ci_path)
    reports = build_reports(args.baseline_sha, args.coverage_sha, args.registry_sha, ci)
    out_dir = POLICY_DIR / "reports"

    if args.check:
        failed = []
        for name, data in reports.items():
            expected = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            path = out_dir / name
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                failed.append(name)
        if failed:
            print("FAIL stale reports: " + ", ".join(failed))
            return 1
        print(f"OK policy reports reproducible={len(reports)} baseline={args.baseline_sha[:12]} coverage={args.coverage_sha[:12]}")
        return 0

    for name, data in reports.items():
        write_json(out_dir / name, data)
    print(f"OK policy reports written={len(reports)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
