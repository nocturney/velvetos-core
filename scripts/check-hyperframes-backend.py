#!/usr/bin/env python3
"""Validate the vfom HyperFrames backend contract. No network. No render. No send."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "packages" / "vfom"
CONFIG, SCHEMA, POLICY, FRAME, FOUNDRY, EDIT = [P / n for n in (
    "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "HYPERFRAMES-BACKEND.md",
    "HYPERFRAMES-FRAME.md", "FOUNDRY.json", "EDIT-DIRECTOR.md")]
BRIDGE = ROOT / "scripts" / "vf_hyperframes.py"
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

    policy = contains(POLICY, "not a second orchestrator", "ffmpeg-svg-caption-composition", "ffprobe receipt", "render receipt", "vfcopy", "RTL")
    contains(FRAME, "portrait 9:16", "explicit RTL", "Do not invent font", "Subject lock", "Evaluation Engine")
    contains(EDIT, "HYPERFRAMES-BACKEND.json", "HYPERFRAMES-RENDER.schema.json", "vf_hyperframes.py plan", "ffmpeg-svg-caption-composition")
    bridge = contains(BRIDGE, f'HYPERFRAMES_VERSION = "{version}"', 'HYPERFRAMES_PACKAGE = f"hyperframes@{HYPERFRAMES_VERSION}"', 'SUPPORTED_STAGES = {"rough", "review", "final"}', 'shutil.which("hyperframes")', '"--strict-all"', '"ffprobe"', '"sha256"', '"audioRequired"')
    if "npx" in bridge or "shell=True" in bridge: fail("bridge must not download via npx or use shell=True")
    contains(SKILL, "HYPERFRAMES-BACKEND.json", "vf_hyperframes.py", "HyperFrames", "ffmpeg-svg-caption-composition")
    if "A render receipt proves a file was produced" not in policy: fail("render/publish receipt boundary missing")
    print(f"OK hyperframes backend pinned={version} offline+primary+fallback+rtl+receipt+wired")

if __name__ == "__main__": main()
