#!/usr/bin/env python3
"""Fold changelog.d/*.md fragments into CHANGELOG.md.

Manual and occasional. This script is not a scheduled workflow and must not
be added to one. A second run on the same tree changes nothing.

  python3 scripts/changelog-compile.py
  python3 scripts/changelog-compile.py --root <dir>
  python3 scripts/changelog-compile.py --selftest
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog_contract as contract  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def selftest() -> int:
    script = str(Path(__file__).resolve())
    history_tail = "## [1.0.0]\n\n- released line must stay byte for byte.\n"
    source = (
        "intro\n\n## [Unreleased]\n\n- 2026-10-01 - **Kept:** stays.\n\n" + history_tail
    )
    fragment = "- 2026-10-18 - **Example:** one line.\n"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "CHANGELOG.md").write_bytes(source.encode("utf-8"))
        folder = root / "changelog.d"
        folder.mkdir()
        (folder / "example-pr.md").write_bytes(fragment.encode("utf-8"))
        first = subprocess.run(
            [sys.executable, script, "--root", str(root)],
            text=True, capture_output=True,
        )
        if first.returncode != 0:
            print(first.stderr or first.stdout, file=sys.stderr)
            print("FAIL changelog-compile first run", file=sys.stderr)
            return 1
        folded = (root / "CHANGELOG.md").read_bytes()
        if (folder / "example-pr.md").exists():
            print("FAIL fragment was not consumed", file=sys.stderr)
            return 1
        marker = b"## [1.0.0]\n"
        if folded.split(marker, 1)[1] != source.encode("utf-8").split(marker, 1)[1]:
            print("FAIL compile rewrote released history", file=sys.stderr)
            return 1
        if folded.count(b"- 2026-10-18 - **Example:** one line.") != 1:
            print("FAIL compile duplicated a bullet", file=sys.stderr)
            return 1
        second = subprocess.run(
            [sys.executable, script, "--root", str(root)],
            text=True, capture_output=True,
        )
        if second.returncode != 0:
            print(second.stderr or second.stdout, file=sys.stderr)
            print("FAIL changelog-compile second run", file=sys.stderr)
            return 1
        if (root / "CHANGELOG.md").read_bytes() != folded:
            print("FAIL changelog-compile is not idempotent", file=sys.stderr)
            return 1
    crlf_tail = "## [1.0.0]\r\n\r\n- released line must stay byte for byte.\r\n"
    crlf_source = (
        "intro\r\n\r\n## [Unreleased]\r\n\r\n- 2026-10-01 - **Kept:** stays.\r\n\r\n" + crlf_tail
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "CHANGELOG.md").write_bytes(crlf_source.encode("utf-8"))
        folder = root / "changelog.d"
        folder.mkdir()
        (folder / "example-pr.md").write_bytes(fragment.encode("utf-8"))
        crlf_run = subprocess.run(
            [sys.executable, script, "--root", str(root)],
            text=True, capture_output=True,
        )
        if crlf_run.returncode != 0:
            print(crlf_run.stderr or crlf_run.stdout, file=sys.stderr)
            print("FAIL changelog-compile CRLF run", file=sys.stderr)
            return 1
        written = (root / "CHANGELOG.md").read_bytes()
        marker = b"## [1.0.0]\r\n"
        if marker not in written or written.split(marker, 1)[1] != crlf_tail.encode("utf-8").split(marker, 1)[1]:
            print("FAIL compile rewrote a CRLF released section", file=sys.stderr)
            return 1
        if list(root.glob(".changelog.*.tmp")):
            print("FAIL compile left a changelog temp file", file=sys.stderr)
            return 1
    print("OK changelog-compile selftest idempotent=yes history=unchanged crlf=kept")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return contract.compile_tree(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
