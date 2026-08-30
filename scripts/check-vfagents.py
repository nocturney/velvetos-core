#!/usr/bin/env python3
"""Validate vfagents fit map against the HQ pack catalog. No Instagram send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIT = ROOT / "packages" / "vfagents" / "fit.json"
MANIFEST = ROOT / "packages" / "manifest.json"
ALLOWED_STATUS = {"embed", "already", "skip", "later"}


def main() -> int:
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packs = {p["name"] for p in manifest["packs"]}
    errors: list[str] = []
    counts = {s: 0 for s in ALLOWED_STATUS}

    if "vfagents" not in packs:
        errors.append("manifest missing pack vfagents")

    items = fit.get("items") or []
    if not items:
        errors.append("fit.json has no items")

    for i, item in enumerate(items):
        iid = item.get("id") or f"#{i}"
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{iid}: bad status {status!r}")
            continue
        counts[status] += 1

        if not item.get("source"):
            errors.append(f"{iid}: source required")

        for pack in item.get("packs") or []:
            if pack not in packs:
                errors.append(f"{iid}: unknown pack {pack}")

        if status == "embed":
            rel = item.get("playbook")
            if not rel:
                errors.append(f"{iid}: embed needs playbook")
            else:
                path = (ROOT / "packages" / "vfagents" / rel).resolve()
                if not path.is_file():
                    errors.append(f"{iid}: missing {rel}")
                if not item.get("packs"):
                    errors.append(f"{iid}: embed needs packs")
        elif status == "skip":
            if not item.get("reason"):
                errors.append(f"{iid}: skip needs reason")
        elif status in {"already", "later"}:
            if not item.get("note"):
                errors.append(f"{iid}: {status} needs note")

    writeup = ROOT / fit.get("writeup", "docs/500-AGENTS.md")
    if not writeup.is_file():
        errors.append(f"missing writeup {writeup}")

    skip_md = ROOT / "packages" / "vfagents" / "SKIP.md"
    if not skip_md.is_file():
        errors.append("missing SKIP.md")

    if errors:
        print("FAIL vfagents")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        "OK vfagents "
        f"embed={counts['embed']} already={counts['already']} "
        f"later={counts['later']} skip={counts['skip']} "
        f"packs={len(packs)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
