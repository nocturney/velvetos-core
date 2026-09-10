#!/usr/bin/env python3
"""Execute one repo-backed Gmail brief send request.

The request file is intentionally narrow and owner-locked. It lets ChatGPT/HQ
commit a rendered brief + send request, while GitHub Actions performs the actual
Gmail API send with a repository secret that never enters the repo or chat.
"""
from __future__ import annotations

import argparse
import json
import os
from email.header import Header
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
    """Return an ASCII-safe RFC 2047 Subject for the legacy MIME builder."""
    return Header(subject, "utf-8").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one VelvetOS Gmail brief send request")
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    args = parser.parse_args()

    request = load_request(args.request)
    if request.get("enabled") is not True:
        print("SKIP gmail brief request disabled")
        return 0

    allowed = (os.environ.get("VFBRIEF_ALLOWED_RECIPIENT") or DEFAULT_ALLOWED_RECIPIENT).strip().lower()
    to = str(request.get("to") or "").strip().lower()
    if to != allowed:
        raise RuntimeError(f"recipient is not owner-allowed: {to!r}")

    subject = str(request.get("subject") or "").strip()
    if not subject:
        raise RuntimeError("send request missing subject")
    encoded_subject = encode_subject(subject)

    html = repo_path(str(request.get("html") or ""))
    images_raw = str(request.get("images") or "").strip()
    if images_raw:
        images = repo_path(images_raw)
        if not images.is_dir():
            raise RuntimeError("send request images path must be a directory")
    else:
        images = ROOT / "packages" / "vfops" / "out" / ".empty-images"
        images.mkdir(parents=True, exist_ok=True)

    argv = [
        "--html",
        str(html),
        "--images",
        str(images),
        "--to",
        to,
        "--subject",
        encoded_subject,
    ]
    if request.get("embedRemoteImages", True):
        argv.append("--embed-remote-images")
    if request.get("remoteImageLimit") is not None:
        argv.extend(["--remote-image-limit", str(int(request["remoteImageLimit"]))])

    print(f"SEND request={request.get('requestId', 'unknown')} to={to} html={html.relative_to(ROOT)}")
    return gmail_brief_send.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
