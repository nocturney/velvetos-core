#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
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


FFMPEG_ZIP_SHA256 = "d760e1b3574402ed18b4865851f87d87e73965a982e6453212df8621fed1c508"
UPLOAD_ARTIFACT = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9"
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
WINDOWS_ACTIONS = {
    CHECKOUT,
    SETUP_PYTHON,
    UPLOAD_ARTIFACT,
}
# Tag and branch refs are refused. This set is the only exception, and it starts empty.
ACTION_REF_ALLOWLIST: frozenset[str] = frozenset()
USE_LINE = re.compile(r"^(?P<prefix>\s*(?:-\s+)?)uses:\s+(?P<spec>\S+)\s*(?:#.*)?$")
VERSION_COMMENT = re.compile(
    r"^\s*#\s+(?P<action>\S+/\S+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
)
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def previous_nonempty(lines: list[str], index: int) -> str:
    """Return the previous non-empty line. index is the 0-based current line."""
    cursor = index - 1
    while cursor >= 0 and lines[cursor].strip() == "":
        cursor -= 1
    return lines[cursor] if cursor >= 0 else ""


def action_pin_problems(
    text: str,
    *,
    path: str = "<fixture>",
    allowlist: frozenset[str] | None = None,
) -> list[str]:
    """Every remote uses: is a 40-hex SHA plus a version comment, unless allowlisted."""
    allowed = ACTION_REF_ALLOWLIST if allowlist is None else allowlist
    problems: list[str] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        match = USE_LINE.match(line)
        if not match:
            continue
        spec = match.group("spec").strip("'\"")
        if spec.startswith("./") or spec.startswith("docker://"):
            continue
        if "@" not in spec:
            problems.append(f"{path}:{number}: action ref has no pin: {spec}")
            continue
        action, ref = spec.rsplit("@", 1)
        if spec in allowed:
            continue
        if not SHA_REF.fullmatch(ref):
            problems.append(f"{path}:{number}: tag or branch ref is not allowlisted: {spec}")
            continue
        comment = VERSION_COMMENT.match(previous_nonempty(lines, number - 1))
        if comment is None:
            problems.append(f"{path}:{number}: SHA pin missing version comment: {spec}")
            continue
        commented = comment.group("action")
        if action != commented and not action.startswith(commented + "/"):
            problems.append(
                f"{path}:{number}: version comment {commented} does not match {action}"
            )
    return problems


def prove_workflow_action_pins(core_workflow: str) -> str:
    """Fixtures plus mutations that revert the Linux and Windows checkouts to @v7."""
    if ACTION_REF_ALLOWLIST:
        fail("workflow action ref allowlist must start empty")
    tag_fixture = "steps:\n  - uses: actions/checkout@v7\n"
    if not any("not allowlisted" in problem for problem in action_pin_problems(tag_fixture)):
        fail("@v7 fixture was not refused")
    branch_fixture = "steps:\n  - uses: actions/checkout@main\n"
    if not any("not allowlisted" in problem for problem in action_pin_problems(branch_fixture)):
        fail("branch ref fixture was not refused")
    pinned_fixture = (
        "steps:\n"
        "  # actions/checkout v7.0.1\n"
        "  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
    )
    pinned_problems = action_pin_problems(pinned_fixture)
    if pinned_problems:
        fail("pinned SHA fixture was refused: " + "; ".join(pinned_problems))
    bare_sha = (
        "steps:\n"
        "  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
    )
    if not any("missing version comment" in problem for problem in action_pin_problems(bare_sha)):
        fail("SHA without a version comment was accepted")
    if action_pin_problems(tag_fixture, allowlist=frozenset({"actions/checkout@v7"})):
        fail("explicit allowlist did not accept actions/checkout@v7")
    linux_reverted = core_workflow.replace(CHECKOUT, "actions/checkout@v7", 1)
    if "  check-all-windows:" not in linux_reverted:
        fail("linux pin mutation lost the windows job")
    windows_of_linux_revert = linux_reverted.split("  check-all-windows:", 1)[1]
    if windows_job_problems(windows_of_linux_revert):
        fail("linux @v7 revert disturbed the windows job sensor")
    if not any(
        "not allowlisted" in problem and "@v7" in problem
        for problem in action_pin_problems(linux_reverted, path=".github/workflows/check-all.yml")
    ):
        fail("reverting the Linux checkout to @v7 was not caught")
    windows_unpinned = core_workflow.split("  check-all-windows:", 1)[1].replace(
        CHECKOUT, "actions/checkout@v7", 1
    )
    if not any(
        "not allowlisted" in problem and "@v7" in problem
        for problem in action_pin_problems(windows_unpinned, path="check-all-windows")
    ):
        fail("reverting the Windows checkout to @v7 was not caught")
    return (
        "tag_fixture=caught sha_fixture=pass bare_sha=caught "
        "linux_revert=caught windows_revert=caught allowlist=empty"
    )


