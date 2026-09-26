"""Publish fingerprint guard — refuse a repeated identical publish (#198).

Incident 2026-09-13: GRID-FOUNDATION-01 went out five extra times during a
retry/verification loop. Single-use approvals stop replaying ONE approval, but
nothing stopped a fresh approval for the SAME asset + caption. This guard does.

Fingerprint = sha256 over canonical JSON of:
  - ig_user_id (the account the write lands on)
  - media_sha256s (ordered digests from the SIGNED approval claims)
  - caption (NFC, trimmed, whitespace-collapsed; "" when the tool has none)

The mutation tool is deliberately NOT part of the fingerprint, so the same
asset + caption cannot be re-sent through a different publish tool either.

Order at the mutation boundary (``remote/delivery_approval_gate.py``):
  Phase A verify → **fingerprint check** → Phase B claim (spend) → ...
A repeat inside the window is refused BEFORE the approval is spent and before
any media fetch. The caption/digests used here are later bound by the existing
post-claim ``mutation_payload_sha256`` / media-byte checks, so lying about them
to dodge the fingerprint only gets the call blocked after claim (nothing is published).

The fingerprint is recorded after the Graph write returns anything other than
a definite failure (success, or ``write_outcome=unknown`` — an ambiguous
media_publish counts as "may be live" and must be reconciled with list_media).

Window: ``VELVET_PUBLISH_FINGERPRINT_WINDOW_SECONDS`` (default 72h). The only
override is operator deploy config (``0`` disables); there is no tool argument
an agent retry loop could set. Store: same GCS bucket as approval spend
(``VELVET_DELIVERY_APPROVAL_SPEND_BUCKET``), prefix ``publish-fingerprints/``;
unconfigured/unavailable ⇒ fail closed, exactly like the spend store.
Known limit: two concurrent calls with two different approvals can both pass
the check before either records (the incident was sequential retries).
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

PUBLISH_TOOLS: frozenset[str] = frozenset(
    {"publish_image", "publish_video", "publish_reel", "publish_carousel", "publish_story"}
)

DEFAULT_WINDOW_SECONDS = 72 * 60 * 60
DEFAULT_PREFIX = "publish-fingerprints/"
_WS = re.compile(r"\s+")


def normalize_caption(caption: Any) -> str:
    if caption is None:
        return ""
    if not isinstance(caption, str):
        raise TypeError("caption must be a string")
    return _WS.sub(" ", unicodedata.normalize("NFC", caption)).strip()


def _media_list(media_sha256s: Any) -> list[str]:
    if media_sha256s is None:
        return []
    if isinstance(media_sha256s, str):
        text = media_sha256s.strip()
        media_sha256s = json.loads(text) if text else []
    if not isinstance(media_sha256s, (list, tuple)):
        raise TypeError("media_sha256s must be a list or compact JSON array string")
    out = []
    for d in media_sha256s:
        if not isinstance(d, str) or not re.fullmatch(r"[0-9a-f]{64}", d):
            raise ValueError("media_sha256s entries must be lowercase sha256 hex")
        out.append(d)
    return out


def publish_fingerprint(*, ig_user_id: str | None, media_sha256s: Any, caption: Any) -> str:
    """Deterministic fingerprint for asset(s) + caption on one account."""
    media = _media_list(media_sha256s)
    if not media:
        raise ValueError("publish fingerprint requires at least one media digest")
    body = json.dumps(
        {
            "ig_user_id": (ig_user_id or "").strip(),
            "media_sha256s": media,
            "caption": normalize_caption(caption),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class FingerprintCheck:
    ok: bool
    status: str  # clear | repeat_within_window | disabled | store_unavailable | error
    detail: str = ""
    last_recorded_at: float | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"ok": self.ok, "status": self.status, "detail": self.detail}
        if self.last_recorded_at is not None:
            out["last_recorded_at"] = self.last_recorded_at
        return out


class FingerprintStore(Protocol):
    def recorded_times(self, fingerprint: str) -> Iterable[float]: ...

    def record(self, fingerprint: str, *, at: float, meta: Mapping[str, Any] | None = None) -> None: ...


class MemoryFingerprintStore:
    """Process-local store for tests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rows: dict[str, list[tuple[float, dict[str, Any]]]] = {}

    def recorded_times(self, fingerprint: str) -> list[float]:
        with self._lock:
            return [t for t, _ in self._rows.get(fingerprint, [])]

    def record(self, fingerprint: str, *, at: float, meta: Mapping[str, Any] | None = None) -> None:
        with self._lock:
            self._rows.setdefault(fingerprint, []).append((at, dict(meta or {})))


