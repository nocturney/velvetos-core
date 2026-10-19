#!/usr/bin/env python3
"""Refuse a floating pip, npm, or apt ffmpeg spec in a workflow command.

Every package token on a workflow or composite-action `pip install` /
`npm install` / `npm i` line must be an exact pin (`name==1.2.3` or
`name@1.2.3`). The installer name is the basename, lowercased, with one
`.exe` or `.cmd` suffix removed. Pip then matches `pip`, `pip3`, or
`pip3.<digits>`. npm matches `npm`, `npm.cmd`, or `npm.exe`.
`npm ci` with no package arguments is allowed. Arguments of `-r` /
`--requirement` are lockfile names, not package specs. INSTALL_SPEC_ALLOWLIST
starts empty; a non-empty committed set fails this sensor. An apt ffmpeg
install must be one exact command sequence on ubuntu-24.04. Stdlib only.
"""
from __future__ import annotations

import re
import shlex
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "install-pins"
WORKFLOWS = ROOT / ".github" / "workflows"
INSTALL_SPEC_ALLOWLIST: frozenset[str] = frozenset()

EXACT_PIP = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9._,-]+\])?=="
    r"[0-9]+(?:\.[0-9]+)*(?:(?:a|b|rc|post|dev)[0-9]+)?(?:\+[A-Za-z0-9.]+)?$"
)
EXACT_NPM = re.compile(
    r"^(?:@[A-Za-z0-9._-]+/)?[A-Za-z0-9._-]+@"
    r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?$"
)
PIP_VALUE_FLAGS = {
    "-r", "--requirement",
    "-c", "--constraint",
    "-i", "--index-url",
    "--extra-index-url",
    "-f", "--find-links",
    "--trusted-host",
    "-t", "--target",
    "--prefix",
    "--src",
    "--root",
    "--log",
    "--report",
    "--config-settings",
    "--no-binary",
    "--only-binary",
    "--implementation",
    "--platform",
    "--python-version",
    "--abi",
    "--upgrade-strategy",
    "--group",
}
NPM_VALUE_FLAGS = {"--prefix", "--registry", "--userconfig", "--cache", "--globalconfig"}
FLOATING_GOOGLE = "pip install --quiet google-api-python-client google-auth"
LOCK_NAME = "requirements-google-clients.py311.lock"
APT_FFMPEG_VERSION = "ffmpeg=7:6.1.1-3ubuntu5"
APT_FFMPEG_SHA256 = "1a23baace5f2688a47e28119aedae6993cd638e6279a7227dfc52d9a337a1c17"
APT_RUNS_ON = "ubuntu-24.04"
APT_POOL_DEB = "ffmpeg_6.1.1-3ubuntu5_amd64.deb"
# Contiguous comment-stripped lines. The cache basename keeps the epoch as %3a.
APT_FFMPEG_COMMANDS = (
    "sudo apt-get update -qq",
    f"sudo apt-get install -y -d '{APT_FFMPEG_VERSION}'",
    "shopt -s nullglob",
    "matches=(/var/cache/apt/archives/ffmpeg_*6.1.1-3ubuntu5_amd64.deb)",
    'if [ "${#matches[@]}" -ne 1 ]; then',
    "printf 'FAIL apt ffmpeg deb count=%s\\n' \"${#matches[@]}\" >&2",
    "exit 1",
    "fi",
    'deb="${matches[0]}"',
    "if [ \"$(basename \"$deb\")\" != 'ffmpeg_7%3a6.1.1-3ubuntu5_amd64.deb' ]; then",
    "printf 'FAIL apt ffmpeg cache name=%s\\n' \"$(basename \"$deb\")\" >&2",
    "exit 1",
    "fi",
    'python3 scripts/verify_ffmpeg_zip_sha256.py --path "$deb" --expected '
    f'"{APT_FFMPEG_SHA256}" --kind deb',
    'sudo apt-get install -y "$deb"',
)
APT_ALLOWED_INSTALLS = frozenset({
    APT_FFMPEG_COMMANDS[1],
    APT_FFMPEG_COMMANDS[-1],
})


def fail(msg: str) -> None:
    print(f"FAIL {NAME}: {msg}", file=sys.stderr)
    raise SystemExit(1)


