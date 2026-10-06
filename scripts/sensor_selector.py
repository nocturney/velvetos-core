#!/usr/bin/env python3
"""Deterministic affected-sensor selector for VelvetOS CI.

Stage 2 used this in shadow mode; Stage 3 uses it as the pull-request execution
selector. Unknown paths and broad harness/policy changes expand to FULL_SUITE.
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


def machine_write_class(paths: Iterable[str], full_suite: bool, config: dict) -> str:
    """Classify a machine-authored diff from its actual paths, never a caller hint."""
    if full_suite:
        return "AUTHORITY_SECURITY"
    routing = config.get("machine_write_routing") or {}
    state_patterns = routing.get("state_data_patterns") or []
    artifact_patterns = routing.get("domain_artifact_patterns") or []
    seen: set[str] = set()
    for path in paths:
        if any(matches(path, pattern) for pattern in state_patterns):
            seen.add("STATE_DATA")
        elif any(matches(path, pattern) for pattern in artifact_patterns):
            seen.add("DOMAIN_ARTIFACT")
        else:
            seen.add("CODE_CONTRACT")
    if "CODE_CONTRACT" in seen or not seen:
        return "CODE_CONTRACT"
    if "DOMAIN_ARTIFACT" in seen:
        return "DOMAIN_ARTIFACT"
    return "STATE_DATA"


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
    ownership_matches: dict[str, list[dict[str, str]]] = {}
    owned_paths: set[str] = set()
    broad_hits: list[dict[str, str]] = []
    neutral_hits: list[dict[str, str]] = []

    broad_patterns = config.get("broad_change_patterns") or []
    neutral_patterns = config.get("neutral_change_patterns") or []
    for path in paths:
        for pattern in broad_patterns:
            if matches(path, pattern):
                broad_hits.append({"path": path, "pattern": pattern})
        for pattern in neutral_patterns:
            if matches(path, pattern):
                neutral_hits.append({"path": path, "pattern": pattern})

    # Selection and coverage are deliberately separate:
    # - triggered_by/depends_on decide which sensors run;
    # - owns decides whether a path is actually mapped by a domain sensor.
    # Cross-cutting / ALWAYS_ON observers must never make a new path "known".
    for row in sensors:
        sid = row["id"]
        for field in ("triggered_by", "depends_on"):
            for pattern in row.get(field) or []:
                if pattern in by_id:
                    continue
                for path in paths:
                    if matches(path, pattern):
                        candidate.add(sid)
                        matches_by_sensor.setdefault(sid, []).append({
                            "path": path,
                            "field": field,
                            "pattern": pattern,
                        })
        if row.get("fallback_scope") == "ALWAYS_ON" or row.get("mapping_state") != "mapped":
            continue
        for pattern in row.get("owns") or []:
            for path in paths:
                if matches(path, pattern):
                    owned_paths.add(path)
                    ownership_matches.setdefault(sid, []).append({
                        "path": path,
                        "pattern": pattern,
                    })

    candidate = expand_sensor_dependencies(candidate, by_id)
    broad_paths = {row["path"] for row in broad_hits}
    neutral_paths = {row["path"] for row in neutral_hits}
    unmatched = sorted(set(paths) - owned_paths - broad_paths - neutral_paths)
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
    machine_class = machine_write_class(paths, full_suite, config)
    post_push_full = set((config.get("machine_write_routing") or {}).get("post_push_full_suite_classes") or [])
    return {
        "schema": "velvetos.sensor-selection.v1",
        "mode": config.get("mode"),
        "full_suite": full_suite,
        "full_suite_reasons": sorted(set(reasons)),
        "changed_paths": paths,
        "broad_hits": broad_hits,
        "neutral_hits": neutral_hits,
        "owned_paths": sorted(owned_paths),
        "unmatched_paths": unmatched,
        "always_on_sensor_ids": sorted(always_on),
        "candidate_sensor_ids": sorted(candidate),
        "selected_sensor_ids": sorted(selected),
        "selected_sensor_paths": [by_id[sid]["path"] for sid in sorted(selected)],
        "selection_count": len(selected),
        "candidate_count": len(candidate),
        "total_sensor_count": len(sensors),
        "matches": {sid: rows for sid, rows in sorted(matches_by_sensor.items())},
        "ownership_matches": {sid: rows for sid, rows in sorted(ownership_matches.items())},
        "machine_write_class": machine_class,
        "post_push_full_suite_required": machine_class in post_push_full,
        "shadow_exit_criteria": config.get("shadow_exit") or {},
    }


def append_summary(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"### VelvetOS sensor selector - {result.get('mode') or 'unknown'}",
        "",
        f"- Full-suite fallback: **{str(result['full_suite']).lower()}**",
        f"- Candidate sensors: **{result['candidate_count']} / {result['total_sensor_count']}**",
        f"- Effective selected sensors: **{result['selection_count']} / {result['total_sensor_count']}**",
        f"- Reasons: {', '.join(result['full_suite_reasons']) or 'none'}",
        f"- Unknown paths: {len(result['unmatched_paths'])}",
        f"- Owned paths: {len(result.get('owned_paths') or [])}",
        f"- Neutral paths: {len(result.get('neutral_hits') or [])}",
        f"- Machine-write class: **{result.get('machine_write_class')}**",
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
                "owns": ["scripts/check-critical.py"],
                "triggered_by": ["**/*.py", "scripts/check-critical.py"],
                "depends_on": [],
                "fallback_scope": "ALWAYS_ON",
                "mapping_state": "mapped",
            },
            {
                "id": "check-copy",
                "path": "scripts/check-copy.py",
                "owns": ["packages/copy/**", "scripts/check-copy.py", "scripts/copy_engine.py"],
                "triggered_by": ["packages/copy/**", "scripts/check-copy.py", "scripts/copy_engine.py"],
                "depends_on": [],
                "fallback_scope": "FULL_SUITE",
                "mapping_state": "mapped",
            },
        ]
    }
    config = {
        "mode": "shadow",
        "unknown_path_behavior": "FULL_SUITE",
        "broad_change_patterns": ["packages/policy/schema/**", "scripts/sensor_selector.py"],
        "neutral_change_patterns": ["CHANGELOG.md"],
        "machine_write_routing": {
            "state_data_patterns": ["state/**"],
            "domain_artifact_patterns": ["artifacts/**"],
            "post_push_full_suite_classes": ["AUTHORITY_SECURITY"],
        },
        "shadow_exit": {"minimum_pull_requests": 20},
    }
    cases = [
        (["packages/copy/a.md"], False, ["check-copy", "check-critical"], "CODE_CONTRACT"),
        (["scripts/copy_engine.py"], False, ["check-copy", "check-critical"], "CODE_CONTRACT"),
        (["packages/policy/schema/x.json"], True, ["check-copy", "check-critical"], "AUTHORITY_SECURITY"),
        (["new/unknown.txt"], True, ["check-copy", "check-critical"], "AUTHORITY_SECURITY"),
        # ALWAYS_ON syntax observes this path, but does not own it; unknown executable remains fail-broad.
        (["scripts/new_runtime.py"], True, ["check-copy", "check-critical"], "AUTHORITY_SECURITY"),
        # A new workflow is likewise unknown even if cross-cutting workflow observers would run in production.
        ([".github/workflows/new-writer.yml"], True, ["check-copy", "check-critical"], "AUTHORITY_SECURITY"),
        # Explicitly neutral documentation can run core-only without becoming unknown.
        (["CHANGELOG.md"], False, ["check-critical"], "CODE_CONTRACT"),
        (["state/cache.json"], False, ["check-copy", "check-critical"], "STATE_DATA"),
        (["artifacts/report.json"], False, ["check-copy", "check-critical"], "DOMAIN_ARTIFACT"),
        # Mixed diffs may only move upward in risk; callers cannot downgrade them.
        (["state/cache.json", "artifacts/report.json"], False, ["check-copy", "check-critical"], "DOMAIN_ARTIFACT"),
        (["state/cache.json", "packages/copy/a.md"], False, ["check-copy", "check-critical"], "CODE_CONTRACT"),
    ]
    # Synthetic domain owner covers state/artifact paths and must be selected for them.
    registry["sensors"][1]["owns"].extend(["state/**", "artifacts/**"])
    registry["sensors"][1]["triggered_by"].extend(["state/**", "artifacts/**"])
    for paths, full, selected, machine_class in cases:
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
        if first["machine_write_class"] != machine_class:
            print(f"FAIL selector machine class mismatch for {paths}: {first['machine_write_class']}", file=sys.stderr)
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
    if "check-runtime-doctor" not in production["candidate_sensor_ids"]:
        print("FAIL runtime receipt changes must select check-runtime-doctor", file=sys.stderr)
        return 1
    if "check-zero-cost-final-acceptance" in production["candidate_sensor_ids"]:
        print("FAIL Stage 4F runtime receipt changes must not directly select historical zero-cost acceptance", file=sys.stderr)
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

    marker_prefix = "SENSOR_SHADOW_SELECTION" if result.get("mode") == "shadow" else "SENSOR_SELECTION"
    print(
        f"{marker_prefix} full_suite={str(result['full_suite']).lower()} "
        f"candidate={result['candidate_count']} selected={result['selection_count']} "
        f"total={result['total_sensor_count']} class={result['machine_write_class']} "
        f"reasons={','.join(result['full_suite_reasons']) or 'none'}"
    )
    marker = {
        "schema": result["schema"],
        "mode": result["mode"],
        "full_suite": result["full_suite"],
        "full_suite_reasons": result["full_suite_reasons"],
        "changed_paths": result["changed_paths"],
        "unmatched_paths": result["unmatched_paths"],
        "neutral_hits": result.get("neutral_hits") or [],
        "machine_write_class": result["machine_write_class"],
        "post_push_full_suite_required": result["post_push_full_suite_required"],
        "candidate_sensor_ids": result["candidate_sensor_ids"],
        "selection_count": result["selection_count"],
        "total_sensor_count": result["total_sensor_count"],
    }
    if args.base:
        marker["base"] = args.base
        marker["head"] = args.head
    print(marker_prefix + "_JSON " + json.dumps(marker, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
