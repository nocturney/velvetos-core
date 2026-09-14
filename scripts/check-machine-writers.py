#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MARKER = "VELVET_MACHINE_WRITER_ALLOW:"


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def is_main_writer(text: str) -> bool:
    if not re.search(r"(?m)^\s*git\s+push\b", text):
        return False
    if "branches: [fix/close-runtime-corners-20260914]" in text and "workflow_dispatch:" not in text:
        return False
    return True


def marker_paths(text: str) -> list[str]:
    m = re.search(r"(?m)^\s*#\s*VELVET_MACHINE_WRITER_ALLOW:\s*(.+?)\s*$", text)
    if not m:
        return []
    return [p for p in m.group(1).split() if p]


def has_write_permission(text: str) -> bool:
    """Accept explicit workflow- or job-level contents: write, never implicit defaults."""
    return bool(re.search(r"(?m)^\s*contents:\s*write\s*(?:#.*)?$", text))


def main() -> int:
    writers = []
    for path in sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        if not is_main_writer(text):
            continue
        rel = path.relative_to(ROOT).as_posix()
        writers.append(rel)
        allowed = marker_paths(text)
        if not allowed:
            fail(f"machine writer {rel} has git push but no {MARKER} contract")
        if not has_write_permission(text):
            fail(f"machine writer {rel} lacks explicit contents: write permission")
        for line in text.splitlines():
            cmd = line.strip()
            if re.fullmatch(r"git add (?:-A|--all|\.)", cmd):
                fail(f"machine writer {rel} uses unrestricted staging: {cmd}")
            if re.match(r"git push\s+(?:--force|-f)\b", cmd):
                fail(f"machine writer {rel} may force-push: {cmd}")
        add_lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("git add ")]
        if not add_lines:
            fail(f"machine writer {rel} pushes but has no explicit git add line")
        if any("${existing[@]}" in ln for ln in add_lines) and "paths=(" not in text:
            fail(f"machine writer {rel} has dynamic staging without bounded paths array")
    if not writers:
        fail("no production machine writers discovered; sensor query likely broken")
    print(f"OK machine-writers={len(writers)} allowlisted force_push=0 unrestricted_stage=0")
    for writer in writers:
        print("- " + writer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
