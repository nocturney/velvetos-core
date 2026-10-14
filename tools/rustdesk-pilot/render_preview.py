"""One-shot, no-network HTML preview generator for synthetic or snapshot data.

This is not an HTTP server and does not attach to VelvetOS Control Center.
Only FIXTURE_ONLY and SNAPSHOT_ONLY inputs may be rendered. The resulting
offline page has no network integrations, no remote-control buttons and an
unambiguous non-live label on every state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cortendesk_inventory import AdapterError, fixture_inventory
from rustdesk_oss_snapshot import snapshot_inventory

MARKER = '__VELVETOS_INVENTORY_JSON__'
TEMPLATE = Path(__file__).resolve().parent / 'preview' / 'template.html'


class PreviewError(ValueError):
    pass


def render_html(inventory: dict) -> str:
    if not isinstance(inventory, dict):
        raise PreviewError('invalid_preview_input')
    if inventory.get('state') not in ('FIXTURE_ONLY', 'SNAPSHOT_ONLY'):
        raise PreviewError('live_data_not_permitted_in_preview')
    devices = inventory.get('devices')
    counts = inventory.get('counts')
    if (not isinstance(devices, list) or len(devices) > 1000 or
            not isinstance(counts, dict) or counts.get('total') != len(devices)):
        raise PreviewError('invalid_preview_inventory')
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
    parser = argparse.ArgumentParser(description='Generate a non-live RustDesk dashboard preview')
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument('--fixture', type=Path, help='Explicit synthetic fixture JSON')
    sources.add_argument('--snapshot', type=Path, help='Explicit offline OSS SQLite snapshot')
    parser.add_argument('--output', type=Path, required=True, help='New local HTML output path')
    args = parser.parse_args(argv)
    try:
        inventory = (fixture_inventory(args.fixture) if args.fixture
                     else snapshot_inventory(args.snapshot))
        html = render_html(inventory)
        # Exclusive creation: never overwrite a potentially existing user file.
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(html)
        print('PREVIEW_CREATED_NON_LIVE')
        return 0
    except (PreviewError, AdapterError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, (PreviewError, AdapterError)) else 'preview_write_failed'
        print('PREVIEW_UNAVAILABLE:' + reason)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
