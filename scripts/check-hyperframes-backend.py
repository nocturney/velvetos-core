#!/usr/bin/env python3
"""Validate vfom HyperFrames backend + canonical Mac/Windows Edge render-host contract."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

from vf_toolchain import component

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "packages" / "vfom"
CONFIG, SCHEMA, POLICY, FRAME, FOUNDRY, EDIT = [P / n for n in (
    "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "HYPERFRAMES-BACKEND.md",
    "HYPERFRAMES-FRAME.md", "FOUNDRY.json", "EDIT-DIRECTOR.md")]
BRIDGE = ROOT / "scripts" / "vf_hyperframes.py"
MAC_BOOTSTRAP = ROOT / "scripts" / "bootstrap-hyperframes-host-macos.sh"
WIN_BOOTSTRAP = ROOT / "scripts" / "bootstrap-media-host-windows.ps1"
HOST_REGISTRY = ROOT / "packages" / "vfmcp" / "RENDER-HOSTS.json"
HOST_PLAYBOOK = ROOT / "packages" / "vfmcp" / "CONNECT-RENDER-HOST.md"
SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr); raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file(): fail(f"missing {path.relative_to(ROOT)}")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict): fail(f"{path.relative_to(ROOT)} must be object")
    return value


def contains(path: Path, *needles: str) -> str:
    if not path.is_file(): fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text: fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def main() -> None:
    cfg = load(CONFIG); exe = cfg.get("execution") or {}; route = cfg.get("routing") or {}; defaults = cfg.get("defaults") or {}
    version = str(component("hyperframes")["version"])
    if cfg.get("noSecondRuntime") is not True: fail("backend must not be second runtime")
    if exe.get("layer") != "edge-or-office-host" or exe.get("bridge") != "scripts/vf_hyperframes.py": fail("execution layer/bridge mismatch")
    if exe.get("package") != "hyperframes": fail("HyperFrames package identity required")
    if exe.get("versionAuthority") != "packages/vfmcp/TOOLCHAIN-VERSIONS.json#components.hyperframes": fail("HyperFrames version authority mismatch")
    if exe.get("networkInstallAllowed") is not False or exe.get("versionMismatch") != "fail": fail("render execution must fail closed")
    if set(exe.get("requires") or []) != {"hyperframes", "ffmpeg", "ffprobe"}: fail("render host requirements mismatch")
    if exe.get("hostRegistry") != "packages/vfmcp/RENDER-HOSTS.json": fail("render host registry path mismatch")
    if exe.get("defaultHost") != "sderot-mac" or exe.get("fallbackHosts") != ["sderot-win"]: fail("render host primary/fallback mismatch")
    hf_failover = exe.get("hostFailover") or {}
    if hf_failover.get("trigger") != "host_unreachable_or_doctor_failure" or hf_failover.get("stickyPerJob") is not True or hf_failover.get("noParallelSameJob") is not True or hf_failover.get("fallbackMayNotLowerQa") is not True:
        fail("render failover contract invalid")
    if route.get("primary") != "hyperframes" or "ffmpeg-svg-caption-composition" not in set(route.get("fallback") or []): fail("primary/fallback backend routing invalid")
    if defaults.get("masterResolution") != "portrait" or defaults.get("masterFormat") != "mp4" or defaults.get("finalQuality") != "high" or defaults.get("strictFinal") is not True: fail("final master defaults invalid")
    if int(defaults.get("maxFinalRenders", 99)) > 2: fail("maxFinalRenders must stay <=2")
    for key in ("realMediaRefsOnly","noInventedAssets","noAIHebrewInsideFootage","hebrewAsDeterministicOverlay","verifiedBrandFontsOnly","verifiedBrandColorsOnly","finalRequiresCheck","finalRequiresReceipt","finalRequiresExistingQA","receiptIsNotPublishReceipt","renderDoesNotAuthorizePublish"):
        if (cfg.get("guardrails") or {}).get(key) is not True: fail(f"guardrail {key} must be true")

    schema = load(SCHEMA); props = schema.get("properties") or {}
    if not {"jobId","backend","projectDir","output"}.issubset(set(schema.get("required") or [])): fail("render request required fields incomplete")
    if (props.get("backend") or {}).get("const") != "hyperframes" or set((props.get("stage") or {}).get("enum") or []) != {"rough","review","final"}: fail("render request backend/stages invalid")

    foundry = load(FOUNDRY); shared = foundry.get("sharedAuthorities") or {}; rb = foundry.get("renderBackend") or {}
    if shared.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json": fail("Foundry render authority missing")
    if rb.get("primary") != "hyperframes" or rb.get("fallback") != "ffmpeg-svg-caption-composition" or rb.get("renderReceiptIsPublishReceipt") is not False: fail("Foundry render routing/receipt boundary invalid")

    hosts = load(HOST_REGISTRY)
    routing = hosts.get("routing") or {}
    if hosts.get("defaultRenderHost") != "sderot-mac" or routing.get("primaryHost") != "sderot-mac" or routing.get("fallbackHosts") != ["sderot-win"]: fail("host registry routing mismatch")
    if routing.get("stickyPerJob") is not True or routing.get("noParallelExecutionForSameJob") is not True or routing.get("qaThresholdsMayNotDegradeOnFallback") is not True: fail("host failover safety contract invalid")

    mac = (hosts.get("hosts") or {}).get("sderot-mac") or {}
    win = (hosts.get("hosts") or {}).get("sderot-win") or {}
    if mac.get("displayName") != "Mac-Office" or mac.get("platform") != "macOS" or mac.get("workerName") != "sderot-mac": fail("canonical Mac host identity mismatch")
    if win.get("platform") != "Windows" or win.get("workerName") != "sderot-win" or "fallback-host" not in set(win.get("roles") or []): fail("canonical Windows fallback identity mismatch")
    for host_id, host in (("sderot-mac", mac), ("sderot-win", win)):
        if host.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json": fail(f"{host_id} render backend mismatch")
        if host.get("toolchainManifest") != "packages/vfmcp/TOOLCHAIN-VERSIONS.json": fail(f"{host_id} toolchain manifest mismatch")
        if host.get("route") != "cursor-agent-worker" or host.get("inboundPortRequired") is not False: fail(f"{host_id} route must be outbound Cursor worker")
    if mac.get("bootstrap") != "scripts/bootstrap-hyperframes-host-macos.sh": fail("Mac bootstrap mismatch")
    if win.get("bootstrap") != "scripts/bootstrap-media-host-windows.ps1": fail("Windows bootstrap mismatch")
    if (win.get("computePolicy") or {}).get("speech") != "cpu-on-windows-amd": fail("Windows AMD speech fallback must be CPU")
    if mac.get("status") not in {"configured_host_smoke_pending", "host_smoke_verified", "live_verified"}: fail("Mac host status invalid")
    if win.get("status") not in {"configured_host_smoke_pending", "fallback_ready", "live_verified"}: fail("Windows host status invalid")

    policy = contains(POLICY, "not a second orchestrator", "ffmpeg-svg-caption-composition", "ffprobe receipt", "render receipt", "vfcopy", "RTL")
    contains(FRAME, "portrait 9:16", "explicit RTL", "Do not invent font", "Subject lock", "Evaluation Engine")
    contains(EDIT, "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "vf_hyperframes.py plan", "ffmpeg-svg-caption-composition")
    bridge = contains(BRIDGE, 'component("hyperframes")', 'HYPERFRAMES_VERSION = str(_HF["version"])', 'SUPPORTED_STAGES = {"rough", "review", "final"}', 'shutil.which("hyperframes")', '"ffprobe"', '"sha256"', '"audioRequired"')
    if "npx" in bridge or "shell=True" in bridge: fail("bridge must not download via npx or use shell=True")
    mac_boot = contains(MAC_BOOTSTRAP, 'vf_toolchain.py get components.hyperframes.version', 'HOST_ID="sderot-mac"', 'HYPERFRAMES_NO_UPDATE_CHECK=1', 'HYPERFRAMES_NO_AUTO_INSTALL=1', 'hyperframes browser ensure', 'python3 scripts/vf_hyperframes.py run', 'data-no-timeline', 'dir="rtl"', 'agent worker --name')
    if '<html lang="he" dir="rtl">' in mac_boot: fail("RTL must not be set on html in HyperFrames smoke render")
    contains(WIN_BOOTSTRAP, "$HostId = 'sderot-win'", "TOOLCHAIN-VERSIONS.json", "hyperframes browser ensure", "scripts/vf_hyperframes.py run", "scripts/vf_speech.py doctor", "agent worker --name $HostId start")
    shell_check = subprocess.run(["bash", "-n", str(MAC_BOOTSTRAP)], text=True, capture_output=True)
    if shell_check.returncode != 0: fail(f"Mac bootstrap shell syntax invalid: {shell_check.stderr.strip()}")
    contains(HOST_PLAYBOOK, "sderot-mac")
    contains(SKILL, "HYPERFRAMES-BACKEND.json", "vf_hyperframes.py", "HyperFrames", "ffmpeg-svg-caption-composition")
    if "A render receipt proves a file was produced" not in policy: fail("render/publish receipt boundary missing")
    print(f"OK hyperframes backend pinned={version} hosts=sderot-mac>sderot-win failover+rtl+receipt+wired")

if __name__ == "__main__": main()
