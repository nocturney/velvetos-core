#!/usr/bin/env python3
"""Production→content continuity rules. No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "packages" / "vfgrowth" / "PRODUCTION-CONTENT.md"
DATA = ROOT / "packages" / "vfgrowth" / "data" / "production-content-followups.json"
PRINT = ROOT / "packages" / "vfprod" / "PRINT-DONE.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def matching_closes(followup: dict, print_done: dict) -> bool:
    """Defensible match only — name similarity alone is insufficient."""
    for key in ("jobId", "correlationId", "printCardPath"):
        a = followup.get(key)
        b = print_done.get(key)
        if a and b and a == b:
            return True
    sku_a = followup.get("sku")
    sku_b = print_done.get("sku")
    src_a = followup.get("sourceLink")
    src_b = print_done.get("sourceLink")
    if sku_a and sku_b and sku_a == sku_b and src_a and src_b and src_a == src_b:
        return True
    return False


def main() -> None:
    if not DOC.is_file():
        fail("missing PRODUCTION-CONTENT.md")
    doc = DOC.read_text(encoding="utf-8")
    for needle in (
        "waiting_for_matching_print.done",
        "finished-media-required",
        "Matching defensible",
        "print.done",
    ):
        if needle not in doc:
            fail(f"PRODUCTION-CONTENT.md missing {needle!r}")

    data = json.loads(DATA.read_text(encoding="utf-8"))
    if "followups" not in data:
        fail("followups array required")

    # Unit-style: process content creates follow-up contract
    sample_fu = {
        "contentId": "process-demo-1",
        "kind": "process",
        "status": "waiting_for_matching_print.done",
        "jobId": "JOB-100",
        "sku": "G004",
        "sourceLink": "src://g004",
    }
    wrong = {"jobId": "JOB-999", "sku": "G004", "sourceLink": "src://other", "correlationId": "x"}
    right = {
        "jobId": "JOB-100",
        "sku": "G004",
        "sourceLink": "src://g004",
        "correlationId": "JOB-100",
    }
    if matching_closes(sample_fu, wrong):
        fail("wrong print.done must not close unrelated follow-up")
    if not matching_closes(sample_fu, right):
        fail("matching print.done must close follow-up")

    # finished path
    after = dict(sample_fu)
    after["status"] = "finished-content-prep"
    after["next"] = ["edit-gate", "preflight", "calendar-slot", "publish-when-ready", "live-verify"]
    if "finished-media-required" not in doc:
        fail("missing finished-media-required path")

    print_done = PRINT.read_text(encoding="utf-8")
    if "print.done" not in print_done:
        fail("PRINT-DONE.md must keep print.done")

    print("OK production-content continuity")


if __name__ == "__main__":
    main()
