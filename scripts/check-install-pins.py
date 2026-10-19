#!/usr/bin/env python3
"""Refuse a floating pip or npm spec in a workflow command.

Every package token on a workflow `pip install` / `npm install` / `npm i`
line must be an exact pin (`name==1.2.3` or `name@1.2.3`). `npm ci` with no
package arguments is allowed. Arguments of `-r` / `--requirement` are lockfile
names, not package specs. INSTALL_SPEC_ALLOWLIST starts empty; a non-empty
committed set fails this sensor. Stdlib only.
"""
from __future__ import annotations

import ast
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


BENTO_SHA256 = "c7da70eaa8d3f457b2458f1685769bf2c488724ac075954f216c70c60f310af0"
BENTO_VERSION = "1.2.9"
BENTO_SHELL_URL = "https://bento.page/releases/slides/Bento_Slides.bento.html"
BENTO_MANIFEST_URL = "https://bento.page/releases/slides/manifest.json"
VERIFY_STEP = """      - name: Verify Bento shell checksum
        run: python3 scripts/verify_bento_shell.py
"""
DECK_STEP = """      - name: Build weekly deck (JSON + HTML)
        run: python3 scripts/vf_weekly_deck.py
"""
NETWORK_FAIL = "FAIL BENTO_SHELL_NETWORK"


def _module_strings(tree: ast.AST) -> dict[str, str]:
    found: dict[str, str] = {}
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                found[target.id] = node.value.value
    return found


def _function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _raises_name(func: ast.AST, name: str) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
            continue
        called = node.exc.func
        if isinstance(called, ast.Name) and called.id == name:
            return True
    return False


def _noteq_sha(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, ast.NotEq) for op in node.ops):
            continue
        names = [node.left, *node.comparators]
        if any(isinstance(side, ast.Name) and side.id == "SHELL_SHA256" for side in names):
            return True
    return False


def _calls_openssl(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.List):
            continue
        values = [elt.value for elt in node.elts if isinstance(elt, ast.Constant)]
        if "openssl" in values:
            return True
    return False


def _calls_name(func: ast.AST, name: str) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            return True
    return False


def bento_verifier_problems(text: str) -> list[str]:
    """The shell pin is the signed manifest, and a mismatch is raised."""
    problems: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [f"bento verifier did not parse: {exc}"]
    strings = _module_strings(tree)
    expected = {
        "SHELL_URL": BENTO_SHELL_URL,
        "MANIFEST_URL": BENTO_MANIFEST_URL,
        "SHELL_VERSION": BENTO_VERSION,
        "SHELL_SHA256": BENTO_SHA256,
    }
    for key, value in expected.items():
        if strings.get(key) != value:
            problems.append(f"bento {key} is not the pinned value")
    pin = _function(tree, "pin_problems")
    load = _function(tree, "load_shell")
    sign = _function(tree, "signature_ok")
    if pin is None or not _noteq_sha(pin) or not _calls_name(pin, "signature_ok"):
        problems.append("bento checksum compare is missing")
    if load is None or not _raises_name(load, "ShellPinError"):
        problems.append("bento mismatch is not raised")
    if sign is None or not _calls_openssl(sign):
        problems.append("bento signature check is missing openssl")
    return problems


def _handler_names(handler: ast.ExceptHandler) -> list[str]:
    kind = handler.type
    if isinstance(kind, ast.Name):
        return [kind.id]
    if isinstance(kind, ast.Attribute):
        return [kind.attr]
    if isinstance(kind, ast.Tuple):
        names: list[str] = []
        for elt in kind.elts:
            if isinstance(elt, ast.Name):
                names.append(elt.id)
            elif isinstance(elt, ast.Attribute):
                names.append(elt.attr)
        return names
    return []


def _raises_system_exit(nodes: list[ast.stmt]) -> bool:
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and isinstance(child.exc, ast.Call):
                func = child.exc.func
                if isinstance(func, ast.Name) and func.id == "SystemExit":
                    return True
    return False


def _returns_const(nodes: list[ast.stmt], value: object) -> bool:
    for node in nodes:
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            if node.value.value == value:
                return True
    return False


def _calls_in(nodes: list[ast.stmt], name: str) -> bool:
    for node in nodes:
        if _calls_name(node, name):
            return True
    return False


def _mentions(node: ast.AST, name: str) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == name:
            return True
    return False


def bento_deck_problems(text: str) -> list[str]:
    """A network error and a checksum mismatch both fail the job."""
    problems: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [f"weekly deck did not parse: {exc}"]
    if _module_strings(tree).get("NETWORK_FAIL") != NETWORK_FAIL:
        problems.append("network failure name is missing")
    build = _function(tree, "build_html")
    entry = _function(tree, "main")
    if (
        build is None
        or not _calls_name(build, "load_shell")
        or not _calls_name(build, "inject_shell")
    ):
        return problems + ["weekly deck does not load the pinned shell"]
    if entry is None or not _raises_system_exit(entry.body):
        problems.append("tampered bytes do not fail the job")
    pin_fail = False
    network_closed = False
    for node in ast.walk(build):
        if not isinstance(node, ast.ExceptHandler):
            continue
        names = _handler_names(node)
        if "Exception" in names and _returns_const(node.body, 0):
            problems.append("weekly deck swallows the shell pin")
        if "ShellPinError" in names:
            pin_fail = _returns_const(node.body, 1)
            if _returns_const(node.body, 0):
                problems.append("tampered bytes do not fail the job")
        if "URLError" not in names:
            continue
        if _returns_const(node.body, 0):
            problems.append("network failure ships the JSON deck")
        elif _calls_in(node.body, "inject_shell") or not (
            _returns_const(node.body, 1) or _raises_system_exit(node.body)
        ):
            problems.append("network-error path reaches the shell build")
        elif not _mentions(node, "NETWORK_FAIL"):
            problems.append("network failure name is missing")
        else:
            network_closed = True
    if not pin_fail:
        problems.append("tampered bytes do not fail the job")
    if not network_closed and not any(
        "network failure ships" in item or "network-error path" in item for item in problems
    ):
        problems.append("network failure does not fail the job")
    return problems


