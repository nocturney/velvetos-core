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
EXIT_RESET = re.compile(r"\$LASTEXITCODE\s*=\s*0\b")
# Tag and branch refs are refused. This set is the only exception, and it starts empty.
ACTION_REF_ALLOWLIST: frozenset[str] = frozenset()
USE_LINE = re.compile(r"^(?P<prefix>\s*(?:-\s+)?)uses:\s+(?P<spec>\S+)\s*(?:#.*)?$")
_FLOW_USES = re.compile(
    r"""['\"]?uses['\"]?\s*:\s*(?P<spec>\"[^\"]+\"|'[^']+'|[^,}\s]+)"""
)
VERSION_COMMENT = re.compile(
    r"^\s*#\s+(?P<action>\S+/\S+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
)
SHA_REF = re.compile(r"^[0-9a-f]{40}$")
DOCKER_DIGEST = re.compile(r"^docker://[^@\s]+@sha256:[0-9a-f]{64}$")


def previous_nonempty(lines: list[str], index: int) -> str:
    """Return the previous non-empty line. index is the 0-based current line."""
    cursor = index - 1
    while cursor >= 0 and lines[cursor].strip() == "":
        cursor -= 1
    return lines[cursor] if cursor >= 0 else ""


def _yaml_code(line: str) -> str:
    """Drop a trailing comment and ``${{ }}``. A quoted ``#`` stays."""
    masked = re.sub(r"\$\{\{.*?\}\}", "", line)
    out: list[str] = []
    quote = ""
    for ch in masked:
        if quote:
            if ch == quote:
                quote = ""
            out.append(ch)
            continue
        if ch in "'\"":
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out)


def _flow_uses_specs(line: str) -> list[str]:
    """``uses:`` values inside a one-line flow mapping. Block lines are separate."""
    code = _yaml_code(line)
    if "{" not in code:
        return []
    specs: list[str] = []
    for match in _FLOW_USES.finditer(code):
        spec = match.group("spec").strip().strip("'\"")
        if spec:
            specs.append(spec)
    return specs


def _uses_problems(
    spec: str,
    number: int,
    lines: list[str],
    path: str,
    allowed: frozenset[str],
    *,
    scan_docker: bool,
) -> list[str]:
    if spec.startswith("./"):
        return []
    if spec.startswith("docker://"):
        if not scan_docker or DOCKER_DIGEST.fullmatch(spec):
            return []
        return [f"{path}:{number}: docker ref is not digest-pinned: {spec}"]
    if "@" not in spec:
        return [f"{path}:{number}: action ref has no pin: {spec}"]
    action, ref = spec.rsplit("@", 1)
    if spec in allowed:
        return []
    if not SHA_REF.fullmatch(ref):
        return [f"{path}:{number}: tag or branch ref is not allowlisted: {spec}"]
    comment = VERSION_COMMENT.match(previous_nonempty(lines, number - 1))
    if comment is None:
        return [f"{path}:{number}: SHA pin missing version comment: {spec}"]
    commented = comment.group("action")
    if action != commented and not action.startswith(commented + "/"):
        return [f"{path}:{number}: version comment {commented} does not match {action}"]
    return []


