"""Immutable media-byte digests for delivery-approval binding.

Instagram Graph publish tools pass PUBLIC https URLs (Meta fetches bytes).
URL/path/filename alone are NOT identity. VelvetOS therefore requires:

1. Content-addressed media URLs embedding ``/sha256/<64-hex>/``
2. Issuer + mutation runtime hash the exact response body (or trusted
   artifact bytes) and bind ``media_sha256s`` to those digests
3. Caller-supplied media digests are never trusted

Non-media mutations (delete/comment) do not carry media digests.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping, Sequence

from .schema import SHA256_RE

MEDIA_BEARING_TOOLS: frozenset[str] = frozenset(
    {
        "publish_image",
        "publish_video",
        "publish_reel",
        "publish_carousel",
        "publish_story",
    }
)

# Path segment that makes a public URL content-addressed / immutable by digest.
_CAS_PATH_RE = re.compile(r"/sha256/([0-9a-f]{64})(?:/|$)", re.IGNORECASE)

# Hard cap when fetching media for digest verification (issue + mutation).
DEFAULT_MEDIA_FETCH_MAX_BYTES = 52_428_800  # 50 MiB

MediaByteFetcher = Callable[[str], bytes]

# Test/injection override (None = use HTTPS fetch).
_FETCHER_OVERRIDE: MediaByteFetcher | None = None


def set_media_byte_fetcher_override(fetcher: MediaByteFetcher | None) -> None:
    """Sensor/tests only — inject URL→bytes without network."""
    global _FETCHER_OVERRIDE
    _FETCHER_OVERRIDE = fetcher


def sha256_hex(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("media bytes must be bytes")
    digest = hashlib.sha256(bytes(data)).hexdigest()
    if not re.fullmatch(SHA256_RE, digest):
        raise RuntimeError("internal digest error")
    return digest


def cas_digest_from_url(url: str) -> str | None:
    """Return embedded sha256 if URL is content-addressed, else None."""
    if not isinstance(url, str) or not url.strip():
        return None
    match = _CAS_PATH_RE.search(url.strip())
    if not match:
        return None
    return match.group(1).lower()


def require_cas_url(url: str) -> str:
    digest = cas_digest_from_url(url)
    if digest is None:
        raise ValueError(
            "media URL must be content-addressed (/sha256/<64-hex>/); "
            "mutable URL/path/filename is not byte identity"
        )
    return digest


def encode_media_sha256s_claim(digests: Sequence[str]) -> str:
    """Flat claim encoding (claims are strings only): compact JSON array."""
    out: list[str] = []
    for d in digests:
        text = str(d).strip().lower()
        if not re.fullmatch(SHA256_RE, text):
            raise ValueError(f"invalid media digest: {d!r}")
        out.append(text)
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


def decode_media_sha256s_claim(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("media_sha256s claim must be a JSON array")
    out: list[str] = []
    for item in data:
        if not isinstance(item, str) or not re.fullmatch(SHA256_RE, item.strip().lower()):
            raise ValueError("media_sha256s entries must be 64-hex digests")
        out.append(item.strip().lower())
    return out


def media_urls_for_tool(mutation_tool: str, params: Mapping[str, Any] | None) -> list[str]:
    """Ordered public media URLs actually referenced by the write tool."""
    tool = (mutation_tool or "").strip()
    src = dict(params or {})
    if tool not in MEDIA_BEARING_TOOLS:
        return []
    if tool == "publish_image":
        url = src.get("image_url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("publish_image requires image_url")
        return [url.strip()]
    if tool in ("publish_video", "publish_reel"):
        urls: list[str] = []
        video = src.get("video_url")
        if not isinstance(video, str) or not video.strip():
            raise ValueError(f"{tool} requires video_url")
        urls.append(video.strip())
        cover = src.get("cover_url")
        if isinstance(cover, str) and cover.strip():
            urls.append(cover.strip())
        return urls
    if tool == "publish_carousel":
        items = src.get("image_urls")
        if not isinstance(items, list) or not items:
            raise ValueError("publish_carousel requires image_urls")
        out: list[str] = []
        for item in items:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("publish_carousel image_urls must be strings")
            out.append(item.strip())
        return out
    if tool == "publish_story":
        image = src.get("image_url")
        video = src.get("video_url")
        has_image = isinstance(image, str) and bool(image.strip())
        has_video = isinstance(video, str) and bool(video.strip())
        if has_image == has_video:
            raise ValueError("publish_story requires exactly one of image_url or video_url")
        return [image.strip() if has_image else str(video).strip()]
    raise KeyError(f"unsupported media tool: {tool}")


def strip_untrusted_media_digest_fields(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Remove caller-supplied media digest fields before issuer recomputation."""
    out = dict(params or {})
    for key in ("media_sha256", "media_sha256s", "media_digest", "media_digests"):
        out.pop(key, None)
    return out


