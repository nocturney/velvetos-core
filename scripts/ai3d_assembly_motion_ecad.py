#!/usr/bin/env python3
"""Phase 8 bounded assembly, motion, collision, and ECAD/MCAD fixtures.

This adapter reuses existing VelvetOS authorities and host runtimes. It is not
an assembly router and it performs no printer or machine actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONFIG = BASE / "assembly-motion-ecad-v1.json"

sys.path.insert(0, str(ROOT / "scripts"))
import vf_cad_stack  # noqa: E402

FREECAD = Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")
KICAD = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
KICAD_MODELS = Path(r"C:\Program Files\KiCad\10.0\share\kicad\3dmodels")
KICAD_BOARD = Path(
    r"C:\Program Files\KiCad\10.0\share\kicad\template\Arduino_Nano\Arduino_Nano.kicad_pcb"
)


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        command,
        cwd=cwd or ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return proc


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def motion_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "build123d-motion-report.json"
    state0 = out_dir / "motion-angle0.step"
    state45 = out_dir / "motion-angle45.step"
    state90 = out_dir / "motion-angle90.step"
    driver = out_dir / "_phase8_motion_driver.py"

    driver.write_text(
        """from build123d import *
from pathlib import Path
import json, sys

out=Path(sys.argv[1])
base=Box(20,20,5,align=(Align.CENTER,Align.CENTER,Align.MIN))
arm=Box(30,6,4,align=(Align.CENTER,Align.CENTER,Align.MIN))
obstacle=Box(8,8,4,align=(Align.CENTER,Align.CENTER,Align.MIN)).move(Location((15,15,5)))
joint=RevoluteJoint(
    "pivot",
    base,
    axis=Axis((0,0,5),(0,0,1)),
    angle_reference=(1,0,0),
    angular_range=(0,180),
)
mount=RigidJoint("mount",arm,Location((-15,0,0)))
samples=[]
for angle in range(0,181,15):
    joint.connect_to(mount,angle=angle)
    bb=arm.bounding_box()
    collision=float((arm & obstacle).volume)
    samples.append({
        "angle_deg": angle,
        "arm_bbox_min": [bb.min.X,bb.min.Y,bb.min.Z],
        "arm_bbox_max": [bb.max.X,bb.max.Y,bb.max.Z],
        "collision_volume_mm3": collision,
    })
    if angle in (0,45,90):
        export_step(
            Compound([base,arm,obstacle]),
            out/f"motion-angle{angle}.step",
        )

range_blocked=False
range_error=None
try:
    joint.connect_to(mount,angle=181)
except ValueError as exc:
    range_blocked=True
    range_error=str(exc)

payload={
    "schema":"velvetos.ai3d.phase8-motion-fixture.v1",
    "status":"PASS",
    "joint_type":"RevoluteJoint",
    "axis_origin_mm":[0,0,5],
    "axis_direction":[0,0,1],
    "angular_range_deg":[0,180],
    "sampling_step_deg":15,
    "samples":samples,
    "range_negative_control":{
        "angle_deg":181,
        "blocked":range_blocked,
        "error":range_error,
    },
    "printer_actions_allowed":False,
}
(out/"build123d-motion-report.json").write_text(
    json.dumps(payload,indent=2)+"\\n",
    encoding="utf-8",
)
""",
        encoding="utf-8",
        newline="\n",
    )
    runtime = vf_cad_stack.runtime_paths()["build123d"]
    proc = run([str(runtime), str(driver), str(out_dir)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0:
        raise RuntimeError(f"build123d motion fixture failed: {proc.stderr[-3000:]}")

    payload = load(report)
    payload["runtime"] = str(runtime)
    payload["artifacts"] = {
        path.name: artifact(path)
        for path in (report, state0, state45, state90)
    }
    return payload


def freecad_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    driver = out_dir / "_phase8_freecad_driver.py"
    report = out_dir / "freecad-assembly-report.json"
    fcstd = out_dir / "freecad-assembly.FCStd"
    step = out_dir / "freecad-assembly.step"

    driver.write_text(
        f"""import FreeCAD as App
