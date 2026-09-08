#!/usr/bin/env python3
"""Production→content continuity — canonical followups via vf_control_plane. No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_control_plane import defensible_match, sync_followups  # noqa: E402

DOC = ROOT / "packages" / "vfgrowth" / "PRODUCTION-CONTENT.md"
POINTER = ROOT / "packages" / "vfgrowth" / "data" / "production-content-followups.json"
CANONICAL = ROOT / "office" / "control" / "followups.json"
PRINT = ROOT / "packages" / "vfprod" / "PRINT-DONE.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not DOC.is_file():
        fail("missing PRODUCTION-CONTENT.md")
    doc = DOC.read_text(encoding="utf-8")
    for needle in (
        "waiting_for_matching_print.done",
        "finished-media-required",
        "Matching defensible",
        "print.done",
        "office/control/followups.json",
        "vf_control_plane",
        "defensible_match",
    ):
        if needle not in doc:
            fail(f"PRODUCTION-CONTENT.md missing {needle!r}")

    if not CANONICAL.is_file():
        fail("missing office/control/followups.json")

    ptr = json.loads(POINTER.read_text(encoding="utf-8"))
    if ptr.get("sourceOfTruth") != "office/control/followups.json":
        fail("production-content-followups.json must pointer to office/control/followups.json")
    if ptr.get("followups"):
        fail("pointer followups array must stay empty (not authoritative)")

    # Unit-style via control-plane defensible_match
    sample_fu = {
        "contentId": "process-demo-1",
        "kind": "process",
        "state": "waiting_for_print_done",
        "jobId": "JOB-100",
        "sku": "G004",
        "sourceLink": "src://g004",
    }
    wrong = {"jobId": "JOB-999", "sku": "G004", "sourceLink": "src://other", "correlation_id": "x"}
    right = {
        "jobId": "JOB-100",
        "sku": "G004",
        "sourceLink": "src://g004",
        "correlation_id": "JOB-100",
    }
    name_only = {"sku": "G004-lookalike", "jobId": "OTHER"}
    if defensible_match(sample_fu, wrong):
        fail("wrong print.done must not close unrelated follow-up")
    if not defensible_match(sample_fu, right):
        fail("matching print.done must close follow-up")
    if defensible_match({"sku": "Ring"}, {"sku": "RingHolder"}):
        fail("name/sku similarity alone must never match")
    if defensible_match(sample_fu, name_only):
        fail("sku without matching sourceLink / jobId must not match")

    # sync_followups is callable (dry)
    sync_followups(mutate=False)

    print_done = PRINT.read_text(encoding="utf-8")
    if "print.done" not in print_done:
        fail("PRINT-DONE.md must keep print.done")

    print("OK production-content continuity (control-plane match)")


if __name__ == "__main__":
    main()
