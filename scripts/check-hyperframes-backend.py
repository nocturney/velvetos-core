#!/usr/bin/env python3
"""Validate HyperFrames + canonical Mac/Windows Edge render-host failover.

Executes the local ffmpeg-svg caption tests when ffmpeg -filters and
ffmpeg -buildconf advertise the required filters and libraries. A missing
capability is SKIP_ENV_MISSING_<CAP>. A missing zoompan filter skips the
caption suite on a local host and fails the sensor when GITHUB_ACTIONS=true,
through ci_skip_failure. The fake-ffmpeg capability tests still run. A render
whose pixels do not match still fails. No network and no send.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
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


def zoompan_suite_action(gap, blocked: str | None) -> str:
    """Missing zoompan skips the caption suite locally.

    ci_skip_failure's line fails the sensor. The fake-ffmpeg capability tests
    still run on a local skip. Any other gap keeps the existing test path.
    blocked is that failure line, or None when the host is not CI.
    """
    token = getattr(gap, "token", None)
    if token != "SKIP_ENV_MISSING_ZOOMPAN":
        return "run"
    if blocked:
        return "fail"
    return "skip"


def prove_zoompan_ci_branches() -> None:
    """Fail the zoompan gap on CI. A local miss still runs the fake-ffmpeg tests.

    The child sets VF_HYPERFRAMES_PROOF so this probe does not call itself.
    """
    if os.environ.get("VF_HYPERFRAMES_PROOF") == "1":
        return
    import stat
    import tempfile

    script = r"""#!/usr/bin/env python3
import sys
args = sys.argv[1:]
if "-filters" in args:
    for name in ("drawtext", "overlay", "afade", "scale", "crop", "format"):
        print(" .. " + name)
    raise SystemExit(0)
if "-buildconf" in args:
    print("--enable-libfribidi")
    print("--enable-libass")
    print("--enable-libharfbuzz")
    print("--enable-libx264")
    raise SystemExit(0)
if "-encoders" in args:
    print(" V..... libx264")
    print(" A..... aac")
    raise SystemExit(0)