def strip_comment(line: str) -> str:
    out: list[str] = []
    quote = ""
    for char in line:
        if quote:
            out.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            out.append(char)
            continue
        if char == "#":
            break
        out.append(char)
    return "".join(out).strip()


def join_continuations(script: str) -> str:
    joined: list[str] = []
    buf = ""
    for line in script.splitlines():
        piece = line.strip()
        if buf:
            buf += " " + piece
        else:
            buf = piece
        if buf.endswith("\\"):
            buf = buf[:-1].rstrip()
            continue
        joined.append(buf)
        buf = ""
    if buf:
        joined.append(buf)
    return "\n".join(joined)


# Path and version suffixes stay visible here. Classification uses command_name.
_INSTALL_LOOK = re.compile(
    r"(?:(?:^|\s)(?:python\S*|py)\s+-m\s+pip|pip3?(?:\.\d+)?(?:\.exe|\.cmd)?)\s+install\b"
    r"|\bnpm(?:\.cmd|\.exe)?\s+(?:install|i|ci)\b",
    re.IGNORECASE,
)


def looks_like_install(command: str) -> bool:
    return _INSTALL_LOOK.search(command) is not None


def split_commands(script: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    quote = ""
    i = 0
    while i < len(script):
        char = script[i]
        if quote:
            buf.append(char)
            if char == quote:
                quote = ""
            i += 1
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            i += 1
            continue
        if script.startswith("&&", i) or script.startswith("||", i):
            parts.append("".join(buf))
            buf = []
            i += 2
            continue
        if char in {";", "|", "\n"}:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(char)
        i += 1
    parts.append("".join(buf))
    return [part.strip() for part in parts if part.strip()]


def run_scripts(text: str) -> list[str]:
    lines = text.splitlines()
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)(?:-\s+)?run:\s*([|>][-+]?)?\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent, block, inline = match.group(1), match.group(2), match.group(3)
        if not block:
            scripts.append(inline)
            index += 1
            continue
        index += 1
        body: list[str] = []
        while index < len(lines):
            nxt = lines[index]
            if nxt.strip() == "":
                body.append("")
                index += 1
                continue
            if len(nxt) - len(nxt.lstrip(" ")) <= len(indent):
                break
            body.append(nxt.strip())
            index += 1
        scripts.append("\n".join(body))
    return scripts


def argv_of(command: str) -> list[str] | None:
    try:
        # POSIX shlex eats `\`, so a Windows tool path would lose its basename.
        argv = shlex.split(command.replace("\\", "/"), posix=True)
    except ValueError:
        return None
    while argv and "=" in argv[0] and not argv[0].startswith("-"):
        argv = argv[1:]
    if argv and argv[0] == "sudo":
        argv = argv[1:]
    return argv


PIP_BIN = re.compile(r"^pip3?(?:\.\d+)?$")
NPM_BIN = re.compile(r"^npm(?:\.cmd|\.exe)?$")


def command_name(token: str) -> str:
    """Basename, lowercase, then one `.exe` or `.cmd` suffix removed."""
    base = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if base.endswith(".exe") or base.endswith(".cmd"):
        base = base[:-4]
    return base


def is_python(token: str) -> bool:
    base = command_name(token)
    return base == "py" or base.startswith("python")


def is_pip_command(token: str) -> bool:
    return PIP_BIN.fullmatch(command_name(token)) is not None


def is_npm_command(token: str) -> bool:
    """Match npm, npm.cmd, or npm.exe on the basename and on the stripped name."""
    base = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return NPM_BIN.fullmatch(base) is not None or NPM_BIN.fullmatch(command_name(token)) is not None


def package_tokens(args: list[str], value_flags: set[str]) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("-"):
            flag = token.split("=", 1)[0]
            if "=" not in token and flag in value_flags:
                index += 2
                continue
            index += 1
            continue
        tokens.append(token)
        index += 1
    return tokens


