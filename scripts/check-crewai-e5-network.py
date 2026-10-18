#!/usr/bin/env python3
"""Offline adversarial fixtures for the CrewAI E5 network-evidence validator."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from office_v2_crewai.contract import SANDBOX_ROOT  # noqa: E402
from vf_office_v2_crewai_e5_network import (  # noqa: E402
    PILOT_STAGE_ROOT, SCHEMA, canonical_bytes, create_receipt, evaluate,
    normalize_pilot_path, pilot_path_admitted,
)


def fixture() -> dict:
    def snap(ts: str, running: bool) -> dict:
        return {
            "captured_at_utc": ts,
            "process_tree": ([{"pid": 4242, "parent_pid": 100,
                              "created_at_utc": "2026-10-18T12:00:01Z"}] if running else []),
            "tcp": ([{"pid": 4242, "state": "Established", "local_address": "127.0.0.1",
                      "local_port": 50123, "remote_address": "127.0.0.1", "remote_port": 11435}]
                    if running else []),
            "udp": [],
        }
    return {
        "schema": SCHEMA,
        "host": "Chris",
        "root_pid": 4242,
        "sample_interval_ms": 250,
        "started_at_utc": "2026-10-18T12:00:01Z",
        "ended_at_utc": "2026-10-18T12:00:03Z",
        "collector_complete": True,
        "collector_errors": [],
        "timed_out": False,
        "exit_code": 0,
        "snapshots": {
            "before": snap("2026-10-18T12:00:00Z", False),
            "during": [snap("2026-10-18T12:00:02Z", True)],
            "after": snap("2026-10-18T12:00:04Z", False),
        },
    }


def append_child(data: dict, pid: int, parent_pid: int) -> None:
    data["snapshots"]["during"][0]["process_tree"].append({
        "pid": pid, "parent_pid": parent_pid,
        "created_at_utc": "2026-10-18T12:00:01Z",
    })


def mutate_pid_reuse(data: dict) -> None:
    another = copy.deepcopy(data["snapshots"]["during"][0])
    another["captured_at_utc"] = "2026-10-18T12:00:02.500000Z"
    another["process_tree"][0]["created_at_utc"] = "2026-10-18T12:00:01.050000Z"
    data["snapshots"]["during"].append(another)


def main() -> int:
    base = fixture()
    errors = []
    if evaluate(base):
        errors.append("valid baseline refused: %s" % evaluate(base))
    nested = copy.deepcopy(base)
    append_child(nested, 4243, 4242)
    append_child(nested, 4244, 4243)
    if evaluate(nested):
        errors.append("valid three-generation process tree refused: %s" % evaluate(nested))
    cases = {
        "tcp-listening": (lambda d: d["snapshots"]["during"][0]["tcp"][0].update(state="Listen"),
                          "TCP_LISTENER_DETECTED"),
        "non-loopback-remote": (lambda d: d["snapshots"]["during"][0]["tcp"][0].update(remote_address="10.0.0.10"),
                                "UNAPPROVED_REMOTE_ENDPOINT"),
        "wrong-ollama-port": (lambda d: d["snapshots"]["during"][0]["tcp"][0].update(remote_port=11434),
                              "WRONG_OLLAMA_PORT"),
        "missing-after": (lambda d: d["snapshots"].pop("after"), "MISSING_SNAPSHOT"),
        "missing-before": (lambda d: d["snapshots"].pop("before"), "MISSING_SNAPSHOT"),
        "missing-during": (lambda d: d["snapshots"].update(during=[]), "MISSING_DURING_SNAPSHOT"),
        "udp-bound-listener": (lambda d: d["snapshots"]["during"][0]["udp"].append({"pid": 4242, "local_port": 5353}),
                               "UDP_ENDPOINT_DETECTED"),
        "missing-collector": (lambda d: d.update(collector_complete=False), "COLLECTOR_INCOMPLETE"),
        "collector-error": (lambda d: d.update(collector_errors=["ACCESS_DENIED"]), "COLLECTOR_INCOMPLETE"),
        "orphan-child": (lambda d: d["snapshots"]["after"]["process_tree"].append({"pid": 4243, "parent_pid": 4242,
                                                "created_at_utc": "2026-10-18T12:00:02Z"}), "PILOT_TREE_STILL_RUNNING"),
        "root-not-seen": (lambda d: d["snapshots"]["during"][0].update(process_tree=[]), "ROOT_NOT_OBSERVED_DURING"),
        "bad-utc": (lambda d: d.update(started_at_utc="2026-10-18T15:00:01+03:00"), "INVALID_RUN_TIMES"),
        "nonzero-exit": (lambda d: d.update(exit_code=2), "PILOT_EXIT_NOT_ZERO"),
        "null-exit-code": (lambda d: d.update(exit_code=None), "PILOT_EXIT_NOT_ZERO"),
        "missing-exit-code": (lambda d: d.pop("exit_code"), "PILOT_EXIT_NOT_ZERO"),
        "non-scalar-root-pid": (lambda d: d.update(root_pid=[4242]), "INVALID_ROOT_PID"),
        "root-pid-object": (lambda d: d.update(root_pid={"pid": 4242}), "INVALID_ROOT_PID"),
        "root-pid-bool": (lambda d: d.update(root_pid=True), "INVALID_ROOT_PID"),
        "orphan-tree-member": (lambda d: append_child(d, 4243, 9999), "INVALID_TREE_ANCESTRY"),
        "foreign-parent": (lambda d: append_child(d, 4243, 100), "INVALID_TREE_ANCESTRY"),
        "self-parent-cycle": (lambda d: append_child(d, 4243, 4243), "INVALID_TREE_ANCESTRY"),
        "two-node-cycle": (lambda d: (append_child(d, 4243, 4244), append_child(d, 4244, 4243)),
                           "INVALID_TREE_ANCESTRY"),
        "false-interval": (lambda d: d.update(sample_interval_ms=5000), "INVALID_SAMPLE_INTERVAL"),
        "pid-reuse-across-snapshots": (mutate_pid_reuse, "PID_REUSED_OR_IDENTITY_CHANGED"),
        "foreign-connection-owner": (
            lambda d: d["snapshots"]["during"][0]["tcp"][0].update(pid=8999),
            "TCP_OWNER_NOT_IN_TREE"),
        "missing-tree": (
            lambda d: d["snapshots"]["during"][0].pop("process_tree"), "INVALID_SNAPSHOT_SHAPE"),
        "non-numeric-ppid": (
            lambda d: d["snapshots"]["during"][0]["process_tree"][0].update(parent_pid="100"),
            "INVALID_TREE_MEMBER"),
        "missing-root-with-child": (
            lambda d: d["snapshots"]["during"][0]["process_tree"][0].update(pid=4243),
            "INVALID_TREE_ANCESTRY"),
    }
    for name, (mutate, expected) in cases.items():
        trial = copy.deepcopy(base)
        mutate(trial)
        reasons = evaluate(trial)
        if expected not in reasons:
            errors.append("%s was not fail-closed (%s)" % (name, reasons))
        receipt = create_receipt(json.dumps(trial).encode("ascii"), trial)
        if receipt["status"] != "FAIL" or receipt["pilot_authorized"] is not False:
            errors.append("%s emitted positive receipt" % name)

    good = create_receipt(json.dumps(base).encode("ascii"), base)
    if (good["status"] != "PASS_SAMPLED_NOT_ENFORCEMENT" or good["network_enforcement_proven"]
            or good["pilot_authorized"]):
        errors.append("sampled observation misrepresented enforcement or GO")
    saved_hash = good.pop("sha256")
    if hashlib.sha256(canonical_bytes(good)).hexdigest() != saved_hash:
        errors.append("receipt self-hash mismatch")

    with tempfile.TemporaryDirectory() as tmp:
        src, dest = Path(tmp) / "snapshots.json", Path(tmp) / "receipt.json"
        src.write_bytes(json.dumps(base).encode("ascii"))
        validator = ROOT / "scripts" / "vf_office_v2_crewai_e5_network.py"
        ok = subprocess.run([sys.executable, str(validator), "--evidence", str(src), "--receipt", str(dest)],
                            text=True, capture_output=True, timeout=10)
        if ok.returncode != 0 or json.loads(dest.read_text())["status"] != "PASS_SAMPLED_NOT_ENFORCEMENT":
            errors.append("CLI positive fixture failed")
        bad = copy.deepcopy(base)
        bad["snapshots"].pop("after")
        src.write_bytes(json.dumps(bad).encode("ascii"))
        denied = subprocess.run([sys.executable, str(validator), "--evidence", str(src), "--receipt", str(dest)],
                                text=True, capture_output=True, timeout=10)
        if denied.returncode == 0 or json.loads(dest.read_text())["status"] != "FAIL":
            errors.append("CLI missing snapshot did not fail")
        bad_root = copy.deepcopy(base)
        bad_root["root_pid"] = [4242]
        src.write_bytes(json.dumps(bad_root).encode("ascii"))
        invalid_root = subprocess.run([sys.executable, str(validator), "--evidence", str(src), "--receipt", str(dest)],
                                      text=True, capture_output=True, timeout=10)
        invalid_receipt = json.loads(dest.read_text())
        if (invalid_root.returncode == 0 or "INVALID_ROOT_PID" not in invalid_receipt["reason_codes"]
                or "Traceback" in invalid_root.stderr):
            errors.append("CLI non-scalar root_pid failed to issue a clean FAIL receipt")
        bad_tree = copy.deepcopy(base)
        append_child(bad_tree, 4243, 9999)
        src.write_bytes(json.dumps(bad_tree).encode("ascii"))
        invalid_tree = subprocess.run([sys.executable, str(validator), "--evidence", str(src), "--receipt", str(dest)],
                                      text=True, capture_output=True, timeout=10)
        tree_receipt = json.loads(dest.read_text())
        if (invalid_tree.returncode != 1 or tree_receipt["status"] != "FAIL"
                or "INVALID_TREE_ANCESTRY" not in tree_receipt["reason_codes"]
                or "Traceback" in invalid_tree.stderr):
            errors.append("CLI orphan process-tree failed to emit fail-closed receipt")
        src.write_text("{broken", encoding="ascii")
        malformed = subprocess.run([sys.executable, str(validator), "--evidence", str(src), "--receipt", str(dest)],
                                   text=True, capture_output=True, timeout=10)
        if malformed.returncode == 0 or "INVALID_JSON" not in json.loads(dest.read_text())["reason_codes"]:
            errors.append("CLI malformed input did not fail")

    ps = ROOT / "scripts" / "collect-crewai-e5-network.ps1"
    if not ps.is_file():
        errors.append("PowerShell collector missing")
    else:
        raw = ps.read_bytes()
        required = (b"Get-NetTCPConnection", b"Get-NetUDPEndpoint", b"Get-CimInstance",
                    b"Start-Process", b"captured_at_utc", b"collector_errors", b"127.0.0.1",
                    b"11435", b"--evidence", b"--receipt")
        if (raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or any(b > 127 for b in raw)
                or not raw.endswith(b"\n")):
            errors.append("collector must be ASCII/LF without BOM")
        if any(needle not in raw for needle in required):
            errors.append("collector missing critical snapshot / enforcement marker")
        ancestry = (b"ParentProcessId", b"CreationDate", b"-gt 0.01",
                    b"PROCESS_TREE_TOO_LARGE", b"PROCESS_TREE_CYCLE",
                    b"PROCESS_TREE_ORPHAN", b"CHILD_CREATED_BEFORE_PARENT",
                    b"PROCESS_IDENTITY_CHANGED_DURING_SAMPLE", b"$afterById")
        if any(needle not in raw for needle in ancestry):
            errors.append("collector must verify CIM parent chains and PID births around network sampling")
        if (b"$null = $script:Child.Handle" not in raw or b"$null -ne $observedExitCode" not in raw
                or b"[int]$script:Child.ExitCode" in raw):
            errors.append("collector ExitCode must fail closed on null, with primed process handle")
        if (b"Test-PilotPathAdmitted" not in raw or b"TrimEnd('\\')" not in raw
                or b"$full.StartsWith($Root" in raw):
            errors.append("collector must admit the exact pilot root and still reject a sibling prefix")
    root = PILOT_STAGE_ROOT
    admitted = (
        root,
        root + "\\",
        root + "\\crew",
        root + "\\crew\\..",
        "d:/velvet/pilots/officev2-verifiedtrio",
    )
    rejected = (
        root + "X",
        root + "X\\crew",
        root + "\\..",
        root + "\\..\\OfficeV2-VerifiedTrioX",
        "D:\\Velvet\\Pilots",
        "C:\\Velvet\\Pilots\\OfficeV2-VerifiedTrio",
        "OfficeV2-VerifiedTrio",
        "",
    )
    if any(not pilot_path_admitted(path) for path in admitted):
        errors.append("exact pilot root or a child directory was rejected")
    if any(pilot_path_admitted(path) for path in rejected):
        errors.append("dotdot or sibling prefix was admitted: %s" % [
            path for path in rejected if pilot_path_admitted(path)
        ])
    if normalize_pilot_path(root + "\\..\\OfficeV2-VerifiedTrioX") != "D:\\Velvet\\Pilots\\OfficeV2-VerifiedTrioX":
        errors.append("dotdot sibling was not normalized outside the pilot root")
    if SANDBOX_ROOT != "D:\\Velvet\\Pilots\\crewai-e4\\sandbox-home" or pilot_path_admitted(SANDBOX_ROOT):
        errors.append("E4 sandbox root moved under the E5 stage")
    validator_source = (ROOT / "scripts" / "vf_office_v2_crewai_e5_network.py").read_text(encoding="utf-8")
    if 'data.get("exit_code") != 0' not in validator_source or "PILOT_EXIT_NOT_ZERO" not in validator_source:
        errors.append("E5 exit_code==0 contract was weakened")
    if errors:
        for error in errors:
            print("FAIL check-crewai-e5-network: %s" % error, file=sys.stderr)
        return 1
    print("OK crewai E5 offline fixture baseline+%d fail-closed mutants, CLI/hash/ASCII checks; no model/network" % len(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
