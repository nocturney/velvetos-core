#!/usr/bin/env python3
"""Fail-closed spawn helpers for absolute tools and allowlisted environments.

Does not replace the git runner in check-all.py or the gh spawns claimed by
subprocess hygiene slice 2. Stage 8 generators stay on their historical
policy-manifest hashes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

GIT_TIMEOUT_SECONDS = 30
_AMBIENT_ENV_KEYS = (
    "SYSTEMROOT",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
)
_BASE_ENV_KEYS = _AMBIENT_ENV_KEYS
FORCED_ENV_KEYS = (
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "XDG_CONFIG_HOME",
    "XDG_CONFIG_DIRS",
    "TEMP",
    "TMP",
    "TMPDIR",
    "GIT_CONFIG_NOSYSTEM",
)
_LOCKED_EXTRA_KEYS = {key.upper() for key in FORCED_ENV_KEYS}
_home_dir: str | None = None
_temp_dir: str | None = None


class SpawnRefusal(RuntimeError):
    """A spawn was not an absolute tool with an allowlisted environment."""


def executable_is_absolute(path: str) -> bool:
    if os.path.isabs(path):
        return True
    return len(path) >= 3 and path[0].isalpha() and path[1] == ":" and path[2] in "\\/"


def same_pinned_directory(
    actual: str,
    expected: str,
    *,
    realpath=os.path.realpath,
    fold_case: bool | None = None,
    separator: str | None = None,
) -> bool:
    """True when both strings are one directory and name the same real path.

    A search PATH is not a pin. Windows compares case-insensitively.
    realpath expands an 8.3 temp directory to its long name.
    """
    if fold_case is None:
        fold_case = os.name == "nt"
    if separator is None:
        separator = os.pathsep
    if not isinstance(actual, str) or not isinstance(expected, str):
        return False
    if not actual or not expected:
        return False
    if separator in actual or separator in expected:
        return False
    left = realpath(actual)
    right = realpath(expected)
    if fold_case:
        left = os.path.normcase(left).casefold()
        right = os.path.normcase(right).casefold()
    return left == right


def join_tool_path(dirs: list[str]) -> str:
    """Join absolute tool directories. A copied search PATH is refused."""
    cleaned: list[str] = []
    for entry in dirs:
        if not isinstance(entry, str) or not entry or os.pathsep in entry:
            raise SpawnRefusal("SPAWN_PATH_REFUSED")
        if not executable_is_absolute(entry):
            raise SpawnRefusal("SPAWN_PATH_REFUSED")
        resolved = str(Path(entry).resolve())
        if resolved not in cleaned:
            cleaned.append(resolved)
    if not cleaned:
        raise SpawnRefusal("SPAWN_PATH_REFUSED")
    return os.pathsep.join(cleaned)


def resolve_executable(name_or_path: str) -> str:
    """Return one absolute executable.

    A bare name is looked up once on the ambient PATH, then pinned.
    Later spawns do not search that PATH again.
    """
    if not isinstance(name_or_path, str) or not name_or_path.strip():
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    if name_or_path.startswith("-"):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    candidate = name_or_path
    if not executable_is_absolute(candidate):
        found = shutil.which(candidate)
        if not found or not executable_is_absolute(found):
            raise SpawnRefusal("SPAWN_PATH_LOOKUP_REFUSED")
        candidate = found
    resolved = str(Path(candidate).resolve())
    if not executable_is_absolute(resolved):
        raise SpawnRefusal("SPAWN_PATH_LOOKUP_REFUSED")
    return resolved


def pinned_path(executable: str) -> str:
    """PATH for one tool. Windows git also gets its sibling tool directories."""
    parent = Path(executable).resolve().parent
    entries = [parent]
    if os.name == "nt" and parent.name.lower() in {"cmd", "bin"} and parent.parent.name.lower() == "git":
        for parts in (("..", "bin"), ("..", "usr", "bin"), ("..", "mingw64", "bin")):
            candidate = (parent.joinpath(*parts)).resolve()
            if candidate.is_dir() and candidate not in entries:
                entries.append(candidate)
    return os.pathsep.join(str(entry) for entry in entries)


def _private_dir(prefix: str) -> str:
    path = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return str(path)


def controlled_home() -> str:
    """Empty directory used as HOME for every allowlisted spawn."""
    global _home_dir
    if _home_dir is None or not Path(_home_dir).is_dir():
        _home_dir = _private_dir("vf-spawn-home-")
    return _home_dir


def controlled_temp() -> str:
    """Private temp directory. Inherited TEMP, TMP, and TMPDIR are not copied."""
    global _temp_dir
    if _temp_dir is None or not Path(_temp_dir).is_dir():
        _temp_dir = _private_dir("vf-spawn-tmp-")
    return _temp_dir


def _system_root() -> str:
    for key in ("SYSTEMROOT", "SystemRoot"):
        value = os.environ.get(key)
        if isinstance(value, str) and value and executable_is_absolute(value):
            try:
                return str(Path(value).resolve())
            except OSError:
                continue
    return ""


def _comspec_is_trusted(value: str, system_root: str) -> bool:
    if not system_root or not value:
        return False
    try:
        resolved = str(Path(value).resolve())
    except OSError:
        return False
    return resolved == system_root or resolved.startswith(system_root + os.sep)


def allowlisted_env(executable: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Copy a fixed key list, pin PATH, and replace home and temp.

    GIT_* and NODE_OPTIONS are never copied. This function sets
    GIT_CONFIG_NOSYSTEM=1 itself. HOME, USERPROFILE, HOMEDRIVE, HOMEPATH,
    XDG_CONFIG_HOME, XDG_CONFIG_DIRS, TEMP, TMP, and TMPDIR come from a
    controlled directory, not from the caller. extra cannot replace those,
    PATH, or smuggle GIT_* / NODE_OPTIONS back in. COMSPEC is copied only
    when it resolves inside SYSTEMROOT.
    """
    env: dict[str, str] = {}
    system_root = _system_root()
    for key in _AMBIENT_ENV_KEYS:
        upper = key.upper()
        if upper.startswith("GIT_") or upper == "NODE_OPTIONS":
            continue
        value = os.environ.get(key)
        if not value:
            continue
        if upper == "COMSPEC" and not _comspec_is_trusted(value, system_root):
            continue
        env[key] = value
    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            upper = key.upper()
            if (
                upper.startswith("GIT_")
                or upper == "NODE_OPTIONS"
                or upper == "PATH"
                or upper in _LOCKED_EXTRA_KEYS
            ):
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            env[key] = value
    home = controlled_home()
    temp = controlled_temp()
    drive, tail = os.path.splitdrive(home)
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["HOMEDRIVE"] = drive
    env["HOMEPATH"] = tail or home
    env["XDG_CONFIG_HOME"] = home
    env["XDG_CONFIG_DIRS"] = home
    env["TEMP"] = temp
    env["TMP"] = temp
    env["TMPDIR"] = temp
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["PATH"] = pinned_path(executable)
    return env


