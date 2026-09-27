#!/usr/bin/env python3
"""Compare Stage 2 shadow selection with the authoritative full-suite result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "sensor-registry.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def append_summary(path: Path, report: dict) -> None:
    lines = [
        "### VelvetOS sensor shadow comparison",
        "",
        f"- Status: **{report['status']}**",
        f"- Full-suite failures: **{len(report['full_failures'])}**",
        f"- Selector misses: **{len(report['selector_misses'])}**",
        f"- Critical misses: **{len(report['critical_misses'])}**",
        "",
    ]
    if report["selector_misses"]:
        lines += [
            "<details><summary>Selector misses requiring classification</summary>",
            "",
            "```text",
            "\n".join(report["selector_misses"]),
            "```",
            "</details>",
            "",
        ]
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def compare(selection: dict, full: dict, registry: dict) -> dict:
    risk = {row["id"]: row.get("risk") for row in registry.get("sensors") or []}
    selected = set(selection.get("selected_sensor_ids") or [])
    full_by_id = {row["sensor_id"]: row for row in full.get("results") or []}
    full_failures = sorted(
        sid for sid, row in full_by_id.items()
        if row.get("status") != "PASS"
    )
    selector_misses = sorted(sid for sid in full_failures if sid not in selected)
    critical_misses = sorted(sid for sid in selector_misses if risk.get(sid) == "critical")

    if not full_by_id:
        status = "INCOMPLETE_FULL_RESULTS"
    elif critical_misses:
        status = "CRITICAL_MISS"
    elif selector_misses:
        status = "NONCRITICAL_MISS_REQUIRES_CLASSIFICATION"
    else:
        status = "NO_MISS"

    return {
        "schema": "velvetos.sensor-shadow-comparison.v1",
        "mode": "shadow",
        "status": status,
        "full_suite_fallback": selection.get("full_suite") is True,
        "full_failures": full_failures,
        "selector_misses": selector_misses,
        "critical_misses": critical_misses,
        "miss_classification": [
            {"sensor_id": sid, "classification": "UNCLASSIFIED_REQUIRES_REVIEW"}
            for sid in selector_misses
        ],
        "blocking_effect": "REPORT_ONLY",
    }


def selftest() -> int:
    registry = {"sensors": [
        {"id": "check-critical", "risk": "critical"},
        {"id": "check-domain", "risk": "high"},
        {"id": "check-other", "risk": "medium"},
    ]}
    full_pass = {"results": [
        {"sensor_id": "check-critical", "status": "PASS"},
        {"sensor_id": "check-domain", "status": "PASS"},
        {"sensor_id": "check-other", "status": "PASS"},
    ]}
    selection = {"selected_sensor_ids": ["check-critical", "check-domain"], "full_suite": False}
    if compare(selection, full_pass, registry)["status"] != "NO_MISS":
        print("FAIL shadow comparison pass case")
        return 1

    full_noncritical = {"results": [
        {"sensor_id": "check-critical", "status": "PASS"},
        {"sensor_id": "check-domain", "status": "PASS"},
        {"sensor_id": "check-other", "status": "FAIL"},
    ]}
    report = compare(selection, full_noncritical, registry)
    if report["status"] != "NONCRITICAL_MISS_REQUIRES_CLASSIFICATION" or report["selector_misses"] != ["check-other"]:
        print("FAIL shadow comparison noncritical miss case")
        return 1

    full_critical = {"results": [
        {"sensor_id": "check-critical", "status": "FAIL"},
        {"sensor_id": "check-domain", "status": "PASS"},
    ]}
    bad_selection = {"selected_sensor_ids": ["check-domain"], "full_suite": False}
    report = compare(bad_selection, full_critical, registry)
    if report["status"] != "CRITICAL_MISS" or report["critical_misses"] != ["check-critical"]:
        print("FAIL shadow comparison critical miss case")
        return 1

    print("OK sensor-shadow-comparison selftest cases=3 miss_detection=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", type=Path)
    ap.add_argument("--full-results", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return selftest()
    if not args.selection or not args.full_results or not args.output:
        ap.error("--selection, --full-results and --output are required")

    selection = load(args.selection)
    full = load(args.full_results)
    registry = load(REGISTRY)
    report = compare(selection, full, registry)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        append_summary(args.summary, report)
    print(
        f"SENSOR_SHADOW_COMPARISON status={report['status']} "
        f"full_failures={len(report['full_failures'])} "
        f"misses={len(report['selector_misses'])} critical_misses={len(report['critical_misses'])}"
    )
    print("SENSOR_SHADOW_COMPARISON_JSON " + json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
