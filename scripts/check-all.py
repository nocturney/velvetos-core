#!/usr/bin/env python3
"""Run VelvetOS computational HQ sensors. No network. No send.

Default behavior is the authoritative active regression surface (CORE + DOMAIN).
Stage 3 uses an exact selector output with --selection for pull requests while
pushes to main run the full active regression. Event/retired lifecycle checks are
explicit-only unless the selector directly activates a relevant event sensor.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
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
REGRESSION_LIFECYCLES = {"CORE", "DOMAIN"}
RETIRED_LIFECYCLE = "RETIRED_RECEIPT"


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


def registry_sensor_rows() -> list[dict]:
    registry = json.loads(SENSOR_REGISTRY.read_text(encoding="utf-8"))
    return [row for row in registry.get("sensors") or [] if isinstance(row, dict)]


def always_on_sensor_ids(rows: list[dict] | None = None) -> set[str]:
    rows = rows if rows is not None else registry_sensor_rows()
    return {
        str(row["id"])
        for row in rows
        if row.get("fallback_scope") == "ALWAYS_ON"
    }


def regression_sensor_ids(rows: list[dict] | None = None) -> set[str]:
    rows = rows if rows is not None else registry_sensor_rows()
    return {str(row["id"]) for row in rows if row.get("lifecycle") in REGRESSION_LIFECYCLES}


def retired_sensor_ids(rows: list[dict] | None = None) -> set[str]:
    rows = rows if rows is not None else registry_sensor_rows()
    return {str(row["id"]) for row in rows if row.get("lifecycle") == RETIRED_LIFECYCLE}


def select_checks(
    all_checks: dict[str, Path],
    selection: dict | None,
    required_always_on: set[str] | None = None,
    required_regression: set[str] | None = None,
    retired: set[str] | None = None,
    include_all_lifecycle: bool = False,
) -> tuple[list[Path], str]:
    regression = required_regression if required_regression is not None else set(all_checks)
    retired_ids = retired or set()
    if selection is None:
        chosen = set(all_checks) if include_all_lifecycle else set(regression)
        unknown = sorted(chosen - set(all_checks))
        if unknown:
            raise ValueError(f"registry references unknown sensors: {unknown}")
        mode = "all-lifecycle" if include_all_lifecycle else "full"
        return [all_checks[sensor_id] for sensor_id in sorted(chosen)], mode
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
    forbidden_retired = sorted(selected & retired_ids)
    if forbidden_retired:
        raise ValueError(f"routine selection includes RETIRED_RECEIPT sensors: {forbidden_retired}")
    if selection.get("full_suite") is True:
        missing_regression = sorted(regression - selected)
        if missing_regression:
            raise ValueError(f"FULL_SUITE selection omits active regression sensors: {missing_regression}")
    return [all_checks[sensor_id] for sensor_id in normalized], "selected"


README_CONTRACT = SCRIPTS / "readme_contract.py"
README_BASE = "origin/main"


def local_readme_gate(repo: Path = ROOT, base: str = README_BASE, head: str = "HEAD", hosted_skip: bool = True) -> tuple[str, int]:
    """Run the Living README contract locally, the same gate the hosted PR workflow runs.

    Returns (message, returncode). Skips with a clear line when there is no git base
    (not a git repo, or origin/main missing) and when running under GitHub Actions,
    where the workflow runs readme_contract.py as its own step. The fixture passes
    hosted_skip=False so its pass/fail cases hold on hosted runners too.
    """
    if hosted_skip and os.environ.get("GITHUB_ACTIONS") == "true":
        return "SKIP readme-contract (hosted workflow runs the README gate as its own step)", 0
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"{base}^{{commit}}"],
        cwd=repo, text=True, capture_output=True,
    )
    if probe.returncode != 0:
        return f"SKIP readme-contract (no git base {base} in {repo})", 0
    proc = subprocess.run(
        [sys.executable, str(README_CONTRACT), "--repo", str(repo), "--base", base, "--head", head],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8",
    )
    text = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)
    return text, proc.returncode


def readme_gate_fixture() -> list[str]:
    """Prove the local gate fails on a capability change without README and passes with it."""
    errors: list[str] = []

    def git(repo: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "readme-gate-fixture")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "scripts").mkdir()
        (repo / "scripts" / "tool.py").write_text("print(1)\n", encoding="utf-8")
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "base")
        git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

        (repo / "scripts" / "tool.py").write_text("print(2)\n", encoding="utf-8")
        git(repo, "commit", "-qam", "capability change without README")
        _, rc = local_readme_gate(repo, base="origin/main", head="HEAD", hosted_skip=False)
        if rc != 1:
            errors.append(f"capability change without README must fail locally, got rc={rc}")

        (repo / "README.md").write_text("base\nupdated\n", encoding="utf-8")
        git(repo, "commit", "-qam", "README update")
        _, rc = local_readme_gate(repo, base="origin/main", head="HEAD", hosted_skip=False)
        if rc != 0:
            errors.append(f"capability change with README must pass locally, got rc={rc}")

        msg, rc = local_readme_gate(repo, base="origin/does-not-exist", head="HEAD", hosted_skip=False)
        if rc != 0 or not msg.startswith("SKIP readme-contract"):
            errors.append(f"missing base must skip with rc=0, got rc={rc} msg={msg!r}")

    with tempfile.TemporaryDirectory() as plain:
        msg, rc = local_readme_gate(Path(plain), base="origin/main", head="HEAD", hosted_skip=False)
        if rc != 0 or not msg.startswith("SKIP readme-contract"):
            errors.append(f"non-git directory must skip with rc=0, got rc={rc} msg={msg!r}")
    return errors


def selftest() -> int:
    fixture_errors = readme_gate_fixture()
    if fixture_errors:
        for error in fixture_errors:
            print(f"FAIL check-all readme gate: {error}", file=sys.stderr)
        return 1
    fixture = {
        "check-a": Path("scripts/check-a.py"),
        "check-b": Path("scripts/check-b.py"),
        "check-retired": Path("scripts/check-retired.py"),
    }
    always_on = {"check-a"}
    regression = {"check-a", "check-b"}
    retired = {"check-retired"}

    selected, mode = select_checks(
        fixture,
        {"selected_sensor_ids": ["check-a", "check-b"], "total_sensor_count": 3},
        always_on,
        regression,
        retired,
    )
    if mode != "selected" or [path.stem for path in selected] != ["check-a", "check-b"]:
        print("FAIL check-all selection fixture", file=sys.stderr)
        return 1

    selected, mode = select_checks(fixture, None, set(), regression, retired)
    if mode != "full" or [path.stem for path in selected] != ["check-a", "check-b"]:
        print("FAIL check-all active full-suite fixture", file=sys.stderr)
        return 1

    selected, mode = select_checks(fixture, None, set(), regression, retired, include_all_lifecycle=True)
    if mode != "all-lifecycle" or [path.stem for path in selected] != ["check-a", "check-b", "check-retired"]:
        print("FAIL check-all all-lifecycle fixture", file=sys.stderr)
        return 1

    for bad in (
        {"selected_sensor_ids": []},
        {"selected_sensor_ids": ["check-a", "check-a"]},
        {"selected_sensor_ids": ["check-missing"]},
        {"selected_sensor_ids": ["check-a"], "total_sensor_count": 4},
        {"selected_sensor_ids": ["check-a"], "full_suite": True, "total_sensor_count": 3},
        {"selected_sensor_ids": ["check-a", "check-b", "check-retired"], "total_sensor_count": 3},
    ):
        try:
            select_checks(fixture, bad, always_on, regression, retired)
        except ValueError:
            continue
        print(f"FAIL check-all accepted invalid selection: {bad}", file=sys.stderr)
        return 1
    try:
        select_checks(
            fixture,
            {"selected_sensor_ids": ["check-b"], "total_sensor_count": 3},
            always_on,
            regression,
            retired,
        )
    except ValueError:
        pass
    else:
        print("FAIL check-all accepted selection missing ALWAYS_ON sensor", file=sys.stderr)
        return 1
    print(
        "OK check-all selftest default=ACTIVE_FULL selected_input=EXACT "
        "always_on=REQUIRED retired=EXPLICIT_ONLY all_lifecycle=AVAILABLE fail_closed=PASS "
        "readme_gate=LOCAL_PARITY"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--selection", type=Path)
    ap.add_argument("--all-lifecycle", action="store_true", help="explicitly replay EVENT_ACCEPTANCE and RETIRED_RECEIPT sensors too")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return selftest()
    if args.selection and args.all_lifecycle:
        print("FAIL --selection and --all-lifecycle are mutually exclusive", file=sys.stderr)
        return 2

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
        rows = registry_sensor_rows()
        required_always_on = always_on_sensor_ids(rows) if selection is not None else set()
        regression = regression_sensor_ids(rows)
        retired = retired_sensor_ids(rows)
        checks, suite_mode = select_checks(
            all_checks,
            selection,
            required_always_on,
            regression,
            retired,
            include_all_lifecycle=args.all_lifecycle,
        )
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
    readme_msg, readme_rc = local_readme_gate()
    if readme_rc != 0:
        failed.append("readme-contract")
        print(f"FAIL readme-contract\n{readme_msg}", file=sys.stderr)
    else:
        print(readme_msg)

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
            "regression_sensor_count": len(regression),
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
