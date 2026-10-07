#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfprod" / "CAD-ENGINE-REGISTRY.json"
MAX_REPAIRS = 2


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def contract(_: argparse.Namespace) -> int:
    registry = load_json(REGISTRY)
    patterns = load_json(ROOT / registry["exact_cad_patterns"])
    return emit({
        "status": "PASS",
        "schema": registry["schema"],
        "max_repair_iterations": registry["max_repair_iterations"],
        "exact_cad_patterns": registry["exact_cad_patterns"],
        "mechanical_feature_packs": registry["mechanical_feature_packs"],
        "coordinate_frame": patterns["coordinate_frame"]["primitive_local_origin"],
        "engines": registry["engines"],
    })


def _positive_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _vector3(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    )


def validate_ir(data: dict) -> str | None:
    if data.get("schema") != "velvetos.geometry-ir.v1" or data.get("units") != "mm":
        return "schema_or_units"
    parts = data.get("parts")
    constraints = data.get("constraints")
    if not isinstance(parts, list) or not parts or not isinstance(constraints, list):
        return "parts_or_constraints"

    ids: list[str] = []
    allowed = {"box", "cylinder", "extrusion", "imported_step", "assembly"}
    for part in parts:
        if (
            not isinstance(part, dict)
            or not isinstance(part.get("id"), str)
            or not part["id"]
            or part.get("kind") not in allowed
        ):
            return "invalid_part"
        if not isinstance(part.get("dimensions"), dict) or not part["dimensions"]:
            return "dimensions_required"
        for value in part["dimensions"].values():
            if not _positive_number(value):
                return "positive_numeric_dimensions_required"
        if part.get("operation", "add") not in {"add", "cut"}:
            return "invalid_operation"
        if "translate_mm" in part and not _vector3(part["translate_mm"]):
            return "invalid_translate_mm"
        ids.append(part["id"])

    if len(ids) != len(set(ids)):
        return "duplicate_part_id"

    known = set(ids)
    for constraint in constraints:
        if (
            not isinstance(constraint, dict)
            or constraint.get("a") not in known
            or constraint.get("b") not in known
        ):
            return "constraint_ref_unknown"
        if constraint.get("type") not in {"align", "offset", "mate", "clearance", "contains"}:
            return "constraint_type"
        value = constraint.get("value_mm")
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            return "constraint_value"
    return None


def _buildability_error(data: dict) -> str | None:
    required = {
        "box": {"x", "y", "z"},
        "cylinder": {"diameter", "height"},
    }
    for index, part in enumerate(data["parts"]):
        kind = part["kind"]
        if kind not in required:
            return f"unsupported_build_kind:{kind}"
        if not required[kind].issubset(part["dimensions"]):
            return f"missing_dimensions:{part['id']}"
        if index == 0 and part.get("operation", "add") == "cut":
            return "first_part_cannot_be_cut"
    return None


def ir_validate(args: argparse.Namespace) -> int:
    data = load_json(args.input)
    error = validate_ir(data)
    return emit(
        {
            "status": "BLOCKED" if error else "PASS",
            "reason": error,
            "parts": len(data.get("parts", [])),
        },
        2 if error else 0,
    )


