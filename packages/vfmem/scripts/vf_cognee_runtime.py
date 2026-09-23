#!/usr/bin/env python3
"""Stage, promote and roll back the local Cognee runtime for vfmem.

This tool never discovers/chooses a version. A caller must pass an exact stable
version and the Git contract must be updated separately. Promotion is allowed only
when the staged receipt version equals packages/vfmem/cognee.json:pinnedVersion.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CFG_PATH = ROOT / "packages" / "vfmem" / "cognee.json"
ADAPTER = ROOT / "packages" / "vfmem" / "scripts" / "vf_cognee.py"
STABLE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
MACHINE = "VFMEM_COGNEE_JSON:"


def cfg() -> dict[str, Any]:
    return json.loads(CFG_PATH.read_text(encoding="utf-8"))


def home() -> Path:
    return Path(os.environ.get("VFMEM_COGNEE_HOME", "~/.velvetos")).expanduser().resolve()


def live_venv() -> Path:
    return Path(os.environ.get("VFMEM_COGNEE_LIVE_VENV", str(home() / "cognee-venv"))).expanduser().resolve()


def runtime_root() -> Path:
    return Path(os.environ.get("VFMEM_COGNEE_ROOT", str(home() / "cognee"))).expanduser().resolve()


def python_in(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def installed_version(venv: Path) -> str | None:
    py = python_in(venv)
    if not py.is_file():
        return None
    p = subprocess.run(
        [str(py), "-c", "import importlib.metadata as m; print(m.version('cognee'))"],
        text=True, encoding="utf-8", errors="replace", capture_output=True, env={**os.environ, "PYTHONUTF8": "1"}, timeout=30,
    )
    return p.stdout.strip() if p.returncode == 0 else None


def run_adapter(py: Path, command: str, root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.update({
        "PYTHONUTF8": "1",
        "VFMEM_COGNEE_MACHINE": "1",
        "VFMEM_COGNEE_ROOT": str(root),
    })
    p = subprocess.run(
        [str(py), str(ADAPTER), command],
        cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env, timeout=900,
    )
    framed = next(
        (line[len(MACHINE):] for line in reversed(p.stdout.splitlines()) if line.startswith(MACHINE)),
        None,
    )
    result = json.loads(framed) if framed else {
        "status": "BLOCKED",
        "reason": (p.stderr or p.stdout or f"exit {p.returncode}")[-1600:],
    }
    if p.returncode != 0 or result.get("status") not in {"PASS", "CURRENT", "SYNCED", "OK"}:
        raise RuntimeError(f"{command} failed: {json.dumps(result, ensure_ascii=True)[:1800]}")
    return result


def atomic_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def stage(version: str, base_python: str | None) -> dict[str, Any]:
    if not STABLE.fullmatch(version):
        raise RuntimeError("candidate must be an exact stable x.y.z version")
    base = Path(base_python).expanduser().resolve() if base_python else Path(sys.executable).resolve()
    if not base.is_file():
        raise RuntimeError("base Python executable missing")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    stage_dir = root / "staging" / f"cognee-{version}-{stamp}"
    data_dir = root / "staging-data" / f"cognee-{version}-{stamp}"
    if stage_dir.exists():
        raise RuntimeError("staging destination already exists")

    subprocess.run([str(base), "-m", "venv", str(stage_dir)], check=True, timeout=180)
    py = python_in(stage_dir)
    subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip"],
        check=True, timeout=300, env={**os.environ, "PYTHONUTF8": "1"},
    )
    subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", f"cognee[gliner]=={version}"],
        check=True, timeout=1200, env={**os.environ, "PYTHONUTF8": "1"},
    )
    actual = installed_version(stage_dir)
    if actual != version:
        raise RuntimeError(f"staged version mismatch: expected {version}, got {actual}")

    smoke = run_adapter(py, "smoke", data_dir)
    receipt = {
        "schema": "vf.cognee.runtime-stage.v1",
        "version": version,
        "stageVenv": str(stage_dir),
        "stageData": str(data_dir),
        "basePython": str(base),
        "smoke": smoke,
        "status": "PASS",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = root / "staging" / f"receipt-{version}-{stamp}.json"
    atomic_json(receipt_path, receipt)
    return {"status": "PASS", "receipt": str(receipt_path), **receipt}


def promote(receipt_path: str) -> dict[str, Any]:
    rp = Path(receipt_path).expanduser().resolve()
    if not rp.is_file() or not rp.is_relative_to(runtime_root()):
        raise RuntimeError("receipt must exist inside Cognee runtime root")
    receipt = json.loads(rp.read_text(encoding="utf-8"))
    if receipt.get("schema") != "vf.cognee.runtime-stage.v1" or receipt.get("status") != "PASS":
        raise RuntimeError("invalid or non-PASS staging receipt")

    version = receipt.get("version")
    pinned = cfg().get("pinnedVersion")
    if version != pinned:
        raise RuntimeError(f"promotion blocked: staged {version} != Git pin {pinned}")

    stage_dir = Path(receipt["stageVenv"]).resolve()
    if not stage_dir.is_dir() or installed_version(stage_dir) != version:
        raise RuntimeError("staged venv missing or version drifted")

    live = live_venv()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rollback = live.with_name(f"{live.name}.rollback-{stamp}")
    failed = live.with_name(f"{live.name}.failed-{stamp}")
    if rollback.exists() or failed.exists():
        raise RuntimeError("promotion archive collision")
    live.parent.mkdir(parents=True, exist_ok=True)

    had_live = live.exists()
    if had_live:
        live.rename(rollback)
    try:
        stage_dir.rename(live)
        doctor = run_adapter(python_in(live), "doctor", runtime_root())
        if doctor.get("installedVersion") != pinned or doctor.get("versionMatch") is not True:
            raise RuntimeError("post-promotion doctor version mismatch")
    except Exception:
        if live.exists():
            live.rename(failed)
        if had_live and rollback.exists():
            rollback.rename(live)
        raise

    record = {
        "schema": "vf.cognee.runtime-promotion.v1",
        "version": version,
        "liveVenv": str(live),
        "rollbackVenv": str(rollback) if had_live else None,
        "doctor": doctor,
        "promotedAt": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
    }
    atomic_json(runtime_root() / "last-promotion.json", record)
    return record


def rollback() -> dict[str, Any]:
    live = live_venv()
    candidates = sorted(live.parent.glob(f"{live.name}.rollback-*"), reverse=True)
    if not candidates:
        raise RuntimeError("no rollback venv available")
    target = candidates[0]
    if not target.is_dir():
        raise RuntimeError("rollback target is not a directory")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    displaced = live.with_name(f"{live.name}.rolled-back-from-{stamp}")
    if live.exists():
        live.rename(displaced)
    try:
        target.rename(live)
        doctor = run_adapter(python_in(live), "doctor", runtime_root())
    except Exception:
        if live.exists():
            live.rename(target)
        if displaced.exists():
            displaced.rename(live)
        raise
    record = {
        "schema": "vf.cognee.runtime-rollback.v1",
        "restoredVersion": installed_version(live),
        "liveVenv": str(live),
        "displacedVenv": str(displaced) if displaced.exists() else None,
        "doctor": doctor,
        "rolledBackAt": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
    }
    atomic_json(runtime_root() / "last-rollback.json", record)
    return record


def status() -> dict[str, Any]:
    c = cfg()
    live = live_venv()
    return {
        "status": "PASS",
        "pinnedVersion": c.get("pinnedVersion"),
        "installedVersion": installed_version(live),
        "versionMatch": installed_version(live) == c.get("pinnedVersion"),
        "liveVenv": str(live),
        "runtimeRoot": str(runtime_root()),
        "rollbackVenvs": [str(x) for x in sorted(live.parent.glob(f"{live.name}.rollback-*"), reverse=True)],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    s = sub.add_parser("stage")
    s.add_argument("--version", required=True)
    s.add_argument("--python")
    pr = sub.add_parser("promote")
    pr.add_argument("--receipt", required=True)
    sub.add_parser("rollback")
    a = p.parse_args(argv)
    try:
        if a.cmd == "status":
            result = status()
        elif a.cmd == "stage":
            result = stage(a.version, a.python)
        elif a.cmd == "promote":
            result = promote(a.receipt)
        else:
            result = rollback()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)[:1800]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())