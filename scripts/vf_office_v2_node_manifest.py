#!/usr/bin/env python3
"""Publish a read-only Node Contract v0 observation for Office v2."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED = {
    "node_id", "os_build", "execution_surfaces", "cpu_ram", "gpu_vram",
    "installed_applications", "capability_contract_versions", "local_runtimes",
    "load", "health", "artifact_locality", "trust_security_level",
    "maintenance_state", "compatibility_range", "observed_at",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(args: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def win_value(script: str) -> str:
    code, out = run(["powershell", "-NoProfile", "-Command", script])
    return out.splitlines()[-1].strip() if code == 0 and out.strip() else "UNKNOWN"


def mac_value(args: list[str]) -> str:
    code, out = run(args)
    return out.strip() if code == 0 and out.strip() else "UNKNOWN"


def app_version(command: list[str], name: str) -> dict[str, str] | None:
    code, out = run(command)
    if code != 0 or not out:
        return None
    return {"name": name, "version": out.splitlines()[0].strip()[:200]}


def collect(node_id: str | None = None) -> dict[str, Any]:
    system = platform.system()
    hostname = socket.gethostname()
    node_id = node_id or ("windows-primary" if system == "Windows" else "mac-mini-office" if system == "Darwin" else hostname.lower())

    apps: list[dict[str, str]] = []
    runtimes: list[str] = [f"Python {platform.python_version()}"]
    health = "PASS"
    maintenance_state = "ACTIVE"
    evidence_refs: list[str] = []

    git = app_version(["git", "--version"], "Git")
    if git:
        apps.append(git)
        runtimes.append(git["version"])
    node = app_version(["node", "--version"], "Node.js")
    if node:
        apps.append(node)
        runtimes.append("Node.js " + node["version"])

    if system == "Windows":
        os_caption = win_value("(Get-CimInstance Win32_OperatingSystem).Caption")
        os_version = win_value("(Get-CimInstance Win32_OperatingSystem).Version")
        os_build = win_value("(Get-CimInstance Win32_OperatingSystem).BuildNumber")
        cpu = win_value("(Get-CimInstance Win32_Processor | Select-Object -First 1).Name")
        ram_raw = win_value("[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,2)")
        try:
            ram_gb = float(ram_raw)
        except ValueError:
            ram_gb = 0.0

        gpu_code, gpu_out = run([
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ])
        if gpu_code == 0 and gpu_out:
            parts = [x.strip() for x in gpu_out.splitlines()[0].split(",")]
            gpu = {
                "gpu": parts[0] if parts else "UNKNOWN",
                "vram_gb": round(float(parts[1]) / 1024, 2) if len(parts) > 1 else None,
                "driver": parts[2] if len(parts) > 2 else None,
            }
        else:
            gpu = None

        known = [
            ("Autodesk Maya", Path(r"C:\Program Files\Autodesk\Maya2027\bin\maya.exe")),
            ("Adobe After Effects", Path(r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe")),
        ]
        for name, path in known:
            if path.is_file():
                apps.append({"name": name, "version": "installed"})

        reboot_probe = win_value(
            "$c=Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending';"
            "$w=Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired';"
            "$p=(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager' "
            "-Name PendingFileRenameOperations -ErrorAction SilentlyContinue).PendingFileRenameOperations;"
            "$meaningful=@($p | Where-Object {$_ -and $_.Trim() -ne ''});"
            "Write-Output ($c.ToString()+'|'+$w.ToString()+'|'+$meaningful.Count)"
        )
        parts = reboot_probe.split("|")
        cbs_pending = len(parts) > 0 and parts[0].strip().lower() == "true"
        wu_pending = len(parts) > 1 and parts[1].strip().lower() == "true"
        try:
            rename_count = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            rename_count = 0
        if cbs_pending or wu_pending:
            health = "WARN"
            maintenance_state = "MAINTENANCE"
        elif rename_count:
            # Preserve delete-only/temp cleanup records as a visible warning; do not treat them as a reboot block.
            health = "WARN"
            maintenance_state = "ACTIVE"

        wsl_code, wsl_out = run(["wsl.exe", "--version"])
        if wsl_code == 0 and wsl_out:
            wsl_out = wsl_out.replace(chr(0), "")
            for line in wsl_out.splitlines():
                clean = line.strip()
                if clean.lower().startswith("wsl version:"):
                    runtimes.append("WSL " + clean.split(":", 1)[1].strip())
                elif clean.lower().startswith("kernel version:"):
                    runtimes.append("WSL kernel " + clean.split(":", 1)[1].strip())

        evidence_root = Path(r"D:\Velvet\Artifacts\OfficeV2\phase1\evidence")
        docker_receipts = sorted(evidence_root.glob("*/docker-user-verify.txt"), key=lambda p: p.stat().st_mtime, reverse=True) if evidence_root.is_dir() else []
        if docker_receipts:
            receipt_text = docker_receipts[0].read_text(encoding="utf-8-sig", errors="replace").replace(chr(0), "")
            for line in receipt_text.splitlines():
                if line.startswith("CLIENT=") and " SERVER=" in line:
                    runtimes.append("Docker Engine " + line.split(" SERVER=", 1)[1].strip())
                elif line.startswith("Docker Compose version "):
                    runtimes.append(line.strip())
            evidence_refs.append(str(docker_receipts[0]).replace("\\", "/"))

        probe_path = Path(r"D:\Velvet\Artifacts\OfficeV2\phase1\evidence\2026-10-06\phase1-final-user-probe.txt")
        if probe_path.is_file():
            probe_text = probe_path.read_text(encoding="utf-8-sig", errors="replace").replace(chr(0), "")
            for line in probe_text.splitlines():
                if line.startswith("PRETTY_NAME="):
                    distro_name = line.split("=", 1)[1].strip().strip('"')
                    runtimes.append("OfficeV2-Lab " + distro_name + " (WSL2)")
                    break
            if "SYSTEMD_EXIT|0" in probe_text:
                runtimes.append("OfficeV2-Lab systemd running")
            mnt_c_unmounted = "MNT_C_EXIT|0" not in probe_text
            mnt_d_unmounted = "MNT_D_EXIT|0" not in probe_text
            if "ARTIFACT_EXIT|0" in probe_text and mnt_c_unmounted and mnt_d_unmounted:
                runtimes.append("OfficeV2-Lab isolated artifact lane active")
            evidence_refs.append(str(probe_path).replace("\\", "/"))

        post_reboot = Path(r"D:\Velvet\Artifacts\OfficeV2\phase1\evidence\2026-10-06\post-reboot-admission.json")
        if post_reboot.is_file():
            evidence_refs.append(str(post_reboot).replace("\\", "/"))
        execution = ["Remote Desktop Commander", "PowerShell", "Python", "Node.js", "DCC Gateway"]
        artifacts = ["D:/Velvet", "D:/Velvet/OfficeV2Lab/artifacts"]
        transport = {"mode": "Remote Desktop Commander + local runtime", "authenticated": True, "arbitrary_shell": True}
    elif system == "Darwin":
        os_caption = "macOS"
        os_version = mac_value(["sw_vers", "-productVersion"])
        os_build = mac_value(["sw_vers", "-buildVersion"])
        cpu = mac_value(["sysctl", "-n", "machdep.cpu.brand_string"])
        if cpu == "UNKNOWN":
            cpu = mac_value(["sysctl", "-n", "hw.model"])
        ram_raw = mac_value(["sysctl", "-n", "hw.memsize"])
        try:
            ram_gb = round(int(ram_raw) / (1024 ** 3), 2)
        except ValueError:
            ram_gb = 0.0
        chip = mac_value(["sysctl", "-n", "machdep.cpu.brand_string"])
        gpu = {"gpu": chip if chip != "UNKNOWN" else "Apple integrated GPU", "vram_gb": None, "driver": None}
        execution = ["Remote Desktop Commander", "CreativeCraft Station Agent", "Python", "Node.js"]
        artifacts = ["/Users/chris/Velvet/Runtime/CreativeCraft"]
        transport = {"mode": "authenticated typed station transport", "authenticated": True, "arbitrary_shell": False}
    else:
        os_caption = system
        os_version = platform.release()
        os_build = platform.version()
        cpu = platform.processor() or "UNKNOWN"
        ram_gb = 0.0
        gpu = None
        execution = ["Python"]
        artifacts = []
        transport = {"mode": "local", "authenticated": True, "arbitrary_shell": True}

    manifest: dict[str, Any] = {
        "node_id": node_id,
        "os_build": {"platform": system.lower(), "version": f"{os_caption} {os_version}".strip(), "build": os_build},
        "execution_surfaces": execution,
        "cpu_ram": {"cpu": cpu, "ram_gb": ram_gb},
        "gpu_vram": gpu,
        "installed_applications": apps,
        "capability_contract_versions": [
            "velvetos.office-v2.capability-contract.v0",
            "velvetos.office-v2.node-contract.v0",
        ],
        "local_runtimes": runtimes,
        "load": {"state": "UNKNOWN", "observations": ["Phase 1 publisher does not infer load without a bounded live metric."]},
        "health": health,
        "artifact_locality": artifacts,
        "trust_security_level": "TRUSTED_OWNER_NODE",
        "maintenance_state": maintenance_state,
        "compatibility_range": [
            "Office v2 Phase 0 contracts",
            "Office v2 Phase 1 neutral LAB prep",
            "Office v2 Phase 1 runtime gate",
        ],
        "observed_at": now_iso(),
        "transport": transport,
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
    }
    return manifest


def validate(data: dict[str, Any]) -> list[str]:
    missing = sorted(REQUIRED - set(data))
    problems = ["missing:" + key for key in missing]
    if not data.get("node_id"):
        problems.append("node_id_empty")
    if data.get("health") not in {"PASS", "WARN", "FAIL", "UNKNOWN"}:
        problems.append("health_invalid")
    if data.get("maintenance_state") not in {"ACTIVE", "DRAINING", "MAINTENANCE", "OFFLINE", "UNKNOWN"}:
        problems.append("maintenance_state_invalid")
    return problems


def self_test() -> dict[str, Any]:
    fixture = {
        "node_id": "fixture",
        "os_build": {"platform": "windows", "version": "x", "build": "1"},
        "execution_surfaces": [],
        "cpu_ram": {"cpu": "x", "ram_gb": 1},
        "gpu_vram": None,
        "installed_applications": [],
        "capability_contract_versions": ["v0"],
        "local_runtimes": [],
        "load": {"state": "UNKNOWN"},
        "health": "PASS",
        "artifact_locality": [],
        "trust_security_level": "TRUSTED_OWNER_NODE",
        "maintenance_state": "ACTIVE",
        "compatibility_range": ["v0"],
        "observed_at": now_iso(),
    }
    good = validate(fixture)
    bad = validate({**fixture, "health": "BROKEN"})
    ok = not good and "health_invalid" in bad
    return {"status": "PASS" if ok else "FAIL", "good_problems": good, "negative_problems": bad}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-id")
    ap.add_argument("--output")
    ap.add_argument("--validate-file")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        result = self_test()
        print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1

    if args.validate_file:
        data = json.loads(Path(args.validate_file).read_text(encoding="utf-8-sig"))
        problems = validate(data)
        result = {"status": "PASS" if not problems else "FAIL", "problems": problems, "node_id": data.get("node_id")}
        print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not problems else 1

    data = collect(args.node_id)
    problems = validate(data)
    payload = {"status": "PASS" if not problems else "FAIL", "problems": problems, "manifest": data}
    if args.output and not problems:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
