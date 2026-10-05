#!/usr/bin/env python3
"""Fail-closed structural sensor for the Office v2 Phase 1 Lab boundary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "docs" / "implementation" / "office-v2" / "phase1" / "lab-boundary-v0.json"

PRODUCTION_ROOTS = (
    "D:/Velvet/State/OfficeV2",
    "D:/Velvet/State/CreativeCraft",
    "D:/Velvet/State/DCC-MCP",
    "D:/Velvet/Services/OpenPost",
)
REQUIRED_DIR_KEYS = {
    "artifacts_windows", "artifacts_wsl", "volumes", "logs",
    "backups", "identity_stubs", "compose", "otel",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not CONFIG.is_file():
        fail("missing Phase 1 lab-boundary-v0.json")
    data = json.loads(CONFIG.read_text(encoding="utf-8-sig"))

    if data.get("lab_root") != "D:/Velvet/Lab/OfficeV2":
        fail("lab_root must be dedicated D:/Velvet/Lab/OfficeV2")
    if data.get("compose_project") != "officev2lab":
        fail("compose_project mismatch")

    network = data.get("network") or {}
    if network.get("name") != "officev2-lab":
        fail("dedicated lab network name missing")
    if network.get("production_network_membership_allowed") is not False:
        fail("production network membership must be forbidden")
    if network.get("host_bind_default") != "127.0.0.1":
        fail("default host bind must be loopback")

    credentials = data.get("credential_policy") or {}
    if credentials.get("production_credentials_allowed") is not False:
        fail("production credentials must be forbidden in LAB")
    if credentials.get("production_secret_mounts_allowed") is not False:
        fail("production secret mounts must be forbidden in LAB")
    if "PRODUCTION_SCOPED_WRITE" in set(credentials.get("allowed_classes") or []):
        fail("production write credential class leaked into LAB")

    authority = data.get("authority_policy") or {}
    for key in ("lab_business_truth_authority", "lab_production_writer_authority", "lab_approval_authority"):
        if authority.get(key) is not False:
            fail(f"{key} must be false")

    paths = data.get("paths") or {}
    if set(paths) != REQUIRED_DIR_KEYS:
        fail(f"lab path keys mismatch: {sorted(paths)}")
    for key, value in paths.items():
        if key == "artifacts_wsl":
            if not str(value).startswith("/mnt/d/Velvet/Lab/OfficeV2/"):
                fail("WSL artifact lane must map the dedicated D: LAB root")
            continue
        if not str(value).startswith("D:/Velvet/Lab/OfficeV2/"):
            fail(f"{key} escapes LAB root")
        if any(str(value).startswith(prod) for prod in PRODUCTION_ROOTS):
            fail(f"{key} points at production state")

    ports = data.get("ports") or {}
    concrete = [
        ports.get("otel_grpc"), ports.get("otel_http"), ports.get("candidate_postgres"),
        ports.get("lab_api"), ports.get("lab_ui"),
    ]
    if not all(isinstance(p, int) and 1024 <= p <= 65535 for p in concrete):
        fail("invalid concrete lab ports")
    if len(set(concrete)) != len(concrete):
        fail("duplicate concrete lab ports")
    if ports.get("forbidden_known_collision") in concrete:
        fail("known production collision reused")
    if ports.get("candidate_range_start", 0) > ports.get("candidate_range_end", -1):
        fail("candidate port range invalid")

    postgres = data.get("candidate_postgres") or {}
    if postgres.get("universal_office_database") is not False:
        fail("Postgres must not become universal Office DB")
    if postgres.get("role") != "DISPOSABLE_OR_CANDIDATE_SPECIFIC_ONLY":
        fail("Postgres role violates Phase 1 rule")

    untrusted = data.get("untrusted_code") or {}
    if untrusted.get("direct_windows_execution_allowed") is not False:
        fail("untrusted code must not run directly on Windows")
    if untrusted.get("direct_wsl_host_execution_allowed") is not False:
        fail("untrusted code must not run directly on WSL host")

    reboot = data.get("phase1_reboot_boundary") or {}
    if reboot.get("automatic_reboot_allowed") is not False:
        fail("automatic reboot must remain false")
    if reboot.get("wsl_feature_enabled") is not True or reboot.get("virtual_machine_platform_enabled") is not True:
        fail("staged feature state not represented")

    raw = CONFIG.read_text(encoding="utf-8-sig")
    forbidden_literals = ("Bearer ", "PRIVATE KEY", "GOOGLE_TOKEN=", "VELVETOS_CONTROL_API_TOKEN=")
    if any(item in raw for item in forbidden_literals):
        fail("secret-like literal found in LAB boundary config")

    print("OK office-v2-phase1-boundary isolated=PASS secrets=NONE authority=NONE auto_reboot=NO")


if __name__ == "__main__":
    main()
