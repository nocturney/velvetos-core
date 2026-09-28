#!/usr/bin/env python3
"""Build a Velvet Factory premium Reel through Photoshop + After Effects on Chris.

CI-safe validation is available with --validate-only. Production render is Windows-only
and keeps all VelvetOS-controlled runtime/artifacts under VELVETOS_RUNTIME_ROOT.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADOBE = ROOT / "packages" / "vfom" / "adobe"
SCHEMA = ADOBE / "REEL-JOB.schema.json"
PS_JSX = ADOBE / "photoshop-product-layer.jsx"
AE_JSX = ADOBE / "build-reel.jsx"
TOKENS = ROOT / "packages" / "vfbrand" / "brand-tokens.json"
DEFAULT_RUNTIME = Path(r"D:\Velvet\Runtime\VelvetOS")
FFMPEG_DIR = Path(r"D:\Velvet\Tools\Shared\ffmpeg\current\bin")
EXPECTED_VIEWS = ["front", "three_quarter", "side", "back", "close_up"]


class ReelError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReelError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReelError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReelError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def runtime_root() -> Path:
    raw = os.environ.get("VELVETOS_RUNTIME_ROOT")
    root = Path(raw) if raw else DEFAULT_RUNTIME
    if os.name == "nt":
        normalized = str(root).replace("/", "\\").lower().rstrip("\\")
        required = str(DEFAULT_RUNTIME).lower().rstrip("\\")
        if normalized != required:
            raise ReelError(
                "VELVETOS_RUNTIME_ROOT must resolve to D:\\Velvet\\Runtime\\VelvetOS "
                "for the Chris production route"
            )
    return root


def resolve_input(value: str, job_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate = (job_dir / path).resolve()
    if candidate.exists():
        return candidate
    return (ROOT / path).resolve()


def validate_shape(manifest: dict[str, Any], variables: dict[str, Any],
                   storyboard: dict[str, Any], prep: dict[str, Any], job_dir: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "schema", "jobId", "status", "reelType", "reference", "canvas", "copy",
        "assets", "scenes", "audioStrategy", "neededInputs", "publicationAuthorized",
    }
    if set(manifest) != required:
        errors.append(f"manifest keys differ from schema: {sorted(set(manifest) ^ required)}")
    if manifest.get("schema") != "velvetos.adobe-reel-job.v1":
        errors.append("manifest schema must be velvetos.adobe-reel-job.v1")
    if manifest.get("jobId") != job_dir.name:
        errors.append("manifest jobId must match job directory")
    if manifest.get("status") not in {"needs_input", "needs_review"}:
        errors.append("status must be needs_input or needs_review")
    if manifest.get("publicationAuthorized") is not False:
        errors.append("publicationAuthorized must be false")

    canvas = manifest.get("canvas") or {}
    if (canvas.get("width"), canvas.get("height"), canvas.get("fps")) != (1080, 1920, 30):
        errors.append("canvas must be exactly 1080x1920 at 30fps")
    duration = canvas.get("durationSeconds")
    if not isinstance(duration, (int, float)) or not 12 <= float(duration) <= 15:
        errors.append("durationSeconds must be 12-15")

    copy = manifest.get("copy") or {}
    if not (2 <= len(copy.get("headlineLines") or []) <= 4):
        errors.append("headlineLines must contain 2-4 lines")
    if len(copy.get("icons") or []) > 3 or len(copy.get("detailLabels") or []) > 3:
        errors.append("icons/detailLabels must be <=3")
    accent = copy.get("accentHex", "")
    if not (isinstance(accent, str) and len(accent) == 7 and accent.startswith("#")):
        errors.append("accentHex must be #RRGGBB")

    assets = manifest.get("assets") or {}
    expected_assets = {
        "brandTokens": "packages/vfbrand/brand-tokens.json",
        "logo": "packages/vfbrand/assets/logo/velvet-factory-logo-gold-full-lockup-traced.svg",
        "rubik": "packages/vfbrand/assets/fonts/rubik/Rubik-VariableFont_wght.ttf",
        "cinzel": "packages/vfbrand/assets/fonts/cinzel/Cinzel-VariableFont_wght.ttf",
        "headlineWeight": 700,
        "subheadWeight": 600,
    }
    for key, expected in expected_assets.items():
        if assets.get(key) != expected:
            errors.append(f"asset binding drift: {key}")

    scenes = manifest.get("scenes") or []
    if len(scenes) != 5:
        errors.append("exactly five source-backed scene slots are required")
    elif [row.get("view") for row in scenes] != EXPECTED_VIEWS:
        errors.append("scene views must be front, three_quarter, side, back, close_up in order")
    for index, scene in enumerate(scenes, start=1):
        if scene.get("id") != f"scene-{index}":
            errors.append(f"scene id drift at index {index}")
        hashes = scene.get("sha256")
        if not isinstance(hashes, dict) or set(hashes) != {"sourcePhoto", "scene", "emptyPlate"}:
            errors.append(f"scene-{index} sha256 object is incomplete")

    if variables.get("jobId") != manifest.get("jobId"):
        errors.append("variables jobId drift")
    if variables.get("headlineLines") != copy.get("headlineLines"):
        errors.append("variables headlineLines drift from manifest")
    for key in ("subhead", "icons", "detailLabels", "cta", "accentHex"):
        if variables.get(key) != copy.get(key):
            errors.append(f"variables {key} drift from manifest copy")

    if prep.get("status") != manifest.get("status"):
        errors.append("prep-status status drift from manifest")
    if prep.get("neededInputs") != manifest.get("neededInputs"):
        errors.append("prep-status neededInputs drift from manifest")

    sb_scenes = storyboard.get("scenes") or []
    if len(sb_scenes) != 5:
        errors.append("storyboard must contain five scene beats")
    else:
        previous = 0.0
        for row in sb_scenes:
            start = float(row.get("start", -1))
            end = float(row.get("end", -1))
            if start < previous or end <= start:
                errors.append("storyboard scene timing is invalid")
                break
            previous = end
        if previous > float(duration or 0):
            errors.append("storyboard scene beats exceed duration")

    if not SCHEMA.is_file() or not PS_JSX.is_file() or not AE_JSX.is_file():
        errors.append("Adobe schema/JSX implementation missing")
    return errors


def validate_brand(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tokens = read_json(TOKENS)
    copy = manifest["copy"]
    assets = manifest["assets"]
    if copy["cta"] != tokens.get("reel", {}).get("endCardCta"):
        errors.append("CTA drift from brand-tokens reel.endCardCta")
    if assets["logo"] != tokens.get("logo", {}).get("preferred", {}).get("overlay"):
        errors.append("logo drift from brand-tokens logo.preferred.overlay")
    roles = tokens.get("fonts", {}).get("roles", {})
    if roles.get("headline", {}).get("family") != "Rubik" or roles.get("headline", {}).get("weight") != 700:
        errors.append("headline font token is not Rubik 700")
    if roles.get("subhead", {}).get("family") != "Rubik" or roles.get("subhead", {}).get("weight") != 600:
        errors.append("subhead font token is not Rubik 600")
    for key in ("brandTokens", "logo", "rubik", "cinzel"):
        path = ROOT / assets[key]
        if not path.is_file():
            errors.append(f"committed asset missing: {assets[key]}")
    return errors


def source_state(manifest: dict[str, Any], job_dir: Path, verify_hashes: bool) -> tuple[list[str], list[dict[str, Any]]]:
    missing: list[str] = []
    resolved: list[dict[str, Any]] = []
    for row in manifest["scenes"]:
        out = dict(row)
        out["sha256"] = dict(row["sha256"])
        for field in ("sourcePhoto", "scene", "emptyPlate"):
            value = row.get(field) or ""
            digest = row["sha256"].get(field) or ""
            if not value:
                missing.append(f"{row['view']}:{field}")
                out[field] = ""
                continue
            path = resolve_input(value, job_dir)
            out[field] = str(path)
            if not path.is_file():
                missing.append(f"{row['view']}:{field}:missing_file")
                continue
            if verify_hashes:
                actual = sha256(path)
                if not digest:
                    raise ReelError(f"missing source SHA-256 for {row['id']} {field}")
                if actual.lower() != digest.lower():
                    raise ReelError(f"SHA-256 mismatch for {row['id']} {field}")
        resolved.append(out)
    return sorted(set(missing)), resolved


def powershell_file_version(path: Path, env: dict[str, str]) -> str:
    escaped = str(path).replace("'", "''")
    cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
        f"(Get-Item -LiteralPath '{escaped}').VersionInfo.FileVersion",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, env=env)
    if proc.returncode != 0:
        raise ReelError(f"cannot read version for {path}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def find_tools(env: dict[str, str]) -> dict[str, Path | str]:
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    ae_dir = program_files / "Adobe" / "Adobe After Effects 2026" / "Support Files"
    ps = program_files / "Adobe" / "Adobe Photoshop 2026" / "Photoshop.exe"
    aerender = ae_dir / "aerender.exe"
    afterfx = ae_dir / "AfterFX.com"
    if not afterfx.is_file():
        afterfx = ae_dir / "AfterFX.exe"
    ffmpeg = FFMPEG_DIR / "ffmpeg.exe"
    ffprobe = FFMPEG_DIR / "ffprobe.exe"

    for label, path in {
        "Photoshop 2026": ps,
        "After Effects 2026": afterfx,
        "aerender": aerender,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
    }.items():
        if not path.is_file():
            raise ReelError(f"{label} missing at expected path: {path}")

    ps_version = powershell_file_version(ps, env)
    ae_version = powershell_file_version(ae_dir / "AfterFX.exe", env)
    if not ps_version.startswith("27.7"):
        raise ReelError(f"Photoshop 2026 v27.7 required; found {ps_version}")
    if not ae_version.startswith("26.3"):
        raise ReelError(f"After Effects 2026 v26.3 required; found {ae_version}")
    return {
        "photoshop": ps,
        "photoshopVersion": ps_version,
        "afterfx": afterfx,
        "afterEffectsVersion": ae_version,
        "aerender": aerender,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
    }


def wait_marker(path: Path, stage: str, timeout_seconds: int = 180) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.is_file():
            data = read_json(path)
            if not data.get("ok"):
                raise ReelError(f"{stage} failed: {data.get('error', 'unknown error')}")
            return data
        time.sleep(1)
    raise ReelError(f"{stage} did not produce completion marker: {path}")


def run_checked(args: list[str], env: dict[str, str], label: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, check=False, text=True, capture_output=True, env=env)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-4000:]
        raise ReelError(f"{label} failed ({proc.returncode}): {tail}")
    return proc


def register_fonts(paths: list[Path]) -> list[Path]:
    if os.name != "nt":
        raise ReelError("Adobe production render requires Windows")
    gdi = ctypes.windll.gdi32
    user32 = ctypes.windll.user32
    registered: list[Path] = []
    for path in paths:
        added = gdi.AddFontResourceExW(str(path), 0, None)
        if added <= 0:
            raise ReelError(f"failed to register font for Windows session: {path}")
        registered.append(path)
    user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
    return registered


def unregister_fonts(paths: list[Path]) -> None:
    if os.name != "nt":
        return
    gdi = ctypes.windll.gdi32
    user32 = ctypes.windll.user32
    for path in paths:
        gdi.RemoveFontResourceExW(str(path), 0, None)
    user32.SendMessageW(0xFFFF, 0x001D, 0, 0)


def ffprobe_verify(ffprobe: Path, output: Path, env: dict[str, str],
                   duration_expected: float) -> dict[str, Any]:
    proc = run_checked([
        str(ffprobe), "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(output),
    ], env, "ffprobe")
    payload = json.loads(proc.stdout)
    videos = [row for row in payload.get("streams", []) if row.get("codec_type") == "video"]
    if len(videos) != 1:
        raise ReelError("ffprobe expected exactly one video stream")
    video = videos[0]
    if (int(video.get("width", 0)), int(video.get("height", 0))) != (1080, 1920):
        raise ReelError("final video is not 1080x1920")
    rate = Fraction(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1")
    if rate != Fraction(30, 1):
        raise ReelError(f"final frame rate is not 30fps: {rate}")
    duration = float(payload.get("format", {}).get("duration") or video.get("duration") or 0)
    if abs(duration - duration_expected) > 0.35:
        raise ReelError(f"final duration drift: {duration:.3f}s vs {duration_expected:.3f}s")
    return {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "durationSeconds": duration,
        "codec": video.get("codec_name"),
        "audioStreams": len([r for r in payload.get("streams", []) if r.get("codec_type") == "audio"]),
    }


def build_config(job_dir: Path, manifest: dict[str, Any], storyboard: dict[str, Any],
                 resolved_scenes: list[dict[str, Any]], run_dir: Path) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for row in resolved_scenes:
        item = dict(row)
        item["productLayer"] = str(run_dir / "product-layers" / f"{row['id']}.png")
        scenes.append(item)

    audio = dict(manifest["audioStrategy"])
    if audio.get("file"):
        audio["file"] = str(resolve_input(audio["file"], job_dir))

    return {
        "jobId": manifest["jobId"],
        "canvas": manifest["canvas"],
        "copy": manifest["copy"],
        "assets": {
            "logo": str(ROOT / manifest["assets"]["logo"]),
            "rubik": str(ROOT / manifest["assets"]["rubik"]),
            "cinzel": str(ROOT / manifest["assets"]["cinzel"]),
        },
        "audioStrategy": audio,
        "storyboard": storyboard,
        "scenes": scenes,
        "enableDust": True,
        "photoshopDone": str(run_dir / "markers" / "photoshop.json"),
        "afterEffectsDone": str(run_dir / "markers" / "after-effects.json"),
        "aepFile": str(run_dir / "project" / f"{manifest['jobId']}.aep"),
        "losslessOutput": str(run_dir / "render" / f"{manifest['jobId']}-lossless.avi"),
        "finalOutput": str(run_dir / "render" / f"{manifest['jobId']}.mp4"),
    }


def render(job_dir: Path, manifest: dict[str, Any], storyboard: dict[str, Any],
           resolved_scenes: list[dict[str, Any]]) -> Path:
    if os.name != "nt":
        raise ReelError("production render is Windows-only")
    if manifest["status"] != "needs_review" or manifest["neededInputs"]:
        raise ReelError("job must be needs_review with neededInputs=[] before production render")
    audio_mode = manifest["audioStrategy"]["mode"]
    if audio_mode == "pending":
        raise ReelError("audioStrategy must be resolved before production render")
    if audio_mode != "intentional_silence":
        audio_value = manifest["audioStrategy"].get("file") or ""
        if not audio_value:
            raise ReelError("resolved audioStrategy requires an approved audio file")
        if not resolve_input(audio_value, job_dir).is_file():
            raise ReelError(f"approved audio file missing: {audio_value}")

    root = runtime_root()
    run_dir = root / "reels" / manifest["jobId"]
    for name in ("markers", "product-layers", "project", "render", "tmp", "receipts"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["TEMP"] = str(run_dir / "tmp")
    env["TMP"] = str(run_dir / "tmp")
    config = build_config(job_dir, manifest, storyboard, resolved_scenes, run_dir)
    config_path = run_dir / "job-config.json"
    write_json(config_path, config)
    env["VF_AE_REEL_CONFIG"] = str(config_path)

    tools = find_tools(env)
    registered: list[Path] = []
    try:
        registered = register_fonts([
            ROOT / manifest["assets"]["rubik"],
            ROOT / manifest["assets"]["cinzel"],
        ])

        for marker in (Path(config["photoshopDone"]), Path(config["afterEffectsDone"])):
            if marker.exists():
                marker.unlink()

        subprocess.Popen([str(tools["photoshop"]), "-r", str(PS_JSX)], env=env)
        ps_marker = wait_marker(Path(config["photoshopDone"]), "Photoshop Select Subject")

        subprocess.Popen([str(tools["afterfx"]), "-r", str(AE_JSX)], env=env)
        ae_marker = wait_marker(Path(config["afterEffectsDone"]), "After Effects build")

        aep = Path(config["aepFile"])
        if not aep.is_file():
            raise ReelError(f"After Effects did not save AEP: {aep}")

        run_checked([
            str(tools["aerender"]), "-project", str(aep), "-rqindex", "1",
        ], env, "aerender")

        lossless = Path(config["losslessOutput"])
        if not lossless.is_file():
            raise ReelError(f"aerender output missing: {lossless}")
        final = Path(config["finalOutput"])
        duration_seconds = float(manifest["canvas"]["durationSeconds"])
        ffmpeg_args = [str(tools["ffmpeg"]), "-y", "-i", str(lossless)]
        if audio_mode == "intentional_silence":
            ffmpeg_args += ["-map", "0:v:0", "-an"]
        else:
            audio_file = Path(config["audioStrategy"]["file"])
            ffmpeg_args += [
                "-i", str(audio_file),
                "-filter_complex", f"[1:a]apad=pad_dur={duration_seconds:.3f}[a]",
                "-map", "0:v:0", "-map", "[a]",
                "-c:a", "aac", "-b:a", "192k",
            ]
        ffmpeg_args += [
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            "-t", f"{duration_seconds:.3f}", "-movflags", "+faststart", str(final),
        ]
        run_checked(ffmpeg_args, env, "ffmpeg H.264 transcode")

        probe = ffprobe_verify(Path(tools["ffprobe"]), final, env, duration_seconds)
        if audio_mode == "intentional_silence" and probe["audioStreams"] != 0:
            raise ReelError("intentional_silence final must not contain an audio stream")
        if audio_mode != "intentional_silence" and probe["audioStreams"] < 1:
            raise ReelError("approved audio strategy produced no final audio stream")
        receipt = {
            "schema": "velvetos.adobe-reel-receipt.v1",
            "jobId": manifest["jobId"],
            "publicationAuthorized": False,
            "tools": {
                "photoshopVersion": tools["photoshopVersion"],
                "afterEffectsVersion": tools["afterEffectsVersion"],
                "ffmpeg": str(tools["ffmpeg"]),
                "ffprobe": str(tools["ffprobe"]),
            },
            "stages": {"photoshop": ps_marker, "afterEffects": ae_marker},
            "verification": probe,
            "hashes": {
                "manifest": sha256(job_dir / "manifest.json"),
                "storyboard": sha256(job_dir / "storyboard.json"),
                "variables": sha256(job_dir / "variables.json"),
                "photoshopJsx": sha256(PS_JSX),
                "afterEffectsJsx": sha256(AE_JSX),
                "aep": sha256(aep),
                "lossless": sha256(lossless),
                "finalMp4": sha256(final),
            },
            "output": str(final),
        }
        write_json(run_dir / "receipts" / "render-receipt.json", receipt)
        return final
    finally:
        unregister_fonts(registered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Path to packages/vfom/jobs/VF-R0xx")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    job_dir = Path(args.job)
    if not job_dir.is_absolute():
        job_dir = (ROOT / job_dir).resolve()
    manifest = read_json(job_dir / "manifest.json")
    variables = read_json(job_dir / "variables.json")
    storyboard = read_json(job_dir / "storyboard.json")
    prep = read_json(job_dir / "prep-status.json")

    errors = validate_shape(manifest, variables, storyboard, prep, job_dir)
    errors.extend(validate_brand(manifest))
    if errors:
        raise ReelError("; ".join(errors))

    missing, resolved = source_state(manifest, job_dir, verify_hashes=not args.validate_only)
    declared = sorted(manifest["neededInputs"])
    if manifest["status"] == "needs_input" and not declared:
        raise ReelError("needs_input job must declare neededInputs")
    if manifest["status"] == "needs_review" and (declared or missing):
        raise ReelError("needs_review job cannot have missing inputs")

    if args.validate_only:
        print(json.dumps({
            "ok": True,
            "jobId": manifest["jobId"],
            "status": manifest["status"],
            "renderable": manifest["status"] == "needs_review" and not declared and not missing,
            "declaredNeededInputs": declared,
            "missingSceneFields": missing,
            "schema": SCHEMA.relative_to(ROOT).as_posix(),
            "publicationAuthorized": False,
        }, ensure_ascii=False, indent=2))
        return 0

    if missing:
        raise ReelError("missing render inputs: " + ", ".join(missing))
    output = render(job_dir, manifest, storyboard, resolved)
    print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReelError as exc:
        print(f"ERROR vf_ae_reel: {exc}", file=sys.stderr)
        raise SystemExit(2)
