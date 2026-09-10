#!/usr/bin/env python3
"""Send one Velvet Factory office brief via Gmail API.

The production path uses multipart/related and Content-ID (CID) images so the
brief does not depend on Gmail loading expiring Canva / Instagram / research
URLs after delivery.

Examples:

  PYTHONPATH=packages python3 -m vfops.gmail_brief_send \
    --html PATH --images DIR --to EMAIL --subject TEXT

  PYTHONPATH=packages python3 -m vfops.gmail_brief_send \
    --html PATH --images DIR --to EMAIL --subject TEXT \
    --embed-remote-images

Credential sources, in order:
- GOOGLE_TOKEN: access token, authorized_user JSON, service account JSON, or a
  path containing one of those.
- GOOGLE_APPLICATION_CREDENTIALS / ADC.

For a normal Gmail user, use an authorized_user OAuth JSON with a refresh token.
No token -> print ``no token`` and exit 2. Does not invent business data.
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import ipaddress
import json
import os
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
IMAGE_SUFFIXES = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}
CONTENT_TYPE_SUFFIX = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
ADC_WELL_KNOWN = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
IMG_SRC_RE = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*[\"'])(https://[^\"']+)([\"'])", re.IGNORECASE)
DEFAULT_REMOTE_IMAGE_LIMIT = 12
DEFAULT_REMOTE_IMAGE_MAX_BYTES = 8 * 1024 * 1024


def fail(msg: str, code: int = 1) -> int:
    print(msg, file=sys.stderr)
    return code


def iter_images(images_dir: Path) -> list[Path]:
    if not images_dir.is_dir():
        raise FileNotFoundError(f"images dir not found: {images_dir}")
    out: list[Path] = []
    for path in sorted(images_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            out.append(path)
    return out


def build_mime(*, html: str, images: list[Path], to: str, subject: str) -> MIMEMultipart:
    """multipart/related: HTML + inline images. filename = Content-ID."""
    msg = MIMEMultipart("related")
    msg["To"] = to
    msg["Subject"] = subject
    html_part = MIMEText(html, "html", "utf-8")
    # Keep cid: references readable in raw RFC822. Gmail API accepts UTF-8 8bit.
    if html_part["Content-Transfer-Encoding"]:
        del html_part["Content-Transfer-Encoding"]
    html_part.set_payload(html)
    html_part["Content-Transfer-Encoding"] = "8bit"
    msg.attach(html_part)
    for path in images:
        subtype = IMAGE_SUFFIXES[path.suffix.lower()]
        part = MIMEImage(path.read_bytes(), _subtype=subtype)
        cid = path.name
        part.add_header("Content-ID", f"<{cid}>")
        part.add_header("Content-Disposition", "inline", filename=cid)
        part.set_param("name", cid)
        msg.attach(part)
    return msg


def _public_ip(host: str) -> None:
    """Reject localhost/private/reserved destinations before fetching images."""
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError(f"image host DNS failed: {host}: {exc}") from exc
    if not infos:
        raise RuntimeError(f"image host resolved to no addresses: {host}")
    for info in infos:
        raw = info[4][0]
        try:
            addr = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise RuntimeError(f"image host returned invalid address: {raw}") from exc
        if not addr.is_global:
            raise RuntimeError(f"refusing non-public image address for {host}: {addr}")


def _validate_remote_url(url: str) -> urllib.parse.SplitResult:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise RuntimeError(f"remote image must use https: {url[:120]}")
    if not parsed.hostname:
        raise RuntimeError(f"remote image has no hostname: {url[:120]}")
    if parsed.username or parsed.password:
        raise RuntimeError("remote image URL must not contain userinfo")
    _public_ip(parsed.hostname)
    return parsed


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        _validate_remote_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_one(url: str, dest: Path, *, max_bytes: int) -> Path:
    _validate_remote_url(url)
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "VelvetOS-Morning-Brief/1.0 (+https://github.com/nocturney/velvetos-core)",
            "Accept": "image/avif,image/webp,image/apng,image/png,image/jpeg,image/gif,image/*;q=0.8",
        },
        method="GET",
    )
    try:
        with opener.open(req, timeout=20) as resp:
            content_type = (resp.headers.get_content_type() or "").lower()
            suffix = CONTENT_TYPE_SUFFIX.get(content_type)
            if not suffix:
                raise RuntimeError(f"remote URL is not a supported image ({content_type or 'unknown'}): {url[:120]}")
            length = resp.headers.get("Content-Length")
            if length:
                try:
                    if int(length) > max_bytes:
                        raise RuntimeError(f"remote image exceeds {max_bytes} bytes: {url[:120]}")
                except ValueError:
                    pass
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = resp.read(min(65536, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise RuntimeError(f"remote image exceeds {max_bytes} bytes: {url[:120]}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"remote image HTTP {exc.code}: {url[:120]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"remote image fetch failed: {url[:120]}: {exc.reason}") from exc
    out = dest.with_suffix(suffix)
    out.write_bytes(b"".join(chunks))
    return out


def embed_remote_images(
    html: str,
    dest_dir: Path,
    *,
    limit: int = DEFAULT_REMOTE_IMAGE_LIMIT,
    max_bytes: int = DEFAULT_REMOTE_IMAGE_MAX_BYTES,
) -> tuple[str, list[Path]]:
    """Download public HTTPS <img src> URLs and rewrite them to local cid: refs.

    URLs are deduplicated. Unsafe/private destinations, unsupported MIME types,
    fetch failures and over-limit images fail closed; the brief is not sent with
    a silently broken visual layer.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    matches = list(IMG_SRC_RE.finditer(html))
    unique: list[str] = []
    for match in matches:
        raw = match.group(2)
        if raw not in unique:
            unique.append(raw)
    if len(unique) > limit:
        raise RuntimeError(f"brief has {len(unique)} remote images; limit is {limit}")

    mapping: dict[str, str] = {}
    downloaded: list[Path] = []
    for idx, raw in enumerate(unique, start=1):
        request_url = html_lib.unescape(raw)
        stem = dest_dir / f"remote-{idx:02d}"
        path = _download_one(request_url, stem, max_bytes=max_bytes)
        mapping[raw] = f"cid:{path.name}"
        downloaded.append(path)

    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{mapping[match.group(2)]}{match.group(3)}"

    return IMG_SRC_RE.sub(repl, html), downloaded


