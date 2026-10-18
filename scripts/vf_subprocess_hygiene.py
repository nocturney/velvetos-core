"""Pinned subprocess spawns. No shell, no inherited environment, no 8.3 expansion.

Path.resolve() and realpath() expand Windows 8.3 short names, so a temp
directory created as RUNNER~1 no longer matches the path that was launched.
This module normalizes separators and, on Windows, case. It does not resolve.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterator


class HygieneError(RuntimeError):
    pass


_spawn = subprocess.run


_BASE_ENV_KEYS = (
    "SystemRoot",
    "SYSTEMROOT",
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


def is_absolute_executable(path: str) -> bool:
    if os.path.isabs(path):
        return True
    return len(path) >= 3 and path[0].isalpha() and path[1] == ":" and path[2] in "\\/"


def _nt_key(path: str) -> str:
    """Case-folded Windows path. `..` stays a segment, and short names stay short."""
    text = path.replace("/", "\\")
    prefix = ""
    rest = text
    if text.startswith("\\\\"):
        prefix = "\\\\"
        rest = text[2:]
    pieces = [piece for piece in rest.split("\\") if piece not in {"", "."}]
    return (prefix + "\\".join(pieces)).casefold()


def paths_match(left: str, right: str, *, os_name: str | None = None) -> bool:
    kind = os.name if os_name is None else os_name
    if kind == "nt":
        return _nt_key(left) == _nt_key(right)
    return os.path.normpath(left) == os.path.normpath(right)


def executable_directory(executable: str) -> str:
    if not is_absolute_executable(executable):
        raise HygieneError("EXECUTABLE_NOT_ABSOLUTE")
    directory = os.path.dirname(os.path.normpath(executable))
    if not directory or not is_absolute_executable(directory):
        raise HygieneError("EXECUTABLE_DIRECTORY_EMPTY")
    return directory


def allowlisted_env(executable: str, extra_keys: tuple[str, ...] = ()) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in (*_BASE_ENV_KEYS, *extra_keys):
        if key.startswith("GIT_"):
            continue
        value = os.environ.get(key)
        if value:
            env[key] = value
    env["PATH"] = executable_directory(executable)
    return env


def pin_which(name: str) -> str:
    found = shutil.which(name)
    if not found or not is_absolute_executable(found):
        raise HygieneError("PATH_LOOKUP_REFUSED")
    return os.path.normpath(found)


def run_absolute(
    executable: str,
    args: list[str],
    *,
    timeout: float,
    extra_keys: tuple[str, ...] = (),
    **kwargs,
) -> subprocess.CompletedProcess:
    if timeout is None or timeout <= 0:
        raise HygieneError("TIMEOUT_REQUIRED")
    if not is_absolute_executable(executable):
        raise HygieneError("EXECUTABLE_NOT_ABSOLUTE")
    if kwargs.get("shell") or "env" in kwargs or "timeout" in kwargs:
        raise HygieneError("CALLER_ENV_REFUSED")
    return _spawn(
        [os.path.normpath(executable), *args],
        timeout=timeout,
        env=allowlisted_env(executable, extra_keys),
        shell=False,
        **kwargs,
    )


def run_pinned(
    name: str,
    args: list[str],
    *,
    timeout: float,
    extra_keys: tuple[str, ...] = (),
    **kwargs,
) -> subprocess.CompletedProcess:
    return run_absolute(pin_which(name), args, timeout=timeout, extra_keys=extra_keys, **kwargs)


@contextlib.contextmanager
def record_pinned_spawn(
    name: str,
    *,
    returncode: int = 0,
) -> Iterator[tuple[list[tuple[list[str], dict]], str]]:
    """Pin `name` to a short path and record the one spawn. resolve/realpath expand it."""
    sentinel = "VF_SUBPROCESS_HYGIENE_SENTINEL"
    tracked = (sentinel, "GIT_EXEC_PATH", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_COUNT", "GH_TOKEN")
    previous = {key: os.environ.get(key) for key in tracked}
    os.environ[sentinel] = "leak"
    os.environ["GIT_EXEC_PATH"] = "/tmp/evil-git-exec"
    os.environ["GIT_CONFIG_GLOBAL"] = "/tmp/evil-gitconfig"
    os.environ["GIT_CONFIG_COUNT"] = "1"
    os.environ["GH_TOKEN"] = "fixture-gh-token"
    short = (
        "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\vf-pin\\" + name + ".exe"
        if os.name == "nt"
        else "/tmp/RUNNER~1/bin/" + name
    )
    calls: list[tuple[list[str], dict]] = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        stdout = ""
        if name == "ffprobe":
            stdout = "{}"
        elif name == "gh":
            stdout = (
                '{"headSha":"abc","status":"completed","conclusion":"success",'
                '"event":"push","ok":true}'
            )
        return subprocess.CompletedProcess(list(argv), returncode, stdout=stdout, stderr="")

    def which(candidate, *args, **kwargs):
        if candidate == name:
            return short
        return original_which(candidate, *args, **kwargs)

    def expanding_resolve(self, *args, **kwargs):
        return Path(str(self).replace("RUNNER~1", "runneradmin"))

    def expanding_realpath(path, *args, **kwargs):
        return str(path).replace("RUNNER~1", "runneradmin")

    global _spawn
    original_run = _spawn
    original_which = shutil.which
    original_resolve = Path.resolve
    original_realpath = os.path.realpath
    _spawn = fake_run
    shutil.which = which
    Path.resolve = expanding_resolve
    os.path.realpath = expanding_realpath
    try:
        yield calls, short
    finally:
        _spawn = original_run
        shutil.which = original_which
        Path.resolve = original_resolve
        os.path.realpath = original_realpath
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def expect_pinned(
    calls: list[tuple[list[str], dict]],
    short: str,
    *,
    timeout: float,
    keep_gh_token: bool,
) -> None:
    if len(calls) != 1:
        raise AssertionError(f"expected one spawn, saw {len(calls)}")
    argv, kwargs = calls[0]
    pinned = os.path.normpath(short)
    if argv[0] != pinned or not is_absolute_executable(argv[0]):
        raise AssertionError(f"executable was not pinned absolute: {argv!r}")
    if kwargs.get("timeout") != timeout:
        raise AssertionError(f"timeout {kwargs.get('timeout')!r} != {timeout}")
    if kwargs.get("shell"):
        raise AssertionError("shell was enabled")
    env = kwargs.get("env")
    if not isinstance(env, dict):
        raise AssertionError("environment was inherited")
    if "VF_SUBPROCESS_HYGIENE_SENTINEL" in env or any(key.startswith("GIT_") for key in env):
        raise AssertionError("environment was not allowlisted: " + ",".join(sorted(env)))
    path = env.get("PATH", "")
    if "runneradmin" in path or "RUNNER~1" not in path:
        raise AssertionError(f"PATH expanded a short name: {path}")
    if not paths_match(path, executable_directory(argv[0])):
        raise AssertionError(f"PATH {path} != {executable_directory(argv[0])}")
    if keep_gh_token and env.get("GH_TOKEN") != "fixture-gh-token":
        raise AssertionError("GH_TOKEN was dropped")
    if not keep_gh_token and "GH_TOKEN" in env:
        raise AssertionError("GH_TOKEN leaked into a non-gh spawn")
    if not paths_match(r"C:\Windows\System32", r"c:\windows\system32", os_name="nt"):
        raise AssertionError("Windows path compare is case-sensitive")
    if paths_match("/Tmp/Bin", "/tmp/bin", os_name="posix"):
        raise AssertionError("POSIX path compare folded case")
