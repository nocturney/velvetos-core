#!/usr/bin/env python3
"""Canonical routine Instagram scheduler for Reform v2 Stage 4D.

Flow:
CONTENT_READY exact evidence -> Cloudflare Publisher media upload -> one
policy_id: instagram.publish decision -> persisted scheduled job -> readback.

This is the standing-authorized routine path. It never mints or bypasses the
signed velvet.delivery_approval.v1 receipt used by direct/immediate MCP
mutations. The Worker derives standing authorization from its own runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from vf_content_ready import canonical_digest, validate_envelope  # noqa: E402
from vfigos.cloudflare_publisher_snapshot import DEFAULT_URL, resolve_token  # noqa: E402

ALLOWED_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".mp4": "video/mp4",
}
KINDS = {"image", "carousel", "reel", "story"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def content_type(path: Path) -> str:
    mime = ALLOWED_MIME.get(path.suffix.lower())
    if not mime:
        guessed, _ = mimetypes.guess_type(path.name)
        mime = guessed or ""
    if mime not in {"image/jpeg", "image/png", "video/mp4"}:
        raise ValueError(f"unsupported media type for {path}: {mime or 'unknown'}")
    return mime


def validate_kind_media(kind: str, media_rows: list[dict[str, Any]]) -> None:
    if kind not in KINDS:
        raise ValueError(f"unsupported kind {kind!r}")
    if not media_rows:
        raise ValueError("at least one media file is required")
    if kind in {"image", "reel", "story"} and len(media_rows) != 1:
        raise ValueError(f"{kind} requires exactly one media file")
    if kind == "carousel" and not 2 <= len(media_rows) <= 10:
        raise ValueError("carousel requires 2-10 media files")
    mimes = [row["content_type"] for row in media_rows]
    if kind in {"image", "carousel"} and any(m not in {"image/jpeg", "image/png"} for m in mimes):
        raise ValueError(f"{kind} accepts image/jpeg or image/png only")
    if kind == "reel" and mimes != ["video/mp4"]:
        raise ValueError("reel requires one video/mp4")
    if kind == "story" and mimes[0] not in {"image/jpeg", "image/png", "video/mp4"}:
        raise ValueError("story requires one image or MP4 video")


def media_rows(paths: list[Path], content_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256_file(path)
        mime = content_type(path)
        ext = ".jpg" if mime == "image/jpeg" else ".png" if mime == "image/png" else ".mp4"
        key = f"{content_id}-{index:02d}-{digest[:20]}{ext}"
        rows.append(
            {
                "path": path,
                "key": key,
                "sha256": digest,
                "content_type": mime,
                "bytes": path.stat().st_size,
            }
        )
    return rows


def parse_schedule(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--scheduled-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("--scheduled-at must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def build_job_payload(
    *,
    envelope: dict[str, Any],
    caption: str,
    media: list[dict[str, Any]],
    kind: str,
    scheduled_at: datetime,
    job_id: str | None = None,
) -> dict[str, Any]:
    validate_kind_media(kind, media)
    bindings = envelope.get("bindings") or {}
    content_id = str(bindings.get("content_id") or "")
    caption_digest = sha256_bytes(caption.encode("utf-8"))
    observed_media = [row["sha256"] for row in media]

    if bindings.get("copy_sha256") != caption_digest:
        raise ValueError("CONTENT_READY copy_sha256 does not match exact caption UTF-8 bytes")
    if bindings.get("media_sha256s") != observed_media:
        raise ValueError("CONTENT_READY media_sha256s do not match exact ordered media bytes")

    payload: dict[str, Any] = {
        "content_id": content_id,
        "package_sha256": bindings.get("package_sha256"),
        "kind": kind,
        "scheduled_at": scheduled_at.isoformat().replace("+00:00", "Z"),
        "caption": caption,
        "media": [{"key": row["key"], "sha256": row["sha256"]} for row in media],
        "authorization": {
            "kind": "policy_authorization_v1",
            "evidence": "CONTENT_READY:" + canonical_digest(envelope),
            "policy_context": {
                "risk_class": "LOW",
                "forbidden_effects": [],
                "content_ready": envelope,
                "human_approval": None,
            },
        },
    }
    if job_id:
        payload["id"] = job_id
    return payload


def request_json(
    *,
    method: str,
    base_url: str,
    path: str,
    token: str,
    body: dict[str, Any] | None = None,
    raw: bytes | None = None,
    mime: str | None = None,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    data = raw
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "VelvetOS-Routine-Instagram/4D",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        headers["Content-Type"] = mime or "application/octet-stream"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        raw_error = exc.read().decode("utf-8", errors="replace")
        try:
            detail: Any = json.loads(raw_error)
        except json.JSONDecodeError:
            detail = raw_error[:1000]
        raise RuntimeError(f"publisher HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"publisher unavailable: {exc}") from exc


def upload_media(base_url: str, token: str, row: dict[str, Any]) -> dict[str, Any]:
    raw = row["path"].read_bytes()
    query = urllib.parse.urlencode({"sha256": row["sha256"]})
    result = request_json(
        method="PUT",
        base_url=base_url,
        path=f"/v1/media/{urllib.parse.quote(row['key'])}?{query}",
        token=token,
        raw=raw,
        mime=row["content_type"],
    )
    if result.get("ok") is not True or result.get("sha256") != row["sha256"]:
        raise RuntimeError(f"media upload verification failed for {row['key']}: {result}")
    return result


def verify_readback(
    *,
    base_url: str,
    token: str,
    job_id: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    result = request_json(
        method="GET",
        base_url=base_url,
        path="/v1/jobs/" + urllib.parse.quote(job_id),
        token=token,
    )
    job = result.get("job") or {}
    problems: list[str] = []
    for key in ("content_id", "package_sha256", "kind", "caption"):
        if job.get(key) != expected.get(key):
            problems.append(f"{key} mismatch")
    expected_media = [(x["key"], x["sha256"]) for x in expected["media"]]
    actual_media = [(x.get("key"), x.get("sha256")) for x in (job.get("media") or [])]
    if actual_media != expected_media:
        problems.append("media order/digest mismatch")
    if job.get("status") not in {"scheduled", "publishing", "published_verified"}:
        problems.append(f"unexpected status {job.get('status')!r}")
    if problems:
        raise RuntimeError("publisher readback mismatch: " + "; ".join(problems))
    return job


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="vf-routine-publish-") as tmp:
        root = Path(tmp)
        image = root / "a.jpg"
        image2 = root / "b.png"
        video = root / "c.mp4"
        image.write_bytes(b"image-a")
        image2.write_bytes(b"image-b")
        video.write_bytes(b"video-c")
        caption = "Velvet Factory"
        rows_image = media_rows([image], "G100")
        rows_carousel = media_rows([image, image2], "G100")
        rows_video = media_rows([video], "G100")

        def envelope_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
            ev = {
                key: {
                    "status": "PASS",
                    "ref": f"fixture/{key}.json",
                    "sha256": str(i) * 64,
                    "failure_mode": None,
                    "reason": None,
                }
                for i, key in enumerate(
                    ["product_truth", "brand", "copy", "visual_qa", "rights_privacy", "render_transport"],
                    start=1,
                )
            }
            return {
                "schema_version": "velvet.content_ready.v1",
                "status": "PASS",
                "bindings": {
                    "content_id": "G100",
                    "package_sha256": "a" * 64,
                    "copy_sha256": sha256_bytes(caption.encode("utf-8")),
                    "media_sha256s": [row["sha256"] for row in rows],
                },
                "evidence": ev,
                "repair_targets": [],
                "retry_targets": [],
                "hard_blockers": [],
                "owner_surface": "NONE",
                "validated_at": "2030-01-01T10:00:00Z",
            }

        when = datetime(2030, 1, 1, 11, 0, tzinfo=timezone.utc)
        for kind, rows in (
            ("image", rows_image),
            ("carousel", rows_carousel),
            ("reel", rows_video),
            ("story", rows_image),
            ("story", rows_video),
        ):
            payload = build_job_payload(
                envelope=envelope_for(rows),
                caption=caption,
                media=rows,
                kind=kind,
                scheduled_at=when,
            )
            assert payload["authorization"]["policy_context"]["risk_class"] == "LOW"
            assert payload["authorization"]["policy_context"]["human_approval"] is None
            assert payload["authorization"]["policy_context"]["content_ready"]["status"] == "PASS"

        try:
            build_job_payload(
                envelope=envelope_for(rows_image),
                caption=caption,
                media=rows_image,
                kind="reel",
                scheduled_at=when,
            )
        except ValueError as exc:
            assert "video/mp4" in str(exc)
        else:
            raise AssertionError("reel accepted image media")

    print("OK routine-instagram happy-path formats=image,carousel,reel,story owner_prompt=0 direct_mcp_receipt=unchanged")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-ready", type=Path)
    parser.add_argument("--caption-file", type=Path)
    parser.add_argument("--media", type=Path, action="append", default=[])
    parser.add_argument("--kind", choices=sorted(KINDS))
    parser.add_argument("--scheduled-at")
    parser.add_argument("--job-id")
    parser.add_argument("--base-url", default=DEFAULT_URL)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    missing = [
        name
        for name, value in (
            ("--content-ready", args.content_ready),
            ("--caption-file", args.caption_file),
            ("--kind", args.kind),
            ("--scheduled-at", args.scheduled_at),
        )
        if not value
    ]
    if missing or not args.media:
        parser.error("missing required arguments: " + ", ".join(missing + ([] if args.media else ["--media"])))

    envelope = json.loads(args.content_ready.read_text(encoding="utf-8"))
    caption = args.caption_file.read_text(encoding="utf-8")
    rows = media_rows(args.media, str((envelope.get("bindings") or {}).get("content_id") or ""))
    when = parse_schedule(args.scheduled_at)

    expected_bindings = {
        "content_id": (envelope.get("bindings") or {}).get("content_id"),
        "package_sha256": (envelope.get("bindings") or {}).get("package_sha256"),
        "copy_sha256": sha256_bytes(caption.encode("utf-8")),
        "media_sha256s": [row["sha256"] for row in rows],
    }
    validation = validate_envelope(envelope, expected_bindings=expected_bindings, root=ROOT, verify_refs=True)
    if validation["content_ready"] != "PASS":
        print(json.dumps({"ok": False, "stage": "content_ready", "validation": validation}, ensure_ascii=False, indent=2))
        return 2

    payload = build_job_payload(
        envelope=envelope,
        caption=caption,
        media=rows,
        kind=args.kind,
        scheduled_at=when,
        job_id=args.job_id,
    )
    if args.prepare_only:
        print(json.dumps({"ok": True, "mode": "prepare-only", "job": payload}, ensure_ascii=False, indent=2))
        return 0

    token = resolve_token()
    uploaded = [upload_media(args.base_url, token, row) for row in rows]
    created = request_json(
        method="POST",
        base_url=args.base_url,
        path="/v1/jobs",
        token=token,
        body=payload,
    )
    policy = created.get("policy") or {}
    if created.get("ok") is not True or policy.get("decision") != "ALLOW":
        raise RuntimeError(f"publisher did not return ALLOW: {created}")
    if "STANDING_AUTHORIZATION" not in (policy.get("reason_codes") or []):
        raise RuntimeError(f"routine happy path did not use standing authorization: {policy}")

    job_id = str(created.get("id") or "")
    if not job_id:
        raise RuntimeError("publisher returned no job id")
    readback = verify_readback(base_url=args.base_url, token=token, job_id=job_id, expected=payload)
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "routine-standing-authorized",
                "content_ready": "PASS",
                "owner_prompt": False,
                "policy_id": policy.get("policy_id"),
                "policy_decision": policy.get("decision"),
                "policy_reason_codes": policy.get("reason_codes"),
                "job_id": job_id,
                "job_status": readback.get("status"),
                "scheduled_at": readback.get("scheduled_at"),
                "uploaded_media": [
                    {"key": row["key"], "sha256": row["sha256"], "idempotent": up.get("idempotent")}
                    for row, up in zip(rows, uploaded)
                ],
                "closure_requirement": "published_verified requires provider receipt + live readback; scheduled is not live proof",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
