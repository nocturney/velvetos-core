#!/usr/bin/env python3
"""Check the Bento Slides shell against its signed release manifest.

The checksum file is https://bento.page/releases/slides/manifest.json.
The signature covers the payload string. The payload names the shell sha256.
Stdlib plus openssl. A signature or sha256 mismatch raises ShellPinError.
A network error propagates. The weekly job runs this command first, so a
network failure fails the job and the JSON deck is not committed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SHELL_URL = "https://bento.page/releases/slides/Bento_Slides.bento.html"
MANIFEST_URL = "https://bento.page/releases/slides/manifest.json"
SHELL_VERSION = "1.2.9"
SHELL_SHA256 = "c7da70eaa8d3f457b2458f1685769bf2c488724ac075954f216c70c60f310af0"
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEGMHSKwWcAoJVq+Dz1ZxWZM6TXATW
IKbaQBpjoTystH9+UU3Nt1cKYk3xFBgJ4bvWsFmeds34wISenURsIsWuPQ==
-----END PUBLIC KEY-----
"""
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bento-slides-manifest-1.2.9.json"


class ShellPinError(Exception):
    pass


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "velvetos-bento-pin"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _der_len(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def _der_int(value: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if raw[0] & 0x80:
        raw = b"\x00" + raw
    return b"\x02" + _der_len(len(raw)) + raw


def p1363_to_der(signature: bytes) -> bytes:
    if len(signature) != 64:
        raise ValueError("ecdsa signature is not 64 bytes")
    body = _der_int(int.from_bytes(signature[:32], "big"))
    body += _der_int(int.from_bytes(signature[32:], "big"))
    return b"\x30" + _der_len(len(body)) + body


def signature_ok(payload: bytes, signature: bytes) -> bool:
    if len(signature) != 64:
        return False
    der = p1363_to_der(signature)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        key = directory / "key.pem"
        body = directory / "payload"
        sig = directory / "sig"
        key.write_text(PUBLIC_KEY_PEM, encoding="utf-8")
        body.write_bytes(payload)
        sig.write_bytes(der)
        proc = subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-verify",
                str(key),
                "-signature",
                str(sig),
                str(body),
            ],
            capture_output=True,
            text=True,
        )
    return proc.returncode == 0


def pin_problems(manifest: bytes, shell: bytes) -> list[str]:
    try:
        obj = json.loads(manifest)
        payload_text = obj["payload"]
        signature = base64.b64decode(obj["sig"])
        info = json.loads(payload_text)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [f"manifest malformed: {exc}"]
    if not isinstance(payload_text, str):
        return ["manifest payload is not a string"]
    if not signature_ok(payload_text.encode("utf-8"), signature):
        return ["manifest signature"]
    if info.get("app") != "bento-slides":
        return ["manifest app"]
    if info.get("version") != SHELL_VERSION:
        return ["manifest version"]
    if info.get("url") != SHELL_URL:
        return ["manifest url"]
    if info.get("sha256") != SHELL_SHA256:
        return ["published checksum"]
    got = hashlib.sha256(shell).hexdigest()
    if got != SHELL_SHA256:
        return ["artifact sha256"]
    return []


def load_shell() -> bytes:
    manifest = fetch(MANIFEST_URL)
    shell = fetch(SHELL_URL)
    problems = pin_problems(manifest, shell)
    if problems:
        raise ShellPinError("; ".join(problems))
    return shell


def self_test() -> int:
    manifest = FIXTURE.read_bytes()
    info = json.loads(json.loads(manifest)["payload"])
    if info["sha256"] != SHELL_SHA256 or info["version"] != SHELL_VERSION:
        print("FAIL bento shell: fixture does not match the pin", file=sys.stderr)
        return 1
    wrong = pin_problems(manifest, b"not-the-shell")
    if wrong != ["artifact sha256"]:
        print(f"FAIL bento shell: wrong bytes were not caught: {wrong}", file=sys.stderr)
        return 1
    tampered = manifest.replace(b"z21mil5B", b"z21mil5C", 1)
    bad = pin_problems(tampered, b"not-the-shell")
    if "manifest signature" not in bad:
        print(f"FAIL bento shell: tampered manifest was not caught: {bad}", file=sys.stderr)
        return 1
    print("OK bento shell self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        shell = load_shell()
    except ShellPinError as exc:
        print(f"FAIL bento shell: {exc}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(shell).hexdigest()
    print(f"OK bento shell {SHELL_VERSION} sha256={digest} bytes={len(shell)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
