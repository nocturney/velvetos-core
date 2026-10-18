#!/usr/bin/env python3
"""Offline, fail-closed CrewAI E5 network snapshot validator and hashed receipt.

This is a sampled observation only, NOT OS network enforcement or an E5 GO.
Stdlib only. Never opens a socket or launches the pilot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = "velvetos.office-v2.crewai-e5-snapshots.v1"
RECEIPT_SCHEMA = "velvetos.office-v2.crewai-e5-receipt.v1"
ALLOWED_ADDRESS = "127.0.0.1"
ALLOWED_PORT = 11435
MAX_SNAPSHOTS = 6000


def utc_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timedelta(0) else None


def evaluate(data: object) -> list[str]:
    reasons: set[str] = set()

    def bad(reason: str) -> None:
        reasons.add(reason)

    if not isinstance(data, dict):
        return ["INVALID_EVIDENCE"]
    if data.get("schema") != SCHEMA or data.get("host") != "Chris":
        bad("INVALID_IDENTITY_OR_SCHEMA")
    root_pid = data.get("root_pid")
    if type(root_pid) is not int or root_pid <= 0:
        bad("INVALID_ROOT_PID")
    if data.get("collector_complete") is not True or data.get("collector_errors") != []:
        bad("COLLECTOR_INCOMPLETE")
    if data.get("timed_out") is not False:
        bad("TIMEOUT_OR_UNKNOWN")
    if type(data.get("exit_code")) is not int or data.get("exit_code") != 0:
        bad("PILOT_EXIT_NOT_ZERO")
    interval = data.get("sample_interval_ms")
    if type(interval) is not int or not 100 <= interval <= 1000:
        bad("INVALID_SAMPLE_INTERVAL")
    started = utc_time(data.get("started_at_utc"))
    ended = utc_time(data.get("ended_at_utc"))
    if started is None or ended is None or ended < started:
        bad("INVALID_RUN_TIMES")

    phases = data.get("snapshots")
    if not isinstance(phases, dict) or set(phases) != {"before", "during", "after"}:
        return sorted(reasons | {"MISSING_SNAPSHOT"})
    before, during, after = phases["before"], phases["during"], phases["after"]
    if not isinstance(during, list) or not 1 <= len(during) <= MAX_SNAPSHOTS:
        bad("MISSING_DURING_SNAPSHOT")
        during = []
    seen_root = False
    last_time = None
    birth_by_pid: dict[int, str] = {}
    all_snaps = [("before", before)] + [("during", snap) for snap in during] + [("after", after)]
    for phase, snap in all_snaps:
        if not isinstance(snap, dict):
            bad("INVALID_SNAPSHOT")
            continue
        stamp = utc_time(snap.get("captured_at_utc"))
        if stamp is None:
            bad("INVALID_SNAPSHOT_TIME")
        else:
            if last_time is not None and stamp < last_time:
                bad("OUT_OF_ORDER_SNAPSHOT")
            last_time = stamp
            if started is not None and ended is not None:
                if phase == "before" and stamp > started:
                    bad("BEFORE_NOT_BEFORE_RUN")
                if phase == "during" and not started <= stamp <= ended:
                    bad("DURING_OUTSIDE_RUN")
                if phase == "after" and stamp < ended:
                    bad("AFTER_NOT_AFTER_RUN")
        tree = snap.get("process_tree")
        tcp = snap.get("tcp")
        udp = snap.get("udp")
        if not isinstance(tree, list) or not isinstance(tcp, list) or not isinstance(udp, list):
            bad("INVALID_SNAPSHOT_SHAPE")
            continue
        pids: set[int] = set()
        for member in tree:
            if not isinstance(member, dict):
                bad("INVALID_TREE_MEMBER")
                continue
            pid, ppid = member.get("pid"), member.get("parent_pid")
            birth = member.get("created_at_utc")
            if (type(pid) is not int or pid <= 0 or type(ppid) is not int
                    or ppid < 0 or utc_time(birth) is None or pid in pids):
                bad("INVALID_TREE_MEMBER")
                continue
            pids.add(pid)
            if pid in birth_by_pid and birth_by_pid[pid] != birth:
                bad("PID_REUSED_OR_IDENTITY_CHANGED")
            birth_by_pid[pid] = birth
        if phase == "during" and type(root_pid) is int and root_pid in pids:
            seen_root = True
        if phase == "before" and (tree or tcp or udp):
            bad("PILOT_TREE_PRESENT_BEFORE_LAUNCH")
        if phase == "after" and tree:
            bad("PILOT_TREE_STILL_RUNNING")
        for item in tcp:
            if not isinstance(item, dict):
                bad("INVALID_TCP_ROW")
                continue
            owner = item.get("pid")
            port = item.get("remote_port")
            if type(owner) is not int or owner not in pids:
                bad("TCP_OWNER_NOT_IN_TREE")
            if str(item.get("state", "")).lower() == "listen":
                bad("TCP_LISTENER_DETECTED")
            if not isinstance(item.get("state"), str) or not item["state"]:
                bad("TCP_STATE_MISSING")
            if item.get("remote_address") != ALLOWED_ADDRESS:
                bad("UNAPPROVED_REMOTE_ENDPOINT")
            if type(port) is not int or port != ALLOWED_PORT:
                bad("WRONG_OLLAMA_PORT")
            if not isinstance(item.get("local_address"), str) or type(item.get("local_port")) is not int:
                bad("INVALID_TCP_ROW")
        for item in udp:
            bad("UDP_ENDPOINT_DETECTED")  # Bound UDP socket is a potential listener.
            if not isinstance(item, dict) or type(item.get("pid")) is not int or item["pid"] not in pids:
                bad("UDP_OWNER_NOT_IN_TREE")
    if not seen_root:
        bad("ROOT_NOT_OBSERVED_DURING")
    return sorted(reasons)


def canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def create_receipt(source: bytes, data: object, parse_error: str | None = None) -> dict:
    reasons = ["INVALID_JSON"] if parse_error else evaluate(data)
    raw = data if isinstance(data, dict) else {}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "source_evidence_sha256": hashlib.sha256(source).hexdigest(),
        "source_evidence_bytes": len(source),
        "host": raw.get("host"),
        "root_pid": raw.get("root_pid"),
        "started_at_utc": raw.get("started_at_utc"),
        "ended_at_utc": raw.get("ended_at_utc"),
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS_SAMPLED_NOT_ENFORCEMENT" if not reasons else "FAIL",
        "reason_codes": reasons,
        "network_enforcement_proven": False,
        "pilot_authorized": False,
    }
    receipt["sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        source = args.evidence.read_bytes()
        if len(source) > 64 * 1024 * 1024:
            raise ValueError("evidence exceeds 64 MiB")
        data = json.loads(source)
        error = None
    except (OSError, ValueError, UnicodeError) as exc:
        source = source if "source" in locals() else b""
        data, error = None, type(exc).__name__
    receipt = create_receipt(source, data, error)
    try:
        args.receipt.write_bytes(json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=True).encode("ascii") + b"\n")
    except OSError as exc:
        print("FAIL E5 receipt write: %s" % exc, file=sys.stderr)
        return 2
    print("%s E5 %s" % ("PASS" if receipt["status"].startswith("PASS") else "FAIL", ",".join(receipt["reason_codes"]) or "sampled only"))
    return 0 if receipt["status"] == "PASS_SAMPLED_NOT_ENFORCEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
