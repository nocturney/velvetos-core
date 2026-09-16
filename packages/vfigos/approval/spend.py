"""Atomic approval spend / claim store.

Production: GCS object create-if-absent (ifGenerationMatch=0).
Tests: in-memory store with threading lock.

Never check-then-create. Never unspend automatically.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ClaimResult:
    ok: bool
    status: str  # claimed | already_spent | store_unavailable | error
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "status": self.status, "detail": self.detail}


class SpendStore(Protocol):
    def claim(self, approval_id: str, *, meta: dict[str, Any] | None = None) -> ClaimResult: ...


class MemorySpendStore:
    """Process-local atomic create-if-absent for tests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spent: dict[str, dict[str, Any]] = {}

    def claim(self, approval_id: str, *, meta: dict[str, Any] | None = None) -> ClaimResult:
        if not approval_id or not isinstance(approval_id, str):
            return ClaimResult(ok=False, status="error", detail="approval_id required")
        with self._lock:
            if approval_id in self._spent:
                return ClaimResult(ok=False, status="already_spent", detail="approval already claimed")
            row = {
                "approval_id": approval_id,
                "claimed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "meta": meta or {},
            }
            self._spent[approval_id] = row
            return ClaimResult(ok=True, status="claimed")

    def is_spent(self, approval_id: str) -> bool:
        with self._lock:
            return approval_id in self._spent


class UnavailableSpendStore:
    """Fail-closed stand-in when GCS is not configured."""

    def claim(self, approval_id: str, *, meta: dict[str, Any] | None = None) -> ClaimResult:
        return ClaimResult(
            ok=False,
            status="store_unavailable",
            detail="approval spend store not configured; mutation blocked",
        )


class GcsSpendStore:
    """GCS create-if-absent via ifGenerationMatch=0.

    Bucket should be dedicated (velvet-ig-approval-spend). Mutation SA needs
    object create only — no delete/overwrite.
    """

    def __init__(self, bucket_name: str, *, prefix: str = "spent/"):
        if not bucket_name:
            raise ValueError("bucket_name required")
        self.bucket_name = bucket_name
        self.prefix = prefix if prefix.endswith("/") else prefix + "/"

    def claim(self, approval_id: str, *, meta: dict[str, Any] | None = None) -> ClaimResult:
        if not approval_id or "/" in approval_id or ".." in approval_id:
            return ClaimResult(ok=False, status="error", detail="invalid approval_id")
        try:
            from google.cloud import storage  # type: ignore
            from google.api_core import exceptions as gax  # type: ignore
        except Exception as exc:
            return ClaimResult(
                ok=False,
                status="store_unavailable",
                detail=f"google-cloud-storage unavailable: {exc}",
            )
        client = storage.Client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(f"{self.prefix}{approval_id}")
        body = json.dumps(
            {
                "approval_id": approval_id,
                "claimed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "meta": meta or {},
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        try:
            # if_generation_match=0 ⇒ create-only (atomic).
            blob.upload_from_string(
                body,
                content_type="application/json",
                if_generation_match=0,
            )
            return ClaimResult(ok=True, status="claimed")
        except Exception as exc:
            name = type(exc).__name__
            msg = str(exc)
            # Precondition Failed / 412 ⇒ already exists.
            if (
                name in {"PreconditionFailed", "Conflict"}
                or "412" in msg
                or "conditionNotMet" in msg
                or getattr(exc, "code", None) == 412
            ):
                return ClaimResult(ok=False, status="already_spent", detail="approval already claimed")
            if isinstance(exc, getattr(gax, "GoogleAPICallError", Exception)):
                return ClaimResult(ok=False, status="store_unavailable", detail=msg)
            return ClaimResult(ok=False, status="store_unavailable", detail=f"{name}: {msg}")


def default_spend_store_from_env(env: Mapping[str, str] | None = None) -> SpendStore:
    import os

    e = env or os.environ
    bucket = (e.get("VELVET_DELIVERY_APPROVAL_SPEND_BUCKET") or "").strip()
    if not bucket:
        return UnavailableSpendStore()
    prefix = (e.get("VELVET_DELIVERY_APPROVAL_SPEND_PREFIX") or "spent/").strip() or "spent/"
    return GcsSpendStore(bucket, prefix=prefix)
