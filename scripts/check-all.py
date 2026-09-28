#!/usr/bin/env python3
"""Run VelvetOS computational HQ sensors. No network. No send.

Default behavior remains the authoritative full suite. Stage 3 can later opt in
to an exact selector output with --selection; that path is dormant until the CI
workflow explicitly uses it after the Stage 2 exit gate passes.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SENSOR_REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "sensor-registry.json"
SKIP = {"check-all.py"}


def git_dirty_state() -> dict[str, bytes] | None:
    """Return {path: current bytes or b''} for git-visible changes, or None without git."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    state: dict[str, bytes] = {}
    for line in proc.stdout.splitlines():
        rel = line[3:].split(" -> ")[-1].strip().strip('"')
        path = ROOT / rel
        try:
            state[rel] = path.read_bytes() if path.is_file() else b""
        except OSError:
            state[rel] = b""
    return state


def discover_checks() -> dict[str, Path]:
    return {
        path.stem: path
        for path in sorted(SCRIPTS.glob("check-*.py"))
        if path.name not in SKIP
    }


def always_on_sensor_ids() -> set[str]:
    registry = json.loads(SENSOR_REGISTRY.read_text(encoding="utf-8"))
    return {
        str(row["id"])
        for row in registry.get("sensors") or []
        if isinstance(row, dict) and row.get("fallback_scope") == "ALWAYS_ON"
    }


def select_checks(
    all_checks: dict[str, Path],
    selection: dict | None,
    required_always_on: set[str] | None = None,
) -> tuple[list[Path], str]:
    if selection is None:
        return list(all_checks.values()), "full"
    sensor_ids = selection.get("selected_sensor_ids")
    if not isinstance(sensor_ids, list) or not sensor_ids:
        raise ValueError("selection must contain non-empty selected_sensor_ids")
    normalized = [str(sensor_id) for sensor_id in sensor_ids]
    if len(normalized) != len(set(normalized)):
        raise ValueError("selection contains duplicate sensor ids")
    selected = set(normalized)
    unknown = sorted(selected - set(all_checks))
    if unknown:
        raise ValueError(f"selection references unknown sensors: {unknown}")
    if selection.get("total_sensor_count") not in {None, len(all_checks)}:
        raise ValueError("selection total_sensor_count does not match live sensor count")
    required = required_always_on or set()
    missing_required = sorted(required - selected)
    if missing_required:
        raise ValueError(f"selection omits ALWAYS_ON sensors: {missing_required}")
    if selection.get("full_suite") is True and selected != set(all_checks):
        raise ValueError("FULL_SUITE selection does not contain every live sensor")
    return [all_checks[sensor_id] for sensor_id in normalized], "selected"


def selftest() -> int:
    fixture = {
        "check-a": Path("scripts/check-a.py"),
        "check-b": Path("scripts/check-b.py"),
    }
    selected, mode = select_checks(
        fixture,
        {"selected_sensor_ids": ["check-a", "check-b"], "total_sensor_count": 2},
        {"check-a"},
    )
    if mode != "selected" or [path.stem for path in selected] != ["check-a", "check-b"]:
        print("FAIL check-all selection fixture", file=sys.stderr)
        return 1
    selected, mode = select_checks(fixture, None)
    if mode != "full" or [path.stem for path in selected] != ["check-a", "check-b"]:
        print("FAIL check-all full-suite fixture", file=sys.stderr)
        return 1
    for bad in (
        {"selected_sensor_ids": []},
        {"selected_sensor_ids": ["check-a", "check-a"]},
        {"selected_sensor_ids": ["check-missing"]},
        {"selected_sensor_ids": ["check-a"], "total_sensor_count": 3},
        {"selected_sensor_ids": ["check-a"], "full_suite": True},
    ):
        try:
            select_checks(fixture, bad)
        except ValueError:
            continue
        print(f"FAIL check-all accepted invalid selection: {bad}", file=sys.stderr)
        return 1
    try:
        select_checks(fixture, {"selected_sensor_ids": ["check-b"]}, {"check-a"})
    except ValueError:
        pass
    else:
        print("FAIL check-all accepted selection missing ALWAYS_ON sensor", file=sys.stderr)
        return 1
    print("OK check-all selftest default=FULL_SUITE selected_input=EXACT always_on=REQUIRED fail_closed=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--selection", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return selftest()

    all_checks = discover_checks()
    if not all_checks:
        print("FAIL no check-*.py sensors found", file=sys.stderr)
        return 1
    selection = None
    if args.selection:
        try:
            selection = json.loads(args.selection.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL invalid selection file: {exc}", file=sys.stderr)
            return 1
    try:
        required_always_on = always_on_sensor_ids() if selection is not None else set()
        checks, suite_mode = select_checks(all_checks, selection, required_always_on)
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    failed: list[str] = []
    results: list[dict[str, object]] = []
    dirty_before = git_dirty_state()
    sensor_env = os.environ.copy()
    sensor_env["PYTHONUTF8"] = "1"
    sensor_env["PYTHONIOENCODING"] = "utf-8"
    # On Windows, isolate each sensor from check-all's console process group.
    # Some sensor dependencies emit console control events during teardown; without
    # a new process group those events can terminate the parent suite itself.
    sensor_creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    print(f"SENSORS {len(checks)} mode={suite_mode}")
    for path in checks:
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            env=sensor_env,
            creationflags=sensor_creationflags,
        )
        duration = round(time.perf_counter() - started, 3)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        results.append({
            "sensor_id": path.stem,
            "path": path.relative_to(ROOT).as_posix(),
            "returncode": proc.returncode,
            "duration_seconds": duration,
            "status": "PASS" if proc.returncode == 0 else "FAIL",
        })
        if proc.returncode == 0:
            print(f"PASS {path.name}  {out}")
        else:
            failed.append(path.name)
            detail = err or out or f"exit {proc.returncode}"
            print(f"FAIL {path.name}  {detail}", file=sys.stderr)

    # Sensors must only read. Report (do not fail on) any git-visible file the run changed,
    # so a routine never commits sensor side effects by accident.
    dirty_after = git_dirty_state()
    drift: list[str] = []
    if dirty_before is not None and dirty_after is not None:
        drift = sorted(
            rel for rel, data in dirty_after.items()
            if rel not in dirty_before or dirty_before[rel] != data
        )
        drift += sorted(rel for rel in dirty_before if rel not in dirty_after)
        if drift:
            print(f"WARN sensor side effects on repo files ({len(drift)}): {', '.join(drift[:20])}")
        else:
            print("OK sensor run left repository files unchanged")

    if args.json_out:
        payload = {
            "schema": "velvetos.sensor-full-results.v1" if suite_mode == "full" else "velvetos.sensor-selected-results.v1",
            "suite_runner": "scripts/check-all.py",
            "suite_mode": suite_mode,
            "sensor_count": len(checks),
            "total_available_sensor_count": len(all_checks),
            "failed_count": len(failed),
            "selected_sensor_ids": [path.stem for path in checks],
            "repository_side_effects": drift,
            "results": results,
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failed:
        print(f"FAIL suite failed={len(failed)}/{len(checks)}", file=sys.stderr)
        return 1
    print(f"OK suite passed={len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
