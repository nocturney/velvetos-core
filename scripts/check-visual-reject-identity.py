#!/usr/bin/env python3
"""Guard the owner-approved visual identity and hard-reject IDs after the Canva removal.

The Canva removal (#362) must not delete reference identity or rejected-design IDs.
This sensor (1) runs the instance template's own cold-start bootstrap check against
this Core checkout, so template drift fails here before it reaches the frontend, and
(2) pins the SHA identity and the rejected G004 design ID in the canonical docs.
Read-only: it copies the template into a temporary directory outside the repo.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "instances" / "velvet-factory"
SHA = "df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897"
REJECT = "DAHUaelaug0"
REQUIRED = {
    "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md": (SHA, REJECT, "Premium but not template-like"),
    "packages/vfom/VELVET-VISUAL-SYSTEM-PROMPT.md": (REJECT, "Use this prompt whenever"),
    "packages/vfom/VISUAL-DNA.json": (SHA, REJECT),
    ".cursor/skills/velvet-brand-guardian/SKILL.md": (REJECT,),
    "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc": (SHA, REJECT, "you MUST load these Core authorities"),
    "instances/velvet-factory/AGENTS.md": (SHA, REJECT, "Never claim a send/publish without receipt/evidence"),
    "instances/velvet-factory/instance/velvet-factory.json": (SHA, REJECT),
}


def fail(message: str) -> None:
    print(f"FAIL visual-reject-identity {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    for rel, needles in REQUIRED.items():
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing {rel}")
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{rel} lost required identity/reject text: {needle}")
    with tempfile.TemporaryDirectory(prefix="vf-instance-bootstrap-") as tmp:
        inst = Path(tmp) / "velvet-factory"
        shutil.copytree(TEMPLATE, inst)
        (inst / "vendor").mkdir(exist_ok=True)
        (inst / "vendor" / "velvetos-core").symlink_to(ROOT, target_is_directory=True)
        proc = subprocess.run(
            [sys.executable, str(inst / "scripts" / "check-instance-visual-bootstrap.py")],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            fail("instance template bootstrap check failed: " + (proc.stderr or proc.stdout).strip())
    print("OK visual-reject-identity: SHA identity + rejected G004 design pinned; instance template bootstrap passes against Core")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
