#!/usr/bin/env python3
"""Refuse a floating pip, npm, or apt ffmpeg spec in a workflow command.

Every package token on a workflow `pip install` / `npm install` / `npm i`
line must be an exact pin (`name==1.2.3` or `name@1.2.3`). `npm ci` with no
package arguments is allowed. Arguments of `-r` / `--requirement` are lockfile
names, not package specs. INSTALL_SPEC_ALLOWLIST starts empty; a non-empty
committed set fails this sensor. An apt ffmpeg install must be one exact
command sequence on ubuntu-24.04. A node command must follow the pinned
setup-node step and its checksum command. A path, `env node`, `bash -c`,
and a `- run:` step still count. `if: false` and `continue-on-error: true`
on those steps are refused. Stdlib only.
"""
from __future__ import annotations

import re
import shlex
import sys
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


def looks_like_install(command: str) -> bool:
    return bool(re.search(
        r"(?:(?:^|\s)(?:python\S*|py)\s+-m\s+pip|pip3?)\s+install\b|\bnpm\s+(?:install|i|ci)\b",
        command,
    ))


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
        match = re.match(r"^(\s*)run:\s*([|>][-+]?)?\s*(.*)$", lines[index])
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
        argv = shlex.split(command, posix=True)
    except ValueError:
        return None
    while argv and "=" in argv[0] and not argv[0].startswith("-"):
        argv = argv[1:]
    if argv and argv[0] == "sudo":
        argv = argv[1:]
    return argv


def is_python(token: str) -> bool:
    base = token.rsplit("/", 1)[-1].lower()
    return base == "py" or base.startswith("python")


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
    if argv[0] in {"pip", "pip3"}:
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
    if argv[0] != "npm" or len(argv) < 2 or argv[1] not in {"install", "i", "ci"}:
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


NODE_PINS = {
    "24.21.0": (
        "python3 scripts/verify_actions_node_sha256.py --version 24.21.0 "
        "--filename node-24.21.0-linux-x64.tar.gz "
        "--expected ab971d19412a3b70ab4ef310656f5da973df476ccacd5cb4f49d447be2773227 "
        "--checksum-url https://github.com/actions/node-versions/releases/download/"
        "24.21.0-34304089047/hashes.sha256"
    ),
    "22.23.3": (
        "python3 scripts/verify_actions_node_sha256.py --version 22.23.3 "
        "--filename node-22.23.3-linux-x64.tar.gz "
        "--expected cf9cfe18f485ac615fbc237e269549f4014fd843395568cf81698ce1903e9bcf "
        "--checksum-url https://github.com/actions/node-versions/releases/download/"
        "22.23.3-35947643734/hashes.sha256"
    ),
}
NODE_SETUP = "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020"
EXPECTED_NODE_SETUPS = 2
NODE_SHELLS = {"bash", "sh", "dash", "zsh"}
NODE_SKIP = re.compile(
    r"""(?m)^[ \t]*(?:-[ \t]*)?(?:"""
    r"""if:[ \t]*(?:false|['"]false['"]|\$\{\{\s*false\s*\}\})"""
    r"""|continue-on-error:[ \t]*(?:true|['"]true['"])"""
    r""")[ \t]*(?:#.*)?$"""
)


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


def node_steps(job: str) -> list[str]:
    lines = job.splitlines()
    start = None
    indent = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)steps:\s*$", line)
        if match:
            indent = len(match.group(1))
            start = index + 1
            break
    if start is None:
        return []
    dash = indent + 2
    steps: list[list[str]] = []
    for line in lines[start:]:
        if line.strip() == "":
            if steps:
                steps[-1].append(line)
            continue
        lead = len(line) - len(line.lstrip(" "))
        if lead <= indent:
            break
        if lead == dash and line.lstrip().startswith("- "):
            steps.append([line])
            continue
        if steps:
            steps[-1].append(line)
    return ["\n".join(step) for step in steps]


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


def step_commands(step: str) -> list[str]:
    """Read run bodies, including a step written as `- run:`."""
    normalized = "\n".join(
        re.sub(r"^(\s*)-\s+run:", r"\1run:", line) for line in step.splitlines()
    )
    commands: list[str] = []
    for script in run_scripts(normalized):
        commands.extend(script_commands(script))
    return commands


def step_node_version(step: str) -> str | None:
    for line in step.splitlines():
        match = re.match(r"""^\s*node-version:\s*['"]?([^'"#\s]+)""", line)
        if match:
            return match.group(1)
    return None


