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
from pathlib import Path

GIT_TIMEOUT_SECONDS = 30
_BASE_ENV_KEYS = (
    "SYSTEMROOT",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
)


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


def allowlisted_env(executable: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Copy a fixed key list and set PATH to the tool directory.

    GIT_* and NODE_OPTIONS are never copied. extra cannot replace PATH or
    smuggle those names back in.
    """
    env: dict[str, str] = {}
    for key in _BASE_ENV_KEYS:
        if key.upper().startswith("GIT_") or key.upper() == "NODE_OPTIONS":
            continue
        value = os.environ.get(key)
        if value:
            env[key] = value
    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            upper = key.upper()
            if upper.startswith("GIT_") or upper == "NODE_OPTIONS" or upper == "PATH":
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            env[key] = value
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
) -> subprocess.CompletedProcess[str]:
    if not argv or not isinstance(argv[0], str):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise SpawnRefusal("SPAWN_TIMEOUT_REFUSED")
    executable = resolve_executable(argv[0])
    env = allowlisted_env(executable, extra_env)
    if path_dirs is not None:
        env["PATH"] = join_tool_path([str(Path(executable).resolve().parent), *path_dirs])
    return subprocess.run(
        [executable, *argv[1:]],
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=check,
        capture_output=True,
        text=True,
        input=input,
    )


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
    dash and a newline, CR, or NUL.
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
    return run_tool(["git", *argv], cwd=cwd, check=check, timeout=timeout, input=input)


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


def allowlisted_git_errors(argv: list[str], kwargs: dict, *, timeout: float) -> list[str]:
    """Errors when one captured git spawn is not absolute, timed, and allowlisted."""
    errors: list[str] = []
    if not argv or not executable_is_absolute(argv[0]):
        return [f"git was not absolute: {argv}"]
    if kwargs.get("timeout") != timeout:
        errors.append("git timeout missing")
    env = kwargs.get("env")
    if (
        not isinstance(env, dict)
        or "VF_SPAWN_SENTINEL" in env
        or any(str(key).upper().startswith("GIT_") for key in env)
    ):
        return errors + ["git environment was not allowlisted"]
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
