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

The backstop is the words, not a wrapper list. Every `run:` block is
split with `shlex`, including nested `-c` and `eval` strings. A step whose
first key is `- run:` is the same block. Each word is split again on `;`,
`&`, `|`, `(`, `)`, `` ` ``, `<`, and `>`, and a `$(...)` or backtick body
is scanned even inside double quotes. A word whose basename is pip, pip3*,
uv, uvx, pipx, npm, npx, pnpm, yarn, or bun, or a `python*` followed by
`-m pip` / `-mpip`, must belong to a pinned or lock install. Otherwise the
step is unclassified. A `shlex` failure refuses the step too.

`requirements-google-clients.py311.lock` must keep the direct pins from
`requirements-google-clients.txt`, and every lock pin must have a sha256
hash. INSTALL_SPEC_ALLOWLIST starts empty; a non-empty committed set fails
this sensor. An apt ffmpeg install must be one exact command sequence on
ubuntu-24.04. A node command must follow the pinned setup-node step and its
checksum command. Stdlib only.
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
SHELL_END = {"fi", "done", "esac", "else", "elif", "then", "do", "{", "}"}
PM_BASES = {"uv", "uvx", "pipx", "npm", "npx", "pnpm", "yarn", "bun", "bunx"}
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
    tokens: bool = True
    lock_versions: bool = True
    lock_hashes: bool = True


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
        rest = tail[1:]
    else:
        index = skip_options(tail, PIP_GLOBAL_VALUE)
        if index >= len(tail) or tail[index] != "install":
            return unclassified(path)
        rest = tail[index + 1:]
    specs = package_tokens(rest, PIP_VALUE_FLAGS)
    if not specs and not _has_requirement(rest):
        return unclassified(path)
    return pip_spec_problems(specs, path=path, allowlist=allowlist)


def _has_requirement(args: list[str]) -> bool:
    return any(token.split("=", 1)[0] in {"-r", "--requirement"} for token in args)


def _normalize_token(token: str) -> str:
    text = token.rstrip(";")
    while text.startswith("$("):
        text = text[2:]
    if text.startswith("(") or text.startswith("`"):
        text = text[1:]
    return text.rstrip(")")


def _shell_c_flag(token: str) -> bool:
    if token.startswith("--") or not token.startswith("-"):
        return False
    body = token[1:].split("=", 1)[0]
    return bool(body) and body.isalpha() and "c" in body


_SLICE_STOP = SHELL_END | {"&&", "||", "|", ";;", "*"}
_META_SPLIT = re.compile(r"[;&|()<>`]+")


def _expand_word(token: str) -> list[str]:
    """Split one shlex word on shell metacharacters and the spaces they expose."""
    pieces: list[str] = []
    for part in _META_SPLIT.split(token):
        part = part.strip()
        if part:
            pieces.extend(part.split())
    return pieces


def _expand_words(words: list[str]) -> list[str]:
    expanded: list[str] = []
    for token in words:
        expanded.extend(_expand_word(token))
    return expanded


def _substitution_scripts(token: str) -> list[str]:
    """Bodies of `$(...)` and backtick pairs that shlex kept inside one word."""
    scripts: list[str] = []
    index = 0
    while index < len(token):
        if token.startswith("$(", index):
            inner, nxt = matching_paren(token, index + 1)
            if inner and inner.strip():
                scripts.append(inner)
            index = max(nxt, index + 2)
            continue
        if token[index] == "`":
            end = token.find("`", index + 1)
            if end > index + 1:
                scripts.append(token[index + 1:end])
                index = end + 1
                continue
        index += 1
    return scripts


def command_slice(words: list[str], start: int) -> list[str]:
    chunk: list[str] = []
    for token in words[start:]:
        bare = _normalize_token(token)
        if not bare or bare in _SLICE_STOP or bare.startswith("*"):
            break
        chunk.append(bare)
    return chunk


def _nested_scripts(words: list[str]) -> list[str]:
    scripts: list[str] = []
    index = 0
    while index < len(words):
        base = _base(_normalize_token(words[index]))
        if base == "eval" and index + 1 < len(words) and any(char.isspace() for char in words[index + 1]):
            scripts.append(words[index + 1])
        if base in SHELLS:
            nxt = index + 1
            while nxt < len(words) and words[nxt].startswith("-") and not _shell_c_flag(words[nxt]):
                nxt += 1
            if nxt + 1 < len(words) and _shell_c_flag(words[nxt]):
                scripts.append(words[nxt + 1])
                index = nxt + 2
                continue
        index += 1
    return scripts


