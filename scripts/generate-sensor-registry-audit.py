#!/usr/bin/env python3
"""Generate/check the Stage 2A sensor-registry audit report. Read-only except report write."""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
REGISTRY = POLICY_DIR / "sensor-registry.json"
REPORT = POLICY_DIR / "reports" / "stage2-sensor-registry-audit.json"
WORKFLOWS = ROOT / ".github" / "workflows"
SCRIPTS = ROOT / "scripts"
CHECK_RE = re.compile(r"(?:python3?|py)\s+(scripts/check-[a-z0-9-]+\.py)\b")
SUITE_RE = re.compile(r"(?:python3?|py)\s+scripts/check-all\.py\b")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sensor_subprocess_targets(path: Path) -> list[str]:
    """Find literal check-*.py subprocess targets; references alone are not nested execution."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            owner = func.value.id if isinstance(func.value, ast.Name) else ""
            if owner != "subprocess" or func.attr not in {"run", "Popen", "check_call", "check_output"}:
                continue
        else:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                value = child.value.replace("\\", "/")
                m = re.search(r"(?:^|/)(check-[a-z0-9-]+\.py)$", value)
                if m:
                    found.add("scripts/" + m.group(1))
    return sorted(found)


def workflow_invocations() -> list[dict]:
    rows: list[dict] = []
    for wf in sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")]):
        text = wf.read_text(encoding="utf-8")
        suite_present = bool(SUITE_RE.search(text))
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for match in CHECK_RE.finditer(line):
                sensor_path = match.group(1)
                if sensor_path == "scripts/check-all.py":
                    continue
                rows.append({
                    "workflow": wf.relative_to(ROOT).as_posix(),
                    "line": i,
                    "sensor_path": sensor_path,
                    "suite_runner_present": suite_present,
                    "potential_duplicate_with_suite_runner": suite_present,
                })
    return rows


def build() -> dict:
    data = load(REGISTRY)
    sensors = data.get("sensors") or []
    live = sorted(
        p.relative_to(ROOT).as_posix()
        for p in SCRIPTS.glob("check-*.py")
        if p.name != "check-all.py"
    )
    nested = []
    for row in sensors:
        path = ROOT / row["path"]
        targets = sensor_subprocess_targets(path)
        if targets:
            nested.append({"sensor_id": row["id"], "targets": targets})

    direct = workflow_invocations()
    duplicates = [row for row in direct if row["potential_duplicate_with_suite_runner"]]
    mapping_counts: dict[str, int] = {}
    fallback_counts: dict[str, int] = {}
    for row in sensors:
        mapping_counts[row["mapping_state"]] = mapping_counts.get(row["mapping_state"], 0) + 1
        fallback_counts[row["fallback_scope"]] = fallback_counts.get(row["fallback_scope"], 0) + 1

    return {
        "report": "stage2-sensor-registry-audit",
        "stage": "2A",
        "behavior_change": False,
        "suite_runner": data.get("suite_runner"),
        "registered_sensor_count": len(sensors),
        "live_sensor_count": len(live),
        "registry_matches_live": sorted(row["path"] for row in sensors) == live,
        "mapping_state_counts": dict(sorted(mapping_counts.items())),
        "fallback_scope_counts": dict(sorted(fallback_counts.items())),
        "dependency_edge_count": sum(len(row.get("depends_on") or []) for row in sensors),
        "sensors_with_dependencies": sum(bool(row.get("depends_on")) for row in sensors),
        "critical_always_on": sorted(
            row["id"] for row in sensors
            if row.get("fallback_scope") == "ALWAYS_ON"
        ),
        "broad_legacy_sensors": sorted(
            row["id"] for row in sensors
            if row.get("mapping_state") == "broad_legacy_baseline"
        ),
        "nested_sensor_invocations": nested,
        "workflow_direct_sensor_invocations": direct,
        "potential_duplicate_sensor_runs": duplicates,
        "duplicate_removal_stage": 3,
        "notes": [
            "Stage 2A records duplicates and nested execution; it does not remove or skip existing checks.",
            "Broad legacy mappings remain fail-broad and are not eligible for affected-only enforcement.",
            "Stage 2B selector shadowing must continue to run the full suite."
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = build()
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not REPORT.is_file() or REPORT.read_text(encoding="utf-8") != rendered:
            print("FAIL stage2 sensor audit report is stale")
            return 1
        print(
            f"OK stage2-sensor-audit sensors={data['registered_sensor_count']} "
            f"always_on={len(data['critical_always_on'])} broad={len(data['broad_legacy_sensors'])} "
            f"duplicate_candidates={len(data['potential_duplicate_sensor_runs'])}"
        )
        return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(rendered, encoding="utf-8")
    print(f"OK wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
