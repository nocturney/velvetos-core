#!/usr/bin/env python3
"""Render a source-truth Blender turntable from a real print file.

Outside Blender, doctor/plan reuse vf_3d.detect_blender.
Inside Blender, invoke with blender -b -P scripts/vf_turntable.py -- plus render arguments.
No generative product geometry and no printer control.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {".3mf", ".stl", ".obj", ".glb", ".gltf", ".blend"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_blender() -> Path | None:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from vf_3d import detect_blender
    return detect_blender()
def parse_hex(value: str) -> tuple[float, float, float, float]:
    text = value.strip().lstrip("#")
    if len(text) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in text):
        raise ValueError("base color must be #RRGGBB")
    return tuple(int(text[i:i+2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def render_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Velvet real-print-file turntable")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--duration", type=float, default=7.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--color-mode", choices=("embedded", "verified-hex"), default="embedded")
    ap.add_argument("--base-color-hex")
    ap.add_argument("--color-source")
    ap.add_argument("--receipt")
    args = ap.parse_args(argv)
    if not 6.0 <= args.duration <= 8.0:
        ap.error("--duration must be 6-8 seconds")
    if args.fps != 30 or (args.width, args.height) != (1080, 1920):
        ap.error("canonical turntable is 1080x1920 at 30fps")
    if args.color_mode == "verified-hex" and (not args.base_color_hex or not args.color_source):
        ap.error("verified-hex requires --base-color-hex and --color-source")
    return args


def import_product(bpy, source: Path) -> list:
    before = set(bpy.data.objects)
    ext = source.suffix.lower()
    if ext == ".3mf":
        bpy.ops.wm.threemf_import(filepath=str(source))
    elif ext == ".stl":
        bpy.ops.wm.stl_import(filepath=str(source))
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=str(source))
    elif ext in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(source))
    elif ext == ".blend":
        with bpy.data.libraries.load(str(source), link=False) as (src, dst):
            dst.objects = [name for name in src.objects if name]
        for obj in dst.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
    else:
        raise RuntimeError(f"unsupported print file extension: {ext}")
    objects = [obj for obj in bpy.data.objects if obj not in before and obj.type in {"MESH", "CURVE", "SURFACE", "FONT"}]
    if not objects:
        raise RuntimeError("real print file imported no renderable product objects")
    return objects
def clear_scene(bpy) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def bounds_world(objects) -> tuple:
    from mathutils import Vector
    points = []
    for obj in objects:
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    center = tuple((mins[i] + maxs[i]) / 2 for i in range(3))
    size = tuple(maxs[i] - mins[i] for i in range(3))
    return center, size


def apply_verified_color(bpy, objects, rgba) -> None:
    material = bpy.data.materials.new("VF_VERIFIED_PRINT_COLOR")
    material.diffuse_color = rgba
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.42
    for obj in objects:
        if hasattr(obj.data, "materials"):
            obj.data.materials.clear()
            obj.data.materials.append(material)


def add_area_light(bpy, name, location, energy, size, color):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def track_to(obj, target=(0.0, 0.0, 0.0)):
    from mathutils import Vector
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
def build_scene(bpy, objects, args):
    center, size = bounds_world(objects)
    pivot = bpy.data.objects.new("VF_PRODUCT_TURNTABLE", None)
    bpy.context.collection.objects.link(pivot)

    for obj in objects:
        world = obj.matrix_world.copy()
        obj.parent = pivot
        obj.matrix_world = world
        obj.location.x -= center[0]
        obj.location.y -= center[1]
        obj.location.z -= center[2]

    if args.color_mode == "verified-hex":
        apply_verified_color(bpy, objects, parse_hex(args.base_color_hex))

    radius = max(size[0], size[1], size[2], 0.001)
    camera_data = bpy.data.cameras.new("VF_CAMERA")
    camera = bpy.data.objects.new("VF_CAMERA", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (radius * 2.55, -radius * 4.4, radius * 1.55)
    camera_data.lens = 60
    track_to(camera)
    bpy.context.scene.camera = camera

    bpy.ops.mesh.primitive_plane_add(size=radius * 10, location=(0, 0, -size[2] * 0.54))
    floor = bpy.context.object
    floor.name = "VF_WARM_INTERIOR_SURFACE"
    floor_mat = bpy.data.materials.new("VF_NEUTRAL_SURFACE")
    floor_mat.diffuse_color = (0.11, 0.085, 0.065, 1.0)
    floor.data.materials.append(floor_mat)

    key = add_area_light(bpy, "VF_WINDOW_KEY", (-radius*2.2, -radius*2.0, radius*3.4), 1100, radius*2.8, (1.0, 0.78, 0.58))
    fill = add_area_light(bpy, "VF_SOFT_FILL", (radius*2.8, -radius*0.4, radius*1.8), 650, radius*3.2, (0.86, 0.92, 1.0))
    rim = add_area_light(bpy, "VF_WARM_RIM", (0, radius*2.6, radius*2.4), 800, radius*2.0, (1.0, 0.58, 0.36))
    for light in (key, fill, rim):
        track_to(light)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    frames = int(round(args.duration * args.fps))
    scene.frame_start = 1
    scene.frame_end = frames
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot.rotation_euler = (0.0, 0.0, math.tau)
    pivot.keyframe_insert(data_path="rotation_euler", frame=frames + 1)
    if pivot.animation_data and pivot.animation_data.action:
        for curve in pivot.animation_data.action.fcurves:
            for keyframe in curve.keyframe_points:
                keyframe.interpolation = "LINEAR"

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(Path(args.output).resolve())
    scene.world.color = (0.025, 0.018, 0.014)
    return {
        "frames": frames,
        "sourceBounds": [round(v, 6) for v in size],
        "loopRule": "frame N+1 is 360 degrees; rendered frames stop at N to avoid duplicate end frame",
    }


def render_inside_blender(args) -> int:
    import bpy
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"FAIL real print file missing: {source}")
    if source.suffix.lower() not in SUPPORTED:
        raise SystemExit(f"FAIL unsupported print file extension: {source.suffix}")
    if output.suffix.lower() != ".mp4":
        raise SystemExit("FAIL turntable output must be .mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    clear_scene(bpy)
    objects = import_product(bpy, source)
    scene_facts = build_scene(bpy, objects, args)
    bpy.ops.render.render(animation=True)
    if not output.is_file() or output.stat().st_size <= 0:
        raise SystemExit("FAIL Blender did not create the expected MP4")
    receipt = {
        "schemaVersion": 1,
        "kind": "real_print_file_turntable",
        "productSource": {
            "path": str(source),
            "sha256": sha256_file(source),
            "rule": "geometry comes from this real print file; no AI product generation",
        },
        "render": {
            "output": str(output),
            "sha256": sha256_file(output),
            "durationSec": args.duration,
            "fps": args.fps,
            "size": [args.width, args.height],
            **scene_facts,
        },
        "color": {
            "mode": args.color_mode,
            "verifiedHex": args.base_color_hex if args.color_mode == "verified-hex" else None,
            "source": args.color_source if args.color_mode == "verified-hex" else "embedded print-file materials",
        },
        "publicationAuthorized": False,
    }
    receipt_path = Path(args.receipt).resolve() if args.receipt else output.with_suffix(output.suffix + ".turntable-receipt.json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VF_TURNTABLE_OK " + json.dumps({"output": str(output), "receipt": str(receipt_path)}, ensure_ascii=False))
    return 0


def outside_main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Velvet turntable helper; actual render runs inside Blender -P")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    plan = sub.add_parser("plan")
    plan.add_argument("--input", required=True)
    plan.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    blender = discover_blender()
    if not blender:
        print(json.dumps({"status":"BLOCKED","reason":"Blender not discovered through vf_3d"}, indent=2))
        return 2
    if args.command == "doctor":
        print(json.dumps({"status":"PASS","blender":str(blender),"discovery":"vf_3d.detect_blender"}, indent=2))
        return 0
    command = [
        str(blender), "--factory-startup", "--disable-autoexec", "-b", "-P",
        str(Path(__file__).resolve()), "--", "--input", args.input, "--output", args.output,
    ]
    print(json.dumps({"status":"PLAN","command":command,"renderExecuted":False}, ensure_ascii=False, indent=2))
    return 0
def main() -> int:
    try:
        import bpy  # type: ignore
    except ImportError:
        return outside_main(sys.argv[1:])
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = render_args(argv)
    return render_inside_blender(args)


if __name__ == "__main__":
    raise SystemExit(main())