def word_lists(text: str, seen: set[str] | None = None) -> list[list[str]] | None:
    """shlex words for one script and every nested -c or eval string."""
    seen = set() if seen is None else set(seen)
    cleaned = "\n".join(strip_comment(line) for line in text.splitlines()).strip()
    if not cleaned or cleaned in seen:
        return []
    seen.add(cleaned)
    try:
        words = shlex.split(cleaned, posix=True)
    except ValueError:
        return None
    lists = [_expand_words(words)]
    for word in words:
        for script in _substitution_scripts(word):
            nested = word_lists(script, seen)
            if nested is None:
                return None
            lists.extend(nested)
    for script in _nested_scripts(words):
        nested = word_lists(script, seen)
        if nested is None:
            return None
        lists.extend(nested)
    return lists


def armed_indexes(words: list[str], rules: InstallRules) -> list[int]:
    found: list[int] = []
    for index, token in enumerate(words):
        bare = _normalize_token(token)
        base = _base(bare)
        if base in PM_BASES or is_pip_executable(base):
            found.append(index)
            continue
        if is_python(bare):
            normalized = [_normalize_token(word) for word in words[index:]]
            if python_pip_tail(normalized, rules) is not None:
                found.append(index)
    return found


def shlex_chunks(script: str) -> list[str] | None:
    """Split a run block into chunks that each survive shlex.

    A line with an open quote stays with the lines that close it. The whole
    block is refused when shlex cannot parse it at all.
    """
    joined = join_continuations(script)
    if word_lists(joined) is None:
        return None
    chunks: list[str] = []
    buf = ""
    for line in joined.splitlines():
        buf = f"{buf}\n{line}" if buf else line
        if word_lists(buf) is None:
            continue
        if buf.strip():
            chunks.append(buf)
        buf = ""
    if buf.strip():
        return None
    return chunks