def _https_fetch(url: str, *, max_bytes: int) -> bytes:
    if not url.lower().startswith("https://"):
        raise ValueError("media fetch requires https URL")
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "velvet-delivery-approval-media-bytes/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — https only
            chunks: list[bytes] = []
            total = 0
            while True:
                block = resp.read(65536)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise ValueError("media body exceeds fetch size cap")
                chunks.append(block)
            return b"".join(chunks)
    except urllib.error.URLError as exc:
        raise ValueError(f"media fetch failed: {exc}") from exc


def fetch_media_bytes(
    url: str,
    *,
    fetcher: MediaByteFetcher | None = None,
    max_bytes: int = DEFAULT_MEDIA_FETCH_MAX_BYTES,
) -> bytes:
    active = fetcher if fetcher is not None else _FETCHER_OVERRIDE
    if active is not None:
        data = active(url)
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("media fetcher must return bytes")
        if len(data) > max_bytes:
            raise ValueError("media body exceeds fetch size cap")
        return bytes(data)
    return _https_fetch(url, max_bytes=max_bytes)


def digests_from_artifact_bytes(
    artifacts: Sequence[Mapping[str, Any]] | None,
) -> list[bytes] | None:
    """Decode optional issuer ``media_artifacts`` (trusted bytes, not digests).

    Each item: ``{"bytes_b64": "..."}`` — sha256 is computed by the issuer.
    """
    if artifacts is None:
        return None
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes)):
        raise ValueError("media_artifacts must be a list")
    out: list[bytes] = []
    for idx, item in enumerate(artifacts):
        if not isinstance(item, Mapping):
            raise ValueError(f"media_artifacts[{idx}] must be an object")
        # Refuse caller-supplied digests as authority.
        for banned in ("sha256", "media_sha256", "digest"):
            if banned in item and item.get("bytes_b64") is None:
                raise ValueError(
                    "media_artifacts must provide bytes_b64; "
                    "caller-supplied digests are not trusted"
                )
        b64 = item.get("bytes_b64")
        if not isinstance(b64, str) or not b64.strip():
            raise ValueError(f"media_artifacts[{idx}].bytes_b64 required")
        pad = "=" * (-len(b64.strip()) % 4)
        try:
            raw = base64.urlsafe_b64decode(b64.strip() + pad)
        except Exception:
            try:
                raw = base64.b64decode(b64.strip() + pad)
            except Exception as exc:
                raise ValueError(f"media_artifacts[{idx}] invalid base64") from exc
        if not raw:
            raise ValueError(f"media_artifacts[{idx}] empty bytes")
        out.append(raw)
    return out


def resolve_media_sha256s(
    mutation_tool: str,
    params: Mapping[str, Any] | None,
    *,
    artifact_bytes: Sequence[bytes] | None = None,
    fetcher: MediaByteFetcher | None = None,
    max_bytes: int = DEFAULT_MEDIA_FETCH_MAX_BYTES,
) -> list[str]:
    """Compute ordered media digests from trusted bytes (artifacts or fetch).

    For each URL:
    - URL must embed ``/sha256/<digest>/`` (content-addressed)
    - Exact body bytes are hashed
    - Body digest must equal the embedded CAS digest
    """
    tool = (mutation_tool or "").strip()
    if tool not in MEDIA_BEARING_TOOLS:
        return []
    urls = media_urls_for_tool(tool, params)
    if artifact_bytes is not None and len(artifact_bytes) != len(urls):
        raise ValueError(
            f"media_artifacts length {len(artifact_bytes)} != media URL count {len(urls)}"
        )
    digests: list[str] = []
    for idx, url in enumerate(urls):
        embedded = require_cas_url(url)
        if artifact_bytes is not None:
            body = artifact_bytes[idx]
            if len(body) > max_bytes:
                raise ValueError("media body exceeds fetch size cap")
        else:
            body = fetch_media_bytes(url, fetcher=fetcher, max_bytes=max_bytes)
        digest = sha256_hex(body)
        if digest != embedded:
            raise ValueError(
                "media bytes do not match content-addressed URL digest "
                f"(url declares {embedded}, body is {digest})"
            )
        digests.append(digest)
    return digests


def inject_media_sha256s(
    mutation_tool: str,
    params: Mapping[str, Any] | None,
    digests: Sequence[str],
) -> dict[str, Any]:
    """Return params copy with authoritative media_sha256s for payload digesting."""
    out = strip_untrusted_media_digest_fields(params)
    tool = (mutation_tool or "").strip()
    if tool in MEDIA_BEARING_TOOLS:
        out["media_sha256s"] = [str(d).strip().lower() for d in digests]
    else:
        out.pop("media_sha256s", None)
    return out
