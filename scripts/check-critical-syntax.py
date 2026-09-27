#!/usr/bin/env python3
"""Fast always-on syntax gate for tracked Python sources. No imports, network, or writes."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tracked_python() -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files failed")
    return [ROOT / rel for rel in proc.stdout.splitlines() if rel.strip()]


def main() -> int:
    problems: list[str] = []
    files = tracked_python()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8-sig")
            ast.parse(source, filename=rel)
        except (OSError, UnicodeError, SyntaxError) as exc:
            problems.append(f"{rel}: {exc}")
    if problems:
        for problem in problems:
            print(f"FAIL critical-syntax {problem}", file=sys.stderr)
        return 1
    print(f"OK critical-syntax tracked_python={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
