#!/usr/bin/env python3
"""Set up the pinned CLI-Anything FreeCAD pilot and its portable FreeCAD backend."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything.json"
PATCH_PATH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything-freecad-overlay.patch"
LOCAL_ROOT = ROOT / ".local-devtools" / "phase5"
CLONE = LOCAL_ROOT / "cli-anything"
VENV = LOCAL_ROOT / "venv"
TOOLS_ROOT = Path.home() / "Documents" / "VelvetPrintLab" / "tools"
FREECAD_NAME = "FreeCAD_1.1.3-Windows-x86_64-py311"
FREECAD_ROOT = TOOLS_ROOT / FREECAD_NAME
FREECAD_CMD = FREECAD_ROOT / "FreeCADCmd.exe"
FREECAD_ARCHIVE = TOOLS_ROOT / f"{FREECAD_NAME}.7z"
FREECAD_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.3/"
    "FreeCAD_1.1.3-Windows-x86_64-py311.7z"
)
FREECAD_SHA256 = "9c6959dc9c4dba64dd818a62447e3dfedb4221d776fb044b239d462f150bcec4"
def run(args: list[str], *, cwd: Path | None = None, check: bool = True,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, env=env)
    if check and proc.returncode:
        raise SystemExit(
            f"FAIL {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def remove_tree(path: Path) -> None:
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=clear_readonly)


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))


def validate_cost_preflights(registry: dict) -> None:
    rels = [
        registry["cost_preflight"],
        registry["freecad"]["cost_preflight"],
    ]
    for rel in rels:
        run([
            sys.executable,
            str(ROOT / "scripts" / "vf_cost_preflight.py"),
            "validate",
            str(ROOT / rel),
        ], cwd=ROOT)
        print(f"OK cost preflight {rel}")


def ensure_clone(registry: dict) -> None:
    pin = registry["pin"]
    if (CLONE / ".git").is_dir():
        head = run(["git", "rev-parse", "HEAD"], cwd=CLONE).stdout.strip()
        if head != pin:
            remove_tree(CLONE)
    if not (CLONE / ".git").is_dir():
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        CLONE.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q"], cwd=CLONE)
        run(["git", "remote", "add", "origin", registry["source"]], cwd=CLONE)
        run(["git", "fetch", "-q", "--depth", "1", "origin", pin], cwd=CLONE)
        run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=CLONE)
    head = run(["git", "rev-parse", "HEAD"], cwd=CLONE).stdout.strip()
    if head != pin:
        raise SystemExit(f"FAIL CLI-Anything pin mismatch: {head}")
    print(f"OK CLI-Anything source {head[:12]}")
def overlay_applied() -> bool:
    return run(
        ["git", "apply", "--unidiff-zero", "--reverse", "--check", str(PATCH_PATH)],
        cwd=CLONE,
        check=False,
    ).returncode == 0


def apply_overlay() -> None:
    if overlay_applied():
        print("OK FreeCAD boolean/export overlay already applied")
        return
    dirty = run(["git", "status", "--porcelain"], cwd=CLONE).stdout.strip()
    if dirty:
        raise SystemExit(
            "FAIL CLI-Anything clone has unexpected local changes; "
            "refusing to overwrite before overlay"
        )
    check = run(
        ["git", "apply", "--unidiff-zero", "--check", str(PATCH_PATH)],
        cwd=CLONE,
        check=False,
    )
    if check.returncode:
        raise SystemExit(f"FAIL overlay no longer applies:\n{check.stderr}")
    run(["git", "apply", "--unidiff-zero", str(PATCH_PATH)], cwd=CLONE)
    if not overlay_applied():
        raise SystemExit("FAIL overlay applied but reverse check did not pass")
    print("OK FreeCAD boolean/export overlay applied")


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_venv() -> None:
    py = venv_python()
    if not py.is_file():
        VENV.parent.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(VENV)])
    packages = [
        "click==8.5.0",
        "prompt-toolkit==3.0.53",
        "pytest==9.1.1",
        "Pillow==12.3.0",
    ]
    run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
         "--no-input", *packages])
    harness = CLONE / "freecad" / "agent-harness"
    run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
         "--no-input", "--no-deps", "-e", str(harness)])
    run([str(py), "-m", "pip", "check"])
    print("OK isolated CLI-Anything FreeCAD venv")
def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_freecad() -> None:
    TOOLS_ROOT.mkdir(parents=True, exist_ok=True)
    part = FREECAD_ARCHIVE.with_suffix(FREECAD_ARCHIVE.suffix + ".part")
    with urllib.request.urlopen(FREECAD_URL) as response, part.open("wb") as out:
        shutil.copyfileobj(response, out)
    actual = file_sha256(part)
    if actual != FREECAD_SHA256:
        part.unlink(missing_ok=True)
        raise SystemExit(f"FAIL FreeCAD SHA256 mismatch: {actual}")
    part.replace(FREECAD_ARCHIVE)
    print(f"OK downloaded FreeCAD archive sha256={actual}")


def ensure_freecad() -> None:
    if FREECAD_CMD.is_file():
        version = run([str(FREECAD_CMD), "--version"]).stdout.strip()
        if "FreeCAD 1.1.3" not in version:
            raise SystemExit(f"FAIL unexpected FreeCAD version: {version}")
        print(f"OK {version}")
        return
    if not FREECAD_ARCHIVE.is_file() or file_sha256(FREECAD_ARCHIVE) != FREECAD_SHA256:
        download_freecad()
    else:
        print("OK existing FreeCAD archive hash")
    run(["tar", "-xf", str(FREECAD_ARCHIVE)], cwd=TOOLS_ROOT)
    if not FREECAD_CMD.is_file():
        raise SystemExit(f"FAIL FreeCADCmd missing after extraction: {FREECAD_CMD}")
    version = run([str(FREECAD_CMD), "--version"]).stdout.strip()
    if "FreeCAD 1.1.3" not in version:
        raise SystemExit(f"FAIL unexpected FreeCAD version: {version}")
    print(f"OK {version}")
def uninstall(remove_freecad: bool) -> None:
    if CLONE.exists():
        remove_tree(CLONE)
        print(f"OK removed {CLONE}")
    if VENV.exists():
        remove_tree(VENV)
        print(f"OK removed {VENV}")
    if remove_freecad and FREECAD_ROOT.exists():
        remove_tree(FREECAD_ROOT)
        print(f"OK removed {FREECAD_ROOT}")
    if remove_freecad and FREECAD_ARCHIVE.exists():
        FREECAD_ARCHIVE.unlink()
        print(f"OK removed {FREECAD_ARCHIVE}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--remove-freecad", action="store_true")
    args = parser.parse_args()

    if args.uninstall:
        uninstall(args.remove_freecad)
        return

    registry = load_registry()
    validate_cost_preflights(registry)
    ensure_clone(registry)
    apply_overlay()
    ensure_venv()
    ensure_freecad()
    print("OK CLI-Anything FreeCAD pilot setup cost=0 gui-preview=disabled")


if __name__ == "__main__":
    main()