def node_executable(token: str) -> bool:
    base = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if base.endswith(".exe"):
        base = base[:-4]
    return base == "node"


def is_node_command(command: str) -> bool:
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return False
    while argv and "=" in argv[0] and not argv[0].startswith("-"):
        argv = argv[1:]
    if argv and argv[0] == "sudo":
        argv = argv[1:]
    if not argv:
        return False
    if argv[0] == "env" or argv[0].endswith("/env"):
        rest = argv[1:]
        while rest and (rest[0].startswith("-") or "=" in rest[0]):
            rest = rest[1:]
        return bool(rest) and node_executable(rest[0])
    if node_executable(argv[0]):
        return True
    shell = argv[0].replace("\\", "/").rsplit("/", 1)[-1]
    if shell in NODE_SHELLS and "-c" in argv:
        idx = argv.index("-c")
        if idx + 1 < len(argv):
            return is_node_command(argv[idx + 1])
    return False


def node_toolchain_problems(text: str, *, path: str) -> list[str]:
    """A node command must follow an exact setup-node step and its checksum command."""
    problems: list[str] = []
    blocks = job_blocks(text)
    if not blocks and ("actions/setup-node@" in text or re.search(r"(?m)^\s*node ", text)):
        problems.append(f"{path} node command is outside a parsed job")
        return problems
    for job, block in blocks:
        steps = node_steps(block)
        pinned_until = -1
        for index, step in enumerate(steps):
            if "actions/setup-node@" not in step:
                continue
            if NODE_SETUP not in step:
                problems.append(f"{path} job {job} setup-node is not the pinned action")
            version = step_node_version(step)
            command = NODE_PINS.get(version or "")
            if command is None:
                problems.append(
                    f"{path} job {job} node-version {version!r} is not an exact toolchain pin"
                )
                continue
            if index + 1 >= len(steps) or step_commands(steps[index + 1]) != [command]:
                problems.append(f"{path} job {job} node toolchain command mismatch")
                continue
            disabled = NODE_SKIP.search(step) or NODE_SKIP.search(steps[index + 1])
            if disabled:
                problems.append(f"{path} job {job} node pin step is disabled")
                continue
            pinned_until = index + 1
        for index, step in enumerate(steps):
            for command in step_commands(step):
                if not is_node_command(command):
                    continue
                if index <= pinned_until:
                    problems.append(f"{path} job {job} node command before the toolchain pin")
                elif pinned_until < 0:
                    problems.append(f"{path} job {job} node command without a pinned toolchain")
    return problems


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


