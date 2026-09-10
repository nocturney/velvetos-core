#!/usr/bin/env python3
"""Offline sensor for Gmail brief OAuth/CID production path. No network, no send."""
from __future__ import annotations

import json
import sys
import tempfile
from email import message_from_bytes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from vfops import gmail_brief_send as sender  # noqa: E402
from vfops.gmail_brief_request import build_safe_mime, encode_subject  # noqa: E402


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

    utf8_subject = "Velvet Factory — בריף הבוקר · בדיקה"
    encoded_subject = encode_subject(utf8_subject)
    try:
        encoded_subject.encode("ascii")
    except UnicodeEncodeError:
        fail("UTF-8 subject was not converted to ASCII-safe RFC 2047")
    if "=?utf-8?" not in encoded_subject.lower():
        fail("UTF-8 subject is missing RFC 2047 encoding")

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
            html = '<html dir="rtl"><body>בדיקת · CID — עברית<img src="https://example.com/a.png?x=1&amp;y=2" alt="A"></body></html>'
            rewritten, images = sender.embed_remote_images(html, tmp_path, limit=3, max_bytes=4096)
        finally:
            sender._download_one = original

        if len(images) != 1 or images[0].name != "remote-01.png":
            fail(f"unexpected embedded images: {[p.name for p in images]}")
        if 'src="cid:remote-01.png"' not in rewritten:
            fail("remote image was not rewritten to cid")

        mime = build_safe_mime(
            html=rewritten,
            images=images,
            to="nocturney@gmail.com",
            subject=utf8_subject,
        )
        try:
            blob_bytes = mime.as_bytes()
        except UnicodeEncodeError as exc:
            fail(f"UTF-8 MIME serialization failed: {exc}")

        parsed = message_from_bytes(blob_bytes)
        if parsed.get_content_type() != "multipart/related":
            fail("MIME is not multipart/related")
        parts = list(parsed.walk())
        html_parts = [p for p in parts if p.get_content_type() == "text/html"]
        if len(html_parts) != 1:
            fail("expected exactly one HTML MIME part")
        decoded_html = html_parts[0].get_payload(decode=True).decode("utf-8")
        if "בדיקת · CID — עברית" not in decoded_html:
            fail("UTF-8 HTML did not round-trip through MIME")
        if 'src="cid:remote-01.png"' not in decoded_html:
            fail("HTML CID reference missing after MIME decoding")
        if not any(p.get("Content-ID") == "<remote-01.png>" for p in parts):
            fail("downloaded image missing matching Content-ID")

    for rel in (
        "packages/vfops/out/gmail-send-request.json",
        ".github/workflows/gmail-brief-send.yml",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "refresh_token\": \"1//" in text or "client_secret\": \"GOCSPX" in text:
            fail(f"credential-looking material committed in {rel}")

    print("OK Gmail brief sender: OAuth bootstrap + owner lock + UTF-8 MIME + remote-image CID rewrite")


if __name__ == "__main__":
    main()