def repair_next(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = (
        {"schema": "velvetos.cad-repair-state.v1", "attempts": 0, "failures": []}
        if not path.exists()
        else load_json(path)
    )
    state["failures"].append(args.failure)
    if state["attempts"] < MAX_REPAIRS:
        state["attempts"] += 1
        decision = "REPAIR_ALLOWED"
    else:
        decision = "FALLBACK_REQUIRED"
    state["decision"] = decision
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return emit(
        {
            "status": "PASS",
            "decision": decision,
            "attempts": state["attempts"],
            "max": MAX_REPAIRS,
        }
    )


def stack_root() -> Path:
    base = Path(
        os.environ.get(
            "VELVET_PRINTLAB_ROOT",
            Path.home() / "Documents" / "VelvetPrintLab",
        )
    )
    return (base / "tools" / "cad-stack").resolve()


def text_to_cad_root() -> Path:
    return Path(
        os.environ.get(
            "TEXT_TO_CAD_ROOT",
            Path.home() / "Documents" / "VelvetPrintLab" / "tools" / "text-to-cad",
        )
    ).resolve()


def _python_in(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def runtime_paths() -> dict[str, Path]:
    root = stack_root()
    return {
        "build123d": _python_in(text_to_cad_root() / ".venv"),
        "cadquery": _python_in(root / "cadquery" / ".venv"),
        "jscad": Path(shutil.which("node") or ""),
    }


def _engine_runtime_version(engine: str) -> str:
    if engine in {"build123d", "cadquery"}:
        runtime = runtime_paths()[engine]
        proc = subprocess.run(
            [
                str(runtime),
                "-c",
                (
                    "import importlib.metadata as m;"
                    f"print(m.version({engine!r}))"
                ),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            raise RuntimeError(f"version probe failed for {engine}: {proc.stderr[-500:]}")
        return proc.stdout.strip().splitlines()[-1]

    if engine == "jscad":
        root = stack_root() / "jscad" / "node_modules" / "@jscad"
        versions = []
        for package in ("modeling", "stl-serializer"):
            payload = load_json(root / package / "package.json")
            versions.append(f"{payload['name']} {payload['version']}")
        return " + ".join(versions)

    raise RuntimeError(f"unsupported engine version probe: {engine}")


def doctor(_: argparse.Namespace) -> int:
    registry = load_json(REGISTRY)
    root = stack_root()
    runtimes = runtime_paths()
    checks = {
        "build123d": runtimes["build123d"].is_file(),
        "cadquery": runtimes["cadquery"].is_file(),
        "jscad": bool(str(runtimes["jscad"])) and runtimes["jscad"].is_file(),
        "cad-cae-copilot": (root / "pilots" / "cad-cae-copilot" / ".git").exists(),
        "forgent3d": (root / "pilots" / "forgent3d-desktop" / ".git").exists(),
    }
    status = "PASS" if all(checks[name] for name in ("build123d", "cadquery", "jscad")) else "BLOCKED"
    return emit(
        {
            "status": status,
            "stack_root": str(root),
            "engines": checks,
            "pilots_required_for_pass": False,
            "registry_schema": registry["schema"],
        },
        0 if status == "PASS" else 2,
    )


ENGINE_FORMATS = {
    "build123d": {
        "step": "model.step",
        "stl": "model.stl",
        "3mf": "model.3mf",
        "glb": "model.glb",
        "dxf": "model-top.dxf",
        "svg": "model-top.svg",
    },
    "cadquery": {
        "step": "model.step",
        "stl": "model.stl",
    },
    "jscad": {
        "stl": "model.stl",
    },
}
DEFAULT_ENGINE_FORMATS = {
    "build123d": ["step", "stl"],
    "cadquery": ["step", "stl"],
    "jscad": ["stl"],
}


def _requested_formats(engine: str, raw: str | None) -> tuple[list[str] | None, str | None]:
    if not raw:
        return list(DEFAULT_ENGINE_FORMATS[engine]), None
    requested: list[str] = []
    for value in raw.split(","):
        normalized = value.strip().lower()
        if not normalized or normalized in requested:
            continue
        requested.append(normalized)
    if not requested:
        return None, "formats_empty"
    unsupported = [name for name in requested if name not in ENGINE_FORMATS[engine]]
    if unsupported:
        return None, f"unsupported_formats:{engine}:{','.join(unsupported)}"
    return requested, None


def _engine_artifacts(engine: str, formats: list[str] | None = None) -> list[str]:
    selected = formats or DEFAULT_ENGINE_FORMATS[engine]
    return [ENGINE_FORMATS[engine][name] for name in selected]


def _select_engine(requested: str, plan_only: bool) -> tuple[str | None, str | None]:
    if requested != "auto":
        if requested not in {"build123d", "cadquery", "jscad"}:
            return None, "unsupported_engine"
        if plan_only:
            return requested, None
        runtime = runtime_paths()[requested]
        if requested == "jscad":
            ok = bool(str(runtime)) and runtime.is_file()
        else:
            ok = runtime.is_file()
        return (requested, None) if ok else (None, f"engine_unavailable:{requested}")

    if plan_only:
        return "build123d", None

    runtimes = runtime_paths()
    for name in ("build123d", "cadquery", "jscad"):
        runtime = runtimes[name]
        if name == "jscad":
            if bool(str(runtime)) and runtime.is_file():
                return name, None
        elif runtime.is_file():
            return name, None
    return None, "no_local_engine_available"


def _build123d_driver() -> str:
    return """from pathlib import Path
import json, sys
from build123d import (
    Align,
    Box,
    Cylinder,
    ExportDXF,
    ExportSVG,
    Location,
    Mesher,
    export_gltf,
    export_step,
    export_stl,
)

data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
out=Path(sys.argv[2])
formats=set(json.loads(sys.argv[3]))
solid=None
for part in data['parts']:
    dims=part['dimensions']
    if part['kind']=='box':
        obj=Box(
            dims['x'],dims['y'],dims['z'],
            align=(Align.CENTER,Align.CENTER,Align.MIN),
        )
    elif part['kind']=='cylinder':
        obj=Cylinder(
            dims['diameter']/2,dims['height'],
            align=(Align.CENTER,Align.CENTER,Align.MIN),
        )
    else:
        raise ValueError('unsupported kind: '+part['kind'])
    obj=obj.move(Location(tuple(part.get('translate_mm',[0,0,0]))))
    op=part.get('operation','add')
    if solid is None:
        if op=='cut':
            raise ValueError('first part cannot be cut')
        solid=obj
    elif op=='add':
        solid=solid+obj
    else:
        solid=solid-obj

if 'step' in formats:
    export_step(solid,out/'model.step')
if 'stl' in formats:
    export_stl(solid,out/'model.stl')
if '3mf' in formats:
    mesher=Mesher()
    mesher.add_shape(solid)
    mesher.write(out/'model.3mf')
if 'glb' in formats:
    ok=export_gltf(solid,out/'model.glb',binary=True)
    if ok is False:
        raise RuntimeError('glb export failed')
if 'dxf' in formats or 'svg' in formats:
    top_face=max(solid.faces(),key=lambda face: face.center().Z)
    if 'dxf' in formats:
        exporter=ExportDXF()
        exporter.add_shape(top_face)
        exporter.write(out/'model-top.dxf')
    if 'svg' in formats:
        exporter=ExportSVG()
        exporter.add_shape(top_face)
        exporter.write(out/'model-top.svg')
"""


def _cadquery_driver() -> str:
    return """from pathlib import Path
import json, sys
import cadquery as cq
from cadquery import exporters

data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
out=Path(sys.argv[2])
solid=None
for part in data['parts']:
    dims=part['dimensions']
    if part['kind']=='box':
        obj=cq.Workplane('XY').box(
            dims['x'],dims['y'],dims['z'],
            centered=(True,True,False),
        )
    elif part['kind']=='cylinder':
        obj=cq.Workplane('XY').circle(dims['diameter']/2).extrude(dims['height'])
    else:
        raise ValueError('unsupported kind: '+part['kind'])
    obj=obj.translate(tuple(part.get('translate_mm',[0,0,0])))
    op=part.get('operation','add')
    if solid is None:
        if op=='cut':
            raise ValueError('first part cannot be cut')
        solid=obj
    elif op=='add':
        solid=solid.union(obj)
    else:
        solid=solid.cut(obj)
exporters.export(solid,str(out/'model.step'))
exporters.export(solid,str(out/'model.stl'))
"""


def _jscad_driver() -> str:
    return """import fs from 'node:fs';
import modeling from '@jscad/modeling';
import serializer from '@jscad/stl-serializer';

const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const outDir=process.argv[3];
const {cuboid,cylinder}=modeling.primitives;
const {translate}=modeling.transforms;
const {union,subtract}=modeling.booleans;
let solid=null;
for (const part of data.parts) {
  const d=part.dimensions;
  let obj;
  let localOffset;
  if (part.kind==='box') {
    obj=cuboid({size:[d.x,d.y,d.z]});
    localOffset=[0,0,d.z/2];
  } else if (part.kind==='cylinder') {
    obj=cylinder({radius:d.diameter/2,height:d.height,segments:64});
    localOffset=[0,0,d.height/2];
  } else throw new Error('unsupported kind: '+part.kind);
  obj=translate(localOffset,obj);
  obj=translate(part.translate_mm || [0,0,0],obj);
  const op=part.operation || 'add';
  if (solid===null) {
    if (op==='cut') throw new Error('first part cannot be cut');
    solid=obj;
  } else if (op==='add') solid=union(solid,obj);
  else solid=subtract(solid,obj);
}
const chunks=serializer.serialize({binary:true},solid);
const bytes=Buffer.concat(chunks.map(x=>Buffer.from(x)));
fs.writeFileSync(outDir+'/model.stl',bytes);
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(args: argparse.Namespace) -> int:
    source = Path(args.input).resolve()
    data = load_json(source)
    error = validate_ir(data) or _buildability_error(data)
    if error:
        return emit({"status": "BLOCKED", "reason": error}, 2)

    engine, engine_error = _select_engine(args.engine, args.plan_only)
    if engine_error or engine is None:
        return emit({"status": "BLOCKED", "reason": engine_error}, 2)

    formats, formats_error = _requested_formats(engine, args.formats)
    if formats_error or formats is None:
        return emit({"status": "BLOCKED", "reason": formats_error, "engine": engine}, 2)

    artifacts = _engine_artifacts(engine, formats)
    engine_version = None
    if not args.plan_only:
        try:
            engine_version = _engine_runtime_version(engine)
        except Exception as exc:
            return emit(
                {
                    "status": "BLOCKED",
                    "reason": f"engine_version_unavailable:{exc}",
                    "engine": engine,
                },
                2,
            )

    out_dir = Path(args.out_dir).resolve()
    plan = {
        "status": "PASS",
        "engine": engine,
        "engine_version": engine_version,
        "coordinate_frame": "xy_center_z_min",
        "formats": formats,
        "plan_only": bool(args.plan_only),
        "input": str(source),
        "input_sha256": _sha256(source),
        "profile_refs": [
            "packages/vfprod/CAD-ENGINE-REGISTRY.json",
            "packages/vfprod/EXACT-CAD-PATTERNS.json",
        ],
        "out_dir": str(out_dir),
        "artifacts": artifacts,
        "parts": len(data["parts"]),
        "printer_actions_allowed": False,
    }
    if args.plan_only:
        return emit(plan)

    out_dir.mkdir(parents=True, exist_ok=True)
    normalized = out_dir / "model-ir.json"
    normalized.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    driver = out_dir / ("_driver.mjs" if engine == "jscad" else "_driver.py")
    if engine == "build123d":
        driver.write_text(_build123d_driver(), encoding="utf-8")
        command = [
            str(runtime_paths()[engine]),
            str(driver),
            str(normalized),
            str(out_dir),
            json.dumps(formats),
        ]
        cwd = ROOT
    elif engine == "cadquery":
        driver.write_text(_cadquery_driver(), encoding="utf-8")
        command = [str(runtime_paths()[engine]), str(driver), str(normalized), str(out_dir)]
        cwd = ROOT
    else:
        jscad_root = stack_root() / "jscad"
        driver = jscad_root / "_velvetos_build_driver.mjs"
        driver.write_text(_jscad_driver(), encoding="utf-8")
        command = [str(runtime_paths()[engine]), str(driver), str(normalized), str(out_dir)]
        cwd = jscad_root

    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180,
        )
    except Exception as exc:
        return emit({"status": "BLOCKED", "reason": f"engine_exec_error:{exc}", "engine": engine}, 2)
    finally:
        try:
            driver.unlink()
        except OSError:
            pass

    if proc.returncode != 0:
        return emit(
            {
                "status": "BLOCKED",
                "reason": "engine_failed",
                "engine": engine,
                "returncode": proc.returncode,
                "stdout": proc.stdout[-2000:],
                "stderr": proc.stderr[-2000:],
            },
            2,
        )

    evidence = []
    for name in artifacts:
        path = out_dir / name
        if not path.is_file() or path.stat().st_size <= 0:
            return emit({"status": "BLOCKED", "reason": f"artifact_missing:{name}", "engine": engine}, 2)
        evidence.append({
            "name": name,
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })

    receipt = {
        **plan,
        "plan_only": False,
        "status": "PASS",
        "normalized_ir": str(normalized),
        "normalized_ir_sha256": _sha256(normalized),
        "artifact_evidence": evidence,
    }
    receipt_path = out_dir / "build-receipt.json"
    receipt["receipt"] = str(receipt_path)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return emit(receipt)


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd", required=True)
    subs.add_parser("contract")
    subs.add_parser("doctor")

    command = subs.add_parser("ir-validate")
    command.add_argument("--input", required=True)

    command = subs.add_parser("build")
    command.add_argument("--input", required=True)
    command.add_argument("--engine", default="auto", choices=["auto", "build123d", "cadquery", "jscad"])
    command.add_argument("--formats", help="comma-separated export formats; defaults preserve existing engine behavior")
    command.add_argument("--out-dir", required=True)
    command.add_argument("--plan-only", action="store_true")

    command = subs.add_parser("repair-next")
    command.add_argument("--state", required=True)
    command.add_argument("--failure", required=True)
    return parser


def main() -> int:
    args = parser().parse_args()
    if args.cmd == "contract":
        return contract(args)
    if args.cmd == "doctor":
        return doctor(args)
    if args.cmd == "ir-validate":
        return ir_validate(args)
    if args.cmd == "build":
        return build(args)
    if args.cmd == "repair-next":
        return repair_next(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
