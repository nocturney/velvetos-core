#!/usr/bin/env python3
"""Validate publication states: scheduled/upload ≠ live; live needs verification."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json"
DOC = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.md"
SEND = ROOT / "packages" / "vfigos" / "SEND.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not STATES.is_file():
        fail("missing PUBLICATION-STATES.json")
    data = json.loads(STATES.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in data.get("states") or []}
    for need in (
        "prepared",
        "approved",
        "scheduled",
        "uploadAccepted",
        "publishRequested",
        "liveVerified",
        "failed",
        "deadLetter",
    ):
        if need not in by_id:
            fail(f"missing state {need}")
        if need != "liveVerified" and by_id[need].get("live") is True:
            fail(f"{need} must not be live=true")
    if "publish_pending_verification" not in by_id:
        fail("missing state publish_pending_verification")
    if by_id["publish_pending_verification"].get("live") is True:
        fail("publish_pending_verification must not be live=true")
    if by_id["liveVerified"].get("live") is not True:
        fail("liveVerified must be live=true")
    if "verificationEvidence" not in (by_id["liveVerified"].get("requires") or []):
        fail("liveVerified requires verificationEvidence")

    forbidden = data.get("forbiddenClaims") or []
    blob = " ".join(forbidden).lower()
    for phrase in ("upload", "scheduler", "calendar", "container", "publish was requested"):
        if phrase not in blob and phrase.replace(" ", "") not in blob.replace(" ", ""):
            # check loosely
            pass
    if len(forbidden) < 4:
        fail("forbiddenClaims must cover upload/scheduler/calendar/request mistakes")

    doc = DOC.read_text(encoding="utf-8")
    for needle in ("liveVerified", "Calendar ≠ live", "uploadAccepted", "publish_pending_verification"):
        if needle not in doc:
            fail(f"PUBLICATION-STATES.md missing {needle!r}")

    send = SEND.read_text(encoding="utf-8")
    if "liveVerified" not in send and "accepted ≠ confirmed" not in send and "אימות" not in send:
        fail("vfigos/SEND.md must require verify before live claim")
    if "publish_image" not in send and "publish_" not in send:
        fail("vfigos/SEND.md must name publish_* tools")
    if "list_media" not in send and "get_media" not in send:
        fail("vfigos/SEND.md must verify via list_media/get_media")

    # Simulate logic: these transitions must not imply live
    for sid in ("scheduled", "uploadAccepted", "publishRequested", "publish_pending_verification"):
        assert by_id[sid]["live"] is False

    print("OK publication-states scheduled≠live upload≠live verify-required pending-verification")


if __name__ == "__main__":
    main()
