#!/usr/bin/env python3
"""Read-only Stage 3 preflight and activation-receipt generator.

This script never changes CI, branch rules, or selector mode. It can emit the
activation receipt after supplied Stage 2 observation evidence satisfies the
exit criteria, including the narrowly scoped owner duration-only exception when configured.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
CONFIG = POLICY_DIR / "sensor-selection.json"
REGISTRY = POLICY_DIR / "sensor-registry.json"
CHECK_ALL = ROOT / "scripts" / "check-all.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_blockers(report: dict, config: dict) -> list[str]:
    progress = report.get("progress") or {}
    criteria = config.get("shadow_exit") or {}
    blockers: list[str] = []
    if report.get("schema") != "velvetos.sensor-shadow-observation.v1":
        blockers.append("OBSERVATION_SCHEMA_INVALID")
    if int(progress.get("observed_pull_requests") or 0) < int(criteria.get("minimum_pull_requests") or 0):
        blockers.append("MINIMUM_PULL_REQUESTS_NOT_MET")
    if float(progress.get("observation_days") or 0) < float(criteria.get("minimum_observation_days") or 0):
        blockers.append("MINIMUM_OBSERVATION_DAYS_NOT_MET")
    if int(progress.get("critical_misses") or 0) != 0:
        blockers.append("CRITICAL_MISS_PRESENT")
    if int(progress.get("unclassified_noncritical_misses") or 0) != 0:
        blockers.append("NONCRITICAL_MISS_UNCLASSIFIED")
    relevant_unfixed = [
        row for row in report.get("noncritical_misses") or []
        if row.get("classification") not in {"UNRELATED", "RELEVANT_MAPPING_FIXED"}
    ]
    if relevant_unfixed:
        blockers.append("RELEVANT_MISS_NOT_REPAIRED")
    if int(progress.get("incomplete_observations") or 0) != 0:
        blockers.append("INCOMPLETE_OBSERVATION_EVIDENCE")
    if int(progress.get("unresolved_runs") or 0) != 0:
        blockers.append("UNRESOLVED_PULL_REQUEST_ID")
    if progress.get("run_history_complete") is not True:
        blockers.append("RUN_HISTORY_INCOMPLETE")
    if progress.get("deterministic_replay_pass") is not True:
        blockers.append("DETERMINISTIC_REPLAY_FAILED")
    if criteria.get("rollback_mode") != "FULL_SUITE_REQUIRED":
        blockers.append("ROLLBACK_MODE_INVALID")
    gate = report.get("gate") or {}
    report_blockers = set(gate.get("blockers") or [])
    if report_blockers - set(blockers):
        blockers.append("REPORT_GATE_HAS_EXTRA_BLOCKERS")
    if not blockers and gate.get("eligible") is not True:
        blockers.append("REPORT_GATE_NOT_ELIGIBLE")
    if int(progress.get("noncritical_misses") or 0) != len(report.get("noncritical_misses") or []):
        blockers.append("NONCRITICAL_MISS_COUNT_MISMATCH")
    return sorted(set(blockers))


def apply_owner_duration_override(report: dict, config: dict, blockers: list[str]) -> tuple[list[str], dict | None]:
    """Allow only the owner-approved duration exception; every other exit invariant stays fail-closed."""
    stage3 = config.get("stage3_preparation") or {}
    override = stage3.get("activation_duration_override") or {}
    if not override:
        return blockers, None
    if blockers != ["MINIMUM_OBSERVATION_DAYS_NOT_MET"]:
        return blockers, None
    if override.get("type") != "OWNER_DURATION_ONLY" or override.get("criterion") != "minimum_observation_days":
        return blockers + ["OWNER_DURATION_OVERRIDE_INVALID"], None
    if override.get("authorized_by") != "owner" or not str(override.get("authorized_at") or "").strip():
        return blockers + ["OWNER_DURATION_OVERRIDE_INVALID"], None
    if override.get("requires_only_blocker") != "MINIMUM_OBSERVATION_DAYS_NOT_MET":
        return blockers + ["OWNER_DURATION_OVERRIDE_SCOPE_INVALID"], None

    progress = report.get("progress") or {}
    report_gate = report.get("gate") or {}
    if sorted(report_gate.get("blockers") or []) != ["MINIMUM_OBSERVATION_DAYS_NOT_MET"]:
        return blockers + ["OWNER_DURATION_OVERRIDE_REPORT_SCOPE_MISMATCH"], None
    if float(progress.get("observation_days") or 0) < float(override.get("minimum_observed_days") or 0):
        return blockers + ["OWNER_DURATION_OVERRIDE_EVIDENCE_FLOOR_NOT_MET"], None
    if int(progress.get("observed_pull_requests") or 0) < int(override.get("minimum_observed_pull_requests") or 0):
        return blockers + ["OWNER_DURATION_OVERRIDE_EVIDENCE_FLOOR_NOT_MET"], None
    if override.get("requires_zero_critical_misses") is not True or int(progress.get("critical_misses") or 0) != 0:
        return blockers + ["OWNER_DURATION_OVERRIDE_CRITICAL_MISS"], None
    if override.get("requires_zero_unclassified_noncritical_misses") is not True or int(progress.get("unclassified_noncritical_misses") or 0) != 0:
        return blockers + ["OWNER_DURATION_OVERRIDE_UNCLASSIFIED_MISS"], None
    if override.get("requires_zero_incomplete_observations") is not True or int(progress.get("incomplete_observations") or 0) != 0:
        return blockers + ["OWNER_DURATION_OVERRIDE_INCOMPLETE_EVIDENCE"], None
    if override.get("requires_run_history_complete") is not True or progress.get("run_history_complete") is not True:
        return blockers + ["OWNER_DURATION_OVERRIDE_HISTORY_INCOMPLETE"], None
    if override.get("requires_deterministic_replay_pass") is not True or progress.get("deterministic_replay_pass") is not True:
        return blockers + ["OWNER_DURATION_OVERRIDE_REPLAY_FAILED"], None
    return [], {
        "type": override.get("type"),
        "criterion": override.get("criterion"),
        "authorized_by": override.get("authorized_by"),
        "authorized_at": override.get("authorized_at"),
        "reason": override.get("reason"),
        "minimum_observed_days": override.get("minimum_observed_days"),
        "minimum_observed_pull_requests": override.get("minimum_observed_pull_requests"),
        "original_blocker": "MINIMUM_OBSERVATION_DAYS_NOT_MET",
    }


def preparation_blockers(config: dict) -> list[str]:
    stage3 = config.get("stage3_preparation") or {}
    blockers: list[str] = []
    if config.get("mode") != "shadow":
        blockers.append("SELECTOR_NOT_SHADOW")
    if stage3.get("state") != "PREPARED_NOT_ACTIVE":
        blockers.append("STAGE3_PREPARATION_STATE_INVALID")
    if stage3.get("activation_requires_shadow_exit_eligible") is not True:
        blockers.append("ACTIVATION_GATE_NOT_REQUIRED")
    if stage3.get("pull_request_execution") != "SELECTED_SUITE":
        blockers.append("PR_TARGET_NOT_SELECTED_SUITE")
    if stage3.get("main_push_execution") != "FULL_SUITE":
        blockers.append("MAIN_PUSH_TARGET_NOT_FULL_SUITE")
    if stage3.get("critical_always_on_preserved") is not True:
        blockers.append("CRITICAL_ALWAYS_ON_NOT_PRESERVED")
    if stage3.get("unknown_or_broad_change_behavior") != "FULL_SUITE":
        blockers.append("FAIL_BROAD_TARGET_MISSING")
    if stage3.get("rollback_mode") != "FULL_SUITE_REQUIRED":
        blockers.append("ROLLBACK_TARGET_INVALID")
    receipt = ROOT / str(stage3.get("activation_receipt") or "")
    if receipt.is_file():
        blockers.append("ACTIVATION_RECEIPT_ALREADY_PRESENT")
    if not CHECK_ALL.is_file() or "--selection" not in CHECK_ALL.read_text(encoding="utf-8"):
        blockers.append("SELECTED_SUITE_RUNNER_NOT_PREPARED")
    return sorted(set(blockers))


def build_receipt(report: dict, config: dict, main_sha: str, override: dict | None, observation_report_sha256: str) -> dict:
    progress = report["progress"]
    misses = report.get("noncritical_misses") or []
    return {
        "schema": "velvetos.stage3-activation-receipt.v1",
        "stage": 3,
        "activation_gate": "PASS_WITH_OWNER_DURATION_OVERRIDE" if override else "PASS",
        "prepared_main_sha": main_sha,
        "observation_generated_at": report.get("generated_at"),
        "observation_start": report.get("observation_start"),
        "observed_pull_requests": progress.get("observed_pull_requests"),
        "observed_runs": progress.get("observed_runs"),
        "observation_days": progress.get("observation_days"),
        "critical_misses": progress.get("critical_misses"),
        "noncritical_misses": len(misses),
        "noncritical_classifications": [
            {
                "run_id": row.get("run_id"),
                "pull_request": row.get("pull_request"),
                "sensor_id": row.get("sensor_id"),
                "classification": row.get("classification"),
            }
            for row in misses
        ],
        "deterministic_replay_pass": progress.get("deterministic_replay_pass"),
        "run_history_complete": progress.get("run_history_complete"),
        "owner_duration_override": override,
        "observation_report_sha256": observation_report_sha256,
        "rollback_mode": config["shadow_exit"]["rollback_mode"],
        "selector_config_sha256": sha256(CONFIG),
        "sensor_registry_sha256": sha256(REGISTRY),
        "stage3_preparation": config.get("stage3_preparation"),
    }


def selftest() -> int:
    config = {
        "mode": "shadow",
        "shadow_exit": {
            "minimum_pull_requests": 20,
            "minimum_observation_days": 7,
            "rollback_mode": "FULL_SUITE_REQUIRED",
        },
        "stage3_preparation": {
            "activation_duration_override": {
                "type": "OWNER_DURATION_ONLY",
                "criterion": "minimum_observation_days",
                "authorized_by": "owner",
                "authorized_at": "2026-10-03T15:41:56+03:00",
                "reason": "fixture",
                "minimum_observed_days": 5.8,
                "minimum_observed_pull_requests": 20,
                "requires_only_blocker": "MINIMUM_OBSERVATION_DAYS_NOT_MET",
                "requires_zero_critical_misses": True,
                "requires_zero_unclassified_noncritical_misses": True,
                "requires_zero_incomplete_observations": True,
                "requires_run_history_complete": True,
                "requires_deterministic_replay_pass": True,
            }
        },
    }
    good = {
        "schema": "velvetos.sensor-shadow-observation.v1",
        "progress": {
            "observed_pull_requests": 20,
            "observation_days": 7,
            "critical_misses": 0,
            "noncritical_misses": 0,
            "unclassified_noncritical_misses": 0,
            "incomplete_observations": 0,
            "unresolved_runs": 0,
            "run_history_complete": True,
            "deterministic_replay_pass": True,
        },
        "noncritical_misses": [],
        "gate": {"eligible": True, "blockers": []},
    }
    if gate_blockers(good, config):
        print("FAIL stage3 preflight rejected eligible fixture", file=sys.stderr)
        return 1
    bad = json.loads(json.dumps(good))
    bad["progress"]["critical_misses"] = 1
    if "CRITICAL_MISS_PRESENT" not in gate_blockers(bad, config):
        print("FAIL stage3 preflight accepted critical miss", file=sys.stderr)
        return 1
    bad = json.loads(json.dumps(good))
    bad["progress"]["run_history_complete"] = False
    if "RUN_HISTORY_INCOMPLETE" not in gate_blockers(bad, config):
        print("FAIL stage3 preflight accepted incomplete history", file=sys.stderr)
        return 1
    duration_only = json.loads(json.dumps(good))
    duration_only["progress"]["observation_days"] = 5.9
    duration_only["gate"] = {"eligible": False, "blockers": ["MINIMUM_OBSERVATION_DAYS_NOT_MET"]}
    remaining, applied = apply_owner_duration_override(duration_only, config, gate_blockers(duration_only, config))
    if remaining or not applied:
        print("FAIL stage3 preflight rejected owner duration-only override fixture", file=sys.stderr)
        return 1
    duration_only["progress"]["critical_misses"] = 1
    if apply_owner_duration_override(duration_only, config, gate_blockers(duration_only, config))[1] is not None:
        print("FAIL stage3 preflight override bypassed critical miss", file=sys.stderr)
        return 1
    print("OK stage3-preflight selftest gate=FAIL_CLOSED duration_override=OWNER_ONLY receipt=AUDITABLE")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observation-report", type=Path)
    ap.add_argument("--emit-receipt", type=Path)
    ap.add_argument("--main-sha", default="")
    ap.add_argument("--require-ready", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return selftest()

    config = load(CONFIG)
    prep = preparation_blockers(config)
    blockers = list(prep)
    report = None
    applied_override = None
    if args.observation_report:
        try:
            report = load(args.observation_report)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL invalid observation report: {exc}", file=sys.stderr)
            return 1
        gate_issues = gate_blockers(report, config)
        gate_issues, applied_override = apply_owner_duration_override(report, config, gate_issues)
        blockers.extend(gate_issues)
    elif args.emit_receipt or args.require_ready:
        blockers.append("OBSERVATION_REPORT_REQUIRED")

    blockers = sorted(set(blockers))
    ready = not blockers
    print(
        f"STAGE3_PREFLIGHT ready={str(ready).lower()} "
        f"mode={config.get('mode')} blockers={','.join(blockers) or 'none'} "
        f"owner_duration_override={str(bool(applied_override)).lower()}"
    )

    if args.emit_receipt:
        configured_receipt = ROOT / str((config.get("stage3_preparation") or {}).get("activation_receipt") or "")
        if args.emit_receipt.resolve() != configured_receipt.resolve():
            print(f"FAIL activation receipt path must be {configured_receipt}", file=sys.stderr)
            return 2
        if not ready or report is None:
            print("FAIL activation receipt requires an eligible preflight", file=sys.stderr)
            return 2
        main_sha = args.main_sha.strip().lower()
        if len(main_sha) != 40 or any(ch not in "0123456789abcdef" for ch in main_sha):
            print("FAIL --main-sha must be a full 40-character Git SHA", file=sys.stderr)
            return 2
        payload = build_receipt(
            report,
            config,
            main_sha,
            applied_override,
            sha256(args.observation_report),
        )
        args.emit_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.emit_receipt.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"STAGE3_ACTIVATION_RECEIPT {args.emit_receipt}")

    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
