#!/usr/bin/env python3
"""Refuse a floating install spec in a workflow command.

Every package token on a workflow pip, npm, uv, pipx, yarn, pnpm, or npx
install must be an exact pin (`name==1.2.3` or `name@1.2.3`). `npm ci`,
`yarn install`, and `pnpm install` with no package arguments are allowed.
Arguments of `-r` / `--requirement` are lockfile names, not package specs.

Wrappers are part of the command: `sudo -H`, `env`, `bash -c` / `sh -c`,
a subshell, `$(...)`, and `python -I -m pip`. Flags may sit before the
subcommand (`pip -q install`, `python -m pip -q`, `python -mpip`,
`pip3.11`). An armed package-manager executable (`pip*`, `python -m pip`
/ `-mpip`, `uv`/`uvx`, `pipx`, `npm`/`npx`, `pnpm`, `yarn`, `bun`) must
be a pinned or lock install, or it is refused as unclassified.

`requirements-google-clients.py311.lock` must keep the direct pins from
`requirements-google-clients.txt`, and every lock pin must have a sha256
hash. INSTALL_SPEC_ALLOWLIST starts empty; a non-empty committed set fails
this sensor. Stdlib only.
"""
from __future__ import annotations

import re
import shlex
import sys
from dataclasses import dataclass
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
PIN_RE = re.compile(
    r"^([A-Za-z0-9_.\-]+)==([^\s;\\]+)\s*(?:;\s*([^\\#]+?))?\s*(?:\\|#.*)?$"
)
PIP_INSTALL_RE = re.compile(r"(?<![\w.-])pip3?\s+install\b")
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
UV_ADD_VALUE_FLAGS = {
    "--extra", "--optional", "--index", "--index-url", "--default-index",
    "--python", "--prefix", "--constraint", "--override", "--group",
}
PIPX_VALUE_FLAGS = {"--python", "--pip-args", "--index-url", "-i", "--preinstall", "--suffix"}
YARN_VALUE_FLAGS = {"--registry", "--cwd", "--cache-folder", "--modules-folder", "--prefix"}
PNPM_VALUE_FLAGS = {"--registry", "--dir", "--filter", "--store-dir", "--config", "--prefix"}
NPX_VALUE_FLAGS = {"-p", "--package", "-c", "--call", "--registry", "--userconfig", "--cache", "--prefix"}
SUDO_VALUE_FLAGS = {"-u", "-g", "-h", "-p", "-C", "-D", "--user", "--group", "--host", "--prompt", "--chdir"}
ENV_VALUE_FLAGS = {"-u", "--unset", "-S", "--split-string", "-C", "--chdir"}
PIP_GLOBAL_VALUE = {
    "-i", "--index-url", "--extra-index-url", "--trusted-host",
    "--timeout", "--retries", "--log", "--cache-dir", "--proxy",
    "--cert", "--client-cert", "--python", "--exists-action",
    "-f", "--find-links", "-c", "--constraint",
    "--report", "--config-settings",
}
UV_GLOBAL_VALUE = {"--python", "--cache-dir", "--directory", "--project", "--no-project"}
UNCLASSIFIED = "unclassified install command"
SHELLS = {"bash", "sh", "dash"}
FLOATING_GOOGLE = "pip install --quiet google-api-python-client google-auth"
LOCK_NAME = "requirements-google-clients.py311.lock"
REQ_NAME = "requirements-google-clients.txt"


@dataclass(frozen=True)
class InstallRules:
    wrappers: bool = True
    uv: bool = True
    pipx: bool = True
    yarn: bool = True
    pnpm: bool = True
    npx: bool = True
    pip_forms: bool = True
    npm_aliases: bool = True
    bun: bool = True
    lock_versions: bool = True
    lock_hashes: bool = True


def fail(msg: str) -> None:
    print(f"FAIL {NAME}: {msg}", file=sys.stderr)
    raise SystemExit(1)


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _base(token: str) -> str:
    return token.rsplit("/", 1)[-1].lower()


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


def _preceded_by_uv(command: str, start: int) -> bool:
    return bool(re.search(r"(?:^|[\s;|&(])uv$", command[:start].rstrip()))


def has_non_uv_pip_install(command: str) -> bool:
    return any(not _preceded_by_uv(command, match.start()) for match in PIP_INSTALL_RE.finditer(command))