def _looks_like_json(raw: str) -> bool:
    text = raw.strip()
    return text.startswith("{") and text.endswith("}")


def _load_json_blob(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def token_material_available() -> bool:
    """True when GOOGLE_TOKEN or ADC is present on the runner (not yet minted)."""
    if (os.environ.get("GOOGLE_TOKEN") or "").strip():
        return True
    adc = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if adc and Path(adc).is_file():
        return True
    if ADC_WELL_KNOWN.is_file():
        return True
    try:
        from google.auth import default as google_default  # type: ignore

        google_default(scopes=[GMAIL_SEND_SCOPE])
        return True
    except Exception:
        return False


def _refresh_authorized_user(data: dict) -> str:
    refresh = (data.get("refresh_token") or "").strip()
    client_id = (data.get("client_id") or "").strip()
    client_secret = (data.get("client_secret") or "").strip()
    if not (refresh and client_id and client_secret):
        raise RuntimeError("authorized_user JSON missing refresh_token/client_id/client_secret")
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OAUTH_TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = (payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("oauth refresh returned no access_token")
    return token


def _service_account_token(data: dict) -> str:
    try:
        from google.oauth2 import service_account  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore

        creds = service_account.Credentials.from_service_account_info(data, scopes=[GMAIL_SEND_SCOPE])
        creds.refresh(Request())
        if not creds.token:
            raise RuntimeError("service account minted empty token")
        return creds.token
    except ImportError:
        pass

    import jwt  # PyJWT

    now = int(time.time())
    email = (data.get("client_email") or "").strip()
    key = data.get("private_key")
    if not (email and key):
        raise RuntimeError("service_account JSON missing client_email/private_key")
    claim = {
        "iss": email,
        "scope": GMAIL_SEND_SCOPE,
        "aud": OAUTH_TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(claim, key, algorithm="RS256")
    if isinstance(assertion, bytes):
        assertion = assertion.decode("ascii")
    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OAUTH_TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = (payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("service account jwt-bearer returned no access_token")
    return token


def _token_from_mapping(data: dict) -> str:
    for key in ("access_token", "token"):
        value = data.get(key)
        if isinstance(value, str) and value.strip() and not value.strip().startswith("{"):
            if data.get("refresh_token") and data.get("client_id"):
                try:
                    return _refresh_authorized_user(data)
                except Exception:
                    return value.strip()
            return value.strip()
    kind = (data.get("type") or "").strip()
    if kind == "authorized_user" or data.get("refresh_token"):
        return _refresh_authorized_user(data)
    if kind == "service_account" or data.get("private_key"):
        return _service_account_token(data)
    raise RuntimeError("credential JSON has no access_token/refresh_token/service_account")


def _token_from_google_auth() -> str | None:
    try:
        from google.auth import default as google_default  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except ImportError:
        return None
    creds, _project = google_default(scopes=[GMAIL_SEND_SCOPE])
    if not getattr(creds, "valid", False) or not getattr(creds, "token", None):
        creds.refresh(Request())
    token = getattr(creds, "token", None)
    return token.strip() if isinstance(token, str) and token.strip() else None


def mint_access_token() -> str:
    raw = (os.environ.get("GOOGLE_TOKEN") or "").strip()
    if raw:
        as_path = Path(raw)
        if as_path.is_file():
            text = as_path.read_text(encoding="utf-8").strip()
            data = _load_json_blob(text)
            if data is not None:
                return _token_from_mapping(data)
            if text:
                return text
            raise RuntimeError(f"GOOGLE_TOKEN file is empty: {as_path}")
        if _looks_like_json(raw):
            data = _load_json_blob(raw)
            if data is None:
                raise RuntimeError("GOOGLE_TOKEN JSON is invalid")
            return _token_from_mapping(data)
        return raw

    adc = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    candidates = []
    if adc:
        candidates.append(Path(adc))
    candidates.append(ADC_WELL_KNOWN)
    for path in candidates:
        if path.is_file():
            data = _load_json_blob(path.read_text(encoding="utf-8"))
            if data is None:
                raise RuntimeError(f"ADC file is not JSON: {path}")
            return _token_from_mapping(data)

    token = _token_from_google_auth()
    if token:
        return token
    raise RuntimeError("no token")


def send_raw_rfc822(access_token: str, raw_bytes: bytes) -> str:
    raw = base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")
    payload = json.dumps({"raw": raw}).encode("utf-8")
    req = urllib.request.Request(
        GMAIL_SEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"gmail send HTTP {exc.code}: {detail}") from exc
    message_id = (body.get("id") or "").strip()
    if not message_id:
        raise RuntimeError(f"gmail send returned no message id: {body!r}")
    return message_id


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m vfops.gmail_brief_send",
        description=(
            "Send one office brief (HTML + inline CID images) via Gmail API. "
            "Exit 2 when GOOGLE_TOKEN / ADC is missing."
        ),
    )
    parser.add_argument("--html", required=True, type=Path, help="Path to rendered brief HTML")
    parser.add_argument("--images", required=True, type=Path, help="Directory of already-local CID images")
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Subject line")
    parser.add_argument(
        "--embed-remote-images",
        action="store_true",
        help="Download public HTTPS <img src> URLs, rewrite them to cid:, and attach inline",
    )
    parser.add_argument(
        "--remote-image-limit",
        type=int,
        default=DEFAULT_REMOTE_IMAGE_LIMIT,
        help=f"Maximum remote images to embed (default {DEFAULT_REMOTE_IMAGE_LIMIT})",
    )
    parser.add_argument(
        "--remote-image-max-bytes",
        type=int,
        default=DEFAULT_REMOTE_IMAGE_MAX_BYTES,
        help=f"Maximum bytes per remote image (default {DEFAULT_REMOTE_IMAGE_MAX_BYTES})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    html_path: Path = args.html
    images_dir: Path = args.images
    if not html_path.is_file():
        return fail(f"html not found: {html_path}")
    if not images_dir.is_dir():
        return fail(f"images dir not found: {images_dir}")
    if args.remote_image_limit < 0:
        return fail("remote image limit must be >= 0")
    if args.remote_image_max_bytes < 1024:
        return fail("remote image max bytes must be >= 1024")

    if not token_material_available():
        return fail("no token: set GOOGLE_TOKEN or ADC (GOOGLE_APPLICATION_CREDENTIALS)", 2)

    try:
        html = html_path.read_text(encoding="utf-8")
        images = iter_images(images_dir)
        with tempfile.TemporaryDirectory(prefix="vfbrief-cid-") as tmp:
            if args.embed_remote_images:
                html, remote_images = embed_remote_images(
                    html,
                    Path(tmp),
                    limit=args.remote_image_limit,
                    max_bytes=args.remote_image_max_bytes,
                )
                images.extend(remote_images)
            mime = build_mime(html=html, images=images, to=args.to, subject=args.subject)
            access_token = mint_access_token()
            message_id = send_raw_rfc822(access_token, mime.as_bytes())
    except Exception as exc:
        return fail(str(exc), 1)

    print(message_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
