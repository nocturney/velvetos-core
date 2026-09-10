#!/usr/bin/env python3
"""Remove expired publish-bridge assets from the branch head.

This is retention hygiene, not secure erasure: Git history can retain old blobs.
The public-release gate therefore remains mandatory before an asset is staged.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path


def parse_date_dir(path: Path) -> dt.date | None:
    try:
        return dt.date.fromisoformat(path.name)
    except ValueError:
        return None


def cleanup(root: Path, retention_days: int, today: dt.date) -> list[str]:
    removed: list[str] = []
    if not root.exists():
        return removed
    cutoff = today - dt.timedelta(days=retention_days)
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        day = parse_date_dir(child)
        if day is None or day > cutoff:
            continue
        shutil.rmtree(child)
        removed.append(str(child))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--today", help="YYYY-MM-DD for deterministic tests")
    args = parser.parse_args()
    if args.retention_days < 1:
        raise SystemExit("retention-days must be >= 1")
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    root = Path(args.root).resolve()
    removed = cleanup(root, args.retention_days, today)
    print(json.dumps({"ok": True, "removed": removed, "historyErasure": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
