#!/usr/bin/env python3
"""P0 #612 read-only Mac Ollama inference runner observation of ONE LAB task.

Observer does not start, stop, schedule, retry or authorize a model or worker.
It correlates an original RUNNING journal + OS-birth-pinned Worker/Aider pair
with a single native Ollama serve->runner child and /api/ps model digest.

It CANNOT prove exclusive model use by clients, GPU utilization/VRAM or entire
host/process-tree attribution. CI ONLY invokes pure offline selftest/verify.
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
import time
import urllib.request

import vf_office_v2_p0_kernel_identity as kernel
import vf_office_v2_p0_native_resource_probe_lab as native
from vf_office_v2_p0_owned_worker_aider_sampler import read_exact

SCHEMA = "velvetos.office-v2.p0-one-local-model-runner-passive-resource.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SCOPE = "ONE_HOST_ONE_FRESH_TASK_CORRELATED_MODEL_RUNNER_NOT_EXCLUSIVE_USAGE"
MODEL = "qwen3.5:4b"
DIGEST = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
PORT = 11556
OBS_COUNT = 10
TIMEOUT = 75
OLLAMA_BINARY = "/Users/chris/Velvet/Pilots/OfficeAccelerator/OllamaPilot/v0.40.1/runtime/ollama"
SAFE_HEX = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"p0-ollama-observed-[A-Za-z0-9_.-]{4,95}\Z")


def need(ok, why):
    if not ok:
        raise kernel.Refused(why)


def digest(x):
    return kernel.digest(x)


def seal(obj):
    x = copy.deepcopy(obj)
    x.pop("observation_sha256", None)
    x["observation_sha256"] = digest(x)
    return x


def write_once(path, value):
    p = Path(path)
    need(not p.exists() and not p.is_symlink(), "EXCLUSIVE_OBSERVATION_REQUIRED")
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def envelope_path(raw):
    p = Path(raw)
    need(p.is_absolute() and p.name == "envelope.json"
         and ID.fullmatch(p.parent.name) is not None
         and p.parent.parent.name.startswith("p0-ollama-observed-")
         and p.parent.parent.parent.name == "AgentEnvelopeLab"
         and all(not a.is_symlink() for a in
                 (p, p.parent, p.parent.parent, p.parent.parent.parent)),
         "ONLY_EXPLICIT_NEW_SYNTHETIC_ENVELOPE")
    need(p.is_file(), "ENVELOPE_NOT_FOUND")
    return p


def root_path(raw, new):
    p = Path(raw)
    need(p.is_absolute() and p.name.startswith("p0-ollama-runner-observer-")
         and p.parent.name == "AgentEnvelopeLab"
         and p.parent.is_dir() and not p.parent.is_symlink()
         and not p.is_symlink() and ".." not in p.parts,
         "OBSERVER_MUST_BE_ISOLATED_UNDER_LAB")
    need(not p.exists() if new else p.is_dir(),
         "OBSERVATION_MUST_BE_FRESH_OR_EXISTING")
    return p


def ollama_ps():
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/ps", method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            need(response.status == 200, "OLLAMA_API_HTTP")
            data = json.loads(response.read(100000).decode("utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise kernel.Refused("LOCAL_OLLAMA_API_UNAVAILABLE")
    need(isinstance(data, dict) and isinstance(data.get("models"), list)
         and len(data["models"]) <= 1, "MODEL_API_AMBIGUITY")
    return data["models"]


def psutil_module():
    try:
        import psutil
    except ImportError:
        raise kernel.Refused("PSUTIL_UNAVAILABLE")
    return psutil


def local_ollama_processes():
    """Read-only discovery: only matching executable+args, NOT exclusive clients."""
    psutil = psutil_module()
    serv, runners = [], []
    for p in psutil.process_iter(attrs=["pid", "ppid", "name"]):
        try:
            args = p.cmdline()
            if not args or str(args[0]) != OLLAMA_BINARY:
                continue
            if len(args) >= 2 and args[1] == "serve":
                serv.append(p)
            elif len(args) >= 2 and args[1] == "runner":
                runners.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return serv, runners


def active_model(model):
    need(isinstance(model, dict)
         and model.get("name") == MODEL
         and model.get("digest") == DIGEST
         and model.get("model") in (MODEL, None),
         "MODEL_NAME_DIGEST_MISMATCH")
    size, resident = model.get("size"), model.get("size_vram")
    need(type(size) is int and 0 < size < 64*(1024**3)
         and type(resident) is int and 0 <= resident < 64*(1024**3),
         "OLLAMA_API_METRIC_SHAPE")
    return {"api_model_size_bytes": size,
            "api_size_vram_bytes": resident,
            "api_reported_only_not_gpu_measurement": True}


def is_same(row):
    actual = kernel.sample(row["pid"])
    return actual is not None and kernel.match(row, actual) == "SAME_KERNEL_INSTANCE_AT_SNAPSHOT"


def collect(serve, runner, started, index, api):
    # Kernel time-of-birth prevents attributing a recycled PID.
    need(is_same(serve) and is_same(runner), "OLLAMA_NATIVE_BIRTH_CHANGED")
    value = native.usage(runner["pid"])
    serve_value = native.usage(serve["pid"])
    need(is_same(serve) and is_same(runner), "PROCESS_BIRTH_CHANGED_DURING_READ")
    need(value["pid"] == runner["pid"]
         and serve_value["pid"] == serve["pid"], "METRIC_PID_DRIFT")
    return {
        "index": index,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "monotonic_offset_ms": max(1, round((time.monotonic()-started)*1000)),
        "runner": {"pid": runner["pid"], "birth_us": runner["birth_us"],
                   "rss_bytes": value["rss_bytes"],
                   "cpu_time_ms": value["cpu_time_ms"]},
        "serve": {"pid": serve["pid"], "birth_us": serve["birth_us"],
                  "rss_bytes": serve_value["rss_bytes"],
                  "cpu_time_ms": serve_value["cpu_time_ms"]},
        **api,
    }


def validate(v):
    need(isinstance(v, dict) and v.get("schema") == SCHEMA
         and v.get("scope") == SCOPE and v.get("issue") == ISSUE,
         "LAB_SCHEMA_OR_AUTHORITY_DRIFT")
    need(v.get("host") == "MacMiniOffice.local" and
         isinstance(v.get("task_id"), str) and
         ID.fullmatch(v["task_id"]) is not None,
         "HOST_OR_TASK_ID_INVALID")
    need(v.get("model") == MODEL and v.get("model_digest") == DIGEST,
         "MODEL_PIN_DRIFT")
    for name in ("server_birth", "runner_birth", "worker_birth", "aider_birth"):
        kernel.require_row(v.get(name))
    ser, run, wk, aid = [v[x] for x in
                         ("server_birth", "runner_birth", "worker_birth", "aider_birth")]
    need(ser["source"] == run["source"] == wk["source"] == aid["source"]
         == "PSUTIL_OS_CREATE_TIME" and
         run["ppid"] == ser["pid"] and
         aid["ppid"] == wk["pid"] and
         len({ser["pid"], run["pid"], wk["pid"], aid["pid"]}) == 4,
         "NATIVE_OS_PARENT_CHILD_BINDING_INVALID")
    for key in ("envelope_sha256", "pin_sha256", "running_journal_raw_sha256"):
        need(isinstance(v.get(key), str) and
             SAFE_HEX.fullmatch(v[key]) is not None, "MISSING_PIN_"+key)
    for flag in ("original_pinned_worker_journal_validated",
                 "read_only_api_sole_model_digest_at_samples",
                 "os_native_birth_before_and_after_each_metric",
                 "observer_never_starts_or_controls_any_process"):
        need(v.get(flag) is True, "REQUIRED_OBSERVATION_MISSING_"+flag)
    for flag in ("exclusive_model_client_use_proven", "actual_gpu_vram_measured",
                 "all_model_processes_accounted", "cross_host_fencing_verified",
                 "canonical_fleet_lease", "autonomous_retry_proven",
                 "production_authority", "ollama_config_modified",
                 "exact_model_call_count_known", "model_started_by_observer"):
        need(v.get(flag) is False, "FALSE_AUTHORITY_OR_MEASUREMENT_"+flag)
    need(type(v.get("paid_api_spend_usd")) is int and
         v["paid_api_spend_usd"] == 0 and
         type(v.get("observer_model_calls")) is int and
         v["observer_model_calls"] == 0, "PAID_OR_MODEL_CALL_BY_OBSERVER")
    samples = v.get("samples")
    need(isinstance(samples, list) and
         len(samples) == OBS_COUNT and v.get("sample_count") == OBS_COUNT,
         "EXACT_SAMPLE_COUNT")
    last_time, last_cpu = -1, {"runner": -1, "serve": -1}
    peaks = {"runner": 0, "serve": 0}
    for i, item in enumerate(samples, 1):
        need(isinstance(item, dict)
             and item.get("index") == i
             and type(item.get("monotonic_offset_ms")) is int
             and item["monotonic_offset_ms"] > last_time
             and isinstance(item.get("observed_at_utc"), str),
             "SAMPLE_TIMING_OR_INDEX")
        last_time = item["monotonic_offset_ms"]
        for kind, pin in (("runner", run), ("serve", ser)):
            row = item.get(kind)
            need(isinstance(row, dict) and
                 row.get("pid") == pin["pid"] and
                 row.get("birth_us") == pin["birth_us"]
                 and type(row.get("rss_bytes")) is int
                 and 1024**2 <= row["rss_bytes"] < 64*(1024**3)
                 and type(row.get("cpu_time_ms")) is int
                 and row["cpu_time_ms"] >= last_cpu[kind],
                 "RESOURCE_OR_IDENTITY_DRIFT_"+kind)
            last_cpu[kind] = row["cpu_time_ms"]
            peaks[kind] = max(peaks[kind], row["rss_bytes"])
        need(item.get("api_reported_only_not_gpu_measurement") is True
             and type(item.get("api_model_size_bytes")) is int
             and 0 < item["api_model_size_bytes"] < 64*(1024**3)
             and type(item.get("api_size_vram_bytes")) is int
             and 0 <= item["api_size_vram_bytes"] < 64*(1024**3),
             "OLLAMA_RESIDENCY_NOT_GPU_TELEMETRY")
    need(v.get("peak_runner_rss_bytes") == peaks["runner"]
         and v.get("peak_server_rss_bytes") == peaks["serve"]
         and v.get("observed_runner_cpu_delta_ms") ==
             samples[-1]["runner"]["cpu_time_ms"] -
             samples[0]["runner"]["cpu_time_ms"]
         and v.get("observed_server_cpu_delta_ms") ==
             samples[-1]["serve"]["cpu_time_ms"] -
             samples[0]["serve"]["cpu_time_ms"],
         "SUMMARY_NOT_CALCULATED_FROM_SAMPLES")
    need(v.get("observation_sha256") == seal(v)["observation_sha256"],
         "HISTORIC_REPORT_SELF_HASH_DRIFT")
    return True


def build(env, pin, journal_hash, server, runner, samples):
    return seal({
        "schema": SCHEMA, "issue": ISSUE, "scope": SCOPE,
        "host": env["host"], "task_id": env["task_id"],
        "model": MODEL, "model_digest": DIGEST,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "server_birth": server, "runner_birth": runner,
        "worker_birth": pin["worker"], "aider_birth": pin["aider"],
        "pin_sha256": pin["pin_sha256"],
        "envelope_sha256": digest(env),
        "running_journal_raw_sha256": journal_hash,
        "sample_count": len(samples), "samples": samples,
        "peak_runner_rss_bytes": max(x["runner"]["rss_bytes"] for x in samples),
        "peak_server_rss_bytes": max(x["serve"]["rss_bytes"] for x in samples),
        "observed_runner_cpu_delta_ms": samples[-1]["runner"]["cpu_time_ms"] -
                                        samples[0]["runner"]["cpu_time_ms"],
        "observed_server_cpu_delta_ms": samples[-1]["serve"]["cpu_time_ms"] -
                                        samples[0]["serve"]["cpu_time_ms"],
        "original_pinned_worker_journal_validated": True,
        "read_only_api_sole_model_digest_at_samples": True,
        "os_native_birth_before_and_after_each_metric": True,
        "observer_never_starts_or_controls_any_process": True,
        "exclusive_model_client_use_proven": False,
        "actual_gpu_vram_measured": False,
        "all_model_processes_accounted": False,
        "cross_host_fencing_verified": False,
        "canonical_fleet_lease": False,
        "autonomous_retry_proven": False,
        "production_authority": False,
        "ollama_config_modified": False,
        "exact_model_call_count_known": False,
        "model_started_by_observer": False,
        "observer_model_calls": 0, "paid_api_spend_usd": 0,
    })


def observe(envelope, root):
    path = envelope_path(envelope)
    dest = root_path(root, new=True)
    env, _ = read_exact(path)
    kernel.checked_env(env, local=True)
    need(env["task_id"] == path.parent.name
         and env["host"] == "MacMiniOffice.local"
         and env.get("kernel_birth_capture") == "REQUIRE_OS_BIRTH_BEFORE_QA_V1"
         and env.get("executor", {}).get("model") == MODEL
         and env["executor"].get("model_digest") == DIGEST
         and env["executor"].get("ollama_port") == PORT
         and env.get("budget", {}).get("max_attempts") == 1
         and env["budget"].get("max_cost_usd") == 0,
         "UNAUTHORIZED_LAB_MODEL_TASK")
    output = path.parent / "output"
    running, pin_file = output / "receipt.json.running", output / "kernel-pin.json"
    need(not running.exists() and not pin_file.exists()
         and not (output / "receipt.json").exists(),
         "TASK_ALREADY_EXECUTED_OR_UNKNOWN_NO_RETRY")
    need(not ollama_ps(), "INITIAL_MODEL_ALREADY_LOADED_ATTRIBUTION_AMBIGUOUS")
    server, runners = local_ollama_processes()
    need(len(server) == 1 and not runners, "OLLAMA_SERVER_OR_RUNNERS_AMBIGUOUS")
    server_row = kernel.sample(server[0].pid)
    need(server_row and server_row["source"] == "PSUTIL_OS_CREATE_TIME",
         "OLLAMA_SERVER_OS_IDENTITY_UNAVAILABLE")
    dest.mkdir(exist_ok=False)
    write_once(dest / "ready.json", {
        "task_id": env["task_id"], "state": "PASSIVE_READY_NOT_A_WORKER",
        "server_birth": server_row, "model_calls": 0
    })
    started = time.monotonic()
    journal = pin = None
    journal_hash = None
    while time.monotonic() - started < TIMEOUT:
        if running.is_file() and pin_file.is_file():
            try:
                journal, journal_hash = read_exact(running)
                pin, _ = read_exact(pin_file)
                kernel.checked_pin(env, journal, pin)
                break
            except (kernel.Refused, ValueError, OSError):
                pass
        time.sleep(.06)
    need(pin is not None, "WORKER_KERNEL_PIN_NOT_OBSERVED")
    need(is_same(pin["worker"]) and is_same(pin["aider"]),
         "WORKER_AIDER_OS_IDENTITY_NOT_LIVE")
    runner_row = None
    while time.monotonic() - started < TIMEOUT:
        models = ollama_ps()
        _, runners = local_ollama_processes()
        accepted = [p for p in runners if p.ppid() == server_row["pid"]]
        need(len(accepted) <= 1, "MULTIPLE_RUNNERS_AMBIGUOUS")
        if len(models) == 1 and len(accepted) == 1:
            active_model(models[0])
            runner_row = kernel.sample(accepted[0].pid)
            break
        time.sleep(.12)
    need(runner_row and is_same(runner_row)
         and runner_row["ppid"] == server_row["pid"],
         "NATIVE_OLLAMA_RUNNER_NOT_PINNED")
    samples = []
    for idx in range(OBS_COUNT):
        need(is_same(pin["worker"]) and is_same(pin["aider"]),
             "ORIGINAL_WORKER_GONE_DURING_SAMPLING")
        models = ollama_ps()
        need(len(models) == 1, "MODEL_LOAD_CHURN_DURING_OBSERVATION")
        api = active_model(models[0])
        samples.append(collect(server_row, runner_row, started, idx + 1, api))
        if idx < OBS_COUNT - 1:
            time.sleep(.5)
    report = build(env, pin, journal_hash, server_row, runner_row, samples)
    validate(report)
    write_once(dest / "report.json", report)
    return {"status": "PASS_ONE_CORRELATED_OS_PINNED_OLLAMA_RUNNER",
            "task_id": env["task_id"], "host": env["host"],
            "samples": len(samples),
            "server_pid": server_row["pid"],
            "runner_pid": runner_row["pid"],
            "observed_peak_runner_rss_bytes": report["peak_runner_rss_bytes"],
            "observed_peak_server_rss_bytes": report["peak_server_rss_bytes"],
            "observed_runner_cpu_delta_ms": report["observed_runner_cpu_delta_ms"],
            "api_size_vram_bytes_first": samples[0]["api_size_vram_bytes"],
            "api_size_vram_is_gpu_measurement": False,
            "exclusive_model_client_use_proven": False,
            "observation_sha256": report["observation_sha256"],
            "model_calls_by_observer": 0,
            "production_authority": False}


def synthetic_fixture():
    ser = {"pid": 100, "ppid": 1, "pgid": 100,
           "birth_us": 1791573180000000, "source": "PSUTIL_OS_CREATE_TIME"}
    run = {"pid": 101, "ppid": 100, "pgid": 101,
           "birth_us": 1791573180010000, "source": "PSUTIL_OS_CREATE_TIME"}
    wk = {"pid": 102, "ppid": 1, "pgid": 102,
          "birth_us": 1791573180020000, "source": "PSUTIL_OS_CREATE_TIME"}
    aid = {"pid": 103, "ppid": 102, "pgid": 103,
           "birth_us": 1791573180030000, "source": "PSUTIL_OS_CREATE_TIME"}
    env = {"host": "MacMiniOffice.local",
           "task_id": "p0-ollama-observed-offline-fixture",
           "executor": {"model": MODEL}}
    pin = {"pin_sha256": "d"*64, "worker": wk, "aider": aid}
    samples = [{
        "index":i+1, "observed_at_utc":"2026-10-09T00:00:00+00:00",
        "monotonic_offset_ms":500*(i+1),
        "runner":{"pid":101,"birth_us":run["birth_us"],
                  "rss_bytes":3_900_000_000+i*16000,
                  "cpu_time_ms":10_000+i*100},
        "serve":{"pid":100,"birth_us":ser["birth_us"],
                 "rss_bytes":31_000_000+i*4000,
                 "cpu_time_ms":1_000+i*5},
        "api_model_size_bytes":3_400_000_000,
        "api_size_vram_bytes":3_200_000_000,
        "api_reported_only_not_gpu_measurement":True,
    } for i in range(OBS_COUNT)]
    return build(env, pin, "f"*64, ser, run, samples)


def selftest():
    good = synthetic_fixture()
    validate(good)
    tests = ["positive_offline_without_OS_API"]
    negatives = [
        ("fake_scope",lambda x:x.update(scope="PRODUCTION")),
        ("wrong_host",lambda x:x.update(host="Chris")),
        ("wrong_model",lambda x:x.update(model="qwen3.5:9b")),
        ("wrong_digest",lambda x:x.update(model_digest="0"*64)),
        ("bad_task",lambda x:x.update(task_id="customer")),
        ("missing_pin",lambda x:x.update(pin_sha256="")),
        ("wrong_ppid",lambda x:x["runner_birth"].update(ppid=555)),
        ("wrong_runner_pid",lambda x:x["samples"][2]["runner"].update(pid=555)),
        ("birth_drift",lambda x:x["samples"][4]["serve"].update(birth_us=1)),
        ("drop_sample",lambda x:x["samples"].pop()),
        ("fake_index",lambda x:x["samples"][0].update(index=99)),
        ("time_rewind",lambda x:x["samples"][5].update(monotonic_offset_ms=0)),
        ("cpu_rewind",lambda x:x["samples"][4]["runner"].update(cpu_time_ms=0)),
        ("fake_peak",lambda x:x.update(peak_runner_rss_bytes=1)),
        ("fake_cpu",lambda x:x.update(observed_server_cpu_delta_ms=10**9)),
        ("wrong_model_size",lambda x:x["samples"][0].update(api_model_size_bytes=-1)),
        ("fake_gpu",lambda x:x.update(actual_gpu_vram_measured=True)),
        ("fake_exclusive",lambda x:x.update(exclusive_model_client_use_proven=True)),
        ("fake_fulltree",lambda x:x.update(all_model_processes_accounted=True)),
        ("fake_fencing",lambda x:x.update(cross_host_fencing_verified=True)),
        ("fake_retry",lambda x:x.update(autonomous_retry_proven=True)),
        ("fake_paid",lambda x:x.update(paid_api_spend_usd=1)),
        ("fake_model_call",lambda x:x.update(observer_model_calls=1)),
    ]
    for label, edit in negatives:
        attempt=copy.deepcopy(good)
        edit(attempt)
        try:
            validate(seal(attempt))
        except kernel.Refused:
            tests.append(label+"_DENIED")
        else:
            raise AssertionError("RESEALED_UNSAFE_REPORT_ACCEPTED:"+label)
    corrupt = dict(good, observation_sha256="0"*64)
    try: validate(corrupt)
    except kernel.Refused: tests.append("raw_tamper_DENIED")
    else: raise AssertionError("UNSEALED_CHANGE_ACCEPTED")
    need(len(tests)==25,"SELFTEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(tests),
            "model_invocations":0,"operating_system_queries":0,
            "distributed_fencing_verified":False,
            "actual_gpu_vram_measured":False,
            "production_authority":False}


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    sub.add_parser("selftest")
    a=sub.add_parser("observe")
    a.add_argument("--envelope",required=True)
    a.add_argument("--root",required=True)
    v=sub.add_parser("verify")
    v.add_argument("--root",required=True)
    args=p.parse_args()
    if args.mode=="selftest":
        result=selftest()
    elif args.mode=="observe":
        result=observe(args.envelope,args.root)
    else:
        root=root_path(args.root,new=False)
        report,_=read_exact(root/"report.json")
        validate(report)
        result={"status":"PASS_OFFLINE_HISTORICAL_REPORT_NOT_LIVE_ATTESTATION",
                "task_id":report["task_id"],"samples":len(report["samples"]),
                "observation_sha256":report["observation_sha256"],
                "model_invocations":0,"production_authority":False}
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (kernel.Refused,OSError,ValueError,KeyError,TypeError,
            AssertionError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:150],
                          "model_invocations":0,
                          "automatic_retry":False,
                          "production_authority":False},sort_keys=True))
        raise SystemExit(2)