def run_tool(
    argv: list[str],
    *,
    timeout: float,
    extra_env: dict[str, str] | None = None,
    cwd: Path | str | None = None,
    check: bool = False,
    input: str | None = None,
    path_dirs: list[str] | None = None,
    close_stdin: bool = False,
) -> subprocess.CompletedProcess[str]:
    if not argv or not isinstance(argv[0], str):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise SpawnRefusal("SPAWN_TIMEOUT_REFUSED")
    executable = resolve_executable(argv[0])
    env = allowlisted_env(executable, extra_env)
    if path_dirs is not None:
        env["PATH"] = join_tool_path([str(Path(executable).resolve().parent), *path_dirs])
    call: dict = {
        "cwd": cwd,
        "env": env,
        "timeout": timeout,
        "check": check,
        "capture_output": True,
        "text": True,
    }
    if input is None and close_stdin:
        call["stdin"] = subprocess.DEVNULL
    elif input is not None:
        call["input"] = input
    return subprocess.run([executable, *argv[1:]], **call)


def git_revision(token: str) -> str:
    """A revision git must see before ``--``.

    Git reads tokens after ``--`` as paths, not revisions. A leading dash is
    an option, and a newline, CR, or NUL is an argument break, so both are
    refused before git runs.
    """
    if (
        not isinstance(token, str)
        or not token
        or token.startswith("-")
        or any(char in token for char in "\n\r\x00")
    ):
        raise SpawnRefusal("GIT_REV_REFUSED")
    return token


