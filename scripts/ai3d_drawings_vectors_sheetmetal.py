#!/usr/bin/env python3
"""Phase 9 bounded drawings, vectors, and sheet-metal fixtures.

This adapter reuses existing Fabrication/CAD authorities. It does not route
production work, control machines, install dependencies, or bundle font files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONFIG = BASE / "drawings-vectors-sheetmetal-v1.json"

sys.path.insert(0, str(ROOT / "scripts"))
import vf_cad_stack  # noqa: E402

FREECAD = Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")
TECHDRAW_TEMPLATE = Path(
    r"C:\Program Files\FreeCAD 1.1\data\Mod\TechDraw\Templates\ISO\A4_Landscape_TD.svg"
)
SHEETMETAL = Path(
    r"D:\Velvet\Runtimes\AI3D\phase9-20261007\FreeCAD_SheetMetal-0.8.24"
)
FREECAD_SITE = Path(
    r"D:\Velvet\Runtimes\AI3D\phase9-20261007\freecad-site-packages"
)
DRAFTWRIGHT_PYTHON = Path(
    r"D:\Velvet\Runtimes\AI3D\phase9-20261007\draftwright-eval\Scripts\python.exe"
)


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )


def run_json(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 240,
) -> dict[str, Any]:
    proc = run(command, cwd=cwd, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(command)
            + "\nstdout:\n"
            + proc.stdout[-5000:]
            + "\nstderr:\n"
            + proc.stderr[-5000:]
        )
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(
            f"expected JSON from {' '.join(command)}; stdout={proc.stdout[-5000:]}"
        ) from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def write_driver(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def dxf_probe(path: Path) -> dict[str, Any]:
    runtime = vf_cad_stack.runtime_paths()["build123d"]
    code = """import json,sys
from pathlib import Path
import ezdxf
from ezdxf import bbox
import build123d as b
p=Path(sys.argv[1])
doc=ezdxf.readfile(p)
msp=doc.modelspace()
ext=bbox.extents(msp,fast=False)
shapes=b.import_dxf(p)
compound=b.Compound(shapes)
bb=compound.bounding_box()
print(json.dumps({
    "dxf_version":doc.dxfversion,
    "entity_count":len(msp),
    "entity_types":sorted({e.dxftype() for e in msp}),
    "ezdxf_extmin":[float(v) for v in ext.extmin],
    "ezdxf_extmax":[float(v) for v in ext.extmax],
    "build123d_shape_count":len(shapes),
    "build123d_bbox_size":[bb.size.X,bb.size.Y,bb.size.Z],
    "build123d_bbox_min":[bb.min.X,bb.min.Y,bb.min.Z],
    "build123d_bbox_max":[bb.max.X,bb.max.Y,bb.max.Z],
}))
"""
    return run_json([str(runtime), "-c", code, str(path)])


def techdraw_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    driver = out_dir / "_phase9_techdraw_driver.py"
    report = out_dir / "techdraw-report.json"
    page_dxf = out_dir / "techdraw-page.dxf"
    view_dxf = out_dir / "techdraw-view.dxf"
    svg_fragment = out_dir / "techdraw-view.svgfrag"
    fcstd = out_dir / "techdraw-page.FCStd"

    write_driver(
        driver,
        f"""import FreeCAD as App
import Part, TechDraw, json
from pathlib import Path

out=Path(r"{str(out_dir)}")
doc=App.newDocument("Phase9TechDraw")
obj=doc.addObject("Part::Feature","Fixture")
obj.Shape=Part.makeBox(40,30,10).cut(
    Part.makeCylinder(5,10,App.Vector(20,15,0))
)
page=doc.addObject("TechDraw::DrawPage","Page")
template=doc.addObject("TechDraw::DrawSVGTemplate","Template")
template.Template=r"{str(TECHDRAW_TEMPLATE)}"
page.Template=template
view=doc.addObject("TechDraw::DrawViewPart","TopView")
view.Source=[obj]
view.Direction=(0.0,0.0,1.0)
view.ScaleType="Custom"
view.Scale=2.0
view.X=100.0
view.Y=120.0
page.addView(view)
doc.recompute()

TechDraw.writeDXFPage(page,str(out/"techdraw-page.dxf"))
TechDraw.writeDXFView(view,str(out/"techdraw-view.dxf"))
svg=TechDraw.viewPartAsSvg(view)
(out/"techdraw-view.svgfrag").write_text(svg,encoding="utf-8")
doc.saveAs(str(out/"techdraw-page.FCStd"))

