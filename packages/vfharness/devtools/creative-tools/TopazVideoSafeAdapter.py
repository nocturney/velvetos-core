import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VELVET_ROOT = Path(r"D:\Velvet").resolve()
TOPAZ_ROOT = Path(r"C:\Program Files\Topaz Labs LLC\Topaz Video")
FFMPEG = TOPAZ_ROOT / "ffmpeg.exe"
FFPROBE = TOPAZ_ROOT / "ffprobe.exe"
MODEL_DIR = Path(r"C:\ProgramData\Topaz Labs LLC\Topaz Video\models")
MODEL_DATA_DIR = Path(r"C:\ProgramData\Topaz Labs LLC\Topaz Video")
REQUIRED_FILTERS = {"tvai_up", "tvai_fi", "tvai_pe", "tvai_cpe", "tvai_stb"}
MODEL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,47}$", re.I)
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

def emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=True))
    raise SystemExit(code)

def fail(message, code="ADAPTER_ERROR", exit_code=2, **extra):
    out = {"ok": False, "error": {"code": code, "message": message}}
    out.update(extra)
    emit(out, exit_code)

def safe_path(raw, *, must_exist=False, output=False):
    if not raw:
        fail("path is required", "INVALID_PATH")
    try:
        p = Path(raw).expanduser().resolve()
    except Exception:
        fail("path could not be resolved", "INVALID_PATH")
    if p != VELVET_ROOT and VELVET_ROOT not in p.parents:
        fail("path must be under D:\\Velvet", "PATH_OUTSIDE_VELVET")
    if must_exist and not p.is_file():
        fail("input file does not exist", "INPUT_NOT_FOUND")
    if output:
        if p.exists():
            fail("output already exists; overwrite is not allowed", "OUTPUT_EXISTS")
        p.parent.mkdir(parents=True, exist_ok=True)
    return p

def model_id(raw):
    if not raw or not MODEL_RE.fullmatch(raw):
        fail("invalid model id", "INVALID_MODEL")
    manifest = MODEL_DIR / f"{raw}.json"
    if not manifest.is_file():
        fail("model is not present in the installed Topaz model catalogue", "MODEL_NOT_CATALOGUED")
    return raw

def env():
    e = os.environ.copy()
    e["TVAI_MODEL_DIR"] = str(MODEL_DIR)
    e["TVAI_MODEL_DATA_DIR"] = str(MODEL_DATA_DIR)
    return e