def looks_like_install(command: str, rules: InstallRules) -> bool:
    if has_non_uv_pip_install(command):
        return True
    if re.search(r"(?:^|[\s;|&(])npm\s+(?:install|i|ci)\b", command):
        return True
    if rules.uv and re.search(r"(?:^|[\s;|&(])uv\s+(?:pip\s+install|add)\b", command):
        return True
    if rules.pipx and re.search(r"(?:^|[\s;|&(])pipx\s+install\b", command):
        return True
    if rules.yarn and re.search(r"(?:^|[\s;|&(])yarn\s+(?:add|install)\b", command):
        return True
    if rules.pnpm and re.search(r"(?:^|[\s;|&(])pnpm\s+(?:add|install)\b", command):
        return True
    if rules.npx and re.search(r"(?:^|[\s;|&(])npx\s+\S", command):
        return True
    return False


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


def raw_argv(command: str) -> list[str] | None:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return None


def _consume_flag(argv: list[str], value_flags: set[str]) -> list[str]:
    token = argv[0]
    flag = token.split("=", 1)[0]
    argv = argv[1:]
    if "=" not in token and flag in value_flags and argv:
        argv = argv[1:]
    return argv


def _skip_env(argv: list[str]) -> list[str]:
    while argv:
        token = argv[0]
        if token.startswith("-"):
            argv = _consume_flag(argv, ENV_VALUE_FLAGS)
            continue
        if "=" in token:
            argv = argv[1:]
            continue
        break
    return argv


def strip_wrappers(argv: list[str]) -> list[str]:
    while argv:
        base = _base(argv[0])
        if argv[0] == "(":
            argv = argv[1:]
            continue
        if "=" in argv[0] and not argv[0].startswith("-"):
            argv = argv[1:]
            continue
        if base == "sudo":
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                argv = _consume_flag(argv, SUDO_VALUE_FLAGS)
            continue
        if base == "env":
            argv = _skip_env(argv[1:])
            continue
        break
    while argv and argv[-1] == ")":
        argv = argv[:-1]
    return argv


def prepare_argv(command: str, rules: InstallRules) -> list[str] | None:
    argv = raw_argv(command)
    if argv is None:
        return None
    if not rules.wrappers:
        while argv and "=" in argv[0] and not argv[0].startswith("-"):
            argv = argv[1:]
        if argv and _base(argv[0]) == "sudo":
            argv = argv[1:]
        return argv
    return strip_wrappers(argv)


def matching_paren(command: str, open_index: int) -> tuple[str | None, int]:
    depth = 0
    quote = ""
    index = open_index
    while index < len(command):
        char = command[index]
        if quote:
            if char == quote and command[index - 1] != "\\":
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return command[open_index + 1:index], index + 1
        index += 1
    return None, open_index + 1


def scan_groups(command: str) -> tuple[list[str], list[str]]:
    substitutions: list[str] = []
    subshells: list[str] = []
    quote = ""
    index = 0
    while index < len(command):
        char = command[index]
        if quote:
            if char == quote and command[index - 1] != "\\":
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if command.startswith("$(", index):
            inner, nxt = matching_paren(command, index + 1)
            if inner is not None:
                substitutions.append(inner)
            index = nxt
            continue
        if char == "(":
            inner, nxt = matching_paren(command, index)
            if inner is not None:
                subshells.append(inner)
            index = nxt
            continue
        index += 1
    return substitutions, subshells


def shell_c_scripts(command: str) -> list[str]:
    argv = raw_argv(command)
    if not argv:
        return []
    scripts: list[str] = []
    index = 0
    while index < len(argv):
        if _base(argv[index]) in SHELLS:
            nxt = index + 1
            while nxt < len(argv) and argv[nxt].startswith("-") and argv[nxt] != "-c":
                nxt += 1
            if nxt + 1 < len(argv) and argv[nxt] == "-c":
                scripts.append(argv[nxt + 1])
                index = nxt + 2
                continue
        index += 1
    return scripts


def expand_commands(command: str, rules: InstallRules) -> list[str]:
    if not rules.wrappers:
        return [command]
    seen: list[str] = []
    pending = [command]
    while pending:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.append(current)
        for script in shell_c_scripts(current):
            pending.extend(part for part in split_commands(script) if part.strip())
        substitutions, subshells = scan_groups(current)
        for inner in substitutions + subshells:
            pending.extend(part for part in split_commands(inner) if part.strip())
    return seen


