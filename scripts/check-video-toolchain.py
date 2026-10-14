#!/usr/bin/env python3
"""Validate video editing/animation adapters. No network, render, or publish."""
from __future__ import annotations

import json
import re
import subprocess
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
MANIM_MAC_BOOTSTRAP = ROOT / "scripts" / "bootstrap-manim-host-macos.sh"


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
    # Optional pattern-adapted motion library: no new runtime or publication authority.
    motion_slot = slots.get("awesomeAiMotion") or {}
    motion = load(P / "MOTION-LIBRARY.json")
    motion_schema = load(P / "hyperframes/MOTION-STORY-VARIABLES.schema.json")
    hf = load(P / "HYPERFRAMES-BACKEND.json")
    source = motion.get("source") or {}
    revision = source.get("commit") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", str(revision)):
        fail("motion source commit must be an immutable 40-char SHA")
    if source.get("repo") != "https://github.com/gongnyang/awesome-ai-motion":
        fail("motion library upstream origin mismatch")
    if motion.get("masterComposer") != "hyperframes" or motion.get("noSecondRuntime") is not True:
        fail("motion library must remain inside canonical HyperFrames")
    if motion_slot.get("sourceRevision") != revision or motion_slot.get("integration") != "pattern-adapted-not-vendored":
        fail("motion toolchain source pin or integration drift")
    if motion_slot.get("installByDefault") is not False or motion_slot.get("masterRenderer") is not False:
        fail("motion toolchain cannot install or own master render")
    if motion_slot.get("status") != "implemented-candidate-template":
        fail("motion library may only offer candidate route, not publish-ready status")
    if hf.get("execution", {}).get("motionLibrary") != "packages/vfom/MOTION-LIBRARY.json":
        fail("HyperFrames motion library binding drift")
    if hf.get("guardrails", {}).get("motionSourceDoesNotAuthorizePublish") is not True:
        fail("motion cannot authorize publishing")
    if motion_slot.get("configuration") != "packages/vfom/MOTION-LIBRARY.json":
        fail("motion slot must resolve authoritative catalog")
    patterns = motion.get("patterns") or []
    if {row.get("id") for row in patterns} != {"product_reveal", "before_after", "shorts_hook"}:
        fail("motion pattern allowlist changed")
    if len(patterns) != 3:
        fail("motion pattern catalog duplicate/invalid")
    preset_names = {name for row in patterns for name in row.get("gsapPresets", [])}
    if preset_names != {"VF_MOTION_MASK_REVEAL", "VF_MOTION_LIGHT_SWEEP", "VF_MOTION_SPLIT_COMPARE", "VF_MOTION_KINETIC_BEATS"}:
        fail("motion preset selection drift")
    declared = set(motion_schema.get("required") or [])
    if motion_schema.get("additionalProperties") is not False or declared != set((motion_schema.get("properties") or {}).keys()):
        fail("motion variables must be strict and explicit")
    if set((motion_schema["properties"]["motionStyle"] or {}).get("enum") or []) != {row["id"] for row in patterns}:
        fail("motion style enum/catalog mismatch")
    template = contains(
        P / "hyperframes/templates/motion-story-reel.html",
        'id="motion-story-reel"', 'data-width="1080"', 'data-height="1920"',
        'data-fps="30"', 'dir="rtl"', 'data-var-src="heroImage"',
        'data-var-src="comparisonImage"', 'data-var-src="audioFile"',
        'variablesStatus', 'sourceAssetRef', 'comparisonEvidenceRef',
        'VF_MOTION_MASK_REVEAL', 'VF_MOTION_LIGHT_SWEEP',
        'VF_MOTION_SPLIT_COMPARE', 'VF_MOTION_KINETIC_BEATS',
    )
    if 'publish(' in template.lower() or 'window.open(' in template:
        fail("motion template must not attempt publication")
    contains(P / "hyperframes/velvet-reel.js", *sorted(preset_names))
    contains(P / "hyperframes/velvet-reel.css", ".vf-motion-stage", ".vf-motion-sheen", ".vf-motion-beats")
    contains(P / "MOTION-LIBRARY.md", "scripts/vf_motion_plan.py", "instagram.publish", "publicationAuthorized=false")
    contains(P / "EDIT-DIRECTOR.md", "MOTION-LIBRARY.json", "scripts/vf_motion_plan.py")
    contains(P / "MOTION-PRESETS.md", *sorted(preset_names))
    planner = ROOT / "scripts/vf_motion_plan.py"
    if motion_slot.get("selector") != "scripts/vf_motion_plan.py":
        fail("motion planner binding mismatch")
    test = subprocess.run([sys.executable, str(planner), "--self-test"], cwd=ROOT, text=True, capture_output=True, timeout=30)
    if test.returncode:
        fail("motion planner selftest: " + (test.stdout + " " + test.stderr).strip()[:500])

    remotion = slots.get("remotion") or {}
    if remotion.get("versionPolicy") != "latest-compatible" or remotion.get("status") != "free-license-eligible":
        fail("Remotion version policy/status mismatch")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(remotion.get("reviewedBaselineVersion") or "")):
        fail("Remotion reviewed baseline must be semver evidence, not an execution pin")
    if remotion.get("compatibilityGate") != "license-eligibility+adapter-smoke":
        fail("Remotion compatibility/license gate mismatch")
    eligibility = remotion.get("licenseEligibility") or {}
    if eligibility.get("currentVerdict") != "FREE_LICENSE_ELIGIBLE" or eligibility.get("currentBusinessHeadcount") != 1:
        fail("Remotion current Free License eligibility evidence mismatch")
    if eligibility.get("freeLicenseMaxHeadcount") != 3 or eligibility.get("recheckAtHeadcount") != 4:
        fail("Remotion headcount threshold mismatch")
    if eligibility.get("commercialUseAllowed") is not True or eligibility.get("automationAllowed") is not True:
        fail("Remotion Free License capability flags mismatch")
    if remotion.get("installByDefault") is not False or remotion.get("masterRenderer") is not False:
        fail("Remotion must remain optional and subordinate")

    manim = slots.get("manim") or {}
    if manim.get("versionPolicy") != "latest-compatible" or manim.get("license") != "MIT":
        fail("Manim version policy/license mismatch")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manim.get("minimumVersion") or "")):
        fail("Manim minimum version must be semver")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manim.get("recoveryVersion") or "")):
        fail("Manim recovery version must be semver")
    if manim.get("compatibilityGate") != "host-doctor+real-smoke":
        fail("Manim compatibility gate mismatch")
    if manim.get("status") != "host-smoke-verified":
        fail("Manim must carry real host smoke evidence before verified status")
    if manim.get("masterRenderer") is not False:
        fail("Manim must not become master renderer")
    if manim.get("bootstrap") != "scripts/bootstrap-manim-host-windows.ps1":
        fail("Manim Windows bootstrap wiring missing")
    if manim.get("macBootstrap") != "scripts/bootstrap-manim-host-macos.sh":
        fail("Manim macOS bootstrap wiring missing")
    mac_evidence = manim.get("macHostEvidence") or {}
    if mac_evidence.get("host") != "sderot-mac" or mac_evidence.get("python") != "3.12":
        fail("Manim macOS host evidence identity mismatch")
    if len(str(mac_evidence.get("sha256") or "")) != 64:
        fail("Manim macOS smoke SHA-256 evidence missing")
    evidence = manim.get("hostEvidence") or {}
    if evidence.get("host") != "sderot-windows" or evidence.get("python") != "3.12":
        fail("Manim host evidence identity mismatch")
    if len(str(evidence.get("sha256") or "")) != 64:
        fail("Manim smoke SHA-256 evidence missing")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(evidence.get("evidenceVersion") or "")):
        fail("Manim historical smoke evidence version missing")
    if evidence.get("evidenceClass") != "historical-smoke-artifact":
        fail("Manim host evidence must be classified as historical artifact proof")
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
        'cfg["output"].parent.mkdir(parents=True, exist_ok=True)',
    )
    if "shell=True" in bridge:
        fail("edit bridge must not use shell=True")

    manim_bootstrap = contains(
        MANIM_BOOTSTRAP,
        "$MANIM_MINIMUM_VERSION = '0.21.0'",
        "$MANIM_RECOVERY_VERSION = '0.21.0'",
        "$HOST_ID = [Environment]::GetEnvironmentVariable('VELVETOS_HOST_ID')",
        "FAIL VELVETOS_HOST_ID is not set.",
        "policy=latest-compatible",
        "manim-host.json",
        "ffprobe",
        "Get-FileHash -Algorithm SHA256",
        "1080",
        "1920",
    )
    if "$MANIM_VERSION =" in manim_bootstrap or "manim==$MANIM" in manim_bootstrap or "version mismatch: expected" in manim_bootstrap:
        fail("Manim bootstrap must not exact-pin normal execution")
    manim_mac_bootstrap = contains(
        MANIM_MAC_BOOTSTRAP,
        'MANIM_MINIMUM_VERSION="0.21.0"',
        'MANIM_RECOVERY_VERSION="0.21.0"',
        'HOST_ID="sderot-mac"',
        'manim-host.json',
        'ffprobe',
        'shasum -a 256',
        '1080',
        '1920',
    )
    if 'manim==$MANIM' in manim_mac_bootstrap or 'version mismatch: expected' in manim_mac_bootstrap:
        fail("Manim macOS bootstrap must not exact-pin normal execution")
    if "ngrok" in manim_bootstrap or "--share-desktop" in manim_bootstrap:
        fail("Manim bootstrap must not create an extra remote route")

    contains(
        DOC,
        "pattern-adapted",
        "HyperFrames remains the canonical master compositor",
        "Free License",
        "Manim",
        "not another editor product",
    )
    contains(EDIT, "VIDEO-TOOLCHAIN.json", "vf_video_edit.py", "HyperFrames remains")
    print(
        "OK video toolchain adapters "
        "edit=implemented remotion=free-license-eligible "
        "manim=host-smoke-verified hyperframes=canonical "
        "motion=source-pinned-candidate"
    )


if __name__ == "__main__":
    main()