payload={{
    "schema":"velvetos.ai3d.phase9-techdraw-fixture.v1",
    "status":"PASS",
    "freecad_version":".".join(App.Version()[:3]),
    "page_type":page.TypeId,
    "view_type":view.TypeId,
    "template":template.Template,
    "visible_edges":len(view.getVisibleEdges()),
    "scale":float(view.Scale),
    "svg_fragment_bytes":len(svg.encode("utf-8")),
    "printer_actions_allowed":False,
}}
(out/"techdraw-report.json").write_text(
    json.dumps(payload,indent=2),encoding="utf-8"
)
""",
    )
    proc = run([str(FREECAD), str(driver)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0 or not report.is_file():
        raise RuntimeError(
            f"TechDraw fixture failed: returncode={proc.returncode} "
            f"report_exists={report.is_file()} "
            f"stdout={proc.stdout[-4000:]} stderr={proc.stderr[-4000:]}"
        )

    payload = load(report)
    payload["dxf_page_probe"] = dxf_probe(page_dxf)
    payload["dxf_view_probe"] = dxf_probe(view_dxf)
    payload["artifacts"] = {
        path.name: artifact(path)
        for path in (report, page_dxf, view_dxf, svg_fragment, fcstd)
    }
    return payload


def sheetmetal_fixture(
    out_dir: Path,
    *,
    k_factor: float,
    k_factor_standard: str,
) -> dict[str, Any]:
    if not (0.0 < k_factor < 1.0):
        raise ValueError("k_factor must be explicit and between 0 and 1")
    standard = k_factor_standard.lower()
    if standard not in {"ansi", "din"}:
        raise ValueError("k_factor_standard must be ANSI or DIN")

    out_dir.mkdir(parents=True, exist_ok=True)
    driver = out_dir / "_phase9_sheetmetal_driver.py"
    report = out_dir / "sheetmetal-report.json"
    folded_step = out_dir / "sheetmetal-folded.step"
    unfolded_step = out_dir / "sheetmetal-unfolded.step"
    unfolded_dxf = out_dir / "sheetmetal-unfolded.dxf"
    fcstd = out_dir / "sheetmetal-unfold.FCStd"

    write_driver(
        driver,
        f"""import sys, json
from pathlib import Path
sys.path.insert(0,r"{str(FREECAD_SITE)}")
sys.path.insert(0,r"{str(SHEETMETAL)}")
import FreeCAD as App
import Part, TechDraw
import networkx
from SheetMetalBaseShapeCmd import smCreateBaseShape
from SheetMetalNewUnfolder import BendAllowanceCalculator, getUnfold

out=Path(r"{str(out_dir)}")
doc=App.newDocument("Phase9SheetMetal")
shape=smCreateBaseShape(
    "L-Shape",
    1.0,
    1.0,
    30.0,
    60.0,
    20.0,
    5.0,
    True,
    "0,0",
)
folded=doc.addObject("Part::Feature","SheetMetalL")
folded.Shape=shape

candidates=[]
for index,face in enumerate(shape.Faces):
    if face.Surface.TypeId!="Part::GeomPlane":
        continue
    normal=face.normalAt(0,0)
    if normal.z < 0.999999:
        continue
    candidates.append((index+1,float(face.Area),float(face.CenterOfGravity.z)))
if not candidates:
    raise RuntimeError("no +Z planar root face")
max_area=max(row[1] for row in candidates)
selected=[row for row in candidates if abs(row[1]-max_area)<=1e-6]
if len(selected)!=1:
    raise RuntimeError("ambiguous +Z root face selection")
root_face=selected[0][0]

bac=BendAllowanceCalculator.from_single_value({k_factor!r},{standard!r})
selected_face,unfolded,bend_lines,root_normal,bend_info=getUnfold(
    bac,folded,"Face"+str(root_face)
)
unfold_obj=doc.addObject("Part::Feature","Unfolded")
unfold_obj.Shape=unfolded

