#!/usr/bin/env python3
"""Risk policy + dead-letter discoverability. No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "vfops" / "risk-policy.json"
LAW = ROOT / "constitution" / "RISK.md"
QUEUE = ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json"
SCHEMA = ROOT / "packages" / "vfharness" / "dead-letter" / "schema.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (POLICY, LAW, QUEUE, SCHEMA):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    law = LAW.read_text(encoding="utf-8")
    for needle in ("GREEN", "YELLOW", "ORANGE", "RED", "weak-metrics", "Dead-letter"):
        if needle not in law and needle.replace("-", " ") not in law:
            if needle == "weak-metrics" and "מדדים חלשים" not in law:
                fail(f"RISK.md missing {needle}")
            elif needle != "weak-metrics":
                fail(f"RISK.md missing {needle}")

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    levels = policy.get("levels") or {}
    for color in ("GREEN", "YELLOW", "ORANGE", "RED"):
        if color not in levels:
            fail(f"risk-policy missing {color}")
    if not levels["GREEN"].get("execute"):
        fail("GREEN must execute")
    if not levels["YELLOW"].get("execute") or not levels["YELLOW"].get("brief"):
        fail("YELLOW must execute + brief")
    if levels["ORANGE"].get("execute") or not levels["ORANGE"].get("prepareOnly"):
        fail("ORANGE must prepare only")
    if not levels["RED"].get("escalate"):
        fail("RED must escalate")
    never = levels["RED"].get("neverFor") or []
    for need in ("weak-metrics", "ordinary-tool-outage-with-failover", "media-intake"):
        if need not in never:
            fail(f"RED.neverFor missing {need}")

    # Weak metrics are not Red
    if "weak-metrics" in (levels["RED"].get("onlyWhen") or []):
        fail("weak-metrics must not be in RED.onlyWhen")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema.get("required") or [])
    for need in (
        "actionId",
        "jobOrContentId",
        "attemptedTool",
        "time",
        "failureSummary",
        "retries",
        "fallbackAttempted",
        "currentState",
        "nextSafeAction",
        "riskColor",
        "christianRequired",
    ):
        if need not in required:
            fail(f"dead-letter schema missing required {need}")

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    if "items" not in queue:
        fail("dead-letter queue.json must have items[]")

    # Discoverability: list CLI exists
    cli = ROOT / "scripts" / "vf_dead_letter.py"
    if not cli.is_file():
        fail("missing vf_dead_letter.py")

    print("OK risk-policy + dead-letter")


if __name__ == "__main__":
    main()
