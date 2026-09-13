#!/usr/bin/env python3
"""Validate HyperFrames + canonical Mac/Windows Edge render-host failover. No network/render/send."""
from __future__ import annotations
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "packages" / "vfom"
CONFIG, SCHEMA, POLICY, FRAME, FOUNDRY, EDIT = [P / n for n in (
    "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "HYPERFRAMES-BACKEND.md",
    "HYPERFRAMES-FRAME.md", "FOUNDRY.json", "EDIT-DIRECTOR.md")]
BRIDGE = ROOT / "scripts" / "vf_hyperframes.py"
MAC_BOOTSTRAP = ROOT / "scripts" / "bootstrap-hyperframes-host-macos.sh"
WINDOWS_BOOTSTRAP = ROOT / "scripts" / "bootstrap-edge-host-windows.ps1"
HOST_REGISTRY = ROOT / "packages" / "vfmcp" / "RENDER-HOSTS.json"
MAC_PLAYBOOK = ROOT / "packages" / "vfmcp" / "CONNECT-RENDER-HOST.md"
WINDOWS_PLAYBOOK = ROOT / "packages" / "vfmcp" / "WINDOWS-EDGE-FALLBACK.md"
SKILL = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be object")
    return value


def contains(path: Path, *needles: str) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def check_common_host(host: dict, *, host_id: str, platform: str, version: str) -> None:
    if host.get("workerName") != host_id or host.get("platform") != platform:
        fail(f"{host_id} identity/platform mismatch")
    if host.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json":
        fail(f"{host_id} render backend mismatch")
    if host.get("hyperframesVersion") != version:
        fail(f"{host_id} HyperFrames pin mismatch")
    if host.get("inboundPortRequired") is not False:
        fail(f"{host_id} must require no inbound port")
    if "video-render-host" not in set(host.get("roles") or []):
        fail(f"{host_id} missing video-render-host role")