page=doc.addObject("TechDraw::DrawPage","UnfoldPage")
template=doc.addObject("TechDraw::DrawSVGTemplate","UnfoldTemplate")
template.Template=r"C:\Program Files\FreeCAD 1.1\data\Mod\TechDraw\Templates\ISO\A4_Landscape_blank.svg"
page.Template=template
view=doc.addObject("TechDraw::DrawViewPart","UnfoldView")
view.Source=[unfold_obj]
view.Direction=(0.0,0.0,1.0)
view.ScaleType="Custom"
view.Scale=1.0
view.X=100.0
view.Y=100.0
page.addView(view)
doc.recompute()
TechDraw.writeDXFView(view,str(out/"sheetmetal-unfolded.dxf"))
Part.export([folded],str(out/"sheetmetal-folded.step"))
Part.export([unfold_obj],str(out/"sheetmetal-unfolded.step"))
doc.saveAs(str(out/"sheetmetal-unfold.FCStd"))

bb=unfolded.BoundBox
payload={{
    "schema":"velvetos.ai3d.phase9-sheetmetal-fixture.v1",
    "status":"PASS",
    "freecad_version":".".join(App.Version()[:3]),
    "sheetmetal_version":"0.8.24",
    "networkx_version":networkx.__version__,
    "root_face":"Face"+str(root_face),
    "root_normal":[root_normal.x,root_normal.y,root_normal.z],
    "thickness_mm":1.0,
    "bend_radius_mm":1.0,
    "k_factor":{k_factor!r},
    "k_factor_standard":{standard.upper()!r},
    "unfold_bbox_mm":[bb.XLength,bb.YLength,bb.ZLength],
    "unfold_volume_mm3":float(unfolded.Volume),
    "bend_count":len(bend_info),
    "bend_angles_deg":[float(item.angle) for item in bend_info],
    "bend_radii_mm":[float(item.radius) for item in bend_info],
    "printer_actions_allowed":False,
}}
(out/"sheetmetal-report.json").write_text(
    json.dumps(payload,indent=2),encoding="utf-8"
)
""",
    )
    proc = run([str(FREECAD), str(driver)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0 or not report.is_file():
        raise RuntimeError(
            f"SheetMetal fixture failed: returncode={proc.returncode} "
            f"report_exists={report.is_file()} "
            f"stdout={proc.stdout[-5000:]} stderr={proc.stderr[-5000:]}"
        )

    payload = load(report)
    payload["dxf_probe"] = dxf_probe(unfolded_dxf)
    payload["artifacts"] = {
        path.name: artifact(path)
        for path in (report, folded_step, unfolded_step, unfolded_dxf, fcstd)
    }
    return payload


def text_vector_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    driver = out_dir / "_phase9_text_vector_driver.py"
    report = out_dir / "text-vector-report.json"

    write_driver(
        driver,
        """from build123d import *
from pathlib import Path
import json,sys

out=Path(sys.argv[1])
samples={
    "latin":"VELVET 3D",
    "hebrew":"\u05d5\u05dc\u05d5\u05d5\u05d8 3D",
}
rows={}
for name,text in samples.items():
    shape=Text(text,10,font="Arial")
    bb=shape.bounding_box()
    dxf=out/(name+".dxf")
    svg=out/(name+".svg")
    dx=ExportDXF(unit=Unit.MM)
    dx.add_shape(shape)
    dx.write(dxf)
    sx=ExportSVG(unit=Unit.MM,fill_color=None,line_weight=0.1)
    sx.add_shape(shape)
    sx.write(svg)
    dxf_shapes=import_dxf(dxf)
    svg_shapes=import_svg(svg,align=None)
    db=Compound(dxf_shapes).bounding_box()
    sb=Compound(svg_shapes).bounding_box()
    rows[name]={
        "text":text,
        "font":"Arial",
        "source_bbox_mm":[bb.size.X,bb.size.Y,bb.size.Z],
        "dxf_bbox_mm":[db.size.X,db.size.Y,db.size.Z],
        "svg_bbox_mm":[sb.size.X,sb.size.Y,sb.size.Z],
        "source_faces":len(shape.faces()),
        "dxf_shapes":len(dxf_shapes),
        "svg_shapes":len(svg_shapes),
        "dxf":str(dxf),
        "svg":str(svg),
    }

