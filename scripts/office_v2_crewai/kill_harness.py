"""Kill only the pilot-owned process tree. Untracked PIDs are refused."""
from __future__ import annotations

import os
import signal
import subprocess
import time

from office_v2_crewai.contract import ATTEMPT_TIMEOUT_SECONDS, COST_CEILING
from office_v2_crewai.usage_guard import UsageRefusal, assert_not_chroma_cli


class KillRefusal(RuntimeError):
    pass


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
        if not argv or not isinstance(argv[0], str):
            raise KillRefusal("SPAWN_ARGV_REFUSED")
        try:
            assert_not_chroma_cli(argv)
        except UsageRefusal as exc:
            raise KillRefusal(str(exc)) from exc
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
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
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return
