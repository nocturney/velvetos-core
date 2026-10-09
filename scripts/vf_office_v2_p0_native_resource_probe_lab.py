#!/usr/bin/env python3
"""Office #612 P0: bounded native OS process-resource observation LAB.

Samples only an exclusively created, synthetic child using PID+OS birth from
the canonical kernel helper. Read-only metric interfaces; no existing model,
GUI, business process, scheduler, production effects or global process kills.
CI runs only pure selftest / historical receipt verification, never live().
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

import vf_office_v2_p0_kernel_identity as kernel

SCHEMA = "velvetos.office-v2.p0-native-owned-process-resource-lab.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
COUNT = 6
SIZE = 12 * 1024 * 1024
RESOURCE = "EXCLUSIVE_TEMP_PYTHON_CHILD_ONLY"


def require(condition, reason):
    if not condition:
        raise kernel.Refused(reason)


def sha_bytes(content):
    return hashlib.sha256(content).hexdigest()


def seal(value):
    row = copy.deepcopy(value)
    row.pop("receipt_sha256", None)
    row["receipt_sha256"] = sha_bytes(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8"))
    return row


def lab_dir(raw, new=False):
    path = Path(raw)
    require(path.is_absolute() and path.name.startswith("p0-resource-probe-")
            and path.parent.name == "AgentEnvelopeLab"
            and not path.is_symlink() and path.parent.is_dir()
            and not path.parent.is_symlink()
            and ".." not in path.parts, "EXCLUSIVE_AGENT_ENVELOPE_LAB_ONLY")
    if new:
        require(not path.exists(), "FRESH_RESOURCE_PROBE_REQUIRED")
    else:
        require(path.is_dir(), "RESOURCE_PROBE_DIR_MISSING")
    return path


def save_new(path, value):
    p = Path(path)
    require(not p.exists() and not p.is_symlink(), "RECEIPT_ALREADY_EXISTS")
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def read_json(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= 1048576,
            "BAD_OR_UNSAFE_RECEIPT")
    before = p.stat()
    raw = p.read_bytes()
    after = p.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "RECEIPT_CHANGED_DURING_READ")
    data = json.loads(raw.decode("utf-8"))
    require(isinstance(data, dict), "JSON_OBJECT_REQUIRED")
    return data


def usage(pid):
    """Get only memory/CPU *of this exact process*, not a host-wide scan."""
    if os.name == "nt":
        command = (f"$p=Get-Process -Id {pid} -ErrorAction Stop; "
                   "@{pid=[int]$p.Id;rss_bytes=[long]$p.WorkingSet64;"
                   "cpu_time_ms=[long][Math]::Round($p.CPU * 1000)} | "
                   "ConvertTo-Json -Compress")
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=9)
        except (OSError, subprocess.TimeoutExpired):
            raise kernel.Refused("WINDOWS_PROCESS_METRIC_UNAVAILABLE")
        require(proc.returncode == 0 and len(proc.stdout) < 2000,
                "WINDOWS_PROCESS_METRIC_QUERY_FAILED")
        try:
            row = json.loads(proc.stdout)
        except ValueError:
            raise kernel.Refused("WINDOWS_PROCESS_METRIC_INVALID_JSON")
    else:
        try:
            import psutil
        except ImportError:
            raise kernel.Refused("PSUTIL_REQUIRED_FOR_OS_METRICS")
        try:
            p = psutil.Process(pid)
            cpu = p.cpu_times()
            row = {"pid": pid, "rss_bytes": int(p.memory_info().rss),
                   "cpu_time_ms": int(round(1000 * (cpu.user + cpu.system)))}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            raise kernel.Refused("PINNED_PROCESS_RESOURCE_UNAVAILABLE")
    require(isinstance(row, dict) and type(row.get("pid")) is int
            and row["pid"] == pid and type(row.get("rss_bytes")) is int
            and row["rss_bytes"] > 0 and
            type(row.get("cpu_time_ms")) is int and row["cpu_time_ms"] >= 0,
            "PROCESS_METRIC_SHAPE_DRIFT")
    return row


def validate(row):
    require(isinstance(row, dict) and row.get("schema") == SCHEMA
            and row.get("issue") == ISSUE
            and row.get("scope") == RESOURCE, "REPORT_SCOPE_DRIFT")
    identity = row.get("owner_child_kernel_birth")
    kernel.require_row(identity)
    require(row.get("host") and isinstance(row["host"], str)
            and identity.get("source") == row.get("kernel_backend"),
            "PINNED_HOST_OR_BACKEND_DRIFT")
    for key in ("only_owned_child_sampled", "sampled_with_os_birth_check_each_time",
                "original_child_alive_at_sample_times",
                "owned_child_finished_after_stop", "cpu_rss_sampled"):
        require(row.get(key) is True, "FALSE_REQUIRED_OBSERVATION_" + key)
    for key in ("model_invocations", "paid_api_spend_usd"):
        require(type(row.get(key)) is int and row[key] == 0,
                "FALSE_MODEL_OR_COST_CLAIM_" + key)
    for key in ("canonical_fleet_lease", "distributed_fencing_verified",
                "all_possible_descendants_excluded", "autonomous_recovery_proven",
                "production_authority", "gpu_vram_measured",
                "host_wide_processes_inspected", "new_job_execution_authorized"):
        require(row.get(key) is False, "UNPROVEN_AUTHORITY_OR_SCOPE_" + key)
    assert_hash = row.get("source_sha256")
    require(isinstance(assert_hash, str) and
            bool(re.fullmatch("[0-9a-f]{64}", assert_hash)),
            "SOURCE_HASH_REQUIRED")
    samples = row.get("samples")
    require(isinstance(samples, list) and len(samples) == COUNT
            and type(row.get("sample_count")) is int
            and row["sample_count"] == COUNT, "EXACT_BOUNDED_SAMPLE_COUNT")
    previous_monotonic, previous_cpu = -1, -1
    rss = []
    for i, item in enumerate(samples):
        require(isinstance(item, dict) and type(item.get("index")) is int
                and item["index"] == i + 1 and
                item.get("kernel_pid") == identity["pid"]
                and item.get("kernel_birth_us") == identity["birth_us"]
                and item.get("kernel_source") == identity["source"]
                and isinstance(item.get("observed_utc"), str)
                and bool(item["observed_utc"]),
                "SAMPLE_IDENTITY_DRIFT")
        offset, cpu, memory = (item.get("monotonic_offset_ms"),
                               item.get("cpu_time_ms"), item.get("rss_bytes"))
        require(type(offset) is int and offset > previous_monotonic
                and type(cpu) is int and cpu >= previous_cpu
                and type(memory) is int and memory >= 1024 * 1024
                and memory < 1024**4, "SAMPLE_METRIC_NONMONOTONIC_OR_IMPLAUSIBLE")
        previous_monotonic, previous_cpu = offset, cpu
        rss.append(memory)
    require(row.get("peak_rss_bytes") == max(rss)
            and row.get("min_rss_bytes") == min(rss)
            and row.get("first_cpu_time_ms") == samples[0]["cpu_time_ms"]
            and row.get("last_cpu_time_ms") == samples[-1]["cpu_time_ms"],
            "REPORT_CPU_RSS_SUMMARY_DRIFT")
    signed = seal(row)
    require(row.get("receipt_sha256") == signed["receipt_sha256"],
            "RECEIPT_SELF_HASH_DRIFT")
    return True


def _fixture(root):
    root = lab_dir(root)
    # Touch individual memory pages to make the resource sample meaningful.
    data = bytearray(SIZE)
    for i in range(0, SIZE, 4096):
        data[i] = (i // 4096) % 251
    save_new(root / "ready.json", {"pid": os.getpid(), "allocated_bytes": SIZE})
    deadline = time.monotonic() + 22
    checksum = 0
    while time.monotonic() < deadline and not (root / "stop.flag").exists():
        checksum = (checksum + sum(data[::4096])) % 65521
        time.sleep(.018)
    del data
    return checksum


def live(raw_root):
    root = lab_dir(raw_root, new=True)
    root.mkdir(exist_ok=False)
    started = time.monotonic()
    child = None
    try:
        opts = {"cwd": root, "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if os.name == "nt":
            opts["creationflags"] = (subprocess.CREATE_NO_WINDOW |
                                     subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            opts["start_new_session"] = True
        child = subprocess.Popen(
            [sys.executable, "-B", str(Path(__file__).resolve()),
             "_fixture", "--root", str(root)], **opts)
        deadline = time.monotonic() + 9
        ready = root / "ready.json"
        while not ready.is_file() and time.monotonic() < deadline:
            require(child.poll() is None, "OWNED_CHILD_DIED_BEFORE_READY")
            time.sleep(.04)
        require(ready.is_file(), "CHILD_NOT_READY_IN_BOUNDED_WINDOW")
        meta = read_json(ready)
        require(meta.get("pid") == child.pid and meta.get("allocated_bytes") == SIZE,
                "WRONG_FIXTURE_OR_PID")
        initial = kernel.sample(child.pid)
        require(initial is not None, "OS_BIRTH_UNAVAILABLE")
        kernel.require_row(initial)
        rows = []
        for i in range(COUNT):
            require(child.poll() is None, "OWNED_CHILD_EXITED_DURING_SAMPLING")
            checked = kernel.sample(child.pid)
            require(checked is not None and
                    kernel.match(initial, checked) ==
                    "SAME_KERNEL_INSTANCE_AT_SNAPSHOT",
                    "PINNED_CHILD_BIRTH_OR_PID_CHANGED")
            metric = usage(child.pid)
            require(child.poll() is None, "OWNED_CHILD_EXITED_DURING_METRIC")
            rows.append({
                "index": i + 1,
                "observed_utc": datetime.now(timezone.utc).isoformat(),
                "monotonic_offset_ms": max(1, round((time.monotonic() - started) * 1000)),
                "kernel_pid": initial["pid"],
                "kernel_birth_us": initial["birth_us"],
                "kernel_source": initial["source"],
                "rss_bytes": metric["rss_bytes"],
                "cpu_time_ms": metric["cpu_time_ms"],
            })
            if i + 1 < COUNT:
                time.sleep(.19)
        (root / "stop.flag").touch(exist_ok=False)
        child.wait(timeout=8)
        require(child.poll() is not None, "OWNED_CHILD_NOT_FINISHED")
        report = seal({
            "schema": SCHEMA, "issue": ISSUE, "scope": RESOURCE,
            "host": platform.node(),
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "owner_child_kernel_birth": initial,
            "kernel_backend": initial["source"],
            "only_owned_child_sampled": True,
            "sampled_with_os_birth_check_each_time": True,
            "original_child_alive_at_sample_times": True,
            "owned_child_finished_after_stop": True,
            "cpu_rss_sampled": True,
            "sample_count": COUNT, "samples": rows,
            "min_rss_bytes": min(x["rss_bytes"] for x in rows),
            "peak_rss_bytes": max(x["rss_bytes"] for x in rows),
            "first_cpu_time_ms": rows[0]["cpu_time_ms"],
            "last_cpu_time_ms": rows[-1]["cpu_time_ms"],
            "source_sha256": sha_bytes(Path(__file__).read_bytes()),
            "canonical_fleet_lease": False,
            "distributed_fencing_verified": False,
            "all_possible_descendants_excluded": False,
            "autonomous_recovery_proven": False,
            "production_authority": False,
            "gpu_vram_measured": False,
            "host_wide_processes_inspected": False,
            "new_job_execution_authorized": False,
            "model_invocations": 0, "paid_api_spend_usd": 0,
        })
        validate(report)
        save_new(root / "report.json", report)
        return {"status": "PASS_PINNED_OWNED_PROCESS_CPU_RSS_LAB",
                "host": report["host"], "child_pid": initial["pid"],
                "native_birth_us": initial["birth_us"],
                "native_source": initial["source"], "samples": COUNT,
                "rss_peak_bytes": report["peak_rss_bytes"],
                "cpu_delta_ms": rows[-1]["cpu_time_ms"] - rows[0]["cpu_time_ms"],
                "receipt_sha256": report["receipt_sha256"],
                "model_invocations": 0, "gpu_vram_measured": False,
                "distributed_fencing_verified": False}
    finally:
        (root / "stop.flag").touch(exist_ok=True)
        if child is not None and child.poll() is None:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Only the exact child handle created by this LAB, never others.
                child.terminate()
                try:
                    child.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    print("OWNED_CHILD_NOT_CONFIRMED_EXIT_MANUAL_REVIEW",
                          file=sys.stderr)


def sample_success():
    identity = {"pid": 31000, "ppid": 30999, "pgid": None,
                "birth_us": 1791500000000000,
                "source": "WINDOWS_CIM_CREATION_DATE"}
    rows = [{"index": i+1, "observed_utc": "2026-10-09T00:00:00+00:00",
             "monotonic_offset_ms": 300*(i+1), "kernel_pid": 31000,
             "kernel_birth_us": identity["birth_us"],
             "kernel_source": identity["source"],
             "rss_bytes": 20_000_000 + i*100_000,
             "cpu_time_ms": 60 + i*12}
            for i in range(COUNT)]
    return seal({
        "schema": SCHEMA, "issue": ISSUE, "scope": RESOURCE, "host": "fixture-host",
        "owner_child_kernel_birth": identity,
        "kernel_backend": identity["source"],
        "only_owned_child_sampled": True,
        "sampled_with_os_birth_check_each_time": True,
        "original_child_alive_at_sample_times": True,
        "owned_child_finished_after_stop": True,
        "cpu_rss_sampled": True,
        "sample_count": COUNT, "samples": rows,
        "min_rss_bytes": rows[0]["rss_bytes"],
        "peak_rss_bytes": rows[-1]["rss_bytes"],
        "first_cpu_time_ms": rows[0]["cpu_time_ms"],
        "last_cpu_time_ms": rows[-1]["cpu_time_ms"],
        "source_sha256": "a"*64,
        "canonical_fleet_lease": False, "distributed_fencing_verified": False,
        "all_possible_descendants_excluded": False,
        "autonomous_recovery_proven": False, "production_authority": False,
        "gpu_vram_measured": False, "host_wide_processes_inspected": False,
        "new_job_execution_authorized": False,
        "model_invocations": 0, "paid_api_spend_usd": 0,
    })


def selftest():
    good = sample_success()
    validate(good)
    cases = ["positive_shape_only_no_os_launched"]
    negatives = [
        ("false_scope", lambda x: x.update(scope="ALL_OS_PROCESS_TREE")),
        ("false_pid", lambda x: x["samples"][2].update(kernel_pid=3)),
        ("wrong_birth", lambda x: x["samples"][3].update(kernel_birth_us=0)),
        ("missing_sample", lambda x: x["samples"].pop()),
        ("false_index", lambda x: x["samples"][0].update(index=9)),
        ("false_low_rss", lambda x: x["samples"][1].update(rss_bytes=0)),
        ("false_cpu", lambda x: x["samples"][3].update(cpu_time_ms=0)),
        ("false_offset", lambda x: x["samples"][4].update(monotonic_offset_ms=1)),
        ("fake_peak", lambda x: x.update(peak_rss_bytes=1)),
        ("fake_cpu_sum", lambda x: x.update(last_cpu_time_ms=10000)),
        ("not_pinned", lambda x: x.update(sampled_with_os_birth_check_each_time=False)),
        ("not_finished", lambda x: x.update(owned_child_finished_after_stop=False)),
        ("false_gpu_metric", lambda x: x.update(gpu_vram_measured=True)),
        ("false_fleet_lease", lambda x: x.update(canonical_fleet_lease=True)),
        ("false_fence", lambda x: x.update(distributed_fencing_verified=True)),
        ("false_auto_recovery", lambda x: x.update(autonomous_recovery_proven=True)),
        ("false_production", lambda x: x.update(production_authority=True)),
        ("false_model_calls", lambda x: x.update(model_invocations=1)),
        ("paid_api", lambda x: x.update(paid_api_spend_usd=1)),
        ("false_global_scan", lambda x: x.update(host_wide_processes_inspected=True)),
    ]
    for label, mutate in negatives:
        changed = copy.deepcopy(good)
        mutate(changed)
        changed = seal(changed)  # negative must be rejected even if re-sealed
        try:
            validate(changed)
        except kernel.Refused:
            cases.append(label + "_denied")
        else:
            raise AssertionError("FALSE_RESEALED_METRIC_ACCEPTED:" + label)
    raw = dict(good, receipt_sha256="0"*64)
    try:
        validate(raw)
    except kernel.Refused:
        cases.append("raw_hash_tamper_denied")
    else:
        raise AssertionError("FALSE_RAW_HASH_ACCEPTED")
    require(len(cases) == 22, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS_OFFLINE", "tests": len(cases), "cases": cases,
            "native_children_spawned": 0, "model_invocations": 0,
            "production_effects": 0, "gpu_vram_measured": False,
            "distributed_fencing_verified": False,
            "all_possible_descendants_excluded": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("selftest")
    trial = sub.add_parser("live")
    trial.add_argument("--root", required=True)
    replay = sub.add_parser("verify")
    replay.add_argument("--root", required=True)
    fixture = sub.add_parser("_fixture", help=argparse.SUPPRESS)
    fixture.add_argument("--root", required=True)
    args = parser.parse_args()
    if args.mode == "_fixture":
        _fixture(args.root)
        return
    if args.mode == "selftest":
        result = selftest()
    elif args.mode == "live":
        result = live(args.root)
    else:
        target = lab_dir(args.root) / "report.json"
        rec = read_json(target)
        validate(rec)
        result = {"status": "PASS_OFFLINE_SELF_HASH_SHAPE_ONLY",
                  "host": rec["host"], "samples": COUNT,
                  "receipt_sha256": rec["receipt_sha256"],
                  "native_process_currently_attested": False,
                  "gpu_vram_measured": False, "model_invocations": 0,
                  "distributed_fencing_verified": False}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (kernel.Refused, ValueError, OSError, TypeError,
            KeyError, AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:160],
                          "no_automatic_retry": True,
                          "model_invocations": 0,
                          "distributed_fencing_verified": False}, sort_keys=True))
        raise SystemExit(2)
