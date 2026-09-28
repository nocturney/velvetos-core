#!/usr/bin/env python3
"""Read-only Stage 3 preflight and activation-receipt generator.

This script never changes CI, branch rules, or selector mode. It can emit the
activation receipt only after supplied Stage 2 observation evidence satisfies
all fixed exit criteria.
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


def build_receipt(report: dict, config: dict, main_sha: str) -> dict:
    progress = report["progress"]
    misses = report.get("noncritical_misses") or []
    return {
        "schema": "velvetos.stage3-activation-receipt.v1",
        "stage": 3,
        "activation_gate": "PASS",
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
    print("OK stage3-preflight selftest gate=FAIL_CLOSED receipt=ELIGIBLE_ONLY")
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
    if args.observation_report:
        try:
            report = load(args.observation_report)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL invalid observation report: {exc}", file=sys.stderr)
            return 1
        blockers.extend(gate_blockers(report, config))
    elif args.emit_receipt or args.require_ready:
        blockers.append("OBSERVATION_REPORT_REQUIRED")

    blockers = sorted(set(blockers))
    ready = not blockers
    print(
        f"STAGE3_PREFLIGHT ready={str(ready).lower()} "
        f"mode={config.get('mode')} blockers={','.join(blockers) or 'none'}"
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
        payload = build_receipt(report, config, main_sha)
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
