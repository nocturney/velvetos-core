#!/usr/bin/env python3
"""Behavioral proof for vfharness safe-ruling execution semantics."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "packages" / "vfharness" / "scripts" / "vf_graceful_escalation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("vf_graceful_escalation_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail():
    return False, None


def main() -> int:
    ladder = _load_module()
    original_state_dir = ladder.STATE_DIR
    try:
        return _run(ladder)
    finally:
        ladder.STATE_DIR = original_state_dir


def _ruling_entry(ladder, tmp: str, task: str) -> dict:
    history = json.loads((Path(tmp) / f"ladder-{task}.json").read_text(encoding="utf-8"))
    return next(row for row in history if row.get("rung") == ladder.Rung.SAFE_RULING)


def _run(ladder) -> int:
    with tempfile.TemporaryDirectory(prefix="vf-harness-ruling-") as tmp:
        ladder.STATE_DIR = Path(tmp)

        def safe_ruling():
            return (
                True,
                "continued-locally",
                {
                    "decision": "reuse the existing local default",
                    "why": "the choice is reversible and does not cross an authority gate",
                    "cost_if_wrong": "redo only this local step",
                },
            )

        ruled = ladder.run_ladder(
            "behavior-safe",
            pack="vfharness",
            attempt_fn=_fail,
            fallback_fn=_fail,
            downgrade_fn=_fail,
            max_retries=1,
            ruling_fn=safe_ruling,
            safe_to_rule=True,
        )
        assert ruled["rung"] == ladder.Rung.SAFE_RULING
        assert ruled["result"] == "continued-locally"
        assert ruled["ruling_text"].startswith("Ruling: ")
        assert ruled["ruling"]["cost_if_wrong"] == "redo only this local step"

        safe_history = json.loads(
            (Path(tmp) / "ladder-behavior-safe.json").read_text(encoding="utf-8")
        )
        safe_entries = [row for row in safe_history if row.get("rung") == ladder.Rung.SAFE_RULING]
        assert len(safe_entries) == 1
        assert safe_entries[0]["ok"] is True
        assert safe_entries[0]["ruling"]["decision"] == "reuse the existing local default"

        blocked_calls = {"count": 0}

        def blocked_ruling():
            blocked_calls["count"] += 1
            return True, "unsafe", {
                "decision": "unsafe",
                "why": "unsafe",
                "cost_if_wrong": "unsafe",
            }

        blocked = ladder.run_ladder(
            "behavior-blocked",
            pack="vfharness",
            attempt_fn=_fail,
            fallback_fn=_fail,
            downgrade_fn=_fail,
            max_retries=1,
            ruling_fn=blocked_ruling,
            safe_to_rule=False,
        )
        assert blocked["rung"] == ladder.Rung.ESCALATE
        assert blocked_calls["count"] == 0
        blocked_history = json.loads(
            (Path(tmp) / "ladder-behavior-blocked.json").read_text(encoding="utf-8")
        )
        blocked_entry = next(
            row for row in blocked_history if row.get("rung") == ladder.Rung.SAFE_RULING
        )
        assert blocked_entry["skipped"] is True
        assert blocked_entry["reason"] == "safe_to_rule guard not granted"

        def malformed_ruling():
            return True, "should-not-pass", {"decision": "missing fields"}

        malformed = ladder.run_ladder(
            "behavior-malformed",
            pack="vfharness",
            attempt_fn=_fail,
            fallback_fn=_fail,
            downgrade_fn=_fail,
            max_retries=1,
            ruling_fn=malformed_ruling,
            safe_to_rule=True,
        )
        assert malformed["rung"] == ladder.Rung.ESCALATE
        malformed_history = json.loads(
            (Path(tmp) / "ladder-behavior-malformed.json").read_text(encoding="utf-8")
        )
        malformed_entry = next(
            row for row in malformed_history if row.get("rung") == ladder.Rung.SAFE_RULING
        )
        assert malformed_entry["reason"] == "invalid_or_failed_ruling"

        valid_payload = {
            "decision": "valid-looking ruling",
            "why": "callback itself reported failure",
            "cost_if_wrong": "none",
        }

        def not_ok_ruling():
            return False, "should-not-pass", dict(valid_payload)

        def raising_ruling():
            raise RuntimeError("secret-payload-must-not-leak")

        def list_ruling():
            return [True, "should-not-pass", dict(valid_payload)]

        def short_tuple_ruling():
            return True, "should-not-pass"

        def none_ruling():
            return None

        failure_cases = {
            "behavior-not-ok": not_ok_ruling,
            "behavior-raises": raising_ruling,
            "behavior-list": list_ruling,
            "behavior-short-tuple": short_tuple_ruling,
            "behavior-none": none_ruling,
        }
        for task, fn in failure_cases.items():
            outcome = ladder.run_ladder(
                task,
                pack="vfharness",
                attempt_fn=_fail,
                fallback_fn=_fail,
                downgrade_fn=_fail,
                max_retries=1,
                ruling_fn=fn,
                safe_to_rule=True,
            )
            assert outcome["rung"] == ladder.Rung.ESCALATE, task
            assert outcome.get("result") != "should-not-pass", task
            entry = _ruling_entry(ladder, tmp, task)
            assert entry["ok"] is False, task
            assert "secret-payload-must-not-leak" not in json.dumps(entry), task

    print("OK vfharness-execution-discipline safe-ruling behavior=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