def token_backstop(
    script: str,
    *,
    path: str,
    allowlist: frozenset[str],
    rules: InstallRules,
) -> list[str]:
    """Refuse an armed package-manager word that is not a pinned or lock install."""
    if not rules.tokens:
        return []
    chunks = shlex_chunks(script)
    if chunks is None:
        return unclassified(path)
    problems: list[str] = []
    for line in chunks:
        lists = word_lists(line)
        if lists is None:
            return unclassified(path)
        for words in lists:
            for index in armed_indexes(words, rules):
                found = command_problems(
                    command_slice(words, index), path=path, allowlist=allowlist, rules=rules
                )
                if not found:
                    continue
                problems.extend(found)
    return problems


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
        if active.tokens:
            problems.extend(token_backstop(script, path=path, allowlist=chosen, rules=active))
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
        "if_then": "run: if true; then pip -q install x; fi\n",
        "for_do": "run: for i in 1; do uvx x; done\n",
        "brace": "run: { pip -q install x; }\n",
        "bang": "run: ! pip -q install x\n",
        "timeout": "run: timeout 60 pip -q install x\n",
        "nohup": "run: nohup python3 -mpip install x\n",
        "eval": "run: eval pip -q install x\n",
        "eval_quote": "run: eval 'pip -q install x'\n",
        "xargs": "run: xargs pip -q install\n",
        "bash_lc": "run: bash -lc 'pip -q install x'\n",
        "if_npm": "run: if true; then npm add x; fi\n",
        "while_pip": "run: while false; do pip3.11 install x; done\n",
        "else_pip": "run: if a; then :; else pip -q install x; fi\n",
        "case_pip": "run: case a in a) pip -q install x;; esac\n",
        "timeout_npm": "run: timeout 60 npm add x\n",
        "timeout_pnpm": "run: timeout 5 pnpm dlx x\n",
        "nice_bun": "run: nice bun add x\n",
        "stdbuf_pnpm": "run: stdbuf -oL pnpm i x\n",
        "time_uvx": "run: time uvx x\n",
        "command_pip": "run: command pip -q install x\n",
        "exec_npm": "run: exec npm add x\n",
        "case_glued": "run: case a in a)pip -q install x;; esac\n",
        "case_pattern": 'run: case "$X" in linux)pip -q install x;; *) echo no;; esac\n',
        "case_uvx": "run: case a in a)uvx x;; esac\n",
        "case_mpip": "run: case a in a)python3 -mpip install x;; esac\n",
        "case_multi": "run: |\n  case a in\n    a)pip -q install x\n    ;;\n  esac\n",
        "dquote_subst": 'run: echo "$(pip -q install x)"\n',
        "backtick": "run: x=`pip -q install x`\n",
        "amp_pip": "run: true&pip -q install x\n",
        "dash_run": "      - run: pip install x\n",
        "dash_block": "      - run: |\n          pip install x\n",
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
        "if_then": "run: if true; then pip -q install x==1.2.3; fi\n",
        "for_do": "run: for i in 1; do uvx x==1.2.3; done\n",
        "brace": "run: { pip -q install x==1.2.3; }\n",
        "bang": "run: ! pip -q install x==1.2.3\n",
        "timeout": "run: timeout 60 pip -q install x==1.2.3\n",
        "nohup": "run: nohup python3 -mpip install x==1.2.3\n",
        "eval": "run: eval pip -q install x==1.2.3\n",
        "eval_quote": "run: eval 'pip -q install x==1.2.3'\n",
        "xargs": "run: xargs pip -q install x==1.2.3\n",
        "bash_lc": "run: bash -lc 'pip -q install x==1.2.3'\n",
        "if_npm": "run: if true; then npm add x@1.2.3; fi\n",
        "while_pip": "run: while false; do pip3.11 install x==1.2.3; done\n",
        "else_pip": "run: if a; then :; else pip -q install x==1.2.3; fi\n",
        "case_pip": "run: case a in a) pip -q install x==1.2.3;; esac\n",
        "timeout_npm": "run: timeout 60 npm add x@1.2.3\n",
        "timeout_pnpm": "run: timeout 5 pnpm dlx x@1.2.3\n",
        "nice_bun": "run: nice bun add x@1.2.3\n",
        "stdbuf_pnpm": "run: stdbuf -oL pnpm i x@1.2.3\n",
        "time_uvx": "run: time uvx x==1.2.3\n",
        "command_pip": "run: command pip -q install x==1.2.3\n",
        "exec_npm": "run: exec npm add x@1.2.3\n",
        "case_glued": "run: case a in a)pip -q install x==1.2.3;; esac\n",
        "case_pattern": 'run: case "$X" in linux)pip -q install x==1.2.3;; *) echo no;; esac\n',
        "case_uvx": "run: case a in a)uvx x==1.2.3;; esac\n",
        "case_mpip": "run: case a in a)python3 -mpip install x==1.2.3;; esac\n",
        "case_multi": "run: |\n  case a in\n    a)pip -q install x==1.2.3\n    ;;\n  esac\n",
        "dquote_subst": 'run: echo "$(pip -q install x==1.2.3)"\n',
        "backtick": "run: x=`pip -q install x==1.2.3`\n",
        "amp_pip": "run: true&pip -q install x==1.2.3\n",
        "dash_run": "      - run: pip install x==1.2.3\n",
        "dash_block": "      - run: |\n          pip install x==1.2.3\n",
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
        "if_then": "floating pip spec x",
        "for_do": "floating pip spec x",
        "brace": "floating pip spec x",
        "bang": "floating pip spec x",
        "timeout": "floating pip spec x",
        "nohup": "floating pip spec x",
        "eval": "floating pip spec x",
        "eval_quote": "floating pip spec x",
        "xargs": UNCLASSIFIED,
        "bash_lc": "floating pip spec x",
        "if_npm": "floating npm spec x",
        "while_pip": "floating pip spec x",
        "else_pip": "floating pip spec x",
        "case_pip": "floating pip spec x",
        "timeout_npm": "floating npm spec x",
        "timeout_pnpm": "floating npm spec x",
        "nice_bun": "floating npm spec x",
        "stdbuf_pnpm": "floating npm spec x",
        "time_uvx": "floating pip spec x",
        "command_pip": "floating pip spec x",
        "exec_npm": "floating npm spec x",
        "case_glued": "floating pip spec x",
        "case_pattern": "floating pip spec x",
        "case_uvx": "floating pip spec x",
        "case_mpip": "floating pip spec x",
        "case_multi": "floating pip spec x",
        "dquote_subst": "floating pip spec x",
        "backtick": "floating pip spec x",
        "amp_pip": "floating pip spec x",
        "dash_run": "floating pip spec x",
        "dash_block": "floating pip spec x",
    }
    groups = {
        "wrappers": [],
        "uv": ["uv_add", "uv_tool", "uvx", "uv_with", "for_do", "time_uvx", "case_uvx"],
        "pipx": ["pipx", "pipx_run"],
        "yarn": ["yarn", "yarn_global", "yarn_dlx"],
        "pnpm": ["pnpm", "pnpm_i", "pnpm_dlx", "timeout_pnpm", "stdbuf_pnpm"],
        "npx": ["npx"],
        "pip_forms": [
            "pip_q", "pip_isolated", "pip_py_q", "pip_mpip", "pip311",
            "if_then", "brace", "bang", "timeout", "nohup", "eval", "eval_quote",
            "xargs", "bash_lc", "while_pip", "else_pip", "case_pip", "command_pip",
            "case_glued", "case_pattern", "case_mpip", "case_multi",
            "dquote_subst", "backtick", "amp_pip",
        ],
        "npm_aliases": ["npm_add", "npm_exec", "if_npm", "timeout_npm", "exec_npm"],
        "bun": ["bun_add", "nice_bun"],
        "tokens": [
            "if_then", "for_do", "brace", "bang", "timeout", "nohup", "eval", "eval_quote",
            "xargs", "bash_lc", "if_npm", "while_pip", "else_pip", "case_pip",
            "timeout_npm", "timeout_pnpm", "nice_bun", "stdbuf_pnpm", "time_uvx",
            "command_pip", "exec_npm",
            "case_glued", "case_pattern", "case_uvx", "case_mpip", "case_multi",
            "dquote_subst", "backtick", "amp_pip",
        ],
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
    if not _caught("run: echo '\n", UNCLASSIFIED):
        fail("shlex failure was not refused")
    if _caught("run: echo '\n", UNCLASSIFIED, rules=InstallRules(tokens=False)):
        fail("off tokens still refused a shlex failure")
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
        if members:
            escaped.append(f"off_{rule_name}=escaped")
        else:
            escaped.append(f"off_{rule_name}=still_closed")
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

def main() -> int:
    if INSTALL_SPEC_ALLOWLIST:
        fail("INSTALL_SPEC_ALLOWLIST must stay empty")
    problems: list[str] = []
    workflows = sorted(WORKFLOWS.glob("*.y*ml"))
    apt_workflows = 0
    node_setups = 0
    for path in workflows:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        problems.extend(install_spec_problems(text, path=rel))
        apt = apt_ffmpeg_problems(text, path=rel)
        if "apt-get install" in text or "apt-get download" in text:
            apt_workflows += 1
        problems.extend(apt)
        problems.extend(node_toolchain_problems(text, path=rel))
        node_setups += text.count("actions/setup-node@")
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

    observer = (WORKFLOWS / "instagram-read-source-observer.yml").read_text(encoding="utf-8")
    if node_toolchain_problems(check_all, path="check-all.yml"):
        fail(f"pinned check-all node was refused: {node_toolchain_problems(check_all, path='check-all.yml')}")
    if node_toolchain_problems(observer, path="instagram-read-source-observer.yml"):
        fail("pinned observer node was refused")

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
        "node digest swap",
        check_all.replace(
            "cf9cfe18f485ac615fbc237e269549f4014fd843395568cf81698ce1903e9bcf",
            "0" * 64,
            1,
        ),
        "command mismatch",
    )
    require_node(
        "commented node verifier",
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


    print(
        f"OK {NAME} workflows={len(workflows)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        f"{bypass_evidence} {lock_evidence} "
        f"apt_ffmpeg={apt_workflows} apt_sequence=pinned extra=caught "
        "comment=caught digest=caught runner=caught pool=caught "
        f"node_setups={node_setups} node_float=caught node_sha=caught "
        "node_comment=caught node_bare=caught node_path=caught node_env=caught "
        "node_bash=caught node_dash=caught node_if=caught node_continue=caught"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
