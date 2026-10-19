#!/usr/bin/env python3
"""Exit 0 only when a file's SHA-256 matches the expected digest.

The Windows check-all job calls this before it uses the pinned ffmpeg zip.
A mismatch exits 1. The comparison is `!=`, so an inverted `==` accepts a bad file.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--kind", default="zip")
    args = parser.parse_args(argv)
    got = file_sha256(Path(args.path))
    expected = args.expected.strip().lower()
    kind = args.kind.strip() or "zip"
    if got != expected:
        print(f"ffmpeg {kind} sha256 mismatch: {got}", file=sys.stderr)
        return 1
    print(f"OK ffmpeg {kind} sha256 {got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
