#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P1 = ROOT / "docs" / "implementation" / "office-v2" / "phase1"
LAB = ROOT / "tools" / "office-v2-lab"

REQUIRED = [
    P1 / "README.md",
    P1 / "lab-boundary-v0.json",
    P1 / "host-change-admission-v0.md",
    P1 / "maintenance-runbook-v0.md",
    P1 / "backup-restore-lab-v0.md",
    P1 / "otel-correlation-v0.json",
    LAB / "compose.yaml",
    LAB / "otel-collector.yaml",
    LAB / "env.example",
    ROOT / "scripts" / "vf_office_v2_lab_doctor.py",
    ROOT / "scripts" / "vf_office_v2_lab_lifecycle.py",
    ROOT / "scripts" / "vf_office_v2_node_manifest.py",
    ROOT / "scripts" / "vf_office_v2_trace_fixture.py",
]


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def self_test(path: Path) -> None:
    p = subprocess.run(
        [sys.executable, str(path), "--self-test", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if p.returncode != 0:
        fail(path.name + " self-test failed")
    data = json.loads(p.stdout)
    if data.get("status") != "PASS":
        fail(path.name + " self-test status is not PASS")


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 1 files: " + ", ".join(missing))

    cfg = json.loads((P1 / "lab-boundary-v0.json").read_text(encoding="utf-8-sig"))
    if cfg.get("production_authority") != "NONE":
        fail("LAB authority boundary mismatch")
    if cfg.get("production_credentials_allowed") is not False:
        fail("LAB must deny production credentials")
    wsl = cfg.get("wsl_runtime") or {}
    if wsl.get("source_distribution") != "Ubuntu-26.04":
        fail("WSL source distribution mismatch")
    if wsl.get("instance_name") != "OfficeV2-Lab":
        fail("dedicated WSL instance name mismatch")
    if wsl.get("docker_desktop_required") is not False:
        fail("Docker Desktop must not be required by the neutral LAB")
    if cfg.get("network", {}).get("name") != "officev2_lab":
        fail("LAB network mismatch")
    if cfg.get("ports") != {
        "otel_grpc": 14317,
        "otel_http": 14318,
        "otel_health": 14319,
        "candidate_db": 15432,
        "node_health": 18780,
    }:
        fail("LAB ports mismatch")
    if cfg.get("artifact_lane", {}).get("windows") != "D:/Velvet/OfficeV2Lab/artifacts":
        fail("artifact lane mismatch")
    if cfg.get("stateful_candidate_rule") != "RESTORE_DRILL_REQUIRED_BEFORE_PRODUCTION_CAPABLE":
        fail("stateful admission rule mismatch")

    compose = (LAB / "compose.yaml").read_text(encoding="utf-8-sig")
    for marker in (
        "officev2-otel",
        "officev2_lab",
        "127.0.0.1:14317:4317",
        "127.0.0.1:14318:4318",
        "127.0.0.1:14319:13133",
        "OTEL_COLLECTOR_IMAGE",
        "OFFICEV2_LAB_ARTIFACTS",
    ):
        if marker not in compose:
            fail("compose missing " + marker)
    if ":latest" in compose.lower():
        fail("unversioned image tag is not allowed")
    if "0.0.0.0:143" in compose:
        fail("LAB host ports must not bind all interfaces")

    env_example = (LAB / "env.example").read_text(encoding="utf-8-sig")
    for marker in ("OFFICEV2_WSL_DISTRO=OfficeV2-Lab", "PRODUCTION_CREDENTIALS_ALLOWED=false"):
        if marker not in env_example:
            fail("LAB env example missing " + marker)

    runbook = (P1 / "maintenance-runbook-v0.md").read_text(encoding="utf-8-sig")
    for marker in ("Ubuntu 26.04 LTS", "OfficeV2-Lab", "Stage A", "Stage F", "production credentials"):
        if marker not in runbook:
            fail("maintenance runbook missing " + marker)

    correlation = json.loads((P1 / "otel-correlation-v0.json").read_text(encoding="utf-8-sig"))
    required_trace = set(correlation.get("required_trace_attributes") or [])
    expected_trace = {
        "velvetos.request_id",
        "velvetos.project_id",
        "velvetos.workflow_id",
        "velvetos.run_id",
        "velvetos.attempt_id",
    }
    if required_trace != expected_trace:
        fail("OTel correlation required attributes mismatch")

    for path in (
        ROOT / "scripts" / "vf_office_v2_lab_doctor.py",
        ROOT / "scripts" / "vf_office_v2_lab_lifecycle.py",
        ROOT / "scripts" / "vf_office_v2_node_manifest.py",
        ROOT / "scripts" / "vf_office_v2_trace_fixture.py",
    ):
        self_test(path)

    print("OK office-v2-phase1 neutral-lab=PASS host-change=GATED")


if __name__ == "__main__":
    main()
