#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

HEX = re.compile(r"#[0-9a-fA-F]{6}")

def fail(msg: str) -> None:
    print(json.dumps({"status":"FAIL","error":msg}, ensure_ascii=False))
    raise SystemExit(1)

def norm_color(value: str) -> str:
    value=value.strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        fail(f"invalid palette color: {value}")
    return value.lower()

def load_vtracer():
    try:
        import vtracer
    except Exception as exc:
        fail(f"vtracer unavailable: {exc}")
    return vtracer

def doctor() -> None:
    vtracer=load_vtracer()
    print(json.dumps({
        "status":"PASS",
        "component":"vtracer",
        "version":pkg_version("vtracer"),
        "config_api":hasattr(vtracer,"Config"),
        "runtime_authority":False,
        "printer_control":False
    }, indent=2))

def trace(args) -> None:
    src=Path(args.input).resolve()
    dst=Path(args.output).resolve()
    if not src.is_file():
        fail(f"missing input: {src}")
    palette=[norm_color(x) for x in args.palette.split(",") if x.strip()]
    if not 1 <= len(palette) <= args.max_palette_colors:
        fail(f"palette must contain 1..{args.max_palette_colors} colors")
    if len(set(palette)) != len(palette):
        fail("palette contains duplicate colors")
    vtracer=load_vtracer()
    cfg=vtracer.Config(mode="polygon", filter_speckle=args.filter_speckle)
    cfg.hierarchical="cutout"
    cfg.palette=palette
    cfg.optimize=2
    cfg.convert_file(str(src), str(dst))
    if not dst.is_file() or dst.stat().st_size <= 0:
        fail("vtracer produced no SVG")
    svg=dst.read_text(encoding="utf-8")
    used={c.lower() for c in HEX.findall(svg)}
    extras=sorted(used-set(palette))
    if extras:
        fail("SVG contains colors outside locked palette: "+",".join(extras))
    receipt={
        "status":"PASS",
        "schema":"velvetos.vtracer.receipt.v1",
        "input":str(src),
        "output":str(dst),
        "palette":palette,
        "palette_count":len(palette),
        "observed_svg_colors":sorted(used),
        "observed_color_count":len(used),
        "hierarchical":"cutout",
        "runtime_authority":False,
        "printer_control":False
    }
    print(json.dumps(receipt, indent=2))

def main() -> None:
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    tr=sub.add_parser("trace")
    tr.add_argument("--input", required=True)
    tr.add_argument("--output", required=True)
    tr.add_argument("--palette", required=True)
    tr.add_argument("--max-palette-colors", type=int, default=4)
    tr.add_argument("--filter-speckle", type=int, default=4)
    args=ap.parse_args()
    if args.cmd=="doctor": doctor()
    elif args.cmd=="trace": trace(args)

if __name__ == "__main__":
    main()
