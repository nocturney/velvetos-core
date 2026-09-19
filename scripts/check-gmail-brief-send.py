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
from vfops import gmail_apps_script_request as bridge  # noqa: E402
from vfops.gmail_brief_request import build_safe_mime, encode_subject  # noqa: E402


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    required = [
        ROOT / "packages" / "vfops" / "gmail_brief_send.py",
        ROOT / "packages" / "vfops" / "gmail_oauth_bootstrap.py",
        ROOT / "packages" / "vfops" / "gmail_brief_request.py",
        ROOT / "packages" / "vfops" / "gmail_apps_script_request.py",
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "Code.gs",
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "appsscript.json",
        ROOT / ".github" / "workflows" / "gmail-brief-send.yml",
        ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    workflow = (ROOT / ".github" / "workflows" / "gmail-brief-send.yml").read_text(encoding="utf-8")
    for needle in (
        "GMAIL_APPS_SCRIPT_URL",
        "GMAIL_APPS_SCRIPT_SECRET",
        "gmail_apps_script_request",
        "VFBRIEF_ALLOWED_RECIPIENT",
        "contents: read",
    ):
        if needle not in workflow:
            fail(f"workflow missing {needle}")
    if "GMAIL_OAUTH_JSON" in workflow:
        fail("workflow still references retired GMAIL_OAUTH_JSON transport")

    request = json.loads((ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json").read_text())
    if request.get("enabled") is not False:
        fail("bootstrap send request must be disabled on main")
    if request.get("to") != "nocturney@gmail.com":
        fail("send request owner recipient lock changed")

    original_refresh = sender._refresh_authorized_user

    def synthetic_refresh_failure(data: dict) -> str:
        raise RuntimeError("synthetic refresh failure")

    sender._refresh_authorized_user = synthetic_refresh_failure
    try:
        try:
            sender._token_from_mapping(
                {
                    "type": "authorized_user",
                    "client_id": "client",
                    "client_secret": "secret",
                    "refresh_token": "refresh",
                    "token": "stale-access-token",
                }
            )
        except RuntimeError as exc:
            if "synthetic refresh failure" not in str(exc):
                fail(f"unexpected OAuth refresh failure: {exc}")
        else:
            fail("authorized_user refresh failure fell back to stale access token")
    finally:
        sender._refresh_authorized_user = original_refresh

    raw = "ZmFrZS1yZmM4MjI"
    sig1 = bridge._signature(
        "test-secret",
        request_id="req-1",
        issued_at=1234567890,
        to="nocturney@gmail.com",
        raw=raw,
    )
    sig2 = bridge._signature(
        "test-secret",
        request_id="req-1",
        issued_at=1234567890,
        to="nocturney@gmail.com",
        raw=raw,
    )
    if sig1 != sig2 or len(sig1) != 64:
        fail("Apps Script HMAC signature is not deterministic SHA-256 hex")

    bridge_source = (
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "Code.gs"
    ).read_text(encoding="utf-8")
    for needle in (
        "ALLOWED_RECIPIENT = 'nocturney@gmail.com'",
        "VF_GMAIL_BRIEF_SHARED_SECRET",
        "MAX_SKEW_SECONDS = 300",
        "LAST_SUCCESS_REQUEST_ID",
        "Gmail.Users.Messages.send({raw: raw}, 'me')",
    ):
        if needle not in bridge_source:
            fail(f"Apps Script bridge missing {needle}")

    manifest = json.loads(
        (ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "appsscript.json").read_text()
    )
    scopes = set(manifest.get("oauthScopes") or [])
    expected_scopes = {"https://www.googleapis.com/auth/gmail.send"}
    if scopes != expected_scopes:
        fail(f"Apps Script scopes changed: {sorted(scopes)}")
    services = (manifest.get("dependencies") or {}).get("enabledAdvancedServices") or []
    gmail_services = [
        item for item in services
        if item.get("serviceId") == "gmail"
        and item.get("userSymbol") == "Gmail"
        and item.get("version") == "v1"
    ]
    if len(gmail_services) != 1:
        fail("Apps Script advanced Gmail service is not pinned to Gmail v1")

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

    print("OK Gmail brief sender: Apps Script advanced Gmail + owner lock + UTF-8 MIME + remote-image CID rewrite")


if __name__ == "__main__":
    main()
