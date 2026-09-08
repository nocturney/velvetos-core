"""Non-overlapping intake runs via a durable lock file."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class LockHandle:
    path: Path
    payload: dict

    def release(self) -> None:
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if data.get("pid") == self.payload.get("pid") and data.get("token") == self.payload.get(
            "token"
        ):
            self.path.unlink(missing_ok=True)


def acquire(lock_path: Path, *, stale_seconds: int = 3600) -> LockHandle | None:
    """Try to acquire lock. Returns None if another live run holds it."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if lock_path.is_file():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        started = float(existing.get("startedEpoch") or 0)
        pid = existing.get("pid")
        alive = False
        if isinstance(pid, int) and pid > 0:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        if alive and started and (now - started) < stale_seconds:
            return None
        # Stale or dead — take over
        lock_path.unlink(missing_ok=True)

    token = f"{os.getpid()}-{int(now * 1000)}"
    payload = {
        "pid": os.getpid(),
        "token": token,
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
        "startedAt": _now(),
        "startedEpoch": now,
    }
    # Exclusive create
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(lock_path), flags, 0o644)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return LockHandle(path=lock_path, payload=payload)
