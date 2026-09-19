#!/usr/bin/env python3
"""Send one gated Velvet Factory brief through the owner-operated Apps Script bridge.

The runner still builds the exact final RFC822/MIME message, including CID images.
Apps Script only verifies the signed request, mints the owner's Google token, calls
Gmail users.messages.send, and returns the real Gmail message id.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from vfops import gmail_brief_send
from vfops.gmail_brief_request import (
    DEFAULT_ALLOWED_RECIPIENT,
    DEFAULT_REQUEST,
    build_safe_mime,
    load_request,
    repo_path,
    validate_visible_text_gate,
)


def _required_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def _signature(secret: str, *, request_id: str, issued_at: int, to: str, raw: str) -> str:
    raw_sha = hashlib.sha256(raw.encode("ascii")).hexdigest()
    canonical = f"{request_id}\n{issued_at}\n{to}\n{raw_sha}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def send_via_apps_script(*, endpoint: str, secret: str, request_id: str, to: str, raw: str) -> dict:
    if not endpoint.startswith("https://script.google.com/"):
        raise RuntimeError("Apps Script endpoint must be an https://script.google.com/ URL")
    issued_at = int(time.time())
    payload = {
        "requestId": request_id,
        "issuedAt": issued_at,
        "to": to,
        "raw": raw,
        "signature": _signature(
            secret,
            request_id=request_id,
            issued_at=issued_at,
            to=to,
            raw=raw,
        ),
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Apps Script bridge HTTP {exc.code}: {detail[:1000]}") from exc
    if status < 200 or status >= 300:
        raise RuntimeError(f"Apps Script bridge HTTP {status}")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Apps Script bridge returned non-JSON") from exc
    if data.get("ok") is not True:
        raise RuntimeError(f"Apps Script bridge rejected send: {data}")
    message_id = str(data.get("messageId") or "").strip()
    if not message_id:
        raise RuntimeError("Apps Script bridge returned no Gmail message id")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    args = parser.parse_args()

    request = load_request(args.request)
    if request.get("enabled") is not True:
        print("SKIP gmail brief request disabled")
        return 0

    visible_path, text_sha = validate_visible_text_gate(request)

    allowed = (os.environ.get("VFBRIEF_ALLOWED_RECIPIENT") or DEFAULT_ALLOWED_RECIPIENT).strip().lower()
    to = str(request.get("to") or "").strip().lower()
    if to != allowed:
        raise RuntimeError(f"recipient is not owner-allowed: {to!r}")

    subject = str(request.get("subject") or "").strip()
    if not subject:
        raise RuntimeError("send request missing subject")
    request_id = str(request.get("requestId") or "").strip()
    if not request_id:
        raise RuntimeError("send request missing requestId")

    html_path = repo_path(str(request.get("html") or ""))
    images_raw = str(request.get("images") or "").strip()
    if images_raw:
        images_dir = repo_path(images_raw)
        if not images_dir.is_dir():
            raise RuntimeError("send request images path must be a directory")
    else:
        images_dir = repo_path("packages/vfops/out", must_exist=True) / ".empty-images"
        images_dir.mkdir(parents=True, exist_ok=True)

    html = html_path.read_text(encoding="utf-8")
    images = gmail_brief_send.iter_images(images_dir)
    remote_limit = int(request.get("remoteImageLimit", gmail_brief_send.DEFAULT_REMOTE_IMAGE_LIMIT))

    endpoint = _required_env("GMAIL_APPS_SCRIPT_URL")
    secret = _required_env("GMAIL_APPS_SCRIPT_SECRET")

    print(
        f"SEND request={request_id} to={to} html={html_path.relative_to(repo_path('.'))} "
        f"visibleText={visible_path.relative_to(repo_path('.'))} text_sha256={text_sha}"
    )

    with tempfile.TemporaryDirectory(prefix="vfbrief-cid-") as tmp:
        if request.get("embedRemoteImages", True):
            html, remote_images = gmail_brief_send.embed_remote_images(
                html,
                Path(tmp),
                limit=remote_limit,
                max_bytes=gmail_brief_send.DEFAULT_REMOTE_IMAGE_MAX_BYTES,
            )
            images.extend(remote_images)
        mime = build_safe_mime(html=html, images=images, to=to, subject=subject)
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii").rstrip("=")

    result = send_via_apps_script(
        endpoint=endpoint,
        secret=secret,
        request_id=request_id,
        to=to,
        raw=raw,
    )
    print("GMAIL_MESSAGE_ID=" + result["messageId"])
    if result.get("threadId"):
        print("GMAIL_THREAD_ID=" + str(result["threadId"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
