#!/usr/bin/env python3
"""#604: fail-closed origin gate for PUBLIC Windows Sandbox smoke receipts.

Pure offline inspection: NO VM launch, no guest source execution, no user token
bridge, no Git effect, no network, no model, no credentials. A guest/host-writable
JSON receipt cannot attest that a Sandbox VM was launched or isolated. This
verifier intentionally has NO positive guest-admission path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

CHALLENGE_SCHEMA = "velvetos.office-v2.p0-wsb-attended-synthetic-challenge.v0"
RECEIPT_SCHEMA = "velvetos.office-v2.p0-wsb-attended-synthetic-guest-receipt.v0"
TASK = "p0-604-wsb-attended-smoke-20261011-a1"
NONCE = re.compile(r"[0-9a-f]{32}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
BLOCKED = "BLOCKED_UNTRUSTED_GUEST_RECEIPT_ORIGIN_NO_HOST_WITNESS"


class Refused(Exception):
    pass


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise Refused(reason)


def result(status: str, **extra: object) -> dict:
    return {
        "schema": "velvetos.office-v2.p0-604-wsb-receipt-origin-gate.v0",
        "status": status,
        "guest_origin_attested": False,
        "independent_host_launch_witness_observed": False,
        "guest_network_and_input_denials_independently_verified": False,
        "actual_vm_guest_isolation_proven": False,
        "generated_code_executed": False,
        "git_sink_credential_custody_proven": False,
        "production_authority": False,
        "external_effects": 0,
        "model_calls": 0,
        **extra,
    }


def check_challenge(challenge: dict) -> None:
    need(type(challenge) is dict, "PUBLIC_CHALLENGE_NOT_OBJECT")
    need(
        challenge.get("schema") == CHALLENGE_SCHEMA
        and challenge.get("task_id") == TASK
        and isinstance(challenge.get("nonce"), str)
        and NONCE.fullmatch(challenge["nonce"]) is not None
        and isinstance(challenge.get("guest_script_sha256"), str)
        and DIGEST.fullmatch(challenge["guest_script_sha256"]) is not None
        and challenge.get("model_calls") == 0
        and challenge.get("production_authority") is False
        and challenge.get("credential_imports") == 0,
        "PUBLIC_CHALLENGE_SCOPE_INVALID",
    )


def evaluate(challenge: dict, receipt: dict | None) -> dict:
    check_challenge(challenge)
    if receipt is None:
        return result(
            "NO_GUEST_RECEIPT_ONLY_HOST_STATIC_PREFLIGHT_ELIGIBLE",
            guest_receipt_observed=False,
            reason="ACTUAL_SANDBOX_NOT_OBSERVED",
        )
    need(type(receipt) is dict, "UNTRUSTED_RECEIPT_NOT_OBJECT")
    required_true = (
        "mapped_input_readonly_write_denied",
        "guest_tcp_egress_connection_denied",
        "source_bytes_match_host_pin",
        "end_to_end_accepted",
    )
    required_false = (
        "model_generated_python_executed",
        "arbitrary_generated_code_admitted",
        "independent_git_sink_signer_proven",
        "general_kernel_escape_resistance_proven",
        "guest_production_credentials_provided",
    )
    need(
        receipt.get("schema") == RECEIPT_SCHEMA
        and receipt.get("status") == "ATTENDED_GUEST_SMOKE_OBSERVATION_ONLY"
        and receipt.get("task_id") == challenge["task_id"]
        and receipt.get("nonce") == challenge["nonce"]
        and all(receipt.get(k) is True for k in required_true)
        and all(receipt.get(k) is False for k in required_false),
        "UNTRUSTED_GUEST_REPORT_FIELDS_INVALID",
    )
    # Even a syntactically perfect or self-declared 'attested' JSON is writable
    # by the host and by the guest. Never derive a trusted launch event from it.
    return result(
        BLOCKED,
        guest_receipt_observed=True,
        receipt_fields_consistent_with_public_challenge=True,
        reason="SEPARATE_TRUSTED_HOST_LAUNCH_WITNESS_NOT_ADMITTED",
    )


def read_public_json(path: Path) -> dict:
    need(path.is_file() and not path.is_symlink(), "PUBLIC_SOURCE_FILE_INVALID")
    need(path.stat().st_size < 65536, "PUBLIC_JSON_TOO_LARGE")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    need(type(value) is dict, "PUBLIC_JSON_NOT_OBJECT")
    return value


def inspect(root: Path) -> dict:
    need(root.is_absolute() and root.parent.name == "AgentEnvelopeLab"
         and root.name.startswith("p0-604-wsb-")
         and root.is_dir() and not root.is_symlink(),
         "EXPLICIT_DISPOSABLE_WSB_LAB_ROOT_REQUIRED")
    inp, out = root / "public-input", root / "public-output"
    need(inp.is_dir() and out.is_dir() and not inp.is_symlink()
         and not out.is_symlink(), "LAB_MOUNTS_MISSING_OR_ALIASED")
    challenge = read_public_json(inp / "challenge.json")
    check_challenge(challenge)
    script = inp / "run-public-smoke.ps1"
    need(script.is_file() and not script.is_symlink()
         and script.stat().st_size < 65536,
         "EXPECTED_PUBLIC_SMOKE_SCRIPT_MISSING")
    need(hashlib.sha256(script.read_bytes()).hexdigest()
         == challenge["guest_script_sha256"],
         "HOST_PUBLIC_SCRIPT_PIN_DRIFT")
    expected = "guest-" + challenge["nonce"] + ".json"
    found = list(out.iterdir())
    need(len(found) <= 1
         and all(p.name == expected and p.is_file() and not p.is_symlink()
                 for p in found), "UNEXPECTED_GUEST_WRITABLE_OUTPUT")
    observed = read_public_json(found[0]) if found else None
    return evaluate(challenge, observed)


def selftest() -> dict:
    challenge = {
        "schema": CHALLENGE_SCHEMA, "task_id": TASK,
        "nonce": "0123456789abcdef0123456789abcdef",
        "guest_script_sha256": "a" * 64, "credential_imports": 0,
        "model_calls": 0, "production_authority": False,
    }
    guest = {
        "schema": RECEIPT_SCHEMA,
        "status": "ATTENDED_GUEST_SMOKE_OBSERVATION_ONLY",
        "task_id": TASK, "nonce": challenge["nonce"],
        "mapped_input_readonly_write_denied": True,
        "guest_tcp_egress_connection_denied": True,
        "source_bytes_match_host_pin": True,
        "end_to_end_accepted": True,
        "model_generated_python_executed": False,
        "arbitrary_generated_code_admitted": False,
        "independent_git_sink_signer_proven": False,
        "general_kernel_escape_resistance_proven": False,
        "guest_production_credentials_provided": False,
    }
    checks = 0
    clean = evaluate(challenge, None)
    need(clean["guest_receipt_observed"] is False
         and clean["actual_vm_guest_isolation_proven"] is False, "EMPTY_FALSE_PASS")
    checks += 1
    for extra in (
        {}, {"actual_vm_launch": False, "guest_process_id": -1},
        {"guest_origin_attested": True, "host_witness": "FORGED"},
        {"captured_at_utc": "2000-01-01T00:00:00Z"},
        {"host_sandbox_process_observed": True},
        {"independent_host_launch_witness_observed": True},
    ):
        claim = dict(guest, **extra)
        value = evaluate(challenge, claim)
        need(value["status"] == BLOCKED
             and value["guest_origin_attested"] is False
             and value["actual_vm_guest_isolation_proven"] is False
             and value["external_effects"] == 0, "FAKE_GUEST_FALSE_ADMISSION")
        checks += 1
    for key, bad in (
        ("nonce", "f" * 32),
        ("source_bytes_match_host_pin", False),
        ("mapped_input_readonly_write_denied", False),
        ("guest_tcp_egress_connection_denied", False),
        ("end_to_end_accepted", False),
        ("model_generated_python_executed", True),
        ("arbitrary_generated_code_admitted", True),
        ("independent_git_sink_signer_proven", True),
        ("general_kernel_escape_resistance_proven", True),
        ("guest_production_credentials_provided", True),
    ):
        altered = dict(guest, **{key: bad})
        try:
            evaluate(challenge, altered)
        except Refused:
            checks += 1
        else:
            raise Refused("MALFORMED_RECEIPT_FALSE_ADMISSION_" + key)
    bad_challenge = dict(challenge, credential_imports=1)
    try:
        evaluate(bad_challenge, guest)
    except Refused:
        checks += 1
    else:
        raise Refused("PRIVILEGED_CHALLENGE_FALSE_ADMISSION")
    need(checks == 18, "EXPECTED_18_OFFLINE_NEGATIVES")
    return result(
        "PASS_18_OFFLINE_ORIGIN_NEGATIVES_NOT_VM_ATTESTATION",
        tests=checks, guest_receipt_acceptance_proven=False,
        actual_vm_launched=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("selftest", "inspect"))
    parser.add_argument("--root")
    args = parser.parse_args()
    need(args.mode == "selftest" or bool(args.root), "INSPECT_LAB_ROOT_REQUIRED")
    row = selftest() if args.mode == "selftest" else inspect(Path(args.root))
    print(json.dumps(row, sort_keys=True))
    return 0 if args.mode == "selftest" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refused, OSError, ValueError, UnicodeError) as exc:
        print(json.dumps(result("FAIL_CLOSED_RECEIPT_ORIGIN_POLICY",
                                reason=str(exc)[:180]), sort_keys=True))
        raise SystemExit(2)
