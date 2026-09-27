#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "packages" / "vfom" / "SPEECH-BACKEND.json"
HOSTS = ROOT / "packages" / "vfmcp" / "RENDER-HOSTS.json"
ADAPTER = ROOT / "scripts" / "vf_speech.py"
WIN = ROOT / "scripts" / "bootstrap-speech-host-windows.ps1"
WRAPPER = ROOT / "scripts" / "bootstrap-media-host-windows.ps1"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL {message}")


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must be object")
    return data


def require_text(path: Path, *needles: str) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def main() -> None:
    cfg = load(CFG)
    provider = cfg.get("provider") or {}
    routing = cfg.get("routing") or {}
    defaults = cfg.get("defaults") or {}
    engines = cfg.get("engines") or {}
    selection = engines.get("selectionPolicy") or {}
    guards = cfg.get("guardrails") or {}
    if provider.get("name") != "voicestudio":
        fail("VoiceStudio provider identity mismatch")
    minimum = str(provider.get("minimumVersion") or "")
    recovery = str(provider.get("recoveryVersion") or "")
    if provider.get("versionPolicy") != "latest-compatible":
        fail("VoiceStudio must use latest-compatible version policy")
    if not re.fullmatch(r"\d+\.\d+\.\d+", minimum) or not re.fullmatch(r"\d+\.\d+\.\d+", recovery):
        fail("VoiceStudio minimum/recovery versions must be semver")
    if provider.get("compatibilityGate") != "speech-doctor+real-hebrew-tts-stt-smoke":
        fail("VoiceStudio compatibility gate mismatch")
    if provider.get("networkExposure") != "loopback-only":
        fail("VoiceStudio must stay loopback-only")
    if routing.get("preferredHost") != "sderot-mac" or routing.get("fallbackOrder") != ["sderot-windows"]:
        fail("speech routing must be sderot-mac > sderot-windows")
    if routing.get("stickyPerJob") is not True or routing.get("fallbackMayNotLowerQa") is not True:
        fail("speech host failover must be sticky and preserve QA")
    if float(defaults.get("qaMinimumSimilarity", 0)) < 0.9 or defaults.get("qaBackTranscribe") is not True:
        fail("back-transcription QA must remain fail-closed at >=0.9")
    if defaults.get("ttsModelWindows") != "omnivoice":
        fail("Windows speech default must be OmniVoice after Hebrew QA certification")
    if engines.get("ttsForbiddenForCommercialPublish") != []:
        fail("speech routing must not hard-block free tools by commercial positioning")
    for key in ("freeToolsMayBeUsedRegardlessOfCommercialPositioning", "commercialSuitabilityIsNotRuntimeBlocker", "licenseMetadataMustBeTracked"):
        if selection.get(key) is not True:
            fail(f"selection policy {key} must be true")
    if guards.get("commercialModelAllowlistRequired") is not False or guards.get("forbidOmniVoiceForCommercialPublish") is not False:
        fail("commercial-positioning model blockers must stay disabled")
    for key in ("licenseMetadataTracked", "voiceCloneRequiresConsent", "speechReceiptIsNotPublishReceipt", "speechDoesNotAuthorizePublish", "qaFailClosed"):
        if guards.get(key) is not True:
            fail(f"guardrail {key} must be true")

    hosts = load(HOSTS)
    if (hosts.get("routing") or {}).get("fallbackOrder") != ["sderot-windows"]:
        fail("host registry fallback must remain canonical sderot-windows")
    mac = (hosts.get("hosts") or {}).get("sderot-mac") or {}
    win = (hosts.get("hosts") or {}).get("sderot-windows") or {}
    if mac.get("speechBackend") != "packages/vfom/SPEECH-BACKEND.json":
        fail("Mac speech backend not bound")
    if win.get("speechBackend") != "packages/vfom/SPEECH-BACKEND.json":
        fail("Windows speech backend not bound")
    if win.get("bootstrap") != "scripts/bootstrap-edge-host-windows.ps1":
        fail("Windows render bootstrap contract changed")
    if win.get("mediaBootstrap") != "scripts/bootstrap-media-host-windows.ps1" or win.get("speechBootstrap") != "scripts/bootstrap-speech-host-windows.ps1":
        fail("Windows canonical media/speech bootstrap not bound")
    if win.get("route") != "remote-desktop-commander" or win.get("computerUse") is not False:
        fail("Windows must reuse Remote Desktop Commander and stay non-browser-subscription")
    for host_id, host in (("sderot-mac", mac), ("sderot-windows", win)):
        if host.get("voiceStudioKnownGoodVersion") != recovery:
            fail(f"{host_id} VoiceStudio recovery baseline mismatch")
        if host.get("voiceStudioVersionPolicy") != "latest-compatible":
            fail(f"{host_id} VoiceStudio version policy mismatch")
        if host.get("voiceStudioCompatibilityGate") != "speech-doctor+real-hebrew-tts-stt-smoke":
            fail(f"{host_id} VoiceStudio compatibility gate mismatch")
    if win.get("speechStatus") != "speech_smoke_verified":
        fail("Windows speech capability must carry verified Hebrew smoke evidence")
    if win.get("speechPromotionPending") != []:
        fail("Windows speech promotion pending list must be empty after verified smoke")
    if "0.93617" not in str(win.get("speechVerifiedEvidence") or ""):
        fail("Windows speech verified evidence missing certified Hebrew QA similarity")

    adapter = require_text(ADAPTER, "/v1/audio/speech", "/v1/audio/transcriptions", "back-transcription-qa", "SELECTION_POLICY", "provider_compatibility", "providerVersionPolicy", 'sys.stdout.reconfigure(encoding="utf-8"', 'encoding="utf-8-sig"')
    if 'PROVIDER["version"]' in adapter or 'PROVIDER["commit"]' in adapter or '"requiredVersion":' in adapter:
        fail("speech adapter must not exact-pin normal VoiceStudio execution")
    help_check = subprocess.run([sys.executable, str(ADAPTER), "--help"], cwd=ROOT, text=True, capture_output=True, timeout=15)
    if help_check.returncode != 0:
        fail(f"speech adapter import/help failed: {(help_check.stderr or help_check.stdout).strip()[:500]}")
    win_bootstrap = require_text(WIN, "sderot-windows", "VoiceStudio_Current_User_", "latest-compatible", "VoiceStudioMinimumVersion", "VoiceStudioRecoveryVersion", "vf_speech.py", "windows-speech-smoke", "speechSmoke", "/engines/select", "commercialPublish = $false")
    if "Downloading pinned VoiceStudio" in win_bootstrap or "$VoiceStudioVersion =" in win_bootstrap:
        fail("Windows speech bootstrap must not exact-pin normal VoiceStudio execution")
    require_text(WRAPPER, "bootstrap-edge-host-windows.ps1", "bootstrap-speech-host-windows.ps1", "Remote Desktop Commander")
    if "shell=True" in adapter:
        fail("speech adapter must not shell out through shell=True")
    print(f"OK speech layer hosts=sderot-mac>sderot-windows voicestudio_policy=latest-compatible minimum={minimum} recovery={recovery} windows_tts=omnivoice qa=fail-closed")


if __name__ == "__main__":
    main()
