#!/usr/bin/env python3
"""Collect read-only Stage 2 shadow-selector evidence from GitHub Actions.

The collector never changes GitHub state. It reads workflow runs/logs through
the authenticated gh CLI, counts each pull request once for observation volume,
preserves every eligible run for historical miss evidence, and evaluates the
predeclared Stage 2 shadow exit criteria.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
CONFIG = POLICY_DIR / "sensor-selection.json"
BASELINE = POLICY_DIR / "reports" / "stage2-shadow-observation-baseline.json"
DEFAULT_CLASSIFICATIONS = POLICY_DIR / "reports" / "stage2-shadow-miss-classifications.json"
DEFAULT_RECOVERIES = POLICY_DIR / "reports" / "stage2-shadow-incomplete-recoveries.json"
RECOVERY_SCHEMA = "velvetos.sensor-shadow-incomplete-recoveries.v1"
RECOVERY_REASONS = {"SELECTOR_SCRIPT_SYNTAX_FAILURE"}
WORKFLOW = "VelvetOS Core Sensors"
SELECTION_MARKER = "SENSOR_SHADOW_SELECTION_JSON "
COMPARISON_MARKER = "SENSOR_SHADOW_COMPARISON_JSON "
CLASSIFICATIONS = {"UNRELATED", "RELEVANT_MAPPING_FIXED"}
_PR_BRANCH_CACHE: dict[tuple[str, str], list[dict]] = {}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gh(args: list[str], timeout: int = 60) -> str:
    if not shutil.which("gh"):
        raise RuntimeError("gh CLI is required")
    proc = subprocess.run(
        ["gh", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "gh command failed").strip())
    return proc.stdout


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def repo_slug() -> str:
    data = json.loads(gh(["repo", "view", "--json", "nameWithOwner"]))
    value = str(data.get("nameWithOwner") or "").strip()
    if "/" not in value:
        raise RuntimeError("cannot resolve GitHub repository")
    return value


def pr_number_for_run(repo: str, run: dict) -> int | None:
    # Prefer a cached branch/time match. This survives force-push/rebase and
    # avoids per-run API calls when the PR head branch is unambiguous.
    branch = str(run.get("headBranch") or "").strip()
    created_at = run.get("createdAt")
    if branch and created_at:
        key = (repo, branch)
        if key not in _PR_BRANCH_CACHE:
            _PR_BRANCH_CACHE[key] = json.loads(gh([
                "pr", "list",
                "--repo", repo,
                "--state", "all",
                "--head", branch,
                "--limit", "20",
                "--json", "number,createdAt,closedAt,mergedAt",
            ]))
        run_time = parse_time(created_at)
        candidates = []
        for pull in _PR_BRANCH_CACHE[key]:
            opened = pull.get("createdAt")
            closed = pull.get("closedAt") or pull.get("mergedAt")
            if not opened or parse_time(opened) > run_time:
                continue
            if closed and run_time > parse_time(closed):
                continue
            candidates.append(pull)
        if len(candidates) == 1:
            return int(candidates[0]["number"])

    # Fall back to GitHub's run/commit associations for missing or ambiguous
    # branch evidence.
    data = json.loads(gh(["api", f"repos/{repo}/actions/runs/{run['databaseId']}"]))
    prs = data.get("pull_requests") or []
    if prs:
        try:
            return int(prs[0]["number"])
        except (KeyError, TypeError, ValueError):
            pass

    sha = str(run.get("headSha") or "")
    if sha:
        pulls = json.loads(gh(["api", f"repos/{repo}/commits/{sha}/pulls"]))
        if pulls:
            try:
                return int(pulls[0]["number"])
            except (KeyError, TypeError, ValueError):
                pass
    return None


def marker_json(log: str, marker: str) -> dict | None:
    found = None
    for line in log.splitlines():
        idx = line.find(marker)
        if idx < 0:
            continue
        raw = line[idx + len(marker):].strip()
        try:
            found = json.loads(raw)
        except json.JSONDecodeError:
            continue
    return found


def load_classifications(path: Path | None) -> dict[tuple[int, str], dict]:
    if path is None:
        return {}
    data = load(path)
    out: dict[tuple[int, str], dict] = {}
    for row in data.get("entries") or []:
        try:
            run_id = int(row["run_id"])
            sensor_id = str(row["sensor_id"])
            classification = str(row["classification"])
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("invalid shadow miss classification row")
        if classification not in CLASSIFICATIONS:
            raise RuntimeError(f"unsupported miss classification: {classification}")
        if not str(row.get("evidence") or "").strip():
            raise RuntimeError("miss classification evidence is required")
        out[(run_id, sensor_id)] = row
    return out


def load_recoveries(path: Path | None) -> dict[int, dict]:
    if path is None:
        return {}
    data = load(path)
    if data.get("schema") != RECOVERY_SCHEMA:
        raise RuntimeError("invalid shadow incomplete recovery schema")
    out: dict[int, dict] = {}
    for row in data.get("entries") or []:
        try:
            run_id = int(row["run_id"])
            pull_request = int(row["pull_request"])
            head_sha = str(row["head_sha"]).lower()
            reason = str(row["reason"])
            expected_selection = str(row["expected_selection"])
            sensor_count = int(row["sensor_count"])
            full_failures = list(row["full_failures"])
            selector_misses = list(row["selector_misses"])
            verification = dict(row["verification"])
            verification_run_id = int(verification["run_id"])
            verification_head_sha = str(verification["head_sha"]).lower()
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("invalid shadow incomplete recovery row")
        if run_id in out:
            raise RuntimeError(f"duplicate shadow incomplete recovery run_id: {run_id}")
        if pull_request < 1 or verification_run_id < 1 or sensor_count < 1:
            raise RuntimeError("shadow incomplete recovery numeric fields must be positive")
        if not re.fullmatch(r"[0-9a-f]{40}", head_sha) or not re.fullmatch(r"[0-9a-f]{40}", verification_head_sha):
            raise RuntimeError("shadow incomplete recovery SHA must be 40 lowercase hex characters")
        if reason not in RECOVERY_REASONS:
            raise RuntimeError(f"unsupported shadow incomplete recovery reason: {reason}")
        if expected_selection != "FULL_SUITE":
            raise RuntimeError("shadow incomplete recovery must prove FULL_SUITE selection")
        if selector_misses != []:
            raise RuntimeError("FULL_SUITE recovery cannot declare selector misses")
        if not all(isinstance(value, str) and re.fullmatch(r"check-[a-z0-9-]+", value) for value in full_failures):
            raise RuntimeError("shadow incomplete recovery full_failures must be sensor ids")
        if str(verification.get("comparison_status") or "") != "NO_MISS":
            raise RuntimeError("shadow incomplete recovery verification must be NO_MISS")
        if not str(row.get("evidence") or "").strip():
            raise RuntimeError("shadow incomplete recovery evidence is required")
        out[run_id] = row
    return out


def parse_full_suite_log(log: str) -> dict:
    sensor_count = None
    failures: set[str] = set()
    for line in log.splitlines():
        count_match = re.search(r"\bSENSORS\s+(\d+)\s+mode=full\b", line)
        if count_match:
            sensor_count = int(count_match.group(1))
        failure_match = re.search(r"\bFAIL\s+(check-[a-z0-9-]+)\.py\b", line)
        if failure_match:
            failures.add(failure_match.group(1))
    return {
        "sensor_count": sensor_count,
        "full_failures": sorted(failures),
    }


def apply_recoveries(
    observations: list[dict],
    recoveries: dict[int, dict],
    total_sensor_count: int,
) -> list[int]:
    by_run: dict[int, dict] = {}
    for observation in observations:
        for row in observation.get("runs") or [observation]:
            by_run[int(row["run_id"])] = row

    recovered: list[int] = []
    for run_id, recovery in recoveries.items():
        row = by_run.get(run_id)
        if row is None:
            continue
        if row.get("evidence_complete"):
            raise RuntimeError(f"recovery targets already-complete run: {run_id}")
        if int(row.get("pull_request") or 0) != int(recovery["pull_request"]):
            raise RuntimeError(f"recovery PR mismatch for run {run_id}")
        if str(row.get("head_sha") or "").lower() != str(recovery["head_sha"]).lower():
            raise RuntimeError(f"recovery head SHA mismatch for run {run_id}")
        if row.get("conclusion") != "failure":
            raise RuntimeError(f"recovery target must be a failed run: {run_id}")

        observed = row.get("full_suite_log_evidence") or {}
        if int(observed.get("sensor_count") or 0) != total_sensor_count:
            raise RuntimeError(f"recovery lacks full-suite log proof for run {run_id}")
        if int(recovery["sensor_count"]) != total_sensor_count:
            raise RuntimeError(f"recovery sensor count mismatch for run {run_id}")
        if sorted(observed.get("full_failures") or []) != sorted(recovery.get("full_failures") or []):
            raise RuntimeError(f"recovery full-failure evidence mismatch for run {run_id}")

        verification = recovery["verification"]
        verification_run_id = int(verification["run_id"])
        verification_row = by_run.get(verification_run_id)
        if verification_row is None:
            raise RuntimeError(f"recovery verification run missing from observation history: {verification_run_id}")
        if int(verification_row.get("pull_request") or 0) != int(recovery["pull_request"]):
            raise RuntimeError(f"recovery verification PR mismatch for run {run_id}")
        if str(verification_row.get("head_sha") or "").lower() != str(verification["head_sha"]).lower():
            raise RuntimeError(f"recovery verification head SHA mismatch for run {run_id}")
        if not verification_row.get("evidence_complete"):
            raise RuntimeError(f"recovery verification run is incomplete: {verification_run_id}")

        selection = verification_row.get("selection") or {}
        comparison = verification_row.get("comparison") or {}
        if selection.get("full_suite") is not True or int(selection.get("selection_count") or 0) != total_sensor_count:
            raise RuntimeError(f"recovery verification did not prove full-suite selection: {verification_run_id}")
        if comparison.get("status") != "NO_MISS":
            raise RuntimeError(f"recovery verification comparison is not NO_MISS: {verification_run_id}")
        if comparison.get("selector_misses") or comparison.get("critical_misses"):
            raise RuntimeError(f"recovery verification contains selector misses: {verification_run_id}")

        row["evidence_recovered"] = True
        row["recovery"] = recovery
        recovered.append(run_id)
    return sorted(recovered)


def scan_observations(
    observations: list[dict],
    classifications: dict[tuple[int, str], dict],
) -> tuple[list[dict], list[dict], list[int]]:
    critical_misses: list[dict] = []
    noncritical_misses: list[dict] = []
    incomplete: list[int] = []
    for observation in observations:
        for row in observation.get("runs") or [observation]:
            if not row["evidence_complete"]:
                if row.get("evidence_recovered"):
                    continue
                incomplete.append(row["run_id"])
                continue
            comparison = row["comparison"] or {}
            critical = set(comparison.get("critical_misses") or [])
            for sensor_id in critical:
                critical_misses.append({
                    "run_id": row["run_id"],
                    "pull_request": row["pull_request"],
                    "sensor_id": sensor_id,
                })
            for sensor_id in comparison.get("selector_misses") or []:
                if sensor_id in critical:
                    continue
                item = {
                    "run_id": row["run_id"],
                    "pull_request": row["pull_request"],
                    "sensor_id": sensor_id,
                }
                classification = classifications.get((row["run_id"], sensor_id))
                if classification:
                    item["classification"] = classification["classification"]
                    item["classification_evidence"] = classification["evidence"]
                else:
                    item["classification"] = "UNCLASSIFIED"
                noncritical_misses.append(item)
    return critical_misses, noncritical_misses, incomplete


def collect(limit: int, classifications_path: Path | None, recoveries_path: Path | None) -> dict:
    config = load(CONFIG)
    baseline = load(BASELINE)
    criteria = config["shadow_exit"]
    start = parse_time(baseline["first_observation"]["created_at"])
    repo = repo_slug()
    runs = json.loads(gh([
        "run", "list",
        "--workflow", WORKFLOW,
        "--event", "pull_request",
        "--limit", str(limit),
        "--json", "databaseId,displayTitle,event,headBranch,headSha,status,conclusion,createdAt,updatedAt,url",
    ], timeout=90))

    eligible = [
        run for run in runs
        if run.get("event") == "pull_request"
        and run.get("createdAt")
        and parse_time(run["createdAt"]) >= start
    ]
    dated_runs = [run for run in runs if run.get("createdAt")]
    history_truncated = bool(
        len(runs) >= limit
        and dated_runs
        and min(parse_time(run["createdAt"]) for run in dated_runs) > start
    )

    # Count each PR once for observation volume, but retain every run. A clean
    # later rerun must never erase a miss discovered by an earlier run.
    by_pr: dict[int, list[dict]] = {}
    unresolved_runs: list[int] = []
    for run in eligible:
        pr = pr_number_for_run(repo, run)
        if pr is None:
            unresolved_runs.append(int(run["databaseId"]))
            continue
        row = dict(run)
        row["pull_request"] = pr
        by_pr.setdefault(pr, []).append(row)

    observations: list[dict] = []
    for pr, runs_for_pr in sorted(
        by_pr.items(),
        key=lambda item: min(parse_time(run["createdAt"]) for run in item[1]),
    ):
        run_rows: list[dict] = []
        for run in sorted(runs_for_pr, key=lambda value: parse_time(value["createdAt"])):
            run_id = int(run["databaseId"])
            row = {
                "pull_request": pr,
                "run_id": run_id,
                "head_sha": run.get("headSha"),
                "head_branch": run.get("headBranch"),
                "created_at": run.get("createdAt"),
                "updated_at": run.get("updatedAt"),
                "conclusion": run.get("conclusion"),
                "url": run.get("url"),
                "selection": None,
                "comparison": None,
                "evidence_complete": False,
            }
            if run.get("status") == "completed":
                try:
                    log = gh(["run", "view", str(run_id), "--log"], timeout=120)
                    row["selection"] = marker_json(log, SELECTION_MARKER)
                    row["comparison"] = marker_json(log, COMPARISON_MARKER)
                    row["full_suite_log_evidence"] = parse_full_suite_log(log)
                    row["evidence_complete"] = bool(row["selection"] and row["comparison"])
                except RuntimeError as exc:
                    row["collection_error"] = str(exc)
            run_rows.append(row)

        latest = max(run_rows, key=lambda value: parse_time(value["updated_at"]))
        observation = dict(latest)
        observation["run_count"] = len(run_rows)
        observation["runs"] = run_rows
        observations.append(observation)

    classifications = load_classifications(classifications_path)
    recoveries = load_recoveries(recoveries_path)
    registry = load(POLICY_DIR / "sensor-registry.json")
    total_sensor_count = len(registry.get("sensors") or [])
    recovered_incomplete = apply_recoveries(observations, recoveries, total_sensor_count)
    critical_misses, noncritical_misses, incomplete = scan_observations(
        observations,
        classifications,
    )

    selector_test = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sensor_selector.py"), "--self-test"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    deterministic_replay_pass = selector_test.returncode == 0

    now = datetime.now(timezone.utc)
    observed_prs = len(observations)
    observed_runs = sum(len(row.get("runs") or [row]) for row in observations)
    observation_days = max(0.0, (now - start).total_seconds() / 86400.0)
    unclassified = [x for x in noncritical_misses if x.get("classification") == "UNCLASSIFIED"]
    relevant_unfixed = [
        x for x in noncritical_misses
        if x.get("classification") not in {"UNRELATED", "RELEVANT_MAPPING_FIXED"}
    ]

    blockers: list[str] = []
    if observed_prs < int(criteria["minimum_pull_requests"]):
        blockers.append("MINIMUM_PULL_REQUESTS_NOT_MET")
    if observation_days < float(criteria["minimum_observation_days"]):
        blockers.append("MINIMUM_OBSERVATION_DAYS_NOT_MET")
    if critical_misses:
        blockers.append("CRITICAL_MISS_PRESENT")
    if unclassified:
        blockers.append("NONCRITICAL_MISS_UNCLASSIFIED")
    if relevant_unfixed:
        blockers.append("RELEVANT_MISS_NOT_REPAIRED")
    if incomplete:
        blockers.append("INCOMPLETE_OBSERVATION_EVIDENCE")
    if unresolved_runs:
        blockers.append("UNRESOLVED_PULL_REQUEST_ID")
    if history_truncated:
        blockers.append("RUN_HISTORY_TRUNCATED")
    if not deterministic_replay_pass:
        blockers.append("DETERMINISTIC_REPLAY_FAILED")
    if criteria.get("rollback_mode") != "FULL_SUITE_REQUIRED":
        blockers.append("ROLLBACK_MODE_INVALID")

    return {
        "schema": "velvetos.sensor-shadow-observation.v1",
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "repository": repo,
        "workflow": WORKFLOW,
        "selector_mode": config.get("mode"),
        "observation_start": start.isoformat().replace("+00:00", "Z"),
        "criteria": criteria,
        "progress": {
            "observed_pull_requests": observed_prs,
            "observed_runs": observed_runs,
            "observation_days": round(observation_days, 4),
            "critical_misses": len(critical_misses),
            "noncritical_misses": len(noncritical_misses),
            "unclassified_noncritical_misses": len(unclassified),
            "incomplete_observations": len(incomplete),
            "recovered_incomplete_observations": len(recovered_incomplete),
            "unresolved_runs": len(unresolved_runs),
            "run_history_complete": not history_truncated,
            "deterministic_replay_pass": deterministic_replay_pass,
        },
        "gate": {
            "eligible": not blockers,
            "blockers": blockers,
        },
        "critical_misses": critical_misses,
        "noncritical_misses": noncritical_misses,
        "incomplete_run_ids": incomplete,
        "recovered_incomplete_run_ids": recovered_incomplete,
        "unresolved_run_ids": unresolved_runs,
        "observations": observations,
        "read_only": True,
    }


def self_test() -> int:
    early = {
        "pull_request": 407,
        "run_id": 1001,
        "evidence_complete": True,
        "comparison": {
            "selector_misses": ["check-scenario-capability-graft"],
            "critical_misses": [],
        },
    }
    later = {
        "pull_request": 407,
        "run_id": 1002,
        "evidence_complete": True,
        "comparison": {
            "selector_misses": [],
            "critical_misses": [],
        },
    }
    observations = [{
        "pull_request": 407,
        "run_id": 1002,
        "runs": [early, later],
    }]
    classifications = {
        (1001, "check-scenario-capability-graft"): {
            "classification": "RELEVANT_MAPPING_FIXED",
            "evidence": "fixture mapping repair",
        }
    }
    critical, noncritical, incomplete = scan_observations(observations, classifications)
    if critical or incomplete:
        raise AssertionError("historical miss fixture produced unexpected critical/incomplete evidence")
    if len(observations) != 1 or len(noncritical) != 1:
        raise AssertionError("PR dedupe erased or duplicated historical miss evidence")
    if noncritical[0].get("classification") != "RELEVANT_MAPPING_FIXED":
        raise AssertionError("historical miss classification was not preserved")

    incomplete_run = {
        "pull_request": 500,
        "run_id": 2001,
        "head_sha": "1" * 40,
        "conclusion": "failure",
        "evidence_complete": False,
        "full_suite_log_evidence": {
            "sensor_count": 3,
            "full_failures": ["check-critical-syntax"],
        },
    }
    verification_run = {
        "pull_request": 500,
        "run_id": 2002,
        "head_sha": "2" * 40,
        "conclusion": "success",
        "evidence_complete": True,
        "selection": {
            "full_suite": True,
            "selection_count": 3,
        },
        "comparison": {
            "status": "NO_MISS",
            "selector_misses": [],
            "critical_misses": [],
        },
    }
    recovery_observations = [{
        "pull_request": 500,
        "run_id": 2002,
        "runs": [incomplete_run, verification_run],
    }]
    _, _, before_recovery = scan_observations(recovery_observations, {})
    if before_recovery != [2001]:
        raise AssertionError("unreviewed incomplete evidence must remain blocking")
    recoveries = {
        2001: {
            "run_id": 2001,
            "pull_request": 500,
            "head_sha": "1" * 40,
            "reason": "SELECTOR_SCRIPT_SYNTAX_FAILURE",
            "expected_selection": "FULL_SUITE",
            "sensor_count": 3,
            "full_failures": ["check-critical-syntax"],
            "selector_misses": [],
            "verification": {
                "run_id": 2002,
                "head_sha": "2" * 40,
                "comparison_status": "NO_MISS",
            },
            "evidence": "fixture reviewed recovery",
        }
    }
    recovered = apply_recoveries(recovery_observations, recoveries, 3)
    _, _, after_recovery = scan_observations(recovery_observations, {})
    if recovered != [2001] or after_recovery:
        raise AssertionError("reviewed full-suite recovery did not clear incomplete evidence")
    bad_recovery = dict(recoveries[2001])
    bad_recovery["full_failures"] = []
    try:
        apply_recoveries(
            [{
                "pull_request": 500,
                "run_id": 2002,
                "runs": [
                    dict(incomplete_run, evidence_recovered=False),
                    verification_run,
                ],
            }],
            {2001: bad_recovery},
            3,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("mismatched recovery evidence must fail closed")

    print("OK sensor-shadow-observation selftest historical_miss_retention=PASS pr_dedupe=PASS incomplete_recovery=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--classifications", type=Path, default=DEFAULT_CLASSIFICATIONS)
    ap.add_argument("--recoveries", type=Path, default=DEFAULT_RECOVERIES)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.limit < 1 or args.limit > 1000:
        ap.error("--limit must be 1..1000")
    try:
        report = collect(args.limit, args.classifications, args.recoveries)
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL sensor-shadow-observation collection: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(
        f"SENSOR_SHADOW_READINESS eligible={str(report['gate']['eligible']).lower()} "
        f"prs={report['progress']['observed_pull_requests']}/{report['criteria']['minimum_pull_requests']} "
        f"days={report['progress']['observation_days']}/{report['criteria']['minimum_observation_days']} "
        f"critical_misses={report['progress']['critical_misses']} "
        f"noncritical_misses={report['progress']['noncritical_misses']}"
    )
    if report["gate"]["blockers"]:
        print("BLOCKERS " + ",".join(report["gate"]["blockers"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