def command_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    problems: list[str] = []
    if not argv:
        return problems
    pip_args: list[str] | None = None
    if is_pip_command(argv[0]):
        pip_args = argv[1:]
    elif len(argv) >= 3 and is_python(argv[0]) and argv[1] == "-m" and argv[2] == "pip":
        pip_args = argv[3:]
    if pip_args is not None:
        if not pip_args or pip_args[0] != "install":
            return problems
        for token in package_tokens(pip_args[1:], PIP_VALUE_FLAGS):
            if EXACT_PIP.fullmatch(token) or token in allowlist:
                continue
            problems.append(f"{path} floating pip spec {token}")
        return problems
    if not is_npm_command(argv[0]) or len(argv) < 2 or argv[1] not in {"install", "i", "ci"}:
        return problems
    kind = argv[1]
    tokens = package_tokens(argv[2:], NPM_VALUE_FLAGS)
    if kind == "ci" and not tokens:
        return problems
    if kind in {"install", "i"} and not tokens:
        problems.append(f"{path} npm install has no exact package spec")
        return problems
    for token in tokens:
        if EXACT_NPM.fullmatch(token) or token in allowlist:
            continue
        problems.append(f"{path} floating npm spec {token}")
    return problems


def install_spec_problems(
    text: str,
    *,
    path: str,
    allowlist: frozenset[str] | None = None,
) -> list[str]:
    chosen = INSTALL_SPEC_ALLOWLIST if allowlist is None else allowlist
    problems: list[str] = []
    for script in run_scripts(text):
        for command in split_commands(join_continuations(script)):
            command = strip_comment(command)
            if not command or not looks_like_install(command):
                continue
            argv = argv_of(command)
            if argv is None:
                problems.append(f"{path} unparsable install command")
                continue
            problems.extend(command_problems(argv, path=path, allowlist=chosen))
    return problems