def workflow_hash_operator(job: str) -> str | None:
    """Return -ne or -eq from the throw that follows the hash gate. Comments do not count."""
    for line in job.splitlines():
        code = line.split("#", 1)[0]
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", code)
        if match and "throw" in code and "sha256 mismatch" in code:
            return match.group(1)
    return None


def ffmpeg_sha_enforced(job: str) -> bool:
    """The hash literal is not enough. A failed verifier must throw, and -eq must not."""
    return (
        "scripts/verify_ffmpeg_zip_sha256.py" in job
        and workflow_hash_operator(job) == "-ne"
    )


def windows_permissions_are_contents_read(job: str) -> bool:
    lines = job.splitlines()
    for index, line in enumerate(lines):
        if not re.match(r"^    permissions:\s*$", line):
            continue
        body = []
        for nxt in lines[index + 1:]:
            if nxt.strip() == "":
                continue
            if not nxt.startswith("      "):
                break
            body.append(nxt.split("#", 1)[0].strip())
        return body == ["contents: read"]
    return False


def drop_ffmpeg_enforcement(job: str) -> str:
    """Mutation: delete the throw line and keep the hash literal."""
    kept: list[str] = []
    dropped = False
    for line in job.splitlines(keepends=True):
        code = line.split("#", 1)[0]
        if (
            not dropped
            and "$LASTEXITCODE" in code
            and "throw" in code
            and "sha256 mismatch" in code
        ):
            dropped = True
            continue
        kept.append(line)
    if not dropped:
        raise ValueError("ffmpeg enforcement line was not present to delete")
    return "".join(kept)


def invert_hash_operator(job: str) -> str:
    """Mutation Claude ran: -ne becomes -eq, so a matching zip throws and a bad zip continues."""
    flipped = job.replace("$LASTEXITCODE -ne 0", "$LASTEXITCODE -eq 0", 1)
    if flipped == job:
        raise ValueError("ffmpeg -ne operator was not present to invert")
    return flipped


def windows_job_problems(job: str) -> list[str]:
    problems: list[str] = []
    for needle in (
        "runs-on: windows-latest",
        "continue-on-error: true",
        "github.event_name == 'pull_request' || github.event_name == 'push'",
        "python scripts/check-all.py",
        "requirements-sensors.py311.lock",
        "--require-hashes",
        FFMPEG_ZIP_SHA256,
        "ffmpeg-7.1.1-full_build.zip",
        "core.autocrlf false",
        CHECKOUT,
        "# actions/checkout v7.0.1",
        SETUP_PYTHON,
        "# actions/setup-python v7.0.0",
        UPLOAD_ARTIFACT,
        "# actions/upload-artifact v7.0.2",
        "name: check-all-windows",
        "if-no-files-found: error",
        "if: always()",
        "persist-credentials: false",
        "fetch-depth: 0",
        "git show <sha>:path",
    ):
        if needle not in job:
            problems.append(f"check-all-windows missing {needle}")
    if not ffmpeg_sha_enforced(job):
        problems.append("check-all-windows does not enforce the ffmpeg zip sha256")
    if not windows_permissions_are_contents_read(job):
        problems.append("check-all-windows permissions must be contents: read only")
    if "statuses:" in job:
        problems.append("check-all-windows must not grant statuses")
    extra_actions = [
        use for use in re.findall(r"uses:\s*(\S+)", job)
        if use not in WINDOWS_ACTIONS
    ]
    if extra_actions:
        problems.append(
            "check-all-windows uses an action outside the allowlist: " + ", ".join(extra_actions)
        )
    if "secrets." in job or "upload_gha_artifact" in job or "ACTIONS_RUNTIME_TOKEN" in job:
        problems.append("check-all-windows must not read a secret or call the internal artifact API")
    return problems


