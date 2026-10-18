#!/usr/bin/env python3
"""#604: Portable fail-closed analysis of sanitized Windows Host Compute events.

No VM launch, generated code, socket, Git writer or privileged action.
A host OS event stream is observational and host-controlled; even a perfect
VM/config/command match is NEVER a guest session, kernel or OS-isolation
attestation. The only runtime 'inspect' exit code is 2 (NOT ADMITTED).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

SCHEMA = "velvetos.office-v2.p0-604-wsb-host-compute-metadata.v0"
CHANNEL = "Microsoft-Windows-Hyper-V-Compute-Operational"
CONFIG_SHA = "781c82ac2f426196c847ba32e0da9170985c7877953f144ddc992623200411ff"
SCRIPT_SHA = "f216aa189f54900b4ba412508de69193d591a648611e1d862da1d067f22eb056"
GUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
EVENT_FIELDS = {
    "event_id", "record_id", "time_utc", "compute_id",
    "exact_public_logon_command_observed", "expected_2048mb_change_observed",
}
SNAPSHOT_FIELDS = {
    "schema", "status", "source_host", "event_channel", "config_sha256",
    "guest_script_sha256", "window_start_utc", "window_end_utc",
    "records_limit_reached", "original_public_output_count",
    "host_event_count", "events", "current_host_user",
    "attended_guest_launched_by_this_probe", "independent_event_attestation",
    "production_authority",
}


class Refused(Exception):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise Refused(reason)


def utc(s: object) -> datetime:
    require(isinstance(s, str), "NONSTRING_EVENT_TIME")
    try:
        value = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused("INVALID_EVENT_TIMESTAMP") from exc
    require(value.tzinfo is not None and value.utcoffset() == timedelta(0),
            "NON_UTC_OR_NAIVE_TIMESTAMP")
    return value.astimezone(timezone.utc)


def verdict(status: str, **extra: object) -> dict:
    return {
        "schema": "velvetos.office-v2.p0-604-wsb-event-identity-gate.v0",
        "status": status,
        "admission_allowed": False,
        "host_log_is_independent_cryptographic_attestation": False,
        "guest_session_proven": False,
        "sandbox_config_and_mounts_enforced_proven": False,
        "network_isolation_proven": False,
        "windows_session1_authorized_launch_witness_proven": False,
        "source_model_code_executed": False,
        "native_git_sink_credential_custody_proven": False,
        "external_effects": 0,
        "production_authority": False,
        **extra,
    }


def evaluate(s: dict) -> dict:
    require(type(s) is dict and set(s) == SNAPSHOT_FIELDS,
            "EXACT_METADATA_SCHEMA_FIELDS_REQUIRED")
    require(s["schema"] == SCHEMA and
            s["status"] == "UNTRUSTED_READ_ONLY_HOST_COMPUTE_METADATA" and
            s["event_channel"] == CHANNEL and
            s["source_host"] == "Chris" and
            s["config_sha256"] == CONFIG_SHA and
            s["guest_script_sha256"] == SCRIPT_SHA and
            isinstance(s["current_host_user"], str) and
            bool(s["current_host_user"]) and
            s["attended_guest_launched_by_this_probe"] is False and
            s["independent_event_attestation"] is False and
            s["production_authority"] is False,
            "PUBLIC_HOST_METADATA_SCOPE_INVALID")
    start, end = utc(s["window_start_utc"]), utc(s["window_end_utc"])
    require(timedelta(0) < end - start <= timedelta(hours=3),
            "UNBOUNDED_OR_REVERSED_EVENT_WINDOW")
    require(type(s["records_limit_reached"]) is bool and
            type(s["original_public_output_count"]) is int and
            0 <= s["original_public_output_count"] < 1000 and
            type(s["host_event_count"]) is int and
            type(s["events"]) is list and
            s["host_event_count"] == len(s["events"]) and
            len(s["events"]) <= 400,
            "EVENT_ARRAY_SIZE_OR_BOOLEAN_INVALID")

    normalized = []
    record_ids = set()
    for entry in s["events"]:
        require(type(entry) is dict and set(entry) == EVENT_FIELDS,
                "UNEXPECTED_EVENT_FIELDS_OR_MISSING_EVENT_FIELD")
        eid, rid = entry["event_id"], entry["record_id"]
        require(type(eid) is int and eid in (2014, 2500, 2007)
                and type(rid) is int and 0 < rid < 2**63
                and rid not in record_ids,
                "UNKNOWN_ID_OR_DUPLICATE_EVENT_RECORD")
        record_ids.add(rid)
        cid = entry["compute_id"]
        require(isinstance(cid, str) and GUID.fullmatch(cid) is not None,
                "INVALID_OR_NONCANONICAL_COMPUTE_UUID")
        command = entry["exact_public_logon_command_observed"]
        memory = entry["expected_2048mb_change_observed"]
        require(type(command) is bool and type(memory) is bool and
                (not command or eid == 2500) and
                (not memory or eid == 2007),
                "INCONSISTENT_SAFELY_REDACTED_EVENT_FIELDS")
        t = utc(entry["time_utc"])
        require(start <= t <= end, "EVENT_TIMESTAMP_OUTSIDE_CAPTURE_WINDOW")
        normalized.append((eid, rid, t, cid, command, memory))

    event_groups = len({r[3] for r in normalized})
    base = {
        "host_event_count": len(normalized),
        "observed_distinct_compute_ids": event_groups,
        "matching_public_logon_command_events": sum(bool(r[4]) for r in normalized),
        "complete_observational_matches": 0,
        "note": "No host-admin-controlled event stream alone grants guest admission",
    }
    if s["records_limit_reached"] or len(normalized) >= 400:
        return verdict("BLOCKED_TRUNCATED_HOST_EVENT_WINDOW", **base)
    if s["original_public_output_count"] != 0:
        return verdict("BLOCKED_PUBLIC_GUEST_OUTPUT_ORIGIN_UNVERIFIED", **base)
    if not normalized:
        return verdict("BLOCKED_NO_HOST_COMPUTE_EVENTS", **base)

    matches = set()
    command_seen = set()
    for proc in (r for r in normalized if r[0] == 2500 and r[4]):
        command_seen.add(proc[3])
        origins = [r for r in normalized if r[0] == 2014
                   and r[3] == proc[3] and r[1] < proc[1]
                   and timedelta(0) <= proc[2] - r[2] <= timedelta(minutes=20)]
        memories = [r for r in normalized if r[0] == 2007 and r[5]
                    and r[3] == proc[3] and r[1] < proc[1]
                    and timedelta(0) <= proc[2] - r[2] <= timedelta(minutes=20)]
        if any(origin[1] < memory[1] and origin[2] <= memory[2]
               for origin in origins for memory in memories):
            matches.add(proc[3])
    base["complete_observational_matches"] = len(matches)
    if len(matches) > 1:
        return verdict("BLOCKED_AMBIGUOUS_MULTIPLE_SANDBOX_LIKE_GUESTS", **base)
    if len(matches) == 1:
        return verdict("BLOCKED_CORRELATED_ETW_METADATA_IS_NOT_GUEST_ATTESTATION", **base)
    if command_seen:
        return verdict("BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION",
                       **base)
    return verdict("BLOCKED_ONLY_UNRELATED_VM_COMPUTE_EVENTS", **base)


def offline_tests() -> dict:
    start = datetime(2026, 10, 11, 7, 0, tzinfo=timezone.utc)
    def timestamp(minutes: int) -> str:
        return (start + timedelta(minutes=minutes)).isoformat()

    def event(eid: int, rid: int, minute: int, cid: str,
              command: bool = False, mem: bool = False) -> dict:
        return {
            "event_id": eid, "record_id": rid, "time_utc": timestamp(minute),
            "compute_id": cid,
            "exact_public_logon_command_observed": command,
            "expected_2048mb_change_observed": mem,
        }

    a, b = "a" * 8 + "-aaaa-aaaa-aaaa-" + "a" * 12, "b" * 8 + "-bbbb-bbbb-bbbb-" + "b" * 12
    c = "c" * 8 + "-cccc-cccc-cccc-" + "c" * 12
    unrelated = [event(2014, 101, 1, a), event(2007, 102, 2, a),
                 event(2500, 103, 3, a),
                 event(2014, 201, 10, b), event(2007, 202, 11, b),
                 event(2500, 203, 12, b)]
    full_a = [event(2014, 301, 21, a), event(2007, 302, 22, a, mem=True),
              event(2500, 303, 23, a, command=True)]
    full_b = [event(2014, 401, 25, b), event(2007, 402, 26, b, mem=True),
              event(2500, 403, 27, b, command=True)]
    base = {
        "schema": SCHEMA, "status": "UNTRUSTED_READ_ONLY_HOST_COMPUTE_METADATA",
        "source_host": "Chris", "event_channel": CHANNEL,
        "config_sha256": CONFIG_SHA, "guest_script_sha256": SCRIPT_SHA,
        "window_start_utc": timestamp(0), "window_end_utc": timestamp(90),
        "records_limit_reached": False, "original_public_output_count": 0,
        "host_event_count": len(unrelated), "events": unrelated,
        "current_host_user": "NT AUTHORITY\\SYSTEM",
        "attended_guest_launched_by_this_probe": False,
        "independent_event_attestation": False, "production_authority": False,
    }
    def with_events(items: list, **overrides: object) -> dict:
        return dict(base, events=items, host_event_count=len(items), **overrides)

    count = 0
    def expect_status(snapshot: dict, status: str) -> None:
        nonlocal count
        r = evaluate(snapshot)
        require(r["status"] == status and r["admission_allowed"] is False
                and r["guest_session_proven"] is False
                and r["production_authority"] is False
                and r["external_effects"] == 0,
                "FAKE_OS_WITNESS_FALSE_ADMISSION")
        count += 1

    def expect_refusal(snapshot: dict) -> None:
        nonlocal count
        try:
            evaluate(snapshot)
        except Refused:
            count += 1
        else:
            raise Refused("INVALID_OS_EVENT_STREAM_FALSE_ADMISSION")

    expect_status(base, "BLOCKED_ONLY_UNRELATED_VM_COMPUTE_EVENTS")
    expect_status(with_events([]), "BLOCKED_NO_HOST_COMPUTE_EVENTS")
    expect_status(with_events(unrelated, records_limit_reached=True),
                  "BLOCKED_TRUNCATED_HOST_EVENT_WINDOW")
    expect_status(with_events(unrelated, original_public_output_count=1),
                  "BLOCKED_PUBLIC_GUEST_OUTPUT_ORIGIN_UNVERIFIED")
    expect_status(with_events([full_a[2]]),
                  "BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION")
    expect_status(with_events([full_a[0], full_a[2]]),
                  "BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION")
    expect_status(with_events(full_a),
                  "BLOCKED_CORRELATED_ETW_METADATA_IS_NOT_GUEST_ATTESTATION")
    expect_status(with_events(full_a + full_b),
                  "BLOCKED_AMBIGUOUS_MULTIPLE_SANDBOX_LIKE_GUESTS")
    expect_status(with_events([full_a[0], full_b[1], full_a[2]]),
                  "BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION")
    expect_status(with_events([full_a[0], full_a[1],
                               event(2500, 309, 50, a, command=True)]),
                  "BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION")
    expect_status(with_events([full_a[0], full_a[1],
                               event(2500, 300, 23, a, command=True)]),
                  "BLOCKED_PUBLIC_COMMAND_WITHOUT_SINGLE_FULL_OS_CORRELATION")
    expect_status(with_events([event(2007, 901, 18, c, mem=True)]),
                  "BLOCKED_ONLY_UNRELATED_VM_COMPUTE_EVENTS")

    expect_refusal(dict(base, event_channel="Application"))
    expect_refusal(dict(base, config_sha256="0" * 64))
    expect_refusal(dict(base, guest_script_sha256="0" * 64))
    expect_refusal(dict(base, independent_event_attestation=True))
    expect_refusal(dict(base, attended_guest_launched_by_this_probe=True))
    expect_refusal(dict(base, production_authority=True))
    expect_refusal(dict(base, records_limit_reached="false"))
    expect_refusal(dict(base, host_event_count=1000))
    expect_refusal(dict(base, claimed_guest_attestation=True))
    expect_refusal(with_events([dict(full_a[2], guest_attested=True)]))
    expect_refusal(with_events([dict(full_a[0],
                                    exact_public_logon_command_observed=True)]))
    expect_refusal(with_events([dict(full_a[2],
                                    expected_2048mb_change_observed=True)]))
    expect_refusal(with_events([dict(full_a[2], compute_id="VM_X")]))
    expect_refusal(with_events([full_a[0], dict(full_a[1], record_id=301)]))
    expect_refusal(with_events([dict(full_a[2], event_id=3999)]))
    expect_refusal(with_events([dict(full_a[0], record_id=0)]))
    expect_refusal(with_events([dict(full_a[0], time_utc=timestamp(110))]))
    expect_refusal(with_events([dict(full_a[0], time_utc="2026-10-11 07:01")]))
    require(count == 30, "OFFLINE_30_TEST_COUNT_DRIFT")
    return verdict(
        "PASS_30_OFFLINE_CROSS_GUEST_IDENTITY_NEGATIVES_NOT_VM_ATTESTATION",
        tests=count, actual_vm_launched=False,
        independent_user_session_witness_available=False,
        model_calls=0, credential_accesses=0,
    )


def inspect(path: Path) -> dict:
    require(path.is_absolute() and not path.is_symlink()
            and path.name.endswith(".json") and
            path.parent.name.startswith("p0-604-wsb-") and
            path.parent.parent.name == "AgentEnvelopeLab" and
            path.is_file() and path.stat().st_size <= 180000,
            "EXPLICIT_PUBLIC_AGENTENVELOPELAB_SNAPSHOT_REQUIRED")
    return evaluate(json.loads(path.read_text(encoding="utf-8-sig")))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("selftest", "inspect"))
    p.add_argument("--snapshot")
    args = p.parse_args()
    require(args.mode == "selftest" or bool(args.snapshot),
            "SNAPSHOT_PATH_REQUIRED")
    outcome = offline_tests() if args.mode == "selftest" else inspect(Path(args.snapshot))
    print(json.dumps(outcome, sort_keys=True))
    return 0 if args.mode == "selftest" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refused, OSError, ValueError, UnicodeError) as exc:
        print(json.dumps(verdict("FAIL_CLOSED_INVALID_OR_UNTRUSTED_OS_EVENT_STREAM",
                                 reason=str(exc)[:160]), sort_keys=True))
        raise SystemExit(2)