def job_blocks(text: str) -> list[tuple[str, str]]:
    """Split top-level `jobs:` entries. Indent is the structure; this is not a YAML loader."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^jobs:\s*$", line):
            start = index + 1
            break
    if start is None:
        return []
    blocks: list[tuple[str, str]] = []
    name: str | None = None
    body: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        match = re.match(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*(?:#.*)?$", line)
        if match:
            if name is not None:
                blocks.append((name, "\n".join(body)))
            name = match.group(1)
            body = [line]
            continue
        if name is not None:
            body.append(line)
    if name is not None:
        blocks.append((name, "\n".join(body)))
    return blocks


def job_runs_on(block: str) -> str | None:
    for line in block.splitlines():
        match = re.match(r"^    runs-on:\s*(.*?)\s*$", line)
        if not match:
            continue
        raw = strip_comment(match.group(1))
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            raw = raw[1:-1]
        return raw
    return None


def script_commands(script: str) -> list[str]:
    commands: list[str] = []
    for line in join_continuations(script).splitlines():
        command = strip_comment(line)
        if command:
            commands.append(command)
    return commands


def count_sequence(lines: list[str], seq: tuple[str, ...]) -> int:
    width = len(seq)
    if width == 0 or len(lines) < width:
        return 0
    return sum(tuple(lines[index:index + width]) == seq for index in range(len(lines) - width + 1))


def apt_ffmpeg_problems(text: str, *, path: str) -> list[str]:
    """The noble ffmpeg step is one exact command slice on ubuntu-24.04."""
    problems: list[str] = []
    blocks = job_blocks(text)
    apt_re = re.compile(r"\bapt-get\s+(install|download)\b")
    if not blocks and apt_re.search(text):
        problems.append(f"{path} apt command is outside a parsed job")
        return problems
    for job, block in blocks:
        raw_hits = [
            strip_comment(line)
            for line in block.splitlines()
            if apt_re.search(strip_comment(line))
        ]
        if not raw_hits:
            continue
        commands = []
        for script in run_scripts(block):
            commands.extend(script_commands(script))
        if any(hit not in commands for hit in raw_hits):
            problems.append(f"{path} job {job} apt command was not parsed from a run step")
        runs_on = job_runs_on(block)
        if runs_on != APT_RUNS_ON:
            problems.append(f"{path} job {job} runs-on {runs_on!r} is not {APT_RUNS_ON}")
        if count_sequence(commands, APT_FFMPEG_COMMANDS) != 1:
            problems.append(f"{path} job {job} apt ffmpeg command sequence mismatch")
        for command in commands:
            if apt_re.search(command) and command not in APT_ALLOWED_INSTALLS:
                problems.append(f"{path} job {job} unexpected apt-get install: {command}")
            if APT_POOL_DEB in command:
                problems.append(f"{path} job {job} apt ffmpeg uses the pool filename")
            if re.search(r"\btest\s+-f\b", command) and "ffmpeg" in command:
                problems.append(f"{path} job {job} apt ffmpeg uses test -f")
    return problems


def float_google_install(text: str) -> str:
    """Mutation: put the pre-pin bare names back on the Google client install."""
    lines = text.splitlines(keepends=True)
    found = 0
    out: list[str] = []
    for line in lines:
        if LOCK_NAME in line and "pip install" in line:
            indent = re.match(r"^\s*", line).group(0)
            newline = "\n" if line.endswith("\n") else ""
            prefix = "run: " if "run:" in line else ""
            out.append(f"{indent}{prefix}{FLOATING_GOOGLE}{newline}")
            found += 1
        else:
            out.append(line)
    if found != 1:
        raise ValueError(f"expected one Google client install, found {found}")
    return "".join(out)


def workflow_files(root: Path) -> list[Path]:
    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        return []
    return sorted(path for path in folder.glob("*.y*ml") if path.is_file())


def action_files(root: Path) -> list[Path]:
    folder = root / ".github" / "actions"
    if not folder.is_dir():
        return []
    return sorted(path for path in folder.glob("**/action.y*ml") if path.is_file())


def main() -> int:
    if INSTALL_SPEC_ALLOWLIST:
        fail("INSTALL_SPEC_ALLOWLIST must stay empty")
    problems: list[str] = []
    workflows = workflow_files(ROOT)
    actions = action_files(ROOT)
    apt_workflows = 0
    for path in workflows:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        problems.extend(install_spec_problems(text, path=rel))
        apt = apt_ffmpeg_problems(text, path=rel)
        if "apt-get install" in text or "apt-get download" in text:
            apt_workflows += 1
        problems.extend(apt)
    for path in actions:
        rel = path.relative_to(ROOT).as_posix()
        problems.extend(install_spec_problems(path.read_text(encoding="utf-8"), path=rel))
    if problems:
        for item in problems:
            print(f"FAIL {NAME}: {item}", file=sys.stderr)
        return 1

    bare = "run: pip install google-api-python-client\n"
    exact = "run: pip install google-api-python-client==2.201.0 google-auth==2.62.0\n"
    mixed = "run: pip install google-api-python-client==2.201.0 google-auth\n"
    hashed = (
        "run: python3 -m pip install --disable-pip-version-check "
        "--require-hashes -r requirements-sensors.py311.lock\n"
    )
    npm_float = "run: npm install left-pad\n"
    npm_exact = "run: npm install left-pad@1.2.3\n"
    npm_ci = "run: npm ci --ignore-scripts\n"
    controls = {
        "bare": install_spec_problems(bare, path="fixture.yml"),
        "exact": install_spec_problems(exact, path="fixture.yml"),
        "mixed": install_spec_problems(mixed, path="fixture.yml"),
        "hashed": install_spec_problems(hashed, path="fixture.yml"),
        "npm_float": install_spec_problems(npm_float, path="fixture.yml"),
        "npm_exact": install_spec_problems(npm_exact, path="fixture.yml"),
        "npm_ci": install_spec_problems(npm_ci, path="fixture.yml"),
        "allow_one": install_spec_problems(
            npm_float, path="fixture.yml", allowlist=frozenset({"left-pad"})
        ),
    }
    if not any("floating pip spec google-api-python-client" in item for item in controls["bare"]):
        fail("bare pip spec was not caught")
    if controls["exact"] or controls["hashed"] or controls["npm_exact"] or controls["npm_ci"]:
        fail(f"exact or hashed install was refused: {controls}")
    if not any("floating pip spec google-auth" in item for item in controls["mixed"]):
        fail("mixed bare token was not caught")
    if any("google-api-python-client" in item for item in controls["mixed"]):
        fail("exact pin in a mixed command was flagged")
    if not any("floating npm spec left-pad" in item for item in controls["npm_float"]):
        fail("npm install left-pad was not caught")
    if controls["allow_one"]:
        fail("allowlist override did not accept left-pad")

    def require_spec(label: str, text: str, needle: str) -> None:
        found = install_spec_problems(text, path="fixture.yml")
        if not any(needle in item for item in found):
            fail(f"{label} was not caught: {found}")

    def allow_spec(label: str, text: str) -> None:
        found = install_spec_problems(text, path="fixture.yml")
        if found:
            fail(f"{label} was refused: {found}")

    require_spec(
        "abs pip",
        "run: /usr/bin/pip install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "abs pip3",
        "run: /usr/local/bin/pip3 install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "dot pip",
        "run: ./pip install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "pip.exe",
        "run: pip.exe install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "PIP.EXE",
        "run: PIP.EXE install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "pip3.11",
        "run: pip3.11 install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "pip3.12",
        "run: pip3.12 install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "windows pip.exe",
        "run: C:\\Python\\Scripts\\pip.exe install google-api-python-client\n",
        "floating pip spec google-api-python-client",
    )
    require_spec(
        "abs npm",
        "run: /usr/bin/npm install left-pad\n",
        "floating npm spec left-pad",
    )
    require_spec(
        "npm.cmd",
        "run: npm.cmd install left-pad\n",
        "floating npm spec left-pad",
    )
    require_spec(
        "npm.exe",
        "run: npm.exe install left-pad\n",
        "floating npm spec left-pad",
    )
    require_spec(
        "compact run",
        "- run: /usr/bin/pip install some-malicious-pkg\n",
        "floating pip spec some-malicious-pkg",
    )
    if not looks_like_install("pip3.11 install google-api-python-client"):
        fail("pip3.11 was invisible to the install scan")
    if not looks_like_install("pip3.12 install google-api-python-client"):
        fail("pip3.12 was invisible to the install scan")
    allow_spec("abs exact pip", "run: /usr/bin/pip install google-api-python-client==2.201.0\n")
    allow_spec("pip3.11 exact", "run: pip3.11 install google-auth==2.62.0\n")
    allow_spec("pip.exe exact", "run: pip.exe install google-api-python-client==2.201.0\n")
    allow_spec("abs npm exact", "run: /usr/bin/npm install left-pad@1.2.3\n")
    allow_spec("abs npm ci", "run: /usr/bin/npm ci --ignore-scripts\n")

    jobs = ROOT / ".github" / "workflows" / "jobs-write-through.yml"
    mutated = float_google_install(jobs.read_text(encoding="utf-8"))
    caught = install_spec_problems(mutated, path="jobs-write-through.yml")
    if not any("floating pip spec google-api-python-client" in item for item in caught):
        fail("reverted Google client install was not caught")
    if not any("floating pip spec google-auth" in item for item in caught):
        fail("reverted google-auth spec was not caught")
    jobs_text = jobs.read_text(encoding="utf-8")
    if install_spec_problems(jobs_text, path="jobs-write-through.yml"):
        fail("pinned jobs-write-through install was refused")
    sneak_line = (
        "run: python3 -m pip install --disable-pip-version-check "
        "--require-hashes -r requirements-google-clients.py311.lock\n"
    )
    sneak = jobs_text.replace(
        sneak_line,
        sneak_line
        + "      - name: Sneak in an unpinned backdoor dependency\n"
        + "        run: /usr/bin/pip install some-malicious-pkg\n",
        1,
    )
    if sneak == jobs_text:
        fail("could not plant the path-qualified pip mutant")
    sneak_found = install_spec_problems(sneak, path="jobs-write-through.yml")
    if not any("floating pip spec some-malicious-pkg" in item for item in sneak_found):
        fail(f"path-qualified pip install in jobs-write-through was not caught: {sneak_found}")
    if any("requirements-google-clients" in item for item in sneak_found):
        fail("pinned lock install was flagged beside the path mutant")

    check_all = (WORKFLOWS / "check-all.yml").read_text(encoding="utf-8")
    research = (WORKFLOWS / "velvetos-research.yml").read_text(encoding="utf-8")
    if apt_ffmpeg_problems(check_all, path="check-all.yml"):
        fail(f"pinned check-all apt step was refused: {apt_ffmpeg_problems(check_all, path='check-all.yml')}")
    if apt_ffmpeg_problems(research, path="velvetos-research.yml"):
        fail("pinned velvetos-research apt step was refused")

    def require_apt(label: str, mutated: str, needle: str) -> None:
        found = apt_ffmpeg_problems(mutated, path="check-all.yml")
        if not any(needle in item for item in found):
            fail(f"{label} was not caught: {found}")

    extra = check_all.replace(
        'sudo apt-get install -y "$deb"\n',
        'sudo apt-get install -y "$deb"\n          sudo apt-get install -y ffmpeg\n',
        1,
    )
    require_apt("extra apt install", extra, "unexpected apt-get install")
    replaced = check_all.replace(
        'sudo apt-get install -y "$deb"',
        "sudo apt-get install -y ffmpeg",
        1,
    )
    require_apt("replaced final install", replaced, "command sequence mismatch")
    commented = check_all.replace(
        "python3 scripts/verify_ffmpeg_zip_sha256.py",
        "# python3 scripts/verify_ffmpeg_zip_sha256.py",
        1,
    )
    require_apt("commented verifier", commented, "command sequence mismatch")
    dropped_sha = check_all.replace(APT_FFMPEG_SHA256, "0" * 64, 1)
    require_apt("digest swap", dropped_sha, "command sequence mismatch")
    latest = check_all.replace("    runs-on: ubuntu-24.04\n", "    runs-on: ubuntu-latest\n", 1)
    require_apt("ubuntu-latest runner", latest, APT_RUNS_ON)
    pool = check_all.replace(
        "matches=(/var/cache/apt/archives/ffmpeg_*6.1.1-3ubuntu5_amd64.deb)",
        "deb=/var/cache/apt/archives/ffmpeg_6.1.1-3ubuntu5_amd64.deb\n          test -f \"$deb\"",
        1,
    )
    require_apt("pool filename", pool, "pool filename")
    floating_apt = (
        "jobs:\n"
        "  sample:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: sudo apt-get install -y ffmpeg\n"
    )
    floating_found = apt_ffmpeg_problems(floating_apt, path="fixture.yml")
    if not any("command sequence mismatch" in item for item in floating_found):
        fail(f"floating apt ffmpeg was not caught: {floating_found}")
    if not any(APT_RUNS_ON in item for item in floating_found):
        fail(f"floating apt runner was not caught: {floating_found}")
    if apt_workflows != 2:
        fail(f"expected 2 apt ffmpeg workflows, found {apt_workflows}")

    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp)
        floating_action = probe / ".github" / "actions" / "sneak" / "action.yml"
        pinned_action = probe / ".github" / "actions" / "ok" / "action.yaml"
        decoy = probe / ".github" / "actions" / "sneak" / "steps.yml"
        floating_action.parent.mkdir(parents=True)
        pinned_action.parent.mkdir(parents=True)
        floating_action.write_text(
            "runs:\n  using: composite\n  steps:\n"
            "    - name: Sneak\n"
            "      run: /usr/bin/pip install some-malicious-pkg\n",
            encoding="utf-8",
        )
        pinned_action.write_text(
            "runs:\n  using: composite\n  steps:\n"
            "    - run: pip3.12 install google-auth==2.62.0\n",
            encoding="utf-8",
        )
        decoy.write_text("run: pip install some-malicious-pkg\n", encoding="utf-8")
        scanned = {path.resolve() for path in action_files(probe)}
        if floating_action.resolve() not in scanned or pinned_action.resolve() not in scanned:
            fail(f"composite action.yml was not scanned: {sorted(scanned)}")
        if decoy.resolve() in scanned:
            fail("non-action yaml under .github/actions was scanned")
        action_found = install_spec_problems(
            floating_action.read_text(encoding="utf-8"),
            path=".github/actions/sneak/action.yml",
        )
        if not any("floating pip spec some-malicious-pkg" in item for item in action_found):
            fail(f"composite action floating pip was not caught: {action_found}")
        if install_spec_problems(
            pinned_action.read_text(encoding="utf-8"),
            path=".github/actions/ok/action.yaml",
        ):
            fail("pinned composite action install was refused")

    print(
        f"OK {NAME} workflows={len(workflows)} actions={len(actions)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        f"apt_ffmpeg={apt_workflows} apt_sequence=pinned extra=caught "
        "comment=caught digest=caught runner=caught pool=caught "
        "path=caught versioned=caught action=caught"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
