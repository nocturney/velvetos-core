#!/usr/bin/env python3
"""Validate the vfom HyperFrames backend + canonical Edge render-host contract. No network. No render. No send."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "packages" / "vfom"
CONFIG, SCHEMA, POLICY, FRAME, FOUNDRY, EDIT = [P / n for n in (
    "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "HYPERFRAMES-BACKEND.md",
    "HYPERFRAMES-FRAME.md", "FOUNDRY.json", "EDIT-DIRECTOR.md")]
BRIDGE = ROOT / "scripts" / "vf_hyperframes.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-hyperframes-host-macos.sh"
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
    if cfg.get("noSecondRuntime") is not True: fail("backend must not be second runtime")
    if exe.get("layer") != "edge-or-office-host" or exe.get("bridge") != "scripts/vf_hyperframes.py": fail("execution layer/bridge mismatch")
    version = str(exe.get("packageVersion") or "")
    if exe.get("package") != "hyperframes" or not re.fullmatch(r"\d+\.\d+\.\d+", version): fail("exact HyperFrames pin required")
    if exe.get("networkInstallAllowed") is not False or exe.get("versionMismatch") != "fail": fail("render execution must fail closed")
    if set(exe.get("requires") or []) != {"hyperframes", "ffmpeg", "ffprobe"}: fail("render host requirements mismatch")
    if exe.get("hostRegistry") != "packages/vfmcp/RENDER-HOSTS.json": fail("render host registry path mismatch")
    if exe.get("defaultHost") != "sderot-mac": fail("default render host must be sderot-mac")
    if exe.get("hostConnectPlaybook") != "packages/vfmcp/CONNECT-RENDER-HOST.md": fail("render host connect playbook mismatch")
    if route.get("primary") != "hyperframes" or "ffmpeg-svg-caption-composition" not in set(route.get("fallback") or []): fail("primary/fallback routing invalid")
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
    services = set((foundry.get("layers") or {}).get("deterministicServices") or [])
    if not {"hyperframes-video-composition","ffmpeg-svg-caption-composition","render-receipt-verification"}.issubset(services): fail("Foundry deterministic render services incomplete")

    hosts = load(HOST_REGISTRY)
    if hosts.get("defaultRenderHost") != "sderot-mac": fail("host registry defaultRenderHost mismatch")
    host = (hosts.get("hosts") or {}).get("sderot-mac") or {}
    if host.get("displayName") != "Mac-Office" or host.get("platform") != "macOS" or host.get("workerName") != "sderot-mac": fail("canonical Mac render host identity mismatch")
    if host.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json": fail("host render backend mismatch")
    if host.get("bootstrap") != "scripts/bootstrap-hyperframes-host-macos.sh": fail("host bootstrap path mismatch")
    if host.get("hyperframesVersion") != version: fail("host HyperFrames pin must match backend pin")
    if host.get("route") != "cursor-agent-worker" or host.get("inboundPortRequired") is not False: fail("host route must reuse Cursor worker with no inbound port")
    status = host.get("status")
    if status not in {"configured_host_smoke_pending", "host_smoke_verified", "live_verified"}: fail("host status invalid")
    if status == "host_smoke_verified":
        pending = set(host.get("productionPromotionPending") or [])
        required_pending = {"approved_media_vault_asset_render_and_existing_qa", "intentional_hyperframes_failure_and_ffmpeg_failover_verification"}
        if pending != required_pending: fail("host_smoke_verified must keep explicit production promotion gates")
        if not str(host.get("verifiedEvidence") or "").strip(): fail("host_smoke_verified requires verifiedEvidence")
    if "video-render-host" not in set(host.get("roles") or []): fail("sderot-mac missing video-render-host role")

    policy = contains(POLICY, "not a second orchestrator", "ffmpeg-svg-caption-composition", "ffprobe receipt", "render receipt", "vfcopy", "RTL")
    contains(FRAME, "portrait 9:16", "explicit RTL", "Do not invent font", "Subject lock", "Evaluation Engine")
    contains(EDIT, "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "vf_hyperframes.py plan", "ffmpeg-svg-caption-composition")
    bridge = contains(BRIDGE, f'HYPERFRAMES_VERSION = "{version}"', 'HYPERFRAMES_PACKAGE = f"hyperframes@{HYPERFRAMES_VERSION}"', 'SUPPORTED_STAGES = {"rough", "review", "final"}', 'shutil.which("hyperframes")', '"--strict-all"', '"ffprobe"', '"sha256"', '"audioRequired"')
    if "npx" in bridge or "shell=True" in bridge: fail("bridge must not download via npx or use shell=True")
    bootstrap = contains(BOOTSTRAP, f'HYPERFRAMES_VERSION="{version}"', 'HOST_ID="sderot-mac"', 'HYPERFRAMES_NO_UPDATE_CHECK=1', 'HYPERFRAMES_NO_AUTO_INSTALL=1', 'hyperframes browser ensure', 'python3 scripts/vf_hyperframes.py doctor', 'python3 scripts/vf_hyperframes.py run', 'data-no-timeline', 'dir="rtl"', 'STATE_DIR="$HOME/.velvetos"', 'agent worker --name')
    if '<html lang="he" dir="rtl">' in bootstrap: fail("RTL must not be set on html in HyperFrames smoke render")
    if "ngrok" in bootstrap or "--share-desktop" in bootstrap: fail("render host bootstrap must not create an extra remote tunnel/desktop route")
    shell_check = subprocess.run(["bash", "-n", str(BOOTSTRAP)], text=True, capture_output=True)
    if shell_check.returncode != 0: fail(f"render host bootstrap shell syntax invalid: {shell_check.stderr.strip()}")
    contains(HOST_PLAYBOOK, "sderot-mac", "bootstrap-hyperframes-host-macos.sh --start-worker", "No inbound port", "host_smoke_verified")
    contains(SKILL, "HYPERFRAMES-BACKEND.json", "vf_hyperframes.py", "HyperFrames", "ffmpeg-svg-caption-composition")
    if "A render receipt proves a file was produced" not in policy: fail("render/publish receipt boundary missing")
    print(f"OK hyperframes backend pinned={version} host=sderot-mac status={status} offline+primary+fallback+rtl+receipt+wired")

if __name__ == "__main__": main()