def main() -> int:
    if INSTALL_SPEC_ALLOWLIST:
        fail("INSTALL_SPEC_ALLOWLIST must stay empty")
    problems: list[str] = []
    workflows = sorted(WORKFLOWS.glob("*.y*ml"))
    node_setups = 0
    apt_workflows = 0
    for path in workflows:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        problems.extend(install_spec_problems(text, path=rel))
        problems.extend(node_toolchain_problems(text, path=rel))
        node_setups += text.count("actions/setup-node@")
        apt = apt_ffmpeg_problems(text, path=rel)
        if "apt-get install" in text or "apt-get download" in text:
            apt_workflows += 1
        problems.extend(apt)
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

    jobs = ROOT / ".github" / "workflows" / "jobs-write-through.yml"
    mutated = float_google_install(jobs.read_text(encoding="utf-8"))
    caught = install_spec_problems(mutated, path="jobs-write-through.yml")
    if not any("floating pip spec google-api-python-client" in item for item in caught):
        fail("reverted Google client install was not caught")
    if not any("floating pip spec google-auth" in item for item in caught):
        fail("reverted google-auth spec was not caught")
    if install_spec_problems(jobs.read_text(encoding="utf-8"), path="jobs-write-through.yml"):
        fail("pinned jobs-write-through install was refused")

    check_all = (WORKFLOWS / "check-all.yml").read_text(encoding="utf-8")
    observer = (WORKFLOWS / "instagram-read-source-observer.yml").read_text(encoding="utf-8")
    research = (WORKFLOWS / "velvetos-research.yml").read_text(encoding="utf-8")
    if node_toolchain_problems(check_all, path="check-all.yml"):
        fail(f"pinned check-all node was refused: {node_toolchain_problems(check_all, path='check-all.yml')}")
    if node_toolchain_problems(observer, path="instagram-read-source-observer.yml"):
        fail("pinned observer node was refused")
    if apt_ffmpeg_problems(check_all, path="check-all.yml"):
        fail(f"pinned check-all apt step was refused: {apt_ffmpeg_problems(check_all, path='check-all.yml')}")
    if apt_ffmpeg_problems(research, path="velvetos-research.yml"):
        fail("pinned velvetos-research apt step was refused")

    def require_node(label: str, mutated: str, needle: str) -> None:
        found = node_toolchain_problems(mutated, path="check-all.yml")
        if not any(needle in item for item in found):
            fail(f"{label} was not caught: {found}")

    require_node(
        "floating node 24",
        observer.replace('node-version: "24.21.0"', 'node-version: "24"', 1),
        "not an exact toolchain pin",
    )
    require_node(
        "digest swap",
        check_all.replace(
            "cf9cfe18f485ac615fbc237e269549f4014fd843395568cf81698ce1903e9bcf",
            "0" * 64,
            1,
        ),
        "command mismatch",
    )
    require_node(
        "commented verifier",
        check_all.replace(
            "run: python3 scripts/verify_actions_node_sha256.py",
            "run: # python3 scripts/verify_actions_node_sha256.py",
            1,
        ),
        "command mismatch",
    )
    bare_node = check_all.replace(
        """      - name: Set up Node
        # Image ubuntu-24.04 on 2026-10-19 had Node 22.23.3.
        # actions/setup-node v4.4.0
        uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020
        with:
          node-version: "22.23.3"

      - name: Verify Node toolchain checksum
        run: python3 scripts/verify_actions_node_sha256.py --version 22.23.3 --filename node-22.23.3-linux-x64.tar.gz --expected cf9cfe18f485ac615fbc237e269549f4014fd843395568cf81698ce1903e9bcf --checksum-url https://github.com/actions/node-versions/releases/download/22.23.3-35947643734/hashes.sha256

""",
        "",
        1,
    )
    require_node("runner node", bare_node, "without a pinned toolchain")

    def require_unpinned(label: str, command: str) -> None:
        sample = (
            "jobs:\n"
            "  sample:\n"
            "    runs-on: ubuntu-24.04\n"
            "    steps:\n"
            f"      - run: {command}\n"
        )
        found = node_toolchain_problems(sample, path="fixture.yml")
        if not any("without a pinned toolchain" in item for item in found):
            fail(f"{label} was not caught: {found}")

    require_unpinned("path node", "/usr/bin/node --version")
    require_unpinned("env node", "env node --version")
    require_unpinned("bash node", "bash -c 'node --version'")
    require_unpinned("dash run node", "node --version")
    require_node(
        "verify if false",
        check_all.replace(
            "      - name: Verify Node toolchain checksum\n        run:",
            "      - name: Verify Node toolchain checksum\n        if: false\n        run:",
            1,
        ),
        "node pin step is disabled",
    )
    require_node(
        "setup if expression false",
        check_all.replace(
            "      - name: Set up Node\n",
            "      - name: Set up Node\n        if: ${{ false }}\n",
            1,
        ),
        "node pin step is disabled",
    )
    require_node(
        "verify continue-on-error",
        check_all.replace(
            "      - name: Verify Node toolchain checksum\n        run:",
            "      - name: Verify Node toolchain checksum\n"
            "        continue-on-error: true\n        run:",
            1,
        ),
        "node pin step is disabled",
    )
    if node_setups != EXPECTED_NODE_SETUPS:
        fail(f"expected {EXPECTED_NODE_SETUPS} setup-node steps, found {node_setups}")
    probe = __import__("subprocess").run(
        [sys.executable, str(ROOT / "scripts" / "verify_actions_node_sha256.py"), "--self-test"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if probe.returncode != 0:
        fail(probe.stderr.strip() or probe.stdout.strip() or "node toolchain self-test failed")

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

    print(
        f"OK {NAME} workflows={len(workflows)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        f"node_setups={node_setups} node_float=caught node_sha=caught "
        "node_comment=caught node_bare=caught node_path=caught node_env=caught "
        "node_bash=caught node_dash=caught node_if=caught node_continue=caught "
        f"apt_ffmpeg={apt_workflows} apt_sequence=pinned extra=caught "
        "comment=caught digest=caught runner=caught pool=caught"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
