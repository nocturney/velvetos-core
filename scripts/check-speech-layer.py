#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

from vf_toolchain import component

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "packages/vfom/SPEECH-BACKEND.json",
    ROOT / "scripts/vf_speech.py",
    ROOT / "scripts/bootstrap-speech-host-macos.sh",
    ROOT / "scripts/bootstrap-media-host-windows.ps1",
]
for path in required:
    if not path.exists():
        raise SystemExit(f"FAIL missing {path.relative_to(ROOT)}")
config = json.loads((ROOT / "packages/vfom/SPEECH-BACKEND.json").read_text(encoding="utf-8"))
assert config["execution"]["defaultHost"] == "sderot-mac"
assert config["execution"]["fallbackHosts"] == ["sderot-win"]
assert config["execution"]["versionAuthority"] == "packages/vfmcp/TOOLCHAIN-VERSIONS.json#components.voicestudio"
assert config["execution"]["failover"]["stickyPerJob"] is True
assert config["execution"]["failover"]["fallbackMayNotLowerQa"] is True
assert component("voicestudio")["version"]
assert "omnivoice" in config["engines"]["ttsForbiddenForCommercialPublish"]
assert config["engines"]["ttsPreferred"][0] == "moss-tts-nano"
assert "faster-whisper" in config["engines"]["asrPreferredOnWindowsAmd"]
assert config["guardrails"]["qaFailClosed"] is True
print("OK speech layer hosts=sderot-mac>sderot-win qa=fail-closed")
