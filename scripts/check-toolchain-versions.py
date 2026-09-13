#!/usr/bin/env python3
"""Fail closed when version-sensitive media components drift from the canonical manifest."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from vf_toolchain import MANIFEST, component, load_manifest

ROOT = Path(__file__).resolve().parents[1]
AUTH = "packages/vfmcp/TOOLCHAIN-VERSIONS.json"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: str) -> dict:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path} must be object")
    return value


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    manifest = load_manifest()
    policy = manifest.get("policy") or {}
    if policy.get("mode") != "single-source-of-truth" or policy.get("driftBehavior") != "fail-closed":
        fail("toolchain policy must be single-source-of-truth + fail-closed")
    hf = component("hyperframes")
    vs = component("voicestudio")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(hf.get("version") or "")):
        fail("HyperFrames version must be exact semver")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(vs.get("version") or "")):
        fail("VoiceStudio version must be exact semver")
    if not str(vs.get("commit") or ""):
        fail("VoiceStudio release commit pin required")

    hf_cfg = load("packages/vfom/HYPERFRAMES-BACKEND.json")
    sp_cfg = load("packages/vfom/SPEECH-BACKEND.json")
    hosts = load("packages/vfmcp/RENDER-HOSTS.json")
    if (hf_cfg.get("execution") or {}).get("versionAuthority") != AUTH + "#components.hyperframes":
        fail("HyperFrames backend must point at canonical version authority")
    if (sp_cfg.get("execution") or {}).get("versionAuthority") != AUTH + "#components.voicestudio":
        fail("Speech backend must point at canonical version authority")
    routing = hosts.get("routing") or {}
    if routing.get("primaryHost") != "sderot-mac" or routing.get("fallbackHosts") != ["sderot-win"]:
        fail("media host routing must be Mac primary -> Windows fallback")
    if routing.get("stickyPerJob") is not True or routing.get("noParallelExecutionForSameJob") is not True:
        fail("failover must be sticky and forbid duplicate same-job execution")
    if routing.get("qaThresholdsMayNotDegradeOnFallback") is not True:
        fail("fallback may not lower QA")

    for host_id in ("sderot-mac", "sderot-win"):
        host = (hosts.get("hosts") or {}).get(host_id) or {}
        if host.get("toolchainManifest") != AUTH:
            fail(f"{host_id} must point at canonical toolchain manifest")
        if host.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json":
            fail(f"{host_id} render backend mismatch")
        if host.get("speechBackend") != "packages/vfom/SPEECH-BACKEND.json":
            fail(f"{host_id} speech backend mismatch")
        if host.get("route") != "cursor-agent-worker" or host.get("inboundPortRequired") is not False:
            fail(f"{host_id} must reuse outbound Cursor worker route")

    win = hosts["hosts"]["sderot-win"]
    if win.get("platform") != "Windows" or win.get("bootstrap") != "scripts/bootstrap-media-host-windows.ps1":
        fail("Windows fallback bootstrap contract mismatch")
    if (win.get("computePolicy") or {}).get("speech") != "cpu-on-windows-amd":
        fail("Windows AMD speech compute policy must be explicit CPU fallback")
    if win.get("status") not in {"configured_host_smoke_pending", "fallback_ready", "live_verified"}:
        fail("invalid Windows fallback status")

    for name in ("hyperframes", "voicestudio"):
        for dep in component(name).get("dependents", []):
            if not (ROOT / dep).exists():
                fail(f"declared {name} dependent missing: {dep}")

    hf_bridge = text("scripts/vf_hyperframes.py")
    sp_bridge = text("scripts/vf_speech.py")
    mac_boot = text("scripts/bootstrap-hyperframes-host-macos.sh")
    win_boot = text("scripts/bootstrap-media-host-windows.ps1")
    if 'component("hyperframes")' not in hf_bridge:
        fail("HyperFrames bridge is not manifest-driven")
    if 'component("voicestudio")' not in sp_bridge:
        fail("Speech bridge is not manifest-driven")
    if "vf_toolchain.py get components.hyperframes.version" not in mac_boot:
        fail("Mac bootstrap is not manifest-driven")
    if "TOOLCHAIN-VERSIONS.json" not in win_boot or "HyperFramesVersion" not in win_boot or "VoiceVersion" not in win_boot:
        fail("Windows bootstrap is not manifest-driven")

    for path, literal in {
        "packages/vfom/HYPERFRAMES-BACKEND.json": str(hf["version"]),
        "packages/vfom/SPEECH-BACKEND.json": str(vs["version"]),
        "packages/vfmcp/RENDER-HOSTS.json": str(hf["version"]),
    }.items():
        if literal in text(path):
            fail(f"duplicated version literal {literal} outside canonical manifest: {path}")

    print(f"OK toolchain authority={MANIFEST.relative_to(ROOT)} hyperframes={hf['version']} voicestudio={vs['version']} hosts=mac>win drift=fail-closed")


if __name__ == "__main__":
    main()