payload={
    "schema":"velvetos.ai3d.phase9-text-vector-fixture.v1",
    "status":"PASS",
    "samples":rows,
    "font_files_copied":False,
    "printer_actions_allowed":False,
}
(out/"text-vector-report.json").write_text(
    json.dumps(payload,ensure_ascii=True,indent=2),encoding="utf-8"
)
""",
    )
    runtime = vf_cad_stack.runtime_paths()["build123d"]
    proc = run([str(runtime), str(driver), str(out_dir)])
    try:
        driver.unlink()
    except OSError:
        pass
    if proc.returncode != 0 or not report.is_file():
        raise RuntimeError(
            f"text/vector fixture failed: returncode={proc.returncode} "
            f"report_exists={report.is_file()} "
            f"stdout={proc.stdout[-4000:]} stderr={proc.stderr[-4000:]}"
        )

    payload = load(report)
    artifacts: dict[str, Any] = {report.name: artifact(report)}
    for row in payload["samples"].values():
        for key in ("dxf", "svg"):
            path = Path(row[key])
            artifacts[path.name] = artifact(path)
    payload["artifacts"] = artifacts
    return payload


def draftwright_evaluation() -> dict[str, Any]:
    if not DRAFTWRIGHT_PYTHON.is_file():
        return {
            "status": "CANDIDATE_ISOLATED_EVAL",
            "installed": False,
            "reason": "isolated evaluation runtime is not installed",
        }
    code = """import importlib.metadata as m,json
import draftwright
d=m.metadata("draftwright")
raw_license=d.get("License-Expression") or d.get("License") or ""
license_id=(
    "AGPL-3.0"
    if "GNU AFFERO GENERAL PUBLIC LICENSE" in raw_license
    and "Version 3" in raw_license
    else raw_license[:160]
)
print(json.dumps({
    "draftwright_version":m.version("draftwright"),
    "license":license_id,
    "build123d_version":m.version("build123d"),
    "module":draftwright.__file__,
}))
"""
    metadata = run_json([str(DRAFTWRIGHT_PYTHON), "-c", code])
    return {
        "status": "CANDIDATE_ISOLATED_EVAL",
        "installed": True,
        "metadata": metadata,
        "canonical_build123d_version": "0.11.1",
        "admission": "BLOCKED_FROM_CANONICAL_RUNTIME",
        "reasons": [
            "AGPL-3.0 product/license decision required before reusable commercial tooling",
            "draftwright 0.4.34 requires build123d<0.11 and isolated env resolves build123d 0.10.0",
            "upstream development status is Alpha",
        ],
    }


def all_fixtures(out_dir: Path) -> dict[str, Any]:
    config = load(CONFIG)
    return {
        "schema": "velvetos.ai3d.phase9-fixture-suite.v1",
        "status": "PASS",
        "authority": config["authority"],
        "techdraw": techdraw_fixture(out_dir / "techdraw"),
        "sheetmetal": sheetmetal_fixture(
            out_dir / "sheetmetal",
            k_factor=0.38,
            k_factor_standard="ansi",
        ),
        "text_vector": text_vector_fixture(out_dir / "text-vector"),
        "draftwright": draftwright_evaluation(),
        "safety": config["safety"],
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd", required=True)

    cmd = sub.add_parser("techdraw")
    cmd.add_argument("--out-dir", type=Path, required=True)

    cmd = sub.add_parser("sheetmetal")
    cmd.add_argument("--out-dir", type=Path, required=True)
    cmd.add_argument("--k-factor", type=float, required=True)
    cmd.add_argument(
        "--k-factor-standard",
        choices=["ansi", "din", "ANSI", "DIN"],
        required=True,
    )

    cmd = sub.add_parser("text-vector")
    cmd.add_argument("--out-dir", type=Path, required=True)

    sub.add_parser("draftwright-eval")

    cmd = sub.add_parser("all")
    cmd.add_argument("--out-dir", type=Path, required=True)
    return root


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def main() -> int:
    args = parser().parse_args()
    if args.cmd == "techdraw":
        return emit(techdraw_fixture(args.out_dir))
    if args.cmd == "sheetmetal":
        return emit(
            sheetmetal_fixture(
                args.out_dir,
                k_factor=args.k_factor,
                k_factor_standard=args.k_factor_standard,
            )
        )
    if args.cmd == "text-vector":
        return emit(text_vector_fixture(args.out_dir))
    if args.cmd == "draftwright-eval":
        return emit(draftwright_evaluation())
    if args.cmd == "all":
        return emit(all_fixtures(args.out_dir))
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
