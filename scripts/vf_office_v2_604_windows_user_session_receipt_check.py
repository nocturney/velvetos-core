#!/usr/bin/env python3
"""#604 one-shot Windows LAB receipt validator, NEVER real worker authority.

Reads a single bounded JSON receipt and checks its declared user-context,
zero-effect contract. A passing result is NOT Windows token attestation,
Core lease, source signature, model permission or authorization to execute.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import tempfile

SCHEMA = "velvetos.office2.604.windows-user-context-one-shot-lab.v1"
ATTEMPT = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_RECEIPT_BYTES = 16384
FIELDS = {
    "schema", "status", "attempt_id", "host", "principal", "session_id",
    "is_system", "elevated", "process_id", "source_sha256", "observed_utc",
    "gui_action_executed", "model_called", "model_generated_code_executed",
    "git_or_provider_write", "core_lease_issued", "isolated_code_executor_proven",
    "receipt_authenticated_to_core",
}
FALSE_FIELDS = {
    "is_system", "elevated", "gui_action_executed", "model_called",
    "model_generated_code_executed", "git_or_provider_write",
    "core_lease_issued", "isolated_code_executor_proven",
    "receipt_authenticated_to_core",
}


class Refused(Exception):
    pass


def verify(value: object, *, expected_sha256: str, expected_attempt: str) -> dict:
    if type(value) is not dict or set(value) != FIELDS:
        raise Refused("FIELDS_NOT_EXACT")
    if value["schema"] != SCHEMA or value["status"] != "PASS_USER_CONTEXT_ONLY":
        raise Refused("SCHEMA_OR_STATE")
    if (type(expected_sha256) is not str or
            not HEX64.fullmatch(expected_sha256.lower()) or
            type(value["source_sha256"]) is not str or
            value["source_sha256"].lower() != expected_sha256.lower()):
        raise Refused("SOURCE_CONTENT_MISMATCH")
    if (type(expected_attempt) is not str or
            not ATTEMPT.fullmatch(expected_attempt) or
            type(value["attempt_id"]) is not str or
            value["attempt_id"] != expected_attempt):
        raise Refused("ATTEMPT_NOT_BOUND")
    if (type(value["host"]) is not str or value["host"].upper() != "CHRIS" or
            type(value["principal"]) is not str or
            value["principal"].upper() != "CHRIS\\CHRIS"):
        raise Refused("HOST_OR_USER_DRIFT")
    if (type(value["session_id"]) is not int or value["session_id"] != 1 or
            type(value["process_id"]) is not int or value["process_id"] <= 0):
        raise Refused("SESSION_OR_PID_INVALID")
    if any(type(value[name]) is not bool or value[name] is not False
           for name in FALSE_FIELDS):
        raise Refused("EXTERNAL_EFFECT_OR_PRIVILEGE_CLAIM")
    if type(value["observed_utc"]) is not str:
        raise Refused("TIME_UNTYPED")
    try:
        observed = datetime.fromisoformat(value["observed_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused("TIME_MALFORMED") from exc
    if observed.tzinfo is None:
        raise Refused("TIME_WITHOUT_ZONE")
    return {
        "status": "PASS_STRUCTURE_ONLY_NOT_AUTHORITY",
        "claimed_host": "CHRIS",
        "claimed_principal": "CHRIS\\Chris",
        "claimed_session": 1,
        "claimed_observed_utc": observed.astimezone(timezone.utc).isoformat(),
        "core_signed_lease": False,
        "authenticated_worker_principal": False,
        "external_effect_granted": False,
        "new_scheduler_created": False,
    }


def read_receipt(path: Path) -> tuple[dict, str]:
    if path.is_symlink():
        raise Refused("SYMLINK_DENIED")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_RECEIPT_BYTES:
        raise Refused("NOT_BOUNDED_REGULAR_FILE")
    raw = path.read_bytes()
    after = path.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
        raise Refused("FILE_CHANGED_DURING_READ")
    if len(raw) > MAX_RECEIPT_BYTES:
        raise Refused("FILE_TOO_LARGE")
    try:
        item = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Refused("INVALID_JSON") from exc
    return item, hashlib.sha256(raw).hexdigest()


def selftest() -> dict:
    import copy
    model = {
        "schema": SCHEMA, "status": "PASS_USER_CONTEXT_ONLY",
        "attempt_id": "a" * 32, "host": "CHRIS", "principal": "CHRIS\\Chris",
        "session_id": 1, "process_id": 501, "source_sha256": "b" * 64,
        "observed_utc": "2026-10-14T15:20:00Z",
        **{field: False for field in FALSE_FIELDS},
    }
    assert set(model) == FIELDS, "test fixture keys drift"
    checks = []
    def case(name, field, bad):
        changed = copy.deepcopy(model)
        if field is None:
            changed.pop("schema")
        else:
            changed[field] = bad
        try:
            verify(changed, expected_sha256="b" * 64, expected_attempt="a" * 32)
            denied = False
        except Refused:
            denied = True
        checks.append((name, denied))
    for field, bad in (
        ("status", "WRITE_AUTHORIZED"), ("attempt_id", "c" * 32),
        ("host", "CHRIS-3DPC"), ("principal", "NT AUTHORITY\\SYSTEM"),
        ("session_id", 0), ("session_id", True),
        ("process_id", False), ("source_sha256", "c" * 64),
        ("observed_utc", "yesterday"), ("observed_utc", "2026-10-14T15:20:00"),
        ("is_system", True), ("elevated", True),
        ("gui_action_executed", True), ("model_called", True),
        ("model_generated_code_executed", True), ("git_or_provider_write", True),
        ("core_lease_issued", True), ("isolated_code_executor_proven", True),
        ("receipt_authenticated_to_core", True),
    ):
        case(field + "-" + str(bad)[:9], field, bad)
    case("required-field-missing", None, None)
    with tempfile.TemporaryDirectory(prefix="vf604-receipt-") as tmp:
        original = Path(tmp) / "receipt.json"
        original.write_text(json.dumps(model), encoding="utf-8")
        parsed, _ = read_receipt(original)
        assert verify(parsed, expected_sha256="b" * 64, expected_attempt="a" * 32)
        symlink = Path(tmp) / "symlink.json"
        symlink.symlink_to(original)
        try:
            read_receipt(symlink)
            denied = False
        except Refused:
            denied = True
        checks.append(("symlink-denied", denied))
    result = {
        "schema": "velvetos.office2.604.windows-user-context-one-shot-tests.v1",
        "status": "PASS" if all(ok for _, ok in checks) else "FAIL",
        "denials_checked": len(checks),
        "denials_passed": sum(ok for _, ok in checks),
        "no_windows_api_called": True,
        "no_authority_granted": True,
    }
    return result


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--selftest", action="store_true")
    cli.add_argument("--receipt", type=Path)
    cli.add_argument("--source-sha256")
    cli.add_argument("--attempt")
    args = cli.parse_args()
    if args.selftest and (args.receipt or args.source_sha256 or args.attempt):
        cli.error("selftest does not accept a live receipt")
    if args.selftest:
        output = selftest()
        print(json.dumps(output, sort_keys=True))
        return 0 if output["status"] == "PASS" else 2
    if not (args.receipt and args.source_sha256 and args.attempt):
        cli.error("--receipt, --source-sha256 and --attempt all required")
    try:
        data, sha = read_receipt(args.receipt)
        output = verify(data, expected_sha256=args.source_sha256,
                        expected_attempt=args.attempt)
        output["source_receipt_sha256"] = sha
        print(json.dumps(output, sort_keys=True))
        return 0
    except (Refused, OSError) as exc:
        print(json.dumps({"status": "REFUSED",
                          "reason": str(exc) if isinstance(exc, Refused)
                          else type(exc).__name__}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
