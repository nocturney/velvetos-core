#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MARKER = "VELVET_MACHINE_WRITER_ALLOW:"
PRECHECK_HELPER = "scripts/push-main-with-check-all.sh"
NON_MAIN_LITERAL_PUSHES = ("HEAD:publish-bridge",)


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def is_machine_writer(text: str) -> bool:
    if PRECHECK_HELPER in text:
        return True
    if not re.search(r"(?m)^\s*git\s+push\b", text):
        return False
    if "branches: [fix/close-runtime-corners-20260914]" in text and "workflow_dispatch:" not in text:
        return False
    return True


def has_unprotected_default_push(text: str) -> bool:
    """Return true when a writer can push the checked-out/default ref without the precheck helper."""
    if PRECHECK_HELPER in text:
        return False
    for line in text.splitlines():
        cmd = line.strip()
        if not re.match(r"git\s+push\b", cmd):
            continue
        if any(target in cmd for target in NON_MAIN_LITERAL_PUSHES):
            continue
        return True
    return False


def marker_paths(text: str) -> list[str]:
    m = re.search(r"(?m)^\s*#\s*VELVET_MACHINE_WRITER_ALLOW:\s*(.+?)\s*$", text)
    if not m:
        return []
    return [p for p in m.group(1).split() if p]


def has_write_permission(text: str) -> bool:
    """Accept explicit workflow- or job-level contents: write, never implicit defaults."""
    return bool(re.search(r"(?m)^\s*contents:\s*write\s*(?:#.*)?$", text))


def main() -> int:
    helper = ROOT / PRECHECK_HELPER
    if not helper.is_file():
        fail(f"missing machine-writer precheck helper: {PRECHECK_HELPER}")
    helper_text = helper.read_text(encoding="utf-8")
    for needle in (
        'target_branch="${1:-main}"',
        'git rebase "origin/$target_branch"',
        'scripts/sensor_selector.py',
        'machine_write_class',
        'AUTHORITY_SECURITY',
        'class=$machine_write_class',
        'precheck_log',
        'post_push=exact_sha_precheck_reused',
        'machine-check/',
        'gh workflow run "$workflow_file"',
        'gh run watch "$check_run_id"',
        '.name == "check-all"',
        '.app.slug == "github-actions"',
        'commits/$head_sha/status',
        '.context == "check-all"',
        '.state == "success"',
        'git merge-base --is-ancestor "origin/$target_branch" "$head_sha"',
        'git push origin "HEAD:refs/heads/$target_branch"',
        'git ls-remote origin "refs/heads/$target_branch"',
        'post-push remote head mismatch',
        'if [[ "$machine_write_class" == "AUTHORITY_SECURITY" ]]',
        '-f execution=main_full',
        'SENSORS [0-9]+ mode=full',
        'OK suite passed=[0-9]+',
    ):
        if needle not in helper_text:
            fail(f"machine-writer precheck helper missing invariant: {needle}")
    if re.search(r"git\s+push\s+(?:--force|-f)\b", helper_text):
        fail("machine-writer precheck helper must never force-push")

    core_workflow = (WORKFLOWS / "check-all.yml").read_text(encoding="utf-8")
    for needle in (
        "workflow_dispatch:",
        "github.event_name == 'workflow_dispatch'",
        "--selection sensor-selection.json",
        "statuses: write",
        "statuses/$GITHUB_SHA",
        "context=check-all",
        "state=success",
        "execution:",
        "machine_precheck",
        "main_full",
        "inputs.execution == 'main_full'",
    ):
        if needle not in core_workflow:
            fail(f"Core Sensors missing machine precheck surface: {needle}")
    if re.search(r"(?m)^\s*schedule:\s*$", core_workflow) or "cron:" in core_workflow:
        fail("check-all.yml must not schedule")
    if "  check-all-windows:" not in core_workflow:
        fail("check-all.yml missing check-all-windows job")
    windows_job = core_workflow.split("  check-all-windows:", 1)[1]
    for needle in (
        "runs-on: windows-latest",
        "continue-on-error: true",
        "github.event_name == 'pull_request' || github.event_name == 'push'",
        "python scripts/check-all.py",
        "requirements-sensors.py311.lock",
        "--require-hashes",
        "d760e1b3574402ed18b4865851f87d87e73965a982e6453212df8621fed1c508",
        "ffmpeg-7.1.1-full_build.zip",
        "scripts/upload_gha_artifact.py",
        "actions/checkout@v7",
        "actions/setup-python@v7",
    ):
        if needle not in windows_job:
            fail(f"check-all-windows missing {needle}")
    extra_actions = [
        use for use in re.findall(r"uses:\s*(\S+)", windows_job)
        if use not in {"actions/checkout@v7", "actions/setup-python@v7"}
    ]
    if extra_actions:
        fail("check-all-windows uses an action outside checkout and setup-python: " + ", ".join(extra_actions))
    if "context=check-all-windows" in core_workflow or "secrets." in windows_job:
        fail("check-all-windows must not publish a status or read a secret")
    if core_workflow.count("context=check-all") != 1:
        fail("check-all status context must stay the single required Linux context")
    artifact_selftest = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "upload_gha_artifact.py"), "--self-test"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=15,
    )
    if artifact_selftest.returncode != 0:
        fail("upload_gha_artifact self-test failed: " + (artifact_selftest.stderr or artifact_selftest.stdout))

    writers = []
    for path in sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        if not is_machine_writer(text):
            continue
        rel = path.relative_to(ROOT).as_posix()
        writers.append(rel)
        allowed = marker_paths(text)
        if not allowed:
            fail(f"machine writer {rel} has git push but no {MARKER} contract")
        if not has_write_permission(text):
            fail(f"machine writer {rel} lacks explicit contents: write permission")
        if has_unprotected_default_push(text):
            fail(f"machine writer {rel} can push the default branch without {PRECHECK_HELPER}")
        if PRECHECK_HELPER in text and not re.search(r"(?m)^\s*actions:\s*write\s*(?:#.*)?$", text):
            fail(f"prechecked machine writer {rel} lacks explicit actions: write permission")
        for line in text.splitlines():
            cmd = line.strip()
            if re.fullmatch(r"git add (?:-A|--all|\.)", cmd):
                fail(f"machine writer {rel} uses unrestricted staging: {cmd}")
            if re.match(r"git push\s+(?:--force|-f)\b", cmd):
                fail(f"machine writer {rel} may force-push: {cmd}")
        add_lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("git add ")]
        if not add_lines:
            fail(f"machine writer {rel} pushes but has no explicit git add line")
        if any("${existing[@]}" in ln for ln in add_lines) and "paths=(" not in text:
            fail(f"machine writer {rel} has dynamic staging without bounded paths array")
    if not writers:
        fail("no production machine writers discovered; sensor query likely broken")
    print(f"OK machine-writers={len(writers)} allowlisted force_push=0 unrestricted_stage=0 default_main=prechecked_exact_sha")
    for writer in writers:
        print("- " + writer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
