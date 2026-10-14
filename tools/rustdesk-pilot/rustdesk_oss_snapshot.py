"""Read-only RustDesk OSS peer discovery from an EXPLICIT, OFFLINE SQLite snapshot.

The upstream OSS hbbs 'peer' table stores registered IDs but does NOT provide
an independently verified last-online timestamp or host inventory. This tool
never opens a known live hbbs path or discovers one on its own. Presence stays
UNKNOWN for every record. No network, control operations, or secrets are read.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from cortendesk_inventory import SCHEMA, AdapterError

MAX_PEERS = 1000
SOURCE = 'rustdesk_oss_peer_snapshot'


def snapshot_inventory(path: Path, *, read_at: str | None = None) -> dict[str, Any]:
    """A one-shot read of a separately acquired, stable SQLite SNAPSHOT file.

    SQLite URI 'mode=ro&immutable=1' does no locking or writes; it must NOT be
    used against a live database with pending WAL records. Caller owns the
    responsibility to provide a completed backup/snapshot, never the live DB.
    """
    try:
        full = path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AdapterError('snapshot_missing') from exc
    if not full.is_file():
        raise AdapterError('snapshot_not_file')
    uri = full.as_uri() + '?mode=ro&immutable=1'
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=1)) as conn:
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA trusted_schema=OFF')
            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='peer'"
            ).fetchone()
            if not table:
                raise AdapterError('snapshot_schema_mismatch')
            columns = {row[1] for row in conn.execute('PRAGMA table_info(peer)')}
            if not {'id', 'created_at'}.issubset(columns):
                raise AdapterError('snapshot_schema_mismatch')
            # Deliberately never select 'uuid', 'guid', 'pk', 'info', 'user', 'note'.
            rows = conn.execute(
                'SELECT id FROM peer ORDER BY id LIMIT ?', (MAX_PEERS + 1,)
            ).fetchall()
    except sqlite3.Error as exc:
        raise AdapterError('snapshot_read_failed') from exc

    if len(rows) > MAX_PEERS:
        raise AdapterError('snapshot_too_many_peers')
    devices: list[dict[str, Any]] = []
    seen: set[str] = set()
    for (identifier,) in rows:
        if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 100:
            raise AdapterError('snapshot_invalid_peer_id')
        if identifier in seen:
            raise AdapterError('snapshot_duplicate_peer_id')
        seen.add(identifier)
        devices.append({
            'device_id': identifier,
            'display_name': identifier,
            'platform': None,
            'presence': 'UNKNOWN',
            'enrollment': 'UNKNOWN',
            'last_seen_at': None,
            'group': None,
            'client_version': None,
        })

    return {
        'schema': SCHEMA,
        'state': 'SNAPSHOT_ONLY',
        'source': SOURCE,
        'mode': 'sqlite_snapshot',
        'observed_at': None,
        'snapshot_read_at': read_at or datetime.now(timezone.utc).isoformat(),
        'devices': devices,
        'counts': {
            'total': len(devices),
            'online': 0,
            'offline': 0,
            'unknown': len(devices),
        },
    }


def local_registry_inventory(path: Path, *, read_at: str | None = None) -> dict[str, Any]:
    """Read ONLY registered peer IDs from a caller-selected live SQLite file.

    Unlike an immutable offline snapshot this uses SQLite mode=ro, so WAL
    transactions are visible. It is a one-time registry read, NOT a liveness
    check, remote-control channel, database export, or persistent service.
    No live DB contents beyond peer.id are included in the returned object.
    """
    try:
        full = path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AdapterError('registry_missing') from exc
    if not full.is_file():
        raise AdapterError('registry_not_file')

    uri = full.as_uri() + '?mode=ro'
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=1)) as conn:
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA trusted_schema=OFF')
            conn.execute('BEGIN')
            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='peer'"
            ).fetchone()
            if not table:
                raise AdapterError('registry_schema_mismatch')
            columns = {row[1] for row in conn.execute('PRAGMA table_info(peer)')}
            if not {'id', 'created_at'}.issubset(columns):
                raise AdapterError('registry_schema_mismatch')
            ids = conn.execute(
                'SELECT id FROM peer ORDER BY id LIMIT ?', (MAX_PEERS + 1,)
            ).fetchall()
    except sqlite3.Error as exc:
        raise AdapterError('registry_read_failed') from exc

    if len(ids) > MAX_PEERS:
        raise AdapterError('registry_too_many_peers')
    devices: list[dict[str, Any]] = []
    seen: set[str] = set()
    for (identifier,) in ids:
        if (not isinstance(identifier, str) or not identifier.strip() or
                len(identifier) > 100):
            raise AdapterError('registry_invalid_peer_id')
        if identifier in seen:
            raise AdapterError('registry_duplicate_peer_id')
        seen.add(identifier)
        devices.append({
            'device_id': identifier,
            'display_name': identifier,
            'platform': None,
            'presence': 'UNKNOWN',
            'enrollment': 'UNKNOWN',
            'last_seen_at': None,
            'group': None,
            'client_version': None,
        })
    return {
        'schema': SCHEMA,
        'state': 'REGISTRY_READ_ONLY',
        'source': 'rustdesk_oss_local_registry',
        'mode': 'explicit_read_only_sqlite',
        'observed_at': None,
        'registry_read_at': read_at or datetime.now(timezone.utc).isoformat(),
        'devices': devices,
        'counts': {
            'total': len(devices), 'online': 0, 'offline': 0,
            'unknown': len(devices),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='RustDesk OSS offline snapshot inventory (never live)'
    )
    parser.add_argument('--snapshot', type=Path, required=True,
                        help='Path to a completed, offline SQLite copy; NOT hbbs live DB')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(snapshot_inventory(args.snapshot), ensure_ascii=False,
                         sort_keys=True, indent=2))
        return 0
    except (AdapterError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, AdapterError) else 'snapshot_unavailable'
        print(json.dumps({
            'schema': SCHEMA,
            'state': 'UNAVAILABLE',
            'reason': reason,
            'devices': [],
        }, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
