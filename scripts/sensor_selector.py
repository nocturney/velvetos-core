#!/usr/bin/env python3
"""Deterministic Stage 2 shadow selector for VelvetOS sensors.

This script never replaces the full suite in Stage 2. Unknown paths and broad
harness/policy changes expand to FULL_SUITE.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
DEFAULT_REGISTRY = POLICY_DIR / "sensor-registry.json"
DEFAULT_CONFIG = POLICY_DIR / "sensor-selection.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def glob_regex(pattern: str) -> re.Pattern[str]:
    """Repo-path glob: * is one segment, ** crosses segments."""
    out = ["^"]
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        ch = pattern[i]
        if ch == "*":
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def matches(path: str, pattern: str) -> bool:
    return bool(glob_regex(pattern).match(path.replace("\\", "/")))


def changed_paths(base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", base, head, "--"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return sorted({line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()})


def expand_sensor_dependencies(selected: set[str], rows: dict[str, dict]) -> set[str]:
    """Support sensor-id dependencies if introduced later; file dependencies are matched directly."""
    changed = True
    while changed:
        changed = False
        for sid in list(selected):
            for dep in rows[sid].get("depends_on") or []:
                if dep in rows and dep not in selected:
                    selected.add(dep)
                    changed = True
    return selected


def select_for_paths(paths: Iterable[str], registry: dict, config: dict) -> dict:
    paths = sorted({p.replace("\\", "/") for p in paths if p})
    sensors = [row for row in registry.get("sensors") or [] if isinstance(row, dict)]
    by_id = {row["id"]: row for row in sensors}
    always_on = {
        row["id"] for row in sensors
        if row.get("fallback_scope") == "ALWAYS_ON"
    }
    candidate = set(always_on)
    matches_by_sensor: dict[str, list[dict[str, str]]] = {}
    matched_paths: set[str] = set()
    broad_hits: list[dict[str, str]] = []

    broad_patterns = config.get("broad_change_patterns") or []
    for path in paths:
        for pattern in broad_patterns:
            if matches(path, pattern):
                broad_hits.append({"path": path, "pattern": pattern})
                matched_paths.add(path)

    for row in sensors:
        sid = row["id"]
        for field in ("triggered_by", "depends_on"):
            for pattern in row.get(field) or []:
                if pattern in by_id:
                    continue
                for path in paths:
                    if matches(path, pattern):
                        candidate.add(sid)
                        matched_paths.add(path)
                        matches_by_sensor.setdefault(sid, []).append({
                            "path": path,
                            "field": field,
                            "pattern": pattern,
                        })

    candidate = expand_sensor_dependencies(candidate, by_id)
    unmatched = sorted(set(paths) - matched_paths)
    reasons: list[str] = []
    full_suite = False
    if broad_hits:
        full_suite = True
        reasons.append("BROAD_CHANGE")
    if unmatched and config.get("unknown_path_behavior") == "FULL_SUITE":
        full_suite = True
        reasons.append("UNKNOWN_PATH")
    if any(row.get("mapping_state") != "mapped" for row in sensors):
        full_suite = True
        reasons.append("UNMAPPED_SENSOR_PRESENT")

    selected = set(by_id) if full_suite else candidate
    return {
        "schema": "velvetos.sensor-selection.v1",
        "mode": config.get("mode"),
        "full_suite": full_suite,
        "full_suite_reasons": sorted(set(reasons)),
        "changed_paths": paths,
        "broad_hits": broad_hits,
        "unmatched_paths": unmatched,
        "always_on_sensor_ids": sorted(always_on),
        "candidate_sensor_ids": sorted(candidate),
        "selected_sensor_ids": sorted(selected),
        "selected_sensor_paths": [by_id[sid]["path"] for sid in sorted(selected)],
        "selection_count": len(selected),
        "candidate_count": len(candidate),
        "total_sensor_count": len(sensors),
        "matches": {sid: rows for sid, rows in sorted(matches_by_sensor.items())},
        "shadow_exit_criteria": config.get("shadow_exit") or {},
    }


def append_summary(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "### VelvetOS sensor selector - shadow",
        "",
        f"- Full-suite fallback: **{str(result['full_suite']).lower()}**",
        f"- Candidate sensors: **{result['candidate_count']} / {result['total_sensor_count']}**",
        f"- Effective selected sensors: **{result['selection_count']} / {result['total_sensor_count']}**",
        f"- Reasons: {', '.join(result['full_suite_reasons']) or 'none'}",
        f"- Unknown paths: {len(result['unmatched_paths'])}",
        "",
        "<details><summary>Candidate sensor IDs</summary>",
        "",
        "```text",
        "\n".join(result["candidate_sensor_ids"]),
        "```",
        "</details>",
        "",
    ]
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def selftest() -> int:
    registry = {
        "sensors": [
            {
                "id": "check-critical",
                "path": "scripts/check-critical.py",
                "triggered_by": ["scripts/check-critical.py"],
                "depends_on": [],
                "fallback_scope": "ALWAYS_ON",
                "mapping_state": "mapped",
            },
            {
                "id": "check-copy",
                "path": "scripts/check-copy.py",
                "triggered_by": ["packages/copy/**", "scripts/check-copy.py"],
                "depends_on": ["scripts/copy_engine.py"],
                "fallback_scope": "FULL_SUITE",
                "mapping_state": "mapped",
            },
        ]
    }
    config = {
        "mode": "shadow",
        "unknown_path_behavior": "FULL_SUITE",
        "broad_change_patterns": ["packages/policy/schema/**", "scripts/sensor_selector.py"],
        "shadow_exit": {"minimum_pull_requests": 20},
    }
    cases = [
        (["packages/copy/a.md"], False, ["check-copy", "check-critical"]),
        (["scripts/copy_engine.py"], False, ["check-copy", "check-critical"]),
        (["packages/policy/schema/x.json"], True, ["check-copy", "check-critical"]),
        (["new/unknown.txt"], True, ["check-copy", "check-critical"]),
    ]
    for paths, full, selected in cases:
        first = select_for_paths(paths, registry, config)
        second = select_for_paths(reversed(paths), registry, config)
        if first != second:
            print(f"FAIL selector nondeterministic for {paths}", file=sys.stderr)
            return 1
        if first["full_suite"] is not full:
            print(f"FAIL selector fallback mismatch for {paths}: {first}", file=sys.stderr)
            return 1
        if first["selected_sensor_ids"] != selected:
            print(f"FAIL selector selection mismatch for {paths}: {first['selected_sensor_ids']}", file=sys.stderr)
            return 1
    if not matches("packages/copy/nested/x.md", "packages/copy/**"):
        print("FAIL ** glob must cross path segments", file=sys.stderr)
        return 1
    if matches("packages/copy/nested/x.md", "packages/*"):
        print("FAIL * glob must not cross path segments", file=sys.stderr)
        return 1
    production = select_for_paths(
        ["packages/vfharness/state/runtime/sderot-windows.json"],
        load_json(DEFAULT_REGISTRY),
        load_json(DEFAULT_CONFIG),
    )
    if "check-zero-cost-final-acceptance" not in production["candidate_sensor_ids"]:
        print("FAIL runtime receipt changes must select check-zero-cost-final-acceptance", file=sys.stderr)
        return 1
    print(f"OK sensor-selector selftest cases={len(cases)} deterministic=PASS unknown=FULL_SUITE broad=FULL_SUITE")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return selftest()
    if bool(args.base) != bool(args.head):
        ap.error("--base and --head must be supplied together")
    if not args.path and not args.base:
        ap.error("supply --base/--head or at least one --path")

    registry = load_json(args.registry)
    config = load_json(args.config)
    paths = list(args.path)
    if args.base:
        paths.extend(changed_paths(args.base, args.head))
    result = select_for_paths(paths, registry, config)
    if args.base:
        result["base"] = args.base
        result["head"] = args.head

    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.summary:
        append_summary(args.summary, result)

    print(
        f"SENSOR_SHADOW_SELECTION full_suite={str(result['full_suite']).lower()} "
        f"candidate={result['candidate_count']} selected={result['selection_count']} "
        f"total={result['total_sensor_count']} reasons={','.join(result['full_suite_reasons']) or 'none'}"
    )
    marker = {
        "schema": result["schema"],
        "mode": result["mode"],
        "full_suite": result["full_suite"],
        "full_suite_reasons": result["full_suite_reasons"],
        "changed_paths": result["changed_paths"],
        "unmatched_paths": result["unmatched_paths"],
        "candidate_sensor_ids": result["candidate_sensor_ids"],
        "selection_count": result["selection_count"],
        "total_sensor_count": result["total_sensor_count"],
    }
    if args.base:
        marker["base"] = args.base
        marker["head"] = args.head
    print("SENSOR_SHADOW_SELECTION_JSON " + json.dumps(marker, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
