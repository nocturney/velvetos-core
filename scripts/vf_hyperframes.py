#!/usr/bin/env python3
"""Thin VelvetOS bridge to the HyperFrames CLI.

Execution adapter only: validate a render request, build pinned HyperFrames commands,
optionally run them on an Edge/Office host, verify with ffprobe and write a receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HYPERFRAMES_VERSION = "0.8.35"
HYPERFRAMES_PACKAGE = f"hyperframes@{HYPERFRAMES_VERSION}"
SUPPORTED_STAGES = {"rough", "review", "final"}
SUPPORTED_FORMATS = {"mp4", "webm", "mov"}
SUPPORTED_RESOLUTIONS = {"portrait", "portrait-4k"}
SUPPORTED_FPS = {24, 30, 60}


def fail(message: str, code: int = 2) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"request not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid request JSON: {exc}")
    if not isinstance(value, dict):
        fail("request must be a JSON object")
    return value


def require_text(obj: dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"request.{key} must be a non-empty string")
    return value.strip()


def resolve_under(base: Path, raw: str, label: str) -> Path:
    candidate = (base / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        fail(f"{label} must stay under projectDir")
    return candidate


def validate_request(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("backend") != "hyperframes":
        fail("request.backend must be 'hyperframes'")
    job_id = require_text(data, "jobId")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", job_id):
        fail("request.jobId contains unsupported characters")

    project_dir = Path(require_text(data, "projectDir")).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"projectDir is not a directory: {project_dir}")

    composition_raw = str(data.get("composition") or "index.html")
    composition = resolve_under(project_dir, composition_raw, "composition")
    if not composition.is_file():
        fail(f"composition not found: {composition}")

    stage = str(data.get("stage") or "rough")
    if stage not in SUPPORTED_STAGES:
        fail(f"stage must be one of {sorted(SUPPORTED_STAGES)}")
    output_format = str(data.get("format") or "mp4")
    if output_format not in SUPPORTED_FORMATS:
        fail(f"format must be one of {sorted(SUPPORTED_FORMATS)}")
    target = str(data.get("target") or "reel_master")
    if target in {"reel_master", "story_master", "feed_video"} and output_format != "mp4":
        fail(f"target {target} requires mp4")

    resolution = str(data.get("resolution") or "portrait")
    if resolution not in SUPPORTED_RESOLUTIONS:
        fail(f"resolution must be one of {sorted(SUPPORTED_RESOLUTIONS)}")
    fps = int(data.get("fps") or 30)
    if fps not in SUPPORTED_FPS:
        fail(f"fps must be one of {sorted(SUPPORTED_FPS)}")

    quality_default = "high" if stage == "final" else "draft" if stage == "rough" else "standard"
    quality = str(data.get("quality") or quality_default)
    if quality not in {"draft", "standard", "high"}:
        fail("quality must be draft, standard or high")
    if stage == "final" and quality != "high":
        fail("final stage requires quality=high")

    output = resolve_under(project_dir, require_text(data, "output"), "output")
    expected_suffix = ".mp4" if output_format == "mp4" else f".{output_format}"
    if output.suffix.lower() != expected_suffix:
        fail(f"output extension must be {expected_suffix}")

    variables_file = None
    if data.get("variablesFile"):
        variables_file = resolve_under(project_dir, str(data["variablesFile"]), "variablesFile")
        if not variables_file.is_file():
            fail(f"variablesFile not found: {variables_file}")
        read_json(variables_file)

    audio_required = bool(data.get("audioRequired", target in {"reel_master", "story_master", "feed_video"}))
    return {
        "jobId": job_id,
        "projectDir": project_dir,
        "composition": composition,
        "compositionArg": composition.relative_to(project_dir).as_posix(),
        "stage": stage,
        "target": target,
        "format": output_format,
        "resolution": resolution,
        "fps": fps,
        "quality": quality,
        "output": output,
        "outputArg": output.relative_to(project_dir).as_posix(),
        "variablesFile": variables_file,
        "variablesFileArg": variables_file.relative_to(project_dir).as_posix() if variables_file else None,
        "audioRequired": audio_required,
        "strictAll": bool(data.get("strictAll", stage == "final")),
    }


def hyperframes_command() -> str:
    path = shutil.which("hyperframes")
    if not path:
        fail(
            f"HyperFrames CLI {HYPERFRAMES_VERSION} is not installed on this render host; "
            "install/cache the pinned CLI outside the content job and rerun doctor"
        )
    return path


def hyperframes_base(resolve: bool = False) -> list[str]:
    return [hyperframes_command() if resolve else "hyperframes"]


def build_commands(req: dict[str, Any], resolve_binary: bool = False) -> list[list[str]]:
    check = hyperframes_base(resolve_binary) + ["check"]
    render = hyperframes_base(resolve_binary) + [
        "render",
        "--composition", req["compositionArg"],
        "--output", req["outputArg"],
        "--quality", req["quality"],
        "--fps", str(req["fps"]),
        "--resolution", req["resolution"],
        "--format", req["format"],
        "--strict-all" if req["strictAll"] else "--strict",
    ]
    if req["variablesFileArg"]:
        render += ["--variables-file", req["variablesFileArg"], "--strict-variables"]
    return [check, render]


def tool_version(tool: str) -> str | None:
    path = shutil.which(tool)
    if not path:
        return None
    try:
        proc = subprocess.run([path, "--version"], text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = (proc.stdout or proc.stderr or "").strip().splitlines()
    return lines[0] if lines else "present"


def node_major(version: str | None) -> int | None:
    if not version:
        return None
    match = re.search(r"v?(\d+)", version)
    return int(match.group(1)) if match else None


def exact_hyperframes_version(version: str | None) -> str | None:
    if not version:
        return None
    match = re.search(r"(?:hyperframes\s*)?v?(\d+\.\d+\.\d+)", version, re.IGNORECASE)
    return match.group(1) if match else None


def doctor() -> int:
    facts = {name: tool_version(name) for name in ("node", "hyperframes", "ffmpeg", "ffprobe")}
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    missing = [name for name, version in facts.items() if version is None]
    if missing:
        print(f"FAIL missing tools: {', '.join(missing)}", file=sys.stderr)
        return 1
    major = node_major(facts["node"])
    if major is None or major < 22:
        print(f"FAIL HyperFrames requires Node >=22; found {facts['node']}", file=sys.stderr)
        return 1
    actual = exact_hyperframes_version(facts["hyperframes"])
    if actual != HYPERFRAMES_VERSION:
        print(
            f"FAIL HyperFrames version mismatch: required {HYPERFRAMES_VERSION}, found {facts['hyperframes']}",
            file=sys.stderr,
        )
        return 1
    print(f"OK hyperframes host prerequisites package={HYPERFRAMES_PACKAGE}")
    return 0


def run_command(cmd: list[str], cwd: Path) -> None:
    print("RUN " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, text=True)
    if proc.returncode != 0:
        fail(f"command failed with exit={proc.returncode}: {' '.join(cmd)}", proc.returncode)


def probe_output(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        fail("ffprobe is required to verify render output")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,width,height,codec_name", "-of", "json", str(path)],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"ffprobe failed: {(proc.stderr or '').strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"ffprobe returned invalid JSON: {exc}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_probe(req: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams") or []
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if not videos:
        fail("render has no video stream")
    video = videos[0]
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    if width <= 0 or height <= 0 or height <= width:
        fail(f"render is not portrait: {width}x{height}")
    if req["audioRequired"] and not audios:
        fail("render requires audio but ffprobe found no audio stream")
    try:
        duration = float((probe.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0
    if duration <= 0:
        fail("render duration is missing or zero")
    return {
        "durationSec": round(duration, 3),
        "width": width,
        "height": height,
        "videoCodec": video.get("codec_name"),
        "audioStreams": len(audios),
        "audioRequired": req["audioRequired"],
    }


def receipt_path(req: dict[str, Any], override: str | None) -> Path:
    if override:
        return resolve_under(req["projectDir"], override, "receipt")
    return req["output"].with_suffix(req["output"].suffix + ".receipt.json")


def execute(req: dict[str, Any], receipt_override: str | None) -> dict[str, Any]:
    if doctor() != 0:
        raise SystemExit(1)
    req["output"].parent.mkdir(parents=True, exist_ok=True)
    commands = build_commands(req, resolve_binary=True)
    for cmd in commands:
        run_command(cmd, req["projectDir"])
    if not req["output"].is_file() or req["output"].stat().st_size <= 0:
        fail(f"render output missing or empty: {req['output']}")
    verified = verify_probe(req, probe_output(req["output"]))
    receipt = {
        "schemaVersion": 1,
        "jobId": req["jobId"],
        "backend": "hyperframes",
        "package": HYPERFRAMES_PACKAGE,
        "stage": req["stage"],
        "target": req["target"],
        "output": req["outputArg"],
        "bytes": req["output"].stat().st_size,
        "sha256": sha256_file(req["output"]),
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "probe": verified,
        "commands": [[Path(cmd[0]).name, *cmd[1:]] for cmd in commands],
    }
    target = receipt_path(req, receipt_override)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK render verified receipt={target}")
    return receipt


def plan(req: dict[str, Any]) -> None:
    print(json.dumps({
        "package": HYPERFRAMES_PACKAGE,
        "cwd": str(req["projectDir"]),
        "commands": build_commands(req),
        "output": str(req["output"]),
        "audioRequired": req["audioRequired"],
        "note": "plan does not install or resolve HyperFrames; run doctor on the authorized render host before run",
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS HyperFrames render bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="check local Node/HyperFrames/FFmpeg prerequisites without network")
    plan_parser = sub.add_parser("plan", help="validate a request and print exact commands; no render/network")
    plan_parser.add_argument("request", type=Path)
    run_parser = sub.add_parser("run", help="execute check+render+ffprobe and write a receipt")
    run_parser.add_argument("request", type=Path)
    run_parser.add_argument("--receipt", help="receipt path relative to projectDir")
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    req = validate_request(read_json(args.request))
    if args.command == "plan":
        plan(req)
        return 0
    execute(req, args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