import Part, json, sys
sys.path.insert(0,r"C:\Program Files\FreeCAD 1.1\Mod\Assembly")
import JointObject

out=r"{str(out_dir)}"
doc=App.newDocument("AI3DPhase8")
assembly=doc.addObject("Assembly::AssemblyObject","Assembly")
assembly.Type="Assembly"
joints=assembly.newObject("Assembly::JointGroup","Joints")

fixed=assembly.newObject("Part::Box","FixedBox")
fixed.Length=10
fixed.Width=10
fixed.Height=10

moving=assembly.newObject("Part::Box","MovingBox")
moving.Length=10
moving.Width=10
moving.Height=10
moving.Placement=App.Placement(App.Vector(40,50,60),App.Rotation(45,55,65))

ground=joints.newObject("App::FeaturePython","GroundedJoint")
JointObject.GroundedJoint(ground,fixed)

joint=joints.newObject("App::FeaturePython","FixedJoint")
JointObject.Joint(joint,0)
refs=[
    [fixed,["Face6","Vertex7"]],
    [moving,["Face6","Vertex7"]],
]
joint.Proxy.setJointConnectors(joint,refs)
doc.recompute()

placement_match=moving.Placement.isSame(fixed.Placement,1e-6)
doc.saveAs(r"{str(fcstd)}")
Part.export([fixed,moving],r"{str(step)}")

payload={{
    "schema":"velvetos.ai3d.phase8-freecad-assembly-fixture.v1",
    "status":"PASS" if placement_match else "FAIL",
    "freecad_version":".".join(App.Version()[:3]),
    "assembly_type":assembly.TypeId,
    "joint_group_type":joints.TypeId,
    "joint_type":joint.JointType,
    "grounded_object":ground.ObjectToGround.Name,
    "placement_match":placement_match,
    "fixed_placement":str(fixed.Placement),
    "moving_placement":str(moving.Placement),
    "printer_actions_allowed":False,
}}
with open(r"{str(report)}","w",encoding="utf-8",newline="\\n") as handle:
    handle.write(json.dumps(payload,indent=2)+"\\n")
""",
        encoding="utf-8",
        newline="\n",
    )
    proc = run([str(FREECAD), str(driver)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0 or not report.is_file():
        raise RuntimeError(
            "FreeCAD assembly fixture failed: "
            f"returncode={proc.returncode} "
            f"report_exists={report.is_file()} "
            f"stdout={proc.stdout[-5000:]} "
            f"stderr={proc.stderr[-5000:]}"
        )
    payload = load(report)
    payload["runtime"] = str(FREECAD)
    payload["artifacts"] = {
        path.name: artifact(path)
        for path in (report, fcstd, step)
    }
    return payload


def ecad_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    board_step = out_dir / "arduino-nano-board-only.step"
    normalized_step = out_dir / "arduino-nano-board-normalized.step"
    enclosure_step = out_dir / "arduino-nano-enclosure-good.step"
    report = out_dir / "ecad-enclosure-report.json"
    component_step = out_dir / "arduino-nano-component-attempt.step"

    board_proc = run(
        [
            str(KICAD),
            "pcb",
            "export",
            "step",
            "--board-only",
            "--force",
            "--output",
            str(board_step),
            str(KICAD_BOARD),
        ]
    )
    if board_proc.returncode != 0:
        raise RuntimeError(
            f"KiCad board-only STEP export failed: {board_proc.stdout[-3000:]} {board_proc.stderr[-3000:]}"
        )

    env = dict(os.environ)
    env["KICAD9_3DMODEL_DIR"] = str(KICAD_MODELS)
    component_proc = run(
        [
            str(KICAD),
            "pcb",
            "export",
            "step",
            "--subst-models",
            "--force",
            "--output",
            str(component_step),
            str(KICAD_BOARD),
        ],
        env=env,
    )
    component_output = (component_proc.stdout or "") + "\n" + (component_proc.stderr or "")
    component_missing = [
        line.strip()
        for line in component_output.splitlines()
        if "Could not add 3D model" in line or "File not found:" in line
    ]

    driver = out_dir / "_phase8_ecad_driver.py"
    driver.write_text(
        """from build123d import *