raise SystemExit(0)
"""
    root = Path(tempfile.mkdtemp(prefix="vf-zoompan-proof-"))
    try:
        binary = root / "ffmpeg"
        binary.write_text(script, encoding="utf-8")
        binary.chmod(binary.stat().st_mode | stat.S_IEXEC)
        probe = root / "ffprobe"
        probe.write_bytes(binary.read_bytes())
        probe.chmod(binary.stat().st_mode)
        # Windows resolves ffmpeg via PATHEXT (.cmd), not an extensionless file.
        (root / "ffmpeg.cmd").write_text('@python "%~dp0ffmpeg" %*\r\n', encoding="utf-8")
        (root / "ffprobe.cmd").write_text('@python "%~dp0ffprobe" %*\r\n', encoding="utf-8")
        base = os.environ.copy()
        base["VF_HYPERFRAMES_PROOF"] = "1"
        base.pop("VF_FAKE_FFMPEG", None)
        base.pop("VF_FAKE_LOG", None)
        base["PATH"] = str(root) + os.pathsep + base.get("PATH", "")
        ci_env = base.copy()
        ci_env["GITHUB_ACTIONS"] = "true"
        local_env = base.copy()
        local_env.pop("GITHUB_ACTIONS", None)
        here = str(Path(__file__).resolve())
        ci = subprocess.run(
            [sys.executable, here],
            cwd=str(ROOT),
            env=ci_env,
            text=True,
            capture_output=True,
        )
        if ci.returncode == 0 or "FAIL SKIP_ENV_MISSING_ZOOMPAN" not in ci.stderr:
            fail("zoompan gap skipped on CI:\n" + (ci.stdout + ci.stderr)[-2000:])
        if "OK hyperframes" in ci.stdout or "OK ffmpeg capability tests" in ci.stdout:
            fail("zoompan CI failure still ran the capability suites")
        local = subprocess.run(
            [sys.executable, here],
            cwd=str(ROOT),
            env=local_env,
            text=True,
            capture_output=True,
        )
        text = local.stdout + local.stderr
        if local.returncode != 0 or "OK ffmpeg capability tests" not in local.stdout:
            fail("missing zoompan skipped the fake-ffmpeg tests:\n" + text[-2000:])
        if "SKIP_ENV_MISSING_ZOOMPAN" not in local.stdout or "OK hyperframes" not in local.stdout:
            fail("missing zoompan did not skip the caption suite:\n" + text[-2000:])
        if "FAIL SKIP_ENV_MISSING_ZOOMPAN" in local.stderr:
            fail("local zoompan gap failed the sensor")
    finally:
        shutil.rmtree(root, ignore_errors=True)


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


def check_common_host(host: dict, *, host_id: str, platform: str, recovery_version: str) -> None:
    if host.get("workerName") != host_id or host.get("platform") != platform:
        fail(f"{host_id} identity/platform mismatch")
    if host.get("renderBackend") != "packages/vfom/HYPERFRAMES-BACKEND.json":
        fail(f"{host_id} render backend mismatch")
    if host.get("hyperframesKnownGoodVersion") != recovery_version:
        fail(f"{host_id} HyperFrames recovery baseline mismatch")
    if host.get("hyperframesVersionPolicy") != "latest-compatible":
        fail(f"{host_id} HyperFrames version policy must be latest-compatible")
    if host.get("hyperframesCompatibilityGate") != "doctor+real-smoke":
        fail(f"{host_id} HyperFrames compatibility gate mismatch")
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
    minimum = str(exe.get("minimumVersion") or "")
    recovery = str(exe.get("recoveryVersion") or "")
    if exe.get("package") != "hyperframes":
        fail("HyperFrames package identity mismatch")
    if exe.get("versionPolicy") != "latest-compatible":
        fail("HyperFrames execution must use latest-compatible policy")
    if not re.fullmatch(r"\d+\.\d+\.\d+", minimum) or not re.fullmatch(r"\d+\.\d+\.\d+", recovery):
        fail("HyperFrames minimum/recovery versions must be semver")
    if exe.get("compatibilityGate") != "doctor+real-smoke":
        fail("HyperFrames compatibility gate must be doctor+real-smoke")
    if exe.get("networkInstallAllowed") is not False or exe.get("versionMismatch") != "capability-check":
        fail("render execution must use capability-check without in-job installs")
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
    if route.get("fallbackBridge") != "scripts/vf_ffmpeg_svg_caption.py":
        fail("ffmpeg-svg-caption fallback bridge missing")
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
    check_common_host(mac, host_id="sderot-mac", platform="macOS", recovery_version=recovery)
    check_common_host(windows, host_id="sderot-windows", platform="Windows", recovery_version=recovery)

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
    bridge = contains(BRIDGE, 'MIN_HYPERFRAMES_VERSION =', f'RECOVERY_HYPERFRAMES_VERSION = "{recovery}"', 'HYPERFRAMES_PACKAGE = "hyperframes"', 'policy=latest-compatible', 'SUPPORTED_STAGES = {"rough", "review", "final"}', 'shutil.which("hyperframes")', '"--strict-all"', '"ffprobe"', '"sha256"', '"audioRequired"', 'failover_after_primary', 'vf_ffmpeg_svg_caption', '"qaLowered": False', "sourceRequest", "prepare_request", '"--tmp-dir"')
    contains(
        ROOT / "scripts" / "vf_ffmpeg_svg_caption.py",
        'BACKEND = "ffmpeg-svg-caption-composition"',
        "Rubik",
        "#a86838",
        '"audioRequired"',
        '"sha256"',
        "def plan",
        "def render_prepared",
        "def prepare_request",
        "def visual_order",
        "text_shaping=0",
        "bidi-self-test=pass",
        "def runtime_tmp_dir",
        "VELVETOS_RUNTIME_ROOT",
        "replace=1",
        "Rubik-wght700",
        '"--tmp-dir"',
        "headlineFontSha256",
        "def release_derived_tmp",
        "caption_gap",
    )
    contains(
        ROOT / "scripts" / "vf_ffmpeg_env.py",
        "SKIP_ENV_MISSING_",
        "-filters",
        "-buildconf",
        "FRIBIDI",
        "LIBASS",
        "GITHUB_ACTIONS",
        "ci_skip_failure",
    )
    contains(
        ROOT / "scripts" / "check-video-normalization.py",
        "normalization_gap",
        "ci_skip_failure",
        "SkipTest",
    )
    contains(
        ROOT / "scripts" / "check-publication-evidence.py",
        "publication_gap",
        "ci_skip_failure",
        "skipTest",
    )
    if "version mismatch: required" in bridge or re.search(r"(?m)^HYPERFRAMES_VERSION\s*=", bridge):
        fail("bridge must not exact-pin normal HyperFrames execution")
    if "npx" in bridge or "shell=True" in bridge:
        fail("bridge must not download via npx or use shell=True")

    mac_bootstrap = contains(MAC_BOOTSTRAP, f'HYPERFRAMES_RECOVERY_VERSION="{recovery}"', 'NODE_RECOVERY_VERSION="22.22.0"', 'HOST_ID="sderot-mac"', 'HYPERFRAMES_NO_UPDATE_CHECK=1', 'HYPERFRAMES_NO_AUTO_INSTALL=1', 'hyperframes browser ensure', 'python3 scripts/vf_hyperframes.py doctor', 'python3 scripts/vf_hyperframes.py run', 'data-no-timeline', 'dir="rtl"', 'STATE_DIR="$HOME/.velvetos"')
    if "Installing pinned HyperFrames" in mac_bootstrap or 'HYPERFRAMES_VERSION="' in mac_bootstrap:
        fail("Mac bootstrap must not exact-pin normal HyperFrames execution")
    if '<html lang="he" dir="rtl">' in mac_bootstrap:
        fail("RTL must not be set on html root in HyperFrames smoke render")
    if "ngrok" in mac_bootstrap or "--share-desktop" in mac_bootstrap:
        fail("Mac render bootstrap must not create an extra remote route")
    bash = shutil.which("bash")
    if sys.platform == "win32" and bash:
        bash_path = Path(bash).resolve()
        # Windows System32\\bash.exe is the WSL launcher, not a POSIX bash that
        # accepts a Windows path argument. Prefer Git Bash when available so
        # this remains a real shell syntax check instead of a false WSL-path failure.
        if bash_path.name.lower() == "bash.exe" and bash_path.parent.name.lower() == "system32":
            git = shutil.which("git")
            git_bash = (Path(git).resolve().parents[1] / "bin" / "bash.exe") if git else None
            bash = str(git_bash) if git_bash and git_bash.is_file() else None
    if bash:
        shell_check = subprocess.run([bash, "-n", str(MAC_BOOTSTRAP)], text=True, capture_output=True)
        if shell_check.returncode != 0:
            fail(f"Mac render host bootstrap shell syntax invalid: {shell_check.stderr.strip()}")

    windows_bootstrap = contains(
        WINDOWS_BOOTSTRAP,
        '$HostId = [Environment]::GetEnvironmentVariable("VELVETOS_HOST_ID")',
        'FAIL VELVETOS_HOST_ID is not set.',
        f'$HyperFramesRecoveryVersion = "{recovery}"',
        '$NodeRecoveryVersion = "22.22.0"',
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

    if "Installing pinned HyperFrames" in windows_bootstrap or '$HyperFramesVersion = "' in windows_bootstrap:
        fail("Windows bootstrap must not exact-pin normal HyperFrames execution")

    contains(
        ROOT / "scripts" / "test_vf_ffmpeg_env.py",
        "SKIP_ENV_MISSING_ZOOMPAN",
        "def require_no_caption_gap(",
        "missing-zoompan",
        "ci_skip_failure",
        "zoompan_suite_action",
    )

    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from vf_ffmpeg_env import caption_gap, ci_skip_failure

    prove_zoompan_ci_branches()
    gap = caption_gap()
    action = zoompan_suite_action(gap, ci_skip_failure(gap))
    if action == "fail":
        fail(gap.line)
    child_env = os.environ.copy()
    child_env["VF_HYPERFRAMES_CAPABILITY_CHILD"] = "1"
    env_tests = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_vf_ffmpeg_env.py")],
        cwd=ROOT,
        env=child_env,
        text=True,
        capture_output=True,
    )
    if env_tests.returncode != 0:
        detail = ((env_tests.stdout or "") + "\n" + (env_tests.stderr or "")).strip()
        fail("ffmpeg capability tests failed:\n" + detail[-4000:])
    print("OK ffmpeg capability tests")
    if action == "skip":
        print(gap.line)
    else:
        caption_tests = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "test_vf_ffmpeg_svg_caption.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if caption_tests.returncode != 0:
            detail = (caption_tests.stderr or caption_tests.stdout or "").strip()
            fail("ffmpeg-svg-caption tests failed:\n" + detail[-4000:])

        if gap is not None:
            print(gap.line)

    print(
        f"OK hyperframes backend policy=latest-compatible minimum={minimum} recovery={recovery} "
        f"hosts=mac:{mac_status},windows:{windows_status} "
        "route=first-healthy verified-only smoke-receipt+qa-boundary+wired"
    )


if __name__ == "__main__":
    main()
