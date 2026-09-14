#!/usr/bin/env python3
"""Validate video editing/animation adapters. No network, render, or publish."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "packages" / "vfom"
CONFIG = P / "VIDEO-TOOLCHAIN.json"
SCHEMA = P / "EDIT-EDL.schema.json"
DOC = P / "VIDEO-TOOLCHAIN.md"
FOUNDRY = P / "FOUNDRY.json"
EDIT = P / "EDIT-DIRECTOR.md"
BRIDGE = ROOT / "scripts" / "vf_video_edit.py"
MANIM_BOOTSTRAP = ROOT / "scripts" / "bootstrap-manim-host-windows.ps1"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be an object")
    return value


def contains(path: Path, *needles: str) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def main() -> None:
    cfg = load(CONFIG)
    if cfg.get("noSecondRuntime") is not True:
        fail("video toolchain must not create a second runtime")
    if cfg.get("masterComposer") != "hyperframes":
        fail("HyperFrames must remain master composer")
    if cfg.get("finalAuthority") != "packages/vfom/HYPERFRAMES-BACKEND.json":
        fail("HyperFrames final authority missing")

    edit = cfg.get("editIntelligence") or {}
    if edit.get("origin") != "https://github.com/browser-use/video-use":
        fail("video-use origin mismatch")
    if edit.get("integration") != "pattern-adapted-not-vendored" or edit.get("status") != "implemented":
        fail("video-use adapter status mismatch")
    if edit.get("bridge") != "scripts/vf_video_edit.py":
        fail("video-use bridge mismatch")
    if edit.get("requestSchema") != "packages/vfom/EDIT-EDL.schema.json":
        fail("video-use schema mismatch")
    required = {
        "audio-first-edl", "word-boundary-cut-contract", "30ms-audio-fades",
        "deterministic-base-cut", "render-receipt", "boundary-inspection",
    }
    if not required.issubset(set(edit.get("features") or [])):
        fail("video-use features incomplete")
    if (edit.get("transcription") or {}).get("hardDependencyOnElevenLabs") is not False:
        fail("ElevenLabs must not become a hard dependency")
    if int((edit.get("selfEvaluation") or {}).get("maxPasses", 99)) > 3:
        fail("video self-evaluation must stay bounded")

    slots = cfg.get("animationSlots") or {}
    if (slots.get("hyperframes") or {}).get("status") != "canonical":
        fail("HyperFrames animation slot must stay canonical")
    remotion = slots.get("remotion") or {}
    if remotion.get("version") != "4.0.523" or remotion.get("status") != "license-gated":
        fail("Remotion pin/status mismatch")
    if remotion.get("installByDefault") is not False or remotion.get("masterRenderer") is not False:
        fail("Remotion must remain optional and subordinate")

    manim = slots.get("manim") or {}
    if manim.get("version") != "0.21.0" or manim.get("license") != "MIT":
        fail("Manim pin/license mismatch")
    if manim.get("status") != "host-smoke-verified":
        fail("Manim must carry real host smoke evidence before verified status")
    if manim.get("masterRenderer") is not False:
        fail("Manim must not become master renderer")
    if manim.get("bootstrap") != "scripts/bootstrap-manim-host-windows.ps1":
        fail("Manim bootstrap wiring missing")
    evidence = manim.get("hostEvidence") or {}
    if evidence.get("host") != "sderot-windows" or evidence.get("python") != "3.12":
        fail("Manim host evidence identity mismatch")
    if len(str(evidence.get("sha256") or "")) != 64:
        fail("Manim smoke SHA-256 evidence missing")
    forbidden = {"physical-product-proof", "customer-result-proof", "stress-test-proof"}
    if not forbidden.issubset(set(manim.get("forbiddenAs") or [])):
        fail("Manim proof boundary incomplete")

    guards = cfg.get("guardrails") or {}
    for key in (
        "mediaVaultRemainsSourceOfTruth", "contentContractRemainsAuthority",
        "claimProvenanceRemainsAuthority", "noGeneratedAssetProvesPhysicalClaim",
        "hebrewVisualTextUsesDeterministicOverlay", "renderReceiptIsNotPublishReceipt",
        "noRuntimeAutoInstallDuringContentJob",
    ):
        if guards.get(key) is not True:
            fail(f"guardrail {key} must be true")

    schema = load(SCHEMA)
    props = schema.get("properties") or {}
    required_fields = {"jobId", "projectDir", "output", "segments"}
    if not required_fields.issubset(set(schema.get("required") or [])):
        fail("EDL schema required fields incomplete")
    if set((props.get("cutPolicy") or {}).get("enum") or []) != {"word-boundary", "visual-only"}:
        fail("EDL cut policies invalid")
    if (props.get("audioFadeSeconds") or {}).get("default") != 0.03:
        fail("EDL default audio fade must be 30ms")

    foundry = load(FOUNDRY)
    shared = foundry.get("sharedAuthorities") or {}
    if shared.get("videoToolchain") != "packages/vfom/VIDEO-TOOLCHAIN.json":
        fail("Foundry video toolchain authority missing")
    if shared.get("editDecisionListSchema") != "packages/vfom/EDIT-EDL.schema.json":
        fail("Foundry EDL schema authority missing")
    services = set((foundry.get("layers") or {}).get("deterministicServices") or [])
    if "deterministic-base-edit" not in services:
        fail("Foundry deterministic base edit service missing")
    if (foundry.get("renderBackend") or {}).get("primary") != "hyperframes":
        fail("video toolchain must not replace HyperFrames")

    bridge = contains(
        BRIDGE,
        'SUPPORTED_FPS = {24, 25, 30, 50, 60}',
        '"word-boundary"',
        'audioFadeSeconds',
        'ffprobe',
        'sha256',
        'publishReceipt": False',
        'command_inspect',
        'libx264',
        'aac',
    )
    if "shell=True" in bridge:
        fail("edit bridge must not use shell=True")

    manim_bootstrap = contains(
        MANIM_BOOTSTRAP,
        "$MANIM_VERSION = '0.21.0'",
        "$HOST_ID = 'sderot-windows'",
        "manim-host.json",
        "ffprobe",
        "Get-FileHash -Algorithm SHA256",
        "1080",
        "1920",
    )
    if "ngrok" in manim_bootstrap or "--share-desktop" in manim_bootstrap:
        fail("Manim bootstrap must not create an extra remote route")

    contains(
        DOC,
        "pattern-adapted",
        "HyperFrames remains the canonical master compositor",
        "license-gated",
        "Manim",
        "not another editor product",
    )
    contains(EDIT, "VIDEO-TOOLCHAIN.json", "vf_video_edit.py", "HyperFrames remains")
    print(
        "OK video toolchain adapters "
        "edit=implemented remotion=license-gated "
        "manim=host-smoke-verified hyperframes=canonical"
    )


if __name__ == "__main__":
    main()