def main() -> None:
    cfg = load(CONFIG)
    exe = cfg.get("execution") or {}
    route = cfg.get("routing") or {}
    defaults = cfg.get("defaults") or {}

    if cfg.get("noSecondRuntime") is not True:
        fail("backend must not be second runtime")
    if exe.get("layer") != "edge-or-office-host" or exe.get("bridge") != "scripts/vf_hyperframes.py":
        fail("execution layer/bridge mismatch")
    version = str(exe.get("packageVersion") or "")
    if exe.get("package") != "hyperframes" or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("exact HyperFrames pin required")
    if exe.get("networkInstallAllowed") is not False or exe.get("versionMismatch") != "fail":
        fail("render execution must fail closed")
    if set(exe.get("requires") or []) != {"hyperframes", "ffmpeg", "ffprobe"}:
        fail("render host requirements mismatch")
    if exe.get("hostRegistry") != "packages/vfmcp/RENDER-HOSTS.json":
        fail("render host registry path mismatch")
    if exe.get("defaultHost") != "sderot-mac":
        fail("default render host must stay sderot-mac")
    if exe.get("fallbackHosts") != ["sderot-windows"]:
        fail("Windows fallback host missing from backend execution contract")
    if exe.get("hostSelection") != "first-healthy":
        fail("backend hostSelection must use canonical first-healthy routing")
    if route.get("hostFailover") != ["sderot-mac", "sderot-windows"]:
        fail("backend hostFailover order mismatch")
    if exe.get("hostConnectPlaybook") != "packages/vfmcp/CONNECT-RENDER-HOST.md":
        fail("render host connect playbook mismatch")
    if route.get("primary") != "hyperframes" or "ffmpeg-svg-caption-composition" not in set(route.get("fallback") or []):
        fail("primary/fallback routing invalid")
    if defaults.get("masterResolution") != "portrait" or defaults.get("masterFormat") != "mp4" or defaults.get("finalQuality") != "high" or defaults.get("strictFinal") is not True:
        fail("final master defaults invalid")
    if int(defaults.get("maxFinalRenders", 99)) > 2:
        fail("maxFinalRenders must stay <=2")
    for key in ("realMediaRefsOnly", "noInventedAssets", "noAIHebrewInsideFootage", "hebrewAsDeterministicOverlay", "verifiedBrandFontsOnly", "verifiedBrandColorsOnly", "finalRequiresCheck", "finalRequiresReceipt", "finalRequiresExistingQA", "receiptIsNotPublishReceipt", "renderDoesNotAuthorizePublish"):
        if (cfg.get("guardrails") or {}).get(key) is not True:
            fail(f"guardrail {key} must be true")

    schema = load(SCHEMA)
    props = schema.get("properties") or {}
    if not {"jobId", "backend", "projectDir", "output"}.issubset(set(schema.get("required") or [])):
        fail("render request required fields incomplete")
    if (props.get("backend") or {}).get("const") != "hyperframes" or set((props.get("stage") or {}).get("enum") or []) != {"rough", "review", "final"}:
        fail("render request backend/stages invalid")

    foundry = load(FOUNDRY)
    shared = foundry.get("sharedAuthorities") or {}
    rb = foundry.get("renderBackend") or {}
    if shared.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json":
        fail("Foundry render authority missing")
    if rb.get("primary") != "hyperframes" or rb.get("fallback") != "ffmpeg-svg-caption-composition" or rb.get("renderReceiptIsPublishReceipt") is not False:
        fail("Foundry render routing/receipt boundary invalid")
    services = set((foundry.get("layers") or {}).get("deterministicServices") or [])
    if not {"hyperframes-video-composition", "ffmpeg-svg-caption-composition", "render-receipt-verification"}.issubset(services):
        fail("Foundry deterministic render services incomplete")

    hosts = load(HOST_REGISTRY)
    routing = hosts.get("routing") or {}
    host_map = hosts.get("hosts") or {}
    if hosts.get("defaultRenderHost") != "sderot-mac":
        fail("host registry defaultRenderHost mismatch")
    if routing.get("mode") != "first-healthy" or routing.get("preferred") != "sderot-mac" or routing.get("fallbackOrder") != ["sderot-windows"]:
        fail("canonical Mac->Windows first-healthy routing mismatch")
    if set(routing.get("eligibleStatuses") or []) != {"host_smoke_verified", "live_verified"}:
        fail("render fallback must be limited to verified host statuses")
    health_rule = str(routing.get("healthRule") or "")
    for word in ("registered", "online", "repo-synced", "bootstrap/doctor", "render-smoke receipt"):
        if word not in health_rule:
            fail(f"host healthRule missing {word!r}")
    if not {"host_offline", "route_unreachable", "host_doctor_failed", "host_smoke_missing"}.issubset(set(routing.get("failoverOn") or [])):
        fail("host failover triggers incomplete")
    if not {"content_contract_failure", "policy_failure", "rights_failure", "qa_failure"}.issubset(set(routing.get("doNotFailoverOn") or [])):
        fail("host failover must not bypass content/policy/rights/QA failures")
    if "never copy cookies" not in str(routing.get("subscriptionRule") or ""):
        fail("subscription credential isolation rule missing")
    if "never relaxes" not in str(routing.get("qualityRule") or ""):
        fail("host failover QA boundary missing")

    mac = host_map.get("sderot-mac") or {}
    windows = host_map.get("sderot-windows") or {}
    check_common_host(mac, host_id="sderot-mac", platform="macOS", version=version)
    check_common_host(windows, host_id="sderot-windows", platform="Windows", version=version)

    if mac.get("displayName") != "Mac-Office" or mac.get("bootstrap") != "scripts/bootstrap-hyperframes-host-macos.sh" or mac.get("route") != "cursor-agent-worker":
        fail("canonical Mac render host contract mismatch")
    mac_status = mac.get("status")
    if mac_status not in {"configured_host_smoke_pending", "host_smoke_verified", "live_verified"}:
        fail("Mac host status invalid")
    if mac_status == "host_smoke_verified":
        pending = set(mac.get("productionPromotionPending") or [])
        required_pending = {"approved_media_vault_asset_render_and_existing_qa", "intentional_hyperframes_failure_and_ffmpeg_failover_verification"}
        if pending != required_pending or not str(mac.get("verifiedEvidence") or "").strip():
            fail("Mac host_smoke_verified evidence/promotion gates invalid")

    if windows.get("displayName") != "Windows-Fallback":
        fail("Windows fallback display identity mismatch")
    if windows.get("bootstrap") != "scripts/bootstrap-edge-host-windows.ps1":
        fail("Windows fallback bootstrap path mismatch")
    if windows.get("route") != "remote-desktop-commander":
        fail("Windows fallback must use existing Remote Desktop Commander route")
    if windows.get("subscriptionHost") is not False or windows.get("computerUse") is not False:
        fail("Windows fallback must not become subscription/computer-use host")
    if not {"repo-worker", "content-worker", "speech-render-host"}.issubset(set(windows.get("roles") or [])):
        fail("Windows fallback operational roles incomplete")
    windows_status = windows.get("status")
    if windows_status not in {"configured_pending_device_registration", "host_smoke_verified", "live_verified"}:
        fail("Windows fallback status invalid")
    promotion = set(windows.get("productionPromotionPending") or [])
    if windows_status == "configured_pending_device_registration":
        if windows.get("verifiedEvidence") is not None:
            fail("unverified Windows host must not carry verifiedEvidence")
        required = {"remote_desktop_commander_device_online", "windows_bootstrap_doctor_and_smoke_receipt", "repo_synced"}
        if not required.issubset(promotion):
            fail("Windows fallback promotion evidence incomplete")
    else:
        if not str(windows.get("verifiedEvidence") or "").strip():
            fail("verified Windows host requires verifiedEvidence")
        required = {"approved_media_vault_asset_render_and_existing_qa", "intentional_hyperframes_failure_and_ffmpeg_failover_verification"}
        if promotion != required:
            fail("verified Windows host must retain full-backend production promotion gates")

    policy = contains(POLICY, "not a second orchestrator", "ffmpeg-svg-caption-composition", "ffprobe receipt", "render receipt", "vfcopy", "RTL")
    contains(FRAME, "portrait 9:16", "explicit RTL", "Do not invent font", "Subject lock", "Evaluation Engine")
    contains(EDIT, "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "vf_hyperframes.py plan", "ffmpeg-svg-caption-composition")
    bridge = contains(BRIDGE, f'HYPERFRAMES_VERSION = "{version}"', 'HYPERFRAMES_PACKAGE = f"hyperframes@{HYPERFRAMES_VERSION}"', 'SUPPORTED_STAGES = {"rough", "review", "final"}', 'shutil.which("hyperframes")', '"--strict-all"', '"ffprobe"', '"sha256"', '"audioRequired"')
    if "npx" in bridge or "shell=True" in bridge:
        fail("bridge must not download via npx or use shell=True")

    mac_bootstrap = contains(MAC_BOOTSTRAP, f'HYPERFRAMES_VERSION="{version}"', 'HOST_ID="sderot-mac"', 'HYPERFRAMES_NO_UPDATE_CHECK=1', 'HYPERFRAMES_NO_AUTO_INSTALL=1', 'hyperframes browser ensure', 'python3 scripts/vf_hyperframes.py doctor', 'python3 scripts/vf_hyperframes.py run', 'data-no-timeline', 'dir="rtl"', 'STATE_DIR="$HOME/.velvetos"')
    if '<html lang="he" dir="rtl">' in mac_bootstrap:
        fail("RTL must not be set on html root in HyperFrames smoke render")
    if "ngrok" in mac_bootstrap or "--share-desktop" in mac_bootstrap:
        fail("Mac render bootstrap must not create an extra remote route")
    bash = shutil.which("bash")
    if bash:
        shell_check = subprocess.run([bash, "-n", str(MAC_BOOTSTRAP)], text=True, capture_output=True)
        if shell_check.returncode != 0:
            fail(f"Mac render host bootstrap shell syntax invalid: {shell_check.stderr.strip()}")

    windows_bootstrap = contains(
        WINDOWS_BOOTSTRAP,
        '$HostId = "sderot-windows"',
        '$HyperFramesVersion = "0.8.34"',
        '$NodeVersionPin = "22.22.0"',
        '$script:Python = @(Resolve-Python)',
        "Get-FileHash -Algorithm SHA256",
        'HYPERFRAMES_NO_UPDATE_CHECK = "1"',
        'HYPERFRAMES_NO_AUTO_INSTALL = "1"',
        "hyperframes browser ensure",
        'Invoke-Python "scripts/vf_hyperframes.py" "doctor"',
        'Invoke-Python "scripts/vf_hyperframes.py" "plan" $requestPath',
        'Invoke-Python "scripts/vf_hyperframes.py" "run" $requestPath',
        "data-no-timeline",
        'dir="rtl"',
        "smokeReceiptSha256",
        'renderSmoke = "pass"',
        'remoteDesktopCommander = "registration-required"',
        'subscriptionHost = $false',
        'computerUse = $false',
    )
    if '<html lang="he" dir="rtl">' in windows_bootstrap:
        fail("RTL must not be set on html root in Windows HyperFrames smoke")
    for forbidden in ("ngrok", "--computer-use", "--share-desktop"):
        if forbidden in windows_bootstrap:
            fail(f"Windows fallback bootstrap must not contain {forbidden}")

    contains(MAC_PLAYBOOK, "sderot-mac", "bootstrap-hyperframes-host-macos.sh --start-worker", "No inbound port", "host_smoke_verified")
    contains(WINDOWS_PLAYBOOK, "sderot-windows", "Remote Desktop Commander", "renderSmoke=pass", "host_smoke_verified", "render receipt", "2026-09-13")
    contains(SKILL, "HYPERFRAMES-BACKEND.json", "vf_hyperframes.py", "HyperFrames", "ffmpeg-svg-caption-composition")
    if "A render receipt proves a file was produced" not in policy:
        fail("render/publish receipt boundary missing")

    print(
        f"OK hyperframes backend pinned={version} "
        f"hosts=mac:{mac_status},windows:{windows_status} "
        "route=first-healthy verified-only smoke-receipt+qa-boundary+wired"
    )


if __name__ == "__main__":
    main()
