"""One-shot local HTML generator for RustDesk registries and synthetic data.

Not an HTTP server or Control Center integration. Real registered IDs are
accepted only by an explicit, read-only local SQLite query with separate
operator opt-in; presence always stays UNKNOWN. Resulting HTML is offline,
private, and never contains remote-control or network functionality.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cortendesk_inventory import AdapterError, fixture_inventory
from rustdesk_oss_snapshot import snapshot_inventory, local_registry_inventory

MARKER = '__VELVETOS_INVENTORY_JSON__'
TEMPLATE = Path(__file__).resolve().parent / 'preview' / 'template.html'


class PreviewError(ValueError):
    pass


def render_html(inventory: dict, *, allow_private_registry: bool = False) -> str:
    if not isinstance(inventory, dict):
        raise PreviewError('invalid_preview_input')
    allowed = {'FIXTURE_ONLY', 'SNAPSHOT_ONLY'}
    if allow_private_registry:
        allowed.add('REGISTRY_READ_ONLY')
    if inventory.get('state') not in allowed:
        raise PreviewError('live_data_not_permitted_in_preview')
    devices = inventory.get('devices')
    counts = inventory.get('counts')
    if (not isinstance(devices, list) or len(devices) > 1000 or
            not isinstance(counts, dict) or counts.get('total') != len(devices)):
        raise PreviewError('invalid_preview_inventory')
    if inventory.get('state') == 'REGISTRY_READ_ONLY':
        if (counts.get('online') != 0 or counts.get('offline') != 0 or
                counts.get('unknown') != len(devices) or
                not isinstance(inventory.get('registry_read_at'), str) or
                not all(isinstance(device, dict) and
                        device.get('presence') == 'UNKNOWN' and
                        device.get('last_seen_at') is None for device in devices)):
            raise PreviewError('registry_presence_must_be_unknown')
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise PreviewError('invalid_preview_template')
    # JSON inside a script tag must NOT contain literal '<' or '</script>'.
    # Rendering uses textContent only, including for arbitrary device aliases.
    embedded = json.dumps(inventory, ensure_ascii=False, separators=(',', ':'))
    embedded = (embedded.replace('&', '\\u0026').replace('<', '\\u003c')
                .replace('>', '\\u003e').replace('\u2028', '\\u2028')
                .replace('\u2029', '\\u2029'))
    return template.replace(MARKER, embedded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate an offline, read-only RustDesk dashboard preview')
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument('--fixture', type=Path, help='Explicit synthetic fixture JSON')
    sources.add_argument('--snapshot', type=Path, help='Explicit offline OSS SQLite snapshot')
    sources.add_argument('--registry-db', type=Path,
                         help='Explicit path to local RustDesk OSS SQLite registry (read-only)')
    parser.add_argument('--allow-live-local-read', action='store_true',
                        help='Required opt-in for a one-shot real local registry read')
    parser.add_argument('--output', type=Path, required=True, help='New local HTML output path')
    args = parser.parse_args(argv)
    try:
        is_registry = args.registry_db is not None
        if is_registry and not args.allow_live_local_read:
            raise PreviewError('local_registry_requires_explicit_opt_in')
        if args.allow_live_local_read and not is_registry:
            raise PreviewError('local_registry_source_required')
        if is_registry:
            # A real device-ID report must never be created inside any git repo.
            output_dir = args.output.parent.resolve(strict=True)
            for ancestor in (output_dir, *output_dir.parents):
                if (ancestor / '.git').exists():
                    raise PreviewError('private_registry_output_must_be_outside_git')
            inventory = local_registry_inventory(args.registry_db)
        elif args.fixture:
            inventory = fixture_inventory(args.fixture)
        else:
            inventory = snapshot_inventory(args.snapshot)
        html = render_html(inventory, allow_private_registry=is_registry)
        # Create a single new private file. No overwrite and no symlink follow.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(args.output, flags, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(html)
        except BaseException:
            try:
                args.output.unlink()
            except OSError:
                pass
            raise
        print('PREVIEW_CREATED_REGISTRY_READ_ONLY' if is_registry
              else 'PREVIEW_CREATED_NON_LIVE')
        return 0
    except (PreviewError, AdapterError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, (PreviewError, AdapterError)) else 'preview_write_failed'
        print('PREVIEW_UNAVAILABLE:' + reason)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
