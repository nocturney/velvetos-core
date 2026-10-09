#!/usr/bin/env python3
"""Office #612: passive, scoped native RSS/CPU observation of a real LAB worker.

The observer never launches or stops a worker, model, scheduler, printer,
browser, external API, or production action. It watches only the exact
OS-birth-bound Worker + Aider process pair for one fresh, explicit synthetic
Task Envelope, via the original canonical kernel-pin and RUNNING journal.
Aider is NOT the Ollama inference server: these samples are only two Python
processes and cannot be labelled total model CPU/RAM or GPU/VRAM.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import sys
import time

import vf_office_v2_p0_kernel_identity as kernel
import vf_office_v2_p0_native_resource_probe_lab as native

SCHEMA = "velvetos.office-v2.p0-owned-worker-aider-cpu-rss-observation.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SCOPE = "ONE_FRESH_SYNTHETIC_WORKER_AIDER_PAIR_ONLY"
SAMPLES = 12
MAX_FILE = 1024 * 1024
MODEL = "qwen3.5:4b"
MODEL_DIGEST = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"


def require(condition, reason):
    if not condition:
        raise kernel.Refused(reason)


def byte_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def seal(value):
    result = copy.deepcopy(value)
    result.pop("observation_sha256", None)
    result["observation_sha256"] = kernel.digest(result)
    return result


def read_exact(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "UNSAFE_OR_MISSING_SOURCE_FILE")
    before = p.stat()
    require(0 < before.st_size <= MAX_FILE, "UNBOUNDED_JSON_SOURCE")
    raw = p.read_bytes()
    after = p.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "FILE_CHANGED_DURING_READ")
    try:
        item = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise kernel.Refused("BAD_OR_PARTIALLY_WRITTEN_JSON")
    require(isinstance(item, dict), "OBJECT_REQUIRED")
    return item, byte_sha(raw)


def save_new(path, value):
    p = Path(path)
    require(not p.exists() and not p.is_symlink(), "ORIGINAL_OBSERVATION_MUST_NOT_OVERWRITE")
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def task_dir(raw):
    p = Path(raw)
    require(p.is_absolute() and p.name == "envelope.json"
            and p.parent.name.startswith("p0-observed-worker-")
            and p.parent.parent.name.startswith("p0-observed-worker-")
            and p.parent.parent.parent.name == "AgentEnvelopeLab"
            and all(not a.is_symlink() for a in (p, p.parent, p.parent.parent,
                                                  p.parent.parent.parent))
            and ".." not in p.parts, "ONLY_EXPLICIT_FRESH_TASK_UNDER_AGENT_ENVELOPE_LAB")
    require(p.parent.is_dir(), "TASK_DIRECTORY_MISSING")
    return p


def observation_dir(raw, new=False):
    p = Path(raw)
    require(p.is_absolute() and p.name.startswith("p0-real-observer-")
            and p.parent.name == "AgentEnvelopeLab"
            and p.parent.is_dir() and not p.parent.is_symlink()
            and not p.is_symlink() and ".." not in p.parts,
            "OWNED_OBSERVATION_DIR_ONLY")
    if new:
        require(not p.exists(), "OBSERVATION_DIR_ALREADY_EXISTS")
    else:
        require(p.is_dir(), "OBSERVATION_DIR_ABSENT")
    return p


def envelope_pins(envelope):
    kernel.checked_env(envelope, local=True)
    require(envelope.get("kernel_birth_capture") ==
            "REQUIRE_OS_BIRTH_BEFORE_QA_V1", "OS_BIRTH_REQUIRED_FOR_MODEL_RESOURCE")
    require(envelope.get("executor", {}).get("model") == MODEL
            and envelope.get("executor", {}).get("model_digest") == MODEL_DIGEST,
            "UNEXPECTED_LOCAL_MODEL")
    require(envelope.get("executor", {}).get("ollama_port") == 11556
            and envelope.get("budget", {}).get("max_attempts") == 1
            and envelope.get("budget", {}).get("max_cost_usd") == 0,
            "UNAUTHORIZED_EXECUTOR_OR_BUDGET")
    return True


def assert_live(expected):
    actual = kernel.sample(expected["pid"])
    require(actual is not None and
            kernel.match(expected, actual) == "SAME_KERNEL_INSTANCE_AT_SNAPSHOT",
            "MODEL_WORKER_OR_AIDER_KERNEL_BIRTH_NOT_LIVE")
    return actual


def sample_pair(pin, number, started):
    worker = pin["worker"]
    aider = pin["aider"]
    assert_live(worker)
    assert_live(aider)
    # Native OS metrics read only the two exact, validated process IDs.
    w = native.usage(worker["pid"])
    a = native.usage(aider["pid"])
    # Reject PID recycling/reparenting during the metric query window.
    assert_live(worker)
    assert_live(aider)
    return {
        "index": number, "utc": datetime.now(timezone.utc).isoformat(),
        "monotonic_offset_ms": max(1, round((time.monotonic() - started)*1000)),
        "worker": {"pid": worker["pid"], "birth_us": worker["birth_us"],
                   "rss_bytes": w["rss_bytes"], "cpu_time_ms": w["cpu_time_ms"]},
        "aider": {"pid": aider["pid"], "birth_us": aider["birth_us"],
                  "rss_bytes": a["rss_bytes"], "cpu_time_ms": a["cpu_time_ms"]},
    }


def validate(row):
    require(isinstance(row, dict) and row.get("schema") == SCHEMA
            and row.get("issue") == ISSUE and row.get("scope") == SCOPE,
            "MODEL_OBSERVER_SCOPE_DRIFT")
    require(isinstance(row.get("task_id"), str) and
            bool(re.fullmatch("p0-observed-worker-[A-Za-z0-9_.-]{4,95}",
                              row["task_id"])),
            "OWNED_TASK_ID_INVALID")
    require(isinstance(row.get("host"), str) and row["host"]
            and row.get("model") == MODEL and row.get("model_digest") == MODEL_DIGEST,
            "MODEL_PIN_OR_HOST_MISSING")
    for field in ("worker_birth", "aider_birth"):
        kernel.require_row(row.get(field))
    worker, aider = row["worker_birth"], row["aider_birth"]
    require(worker["pid"] != aider["pid"] and
            worker["source"] == aider["source"] and
            aider["ppid"] == worker["pid"] and
            aider["birth_us"] >= worker["birth_us"],
            "WORKER_AIDER_NATIVE_OS_LINEAGE_DRIFT")
    require(row.get("kernel_pin_sha256") and
            re.fullmatch("[a-f0-9]{64}", row["kernel_pin_sha256"])
            and row.get("envelope_sha256") and
            re.fullmatch("[a-f0-9]{64}", row["envelope_sha256"])
            and row.get("running_journal_raw_sha256") and
            re.fullmatch("[a-f0-9]{64}", row["running_journal_raw_sha256"]),
            "PIN_ENVELOPE_JOURNAL_REQUIRED")
    for flag in ("independent_worker_pin_validated_against_running_journal",
                 "os_birth_matched_before_after_every_metric_sample",
                 "only_pinned_worker_and_aider_pids_sampled",
                 "read_only_no_model_worker_control"):
        require(row.get(flag) is True, "REQUIRED_OBSERVER_PROOF_ABSENT_"+flag)
    for flag in ("model_inference_server_measured", "gpu_vram_measured",
                 "full_process_family_attributed", "autonomous_recovery_proven",
                 "cross_host_fencing_verified", "canonical_fleet_lease",
                 "all_orphans_excluded", "production_writer",
                 "automatic_retries_authorized", "model_started_by_observer"):
        require(row.get(flag) is False, "FALSE_MODEL_OR_AUTHORITY_CLAIM_"+flag)
    require(type(row.get("paid_api_spend_usd")) is int
            and row["paid_api_spend_usd"] == 0 and
            type(row.get("model_calls_by_observer")) is int
            and row["model_calls_by_observer"] == 0,
            "FALSE_PAID_OR_MODEL_CALL")
    require(row.get("sample_count") == SAMPLES
            and isinstance(row.get("samples"), list)
            and len(row["samples"]) == SAMPLES,
            "EXACT_BOUNDED_PAIR_SAMPLE_COUNT_REQUIRED")
    prior_ms = -1
    prior_cpu = {"worker": -1, "aider": -1}
    max_rss = {"worker": 0, "aider": 0}
    max_pair = 0
    for idx, sample in enumerate(row["samples"], 1):
        require(isinstance(sample, dict) and
                type(sample.get("index")) is int and sample["index"] == idx
                and isinstance(sample.get("utc"), str) and sample["utc"]
                and type(sample.get("monotonic_offset_ms")) is int
                and sample["monotonic_offset_ms"] > prior_ms,
                "TIMESTAMP_OR_SAMPLE_INDEX_DRIFT")
        prior_ms = sample["monotonic_offset_ms"]
        pair = 0
        for key, expected in (("worker", worker), ("aider", aider)):
            metric = sample.get(key)
            require(isinstance(metric, dict)
                    and type(metric.get("pid")) is int
                    and metric["pid"] == expected["pid"]
                    and type(metric.get("birth_us")) is int
                    and metric["birth_us"] == expected["birth_us"]
                    and type(metric.get("rss_bytes")) is int
                    and 1024**2 <= metric["rss_bytes"] < 1024**4
                    and type(metric.get("cpu_time_ms")) is int
                    and metric["cpu_time_ms"] >= prior_cpu[key],
                    "SAMPLE_PROCESS_BIRTH_OR_COUNTER_DRIFT")
            prior_cpu[key] = metric["cpu_time_ms"]
            max_rss[key] = max(max_rss[key], metric["rss_bytes"])
            pair += metric["rss_bytes"]
        max_pair = max(pair, max_pair)
    require(row.get("observed_peak_worker_rss_bytes") == max_rss["worker"]
            and row.get("observed_peak_aider_rss_bytes") == max_rss["aider"]
            and row.get("observed_peak_pair_rss_bytes") == max_pair
            and row.get("observed_worker_cpu_delta_ms") ==
                row["samples"][-1]["worker"]["cpu_time_ms"] -
                row["samples"][0]["worker"]["cpu_time_ms"]
            and row.get("observed_aider_cpu_delta_ms") ==
                row["samples"][-1]["aider"]["cpu_time_ms"] -
                row["samples"][0]["aider"]["cpu_time_ms"],
            "PAIR_PEAK_OR_CPU_SUMMARY_DRIFT")
    require(row.get("observation_sha256") == seal(row)["observation_sha256"],
            "SELF_HASH_DRIFT")
    return True


def build_record(env, pin, journal_bytes_hash, samples):
    worker = pin["worker"]
    aider = pin["aider"]
    return seal({
        "schema": SCHEMA, "issue": ISSUE, "scope": SCOPE,
        "host": env["host"], "task_id": env["task_id"],
        "model": env["executor"]["model"],
        "model_digest": env["executor"]["model_digest"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "envelope_sha256": kernel.digest(env),
        "kernel_pin_sha256": pin["pin_sha256"],
        "running_journal_raw_sha256": journal_bytes_hash,
        "worker_birth": worker, "aider_birth": aider,
        "sample_count": len(samples), "samples": samples,
        "observed_peak_worker_rss_bytes":
            max(x["worker"]["rss_bytes"] for x in samples),
        "observed_peak_aider_rss_bytes":
            max(x["aider"]["rss_bytes"] for x in samples),
        "observed_peak_pair_rss_bytes":
            max(x["worker"]["rss_bytes"] + x["aider"]["rss_bytes"]
                for x in samples),
        "observed_worker_cpu_delta_ms":
            samples[-1]["worker"]["cpu_time_ms"] -
            samples[0]["worker"]["cpu_time_ms"],
        "observed_aider_cpu_delta_ms":
            samples[-1]["aider"]["cpu_time_ms"] -
            samples[0]["aider"]["cpu_time_ms"],
        "independent_worker_pin_validated_against_running_journal": True,
        "os_birth_matched_before_after_every_metric_sample": True,
        "only_pinned_worker_and_aider_pids_sampled": True,
        "read_only_no_model_worker_control": True,
        "model_inference_server_measured": False,
        "gpu_vram_measured": False,
        "full_process_family_attributed": False,
        "autonomous_recovery_proven": False,
        "cross_host_fencing_verified": False,
        "canonical_fleet_lease": False,
        "all_orphans_excluded": False,
        "production_writer": False,
        "automatic_retries_authorized": False,
        "model_started_by_observer": False,
        "model_calls_by_observer": 0,
        "paid_api_spend_usd": 0,
    })


def observe(task_arg, root_arg):
    task = task_dir(task_arg)
    root = observation_dir(root_arg, new=True)
    env, _ = read_exact(task)
    envelope_pins(env)
    require(env["task_id"] == task.parent.name
            and Path(env["worktree_path"]).is_relative_to(task.parent),
            "TASK_DIRECTORY_ENVELOPE_PATH_MISMATCH")
    out = task.parent / "output"
    journal_path = out / "receipt.json.running"
    pin_path = out / "kernel-pin.json"
    require(not (out / "receipt.json").exists()
            and not journal_path.exists() and not pin_path.exists(),
            "WORKER_ALREADY_STARTED_OR_OUTCOME_UNKNOWN")
    root.mkdir(exist_ok=False)
    save_new(root / "ready.json", {
        "scope": SCOPE, "state": "PASSIVE_SAMPLER_READY_NOT_OWNER",
        "task_id": env["task_id"], "host": platform.node(),
        "envelope_sha256": kernel.digest(env), "model_calls": 0,
    })
    started = time.monotonic()
    deadline = started + 26
    pin = None
    journal_hash = None
    while time.monotonic() < deadline:
        if journal_path.is_file() and pin_path.is_file():
            try:
                journal, journal_hash = read_exact(journal_path)
                pin, _ = read_exact(pin_path)
                kernel.checked_pin(env, journal, pin)
                break
            except (kernel.Refused, ValueError, OSError):
                # Allow a child only a very short window to fsync its fresh
                # evidence; mismatches still fail after bounded deadline.
                pass
        time.sleep(.035)
    require(pin is not None and journal_hash is not None,
            "PINNED_WORKER_JOURNAL_NOT_OBSERVED_WITHIN_LIMIT")
    require(pin.get("worker") and pin.get("aider"),
            "OWNER_LINEAGE_MISSING")
    rows = []
    for index in range(1, SAMPLES + 1):
        rows.append(sample_pair(pin, index, started))
        if index < SAMPLES:
            time.sleep(.65)
    record = build_record(env, pin, journal_hash, rows)
    validate(record)
    save_new(root / "report.json", record)
    return {
        "status": "PASS_PINNED_REAL_LAB_WORKER_AIDER_CPU_RSS_OBSERVED",
        "task_id": record["task_id"], "host": record["host"],
        "samples": SAMPLES,
        "peak_worker_rss_bytes": record["observed_peak_worker_rss_bytes"],
        "peak_aider_rss_bytes": record["observed_peak_aider_rss_bytes"],
        "peak_pair_rss_bytes": record["observed_peak_pair_rss_bytes"],
        "worker_cpu_delta_ms": record["observed_worker_cpu_delta_ms"],
        "aider_cpu_delta_ms": record["observed_aider_cpu_delta_ms"],
        "observation_sha256": record["observation_sha256"],
        "model_calls_by_observer": 0,
        "inference_server_included": False,
        "gpu_vram_measured": False,
        "production_authority": False,
        "distributed_fencing_verified": False,
    }


def sample_fixture():
    env = {
        "host": "synthetic-mac-host",
        "task_id": "p0-observed-worker-synthetic-001",
        "executor": {"model": MODEL, "model_digest": MODEL_DIGEST},
    }
    wk = {"pid": 24000, "ppid": 23990, "birth_us": 1791573000000000,
          "pgid": 24000, "source": "PSUTIL_OS_CREATE_TIME"}
    aid = {"pid": 24001, "ppid": 24000, "birth_us": 1791573000000700,
           "pgid": 24001, "source": "PSUTIL_OS_CREATE_TIME"}
    pin = {"worker": wk, "aider": aid,
           "pin_sha256": "d"*64}
    data = [{
        "index": i+1,
        "utc": "2026-10-09T00:00:00+00:00",
        "monotonic_offset_ms": (i+1)*700,
        "worker": {"pid": 24000, "birth_us": wk["birth_us"],
                   "rss_bytes": 28_000_000 + i*3_000,
                   "cpu_time_ms": 100 + 2*i},
        "aider": {"pid": 24001, "birth_us": aid["birth_us"],
                  "rss_bytes": 155_000_000 + i*25_000,
                  "cpu_time_ms": 800 + 40*i},
    } for i in range(SAMPLES)]
    return build_record(env, pin, "f"*64, data)


def selftest():
    require(isinstance(platform.node(), str) and bool(platform.node()),
            "OS_HOST_IDENTITY_REQUIRED")
    good = sample_fixture()
    validate(good)
    cases = ["valid_offline_claim_shape_not_execution"]
    bad = [
        ("wrong_scope", lambda d: d.update(scope="FLEET")),
        ("fake_host", lambda d: d.update(host="")),
        ("fake_model", lambda d: d.update(model="qwen3.5:9b")),
        ("wrong_model_digest", lambda d: d.update(model_digest="0"*64)),
        ("wrong_task_id", lambda d: d.update(task_id="customer-order")),
        ("missing_pin", lambda d: d.update(kernel_pin_sha256="")),
        ("missing_running", lambda d: d.update(running_journal_raw_sha256="")),
        ("mismatched_worker", lambda d: d["aider_birth"].update(ppid=1)),
        ("changed_birth", lambda d: d["samples"][0]["aider"].update(birth_us=1)),
        ("changed_pid", lambda d: d["samples"][0]["worker"].update(pid=1)),
        ("missing_sample", lambda d: d["samples"].pop()),
        ("duplicate_sample", lambda d: d["samples"][2].update(index=2)),
        ("stale_timestamp", lambda d: d["samples"][3].update(monotonic_offset_ms=0)),
        ("cpu_rollover", lambda d: d["samples"][3]["aider"].update(cpu_time_ms=0)),
        ("false_rss", lambda d: d["samples"][2]["worker"].update(rss_bytes=-2)),
        ("invented_peak", lambda d: d.update(observed_peak_pair_rss_bytes=1)),
        ("wrong_cpu_delta", lambda d: d.update(observed_aider_cpu_delta_ms=1)),
        ("not_pinned", lambda d: d.update(os_birth_matched_before_after_every_metric_sample=False)),
        ("falsely_models_ollama", lambda d: d.update(model_inference_server_measured=True)),
        ("falsely_gpu", lambda d: d.update(gpu_vram_measured=True)),
        ("falsely_fenced", lambda d: d.update(cross_host_fencing_verified=True)),
        ("falsely_auto_retry", lambda d: d.update(automatic_retries_authorized=True)),
        ("falsely_model_started", lambda d: d.update(model_started_by_observer=True)),
        ("paid_call", lambda d: d.update(paid_api_spend_usd=1)),
    ]
    for label, f in bad:
        modified = copy.deepcopy(good)
        f(modified)
        try:
            validate(seal(modified))
        except kernel.Refused:
            cases.append(label+"_rejected")
        else:
            raise AssertionError("FALSE_RESEALED_EVIDENCE_ACCEPTED:"+label)
    tampered = dict(good, observation_sha256="0"*64)
    try:
        validate(tampered)
    except kernel.Refused:
        cases.append("direct_byte_tamper_rejected")
    else:
        raise AssertionError("UNSEALED_EVIDENCE_ACCEPTED")
    require(len(cases) == 26, "SELFTEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE", "tests":len(cases),
            "cases":cases, "model_calls_by_observer":0,
            "live_os_calls":0, "automatic_retries_authorized":False,
            "gpu_vram_measured":False,
            "production_authority":False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("selftest")
    trial = sub.add_parser("observe")
    trial.add_argument("--envelope", required=True)
    trial.add_argument("--root", required=True)
    replay = sub.add_parser("verify")
    replay.add_argument("--root", required=True)
    args = parser.parse_args()
    if args.mode == "selftest":
        result = selftest()
    elif args.mode == "observe":
        result = observe(args.envelope, args.root)
    else:
        root = observation_dir(args.root)
        row, _ = read_exact(root / "report.json")
        validate(row)
        result = {
            "status": "PASS_OFFLINE_HISTORIC_OBSERVER_SHAPE_ONLY",
            "task_id": row["task_id"],
            "observation_sha256": row["observation_sha256"],
            "samples": len(row["samples"]),
            "model_calls_by_observer": 0,
            "os_birth_currently_reobserved": False,
            "production_authority": False,
        }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (kernel.Refused, OSError, ValueError, TypeError, KeyError,
            AssertionError) as error:
        print(json.dumps({
            "status": "FAIL_CLOSED", "reason": str(error)[:160],
            "automatic_retries_authorized": False,
            "model_calls_by_observer": 0,
            "production_authority": False,
        }, sort_keys=True))
        raise SystemExit(2)
