#!/usr/bin/env python3
"""Collect read-only Stage 2 shadow-selector evidence from GitHub Actions.

The collector never changes GitHub state. It reads workflow runs/logs through
the authenticated gh CLI, deduplicates reruns by pull request, extracts the
machine-readable selector/comparison markers, and evaluates the predeclared
Stage 2 shadow exit criteria.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
CONFIG = POLICY_DIR / "sensor-selection.json"
BASELINE = POLICY_DIR / "reports" / "stage2-shadow-observation-baseline.json"
WORKFLOW = "VelvetOS Core Sensors"
SELECTION_MARKER = "SENSOR_SHADOW_SELECTION_JSON "
COMPARISON_MARKER = "SENSOR_SHADOW_COMPARISON_JSON "
CLASSIFICATIONS = {"UNRELATED", "RELEVANT_MAPPING_FIXED"}


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


def collect(limit: int, classifications_path: Path | None) -> dict:
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

    # Resolve PRs and keep the latest completed run per PR so reruns do not
    # inflate the observation volume.
    by_pr: dict[int, dict] = {}
    unresolved_runs: list[int] = []
    for run in eligible:
        pr = pr_number_for_run(repo, run)
        if pr is None:
            unresolved_runs.append(int(run["databaseId"]))
            continue
        current = by_pr.get(pr)
        if current is None or parse_time(run["updatedAt"]) > parse_time(current["updatedAt"]):
            run = dict(run)
            run["pull_request"] = pr
            by_pr[pr] = run

    observations: list[dict] = []
    for pr, run in sorted(by_pr.items(), key=lambda item: item[1]["createdAt"]):
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
                row["evidence_complete"] = bool(row["selection"] and row["comparison"])
            except RuntimeError as exc:
                row["collection_error"] = str(exc)
        observations.append(row)

    classifications = load_classifications(classifications_path)
    critical_misses: list[dict] = []
    noncritical_misses: list[dict] = []
    incomplete: list[int] = []
    for row in observations:
        if not row["evidence_complete"]:
            incomplete.append(row["run_id"])
            continue
        comparison = row["comparison"] or {}
        for sensor_id in comparison.get("critical_misses") or []:
            critical_misses.append({"run_id": row["run_id"], "pull_request": row["pull_request"], "sensor_id": sensor_id})
        for sensor_id in comparison.get("selector_misses") or []:
            if sensor_id in set(comparison.get("critical_misses") or []):
                continue
            item = {"run_id": row["run_id"], "pull_request": row["pull_request"], "sensor_id": sensor_id}
            classification = classifications.get((row["run_id"], sensor_id))
            if classification:
                item["classification"] = classification["classification"]
                item["classification_evidence"] = classification["evidence"]
            else:
                item["classification"] = "UNCLASSIFIED"
            noncritical_misses.append(item)

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
            "observation_days": round(observation_days, 4),
            "critical_misses": len(critical_misses),
            "noncritical_misses": len(noncritical_misses),
            "unclassified_noncritical_misses": len(unclassified),
            "incomplete_observations": len(incomplete),
            "deterministic_replay_pass": deterministic_replay_pass,
        },
        "gate": {
            "eligible": not blockers,
            "blockers": blockers,
        },
        "critical_misses": critical_misses,
        "noncritical_misses": noncritical_misses,
        "incomplete_run_ids": incomplete,
        "unresolved_run_ids": unresolved_runs,
        "observations": observations,
        "read_only": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--classifications", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.limit < 1 or args.limit > 1000:
        ap.error("--limit must be 1..1000")
    try:
        report = collect(args.limit, args.classifications)
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
