#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "UPSTREAM-WATCH.json"
TOOL_STATUS = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"
GROK = ROOT / "automation" / "grok" / "manifest.json"
SPEECH = ROOT / "packages" / "vfom" / "SPEECH-BACKEND.json"
COGNEE = ROOT / "packages" / "vfmem" / "cognee.json"
RESEARCH_DAILY = ROOT / "packages" / "vfresearch" / "DAILY.md"
OFFICE_LOOP = ROOT / "scripts" / "vfops_loop.py"
HF = ROOT / "scripts" / "vf_hyperframes.py"
HF_WIN = ROOT / "scripts" / "bootstrap-edge-host-windows.ps1"
HF_MAC = ROOT / "scripts" / "bootstrap-hyperframes-host-macos.sh"
MANIM_WIN = ROOT / "scripts" / "bootstrap-manim-host-windows.ps1"
VIDEO_TOOLCHAIN = ROOT / "packages" / "vfom" / "VIDEO-TOOLCHAIN.json"
UPSTREAM_CLI = ROOT / "scripts" / "vf_upstream_watch.py"
GITHUB = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", re.I)


def fail(message: str) -> None:
    print(f"UPSTREAM WATCH FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def norm_repo(value: str) -> str:
    return value.removesuffix(".git").rstrip(".,;").casefold()


def provenance_files() -> set[Path]:
    """Files that represent embedded/adapted provenance, not broad research history."""
    files: set[Path] = set()
    for base, pattern in (
        (ROOT / ".cursor" / "skills", "SKILL.md"),
        (ROOT / ".agents", "*"),
        (ROOT / "packages" / "vfagents", "*.md"),
        (ROOT / "packages" / "vfharness" / "playbooks", "*.md"),
        (ROOT / "packages" / "vfmem", "*.md"),
    ):
        if base.exists():
            files.update(path for path in base.rglob(pattern) if path.is_file())
    packages = ROOT / "packages"
    if packages.exists():
        files.update(path for path in packages.glob("*/ORIGIN.md") if path.is_file())
        files.update(path for path in packages.glob("*/catalog.json") if path.is_file())
    for rel in ("packages/vfom/VIDEO-TOOLCHAIN.json", "packages/vfom/LOCK.md"):
        path = ROOT / rel
        if path.is_file():
            files.add(path)
    return files


def provenance_repos() -> set[str]:
    repos: set[str] = set()
    for path in provenance_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        repos.update(norm_repo(match.group(1)) for match in GITHUB.finditer(text))
    return repos


def main() -> int:
    if not REGISTRY.is_file():
        fail("UPSTREAM-WATCH.json missing")
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema") != "velvetos.upstream-watch.v1":
        fail("registry schema mismatch")
    policy = data.get("policy") or {}
    if policy.get("default") != "latest-compatible" or policy.get("autoUpgrade") is not False:
        fail("default must be latest-compatible with autoUpgrade=false")
    if policy.get("pendingUpdates") != "sticky-until-explicit-reviewed-adoption-ack":
        fail("pending updates must remain sticky until reviewed adoption acknowledgement")
    if "vf_upstream_watch.py ack" not in str(policy.get("adoptionAck") or ""):
        fail("registry must document explicit adoption acknowledgement command")
    selftest = subprocess.run(
        [sys.executable, str(UPSTREAM_CLI), "selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
    )
    if selftest.returncode != 0 or "sticky-pending" not in (selftest.stdout or ""):
        fail(f"upstream behavioral selftest failed: {selftest.stderr or selftest.stdout}")
    sources = data.get("sources") or []
    tracked = {norm_repo(str(row.get("repo") or "")): row for row in sources if row.get("repo")}
    excluded_rows = data.get("excludedSources") or []
    excluded = {norm_repo(str(row.get("repo") or "")): row for row in excluded_rows if row.get("repo")}
    overlap = sorted(set(tracked) & set(excluded))
    if overlap:
        fail("repo cannot be both monitored and excluded: " + ", ".join(overlap[:20]))
    missing = sorted(provenance_repos() - set(tracked) - set(excluded))
    if missing:
        fail("unclassified embedded provenance repos: " + ", ".join(missing[:20]))
    for repo, row in excluded.items():
        if not str(row.get("reason") or "").strip() or row.get("status") not in {"frozen", "forbidden", "historical-no-monitor"}:
            fail(f"excluded repo lacks explicit status/reason: {repo}")
    if "getopenpost/openpost" not in excluded or excluded["getopenpost/openpost"].get("status") != "frozen":
        fail("OpenPost upstream must be explicitly excluded as frozen")
    if "superdesigndev/treg" not in excluded or excluded["superdesigndev/treg"].get("status") != "forbidden":
        fail("Treg upstream must be explicitly excluded as forbidden")
    for repo, row in tracked.items():
        if "openpost" in repo:
            fail("OpenPost must not be update-tracked while frozen")
        if row.get("updatePolicy") != "latest-compatible" or row.get("autoUpgrade") is not False:
            fail(f"{repo} must use latest-compatible and autoUpgrade=false")
        forbidden = set(row) & {"pinnedVersion", "requiredVersion", "exactVersion"}
        if forbidden:
            fail(f"{repo} has operational exact-version fields: {sorted(forbidden)}")
    status = json.loads(TOOL_STATUS.read_text(encoding="utf-8"))
    rules = status.get("rules") or {}
    if "latest-compatible" not in str(rules.get("version_default") or ""):
        fail("global tool version default must be latest-compatible")
    for phrase in ("rollback", "recovery", "reproduc"):
        if phrase not in str(rules.get("exact_version_exception") or "").casefold():
            fail(f"global exact-version exception must document {phrase}")
    if "separate reviewed action" not in str(rules.get("upgrade_application") or ""):
        fail("upgrade application must remain separate from update detection")
    if rules.get("upstream_registry") != "packages/velvetos/UPSTREAM-WATCH.json":
        fail("tool status must bind the upstream registry")
    tools = status.get("tools") or {}
    openpost = tools.get("openpost") or {}
    if openpost.get("status") != "frozen" or openpost.get("upgrade_watch") is not False:
        fail("OpenPost frozen/no-upgrade-watch policy missing")
    exceptions = data.get("stabilityExceptions") or []
    cognee_exception = [
        row for row in exceptions
        if row.get("component") == "cognee" and row.get("class") == "staged-stability-pin"
    ]
    if len(cognee_exception) != 1:
        fail("Cognee exact pin must be explicitly classified as staged stability")
    cognee = json.loads(COGNEE.read_text(encoding="utf-8"))
    cognee_source = tracked.get("topoteretes/cognee") or {}
    expected_cognee_release = "v" + str(cognee.get("pinnedVersion") or "").lstrip("v")
    if cognee_source.get("adoptedRelease") != expected_cognee_release:
        fail(
            "Cognee tracked adoptedRelease must match the staged stability pin "
            f"{expected_cognee_release}"
        )
    if cognee_source.get("adoptionClass") != "staged-stability-pin":
        fail("Cognee tracked source must classify its exact pin as staged stability")
    updates = cognee.get("updates") or {}
    if not all(updates.get(k) is True for k in ("stagingVenv", "requireSmoke", "requireVfmemSensor", "rollbackOnFailure", "updatePinOnlyAfterGreen")):
        fail("Cognee stability pin lacks staging/smoke/rollback gates")
    speech = json.loads(SPEECH.read_text(encoding="utf-8")).get("provider") or {}
    if speech.get("versionPolicy") != "latest-compatible" or speech.get("compatibilityGate") != "speech-doctor+real-hebrew-tts-stt-smoke":
        fail("VoiceStudio must use latest-compatible + speech smoke policy")
    if "version" in speech or "commit" in speech:
        fail("VoiceStudio provider must not carry operational exact version/commit fields")
    grok = json.loads(GROK.read_text(encoding="utf-8"))
    upstream_binding = grok.get("upstreamWatch") or {}
    if upstream_binding != {
        "ownerRoutineId": "velvet-research-seat",
        "registry": "packages/velvetos/UPSTREAM-WATCH.json",
        "report": "packages/vfresearch/sources/upstream-watch-latest.json",
        "autoUpgrade": False,
        "consumerRoutineId": "velvetos-office-loop",
    }:
        fail("Grok manifest upstream-watch ownership binding mismatch")
    research_text = RESEARCH_DAILY.read_text(encoding="utf-8")
    for needle in ("vf_upstream_watch.py check --write", "upstream-watch-latest.json", "אין auto-upgrade"):
        if needle not in research_text:
            fail(f"Research Seat daily contract missing upstream watch marker: {needle}")
    office_text = OFFICE_LOOP.read_text(encoding="utf-8")
    for needle in ("UPSTREAM_REPORT", "upstream watch report stale", "research+upstreams verified"):
        if needle not in office_text:
            fail(f"Office Loop missing upstream report consumption marker: {needle}")
    all_rows = list(grok.get("routines") or []) + list(grok.get("retiredRoutines") or [])
    if any(str(x.get("id") or "").casefold() == "openpost-release-watch" for x in all_rows):
        fail("OpenPost Release Watch must be deleted from scheduler authority")
    hf_text = HF.read_text(encoding="utf-8")
    win_text = HF_WIN.read_text(encoding="utf-8")
    mac_text = HF_MAC.read_text(encoding="utf-8")
    if re.search(r"(?m)^HYPERFRAMES_VERSION\s*=", hf_text):
        fail("HyperFrames runtime is exact-version locked")
    if re.search(r"(?m)^\$HyperFramesVersion\s*=", win_text):
        fail("Windows HyperFrames bootstrap is exact-version locked")
    if re.search(r"(?m)^HYPERFRAMES_VERSION\s*=", mac_text):
        fail("Mac HyperFrames bootstrap is exact-version locked")

    manim_text = MANIM_WIN.read_text(encoding="utf-8")
    if re.search(r"(?m)^\$MANIM_VERSION\s*=", manim_text) or "manim==$MANIM" in manim_text:
        fail("Manim bootstrap is exact-version locked")
    video = json.loads(VIDEO_TOOLCHAIN.read_text(encoding="utf-8"))
    slots = video.get("animationSlots") or {}
    manim = slots.get("manim") or {}
    remotion = slots.get("remotion") or {}
    if manim.get("versionPolicy") != "latest-compatible" or manim.get("compatibilityGate") != "host-doctor+real-smoke":
        fail("Manim must use latest-compatible + smoke compatibility gate")
    if remotion.get("versionPolicy") != "latest-compatible" or remotion.get("compatibilityGate") != "license-eligibility+adapter-smoke":
        fail("Remotion must use latest-compatible + license/smoke compatibility gate")
    print(
        f"UPSTREAM WATCH PASS sources={len(sources)} provenance={len(provenance_repos())} "
        f"excluded={len(excluded)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
