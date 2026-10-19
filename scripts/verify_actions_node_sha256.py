#!/usr/bin/env python3
"""Check one actions/node-versions build against its release hashes.sha256.

The checksum URL is the release file hashes.sha256. The artifact URL is that
same directory plus the filename. After the hash matches, `node --version`
must be v<version>. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import urllib.request

PREFIX = "https://github.com/actions/node-versions/releases/download/"
SUFFIX = "/hashes.sha256"
HEX = re.compile(r"^[0-9a-f]{64}$")
NAME = re.compile(r"^node-.+\.tar\.gz$")


def fail(msg: str) -> None:
    print(f"FAIL node toolchain: {msg}", file=sys.stderr)
    raise SystemExit(1)


def published_hash(text: str, filename: str) -> str:
    found: str | None = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[1] != filename:
            continue
        if found is not None:
            raise ValueError(f"duplicate checksum for {filename}")
        found = parts[0].lower()
    if found is None:
        raise ValueError(f"checksum file has no {filename}")
    if not HEX.fullmatch(found):
        raise ValueError(f"published checksum is not sha256 for {filename}")
    return found


def artifact_problems(
    checksum_text: str,
    *,
    filename: str,
    expected: str,
    blob: bytes,
) -> list[str]:
    problems: list[str] = []
    wanted = expected.lower()
    if not HEX.fullmatch(wanted):
        problems.append("expected is not sha256")
        return problems
    try:
        published = published_hash(checksum_text, filename)
    except ValueError as exc:
        problems.append(str(exc))
        return problems
    if published != wanted:
        problems.append(f"published checksum {published} != expected {wanted}")
    got = hashlib.sha256(blob).hexdigest()
    if got != wanted:
        problems.append(f"artifact sha256 {got} != expected {wanted}")
    return problems


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "velvetos-node-pin"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version")
    parser.add_argument("--filename")
    parser.add_argument("--expected")
    parser.add_argument("--checksum-url")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.version or not args.filename or not args.expected or not args.checksum_url:
        fail("version, filename, expected, and checksum-url are required")
    expected = args.expected.lower()
    if not HEX.fullmatch(expected):
        fail("expected is not sha256")
    if not NAME.fullmatch(args.filename) or args.version not in args.filename:
        fail("filename does not match version")
    if not args.checksum_url.startswith(PREFIX) or not args.checksum_url.endswith(SUFFIX):
        fail("checksum url is not an actions/node-versions hashes.sha256")
    tag = args.checksum_url[len(PREFIX):-len(SUFFIX)]
    if not tag.startswith(args.version + "-") or "/" in tag:
        fail("checksum url tag does not match version")
    checksum_text = fetch(args.checksum_url).decode("utf-8")
    artifact_url = args.checksum_url[: -len("hashes.sha256")] + args.filename
    blob = fetch(artifact_url)
    problems = artifact_problems(
        checksum_text, filename=args.filename, expected=expected, blob=blob
    )
    if problems:
        fail("; ".join(problems))
    proc = subprocess.run(["node", "--version"], text=True, capture_output=True)
    runtime = (proc.stdout or "").strip()
    if proc.returncode != 0 or runtime != f"v{args.version}":
        fail(f"runtime {runtime or proc.stderr.strip()} != v{args.version}")
    digest = hashlib.sha256(blob).hexdigest()
    print(f"OK node toolchain {args.version} sha256={digest} runtime={runtime}")
    return 0


def self_test() -> int:
    filename = "node-24.21.0-linux-x64.tar.gz"
    blob = b"node-bytes"
    digest = hashlib.sha256(blob).hexdigest()
    text = f"{digest} {filename}\n"
    if artifact_problems(text, filename=filename, expected=digest, blob=blob):
        fail("matching artifact was refused")
    swapped = artifact_problems(text, filename=filename, expected="0" * 64, blob=blob)
    if not any("published checksum" in item for item in swapped):
        fail("swapped expected hash was not caught")
    wrong = artifact_problems(text, filename=filename, expected=digest, blob=b"other")
    if not any("artifact sha256" in item for item in wrong):
        fail("wrong artifact bytes were not caught")
    print("OK node toolchain self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
