#!/usr/bin/env python3
"""Validate the vfom HyperFrames backend contract. No network. No render. No send."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "packages" / "vfom" / "HYPERFRAMES-BACKEND.json"
SCHEMA = ROOT / "packages" / "vfom" / "HYPERFRAMES-RENDER.schema.json"
POLICY = ROOT / "packages" / "vfom" / "HYPERFRAMES-BACKEND.md"
FRAME = ROOT / "packages" / "vfom" / "HYPERFRAMES-FRAME.md"
FOUNDRY = ROOT / "packages" / "vfom" / "FOUNDRY.json"
EDIT = ROOT / "packages" / "vfom" / "EDIT-DIRECTOR.md"
BRIDGE = ROOT / "scripts" / "vf_hyperframes.py"
SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be an object")
    return value


def must_contain(path: Path, needles: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def main() -> None:
    config = load_json(CONFIG)
    if config.get("noSecondRuntime") is not True:
        fail("HyperFrames backend must remain a backend, not a second runtime")

    execution = config.get("execution") or {}
    if execution.get("layer") != "edge-or-office-host":
        fail("HyperFrames execution must stay on edge-or-office-host")
    if execution.get("bridge") != "scripts/vf_hyperframes.py":
        fail("HyperFrames bridge path mismatch")
    if execution.get("requestSchema") != "packages/vfom/HYPERFRAMES-RENDER.schema.json":
        fail("HyperFrames request schema path mismatch")
    if execution.get("package") != "hyperframes":
        fail("HyperFrames package identity mismatch")
    version = str(execution.get("packageVersion") or "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("HyperFrames packageVersion must be an exact semver pin")
    if execution.get("networkInstallAllowed") is not False:
        fail("backend must not silently install/change HyperFrames at render time")

    routing = config.get("routing") or {}
    if routing.get("primary") != "hyperframes":
        fail("HyperFrames must be the primary configured video renderer")
    if "ffmpeg-svg-caption-composition" not in set(routing.get("fallback") or []):
        fail("existing FFmpeg/SVG fallback must remain configured")

    defaults = config.get("defaults") or {}
    if defaults.get("masterResolution") != "portrait" or defaults.get("masterFormat") != "mp4":
        fail("social master defaults must remain portrait MP4")
    if defaults.get("finalQuality") != "high" or defaults.get("strictFinal") is not True:
        fail("final HyperFrames render must remain high + strict")
    if int(defaults.get("maxFinalRenders", 99)) > 2:
        fail("HyperFrames integration must preserve <=2 final renders")

    guardrails = config.get("guardrails") or {}
    for key in (
        "realMediaRefsOnly",
        "noInventedAssets",
        "noAIHebrewInsideFootage",
        "hebrewAsDeterministicOverlay",
        "verifiedBrandFontsOnly",
        "verifiedBrandColorsOnly",
        "finalRequiresCheck",
        "finalRequiresReceipt",
        "finalRequiresExistingQA",
        "receiptIsNotPublishReceipt",
        "renderDoesNotAuthorizePublish",
    ):
        if guardrails.get(key) is not True:
            fail(f"guardrail {key} must be true")

    schema = load_json(SCHEMA)
    required = set(schema.get("required") or [])
    if not {"jobId", "backend", "projectDir", "output"}.issubset(required):
        fail("render request required fields incomplete")
    props = schema.get("properties") or {}
    if (props.get("backend") or {}).get("const") != "hyperframes":
        fail("request backend must be const hyperframes")
    if set((props.get("stage") or {}).get("enum") or []) != {"rough", "review", "final"}:
        fail("render stage enum mismatch")

    foundry = load_json(FOUNDRY)
    shared = foundry.get("sharedAuthorities") or {}
    if shared.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json":
        fail("FOUNDRY sharedAuthorities.renderBackend must point at HyperFrames contract")
    render_backend = foundry.get("renderBackend") or {}
    if render_backend.get("primary") != "hyperframes":
        fail("FOUNDRY renderBackend.primary must be hyperframes")
    if render_backend.get("fallback") != "ffmpeg-svg-caption-composition":
        fail("FOUNDRY must preserve FFmpeg/SVG fallback")
    if render_backend.get("renderReceiptIsPublishReceipt") is not False:
        fail("FOUNDRY must distinguish render receipt from publish receipt")
    services = set((foundry.get("layers") or {}).get("deterministicServices") or [])
    for service in ("hyperframes-video-composition", "ffmpeg-svg-caption-composition", "render-receipt-verification"):
        if service not in services:
            fail(f"FOUNDRY deterministicServices missing {service}")

    policy = must_contain(POLICY, (
        "not a second orchestrator",
        "ffmpeg-svg-caption-composition",
        "ffprobe receipt",
        "render receipt",
        "vfcopy",
        "RTL",
    ))
    must_contain(FRAME, (
        "portrait 9:16",
        "explicit RTL",
        "Do not invent font",
        "Subject lock",
        "Evaluation Engine",
    ))
    must_contain(EDIT, (
        "HYPERFRAMES-BACKEND.json",
        "HYPERFRAMES-RENDER.schema.json",
        "vf_hyperframes.py plan",
        "ffmpeg-svg-caption-composition",
    ))
    bridge = must_contain(BRIDGE, (
        f'HYPERFRAMES_PACKAGE = "hyperframes@{version}"',
        'SUPPORTED_STAGES = {"rough", "review", "final"}',
        '"--strict-all"',
        '"ffprobe"',
        '"sha256"',
        '"audioRequired"',
    ))
    if "shell=True" in bridge:
        fail("HyperFrames bridge must not use shell=True")

    must_contain(SKILL, (
        "HYPERFRAMES-BACKEND.json",
        "vf_hyperframes.py",
        "HyperFrames",
        "ffmpeg-svg-caption-composition",
    ))
    if "A render receipt proves a file was produced" not in policy:
        fail("policy must distinguish render receipt from publish evidence")

    print(f"OK hyperframes backend pinned={version} primary+fallback+rtl+receipt+wired")


if __name__ == "__main__":
    main()
