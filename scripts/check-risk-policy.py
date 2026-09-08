#!/usr/bin/env python3
"""Risk policy mirrors + canonical dead-letter discoverability. No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR_POLICY = ROOT / "packages" / "vfops" / "risk-policy.json"
LAW_MIRROR = ROOT / "constitution" / "RISK.md"
CANONICAL_POLICY = ROOT / "office" / "control" / "POLICY.md"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
CANONICAL_DEAD = ROOT / "office" / "control" / "dead-letter.json"
HARNESS_QUEUE = ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json"
HARNESS_README = ROOT / "packages" / "vfharness" / "dead-letter" / "README.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (MIRROR_POLICY, LAW_MIRROR, CANONICAL_POLICY, CONTROL_PLANE, CANONICAL_DEAD, HARNESS_QUEUE, HARNESS_README):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    # Canonical policy body
    policy_md = CANONICAL_POLICY.read_text(encoding="utf-8")
    for needle in ("ירוק", "צהוב", "כתום", "אדום", "Don't Bother Christian"):
        if needle not in policy_md:
            fail(f"POLICY.md missing {needle}")

    # RISK.md is a short mirror
    law = LAW_MIRROR.read_text(encoding="utf-8")
    if "office/control/POLICY.md" not in law:
        fail("RISK.md must point to office/control/POLICY.md as SOURCE OF TRUTH")
    for needle in ("GREEN", "YELLOW", "ORANGE", "RED", "Dead-letter", "office/control/dead-letter.json"):
        if needle not in law:
            fail(f"RISK.md mirror missing {needle}")
    if "weak-metrics" not in law and "מדדים חלשים" not in law:
        fail("RISK.md missing weak-metrics / מדדים חלשים")

    # risk-policy.json is a mirror JSON
    policy = json.loads(MIRROR_POLICY.read_text(encoding="utf-8"))
    if policy.get("sourceOfTruth") != "office/control/POLICY.md":
        fail("risk-policy.json sourceOfTruth must be office/control/POLICY.md")
    if "control-plane.json" not in (policy.get("mirrorOf") or ""):
        fail("risk-policy.json must mirror control-plane.json#dontBotherChristian")
    levels = policy.get("levels") or {}
    for color in ("GREEN", "YELLOW", "ORANGE", "RED"):
        if color not in levels:
            fail(f"risk-policy mirror missing {color}")
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
    if "weak-metrics" in (levels["RED"].get("onlyWhen") or []):
        fail("weak-metrics must not be in RED.onlyWhen")

    # Canonical dead-letter store
    dead = json.loads(CANONICAL_DEAD.read_text(encoding="utf-8"))
    if "items" not in dead:
        fail("office/control/dead-letter.json must have items[]")

    # Harness queue is pointer only
    queue = json.loads(HARNESS_QUEUE.read_text(encoding="utf-8"))
    if queue.get("sourceOfTruth") != "office/control/dead-letter.json":
        fail("harness dead-letter/queue.json must be a pointer to office/control/dead-letter.json")
    if queue.get("items"):
        fail("harness dead-letter/queue.json must keep items=[] (not authoritative)")

    readme = HARNESS_README.read_text(encoding="utf-8")
    if "office/control/dead-letter.json" not in readme:
        fail("harness dead-letter README must declare SoT")

    # Old schema must not reclaim authority
    old_schema = ROOT / "packages" / "vfharness" / "dead-letter" / "schema.json"
    if old_schema.is_file():
        sch = json.loads(old_schema.read_text(encoding="utf-8"))
        if sch.get("required") and not sch.get("sourceOfTruth"):
            fail("dead-letter schema.json must not remain an authoritative store — delete or pointerize")

    cli = ROOT / "scripts" / "vf_dead_letter.py"
    if not cli.is_file():
        fail("missing vf_dead_letter.py")
    cli_txt = cli.read_text(encoding="utf-8")
    if "record_dead_letter" not in cli_txt or "vf_control_plane" not in cli_txt:
        fail("vf_dead_letter.py must wrap vf_control_plane.record_dead_letter")

    plane = json.loads(CONTROL_PLANE.read_text(encoding="utf-8"))
    if (plane.get("sourcesOfTruth") or {}).get("dead_letter") != "office/control/dead-letter.json":
        fail("control-plane sourcesOfTruth.dead_letter mismatch")
    if (plane.get("sourcesOfTruth") or {}).get("risk_policy") != "office/control/POLICY.md":
        # optional key — prefer present
        if "risk_policy" in (plane.get("sourcesOfTruth") or {}) and plane["sourcesOfTruth"]["risk_policy"] != "office/control/POLICY.md":
            fail("risk_policy SoT mismatch")

    print("OK risk-policy + dead-letter (POLICY.md canonical)")


if __name__ == "__main__":
    main()
