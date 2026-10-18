#!/usr/bin/env python3
"""Sensor: Office 2.0 read-only desk stays offline, fixture-tested, and manual-dispatch only."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "office_v2_mvp.py"
TEST = ROOT / "scripts" / "test_office_v2_mvp.py"
FIXTURE = ROOT / "scripts" / "fixtures" / "office_v2_mvp" / "api.json"
NEXT = ROOT / "docs" / "office-v2" / "NEXT.md"
WORKFLOW = ROOT / ".github" / "workflows" / "office-v2-board.yml"
LOCKS = (
    ROOT / "requirements-sensors.txt",
    ROOT / "requirements-sensors.py311.lock",
    ROOT / "requirements-sensors.py312.lock",
)


def fail(message: str) -> None:
    print(f"FAIL office-v2-mvp: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    for path in (SCRIPT, TEST, FIXTURE, NEXT, WORKFLOW):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "gh pr create",
        "gh pr merge",
        "gh issue create",
        "--method POST",
        "import crewai",
        "import langgraph",
    ):
        if forbidden in source:
            fail(f"script contains forbidden text: {forbidden}")
    if "6249011608" not in source or "Asia/Jerusalem" not in source:
        fail("script missing research comment or Jerusalem clock")
    if "--method\", \"GET\"" not in source and '"GET"' not in source:
        fail("script does not pin GitHub reads to GET")
    next_doc = NEXT.read_text(encoding="utf-8")
    if "6249011608" not in next_doc:
        fail("next-step doc missing verified research comment 6249011608")
    lock_blob = "\n".join(path.read_text(encoding="utf-8").lower() for path in LOCKS)
    if "crewai" in lock_blob or "langgraph" in lock_blob:
        fail("lockfile now contains an agent framework; update the desk admission before importing it")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if "workflow_dispatch:" not in workflow:
        fail("workflow is not manual-dispatch")
    if re.search(r"(?m)^\s*schedule:\s*$", workflow) or "cron:" in workflow:
        fail("workflow must not schedule; ChatGPT automations own the clock")
    if re.search(r"(?m)^\s*contents:\s*write\s*$", workflow):
        fail("workflow must not request contents: write")
    if "contents: read" not in workflow:
        fail("workflow missing contents: read")
    for needle in ("office_v2_mvp.py", "actions/upload-artifact@", "persist-credentials: false"):
        if needle not in workflow:
            fail(f"workflow missing {needle}")
    if "git push" in workflow or "gh pr" in workflow:
        fail("workflow must not write to GitHub")
    proc = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        detail = (proc.stdout + "\n" + proc.stderr).strip()
        fail("fixture unit test failed\n" + detail[-2000:])
    print("OK office-v2-mvp offline fixture read_only=GET schedule=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
