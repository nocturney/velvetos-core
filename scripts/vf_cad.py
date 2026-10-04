#!/usr/bin/env python3
"""VelvetOS bridge to the local Text-to-CAD + VelvetPrintLab toolchain.

This bridge never uploads to a printer, starts a print, heats, or moves hardware.
It extends vfprod by reusing the existing VelvetPrintLab printer_matrix.json as
the printer/profile source of truth.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PRINTLAB = Path.home() / "Documents" / "VelvetPrintLab"


def printlab_root() -> Path:
    return Path(os.environ.get("VELVET_PRINTLAB_ROOT", DEFAULT_PRINTLAB)).resolve()


def text2cad_root(root: Path) -> Path:
    return Path(os.environ.get("TEXT_TO_CAD_ROOT", root / "tools" / "text-to-cad")).resolve()


def venv_python(repo: Path) -> Path:
    candidate = repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    # Keep the venv launcher path intact. On macOS, uv-created venvs use a
    # symlink here; resolving it would bypass pyvenv.cfg and lose site-packages.
    return candidate


def router_root(root: Path) -> Path:
    return (root / "slicer-router").resolve()


def load_matrix(root: Path) -> dict:
    path = router_root(root) / "printer_matrix.json"
    if not path.is_file():
        raise RuntimeError(f"printer matrix missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    safety = data.get("safety", {})
    if not all(safety.get(k) is False for k in ("printer_network_control", "upload", "start_print", "heating", "motion")):
        raise RuntimeError("printer_matrix safety boundary is not fail-closed")
    return data


def run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def scalar(value, fallback=None):
    if isinstance(value, list):
        value = value[0] if value else fallback
    return fallback if value in (None, "") else value


def bed_size(machine: dict) -> tuple[float, float]:
    area = machine.get("printable_area")
    if not isinstance(area, list) or len(area) < 3:
        raise RuntimeError("native machine profile lacks printable_area")
    pts = []
    for raw in area:
        x, y = str(raw).split("x", 1)
        pts.append((float(x), float(y)))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def native_path(router: Path, value: str) -> Path:
    # printer_matrix.json is shared across Windows and macOS. Normalize either
    # separator style so the same canonical matrix resolves on both hosts.
    normalized = value.replace("\\", "/")
    p = (router / Path(normalized)).resolve()
    try:
        p.relative_to(router.resolve())
    except ValueError as exc:
        raise RuntimeError(f"native profile escapes slicer-router: {value}") from exc
    if not p.is_file():
        raise RuntimeError(f"native profile missing: {p}")
    return p


def make_profiles(root: Path, matrix: dict) -> dict:
    router = router_root(root)
    out_dir = router / "text-to-cad-profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    created = {}
    for key, row in matrix["printers"].items():
        machine_path = native_path(router, row["machine"])
        process_path = native_path(router, row["process"])
        filament_path = native_path(router, row["filament"])
        machine = json.loads(machine_path.read_text(encoding="utf-8"))
        filament = json.loads(filament_path.read_text(encoding="utf-8"))
        width, depth = bed_size(machine)
        height = float(machine["printable_height"])
        wrapper = {
            "backend": "orcaslicer",
            "native_config": str(machine_path),
            "native_settings": [str(machine_path), str(process_path)],
            "native_filaments": [str(filament_path)],
            "machine": {
                "name": row["display_name"],
                "bed_size_mm": [width, depth],
                "z_height_mm": height,
            },
            "filament": {
                "type": str(scalar(filament.get("filament_type"), matrix["defaults"]["material"])),
                "nozzle_temp_c": float(scalar(filament.get("nozzle_temperature"), 0)),
                "bed_temp_c": float(scalar(
                    filament.get("hot_plate_temp"),
                    scalar(filament.get("textured_plate_temp"), 0),
                )),
            },
            "velvetos": {
                "printer_key": key,
                "units": row.get("units", []),
                "production_authority": row.get("production_authority"),
                "source": str(router / "printer_matrix.json"),
                "network_control": False,
                "upload": False,
                "start_print": False,
            },
        }
        dest = out_dir / f"{key}.json"
        dest.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created[key] = str(dest)
    return created


def _orca_version(path: Path) -> tuple[tuple[int, ...], str]:
    try:
        cp = subprocess.run(
            [str(path), "--version"], text=True, capture_output=True,
            timeout=10, check=False,
        )
        line = (cp.stdout.splitlines() or cp.stderr.splitlines() or [""])[0].strip()
    except Exception:
        return (), ""
    match = re.search(r"(\d+(?:\.\d+)+)", line)
    if match and "invalid option" not in line.casefold():
        version = tuple(int(part) for part in match.group(1).split("."))
        return version, line
    path_match = re.search(r"(\d+(?:\.\d+)+)", path.parent.name)
    if path_match:
        value = path_match.group(1)
        return tuple(int(part) for part in value.split(".")), f"{value} (from install path)"
    return (), line


def discover_orca(root: Path, matrix: dict) -> dict:
    """Discover the installed OrcaSlicer dynamically; matrix path is only a hint."""
    candidates: list[Path] = []
    if os.environ.get("ORCASLICER_BIN"):
        candidates.append(Path(os.environ["ORCASLICER_BIN"]))
    configured = ((matrix.get("slicer_engine") or {}).get("executable") or "").strip()
    if configured:
        candidates.append(Path(configured))
    for name in ("orca-slicer", "OrcaSlicer", "orca-slicer.exe", "OrcaSlicer.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    tools = root / "tools"
    if tools.is_dir():
        candidates.extend(tools.glob("OrcaSlicer*\\orca-slicer.exe"))
        candidates.extend(tools.glob("OrcaSlicer*\\OrcaSlicer.exe"))
    if os.name == "nt":
        for base in (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs",
        ):
            candidates.extend(base.glob("OrcaSlicer*\\orca-slicer.exe"))
            candidates.extend(base.glob("OrcaSlicer*\\OrcaSlicer.exe"))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()
            key = str(resolved).casefold()
            if key not in seen:
                seen.add(key)
                unique.append(resolved)
    if not unique:
        raise RuntimeError("No usable OrcaSlicer installation was discovered")

    ranked = []
    for candidate in unique:
        version_key, display = _orca_version(candidate)
        ranked.append((version_key, candidate.stat().st_mtime, candidate, display))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, selected, display = ranked[0]
    return {
        "path": str(selected),
        "observed_version": display or None,
        "configured_hint": configured or None,
        "candidates": [str(item[2]) for item in ranked],
    }


def discover_prusa() -> str | None:
    """Discover a local PrusaSlicer CLI without changing backend preference order."""
    candidates: list[Path] = []
    configured = os.environ.get("PRUSASLICER_BIN", "").strip()
    if configured:
        candidates.append(Path(configured))
    for name in ("prusa-slicer", "PrusaSlicer", "prusa-slicer-console", "prusa-slicer-console.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        local_programs = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs"
        candidates.extend([
            program_files / "Prusa3D" / "PrusaSlicer" / "prusa-slicer-console.exe",
            program_files / "Prusa3D" / "PrusaSlicer" / "prusa-slicer.exe",
            program_files_x86 / "Prusa3D" / "PrusaSlicer" / "prusa-slicer-console.exe",
            local_programs / "PrusaSlicer" / "prusa-slicer-console.exe",
        ])
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def tool_env(root: Path, matrix: dict) -> dict:
    env = os.environ.copy()
    slicer = discover_orca(root, matrix)
    env["ORCASLICER_BIN"] = slicer["path"]
    prusa = discover_prusa()
    if prusa:
        env["PRUSASLICER_BIN"] = prusa
    return env


def doctor(_: argparse.Namespace) -> int:
    root = printlab_root()
    repo = text2cad_root(root)
    py = venv_python(repo)
    matrix = load_matrix(root)
    errors = []
    if not repo.is_dir():
        errors.append(f"text-to-cad repo missing: {repo}")
    if not py.is_file():
        errors.append(f"text-to-cad venv missing: {py}")
    if errors:
        print(json.dumps({"status": "BLOCKED", "errors": errors}, indent=2))
        return 2
    cad = run([str(py), "-m", "cadgen.cli", "doctor", str(repo / "skills" / "cad")], cwd=repo)
    gcode = run([str(py), str(repo / "skills" / "gcode" / "scripts" / "gcode_tool.py"), "discover"],
                cwd=repo, env=tool_env(root, matrix))
    slicer = discover_orca(root, matrix)
    profiles = make_profiles(root, matrix)
    ok = cad.returncode == 0 and gcode.returncode == 0 and '"available": true' in gcode.stdout
    result = {
        "status": "PASS" if ok else "BLOCKED",
        "text_to_cad_root": str(repo),
        "python": str(py),
        "upstream_commit": run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip(),
        "cadgen_doctor": {"returncode": cad.returncode, "stdout": cad.stdout.strip(), "stderr": cad.stderr.strip()},
        "gcode_discover": {"returncode": gcode.returncode, "stdout": gcode.stdout.strip(), "stderr": gcode.stderr.strip()},
        "slicer": slicer,
        "profiles": profiles,
        "safety": matrix["safety"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def profiles_cmd(_: argparse.Namespace) -> int:
    root = printlab_root()
    matrix = load_matrix(root)
    print(json.dumps({"status": "PASS", "profiles": make_profiles(root, matrix)}, indent=2))
    return 0


def dfam_cmd(args: argparse.Namespace) -> int:
    root = printlab_root()
    repo = text2cad_root(root)
    py = venv_python(repo)
    tool = repo / "skills" / "dfam-check" / "scripts" / "dfam_tool.py"
    cmd = [str(py), str(tool), "measure", str(Path(args.input).resolve()), "--angle-limit", str(args.angle_limit)]
    proc = run(cmd, cwd=repo)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def slice_cmd(args: argparse.Namespace) -> int:
    root = printlab_root()
    repo = text2cad_root(root)
    py = venv_python(repo)
    matrix = load_matrix(root)
    wrappers = make_profiles(root, matrix)
    if args.printer not in wrappers:
        raise RuntimeError(f"unknown printer key: {args.printer}")
    tool = repo / "skills" / "gcode" / "scripts" / "gcode_tool.py"
    output = Path(args.output).resolve()
    cmd = [
        str(py), str(tool), "slice",
        "--input", str(Path(args.input).resolve()),
        "--output", str(output),
        "--profile", wrappers[args.printer],
        "--backend", "orcaslicer",
        "--execute" if args.execute else "--dry-run",
    ]
    proc = run(cmd, cwd=repo, env=tool_env(root, matrix))
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0 or not args.execute:
        return proc.returncode
    val = run([
        str(py), str(tool), "validate",
        "--gcode", str(output),
        "--profile", wrappers[args.printer],
        "--json",
    ], cwd=repo, env=tool_env(root, matrix))
    sys.stdout.write(val.stdout)
    sys.stderr.write(val.stderr)
    return val.returncode


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("profiles")
    dfam = sub.add_parser("dfam")
    dfam.add_argument("--input", required=True)
    dfam.add_argument("--angle-limit", type=float, default=45.0)
    sl = sub.add_parser("slice")
    sl.add_argument("--input", required=True)
    sl.add_argument("--printer", required=True, choices=["h2d", "u1", "ecc2", "c5", "c5pro"])
    sl.add_argument("--output", required=True)
    sl.add_argument("--execute", action="store_true", help="Run local slicing; never uploads or starts a printer")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "doctor":
            return doctor(args)
        if args.command == "profiles":
            return profiles_cmd(args)
        if args.command == "dfam":
            return dfam_cmd(args)
        if args.command == "slice":
            return slice_cmd(args)
        raise RuntimeError("unsupported command")
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
