#!/usr/bin/env python3
"""Isolated motion-template render smoke. Generated assets are NOT Media Vault facts.

Proves only that the optional HyperFrames template can render on a provisioned
host. This deliberately bypasses the *production* motion planner because all
media in this test are synthetic placeholders, not publishable product assets.
No posting, publishing, network installation, or live business asset mutation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIABLE_SCHEMA = ROOT / "packages/vfom/hyperframes/MOTION-STORY-VARIABLES.schema.json"


def png(path: Path, tone: int) -> None:
    width, height = 480, 854
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            band = 18 if (x // 48 + y // 70) % 2 else 0
            v = max(0, min(255, tone + band))
            raw.extend((v, v, v))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(bytes(raw), level=6))
    payload += chunk(b"IEND", b"")
    path.write_bytes(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", choices=("product_reveal", "before_after", "shorts_hook"), default="product_reveal")
    parser.add_argument("--keep", action="store_true", help="keep synthetic render files under .staging for optional offline inspection")
    parser.add_argument("--diagnose", action="store_true", help="diagnostic-only permissive render; NEVER a pass for production QA")
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("hyperframes"):
        print("FAIL missing ffmpeg/hyperframes; run vf_hyperframes doctor", file=sys.stderr)
        return 2

    staging = ROOT / ".staging"
    staging.mkdir(exist_ok=True)
    job = Path(tempfile.mkdtemp(prefix="motion-smoke-", dir=staging))
    try:
        png(job / "before.png", 65)
        png(job / "after.png", 105)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=7",
                        "-c:a", "pcm_s16le", str(job / "test-tone.wav")],
                       check=True, timeout=45)
        rel = job.relative_to(ROOT).as_posix()
        required = json.loads(VARIABLE_SCHEMA.read_text(encoding="utf-8"))["required"]
        variables = {key: "" for key in required}
        variables.update({
            "motionStyle": args.style,
            "variablesStatus": "ready",
            "neededInputs": "",
            "headline": "בדיקת תנועה בלבד",
            "subhead": "מקור סינתטי לבדיקת מנוע, לא מוצר",
            "heroImage": rel + "/before.png",
            "sourceAssetRef": "TECHNICAL_FIXTURE_NOT_A_MEDIA_VAULT_ASSET",
            "comparisonImage": rel + "/after.png",
            "comparisonAssetRef": "TECHNICAL_FIXTURE_NOT_A_MEDIA_VAULT_ASSET_AFTER",
            "comparisonEvidenceRef": rel + "/fixture-only.json",
            "beat1": "הדמיה",
            "beat2": "בדיקה",
            "beat3": "ללא פרסום",
            "audioFile": rel + "/test-tone.wav",
            "accentId": "copper",
            "accentHex": "#a86838",
            "accentSource": "brand-tokens",
        })
        (job / "fixture-only.json").write_text(json.dumps({"technicalFixtureOnly": True, "verifiedProduct": False}), encoding="utf-8")
        (job / "variables.json").write_text(json.dumps(variables, ensure_ascii=False, indent=2), encoding="utf-8")
        request = {
            "jobId": "VF-MOTION-TECHNICAL-SMOKE",
            "backend": "hyperframes",
            "projectDir": str(ROOT),
            "composition": "packages/vfom/hyperframes/templates/motion-story-reel.html",
            "stage": "rough", "target": "review", "format": "mp4",
            "resolution": "portrait", "fps": 30, "quality": "draft",
            "output": rel + "/rough.mp4",
            "variablesFile": rel + "/variables.json",
            "audioRequired": True,
        }
        req = job / "request.json"
        req.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
        # This *technical-only* smoke calls render -c directly because check
        # currently requires a root index.html. Production must continue using
        # the existing bridge's check+receipt gate; do not treat smoke as approval.
        cmd = [str(shutil.which("hyperframes")), "render", "--composition", request["composition"],
               "--output", request["output"], "--quality", "draft",
               "--fps", "30", "--format", "mp4", "--strict-variables",
               "--variables-file", request["variablesFile"]]
        if not args.diagnose:
            cmd.append("--strict")
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=240)
        if proc.returncode != 0:
            print("FAIL direct smoke render in " + str(job) + ": " + proc.stdout[-7000:] + proc.stderr[-7000:], file=sys.stderr)
            return proc.returncode
        output = job / "rough.mp4"
        if not output.is_file():
            print("FAIL smoke output missing", file=sys.stderr)
            return 2
        from vf_hyperframes import probe_output, verify_probe, sha256_file, validate_request
        render_request = validate_request(request)
        probe = verify_probe(render_request, probe_output(output))
        digest = sha256_file(output)
        data = {"backend": "hyperframes", "sha256": digest}
        (job / "technical-smoke.receipt.json").write_text(
            json.dumps({"technicalFixtureOnly": True, "publishAuthorized": False,
                        "sha256": digest, "probe": probe}, indent=2), encoding="utf-8"
        )
        if probe.get("width") != 1080 or probe.get("height") != 1920 or probe.get("audioStreams", 0) < 1:
            print("FAIL smoke media dimensions/audio", file=sys.stderr)
            return 2
        print(json.dumps({
            "technicalFixtureOnly": True,
            "style": args.style,
            "result": "PASS",
            "backend": data.get("backend"),
            "durationSec": probe.get("durationSec"),
            "size": [probe.get("width"), probe.get("height")],
            "audioStreams": probe.get("audioStreams"),
            "renderSha256": data.get("sha256"),
            "publishAuthorized": False,
            "diagnosticOnly": args.diagnose,
            "keptUnder": str(job) if args.keep else None,
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print("FAIL motion smoke host dependency: " + str(exc), file=sys.stderr)
        return 2
    finally:
        if not args.keep:
            shutil.rmtree(job, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