class UnavailableFingerprintStore:
    """Fail-closed stand-in when no bucket is configured."""

    def recorded_times(self, fingerprint: str) -> list[float]:
        raise RuntimeError("publish fingerprint store not configured; publish blocked")

    def record(self, fingerprint: str, *, at: float, meta: Mapping[str, Any] | None = None) -> None:
        raise RuntimeError("publish fingerprint store not configured")


class GcsFingerprintStore:
    """``<prefix><fingerprint>/<epoch_ms>.json`` objects, create-only (no overwrite/delete).

    Needs storage.objects.list + get + create on the bucket for the mutation SA.
    """

    def __init__(self, bucket_name: str, *, prefix: str = DEFAULT_PREFIX):
        if not bucket_name:
            raise ValueError("bucket_name required")
        self.bucket_name = bucket_name
        self.prefix = prefix if prefix.endswith("/") else prefix + "/"

    def _bucket(self):
        from google.cloud import storage  # type: ignore

        return storage.Client().bucket(self.bucket_name)

    def recorded_times(self, fingerprint: str) -> list[float]:
        bucket = self._bucket()
        out: list[float] = []
        for blob in bucket.client.list_blobs(bucket, prefix=f"{self.prefix}{fingerprint}/"):
            stem = blob.name.rsplit("/", 1)[-1].split(".", 1)[0]
            if stem.isdigit():
                out.append(int(stem) / 1000.0)
        return out

    def record(self, fingerprint: str, *, at: float, meta: Mapping[str, Any] | None = None) -> None:
        blob = self._bucket().blob(f"{self.prefix}{fingerprint}/{int(at * 1000)}.json")
        body = json.dumps(
            {"fingerprint": fingerprint, "recorded_at": at, "meta": dict(meta or {})},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        blob.upload_from_string(body, content_type="application/json", if_generation_match=0)


def window_seconds_from_env(env: Mapping[str, str] | None = None) -> int:
    import os

    e = env if env is not None else os.environ
    raw = (e.get("VELVET_PUBLISH_FINGERPRINT_WINDOW_SECONDS") or "").strip()
    if not raw:
        return DEFAULT_WINDOW_SECONDS
    value = int(raw)
    if value < 0:
        raise ValueError("VELVET_PUBLISH_FINGERPRINT_WINDOW_SECONDS must be >= 0")
    return value


def default_fingerprint_store_from_env(env: Mapping[str, str] | None = None) -> FingerprintStore:
    import os

    e = env if env is not None else os.environ
    bucket = (e.get("VELVET_DELIVERY_APPROVAL_SPEND_BUCKET") or "").strip()
    if not bucket:
        return UnavailableFingerprintStore()
    prefix = (e.get("VELVET_PUBLISH_FINGERPRINT_PREFIX") or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX
    return GcsFingerprintStore(bucket, prefix=prefix)


def check_fingerprint(
    fingerprint: str,
    *,
    store: FingerprintStore,
    window_seconds: int,
    now: float | None = None,
) -> FingerprintCheck:
    """Refuse when the same fingerprint was recorded within ``window_seconds``."""
    if window_seconds == 0:
        return FingerprintCheck(ok=True, status="disabled", detail="window disabled by operator config")
    t = time.time() if now is None else now
    try:
        times = [float(x) for x in store.recorded_times(fingerprint)]
    except Exception as exc:  # fail closed
        return FingerprintCheck(ok=False, status="store_unavailable", detail=f"{type(exc).__name__}: {exc}")
    recent = [x for x in times if t - window_seconds <= x <= t + 60]
    if recent:
        last = max(recent)
        return FingerprintCheck(
            ok=False,
            status="repeat_within_window",
            detail=(
                f"identical asset+caption already published {int(t - last)}s ago "
                f"(window {window_seconds}s); reconcile with list_media instead of re-publishing"
            ),
            last_recorded_at=last,
        )
    return FingerprintCheck(ok=True, status="clear")


def is_definite_failure(result: Any) -> bool:
    """True only when the Graph write certainly did not create a post."""
    if not isinstance(result, Mapping):
        return False
    if result.get("blocked"):
        return True
    if result.get("ok") is False:
        return result.get("write_outcome") != "unknown"
    return False
