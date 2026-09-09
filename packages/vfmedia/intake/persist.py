"""Atomic catalog/inbox persistence with conflict detection."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class PersistConflictError(RuntimeError):
    """Another writer changed the file since we loaded it."""


class PersistError(RuntimeError):
    """Failed to persist durable state."""


def file_digest(path: Path) -> str:
    if not path.is_file():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def atomic_write_json(path: Path, data: Any) -> str:
    """Write JSON atomically; return new sha256 digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception as exc:  # noqa: BLE001
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise PersistError(f"atomic write failed for {path}: {exc}") from exc
    return file_digest(path)


def load_json_with_digest(path: Path, default: Any = None) -> tuple[Any, str]:
    if not path.is_file():
        return default, "missing"
    return json.loads(path.read_text(encoding="utf-8")), file_digest(path)


def merge_catalog_items(base_items: list[dict], ours: list[dict]) -> list[dict]:
    """Merge by sourceFile.id — ours wins on same id; keep foreign new ids."""
    by_id: dict[str, dict] = {}
    order: list[str] = []

    def _fid(item: dict) -> str:
        return ((item.get("sourceFile") or {}).get("id") or item.get("id") or "").strip()

    for item in base_items:
        fid = _fid(item)
        if not fid:
            continue
        if fid not in by_id:
            order.append(fid)
        by_id[fid] = item
    for item in ours:
        fid = _fid(item)
        if not fid:
            continue
        if fid not in by_id:
            order.append(fid)
        by_id[fid] = item
    return [by_id[i] for i in order]


def save_catalog_conflict_aware(
    path: Path,
    catalog: dict,
    *,
    expected_digest: str | None,
) -> str:
    """
    Persist catalog. If another writer changed the file (digest mismatch),
    reload + merge items by sourceFile.id, then write.
    """
    current_digest = file_digest(path) if path.is_file() else "missing"
    if expected_digest is not None and current_digest != expected_digest and path.is_file():
        them, _ = load_json_with_digest(path, {"items": []})
        if not isinstance(them, dict):
            raise PersistConflictError(f"catalog conflict and unreadable peer at {path}")
        catalog = dict(catalog)
        catalog["items"] = merge_catalog_items(them.get("items") or [], catalog.get("items") or [])
        # keep oneCatalog lock from either side
        if them.get("oneCatalog") is True:
            catalog["oneCatalog"] = True
    return atomic_write_json(path, catalog)


def save_inbox_conflict_aware(
    path: Path,
    inbox: dict,
    *,
    expected_digest: str | None,
    card_id: str = "vfmedia-auto-intake",
) -> str:
    current_digest = file_digest(path) if path.is_file() else "missing"
    if expected_digest is not None and current_digest != expected_digest and path.is_file():
        them, _ = load_json_with_digest(path, {"buckets": {}})
        if isinstance(them, dict):
            buckets = them.setdefault("buckets", {})
            ours_buckets = inbox.get("buckets") or {}
            for name, items in ours_buckets.items():
                peer = buckets.setdefault(name, [])
                # replace our card id; keep peer other items
                peer[:] = [x for x in peer if (x or {}).get("id") != card_id]
                for item in items:
                    if (item or {}).get("id") == card_id:
                        peer.append(item)
            inbox = them
            inbox["buckets"] = buckets
    return atomic_write_json(path, inbox)