def run(cmd, timeout=300):
    try:
        cp = subprocess.run(
            [str(x) for x in cmd],
            env=env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
    except subprocess.TimeoutExpired:
        fail("Topaz command timed out", "TIMEOUT")
    return cp

def safe_error_text(text):
    # Do not expose license, machine, serial, token or device identifiers from vendor logs.
    blocked = ("license", "machine id", "serial", "issued to", "device id", "rlm")
    lines = []
    for line in (text or "").splitlines():
        low = line.lower()
        if any(word in low for word in blocked):
            continue
        if line.strip():
            lines.append(line.strip())
    return "\n".join(lines[-12:])[:3000]

def list_filters():
    cp = run([FFMPEG, "-hide_banner", "-filters"], timeout=20)
    text = (cp.stdout or "") + "\n" + (cp.stderr or "")
    found = sorted(name for name in REQUIRED_FILTERS if re.search(rf"\b{re.escape(name)}\b", text))
    return found

def probe():
    if not FFMPEG.is_file() or not FFPROBE.is_file():
        fail("bundled ffmpeg/ffprobe missing", "RUNTIME_MISSING")
    ver = run([FFMPEG, "-hide_banner", "-version"], timeout=20)
    if ver.returncode != 0:
        fail("bundled ffmpeg version probe failed", "FFMPEG_PROBE_FAILED")
    first = ((ver.stdout or ver.stderr or "").splitlines() or [""])[0]
    found = list_filters()
    missing = sorted(REQUIRED_FILTERS - set(found))
    if missing:
        fail("required Topaz filters missing", "FILTERS_MISSING", missing=missing)
    manifests = sorted(p.stem for p in MODEL_DIR.glob("*.json") if MODEL_RE.fullmatch(p.stem))
    cached_paths = sorted(p for p in MODEL_DATA_DIR.glob("*.tz*") if p.is_file())
    cached = [p.name for p in cached_paths]
    accepted_payloads = [p for p in cached_paths if p.name.lower().startswith("ahq-v12-") and p.stat().st_size > 1024 * 1024]
    if not accepted_payloads:
        fail("accepted ahq-12 model payload is missing", "ACCEPTED_MODEL_PAYLOAD_MISSING")
    emit({
        "ok": True,
        "status": "PASS",
        "mode": "cli_headless",
        "ffmpeg": first,
        "filters": found,
        "model_catalog_count": len(manifests),
        "cached_payload_count": len(cached),
        "automatic_downloads": False,
        "operations": ["probe", "probe-media", "enhance"],
        "blocked": [
            "arbitrary_ffmpeg_args",
            "automatic_model_downloads",
            "interpolate_pending_acceptance",
            "stabilize_pending_acceptance",
            "camera_pose_pending_acceptance"
        ],
    })

def probe_media(path):
    p = safe_path(path, must_exist=True)
    cp = run([
        FFPROBE, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", p
    ], timeout=30)
    if cp.returncode != 0:
        fail("ffprobe failed", "MEDIA_PROBE_FAILED", detail=safe_error_text(cp.stderr))
    try:
        data = json.loads(cp.stdout)
    except Exception:
        fail("ffprobe returned invalid JSON", "MEDIA_PROBE_INVALID")
    streams = []
    for s in data.get("streams", []):
        streams.append({
            "index": s.get("index"),
            "codec_type": s.get("codec_type"),
            "codec_name": s.get("codec_name"),
            "width": s.get("width"),
            "height": s.get("height"),
            "r_frame_rate": s.get("r_frame_rate"),
            "avg_frame_rate": s.get("avg_frame_rate"),
            "nb_frames": s.get("nb_frames"),
            "duration": s.get("duration"),
        })
    fmt = data.get("format") or {}
    emit({
        "ok": True,
        "path": str(p),
        "streams": streams,
        "format": {
            "format_name": fmt.get("format_name"),
            "duration": fmt.get("duration"),
            "size": fmt.get("size"),
        }
    })

def validate_device(raw):
    text = str(raw)
    if text in {"-2", "-1"}:
        return text
    if not re.fullmatch(r"\d+(?:\.\d+)*", text):
        fail("device must be -2, -1, or a dot-separated GPU index list", "INVALID_DEVICE")
    return text

def validate_vram(value):
    try:
        v = float(value)
    except Exception:
        fail("vram must be numeric", "INVALID_VRAM")
    if not (0.1 <= v <= 1.0):
        fail("vram must be between 0.1 and 1.0", "INVALID_VRAM")
    return v

def common_io(input_path, output_path):
    src = safe_path(input_path, must_exist=True)
    dst = safe_path(output_path, output=True)
    if dst.suffix.lower() != ".mkv":
        fail("safe production output must use .mkv", "INVALID_OUTPUT_FORMAT")
    if src == dst:
        fail("input and output must differ", "INVALID_OUTPUT_PATH")
    return src, dst

def enhance(args):
    src, dst = common_io(args.input, args.output)
    model = model_id(args.model)
    if args.scale not in (1, 2, 4):
        fail("scale must be 1, 2, or 4", "INVALID_SCALE")
    device = validate_device(args.device)
    vram = validate_vram(args.vram)
    filt = (
        f"tvai_up=model={model}:scale={args.scale}:download=0:"
        f"device={device}:vram={vram:g}"
    )
    cp = run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-n",
        "-i", src,
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", filt,
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "rgb48le",
        "-c:a", "copy",
        dst,
    ], timeout=args.timeout)
    if cp.returncode != 0:
        if dst.exists():
            try: dst.unlink()
            except OSError: pass
        fail("Topaz enhancement failed", "TOPAZ_ENHANCE_FAILED", detail=safe_error_text(cp.stderr))
    if not dst.is_file() or dst.stat().st_size <= 0:
        fail("Topaz enhancement produced no artifact", "OUTPUT_MISSING")
    emit({
        "ok": True,
        "operation": "enhance",
        "model": model,
        "scale": args.scale,
        "download": False,
        "output": str(dst),
        "bytes": dst.stat().st_size,
    })

def interpolate(args):
    src, dst = common_io(args.input, args.output)
    model = model_id(args.model)
    device = validate_device(args.device)
    vram = validate_vram(args.vram)
    if not re.fullmatch(r"(?:\d+(?:\.\d+)?|\d+/\d+)", args.fps):
        fail("fps must be numeric or a rational such as 60000/1001", "INVALID_FPS")
    filt = (
        f"tvai_fi=model={model}:fps={args.fps}:download=0:"
        f"device={device}:vram={vram:g}:rdt={args.rdt:g}"
    )
    cp = run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-n",
        "-i", src,
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", filt,
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "rgb48le",
        "-c:a", "copy",
        dst,
    ], timeout=args.timeout)
    if cp.returncode != 0:
        if dst.exists():
            try: dst.unlink()
            except OSError: pass
        fail("Topaz interpolation failed", "TOPAZ_INTERPOLATE_FAILED", detail=safe_error_text(cp.stderr))
    emit({
        "ok": True,
        "operation": "interpolate",
        "model": model,
        "fps": args.fps,
        "download": False,
        "output": str(dst),
        "bytes": dst.stat().st_size,
    })

def main():
    ap = argparse.ArgumentParser(add_help=True)
    sp = ap.add_subparsers(dest="operation", required=True)
    sp.add_parser("probe")
    pm = sp.add_parser("probe-media")
    pm.add_argument("path")
    pe = sp.add_parser("enhance")
    pe.add_argument("--input", required=True)
    pe.add_argument("--output", required=True)
    pe.add_argument("--model", default="ahq-12")
    pe.add_argument("--scale", type=int, default=1)
    pe.add_argument("--device", default="0")
    pe.add_argument("--vram", type=float, default=0.5)
    pe.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()
    if args.operation == "probe":
        probe()
    elif args.operation == "probe-media":
        probe_media(args.path)
    elif args.operation == "enhance":
        enhance(args)

if __name__ == "__main__":
    main()