HASH_GATE = ROOT / "scripts" / "verify_ffmpeg_zip_sha256.py"


def hash_gate_exits(script: Path, data: bytes, expected: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "fixture.bin"
        fixture.write_bytes(data)
        proc = subprocess.run(
            [sys.executable, str(script), "--path", str(fixture), "--expected", expected],
            text=True,
            capture_output=True,
            timeout=15,
        )
        return proc.returncode


def prove_ffmpeg_hash_gate() -> str:
    """Run the real verifier, then a copy whose comparison is inverted."""
    if not HASH_GATE.is_file():
        fail("missing ffmpeg hash gate: scripts/verify_ffmpeg_zip_sha256.py")
    source = HASH_GATE.read_text(encoding="utf-8")
    if source.count("got != expected") != 1:
        fail("ffmpeg hash gate must compare with got != expected exactly once")
    data = b"not-the-ffmpeg-zip"
    wrong = "0" * 64
    right = hashlib.sha256(data).hexdigest()
    mismatch = hash_gate_exits(HASH_GATE, data, wrong)
    match = hash_gate_exits(HASH_GATE, data, right)
    if mismatch == 0 or match != 0:
        fail(
            "ffmpeg hash gate fixture failed: "
            f"wrong_digest_exit={mismatch} match_exit={match}"
        )
    inverted = source.replace("got != expected", "got == expected", 1)
    with tempfile.TemporaryDirectory() as tmp:
        mutated = Path(tmp) / "verify_ffmpeg_zip_sha256.py"
        mutated.write_text(inverted, encoding="utf-8")
        inverted_exit = hash_gate_exits(mutated, data, wrong)
    if inverted_exit != 0:
        fail("inverting got != expected still rejected a wrong digest")
    return f"wrong_digest_exit={mismatch} match_exit={match} inverted_operator_exit={inverted_exit}"


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
    for problem in windows_job_problems(windows_job):
        fail(problem)
    try:
        mutated = drop_ffmpeg_enforcement(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if FFMPEG_ZIP_SHA256 not in mutated:
        fail("ffmpeg enforcement mutation also deleted the hash literal")
    mutated_problems = windows_job_problems(mutated)
    if not any(problem == "check-all-windows does not enforce the ffmpeg zip sha256" for problem in mutated_problems):
        fail("deleting the ffmpeg sha256 enforcement line was not caught")
    try:
        flipped = invert_hash_operator(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if ffmpeg_sha_enforced(flipped) or workflow_hash_operator(flipped) != "-eq":
        fail("flipping the ffmpeg hash operator from -ne to -eq was not caught")
    flipped_problems = windows_job_problems(flipped)
    if not any(problem == "check-all-windows does not enforce the ffmpeg zip sha256" for problem in flipped_problems):
        fail("the -ne to -eq mutation still passed the windows job sensor")
    gate_evidence = prove_ffmpeg_hash_gate()
    print(
        "OK check-all-windows ffmpeg-sha-enforce "
        f"delete=caught operator_flip=caught {gate_evidence} permissions=contents:read"
    )
    pin_evidence = prove_workflow_action_pins(core_workflow)
    for path in sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))):
        rel = path.relative_to(ROOT).as_posix()
        for problem in action_pin_problems(path.read_text(encoding="utf-8"), path=rel):
            fail(problem)
    print(f"OK workflow-action-pins {pin_evidence}")
    if core_workflow.count("context=check-all") != 1:
        fail("check-all status context must stay the single required Linux context")
    if "context=check-all-windows" in core_workflow:
        fail("check-all-windows must not publish a status")

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
