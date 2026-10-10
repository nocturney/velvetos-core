#!/usr/bin/env python3
"""#604: independent read-only recheck of pre-existing Dagu 1/2/4 LAB logs.

Observe mode is explicitly opt-in and NEVER invokes a Dagu executable.
CI runs only offline verify/selftest against sanitized evidence; no host access,
models, scheduler, leases, network effects, production commands or process kills.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
P2 = ROOT / "docs/implementation/office-v2/phase2"
EVIDENCE = P2 / "p0-dagu-two-host-13-run-forensic-audit-2026-10-10.json"
SCHEMA = "velvetos.office-v2.fleet.dagu-13-run-forensic-audit.v0"
SOURCE_HASHES = {
    "manifest.json": "662ccfb7289f9481cc7e332c42886ba078d1575c89c866788efbd861e220c61b",
    "groups-progress.json": "c4fac834e961ca44ed9c2ac2831989b99e75004eec6e64eb2631c82d3d1c58ec",
    "fairness.json": "26dd1ec4c18caae6478db2bd939014fa736c70f96ac7ca096d901cb3fddd410b",
    "independent-audit.json": "650e344a287d127caa9f974a360391b0ad6da0e45bca6a35fd807922aa65e9e6",
}
EXPECTED_DIGEST = "d5d7a4ca0b3763074c62a08ba762c307ab2f986240bd9a267e3a4eed41783976"
EXPECTED_GROUPS = {"solo": 1, "dual": 2, "quad": 4, "fair": 6}
EXPECTED_OVERLAP = {"solo": 1, "dual": 2, "quad": 4, "fair": 1}
EXPECTED_PHYSICAL_HOSTS = {"mac": 10, "win": 3}
EXPECTED_QUEUE_INVERSION_COUNT = 4
EXPECTED_LOG_WITNESS_SET_SHA256 = "26bebd62fc9005fbedf49ac7cbbbb2c7e7acea8f596a93df43b7015861fb0226"


class Refused(Exception):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise Refused(reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_strict_json(path: Path, limit: int = 250000) -> dict:
    need(path.is_file() and not path.is_symlink() and
         0 < path.stat().st_size < limit, "SOURCE_JSON_UNAVAILABLE")
    obj = json.loads(path.read_text(encoding="utf-8"))
    need(type(obj) is dict, "NOT_JSON_OBJECT")
    return obj


def timestamp(s: str) -> datetime:
    need(type(s) is str and len(s) < 64, "TIMESTAMP_INVALID")
    s = s.strip().replace("Z", "+00:00")
    s = re.sub(r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)", r"\1", s)
    dt = datetime.fromisoformat(s)
    need(dt.tzinfo is not None, "TIMESTAMP_MUST_INCLUDE_ZONE")
    return dt


def parse_record(content: str, marker: str, tag: str) -> tuple:
    lines = [line for line in content.splitlines()
             if line.startswith(marker + "|" + tag + "|")]
    need(len(lines) == 1, "WRONG_MARKER_COUNT_" + marker)
    parts = lines[0].split("|")
    need(len(parts) >= (5 if marker == "VF604_END" else 4) and
         parts[0] == marker and parts[1] == tag,
         "MALFORMED_MARKER_" + marker)
    return parts[2].strip(), timestamp(parts[3]), (parts[4].strip() if len(parts) > 4 else None)


def max_overlap(spans: list) -> int:
    events = []
    for a, b in spans:
        events.append((a, 1))
        events.append((b, -1))
    c = peak = 0
    for _, delta in sorted(events, key=lambda x: (x[0], x[1])):
        c += delta
        need(c >= 0, "NEGATIVE_OVERLAP")
        peak = max(peak, c)
    need(c == 0, "OPEN_TIMESPAN")
    return peak


def inversions(order: list, submitted: list) -> int:
    need(type(order) is list and type(submitted) is list and
         len(order) == len(submitted) == len(set(order)) == len(set(submitted)) and
         set(order) == set(submitted), "FAIRNESS_SET_CHANGED")
    index = {name: i for i, name in enumerate(submitted)}
    a = [index[name] for name in order]
    return sum(a[i] > a[j] for i in range(len(a)) for j in range(i + 1, len(a)))


def observe(lab_root: Path) -> dict:
    root = lab_root.resolve(strict=True)
    need(root.name == "fleet-placement-20261008-1423z" and
         "ComputerUseFleet/dagu/2.18.2" in root.as_posix() and
         root.is_dir(), "WRONG_LAB_ROOT")
    evidence = root / "evidence"
    files = {}
    for name, expected_sha in SOURCE_HASHES.items():
        path = evidence / name
        need(path.is_file() and not path.is_symlink(), "MISSING_HISTORIC_" + name)
        need(digest(path.read_bytes()) == expected_sha, "HISTORIC_FILE_DRIFT_" + name)
        files[name] = load_strict_json(path, 1200000)

    manifest = files["manifest.json"]
    groups = files["groups-progress.json"]
    fairness = files["fairness.json"]
    historical = files["independent-audit.json"]
    need(manifest.get("schema") == "velvetos.office-v2.fleet-placement-lab-input.v1"
         and manifest.get("authority") is False
         and manifest.get("no_gpu_model_gui_business_or_paid_operations") is True
         and manifest.get("expected_sha256") == EXPECTED_DIGEST
         and manifest.get("status") == "FIXTURE_PREPARED_NOT_EXECUTED",
         "MANIFEST_SCOPE_UNSAFE")
    need(historical.get("schema") == "velvetos.office-v2.fleet-placement-independent-audit.v1"
         and historical.get("status") == "PARTIAL_LAB_NOT_PRODUCTION"
         and historical.get("acceptance_gate") == "FAIL_CLOSED_CLEANUP_PENDING"
         and historical.get("count_expected") == 13
         and historical.get("count_verified") == 13
         and historical.get("files_sha256") ==
             {k: SOURCE_HASHES[k] for k in ("manifest.json", "groups-progress.json", "fairness.json")},
         "HISTORIC_AUDIT_NOT_EXACT")
    expected_jobs = {it["tag"]: it for it in manifest["jobs"]
                     if it["group"] in EXPECTED_GROUPS}
    need(len(expected_jobs) == 13 and len(historical["postconditions"]) == 13,
         "EXPECTED_TASK_SET_INVALID")
    historic_post = {it["dag"]: it for it in historical["postconditions"]}
    need(len(historic_post) == 13, "HISTORIC_DUPLICATE_DAG")
    observations = []
    group_spans = {k: [] for k in EXPECTED_GROUPS}
    group_counts = {k: 0 for k in EXPECTED_GROUPS}
    host_counts = {"mac": 0, "win": 0}
    for group in EXPECTED_GROUPS:
        entries = (fairness["observed"] if group == "fair"
                   else groups["groups"][group]["observed"])
        for row in entries:
            tag = row.get("dag") if group == "fair" else row.get("tag")
            job = expected_jobs.get(tag)
            need(job is not None and job["group"] == group and
                 row.get("dag") == job["dag"] and
                 row.get("status") == "succeeded",
                 "WRONG_JOB_OR_TERMINAL_STATE")
            raw_paths = row.get("log_paths") if group == "fair" else row.get("stdout_paths")
            need(type(raw_paths) is list and len(raw_paths) == 1,
                 "ONE_EXACT_LOG_REQUIRED")
            raw_path = Path(raw_paths[0])
            resolved = raw_path.resolve(strict=True)
            need(resolved.is_relative_to(root) and resolved.is_file()
                 and not raw_path.is_symlink() and resolved.stat().st_size < 12000,
                 "LOG_PATH_OUT_OF_SCOPE")
            content = resolved.read_text(encoding="utf-8", errors="replace")
            begin_host, start, _ = parse_record(content, "VF604_BEGIN", tag)
            end_host, end, output_digest = parse_record(content, "VF604_END", tag)
            host = "win" if job["host"] == "win" else "mac"
            expected_worker = ("vf604-win-1423z" if host == "win"
                               else "vf604-fair-1423z" if group == "fair"
                               else "vf604-mac-1423z")
            historical_row = historic_post.get(job["dag"])
            actual_hash = digest(content.encode("utf-8"))
            need(begin_host == end_host == host and
                 0 < (end - start).total_seconds() < 40 and
                 output_digest == EXPECTED_DIGEST and
                 "VF604_POSTCONDITION_PASS|" + tag in content and
                 row.get("workerId") == expected_worker and
                 row.get("log_sha256") == actual_hash and
                 type(historical_row) is dict and
                 historical_row.get("postcondition_verified") is True and
                 historical_row.get("stdout_sha256") == actual_hash and
                 historical_row.get("worker_id") == expected_worker and
                 historical_row.get("host_from_stdout") == host and
                 historical_row.get("run_status") == "succeeded" and
                 historical_row.get("start_utc") == start.isoformat() and
                 historical_row.get("end_utc") == end.isoformat(),
                 "REAL_LOG_PROVENANCE_OR_CONTENT_MISMATCH")
            need(not any(x["dag"] == job["dag"] for x in observations),
                 "DUPLICATE_OBSERVATION")
            group_spans[group].append((start, end))
            group_counts[group] += 1
            host_counts[host] += 1
            observations.append({
                "group": group,
                "dag": job["dag"],
                "worker_id": expected_worker,
                "physical_host": host,
                "stdout_sha256": actual_hash,
                "start_utc": start.isoformat(),
                "end_utc": end.isoformat(),
                "postcondition_verified": True,
            })
    peaks = {k: max_overlap(v) for k, v in group_spans.items()}
    need(group_counts == EXPECTED_GROUPS and
         peaks == EXPECTED_OVERLAP and
         host_counts == EXPECTED_PHYSICAL_HOSTS and
         historical.get("peak_overlap") == EXPECTED_OVERLAP,
         "CONCURRENCY_OR_HOST_COUNT_WRONG")
    fair_metrics = fairness.get("metrics", {})
    fair_history = historical.get("fairness", {})
    count = inversions(fair_metrics.get("start_order"),
                       fair_metrics.get("submit_order"))
    need(count == EXPECTED_QUEUE_INVERSION_COUNT and
         fair_metrics.get("dispatch_inversions") == count and
         fair_history.get("dispatch_inversions") == count and
         fair_history.get("max_slots") == 1,
         "FAIRNESS_NONFIFO_DRIFT")
    need({k: historical["timing_samples"][k]["n"] for k in
          ("solo", "dual", "quad")} == {"solo": 1, "dual": 2, "quad": 4},
         "ONE_ROUND_SAMPLE_COUNTS_CHANGED")
    return {
        "schema": SCHEMA,
        "status": "VERIFIED_HISTORIC_RAW_13_OF_13_NO_CURRENT_LEASE",
        "scope": "#604_EXISTING_DAGU_2_18_2_SYNTHETIC_LAB_ONLY",
        "historical_utc": historical["audited_utc"],
        "historical_source_sha256": SOURCE_HASHES,
        "historical_distinct_job_count": 13,
        "historical_group_counts": group_counts,
        "historical_physical_host_counts": host_counts,
        "max_verified_overlap": peaks,
        "historical_non_fifo_dispatch_inversions": count,
        "exact_original_stdout_hashes": {
            x["dag"]: x["stdout_sha256"] for x in sorted(observations, key=lambda t: t["dag"])},
        "conclusions": {
            "synthetic_postconditions_rechecked_on_original_logs": True,
            "model_backed_coding_workers_proven": False,
            "durable_distributed_lease_issued": False,
            "atomic_effect_boundary_fencing_proven": False,
            "crash_recovery_or_retry_proven": False,
            "cancellation_proven": False,
            "fifo_order_proven": False,
            "same_fixture_vendor_comparison_proven": False,
            "production_authority": False,
            "new_model_calls": 0,
            "new_scheduler_runs": 0,
            "original_lab_evidence_modified": False,
        },
        "cleanup": "SEPARATE_LIVE_HOST_STOP_VERIFICATION_REQUIRED",
        "statistical_limits": "ONE_ROUND_N_1_2_4_NO_STABLE_P95",
    }


def verify_json(v: dict):
    need(type(v) is dict and v.get("schema") == SCHEMA
         and v.get("status") == "VERIFIED_HISTORIC_RAW_13_OF_13_NO_CURRENT_LEASE"
         and v.get("scope") == "#604_EXISTING_DAGU_2_18_2_SYNTHETIC_LAB_ONLY"
         and v.get("historical_source_sha256") == SOURCE_HASHES
         and v.get("historical_distinct_job_count") == 13
         and v.get("historical_group_counts") == EXPECTED_GROUPS
         and v.get("historical_physical_host_counts") == EXPECTED_PHYSICAL_HOSTS
         and v.get("max_verified_overlap") == EXPECTED_OVERLAP
         and v.get("historical_non_fifo_dispatch_inversions") == 4
         and v.get("cleanup") == "SEPARATE_LIVE_HOST_STOP_VERIFICATION_REQUIRED"
         and v.get("statistical_limits") == "ONE_ROUND_N_1_2_4_NO_STABLE_P95",
         "HISTORICAL_REPORT_SCOPE_INVALID")
    sha_by_dag = v.get("exact_original_stdout_hashes")
    need(type(sha_by_dag) is dict and len(sha_by_dag) == 13 and
         all(type(k) is str and k.startswith("vf604-") and
             re.fullmatch(r"[a-f0-9]{64}", val) for k, val in sha_by_dag.items()) and
         digest(json.dumps(sha_by_dag, sort_keys=True, separators=(",", ":")).encode())
         == EXPECTED_LOG_WITNESS_SET_SHA256,
         "ORIGINAL_LOG_WITNESS_SET_INVALID")
    flags = v.get("conclusions") or {}
    need(flags.get("synthetic_postconditions_rechecked_on_original_logs") is True
         and flags.get("original_lab_evidence_modified") is False
         and flags.get("new_model_calls") == 0
         and flags.get("new_scheduler_runs") == 0,
         "HISTORICAL_CLAIM_OR_EFFECTS_INVALID")
    for k in ("model_backed_coding_workers_proven", "durable_distributed_lease_issued",
              "atomic_effect_boundary_fencing_proven", "crash_recovery_or_retry_proven",
              "cancellation_proven", "fifo_order_proven",
              "same_fixture_vendor_comparison_proven", "production_authority"):
        need(flags.get(k) is False, "FALSE_DISTRIBUTED_AUTHORITY_" + k)


def selftest(proof):
    verify_json(proof)
    tested = ["pinned_historic_positive"]
    mutations = [
        ("wrong_schema", lambda q:q.update(schema="unsupported")),
        ("wrong_source", lambda q:q["historical_source_sha256"].update({"manifest.json":"0"*64})),
        ("false_lease", lambda q:q["conclusions"].update(durable_distributed_lease_issued=True)),
        ("false_fence", lambda q:q["conclusions"].update(atomic_effect_boundary_fencing_proven=True)),
        ("false_prod", lambda q:q["conclusions"].update(production_authority=True)),
        ("false_recovery", lambda q:q["conclusions"].update(crash_recovery_or_retry_proven=True)),
        ("false_cancel", lambda q:q["conclusions"].update(cancellation_proven=True)),
        ("false_fifo", lambda q:q["conclusions"].update(fifo_order_proven=True)),
        ("false_model", lambda q:q["conclusions"].update(model_backed_coding_workers_proven=True)),
        ("false_comparison", lambda q:q["conclusions"].update(same_fixture_vendor_comparison_proven=True)),
        ("fake_overlap", lambda q:q["max_verified_overlap"].update(quad=5)),
        ("fake_hosts", lambda q:q["historical_physical_host_counts"].update(win=4)),
        ("fake_queue", lambda q:q.update(historical_non_fifo_dispatch_inversions=0)),
        ("fake_logger", lambda q:q["exact_original_stdout_hashes"].update(
            {next(iter(q["exact_original_stdout_hashes"])):"0"*64})),
        ("false_cleared", lambda q:q.update(cleanup="CLEANED_NO_RECEIPT")),
        ("invented_samples", lambda q:q.update(statistical_limits="VALID_P95")),
        ("fake_new_effects", lambda q:q["conclusions"].update(new_model_calls=1)),
    ]
    # Log sha values are integrity witnesses but not externally signed receipts.
    for label, action in mutations:
        q = copy.deepcopy(proof)
        action(q)
        try:
            verify_json(q)
        except Refused:
            tested.append(label + "_DENIED")
        else:
            raise AssertionError("FALSE_PASS_" + label)
    need(len(tested) == 18, "NEGATIVE_TEST_COUNT_CHANGED")
    return {"status": "PASS_OFFLINE", "tests": len(tested),
            "model_calls": 0, "fleet_writer_admission": False,
            "git_effects": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("observe", "verify", "selftest"))
    parser.add_argument("--lab-root", default=None)
    args = parser.parse_args()
    if args.mode == "observe":
        need(bool(args.lab_root), "EXPLICIT_EXISTING_LAB_ROOT_REQUIRED")
        data = observe(Path(args.lab_root))
        verify_json(data)
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    need(args.lab_root is None, "OFFLINE_MODE_REJECTS_LIVE_PATH")
    data = load_strict_json(EVIDENCE)
    verify_json(data)
    print(json.dumps(data if args.mode == "verify" else selftest(data),
                     sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, AssertionError, OSError, ValueError, KeyError, TypeError,
            AttributeError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":str(exc)[:180],
                          "model_calls":0, "git_effects":0}, sort_keys=True))
        raise SystemExit(2)
