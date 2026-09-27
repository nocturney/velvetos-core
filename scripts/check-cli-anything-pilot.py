#!/usr/bin/env python3
"""Validate the scoped CLI-Anything FreeCAD adapter."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything.json"
PATCH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything-freecad-overlay.patch"
ADAPTER = ROOT / "scripts" / "vf_cli_anything.py"
VENV = ROOT / ".local-devtools" / "phase5" / "venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
CLONE = ROOT / ".local-devtools" / "phase5" / "cli-anything"
FREECAD_ROOT = (
    Path.home() / "Documents" / "VelvetPrintLab" / "tools"
    / "FreeCAD_1.1.3-Windows-x86_64-py311"
)
FREECAD_CMD = FREECAD_ROOT / "FreeCADCmd.exe"

GUI_DESELECTS = [
    "cli_anything/freecad/tests/test_full_e2e.py::TestFreeCADBackend::test_preview_capture_bundle",
    "cli_anything/freecad/tests/test_full_e2e.py::TestFreeCADBackend::test_preview_capture_bundle_body_patterns",
    "cli_anything/freecad/tests/test_full_e2e.py::TestCLISubprocess::test_preview_capture_subprocess",
    "cli_anything/freecad/tests/test_full_e2e.py::TestCLISubprocess::test_motion_render_frames_subprocess",
    "cli_anything/freecad/tests/test_full_e2e.py::TestCLISubprocess::test_motion_render_video_subprocess",
    "cli_anything/freecad/tests/test_full_e2e.py::TestCLISubprocess::test_preview_live_poll_auto_refresh",
]
def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def run(args: list[str], *, cwd: Path | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def static_checks() -> dict:
    data = load_json(REGISTRY)
    if data.get("state") != "ACTIVE_SCOPE_LIMITED":
        fail("CLI-Anything state must remain ACTIVE_SCOPE_LIMITED")
    if data["authority"].get("runtime_authority") is not False:
        fail("CLI-Anything gained runtime authority")
    if data["authority"].get("slicer_authority") is not False:
        fail("CLI-Anything gained slicer authority")
    for key in ("printer_network_control", "upload", "start_print", "heating", "motion"):
        if data["safety"].get(key) is not False:
            fail(f"unsafe CLI-Anything capability enabled: {key}")
    if data["safety"].get("incremental_recurring_cost_ils") != 0:
        fail("CLI-Anything recurring cost is not zero")

    for rel in (data["cost_preflight"], data["freecad"]["cost_preflight"]):
        preflight = load_json(ROOT / rel)
        if preflight.get("expected_recurring_cost") != "0 ILS/month incremental":
            fail(f"non-zero Cost Preflight: {rel}")

    patch_text = PATCH.read_text(encoding="utf-8")
    for marker in ("_derived_boolean_ops", "visible_names", "No visible valid shape objects"):
        if marker not in patch_text:
            fail(f"overlay missing marker: {marker}")

    adapter_text = ADAPTER.read_text(encoding="utf-8")
    for marker in ('BLOCKED_GROUPS = {"preview", "motion", "repl"}', "FREECAD_PATH"):
        if marker not in adapter_text:
            fail(f"adapter guard missing: {marker}")
    if "start_print(" in adapter_text or "upload_print(" in adapter_text:
        fail("adapter contains printer-control surface")

    three_mf = data["three_mf"]
    if three_mf.get("status") != "BLOCKED_NOT_ROUTABLE":
        fail("3MF harness must remain blocked until its failing tests are repaired")
    return data
def strict_env() -> dict[str, str]:
    env = os.environ.copy()
    scripts = VENV / ("Scripts" if os.name == "nt" else "bin")
    env["PATH"] = os.pathsep.join([str(scripts), str(FREECAD_ROOT), env.get("PATH", "")])
    env["FREECAD_PATH"] = str(FREECAD_CMD)
    env["CLI_ANYTHING_FORCE_INSTALLED"] = "1"
    env["PYTHONUTF8"] = "1"
    return env


def run_upstream_headless_tests() -> None:
    if not VENV_PY.is_file() or not FREECAD_CMD.is_file():
        fail("strict dependencies missing; run setup-cli-anything-pilot.py")
    harness = CLONE / "freecad" / "agent-harness"
    args = [
        str(VENV_PY), "-m", "pytest",
        "cli_anything/freecad/tests",
        "-q", "--disable-warnings", "--tb=short",
    ]
    for node in GUI_DESELECTS:
        args.extend(["--deselect", node])
    proc = run(args, cwd=harness, env=strict_env())
    if proc.returncode or "106 passed, 6 deselected" not in proc.stdout:
        fail(f"upstream headless suite failed:\n{proc.stdout}\n{proc.stderr}")


def adapter_call(args: list[str]) -> dict:
    proc = run([sys.executable, str(ADAPTER), "freecad", "--", *args], cwd=ROOT)
    if proc.returncode:
        fail(f"adapter command failed {args}:\n{proc.stdout}\n{proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"adapter returned non-JSON for {args}: {exc}\n{proc.stdout}")
    raise AssertionError("unreachable")


def real_smoke() -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="vf-cli-anything-") as tmp:
        root = Path(tmp)
        project = root / "project.json"
        stl = root / "part.stl"
        gcode = root / "part-u1.gcode"

        adapter_call(["document", "new", "-n", "VFStrict", "-o", str(project)])
        adapter_call(["-p", str(project), "part", "add", "box", "-n", "Base",
                      "-P", "length=40", "-P", "width=30", "-P", "height=5"])
        adapter_call(["-p", str(project), "part", "add", "cylinder", "-n", "Hole",
                      "-P", "radius=4", "-P", "height=10", "-pos", "20,15,-2.5"])
        adapter_call(["-p", str(project), "part", "boolean", "cut", "0", "1"])
        export = adapter_call([
            "-p", str(project), "export", "render", str(stl),
            "-p", "stl", "--overwrite",
        ])
        if export.get("file_size", 0) <= 0 or not stl.is_file():
            fail("strict STL export missing")
        dfam_proc = run([
            sys.executable, str(ROOT / "scripts" / "vf_cad.py"),
            "dfam", "--input", str(stl), "--angle-limit", "45",
        ], cwd=ROOT)
        if dfam_proc.returncode:
            fail(f"DfAM smoke failed: {dfam_proc.stderr}")
        dfam = json.loads(dfam_proc.stdout)
        mesh = dfam["mesh"]
        if mesh.get("body_count") != 1 or mesh.get("watertight") is not True:
            fail(f"geometry acceptance failed: {mesh}")
        bbox = mesh.get("bbox_mm")
        if not bbox or any(abs(a - b) > 0.05 for a, b in zip(bbox, [40.0, 30.0, 5.0])):
            fail(f"geometry bbox drift: {bbox}")
        if not math.isclose(float(mesh.get("volume_mm3", 0)), 5748.7, abs_tol=1.0):
            fail(f"geometry volume drift: {mesh.get('volume_mm3')}")

        slice_proc = run([
            sys.executable, str(ROOT / "scripts" / "vf_cad.py"),
            "slice", "--input", str(stl), "--printer", "u1", "--output", str(gcode),
        ], cwd=ROOT)
        if slice_proc.returncode:
            fail(f"Orca dry-run failed: {slice_proc.stderr}")
        dry = json.loads(slice_proc.stdout)
        if dry.get("dry_run") is not True or dry.get("profile", {}).get("machine_name") != "Snapmaker U1":
            fail(f"unexpected Orca dry-run receipt: {dry}")
        return dfam, dry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    static_checks()
    if args.strict:
        doctor = run([sys.executable, str(ADAPTER), "doctor"], cwd=ROOT)
        if doctor.returncode:
            fail(f"adapter doctor failed:\n{doctor.stdout}\n{doctor.stderr}")
        payload = json.loads(doctor.stdout)
        if payload.get("status") != "PASS":
            fail(f"adapter doctor not PASS: {payload}")
        run_upstream_headless_tests()
        dfam, dry = real_smoke()
        print(
            "OK cli-anything strict headless_tests=106 geometry_body=1 "
            f"volume_mm3={dfam['mesh']['volume_mm3']} "
            f"orca={dry['profile']['machine_name']} cost=0"
        )
    else:
        print("OK cli-anything offline scope=FREECAD_HEADLESS 3MF=BLOCKED cost=0")


if __name__ == "__main__":
    main()
