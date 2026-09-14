#!/usr/bin/env python3
"""Deterministic base-edit adapter for Velvet Visual Foundry.

This is not an orchestrator or publisher. It consumes an approved EDL-like
request, returns a normalized base cut plus receipt, and leaves public text,
composition, QA and publishing to the existing Foundry/HyperFrames path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SUPPORTED_FPS = {24, 25, 30, 50, 60}
RESOLUTIONS = {"portrait": (1080, 1920), "landscape": (1920, 1080)}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def run(cmd: list[str], *, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture, check=True)


def tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        fail(f"required tool missing: {name}")
    return found


def load_request(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid request JSON: {exc}")
    if not isinstance(value, dict):
        fail("request must be a JSON object")
    return value


def inside(root: Path, value: str, *, must_exist: bool = False) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        fail(f"path escapes projectDir: {value}")
    if must_exist and not candidate.is_file():
        fail(f"source file missing: {candidate}")
    return candidate


def probe(path: Path) -> dict:
    ffprobe = tool("ffprobe")
    result = run([
        ffprobe, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path)
    ], capture=True)
    return json.loads(result.stdout)


def media_duration(data: dict) -> float:
    try:
        return float((data.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        return 0.0


def has_audio(data: dict) -> bool:
    return any(stream.get("codec_type") == "audio" for stream in data.get("streams") or [])


def video_stream(data: dict) -> dict:
    for stream in data.get("streams") or []:
        if stream.get("codec_type") == "video":
            return stream
    fail("rendered output has no video stream")
    return {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_request(req: dict) -> dict:
    for key in ("jobId", "projectDir", "output", "segments"):
        if key not in req:
            fail(f"request missing required field: {key}")
    project = Path(str(req["projectDir"])).expanduser().resolve()
    if not project.is_dir():
        fail(f"projectDir missing: {project}")
    output = inside(project, str(req["output"]))
    fps = int(req.get("fps", 30))
    if fps not in SUPPORTED_FPS:
        fail(f"unsupported fps: {fps}")
    resolution = str(req.get("resolution", "portrait"))
    if resolution not in RESOLUTIONS:
        fail(f"unsupported resolution: {resolution}")
    policy = str(req.get("cutPolicy", "visual-only"))
    if policy not in {"word-boundary", "visual-only"}:
        fail(f"unsupported cutPolicy: {policy}")
    padding_ms = int(req.get("cutPaddingMs", 80))
    if not 30 <= padding_ms <= 200:
        fail("cutPaddingMs must be 30..200")
    fade = float(req.get("audioFadeSeconds", 0.03))
    if not 0.01 <= fade <= 0.10:
        fail("audioFadeSeconds must be 0.01..0.10")
    segments = req.get("segments")
    if not isinstance(segments, list) or not segments:
        fail("segments must be a non-empty list")
    normalized = []
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            fail(f"segment {index} must be object")
        for key in ("source", "start", "end"):
            if key not in segment:
                fail(f"segment {index} missing {key}")
        source = inside(project, str(segment["source"]), must_exist=True)
        start = float(segment["start"])
        end = float(segment["end"])
        if start < 0 or end <= start:
            fail(f"segment {index} invalid range {start}..{end}")
        source_probe = probe(source)
        duration = media_duration(source_probe)
        if duration <= 0 or end > duration + 0.05:
            fail(f"segment {index} exceeds source duration ({duration:.3f}s)")
        if policy == "word-boundary":
            if segment.get("wordBoundaryStart") is not True or segment.get("wordBoundaryEnd") is not True:
                fail(f"segment {index} lacks verified word-boundary attestations")
        normalized.append({
            "source": source,
            "sourceRelative": source.relative_to(project).as_posix(),
            "start": start,
            "end": end,
            "duration": end - start,
            "hasAudio": has_audio(source_probe),
            "beat": str(segment.get("beat") or ""),
            "reason": str(segment.get("reason") or ""),
        })
    return {
        "jobId": str(req["jobId"]),
        "project": project,
        "output": output,
        "fps": fps,
        "resolution": resolution,
        "size": RESOLUTIONS[resolution],
        "cutPolicy": policy,
        "cutPaddingMs": padding_ms,
        "fade": fade,
        "audioRequired": bool(req.get("audioRequired", True)),
        "segments": normalized,
    }


def render_segment(cfg: dict, segment: dict, target: Path) -> None:
    ffmpeg = tool("ffmpeg")
    width, height = cfg["size"]
    duration = segment["duration"]
    fade = min(cfg["fade"], max(duration / 4.0, 0.01))
    fade_out = max(0.0, duration - fade)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={cfg['fps']},format=yuv420p"
    )
    af = (
        "aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
        f"afade=t=in:st=0:d={fade:.3f},"
        f"afade=t=out:st={fade_out:.3f}:d={fade:.3f}"
    )
    cmd = [
        ffmpeg, "-y", "-v", "warning", "-i", str(segment["source"]),
        "-ss", f"{segment['start']:.6f}", "-t", f"{duration:.6f}",
    ]
    if segment["hasAudio"]:
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-vf", vf, "-af", af]
    else:
        if cfg["audioRequired"]:
            fail(f"audio required but source has no audio: {segment['sourceRelative']}")
        cmd += [
            "-f", "lavfi", "-t", f"{duration:.6f}",
            "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf, "-af", af,
        ]
    cmd += [
        "-r", str(cfg["fps"]), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-ac", "2", "-shortest", str(target),
    ]
    run(cmd)


def concat_segments(cfg: dict, rendered: list[Path], target: Path, temp_dir: Path) -> None:
    ffmpeg = tool("ffmpeg")
    concat_file = temp_dir / "concat.txt"
    lines = []
    for path in rendered:
        safe = path.resolve().as_posix()
        if "'" in safe:
            fail("temporary render path contains unsupported apostrophe")
        lines.append("file '" + safe + "'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    run([
        ffmpeg, "-y", "-v", "warning", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-ac", "2", "-movflags", "+faststart", str(target),
    ])


def receipt_for(cfg: dict) -> dict:
    data = probe(cfg["output"])
    video = video_stream(data)
    duration = media_duration(data)
    width, height = cfg["size"]
    if duration <= 0:
        fail("rendered output duration is zero")
    if int(video.get("width") or 0) != width or int(video.get("height") or 0) != height:
        fail("rendered output dimensions do not match requested canvas")
    if cfg["audioRequired"] and not has_audio(data):
        fail("rendered output missing required audio")
    return {
        "schemaVersion": 1,
        "jobId": cfg["jobId"],
        "kind": "vf-video-base-edit",
        "output": str(cfg["output"]),
        "bytes": cfg["output"].stat().st_size,
        "sha256": sha256(cfg["output"]),
        "duration": duration,
        "width": width,
        "height": height,
        "fps": cfg["fps"],
        "segmentCount": len(cfg["segments"]),
        "cutPolicy": cfg["cutPolicy"],
        "audioFadeSeconds": cfg["fade"],
        "publishReceipt": False,
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
    }


def command_doctor() -> None:
    ffmpeg = tool("ffmpeg")
    ffprobe = tool("ffprobe")
    ffmpeg_line = run([ffmpeg, "-version"], capture=True).stdout.splitlines()[0]
    ffprobe_line = run([ffprobe, "-version"], capture=True).stdout.splitlines()[0]
    print(json.dumps({"ffmpeg": ffmpeg_line, "ffprobe": ffprobe_line}, indent=2))
    print("OK video edit prerequisites ffmpeg+ffprobe")


def command_validate(request_path: Path) -> dict:
    cfg = validate_request(load_request(request_path))
    print(f"OK edit request segments={len(cfg['segments'])} policy={cfg['cutPolicy']}")
    return cfg


def command_plan(request_path: Path) -> None:
    cfg = command_validate(request_path)
    print(json.dumps({
        "jobId": cfg["jobId"],
        "segments": len(cfg["segments"]),
        "output": str(cfg["output"]),
        "canvas": f"{cfg['size'][0]}x{cfg['size'][1]}",
        "fps": cfg["fps"],
        "cutPolicy": cfg["cutPolicy"],
        "inspectionPaddingMs": cfg["cutPaddingMs"],
        "audioFadeSeconds": cfg["fade"],
        "handoff": "base cut only; overlays/RTL/final composition remain HyperFrames responsibilities",
    }, indent=2))


def command_run(request_path: Path) -> None:
    command_doctor()
    cfg = command_validate(request_path)
    with tempfile.TemporaryDirectory(prefix="vf-video-edit-", dir=str(cfg["output"].parent)) as tmp:
        temp_dir = Path(tmp)
        rendered: list[Path] = []
        for index, segment in enumerate(cfg["segments"]):
            target = temp_dir / f"seg-{index:03d}.mp4"
            print(
                f"RUN segment {index + 1}/{len(cfg['segments'])} "
                f"{segment['sourceRelative']} {segment['start']:.3f}-{segment['end']:.3f}"
            )
            render_segment(cfg, segment, target)
            rendered.append(target)
        concat_segments(cfg, rendered, cfg["output"], temp_dir)
    receipt = receipt_for(cfg)
    receipt_path = Path(str(cfg["output"]) + ".receipt.json")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK base edit verified output={cfg['output']}")
    print(f"OK receipt={receipt_path}")


def command_inspect(request_path: Path) -> None:
    cfg = validate_request(load_request(request_path))
    if not cfg["output"].is_file():
        fail(f"rendered output missing: {cfg['output']}")
    total = media_duration(probe(cfg["output"]))
    if total <= 0:
        fail("cannot inspect zero-duration output")
    pad = cfg["cutPaddingMs"] / 1000.0
    samples: list[tuple[str, float]] = [("first", min(0.15, total / 2))]
    elapsed = 0.0
    for index, segment in enumerate(cfg["segments"][:-1], start=1):
        elapsed += segment["duration"]
        samples.extend([
            (f"cut-{index}-pre", max(0.0, elapsed - pad)),
            (f"cut-{index}-at", min(total, elapsed)),
            (f"cut-{index}-post", min(total, elapsed + pad)),
        ])
    samples.append(("last", max(0.0, total - min(0.15, total / 2))))
    inspect_dir = cfg["output"].parent / f"{cfg['output'].name}.inspect"
    inspect_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = tool("ffmpeg")
    manifest = []
    for name, timestamp in samples:
        image = inspect_dir / f"{name}-{timestamp:.3f}.jpg"
        run([
            ffmpeg, "-y", "-v", "error", "-ss", f"{timestamp:.6f}",
            "-i", str(cfg["output"]), "-frames:v", "1", "-update", "1", str(image),
        ])
        manifest.append({"name": name, "time": timestamp, "image": str(image)})
    manifest_path = inspect_dir / "inspection.json"
    manifest_path.write_text(json.dumps({"output": str(cfg["output"]), "samples": manifest}, indent=2) + "\n", encoding="utf-8")
    print(f"OK boundary inspection samples={len(samples)} dir={inspect_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "validate", "plan", "run", "inspect"])
    parser.add_argument("request", nargs="?")
    args = parser.parse_args()
    if args.command == "doctor":
        command_doctor()
        return
    if not args.request:
        fail(f"{args.command} requires request.json")
    request_path = Path(args.request).expanduser().resolve()
    if args.command == "validate":
        command_validate(request_path)
    elif args.command == "plan":
        command_plan(request_path)
    elif args.command == "run":
        command_run(request_path)
    else:
        command_inspect(request_path)


if __name__ == "__main__":
    main()
