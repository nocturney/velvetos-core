#!/usr/bin/env python3
"""Archive expired publish-bridge assets instead of deleting them.

Assets leave the active Instagram transport path after the retention window but
remain preserved under the archive path. No automatic deletion of archived
assets is performed.
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


def archive_expired(
    active_root: Path,
    archive_root: Path,
    retention_days: int,
    today: dt.date,
) -> list[dict[str, str]]:
    archived: list[dict[str, str]] = []
    if not active_root.exists():
        return archived

    cutoff = today - dt.timedelta(days=retention_days)
    archive_root.mkdir(parents=True, exist_ok=True)

    for child in sorted(active_root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        day = parse_date_dir(child)
        if day is None or day > cutoff:
            continue

        target = archive_root / child.name
        if target.exists():
            raise RuntimeError(
                f"archive collision for {child.name}: {target} already exists; refusing to overwrite or delete"
            )

        shutil.move(str(child), str(target))
        archived.append({"from": str(child), "to": str(target)})

    return archived


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="active publish-bridge assets root")
    parser.add_argument("--archive-root", required=True, help="archive destination root")
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--today", help="YYYY-MM-DD for deterministic tests")
    args = parser.parse_args()

    if args.retention_days < 1:
        raise SystemExit("retention-days must be >= 1")

    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    active_root = Path(args.root).resolve()
    archive_root = Path(args.archive_root).resolve()

    if active_root == archive_root:
        raise SystemExit("archive-root must differ from root")
    if archive_root.is_relative_to(active_root):
        raise SystemExit("archive-root must not be nested inside active root")

    archived = archive_expired(active_root, archive_root, args.retention_days, today)
    print(
        json.dumps(
            {
                "ok": True,
                "archived": archived,
                "deleted": [],
                "archiveRetention": "unlimited",
                "deleteArchived": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