def is_python(token: str) -> bool:
    base = _base(token)
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


def is_versioned_pip(base: str) -> bool:
    return re.fullmatch(r"pip\d+(?:\.\d+)+", base) is not None


def is_pip_executable(base: str) -> bool:
    return base in {"pip", "pip3"} or is_versioned_pip(base)


def skip_options(args: list[str], value_flags: set[str]) -> int:
    """Index of the first token that is not a leading option."""
    index = 0
    while index < len(args) and args[index].startswith("-"):
        token = args[index]
        flag = token.split("=", 1)[0]
        index += 1
        if "=" not in token and flag in value_flags and index < len(args):
            index += 1
    return index


def unclassified(path: str) -> list[str]:
    return [f"{path} {UNCLASSIFIED}"]


def python_pip_tail(argv: list[str], rules: InstallRules) -> list[str] | None:
    """Arguments after `python -m pip` or `python -mpip`. None when this is not pip."""
    if not argv or not is_python(argv[0]):
        return None
    if not rules.wrappers and not rules.pip_forms:
        if len(argv) >= 3 and argv[1] == "-m" and argv[2] == "pip":
            return argv[3:]
        return None
    index = 1
    while index < len(argv):
        token = argv[index]
        if rules.pip_forms and token in {"-mpip", "-m=pip"}:
            return argv[index + 1:]
        if token == "-m":
            if index + 1 < len(argv) and _base(argv[index + 1]) == "pip":
                return argv[index + 2:]
            return None
        if not token.startswith("-"):
            return None
        flag = token.split("=", 1)[0]
        if flag in {"-c", "-m"}:
            return None
        if flag == "-I" and not rules.wrappers:
            return None
        if flag in {"-X", "-W"} and "=" not in token:
            index += 2
            continue
        if rules.wrappers or flag in {"-q", "-v", "-E", "-s", "-S", "-B", "-O", "-OO", "-u", "-b"}:
            index += 1
            continue
        return None
    return None


def classify_pip_tail(
    tail: list[str],
    *,
    path: str,
    allowlist: frozenset[str],
    forms: bool,
) -> list[str] | None:
    if not forms:
        if not tail or tail[0] != "install":
            return None
        return pip_spec_problems(package_tokens(tail[1:], PIP_VALUE_FLAGS), path=path, allowlist=allowlist)
    index = skip_options(tail, PIP_GLOBAL_VALUE)
    if index >= len(tail) or tail[index] != "install":
        return unclassified(path)
    return pip_spec_problems(
        package_tokens(tail[index + 1:], PIP_VALUE_FLAGS), path=path, allowlist=allowlist
    )