def bento_workflow_problems(text: str) -> list[str]:
    problems: list[str] = []
    if VERIFY_STEP not in text:
        problems.append("weekly deck workflow is missing the shell checksum step")
    if DECK_STEP not in text:
        problems.append("weekly deck workflow is missing the JSON deck step")
    verify_at = text.find("run: python3 scripts/verify_bento_shell.py")
    deck_at = text.find("run: python3 scripts/vf_weekly_deck.py")
    if verify_at < 0 or deck_at < 0 or verify_at > deck_at:
        problems.append("shell checksum step does not run before the JSON deck")
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
    for path in workflows:
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

    jobs = ROOT / ".github" / "workflows" / "jobs-write-through.yml"
    mutated = float_google_install(jobs.read_text(encoding="utf-8"))
    caught = install_spec_problems(mutated, path="jobs-write-through.yml")
    if not any("floating pip spec google-api-python-client" in item for item in caught):
        fail("reverted Google client install was not caught")
    if not any("floating pip spec google-auth" in item for item in caught):
        fail("reverted google-auth spec was not caught")
    if install_spec_problems(jobs.read_text(encoding="utf-8"), path="jobs-write-through.yml"):
        fail("pinned jobs-write-through install was refused")

    verifier = (ROOT / "scripts" / "verify_bento_shell.py").read_text(encoding="utf-8")
    deck = (ROOT / "scripts" / "vf_weekly_deck.py").read_text(encoding="utf-8")
    weekly = (WORKFLOWS / "velvetos-weekly-deck.yml").read_text(encoding="utf-8")
    if bento_verifier_problems(verifier):
        fail(f"pinned bento verifier was refused: {bento_verifier_problems(verifier)}")
    if bento_deck_problems(deck):
        fail(f"pinned weekly deck was refused: {bento_deck_problems(deck)}")
    if bento_workflow_problems(weekly):
        fail(f"pinned weekly workflow was refused: {bento_workflow_problems(weekly)}")

    def require_bento(label: str, found: list[str], needle: str) -> None:
        if not any(needle in item for item in found):
            fail(f"{label} was not caught: {found}")

    require_bento(
        "bento digest",
        bento_verifier_problems(verifier.replace(BENTO_SHA256, "0" * 64, 1)),
        "SHELL_SHA256 is not the pinned value",
    )
    require_bento(
        "bento raise",
        bento_verifier_problems(
            verifier.replace(
                '    if problems:\n        raise ShellPinError("; ".join(problems))\n    return shell\n',
                "    return shell\n",
                1,
            )
        ),
        "mismatch is not raised",
    )
    require_bento(
        "bento tamper",
        bento_deck_problems(deck.replace(
            '        print(f"FAIL bento shell: {exc}", file=sys.stderr)\n        return 1\n',
            '        print(f"FAIL bento shell: {exc}", file=sys.stderr)\n        return 0\n',
            1,
        )),
        "tampered bytes do not fail the job",
    )
    require_bento(
        "bento offline",
        bento_deck_problems(deck.replace(
            f'        print(f"{{NETWORK_FAIL}} HTML build skipped: {{exc}}", file=sys.stderr)\n'
            "        return 1\n",
            f'        print(f"{{NETWORK_FAIL}} HTML build skipped: {{exc}}", file=sys.stderr)\n'
            "        return 0\n",
            1,
        )),
        "network failure ships the JSON deck",
    )
    require_bento(
        "bento network path",
        bento_deck_problems(deck.replace(
            f'        print(f"{{NETWORK_FAIL}} HTML build skipped: {{exc}}", file=sys.stderr)\n'
            "        return 1\n",
            f'        print(f"{{NETWORK_FAIL}} HTML build skipped: {{exc}}", file=sys.stderr)\n',
            1,
        )),
        "network-error path reaches the shell build",
    )
    require_bento(
        "bento network gate",
        bento_workflow_problems(weekly.replace(VERIFY_STEP, "", 1)),
        "missing the shell checksum step",
    )
    for script, label in (
        ("verify_bento_shell.py", "bento shell self-test failed"),
        ("vf_weekly_deck.py", "weekly deck self-test failed"),
    ):
        probe = __import__("subprocess").run(
            [sys.executable, str(ROOT / "scripts" / script), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if probe.returncode != 0:
            fail(probe.stderr.strip() or probe.stdout.strip() or label)

    print(
        f"OK {NAME} workflows={len(workflows)} floating=0 allowlist=empty "
        "bare=caught exact=pass mixed=caught npm_float=caught npm_exact=pass "
        "npm_ci=pass hashed_lock=pass allow_one=pass mutation=caught "
        "bento_sha=caught bento_raise=caught bento_tamper=caught "
        "bento_offline=caught bento_network_path=caught bento_gate=caught"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
