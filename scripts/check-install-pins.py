#!/usr/bin/env python3
"""Refuse a floating pip or npm spec in a workflow command.

Every package token on a workflow `pip install` / `npm install` / `npm i`
line must be an exact pin (`name==1.2.3` or `name@1.2.3`). `npm ci` with no
package arguments is allowed. Arguments of `-r` / `--requirement` are lockfile
names, not package specs. INSTALL_SPEC_ALLOWLIST starts empty; a non-empty
committed set fails this sensor. Stdlib only.
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


PYTHON_PINS = {
    "3.11.17": {
        "runs_on": "ubuntu-24.04",
        "command": (
            "python3 scripts/verify_actions_python_sha256.py --version 3.11.17 "
            "--filename python-3.11.17-linux-24.04-x64.tar.gz "
            "--expected ae713815fe406a06f1691856f697a0b1e58b3e986f44e62f0cd0bca2424f1aac "
            "--checksum-url https://github.com/actions/python-versions/releases/download/"
            "3.11.17-36876195594/hashes.sha256"
        ),
    },
    "3.12.15": {
        "runs_on": "ubuntu-24.04",
        "command": (
            "python3 scripts/verify_actions_python_sha256.py --version 3.12.15 "
            "--filename python-3.12.15-linux-24.04-x64.tar.gz "
            "--expected fcb672b0437c2d8df5565b7cc250b2b0d7455e2b8d6a4a107cfa6f2efe4f7ed8 "
            "--checksum-url https://github.com/actions/python-versions/releases/download/"
            "3.12.15-36805895057/hashes.sha256"
        ),
    },
    "3.11.9": {
        "runs_on": "windows-latest",
        "command": (
            "python scripts/verify_actions_python_sha256.py --version 3.11.9 "
            "--filename python-3.11.9-win32-x64.zip "
            "--expected c92a530d9ac9539feea075bb033e7e03580412999d2e2833b7b62d948da60d03 "
            "--checksum-url https://github.com/actions/python-versions/releases/download/"
            "3.11.9-9947079978/hashes.sha256"
        ),
    },
}
EXPECTED_PYTHON_SETUPS = 13


def job_blocks(text: str) -> list[tuple[str, str]]:
    """Split top-level jobs by indent. This is not a YAML loader."""
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


def workflow_steps(job: str) -> list[str]:
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


def script_commands(script: str) -> list[str]:
    commands: list[str] = []
    for line in join_continuations(script).splitlines():
        command = strip_comment(line)
        if command:
            commands.append(command)
    return commands


def step_python_version(step: str) -> str | None:
    for line in step.splitlines():
        match = re.match(r"""^\s*python-version:\s*['"]?([^'"#\s]+)""", line)
        if match:
            return match.group(1)
    return None


def python_toolchain_problems(text: str, *, path: str) -> list[str]:
    """Each setup-python step is an exact patch plus the next checksum command."""
    problems: list[str] = []
    blocks = job_blocks(text)
    if not blocks and "actions/setup-python@" in text:
        problems.append(f"{path} setup-python is outside a parsed job")
        return problems
    for job, block in blocks:
        steps = workflow_steps(block)
        for index, step in enumerate(steps):
            if "actions/setup-python@" not in step:
                continue
            version = step_python_version(step)
            pin = PYTHON_PINS.get(version or "")
            if pin is None:
                problems.append(
                    f"{path} job {job} python-version {version!r} is not an exact toolchain pin"
                )
                continue
            runs_on = job_runs_on(block)
            if runs_on != pin["runs_on"]:
                problems.append(
                    f"{path} job {job} runs-on {runs_on!r} is not {pin['runs_on']}"
                )
            if index + 1 >= len(steps):
                problems.append(f"{path} job {job} python toolchain checksum step is missing")
                continue
            commands: list[str] = []
            for script in run_scripts(steps[index + 1]):
                commands.extend(script_commands(script))
            if commands != [pin["command"]]:
                problems.append(f"{path} job {job} python toolchain command mismatch")
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
    python_setups = 0
    for path in workflows:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        problems.extend(install_spec_problems(text, path=rel))
        problems.extend(python_toolchain_problems(text, path=rel))
        python_setups += text.count("actions/setup-python@")
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
    research = (WORKFLOWS / "velvetos-research.yml").read_text(encoding="utf-8")
    if python_toolchain_problems(check_all, path="check-all.yml"):
        fail(f"pinned check-all python was refused: {python_toolchain_problems(check_all, path='check-all.yml')}")
    if python_toolchain_problems(research, path="velvetos-research.yml"):
        fail("pinned velvetos-research python was refused")

    def require_python(label: str, mutated: str, needle: str) -> None:
        found = python_toolchain_problems(mutated, path="check-all.yml")
        if not any(needle in item for item in found):
            fail(f"{label} was not caught: {found}")

    require_python(
        "floating 3.11",
        check_all.replace('python-version: "3.11.17"', 'python-version: "3.11"', 1),
        "not an exact toolchain pin",
    )
    require_python(
        "digest swap",
        check_all.replace(
            "ae713815fe406a06f1691856f697a0b1e58b3e986f44e62f0cd0bca2424f1aac",
            "0" * 64,
            1,
        ),
        "command mismatch",
    )
    require_python(
        "commented verifier",
        check_all.replace(
            "run: python3 scripts/verify_actions_python_sha256.py",
            "run: # python3 scripts/verify_actions_python_sha256.py",
            1,
        ),
        "command mismatch",
    )
    require_python(
        "ubuntu-latest runner",
        check_all.replace("    runs-on: ubuntu-24.04\n", "    runs-on: ubuntu-latest\n", 1),
        "ubuntu-24.04",
    )
    require_python(
        "windows patch upgrade",
        check_all.replace('python-version: "3.11.9"', 'python-version: "3.11.17"', 1),
        "command mismatch",
    )
    if python_setups != EXPECTED_PYTHON_SETUPS:
        fail(f"expected {EXPECTED_PYTHON_SETUPS} setup-python steps, found {python_setups}")
    verifier = ROOT / "scripts" / "verify_actions_python_sha256.py"
    probe = __import__("subprocess").run(
        [sys.executable, str(verifier), "--self-test"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if probe.returncode != 0:
        fail(probe.stderr.strip() or probe.stdout.strip() or "python toolchain self-test failed")

    print(
        f"OK {NAME} workflows={len(workflows)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        f"python_setups={python_setups} python_float=caught python_sha=caught "
        "python_comment=caught python_runner=caught"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