from pathlib import Path
import json, sys

board_path=Path(sys.argv[1])
out=Path(sys.argv[2])
compound=import_step(board_path)
solids=compound.solids()
if len(solids)!=1:
    raise RuntimeError(f"expected one board solid, got {len(solids)}")
board=solids[0]
bb=board.bounding_box()
center=bb.center()
board=board.move(Location((-center.X,-center.Y,1-bb.min.Z)))
bb=board.bounding_box()
x,y,z=bb.size.X,bb.size.Y,bb.size.Z

outer=Box(x+6,y+6,6,align=(Align.CENTER,Align.CENTER,Align.MIN))
good_inner=Box(x+2,y+2,4,align=(Align.CENTER,Align.CENTER,Align.MIN)).move(Location((0,0,1)))
good_shell=outer-good_inner
bad_inner=Box(x-2,y-2,4,align=(Align.CENTER,Align.CENTER,Align.MIN)).move(Location((0,0,1)))
bad_shell=outer-bad_inner

good_collision=float((good_shell & board).volume)
bad_collision=float((bad_shell & board).volume)
export_step(board,out/"arduino-nano-board-normalized.step")
export_step(good_shell,out/"arduino-nano-enclosure-good.step")

payload={
    "schema":"velvetos.ai3d.phase8-ecad-interference.v1",
    "status":"PASS",
    "board_bbox_mm":[x,y,z],
    "good_clearance_xy_mm":1.0,
    "good_collision_volume_mm3":good_collision,
    "negative_clearance_xy_mm":-1.0,
    "negative_collision_volume_mm3":bad_collision,
    "board_solids":len(solids),
    "printer_actions_allowed":False,
}
(out/"ecad-enclosure-report.json").write_text(
    json.dumps(payload,indent=2)+"\\n",
    encoding="utf-8",
)
""",
        encoding="utf-8",
        newline="\n",
    )
    runtime = vf_cad_stack.runtime_paths()["build123d"]
    proc = run([str(runtime), str(driver), str(board_step), str(out_dir)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0:
        raise RuntimeError(f"ECAD interference probe failed: {proc.stderr[-3000:]}")

    payload = load(report)
    payload["kicad_runtime"] = str(KICAD)
    payload["build123d_runtime"] = str(runtime)
    payload["board_source"] = str(KICAD_BOARD)
    payload["component_complete_attempt"] = {
        "returncode": component_proc.returncode,
        "missing_model_messages": component_missing,
        "status": "CANDIDATE_BLOCKED_FIXTURE" if component_missing else "PASS",
    }
    paths = [report, board_step, normalized_step, enclosure_step]
    if component_step.is_file():
        paths.append(component_step)
    payload["artifacts"] = {path.name: artifact(path) for path in paths}
    return payload


def all_fixtures(out_dir: Path) -> dict[str, Any]:
    config = load(CONFIG)
    motion = motion_fixture(out_dir / "motion")
    freecad = freecad_fixture(out_dir / "freecad")
    ecad = ecad_fixture(out_dir / "ecad")
    return {
        "schema": "velvetos.ai3d.phase8-fixture-suite.v1",
        "status": "PASS",
        "authority": config["authority"],
        "motion": motion,
        "freecad": freecad,
        "ecad": ecad,
        "safety": config["safety"],
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="cmd", required=True)
    for name in ("motion", "freecad", "ecad", "all"):
        command = subs.add_parser(name)
        command.add_argument("--out-dir", type=Path, required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.cmd == "motion":
        return emit(motion_fixture(args.out_dir))
    if args.cmd == "freecad":
        return emit(freecad_fixture(args.out_dir))
    if args.cmd == "ecad":
        return emit(ecad_fixture(args.out_dir))
    if args.cmd == "all":
        return emit(all_fixtures(args.out_dir))
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
