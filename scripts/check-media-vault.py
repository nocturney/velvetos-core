#!/usr/bin/env python3
"""Validate shared Velvet Media vault overlay. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "constitution" / "MEDIA-VAULT.md"
CATALOG = ROOT / "packages" / "vfigos" / "media-catalog.json"
SKILL = ROOT / "packages" / "vfigos" / "SKILL.md"
SEND = ROOT / "packages" / "vfigos" / "SEND.md"
CONST = ROOT / "constitution" / "CONSTITUTION.md"
AGENTS = ROOT / "AGENTS.md"

REQUIRED_FOLDER_IDS = {
    "rootId": "1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv",
    "inbox": "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "source": "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "in_progress": "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "approved": "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
}

ITEM_REQUIRED = {
    "sourceFileId",
    "viewUrl",
    "description",
    "uploadedAt",
    "status",
    "assignee",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (POLICY, CATALOG, SKILL, SEND, CONST, AGENTS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    policy = POLICY.read_text(encoding="utf-8")
    for fid in REQUIRED_FOLDER_IDS.values():
        if fid not in policy:
            fail(f"MEDIA-VAULT.md missing folder id {fid}")
    for needle in (
        "מנהל קליטה",
        "media-catalog.json",
        "שינוי הרשאות שיתוף",
        "download_file_content",
        "מאושר לפרסום",
    ):
        if needle not in policy:
            fail(f"MEDIA-VAULT.md missing needle {needle!r}")

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        fail("media-catalog.json schemaVersion must be 1")
    vault = data.get("vault") or {}
    if vault.get("rootId") != REQUIRED_FOLDER_IDS["rootId"]:
        fail("catalog vault.rootId mismatch")
    folders = vault.get("folders") or {}
    for key in ("inbox", "source", "in_progress", "approved"):
        if folders.get(key) != REQUIRED_FOLDER_IDS[key]:
            fail(f"catalog folders.{key} mismatch")
    if "intakeManagerStatus" not in data:
        fail("catalog missing intakeManagerStatus")
    if not isinstance(data.get("items"), list):
        fail("catalog items must be a list")

    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            fail(f"items[{i}] must be object")
        missing = ITEM_REQUIRED - set(item)
        if missing:
            fail(f"items[{i}] missing fields {sorted(missing)}")
        if item.get("status") not in {
            "inbox",
            "source",
            "in_progress",
            "approved",
            "published",
            "blocked",
        }:
            fail(f"items[{i}] invalid status")
        # Never invent sale price fields in media catalog
        for bad in ("price_ils", "sale_ils", "estimated_value_ils"):
            if bad in item and item[bad] is not None:
                fail(f"items[{i}] must not invent {bad}")

    skill = SKILL.read_text(encoding="utf-8")
    if "MEDIA-VAULT.md" not in skill or "media-catalog.json" not in skill:
        fail("vfigos/SKILL.md must point at MEDIA-VAULT + media-catalog")

    send = SEND.read_text(encoding="utf-8")
    if "MEDIA-VAULT.md" not in send:
        fail("vfigos/SEND.md must point at constitution/MEDIA-VAULT.md")

    const = CONST.read_text(encoding="utf-8")
    if "MEDIA-VAULT.md" not in const:
        fail("CONSTITUTION.md must mention MEDIA-VAULT.md")

    agents = AGENTS.read_text(encoding="utf-8")
    if "MEDIA-VAULT.md" not in agents:
        fail("AGENTS.md must mention MEDIA-VAULT.md")

    print("PASS media-vault overlay (single catalog · folder ids · no parallel)")


if __name__ == "__main__":
    main()
