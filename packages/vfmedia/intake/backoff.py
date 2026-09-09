"""Backoff policy for intake retries — never a permanent hard stop."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Escalating delays; after the last step, keep using the final interval forever.
BACKOFF_SECONDS = (60, 300, 900, 3600, 14400)  # 1m → 5m → 15m → 1h → 4h


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def backoff_seconds_for_attempt(attempts: int) -> int:
    if attempts <= 0:
        return BACKOFF_SECONDS[0]
    idx = min(attempts - 1, len(BACKOFF_SECONDS) - 1)
    return BACKOFF_SECONDS[idx]


def record_failure(row: dict | None, err: str, *, now: datetime | None = None) -> dict:
    now = now or _now()
    row = dict(row or {})
    attempts = int(row.get("attempts") or 0) + 1
    delay = backoff_seconds_for_attempt(attempts)
    next_at = now + timedelta(seconds=delay)
    row.update(
        {
            "attempts": attempts,
            "lastError": err,
            "updatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "nextAfter": next_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "backoffSeconds": delay,
            "permanentStop": False,
            "policy": "exponential-cap-then-repeat",
        }
    )
    return row


def ready_for_retry(row: dict | None, *, now: datetime | None = None) -> bool:
    """True if no backoff window, or nextAfter has passed. Never permanently blocked."""
    if not row:
        return True
    now = now or _now()
    nxt = _parse(row.get("nextAfter"))
    if nxt is None:
        return True
    return now >= nxt


def clear_retry() -> dict:
    return {}
