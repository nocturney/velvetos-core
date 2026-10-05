#!/usr/bin/env python3
"""Read-only Office v2 Phase 1 LAB/host admission doctor."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

LAB_ROOT = Path(r"D:\Velvet\OfficeV2Lab") if os.name == "nt" else Path("/mnt/d/Velvet/OfficeV2Lab")
WSL_DISTRO = os.environ.get("OFFICEV2_WSL_DISTRO", "OfficeV2-Lab")
PORTS = [14317, 14318, 14319, 15432, 18780]


def command(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        output = ((p.stdout or "") + (p.stderr or "")).replace("\x00", "")
        return p.returncode, output
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def port_free(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) != 0
    finally:
        s.close()


def pending_reboot_windows() -> dict[str, bool]:
    if os.name != "nt":
        return {"cbs": False, "windows_update": False, "pending_file_rename": False}
    ps = (
        "$c=Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending';"
        "$w=Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired';"
        "$p=(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager' "
        "-Name PendingFileRenameOperations -ErrorAction SilentlyContinue).PendingFileRenameOperations;"
        "Write-Output ($c.ToString()+'|'+$w.ToString()+'|'+([bool]$p).ToString())"
    )
    code, out = command(["powershell", "-NoProfile", "-Command", ps])
    if code != 0:
        return {"cbs": True, "windows_update": True, "pending_file_rename": True}
    line = out.strip().splitlines()[-1] if out.strip() else "True|True|True"
    parts = [x.strip().lower() == "true" for x in line.split("|")]
    if len(parts) != 3:
        return {"cbs": True, "windows_update": True, "pending_file_rename": True}
    return {"cbs": parts[0], "windows_update": parts[1], "pending_file_rename": parts[2]}


def detect() -> dict[str, Any]:
    roots = {
        name: (LAB_ROOT / name).is_dir()
        for name in ("artifacts", "backups", "state", "logs")
    }
    ports = {str(port): ("FREE" if port_free(port) else "IN_USE") for port in PORTS}

    if os.name == "nt":
        wsl_code, wsl_out = command(["wsl", "--status"])
        wsl_platform_ready = wsl_code == 0 and "not installed" not in wsl_out.lower()
        list_code, list_out = command(["wsl", "--list", "--quiet"]) if wsl_platform_ready else (127, "")
        distros = [line.strip() for line in list_out.splitlines() if line.strip()]
        distro_ready = list_code == 0 and any(name.casefold() == WSL_DISTRO.casefold() for name in distros)
        wsl_ready = wsl_platform_ready and distro_ready
        if distro_ready:
            docker_code, docker_out = command([
                "wsl", "-d", WSL_DISTRO, "--",
                "docker", "version", "--format", "{{.Server.Version}}",
            ])
            docker_path = f"wsl:{WSL_DISTRO}:docker"
            docker_ready = docker_code == 0
        else:
            docker_code, docker_out, docker_path, docker_ready = 127, "WSL LAB distro missing", None, False
    else:
        wsl_code, wsl_out, wsl_platform_ready, distro_ready, wsl_ready = 0, "not-applicable", True, True, True
        docker_path = shutil.which("docker")
        docker_code, docker_out = (
            command([docker_path, "version", "--format", "{{.Server.Version}}"])
            if docker_path else (127, "missing")
        )
        docker_ready = docker_path is not None and docker_code == 0

    reboot = pending_reboot_windows()

    if any(reboot.values()):
        verdict = "MAINTENANCE_BLOCKED_PREP_ALLOWED"
        mutations_allowed = False
        reason = "pending reboot state exists"
    elif not wsl_ready or not docker_ready:
        verdict = "RUNTIME_MISSING_PREP_ALLOWED"
        mutations_allowed = False
        reason = "WSL/Docker runtime is not ready"
    elif not all(roots.values()) or any(v != "FREE" for v in ports.values()):
        verdict = "LAB_BOUNDARY_NOT_READY"
        mutations_allowed = False
        reason = "LAB roots/ports are not ready"
    else:
        verdict = "READY_FOR_LAB_RUNTIME"
        mutations_allowed = True
        reason = "read-only prerequisites pass"

    return {
        "schema": "velvetos.office-v2.lab-doctor.v0",
        "platform": platform.platform(),
        "verdict": verdict,
        "host_mutation_allowed": mutations_allowed,
        "reason": reason,
        "lab_root": str(LAB_ROOT).replace("\\", "/"),
        "roots": roots,
        "ports": ports,
        "wsl": {
            "ready": wsl_ready,
            "platform_ready": wsl_platform_ready,
            "distro": WSL_DISTRO,
            "distro_ready": distro_ready,
            "exit_code": wsl_code,
            "summary": wsl_out.strip()[:500],
        },
        "docker": {
            "ready": docker_ready,
            "surface": f"WSL:{WSL_DISTRO}" if os.name == "nt" else "LOCAL_LINUX",
            "path": docker_path,
            "exit_code": docker_code,
            "summary": docker_out.strip()[:500],
        },
        "pending_reboot": reboot,
        "writes_performed": 0,
    }


def decide(f: dict[str, Any]) -> str:
    if f["pending_reboot"]:
        return "MAINTENANCE_BLOCKED_PREP_ALLOWED"
    if not f["wsl_ready"] or not f["docker_ready"]:
        return "RUNTIME_MISSING_PREP_ALLOWED"
    if not f["roots_ready"] or not f["ports_ready"]:
        return "LAB_BOUNDARY_NOT_READY"
    return "READY_FOR_LAB_RUNTIME"


def self_test() -> dict[str, Any]:
    blocked = decide({
        "pending_reboot": True,
        "wsl_ready": False,
        "docker_ready": False,
        "roots_ready": True,
        "ports_ready": True,
    })
    missing = decide({
        "pending_reboot": False,
        "wsl_ready": False,
        "docker_ready": False,
        "roots_ready": True,
        "ports_ready": True,
    })
    ready = decide({
        "pending_reboot": False,
        "wsl_ready": True,
        "docker_ready": True,
        "roots_ready": True,
        "ports_ready": True,
    })
    ok = (
        blocked == "MAINTENANCE_BLOCKED_PREP_ALLOWED"
        and missing == "RUNTIME_MISSING_PREP_ALLOWED"
        and ready == "READY_FOR_LAB_RUNTIME"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "blocked_fixture": blocked,
        "missing_runtime_fixture": missing,
        "ready_fixture": ready,
        "writes_performed": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = self_test() if args.self_test else detect()
    print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if (result.get("status") == "PASS" or result.get("verdict")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