def action_pin_problems(
    text: str,
    *,
    path: str = "<fixture>",
    allowlist: frozenset[str] | None = None,
    scan_flow: bool = True,
    scan_docker: bool = True,
) -> list[str]:
    """Every remote uses: is a 40-hex SHA plus a version comment, unless allowlisted.

    A one-line flow mapping is scanned too. ``docker://`` must be
    ``docker://name@sha256:<64 hex>``. ``./`` local actions stay unpinned.
    ``scan_flow=False`` and ``scan_docker=False`` exist so the mutation log
    can show those checks are load-bearing.
    """
    allowed = ACTION_REF_ALLOWLIST if allowlist is None else allowlist
    problems: list[str] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        match = USE_LINE.match(line)
        if match:
            specs = [match.group("spec").strip("'\"")]
        elif scan_flow and not line.lstrip().startswith("#"):
            specs = _flow_uses_specs(line)
        else:
            continue
        for spec in specs:
            problems.extend(
                _uses_problems(
                    spec, number, lines, path, allowed, scan_docker=scan_docker
                )
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
    flow_tag = "steps:\n  - { name: Sneaky, uses: actions/checkout@v7 }\n"
    if not any("not allowlisted" in problem for problem in action_pin_problems(flow_tag)):
        fail("flow-mapping @v7 was not refused")
    if action_pin_problems(flow_tag, scan_flow=False):
        fail("turning off the flow scan still caught @v7")
    flow_quoted = 'steps:\n  - { "uses": "actions/checkout@v7" }\n'
    if not any("not allowlisted" in problem for problem in action_pin_problems(flow_quoted)):
        fail("quoted flow-mapping @v7 was not refused")
    flow_sha = (
        "steps:\n"
        "  # actions/checkout v7.0.1\n"
        "  - { uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 }\n"
    )
    flow_sha_problems = action_pin_problems(flow_sha)
    if flow_sha_problems:
        fail("digest-pinned flow step was refused: " + "; ".join(flow_sha_problems))
    flow_local = "steps:\n  - { uses: ./.github/actions/local }\n"
    if action_pin_problems(flow_local):
        fail("local flow action was refused")
    smoke_path = WORKFLOWS / "instagram-read-smoke.yml"
    smoke = smoke_path.read_text(encoding="utf-8")
    if action_pin_problems(smoke, path=smoke_path.as_posix()):
        fail("live instagram-read-smoke.yml was refused")
    smoke_flow = smoke + "\n      - { name: Sneaky, uses: actions/checkout@v7 }\n"
    if not any(
        "not allowlisted" in problem
        for problem in action_pin_problems(smoke_flow, path=smoke_path.as_posix())
    ):
        fail("flow-mapping @v7 appended to a real workflow was not caught")
    docker_tag = "steps:\n  - uses: docker://alpine:latest\n"
    if not any("not digest-pinned" in problem for problem in action_pin_problems(docker_tag)):
        fail("docker://alpine:latest was not refused")
    if action_pin_problems(docker_tag, scan_docker=False):
        fail("turning off the docker scan still caught alpine:latest")
    docker_digest = (
        "steps:\n"
        "  - uses: docker://alpine@sha256:"
        + ("a" * 64)
        + "\n"
    )
    docker_problems = action_pin_problems(docker_digest)
    if docker_problems:
        fail("digest-pinned docker ref was refused: " + "; ".join(docker_problems))
    docker_bare = "steps:\n  - uses: docker://alpine\n"
    if not any("not digest-pinned" in problem for problem in action_pin_problems(docker_bare)):
        fail("docker://alpine without a digest was not refused")
    smoke_docker = smoke + "\n      - uses: docker://alpine:latest\n"
    if not any(
        "not digest-pinned" in problem
        for problem in action_pin_problems(smoke_docker, path=smoke_path.as_posix())
    ):
        fail("docker://alpine:latest appended to a real workflow was not caught")
    return (
        "tag_fixture=caught sha_fixture=pass bare_sha=caught "
        "linux_revert=caught windows_revert=caught allowlist=empty "
        "flow_v7=caught flow_sha=pass flow_off=escaped "
        "docker_tag=caught docker_digest=pass docker_off=escaped"
    )


class _PwshScope:
    __slots__ = ("dead", "killed")

    def __init__(self, dead: bool) -> None:
        self.dead = dead
        self.killed = False


def _pwsh_edge(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start else ""
    after = text[end] if end < len(text) else ""
    return not (before.isalnum() or before in "_$") and not (after.isalnum() or after in "_$")


def _skip_sq(text: str, index: int) -> int:
    cursor = index + 1
    while cursor < len(text):
        if text[cursor] == "'":
            if cursor + 1 < len(text) and text[cursor + 1] == "'":
                cursor += 2
                continue
            return cursor + 1
        cursor += 1
    return len(text)


def _skip_dq(text: str, index: int) -> int:
    cursor = index + 1
    while cursor < len(text):
        if text[cursor] == "`":
            cursor += 2
            continue
        if text[cursor] == '"':
            return cursor + 1
        cursor += 1
    return len(text)


def _split_pwsh_op(text: str, op: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    cursor = 0
    depth = 0
    while cursor < len(text):
        char = text[cursor]
        if char in "'\"":
            end = _skip_sq(text, cursor) if char == "'" else _skip_dq(text, cursor)
            buf.append(text[cursor:end])
            cursor = end
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        if (
            depth == 0
            and text[cursor:cursor + len(op)].lower() == op.lower()
            and _pwsh_edge(text, cursor, cursor + len(op))
        ):
            parts.append("".join(buf))
            buf = []
            cursor += len(op)
            continue
        buf.append(char)
        cursor += 1
    parts.append("".join(buf))
    return parts


def _pwsh_disjunct_false(part: str) -> bool:
    if re.sub(r"\s+", "", part).lower() == "$false":
        return True
    arms = _split_pwsh_op(part, "-and")
    if len(arms) > 1:
        return any(re.sub(r"\s+", "", arm).lower() == "$false" for arm in arms)
    return False


def _pwsh_condition_false(condition: str) -> bool:
    arms = [arm for arm in _split_pwsh_op(condition, "-or") if arm.strip()]
    return bool(arms) and all(_pwsh_disjunct_false(arm) for arm in arms)


def _read_pwsh_word(text: str, index: int) -> tuple[str, int] | None:
    cursor = index
    if text[cursor] == "$":
        cursor += 1
    if cursor >= len(text) or not (text[cursor].isalpha() or text[cursor] == "_"):
        return None
    cursor += 1
    while cursor < len(text) and (text[cursor].isalnum() or text[cursor] == "_"):
        cursor += 1
    return text[index:cursor], cursor


def _skip_pwsh_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _read_pwsh_paren(text: str, index: int) -> tuple[str, int]:
    depth = 0
    cursor = index
    while cursor < len(text):
        char = text[cursor]
        if char in "'\"":
            cursor = _skip_sq(text, cursor) if char == "'" else _skip_dq(text, cursor)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[index + 1:cursor], cursor + 1
        cursor += 1
    return text[index + 1:], len(text)


# Residual if(0), while, trap, try, and uncalled function or scriptblock shapes belong to scripts/check-ffmpeg-hash-gate.ps1.
def powershell_reachable(text: str) -> str:
    """PowerShell that can run. Comments, strings, here-strings, if($false), and code after exit/return are gone.

    A reachable throw keeps the words sha256 mismatch so the hash-gate matcher can see them.
    #861 exact-matches the workflow step body; this tokenizer does not change that body.
    """
    out: list[str] = []
    scopes = [_PwshScope(False)]
    index = 0
    pending_dead_block = False
    pending_dead_stmt = False
    at_stmt = True

    def dead() -> bool:
        top = scopes[-1]
        return top.dead or top.killed or pending_dead_stmt

    def emit(piece: str) -> None:
        if not dead():
            out.append(piece)

    while index < len(text):
        if text.startswith("<#", index):
            end = text.find("#>", index + 2)
            chunk = text[index:] if end < 0 else text[index:end + 2]
            out.append("\n" * chunk.count("\n"))
            index = len(text) if end < 0 else end + 2
            continue
        if text[index] == "#":
            end = text.find("\n", index)
            out.append("\n")
            at_stmt = True
            pending_dead_stmt = False
            index = len(text) if end < 0 else end + 1
            continue
        if text[index] == "@" and index + 2 < len(text) and text[index + 1] in "'\"":
            closer = "\n'@" if text[index + 1] == "'" else '\n"@'
            line_end = index + 2
            if line_end < len(text) and text[line_end] == "\r":
                line_end += 1
            if line_end < len(text) and text[line_end] == "\n":
                end = text.find(closer, line_end)
                chunk = text[index:] if end < 0 else text[index:end + len(closer)]
                out.append("\n" * chunk.count("\n"))
                index = len(text) if end < 0 else end + len(closer)
                continue
        if text[index] in "'\"":
            end = _skip_sq(text, index) if text[index] == "'" else _skip_dq(text, index)
            content = text[index + 1:end - 1] if end > index and text[end - 1:end] == text[index] else text[index + 1:end]
            if "sha256 mismatch" in content.lower():
                emit('"sha256 mismatch"')
            else:
                emit('""')
            at_stmt = False
            index = end
            continue
        char = text[index]
        if char == "\n":
            out.append("\n")
            at_stmt = True
            pending_dead_stmt = False
            index += 1
            continue
        if char in " \t\r":
            emit(char)
            index += 1
            continue
        if char == "{":
            if pending_dead_block:
                scopes.append(_PwshScope(True))
                pending_dead_block = False
            else:
                scopes.append(_PwshScope(dead()))
            emit("{")
            at_stmt = True
            index += 1
            continue
        if char == "}":
            if len(scopes) > 1:
                scopes.pop()
            emit("}")
            at_stmt = True
            index += 1
            continue
        if char == ";":
            emit(";")
            at_stmt = True
            pending_dead_stmt = False
            index += 1
            continue
        word = _read_pwsh_word(text, index)
        if word is not None:
            token, nxt = word
            lowered = token.lower()
            if lowered == "if" and at_stmt and not dead():
                paren_at = _skip_pwsh_ws(text, nxt)
                if paren_at < len(text) and text[paren_at] == "(":
                    condition, after = _read_pwsh_paren(text, paren_at)
                    body_at = _skip_pwsh_ws(text, after)
                    if _pwsh_condition_false(condition):
                        if body_at < len(text) and text[body_at] == "{":
                            pending_dead_block = True
                            index = body_at
                        else:
                            pending_dead_stmt = True
                            index = body_at
                        continue
                    emit("if ")
                    emit(condition)
                    at_stmt = False
                    index = after
                    continue
            if lowered in ("exit", "return") and at_stmt and not dead():
                scopes[-1].killed = True
                at_stmt = False
                index = nxt
                continue
            emit(token)
            at_stmt = False
            index = nxt
            continue
        emit(char)
        at_stmt = False
        index += 1
    return "".join(out)


def workflow_hash_operator(job: str) -> str | None:
    """Return -ne or -eq from a reachable hash-gate throw."""
    for line in powershell_reachable(job).splitlines():
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", line)
        if match and "throw" in line and "sha256 mismatch" in line:
            return match.group(1)
    return None


def ffmpeg_sha_enforced(job: str) -> bool:
    """The hash literal is not enough. A failed verifier must throw, and -eq must not."""
    reached = powershell_reachable(job)
    return (
        "scripts/verify_ffmpeg_zip_sha256.py" in reached
        and workflow_hash_operator(job) == "-ne"
    )


def ffmpeg_exit_was_reset(job: str) -> bool:
    """True when LASTEXITCODE is set to 0 after the verifier and before the throw.

    The assignment may sit on the verifier line. The -ne throw can still be present.
    Only reachable PowerShell counts.
    """
    codes = powershell_reachable(job).splitlines()
    start = next(
        (index for index, code in enumerate(codes) if "scripts/verify_ffmpeg_zip_sha256.py" in code),
        None,
    )
    if start is None:
        return False
    end = None
    for index in range(start, len(codes)):
        code = codes[index]
        if (
            re.search(r"\$LASTEXITCODE\s+-ne\s+0\b", code)
            and "throw" in code
            and "sha256 mismatch" in code
        ):
            end = index
            break
    if end is None:
        return False
    return any(EXIT_RESET.search(code) for code in codes[start:end + 1])


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


def flip_persist_credentials(job: str) -> str:
    """Mutation: persist-credentials: false becomes true, so the checkout keeps a token."""
    mutated = job.replace("persist-credentials: false", "persist-credentials: true", 1)
    if mutated == job:
        raise ValueError("persist-credentials: false was not present to flip")
    return mutated


# Quoted keys and a space before the colon do not contain the bare text
# "continue-on-error:". #861's duplicate-key loader is still on an open branch.
_CONTINUE_ON_ERROR_KEY = re.compile(
    r"""(?m)(?:^|[{,\s])(?:["']continue-on-error["']|continue-on-error)[ \t]*:"""
)


def windows_continues_on_error(job: str) -> bool:
    return _CONTINUE_ON_ERROR_KEY.search(job) is not None


def insert_windows_continue_on_error(job: str, line: str) -> str:
    """Mutation: put a continue-on-error key back on the Windows job."""
    needle = "runs-on: windows-latest\n"
    mutated = job.replace(needle, needle + "    " + line + "\n", 1)
    if mutated == job:
        raise ValueError("runs-on: windows-latest was not present to restore continue-on-error")
    return mutated


def reset_ffmpeg_exit(job: str) -> str:
    """Mutation from the #827 verdict: zero LASTEXITCODE on the verifier line."""
    needle = "python scripts/verify_ffmpeg_zip_sha256.py --path $zip --expected $expected"
    mutated = job.replace(needle, needle + "; $LASTEXITCODE = 0", 1)
    if mutated == job:
        raise ValueError("ffmpeg verifier call was not present to reset LASTEXITCODE")
    return mutated


FFMPEG_THROW = 'if ($LASTEXITCODE -ne 0) { throw "ffmpeg zip sha256 mismatch: $expected" }'


def line_comment_hash_operator(job: str) -> str | None:
    """The pre-tokenization matcher. A multiline <# #> comment still looks live to it."""
    for line in job.splitlines():
        code = line.split("#", 1)[0]
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", code)
        if match and "throw" in code and "sha256 mismatch" in code:
            return match.group(1)
    return None


def hide_ffmpeg_throw(job: str, wrapped: str) -> str:
    if job.count(FFMPEG_THROW) != 1:
        raise ValueError("ffmpeg throw was not present once")
    return job.replace(FFMPEG_THROW, wrapped, 1)


def prove_ffmpeg_throw_reachable(job: str) -> str:
    """Mutations that keep the throw text but make it unreachable."""
    if workflow_hash_operator(job) != "-ne" or not ffmpeg_sha_enforced(job):
        fail("live ffmpeg throw is not a reachable -ne gate")
    if ffmpeg_exit_was_reset(job):
        fail("live ffmpeg throw was treated as an exit reset")
    hides = {
        "block": "<#\n" + FFMPEG_THROW + "\n#>",
        "inline_block": "<# " + FFMPEG_THROW + " #>",
        "here_literal": "@'\n" + FFMPEG_THROW + "\n'@",
        "here_expand": '@"\n' + FFMPEG_THROW + '\n"@',
        "if_false": "if ($false) { " + FFMPEG_THROW + " }",
        "if_false_case": "If ($False) { " + FFMPEG_THROW + " }",
        "and_false": 'if ($LASTEXITCODE -ne 0 -and $false) { throw "ffmpeg zip sha256 mismatch: $expected" }',
        "or_true": None,
        "exit": "exit 0\n" + FFMPEG_THROW,
        "return": "return\n" + FFMPEG_THROW,
        "string": "$note = '" + FFMPEG_THROW + "'",
    }
    # A false disjunct beside a true one must stay reachable.
    or_true = 'if ($false -or $true) { ' + FFMPEG_THROW + " }"
    if not ffmpeg_sha_enforced(hide_ffmpeg_throw(job, or_true)):
        fail("if ($false -or $true) hid a reachable throw")
    conditional_exit = "if ($true) { exit }\n" + FFMPEG_THROW
    if not ffmpeg_sha_enforced(hide_ffmpeg_throw(job, conditional_exit)):
        fail("exit inside if hid a later throw")
    fooled = ("block", "here_literal", "here_expand", "if_false", "and_false", "exit", "return", "string")
    for name, wrapped in hides.items():
        if wrapped is None:
            continue
        mutated = hide_ffmpeg_throw(job, wrapped)
        old = line_comment_hash_operator(mutated)
        if name in fooled and old != "-ne":
            fail("line-comment matcher was not fooled by " + name)
        if name == "inline_block" and old is not None:
            fail("single-line block comment still matched after a hash split")
        if ffmpeg_sha_enforced(mutated) or workflow_hash_operator(mutated) is not None:
            fail("hidden ffmpeg throw still counted as enforced: " + name)
        problems = windows_job_problems(mutated)
        if not any(
            problem == "check-all-windows does not enforce the ffmpeg zip sha256"
            for problem in problems
        ):
            fail("hidden ffmpeg throw was not caught: " + name)
    return "throw_hidden=caught"


def windows_job_problems(job: str) -> list[str]:
    problems: list[str] = []
    for needle in (
        "runs-on: windows-latest",
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
        "scripts/check-ffmpeg-hash-gate.ps1",
    ):
        if needle not in job:
            problems.append(f"check-all-windows missing {needle}")
    if windows_continues_on_error(job):
        problems.append("check-all-windows must not continue on error")
    if not ffmpeg_sha_enforced(job):
        problems.append("check-all-windows does not enforce the ffmpeg zip sha256")
    if ffmpeg_exit_was_reset(job):
        problems.append("check-all-windows resets LASTEXITCODE after the ffmpeg hash gate")
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
HASH_GATE_PARSER = ROOT / "scripts" / "check-ffmpeg-hash-gate.ps1"
HASH_GATE_PARSER_NEEDLES = (
    "Parser]::ParseInput",
    "EndBlock",
    "TrapStatementAst",
    "BreakStatementAst",
    "ContinueStatementAst",
    "ExitStatementAst",
    "ReturnStatementAst",
    "TokenKind]::Ine",
    "scripts/verify_ffmpeg_zip_sha256.py",
    "'if-zero'",
    "'if-null'",
    "'if-not'",
    "'if-bang'",
    "'if-parens'",
    "'if-var'",
    "'if-backtick'",
    "'while-false'",
    "'function-never'",
    "'scriptblock'",
    "'else-branch'",
    "'try-catch'",
    "'trap'",
    "'break-before'",
    "'midword-hash'",
)


def hash_gate_parser_problems(text: str) -> list[str]:
    """Linux presence pin. The parser itself runs on the Windows job."""
    problems: list[str] = []
    for needle in HASH_GATE_PARSER_NEEDLES:
        if needle not in text:
            problems.append(f"ffmpeg hash-gate parser missing {needle}")
    return problems


def drop_hash_gate_parser_step(job: str) -> str:
    """Mutation: the Windows job no longer invokes the parser allowlist."""
    mutated = job.replace(
        "scripts/check-ffmpeg-hash-gate.ps1",
        "scripts/check-ffmpeg-hash-gate-removed.ps1",
        1,
    )
    if mutated == job:
        raise ValueError("ffmpeg hash-gate parser step was not present to remove")
    return mutated


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
    try:
        reset = reset_ffmpeg_exit(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if not ffmpeg_sha_enforced(reset):
        fail("the LASTEXITCODE reset mutation must keep the -ne throw")
    reset_problems = windows_job_problems(reset)
    if not any(
        problem == "check-all-windows resets LASTEXITCODE after the ffmpeg hash gate"
        for problem in reset_problems
    ):
        fail("resetting LASTEXITCODE after the ffmpeg hash gate was not caught")
    try:
        creds = flip_persist_credentials(windows_job)
    except ValueError as exc:
        fail(str(exc))
    cred_problems = windows_job_problems(creds)
    if not any("persist-credentials: false" in problem for problem in cred_problems):
        fail("flipping persist-credentials to true was not caught")
    continue_variants = (
        "continue-on-error: true",
        '"continue-on-error": true',
        "'continue-on-error': true",
        "continue-on-error : true",
        '"continue-on-error" : true',
    )
    for line in continue_variants:
        try:
            continued = insert_windows_continue_on_error(windows_job, line)
        except ValueError as exc:
            fail(str(exc))
        if line != "continue-on-error: true" and "continue-on-error:" in line:
            fail("continue-on-error variant fixture still contains the bare needle")
        continued_problems = windows_job_problems(continued)
        if not any(
            problem == "check-all-windows must not continue on error"
            for problem in continued_problems
        ):
            fail("continue-on-error variant was not caught: " + line)
    if not HASH_GATE_PARSER.is_file():
        fail("missing ffmpeg hash-gate parser: scripts/check-ffmpeg-hash-gate.ps1")
    parser_text = HASH_GATE_PARSER.read_text(encoding="utf-8")
    for problem in hash_gate_parser_problems(parser_text):
        fail(problem)
    stripped = parser_text.replace("'if-zero'", "'gone'", 1)
    if stripped == parser_text:
        fail("if-zero mutant label was not present to delete")
    stripped_problems = hash_gate_parser_problems(stripped)
    if not any(
        problem == "ffmpeg hash-gate parser missing 'if-zero'"
        for problem in stripped_problems
    ):
        fail("deleting the if-zero mutant label was not caught")
    try:
        dropped_parser = drop_hash_gate_parser_step(windows_job)
    except ValueError as exc:
        fail(str(exc))
    dropped_parser_problems = windows_job_problems(dropped_parser)
    if not any(
        problem == "check-all-windows missing scripts/check-ffmpeg-hash-gate.ps1"
        for problem in dropped_parser_problems
    ):
        fail("removing the ffmpeg hash-gate parser step was not caught")
    throw_evidence = prove_ffmpeg_throw_reachable(windows_job)
    gate_evidence = prove_ffmpeg_hash_gate()
    print(
        "OK check-all-windows ffmpeg-sha-enforce "
        "delete=caught operator_flip=caught exit_reset=caught credentials=caught "
        f"continue_on_error=caught variants=quoted,spaced parser_step=caught label=caught {throw_evidence} "
        f"{gate_evidence} permissions=contents:read"
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