def run_git(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    check: bool = False,
    timeout: float = GIT_TIMEOUT_SECONDS,
    input: str | None = None,
    user_args: list[str] | None = None,
    revisions: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Absolute git with a timeout and an allowlisted environment.

    ``user_args`` (urls, refspecs, paths) are placed after ``--`` so git does
    not parse them as options. ``revisions`` stay before ``--`` because git
    would otherwise treat them as paths; ``git_revision`` refuses a leading
    dash and a newline, CR, or NUL. With no ``input``, stdin is ``DEVNULL``
    so ``git apply --check`` cannot wait on an inherited pipe.
    """
    if any(not isinstance(arg, str) or arg == "" for arg in args):
        raise SpawnRefusal("GIT_ARGV_REFUSED")
    argv = list(args)
    if revisions:
        argv.extend(git_revision(rev) for rev in revisions)
    if user_args is not None or revisions:
        operands = [] if user_args is None else list(user_args)
        for item in operands:
            if not isinstance(item, str) or item == "":
                raise SpawnRefusal("GIT_USER_ARG_REFUSED")
        argv.append("--")
        argv.extend(operands)
    return run_tool(
        ["git", *argv],
        cwd=cwd,
        check=check,
        timeout=timeout,
        input=input,
        close_stdin=input is None,
    )


def prove_refused_git_args() -> list[str]:
    """An empty argv item and an empty user arg are refused before git runs."""
    errors: list[str] = []
    spawned: list[list[str]] = []
    original = subprocess.run

    def fake_run(argv, **kwargs):
        spawned.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    subprocess.run = fake_run
    try:
        try:
            run_git([""])
        except SpawnRefusal as exc:
            if str(exc) != "GIT_ARGV_REFUSED":
                errors.append(f"empty argv refused as {exc}")
        else:
            errors.append("empty argv item was accepted")
        try:
            run_git(["status"], user_args=[""])
        except SpawnRefusal as exc:
            if str(exc) != "GIT_USER_ARG_REFUSED":
                errors.append(f"empty user arg refused as {exc}")
        else:
            errors.append("empty user arg was accepted")
    finally:
        subprocess.run = original
    if spawned:
        errors.append("refused git argv spawned git")
    return errors


def user_arg_separator_errors(argv: list[str], user_args: list[str]) -> list[str]:
    """Errors when ``--`` is not the separator immediately before user args."""
    if len(argv) < 2 or "--" not in argv[1:]:
        return ["git missing -- before user args"]
    idx = argv.index("--")
    if argv[idx + 1:] != list(user_args):
        return [f"git -- was not before the user args: {argv}"]
    return []


def revision_form_errors(argv: list[str], revisions: list[str]) -> list[str]:
    """Errors when revisions are not the tokens immediately before ``--``."""
    if len(argv) < 2 or "--" not in argv[1:]:
        return ["git missing -- after revisions"]
    idx = argv.index("--")
    if argv[idx - len(revisions):idx] != list(revisions):
        return [f"git revisions were not directly before --: {argv}"]
    if argv[idx + 1:]:
        return [f"git revision form gained pathspecs: {argv}"]
    return []


def captured_rev_parse_errors(captured: list[list[str]], revisions: list[str]) -> list[str]:
    """Every captured ``rev-parse`` keeps ``revisions`` immediately before ``--``."""
    parses = [argv for argv in captured if len(argv) > 1 and argv[1] == "rev-parse"]
    if not parses:
        return ["rev-parse was not captured"]
    errors: list[str] = []
    for argv in parses:
        errors.extend(revision_form_errors(argv, revisions))
    return errors


def allowlisted_git_errors(argv: list[str], kwargs: dict, *, timeout: float) -> list[str]:
    """Errors when one captured git spawn is not absolute, timed, and allowlisted."""
    errors: list[str] = []
    if not argv or not executable_is_absolute(argv[0]):
        return [f"git was not absolute: {argv}"]
    if kwargs.get("timeout") != timeout:
        errors.append("git timeout missing")
    env = kwargs.get("env")
    git_keys = [str(key).upper() for key in (env or {}) if str(key).upper().startswith("GIT_")]
    if (
        not isinstance(env, dict)
        or "VF_SPAWN_SENTINEL" in env
        or set(git_keys) != {"GIT_CONFIG_NOSYSTEM"}
        or env.get("GIT_CONFIG_NOSYSTEM") != "1"
    ):
        return errors + ["git environment was not allowlisted"]
    home = controlled_home()
    temp = controlled_temp()
    if (
        env.get("HOME") != home
        or env.get("USERPROFILE") != home
        or env.get("XDG_CONFIG_HOME") != home
        or env.get("XDG_CONFIG_DIRS") != home
        or env.get("TEMP") != temp
        or env.get("TMP") != temp
        or env.get("TMPDIR") != temp
    ):
        errors.append("git home or temp was not the sandbox")
    parts = env.get("PATH", "").split(os.pathsep)
    first = parts[0] if parts else ""
    if not same_pinned_directory(first, str(Path(argv[0]).resolve().parent)):
        errors.append("git PATH was not the executable directory")
    install = Path(argv[0]).resolve().parent
    root = install.parent if os.name == "nt" and install.parent.name.lower() == "git" else install
    for entry in parts[1:]:
        resolved = Path(entry).resolve()
        if resolved != root and root not in resolved.parents:
            errors.append(f"git PATH escaped the install: {entry}")
    return errors


def prove_controlled_home() -> list[str]:
    """A poisoned home, temp, or COMSPEC does not reach the child or git config."""
    import json
    import sys

    errors: list[str] = []
    keys = (
        "HOME",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "XDG_CONFIG_HOME",
        "XDG_CONFIG_DIRS",
        "TEMP",
        "TMP",
        "TMPDIR",
        "COMSPEC",
    )
    previous = {key: os.environ.get(key) for key in keys}
    with tempfile.TemporaryDirectory(prefix="vf-spawn-poison-") as tmp:
        root = Path(tmp)
        poison_home = root / "poison-home"
        poison_xdg = root / "poison-xdg"
        poison_tmp = root / "poison-tmp"
        poison_home.mkdir()
        (poison_xdg / "git").mkdir(parents=True)
        poison_tmp.mkdir()
        marker = root / "hook-ran"
        hook = root / "hook.sh"
        hook.write_text(f"#!/bin/sh\nprintf hooked > '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)
        config = f"[core]\n\tfsmonitor = {hook}\n"
        (poison_home / ".gitconfig").write_text(config, encoding="utf-8")
        (poison_xdg / "git" / "config").write_text(config, encoding="utf-8")
        evil_cmd = root / "evil-cmd"
        evil_cmd.write_text("#!/bin/sh\n", encoding="utf-8")
        poisoned = {
            "HOME": str(poison_home),
            "USERPROFILE": str(poison_home),
            "HOMEDRIVE": "Z:",
            "HOMEPATH": "\\PoisonUsers\\attacker",
            "XDG_CONFIG_HOME": str(poison_xdg),
            "XDG_CONFIG_DIRS": str(poison_xdg),
            "TEMP": str(poison_tmp),
            "TMP": str(poison_tmp),
            "TMPDIR": str(poison_tmp),
            "COMSPEC": str(evil_cmd),
        }
        os.environ.update(poisoned)
        repo = root / "repo"
        repo.mkdir()
        try:
            report_keys = keys + ("GIT_CONFIG_NOSYSTEM",)
            shown = run_tool(
                [
                    sys.executable,
                    "-c",
                    "import json,os; keys=" + repr(report_keys) + "; "
                    "print(json.dumps({key: os.environ.get(key) for key in keys}))",
                ],
                timeout=30,
            )
            listed = run_git(["config", "--global", "--get", "core.fsmonitor"])
            run_git(["init", "-q", "-b", "main"], cwd=repo)
            status = run_git(["status"], cwd=repo)
            try:
                run_tool([sys.executable, "-c", "print(1)"], timeout=30, extra_env={"HOME": str(poison_home)})
            except SpawnRefusal as exc:
                if "SPAWN_ENV_REFUSED" not in str(exc):
                    errors.append(f"extra HOME refused as {exc}")
            else:
                errors.append("extra HOME was accepted")
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        if shown.returncode != 0:
            return errors + [f"child env probe failed: {shown.stderr}"]
        try:
            child = json.loads(shown.stdout)
        except json.JSONDecodeError as exc:
            return errors + [f"child env was not JSON: {exc}"]
        home = controlled_home()
        temp = controlled_temp()
        if child.get("HOME") != home or child.get("USERPROFILE") != home:
            errors.append(f"poisoned home reached the child: {child}")
        if child.get("XDG_CONFIG_HOME") != home or child.get("XDG_CONFIG_DIRS") != home:
            errors.append(f"poisoned XDG config reached the child: {child}")
        if child.get("TEMP") != temp or child.get("TMP") != temp or child.get("TMPDIR") != temp:
            errors.append(f"poisoned temp reached the child: {child}")
        if child.get("COMSPEC") == str(evil_cmd):
            errors.append("poisoned COMSPEC reached the child")
        if child.get("GIT_CONFIG_NOSYSTEM") != "1":
            errors.append(f"GIT_CONFIG_NOSYSTEM was not forced: {child}")
        for key, value in poisoned.items():
            if value and value in shown.stdout:
                errors.append(f"poisoned {key} reached the child")
        if hook.name in (listed.stdout or "") or (listed.stdout or "").strip():
            errors.append(f"poisoned global gitconfig was read: {listed.stdout!r}")
        if marker.is_file():
            errors.append("poisoned core.fsmonitor ran")
        if status.returncode != 0:
            errors.append(f"git status failed under the sandbox: {status.stderr}")
    return errors


def windows_pin_case_errors() -> list[str]:
    """8.3 and case-fold pin checks. A search PATH is not one directory."""
    errors: list[str] = []
    short = "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\tool-abc"
    long = "C:\\Users\\runneradmin\\AppData\\Local\\Temp\\tool-abc"

    def expand_short(path: str) -> str:
        return str(path).replace("/", "\\").replace("RUNNER~1", "runneradmin")

    if not same_pinned_directory(short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("8.3 directory did not match its long path")
    if not same_pinned_directory(short, long.upper(), realpath=expand_short, fold_case=True, separator=";"):
        errors.append("pin comparison stayed case-sensitive")
    if same_pinned_directory(short, long + "\\other", realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a different directory was accepted as the pin")
    if same_pinned_directory(long + ";" + short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a search PATH was accepted as the pin")
    return errors