def pip_spec_problems(tokens: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    problems: list[str] = []
    for token in tokens:
        if EXACT_PIP.fullmatch(token) or token in allowlist:
            continue
        problems.append(f"{path} floating pip spec {token}")
    return problems


def npm_spec_problems(tokens: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    problems: list[str] = []
    for token in tokens:
        if EXACT_NPM.fullmatch(token) or token in allowlist:
            continue
        problems.append(f"{path} floating npm spec {token}")
    return problems


def spec_from_runner(
    args: list[str],
    *,
    path: str,
    allowlist: frozenset[str],
    value_flags: set[str],
    spec_flags: set[str],
    kind: str,
) -> list[str]:
    specs: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("--") and "=" in token:
            flag, value = token.split("=", 1)
            if flag in spec_flags:
                specs.append(value)
            index += 1
            continue
        flag = token.split("=", 1)[0]
        if token.startswith("-"):
            if flag in spec_flags and "=" not in token and index + 1 < len(args):
                specs.append(args[index + 1])
                index += 2
                continue
            if "=" not in token and flag in value_flags and index + 1 < len(args):
                index += 2
                continue
            index += 1
            continue
        if not specs:
            specs.append(token)
        break
    if not specs:
        return unclassified(path)
    if kind == "pip":
        return pip_spec_problems(specs, path=path, allowlist=allowlist)
    return npm_spec_problems(specs, path=path, allowlist=allowlist)


def npm_problems(argv: list[str], *, path: str, allowlist: frozenset[str], aliases: bool) -> list[str] | None:
    if not argv or _base(argv[0]) != "npm":
        return None
    args = argv[1:]
    index = skip_options(args, NPM_VALUE_FLAGS)
    if index >= len(args):
        return unclassified(path) if aliases else None
    kind = args[index]
    tokens = package_tokens(args[index + 1:], NPM_VALUE_FLAGS)
    if kind == "ci" and not tokens:
        return []
    if kind in {"install", "i"}:
        if not tokens:
            return [f"{path} npm install has no exact package spec"]
        return npm_spec_problems(tokens, path=path, allowlist=allowlist)
    if kind == "add":
        if not aliases:
            return None
        if not tokens:
            return [f"{path} npm add has no exact package spec"]
        return npm_spec_problems(tokens, path=path, allowlist=allowlist)
    if kind == "exec":
        if not aliases:
            return None
        return spec_from_runner(
            args[index + 1:], path=path, allowlist=allowlist,
            value_flags=NPM_VALUE_FLAGS, spec_flags={"--package"}, kind="npm",
        )
    return unclassified(path) if aliases else None


def uv_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    if _base(argv[0]) == "uvx":
        return spec_from_runner(
            argv[1:], path=path, allowlist=allowlist,
            value_flags=UV_GLOBAL_VALUE, spec_flags={"--from"}, kind="pip",
        )
    args = argv[1:]
    index = skip_options(args, UV_GLOBAL_VALUE)
    if index >= len(args):
        return unclassified(path)
    sub = args[index]
    rest = args[index + 1:]
    if sub == "pip":
        nested = skip_options(rest, PIP_GLOBAL_VALUE)
        if nested < len(rest) and rest[nested] == "install":
            return pip_spec_problems(
                package_tokens(rest[nested + 1:], PIP_VALUE_FLAGS), path=path, allowlist=allowlist
            )
        return unclassified(path)
    if sub == "add":
        tokens = package_tokens(rest, UV_ADD_VALUE_FLAGS)
        if not tokens:
            return [f"{path} uv add has no exact package spec"]
        return pip_spec_problems(tokens, path=path, allowlist=allowlist)
    if sub == "tool":
        nested = skip_options(rest, UV_ADD_VALUE_FLAGS)
        if nested < len(rest) and rest[nested] == "install":
            tokens = package_tokens(rest[nested + 1:], UV_ADD_VALUE_FLAGS)
            if not tokens:
                return unclassified(path)
            return pip_spec_problems(tokens, path=path, allowlist=allowlist)
        return unclassified(path)
    if sub == "run":
        return spec_from_runner(
            rest, path=path, allowlist=allowlist,
            value_flags=UV_GLOBAL_VALUE, spec_flags={"--with"}, kind="pip",
        )
    return unclassified(path)


def yarn_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    args = argv[1:]
    index = skip_options(args, YARN_VALUE_FLAGS)
    if index < len(args) and args[index] == "global":
        index += 1
        index += skip_options(args[index:], YARN_VALUE_FLAGS)
    if index >= len(args):
        return unclassified(path)
    sub = args[index]
    tokens = package_tokens(args[index + 1:], YARN_VALUE_FLAGS)
    if sub == "install" and not tokens:
        return []
    if sub in {"add", "dlx"}:
        if not tokens:
            return [f"{path} yarn {sub} has no exact package spec"]
        return npm_spec_problems(tokens, path=path, allowlist=allowlist)
    return unclassified(path)


def pnpm_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    args = argv[1:]
    index = skip_options(args, PNPM_VALUE_FLAGS)
    if index >= len(args):
        return unclassified(path)
    sub = args[index]
    tokens = package_tokens(args[index + 1:], PNPM_VALUE_FLAGS)
    if sub in {"install", "i"} and not tokens:
        return []
    if sub in {"install", "i", "add", "dlx"}:
        if not tokens:
            return [f"{path} pnpm {sub} has no exact package spec"]
        return npm_spec_problems(tokens, path=path, allowlist=allowlist)
    return unclassified(path)


def pipx_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    args = argv[1:]
    index = skip_options(args, PIPX_VALUE_FLAGS)
    if index >= len(args):
        return unclassified(path)
    sub = args[index]
    rest = args[index + 1:]
    if sub == "install":
        tokens = package_tokens(rest, PIPX_VALUE_FLAGS)
        if not tokens:
            return [f"{path} pipx install has no exact package spec"]
        return pip_spec_problems(tokens, path=path, allowlist=allowlist)
    if sub == "run":
        return spec_from_runner(
            rest, path=path, allowlist=allowlist,
            value_flags=PIPX_VALUE_FLAGS, spec_flags={"--spec"}, kind="pip",
        )
    return unclassified(path)


def bun_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    if _base(argv[0]) == "bunx":
        return spec_from_runner(
            argv[1:], path=path, allowlist=allowlist,
            value_flags=set(), spec_flags={"--package"}, kind="npm",
        )
    args = argv[1:]
    index = skip_options(args, {"--cwd", "--config"})
    if index >= len(args):
        return unclassified(path)
    sub = args[index]
    tokens = package_tokens(args[index + 1:], {"--cwd", "--config"})
    if sub in {"install", "i"} and not tokens:
        return []
    if sub in {"add", "x", "dlx"}:
        if not tokens:
            return unclassified(path)
        return npm_spec_problems(tokens, path=path, allowlist=allowlist)
    return unclassified(path)


def npx_problems(argv: list[str], *, path: str, allowlist: frozenset[str]) -> list[str]:
    specs: list[str] = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token.startswith("--package="):
            specs.append(token.split("=", 1)[1])
            index += 1
            continue
        if token in {"-p", "--package"}:
            if index + 1 < len(argv):
                specs.append(argv[index + 1])
            index += 2
            continue
        if token.startswith("-"):
            flag = token.split("=", 1)[0]
            if "=" not in token and flag in NPX_VALUE_FLAGS:
                index += 2
                continue
            index += 1
            continue
        if not specs:
            specs.append(token)
        break
    if not specs:
        return [f"{path} npx has no exact package spec"]
    return npm_spec_problems(specs, path=path, allowlist=allowlist)


def command_problems(
    argv: list[str],
    *,
    path: str,
    allowlist: frozenset[str],
    rules: InstallRules,
) -> list[str] | None:
    if not argv:
        return None
    base = _base(argv[0])
    if base in {"uv", "uvx"}:
        if not rules.uv:
            return None
        return uv_problems(argv, path=path, allowlist=allowlist)
    if base == "pipx":
        if not rules.pipx:
            return None
        return pipx_problems(argv, path=path, allowlist=allowlist)
    if base == "yarn":
        if not rules.yarn:
            return None
        return yarn_problems(argv, path=path, allowlist=allowlist)
    if base == "pnpm":
        if not rules.pnpm:
            return None
        return pnpm_problems(argv, path=path, allowlist=allowlist)
    if base == "npx":
        if not rules.npx:
            return None
        return npx_problems(argv, path=path, allowlist=allowlist)
    if base == "npm":
        return npm_problems(argv, path=path, allowlist=allowlist, aliases=rules.npm_aliases)
    if base in {"bun", "bunx"}:
        if not rules.bun:
            return None
        return bun_problems(argv, path=path, allowlist=allowlist)
    if is_versioned_pip(base):
        if not rules.pip_forms:
            return None
        return classify_pip_tail(argv[1:], path=path, allowlist=allowlist, forms=True)
    if base in {"pip", "pip3"}:
        return classify_pip_tail(argv[1:], path=path, allowlist=allowlist, forms=rules.pip_forms)
    tail = python_pip_tail(argv, rules)
    if tail is None:
        return None
    return classify_pip_tail(tail, path=path, allowlist=allowlist, forms=rules.pip_forms)


def install_spec_problems(
    text: str,
    *,
    path: str,
    allowlist: frozenset[str] | None = None,
    rules: InstallRules | None = None,
) -> list[str]:
    chosen = INSTALL_SPEC_ALLOWLIST if allowlist is None else allowlist
    active = InstallRules() if rules is None else rules
    problems: list[str] = []
    for script in run_scripts(text):
        for command in split_commands(join_continuations(script)):
            command = strip_comment(command)
            if not command:
                continue
            installish = looks_like_install(command, active)
            classified = False
            for leaf in expand_commands(command, active):
                leaf_installish = looks_like_install(leaf, active)
                argv = prepare_argv(leaf, active)
                if argv is None:
                    if installish or leaf_installish:
                        problems.append(f"{path} unparsable install command")
                        classified = True
                    continue
                found = command_problems(argv, path=path, allowlist=chosen, rules=active)
                if found is None:
                    continue
                classified = True
                problems.extend(found)
            if active.wrappers and installish and not classified:
                problems.append(f"{path} {UNCLASSIFIED}")
    return problems


def parse_direct(text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        match = PIN_RE.match(line)
        if not match:
            raise ValueError(f"unparsed requirement line: {line!r}")
        pins[norm(match.group(1))] = match.group(2)
    return pins


def parse_google_lock(text: str) -> dict[str, dict[str, object]]:
    pins: dict[str, dict[str, object]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("--hash="):
            if current is None:
                raise ValueError("hash line before any pin")
            if not re.fullmatch(r"--hash=sha256:[0-9a-f]{64}\s*\\?", line):
                raise ValueError(f"bad hash line: {line!r}")
            pins[current]["hashes"] = int(pins[current]["hashes"]) + 1
            continue
        match = PIN_RE.match(line)
        if not match:
            raise ValueError(f"unparsed lock line: {line!r}")
        current = norm(match.group(1))
        pins[current] = {"version": match.group(2), "hashes": 0}
    return pins


def google_lock_problems(
    req_text: str,
    lock_text: str,
    *,
    rules: InstallRules | None = None,
) -> list[str]:
    active = InstallRules() if rules is None else rules
    try:
        direct = parse_direct(req_text)
        locked = parse_google_lock(lock_text)
    except ValueError as exc:
        return [str(exc)]
    problems: list[str] = []
    if active.lock_versions:
        for name, ver in direct.items():
            have = locked.get(name)
            if have is None:
                problems.append(f"google lock missing {name}=={ver}")
            elif have["version"] != ver:
                problems.append(
                    f"google lock pins {name}=={have['version']} but requirements say {ver}"
                )
    if active.lock_hashes:
        for name, meta in locked.items():
            if int(meta["hashes"]) < 1:
                problems.append(f"google lock {name} has no sha256 hash")
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


def _caught(text: str, needle: str, *, rules: InstallRules | None = None) -> bool:
    found = install_spec_problems(text, path="fixture.yml", rules=rules)
    return any(needle in item for item in found)


def prove_bypasses() -> str:
    bare = "run: pip install x\n"
    fixtures = {
        "sudo": "run: sudo -H pip install x\n",
        "env": "run: env A=1 pip install x\n",
        "bash": "run: bash -c 'pip install x'\n",
        "sh": "run: sh -c 'pip install x'\n",
        "subshell": "run: (pip install x)\n",
        "subst": "run: echo $(pip install x)\n",
        "python_i": "run: python3 -I -m pip install x\n",
        "uv_pip": "run: uv pip install x\n",
        "uv_add": "run: uv add x\n",
        "uv_tool": "run: uv tool install x\n",
        "uvx": "run: uvx x\n",
        "uv_with": "run: uv run --with x foo\n",
        "pipx": "run: pipx install x\n",
        "pipx_run": "run: pipx run x\n",
        "yarn": "run: yarn add x\n",
        "yarn_global": "run: yarn global add x\n",
        "yarn_dlx": "run: yarn dlx x\n",
        "pnpm": "run: pnpm add x\n",
        "pnpm_i": "run: pnpm i x\n",
        "pnpm_dlx": "run: pnpm dlx x\n",
        "npx": "run: npx x\n",
        "pip_q": "run: pip -q install x\n",
        "pip_isolated": "run: pip --isolated install x\n",
        "pip_py_q": "run: python3 -m pip -q install x\n",
        "pip_mpip": "run: python3 -mpip install x\n",
        "pip311": "run: pip3.11 install x\n",
        "npm_add": "run: npm add x\n",
        "npm_exec": "run: npm exec x\n",
        "bun_add": "run: bun add x\n",
    }
    exact = {
        "sudo": "run: sudo -H pip install x==1.2.3\n",
        "env": "run: env A=1 pip install x==1.2.3\n",
        "bash": "run: bash -c 'pip install x==1.2.3'\n",
        "sh": "run: sh -c 'pip install x==1.2.3'\n",
        "subshell": "run: (pip install x==1.2.3)\n",
        "subst": "run: echo $(pip install x==1.2.3)\n",
        "python_i": "run: python3 -I -m pip install x==1.2.3\n",
        "uv_pip": "run: uv pip install x==1.2.3\n",
        "uv_add": "run: uv add x==1.2.3\n",
        "uv_tool": "run: uv tool install x==1.2.3\n",
        "uvx": "run: uvx x==1.2.3\n",
        "uv_with": "run: uv run --with x==1.2.3 foo\n",
        "pipx": "run: pipx install x==1.2.3\n",
        "pipx_run": "run: pipx run x==1.2.3\n",
        "yarn": "run: yarn add x@1.2.3\n",
        "yarn_global": "run: yarn global add x@1.2.3\n",
        "yarn_dlx": "run: yarn dlx x@1.2.3\n",
        "pnpm": "run: pnpm add x@1.2.3\n",
        "pnpm_i": "run: pnpm i x@1.2.3\n",
        "pnpm_dlx": "run: pnpm dlx x@1.2.3\n",
        "npx": "run: npx x@1.2.3\n",
        "pip_q": "run: pip -q install x==1.2.3\n",
        "pip_isolated": "run: pip --isolated install x==1.2.3\n",
        "pip_py_q": "run: python3 -m pip -q install x==1.2.3\n",
        "pip_mpip": "run: python3 -mpip install x==1.2.3\n",
        "pip311": "run: pip3.11 install x==1.2.3\n",
        "npm_add": "run: npm add x@1.2.3\n",
        "npm_exec": "run: npm exec x@1.2.3\n",
        "bun_add": "run: bun add x@1.2.3\n",
    }
    needles = {
        "sudo": "floating pip spec x",
        "env": "floating pip spec x",
        "bash": "floating pip spec x",
        "sh": "floating pip spec x",
        "subshell": "floating pip spec x",
        "subst": "floating pip spec x",
        "python_i": "floating pip spec x",
        "uv_pip": "floating pip spec x",
        "uv_add": "floating pip spec x",
        "uv_tool": "floating pip spec x",
        "uvx": "floating pip spec x",
        "uv_with": "floating pip spec x",
        "pipx": "floating pip spec x",
        "pipx_run": "floating pip spec x",
        "yarn": "floating npm spec x",
        "yarn_global": "floating npm spec x",
        "yarn_dlx": "floating npm spec x",
        "pnpm": "floating npm spec x",
        "pnpm_i": "floating npm spec x",
        "pnpm_dlx": "floating npm spec x",
        "npx": "floating npm spec x",
        "pip_q": "floating pip spec x",
        "pip_isolated": "floating pip spec x",
        "pip_py_q": "floating pip spec x",
        "pip_mpip": "floating pip spec x",
        "pip311": "floating pip spec x",
        "npm_add": "floating npm spec x",
        "npm_exec": "floating npm spec x",
        "bun_add": "floating npm spec x",
    }
    groups = {
        "wrappers": ["sudo", "env", "bash", "sh", "subshell", "subst", "python_i"],
        "uv": ["uv_pip", "uv_add", "uv_tool", "uvx", "uv_with"],
        "pipx": ["pipx", "pipx_run"],
        "yarn": ["yarn", "yarn_global", "yarn_dlx"],
        "pnpm": ["pnpm", "pnpm_i", "pnpm_dlx"],
        "npx": ["npx"],
        "pip_forms": ["pip_q", "pip_isolated", "pip_py_q", "pip_mpip", "pip311"],
        "npm_aliases": ["npm_add", "npm_exec"],
        "bun": ["bun_add"],
    }
    for name, text in fixtures.items():
        if not _caught(text, needles[name]):
            fail(f"bypass {name} was not caught: {install_spec_problems(text, path='fixture.yml')}")
        if install_spec_problems(exact[name], path="fixture.yml"):
            fail(f"exact {name} was refused: {install_spec_problems(exact[name], path='fixture.yml')}")
    if install_spec_problems("run: yarn install --frozen-lockfile\n", path="fixture.yml"):
        fail("yarn install from a lockfile was refused")
    if install_spec_problems("run: pnpm install --frozen-lockfile\n", path="fixture.yml"):
        fail("pnpm install from a lockfile was refused")
    if not _caught("run: npx -y x\n", "floating npm spec x"):
        fail("npx -y x was not caught")
    if install_spec_problems("run: npx --package x@1.2.3 cowsay\n", path="fixture.yml"):
        fail("npx --package exact spec was refused")
    if not _caught("run: VAR=1 pip install x\n", "floating pip spec x", rules=InstallRules(wrappers=False)):
        fail("VAR=1 pip install escaped the pre-wrapper parser")
    if not _caught("run: sudo pip install x\n", "floating pip spec x", rules=InstallRules(wrappers=False)):
        fail("bare sudo pip install escaped the pre-wrapper parser")
    if not _caught("run: pip freeze\n", UNCLASSIFIED):
        fail("pip freeze was not refused as unclassified")
    if _caught("run: pip freeze\n", UNCLASSIFIED, rules=InstallRules(pip_forms=False)):
        fail("off pip_forms still refused pip freeze")
    if not _caught("run: uv tool\n", UNCLASSIFIED):
        fail("uv tool was not refused as unclassified")
    if not _caught("run: timeout pip install x\n", UNCLASSIFIED):
        fail("timeout wrapper was not refused as unclassified")
    if not _caught("run: npm install left-pad\n", "floating npm spec left-pad", rules=InstallRules(npm_aliases=False)):
        fail("off npm_aliases let npm install escape")
    escaped: list[str] = []
    for rule_name, members in groups.items():
        off = InstallRules(**{rule_name: False})
        if not _caught(bare, "floating pip spec x", rules=off):
            fail(f"off_{rule_name} let bare pip install escape")
        for name, text in fixtures.items():
            caught = _caught(text, needles[name], rules=off)
            if name in members and caught:
                fail(f"off_{rule_name} still caught {name}")
            if name not in members and not caught:
                fail(f"off_{rule_name} let {name} escape")
        escaped.append(f"off_{rule_name}=escaped")
    return (
        "bypass=" + ",".join(f"{name}=caught" for name in fixtures)
        + " exact=pass lockfile_install=pass"
        + " load_bearing=" + ",".join(escaped)
    )


def prove_google_lock(req_text: str, lock_text: str) -> str:
    if google_lock_problems(req_text, lock_text):
        fail(f"live google lock drifted: {google_lock_problems(req_text, lock_text)}")
    drifted = req_text.replace("google-auth==2.62.0", "google-auth==2.62.1")
    stripped = re.sub(r"\n\s+--hash=sha256:[0-9a-f]{64}(?: \\)?", "", lock_text)
    if not google_lock_problems(drifted, lock_text):
        fail("google requirements version drift was not caught")
    if not any("no sha256 hash" in item for item in google_lock_problems(req_text, stripped)):
        fail("google lock hash drop was not caught")
    if google_lock_problems(drifted, lock_text, rules=InstallRules(lock_versions=False)):
        fail("off_lock_versions still caught version drift")
    if not any(
        "no sha256 hash" in item
        for item in google_lock_problems(req_text, stripped, rules=InstallRules(lock_versions=False))
    ):
        fail("off_lock_versions let a missing hash escape")
    if google_lock_problems(req_text, stripped, rules=InstallRules(lock_hashes=False)):
        fail("off_lock_hashes still caught a missing hash")
    if not google_lock_problems(drifted, lock_text, rules=InstallRules(lock_hashes=False)):
        fail("off_lock_hashes let version drift escape")
    return "lock=match load_bearing=off_lock_versions=escaped,off_lock_hashes=escaped"


def main() -> int:
    if INSTALL_SPEC_ALLOWLIST:
        fail("INSTALL_SPEC_ALLOWLIST must stay empty")
    problems: list[str] = []
    workflows = sorted(WORKFLOWS.glob("*.y*ml"))
    for path in workflows:
        rel = path.relative_to(ROOT).as_posix()
        problems.extend(install_spec_problems(path.read_text(encoding="utf-8"), path=rel))
    req_text = (ROOT / REQ_NAME).read_text(encoding="utf-8")
    lock_text = (ROOT / LOCK_NAME).read_text(encoding="utf-8")
    problems.extend(google_lock_problems(req_text, lock_text))
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

    bypass_evidence = prove_bypasses()
    lock_evidence = prove_google_lock(req_text, lock_text)
    print(
        f"OK {NAME} workflows={len(workflows)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        f"{bypass_evidence} {lock_evidence}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
