#!/usr/bin/env python3
"""One-time OAuth bootstrap for the VelvetOS Gmail brief sender.

Run this on a trusted local machine with a Google OAuth *Desktop app* client
JSON. It requests only gmail.send, receives the loopback callback locally,
exchanges the code, and stores an authorized_user JSON with a refresh token.

The output is a secret. Never commit it to git.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/gmail.send"
DEFAULT_OUTPUT = Path.home() / ".config" / "velvetos" / "gmail-oauth.json"


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def load_client(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    block = data.get("installed") or data.get("web")
    if not isinstance(block, dict):
        raise RuntimeError("OAuth client JSON must contain installed{} or web{}")
    client_id = (block.get("client_id") or "").strip()
    client_secret = (block.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("OAuth client JSON missing client_id/client_secret")
    return {"client_id": client_id, "client_secret": client_secret}


class CallbackHandler(BaseHTTPRequestHandler):
    server_version = "VelvetOSOAuth/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_params = params  # type: ignore[attr-defined]
        body = "VelvetOS Gmail authorization received. You may close this tab."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def exchange_code(*, client: dict, code: str, redirect_uri: str, verifier: str) -> dict:
    payload = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("refresh_token"):
        raise RuntimeError(
            "Google returned no refresh_token. Revoke the app grant and retry with prompt=consent."
        )
    return data


def write_secret(path: Path, *, client: dict, token: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "authorized_user",
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": token["refresh_token"],
        "token": token.get("access_token", ""),
        "token_uri": TOKEN_URL,
        "scopes": [SCOPE],
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-time Gmail OAuth bootstrap for VelvetOS")
    parser.add_argument("--client-secrets", required=True, type=Path, help="Google OAuth Desktop client JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Secret output path (default {DEFAULT_OUTPUT})")
    parser.add_argument("--port", type=int, default=8765, help="Loopback port (default 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Print URL only; do not open the browser")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = load_client(args.client_secrets)
    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = secrets.token_urlsafe(24)
    server = HTTPServer(("127.0.0.1", args.port), CallbackHandler)
    redirect_uri = f"http://127.0.0.1:{server.server_port}/oauth2callback"
    query = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    url = f"{AUTH_URL}?{query}"
    print("Open this Google authorization URL on this machine:\n")
    print(url)
    print(f"\nWaiting for the local callback on {redirect_uri} ...")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()
    params = getattr(server, "oauth_params", {})
    if params.get("state", [None])[0] != state:
        raise RuntimeError("OAuth state mismatch")
    if params.get("error"):
        raise RuntimeError(f"Google OAuth error: {params['error'][0]}")
    code = params.get("code", [None])[0]
    if not code:
        raise RuntimeError("OAuth callback contained no authorization code")
    token = exchange_code(client=client, code=code, redirect_uri=redirect_uri, verifier=verifier)
    write_secret(args.output, client=client, token=token)
    print(f"Saved Gmail OAuth secret to {args.output}")
    print("Keep this file private. Do not commit it to git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
