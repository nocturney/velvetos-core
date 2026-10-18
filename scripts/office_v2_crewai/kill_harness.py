"""Kill only the pilot-owned process tree. Untracked PIDs are refused."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from office_v2_crewai.contract import ATTEMPT_TIMEOUT_SECONDS, COST_CEILING
from office_v2_crewai.usage_guard import UsageRefusal, assert_not_chroma_cli

TASKKILL_TIMEOUT_SECONDS = 8
_SPAWN_ENV_KEYS = (
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


class KillRefusal(RuntimeError):
    pass


def executable_is_absolute(path: str) -> bool:
    if os.path.isabs(path):
        return True
    return len(path) >= 3 and path[0].isalpha() and path[1] == ":" and path[2] in "\\/"


def _python_argv0(argv0: str) -> bool:
    base = argv0.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if base.endswith(".exe"):
        base = base[:-4]
    return base == "python" or base.startswith("python")


def pin_spawn_executable(argv: list[str]) -> list[str]:
    """Python children use this interpreter. Any other child must already be absolute."""
    if not argv or not isinstance(argv[0], str):
        raise KillRefusal("SPAWN_ARGV_REFUSED")
    if _python_argv0(argv[0]):
        return [sys.executable, *argv[1:]]
    if executable_is_absolute(argv[0]):
        return list(argv)
    raise KillRefusal("SPAWN_PATH_LOOKUP_REFUSED")


def spawn_environment(executable: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in _SPAWN_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            env[key] = value
    env["PATH"] = str(Path(executable).resolve().parent)
    return env


def taskkill_argv(pid: int) -> list[str]:
    if type(pid) is not int or pid <= 1:
        raise KillRefusal("TASKKILL_PID_REFUSED")
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    root = root.rstrip("\\/")
    exe = root + "\\System32\\taskkill.exe"
    if not executable_is_absolute(exe):
        raise KillRefusal("TASKKILL_PATH_REFUSED")
    return [exe, "/PID", str(pid), "/T", "/F"]


def isolated_argv(argv: list[str]) -> list[str]:
    """Run a Python child with -I so user site, .pth, and PYTHONHOME do not load."""
    if not argv or not isinstance(argv[0], str):
        raise KillRefusal("SPAWN_ARGV_REFUSED")
    base = argv[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if not (base == "python" or base.startswith("python")):
        return list(argv)
    if any(part in {"-I", "-E"} for part in argv[1:]):
        return list(argv)
    return [argv[0], "-I", *argv[1:]]


class KillHarness:
    def __init__(self, timeout_seconds: int = ATTEMPT_TIMEOUT_SECONDS, cost_ceiling: int = COST_CEILING):
        if int(cost_ceiling) != 0:
            raise KillRefusal("COST_CEILING_NOT_ZERO")
        if int(timeout_seconds) <= 0:
            raise KillRefusal("TIMEOUT_NOT_POSITIVE")
        self.timeout_seconds = int(timeout_seconds)
        self.cost_ceiling = 0
        self.owned: set[int] = set()
        self.killed: list[int] = []

    def spawn(self, argv: list[str]) -> subprocess.Popen:
        argv = isolated_argv(argv)
        try:
            assert_not_chroma_cli(argv)
        except UsageRefusal as exc:
            raise KillRefusal(str(exc)) from exc
        argv = pin_spawn_executable(argv)
        kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "env": spawn_environment(argv[0]),
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen(argv, **kwargs)
        self.owned.add(proc.pid)
        return proc

    def expired(self, started_monotonic: float, now: float | None = None) -> bool:
        clock = time.monotonic() if now is None else now
        return (clock - started_monotonic) >= self.timeout_seconds

    def socket_timeout(self, started_monotonic: float, now: float, cap: float = 30) -> float:
        """Seconds left for one socket, never above cap. Zero remaining is a refusal."""
        if self.expired(started_monotonic, now=now):
            raise KillRefusal("ATTEMPT_TIMEOUT")
        remaining = self.timeout_seconds - (now - started_monotonic)
        if remaining <= 0:
            raise KillRefusal("ATTEMPT_TIMEOUT")
        return float(min(cap, remaining))

    def signal_pid(self, pid: int) -> str:
        if pid not in self.owned or pid <= 1 or pid == os.getpid():
            return "REFUSED_NOT_OWNED"
        self._terminate(pid)
        self.owned.discard(pid)
        self.killed.append(pid)
        return "KILLED"

    def kill_owned(self) -> list[int]:
        killed = []
        for pid in list(self.owned):
            if self.signal_pid(pid) == "KILLED":
                killed.append(pid)
        return killed

    def _terminate(self, pid: int) -> None:
        if os.name == "nt":
            subprocess.run(
                taskkill_argv(pid),
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=TASKKILL_TIMEOUT_SECONDS,
            )
            return
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return
