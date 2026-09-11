#!/usr/bin/env python3
"""Execute one repo-backed Gmail brief send request.

The request file is intentionally narrow and owner-locked. It lets ChatGPT/HQ
commit a rendered brief + send request, while GitHub Actions performs the actual
Gmail API send with a repository secret that never enters the repo or chat.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from vfops import gmail_brief_send

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REQUEST = ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json"
DEFAULT_ALLOWED_RECIPIENT = "nocturney@gmail.com"


def repo_path(raw: str, *, must_exist: bool = True) -> Path:
    path = (ROOT / raw).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"request path escapes repository: {raw}") from exc
    if must_exist and not path.exists():
        raise RuntimeError(f"request path does not exist: {raw}")
    return path


def load_request(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("send request must be a JSON object")
    return data


def encode_subject(subject: str) -> str:
    """Return an ASCII-safe RFC 2047 Subject."""
    return Header(subject, "utf-8").encode()


def build_safe_mime(*, html: str, images: list[Path], to: str, subject: str) -> MIMEMultipart:
    """Build RFC-safe multipart/related MIME with UTF-8 HTML and CID images."""
    msg = MIMEMultipart("related")
    msg["To"] = to
    msg["Subject"] = encode_subject(subject)
    msg.attach(MIMEText(html, "html", "utf-8"))
    for path in images:
        subtype = gmail_brief_send.IMAGE_SUFFIXES[path.suffix.lower()]
        part = MIMEImage(path.read_bytes(), _subtype=subtype)
        cid = path.name
        part.add_header("Content-ID", f"<{cid}>")
        part.add_header("Content-Disposition", "inline", filename=cid)
        part.set_param("name", cid)
        msg.attach(part)
    return msg


def validate_visible_text_gate(request: dict) -> tuple[Path, str]:
    """Bind an enabled send to the exact owner-visible text gated in this run."""
    visible_raw = str(request.get("visibleText") or "").strip()
    if not visible_raw:
        raise RuntimeError("enabled send request missing visibleText")
    visible_path = repo_path(visible_raw)
    text = visible_path.read_text(encoding="utf-8")
    actual_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    receipt_raw = (os.environ.get("VF_VISIBLE_TEXT_GATE_RECEIPT") or "").strip()
    if not receipt_raw:
        raise RuntimeError("missing VF_VISIBLE_TEXT_GATE_RECEIPT")
    receipt_path = Path(receipt_raw)
    if not receipt_path.is_file():
        raise RuntimeError("visible text gate receipt file is missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("visible_text_gate") != "PASS":
        raise RuntimeError("visible text gate is not PASS")
    if receipt.get("surface") != "owner-brief":
        raise RuntimeError("visible text gate surface is not owner-brief")
    if receipt.get("text_sha256") != actual_sha:
        raise RuntimeError("visible text changed after gate or receipt does not match")
    return visible_path, actual_sha


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one VelvetOS Gmail brief send request")
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

    html_path = repo_path(str(request.get("html") or ""))
    images_raw = str(request.get("images") or "").strip()
    if images_raw:
        images_dir = repo_path(images_raw)
        if not images_dir.is_dir():
            raise RuntimeError("send request images path must be a directory")
    else:
        images_dir = ROOT / "packages" / "vfops" / "out" / ".empty-images"
        images_dir.mkdir(parents=True, exist_ok=True)

    html = html_path.read_text(encoding="utf-8")
    images = gmail_brief_send.iter_images(images_dir)
    remote_limit = int(request.get("remoteImageLimit", gmail_brief_send.DEFAULT_REMOTE_IMAGE_LIMIT))

    print(
        f"SEND request={request.get('requestId', 'unknown')} to={to} "
        f"html={html_path.relative_to(ROOT)} visibleText={visible_path.relative_to(ROOT)} "
        f"text_sha256={text_sha}"
    )
    try:
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
            access_token = gmail_brief_send.mint_access_token()
            message_id = gmail_brief_send.send_raw_rfc822(access_token, mime.as_bytes())
    except Exception as exc:
        print(str(exc), file=os.sys.stderr)
        return 1

    print(message_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
