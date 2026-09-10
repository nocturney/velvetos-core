#!/usr/bin/env python3
"""Offline sensor for Gmail brief OAuth/CID production path. No network, no send."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from vfops import gmail_brief_send as sender  # noqa: E402


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    required = [
        ROOT / "packages" / "vfops" / "gmail_brief_send.py",
        ROOT / "packages" / "vfops" / "gmail_oauth_bootstrap.py",
        ROOT / "packages" / "vfops" / "gmail_brief_request.py",
        ROOT / ".github" / "workflows" / "gmail-brief-send.yml",
        ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    workflow = (ROOT / ".github" / "workflows" / "gmail-brief-send.yml").read_text(encoding="utf-8")
    for needle in ("GMAIL_OAUTH_JSON", "gmail_brief_request", "VFBRIEF_ALLOWED_RECIPIENT", "contents: read"):
        if needle not in workflow:
            fail(f"workflow missing {needle}")

    request = json.loads((ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json").read_text())
    if request.get("enabled") is not False:
        fail("bootstrap send request must be disabled on main")
    if request.get("to") != "nocturney@gmail.com":
        fail("send request owner recipient lock changed")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = sender._download_one

        def fake_download(url: str, dest: Path, *, max_bytes: int) -> Path:
            if not url.startswith("https://"):
                fail("embed test received non-https URL")
            out = dest.with_suffix(".png")
            out.write_bytes(b"\x89PNG\r\n\x1a\nCIDTEST")
            return out

        sender._download_one = fake_download
        try:
            html = '<table><tr><td><img src="https://example.com/a.png?x=1&amp;y=2" alt="A"></td></tr></table>'
            rewritten, images = sender.embed_remote_images(html, tmp_path, limit=3, max_bytes=4096)
        finally:
            sender._download_one = original

        if len(images) != 1 or images[0].name != "remote-01.png":
            fail(f"unexpected embedded images: {[p.name for p in images]}")
        if 'src="cid:remote-01.png"' not in rewritten:
            fail("remote image was not rewritten to cid")
        if "https://example.com/a.png" in rewritten:
            fail("remote image URL survived after CID rewrite")

        mime = sender.build_mime(
            html=rewritten,
            images=images,
            to="nocturney@gmail.com",
            subject="CID sensor",
        )
        blob = mime.as_string()
        if "multipart/related" not in blob:
            fail("MIME is not multipart/related")
        if "Content-ID: <remote-01.png>" not in blob:
            fail("downloaded image missing matching Content-ID")
        if "cid:remote-01.png" not in blob:
            fail("HTML CID reference missing from MIME")

    # Credential material must not be committed into the request template/workflow.
    for rel in (
        "packages/vfops/out/gmail-send-request.json",
        ".github/workflows/gmail-brief-send.yml",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "refresh_token\": \"1//" in text or "client_secret\": \"GOCSPX" in text:
            fail(f"credential-looking material committed in {rel}")

    print("OK Gmail brief sender: OAuth bootstrap + owner lock + remote-image CID rewrite")


if __name__ == "__main__":
    main()
