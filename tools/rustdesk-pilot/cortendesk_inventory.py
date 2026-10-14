"""Research-only, read-only CortenDesk device inventory adapter for VelvetOS.

No server process, scheduler, configuration write, credential discovery, or
remote-control operation is implemented here. A live read needs opt-in.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SCHEMA = 'velvetos.remote_inventory.v0'
PAGE_SIZE = 100
MAX_PAGES = 10
MAX_BODY_BYTES = 2_000_000


class AdapterError(ValueError):
    """A safe, non-secret adapter error code."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_origin(base_url: str) -> str:
    """Require one HTTPS origin, allowing HTTP only on true loopback."""
    try:
        parsed = urlsplit(base_url)
        host = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise AdapterError('invalid_origin') from exc
    if (not host or parsed.scheme not in ('http', 'https') or
            parsed.username is not None or parsed.password is not None or
            parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise AdapterError('invalid_origin')
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host.lower() == 'localhost'
    if parsed.scheme == 'http' and not loopback:
        raise AdapterError('https_required')
    return urlunsplit((parsed.scheme, parsed.netloc, '', '', ''))


def get_json(url: str, token: str, timeout: float = 5.0) -> dict[str, Any]:
    """One GET only; no redirects, proxy credential leakage, or write methods."""
    req = Request(url, headers={'Accept': 'application/json',
                                'Authorization': 'Bearer ' + token}, method='GET')
    opener = build_opener(ProxyHandler({}), NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as response:
            if response.status != 200:
                raise AdapterError('request_failed')
            body = response.read(MAX_BODY_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise AdapterError('request_failed') from exc
    if len(body) > MAX_BODY_BYTES:
        raise AdapterError('response_too_large')
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeError) as exc:
        raise AdapterError('invalid_response') from exc
    if not isinstance(payload, dict):
        raise AdapterError('invalid_response')
    return payload


def _integer(value: Any) -> bool:
    return type(value) is int


def _nonempty(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _validated_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AdapterError('invalid_last_seen_at')
    stamp = value.strip()
    try:
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError('naive timestamp')
    except (TypeError, ValueError) as exc:
        raise AdapterError('invalid_last_seen_at') from exc
    return stamp


def normalize_device(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise AdapterError('invalid_device')
    device_id = _nonempty(raw.get('rustdesk_id'))
    if not device_id:
        raise AdapterError('missing_device_id')
    online = raw.get('online')
    if online is True:
        presence = 'ONLINE'
    elif online is False:
        presence = 'OFFLINE'
    elif online is None:
        presence = 'UNKNOWN'
    else:
        raise AdapterError('invalid_presence')
    status = raw.get('status')
    enrollment = status if status in ('active', 'pending', 'disabled') else 'unknown'
    group = raw.get('device_group')
    if group is not None and not isinstance(group, dict):
        raise AdapterError('invalid_device_group')
    return {
        'device_id': device_id,
        'display_name': (_nonempty(raw.get('alias')) or
                         _nonempty(raw.get('hostname')) or device_id),
        'platform': _nonempty(raw.get('platform')),
        'presence': presence,
        'enrollment': enrollment.upper(),
        'last_seen_at': _validated_timestamp(raw.get('last_online_at')),
        'group': _nonempty(group.get('name')) if group else None,
        'client_version': _nonempty(raw.get('version')),
    }


def parse_page(payload: Any, expected_page: int) -> tuple[list[Any], int, int]:
    if (not isinstance(payload, dict) or type(payload.get('code')) is not int or payload['code'] != 0):
        raise AdapterError('upstream_rejected')
    rows = payload.get('data')
    current, total_pages, total = (payload.get('current'),
                                   payload.get('total_pages'), payload.get('total'))
    if (not isinstance(rows, list) or not _integer(current) or
            not _integer(total_pages) or not _integer(total) or
            current != expected_page or total_pages < 1 or
            total_pages > MAX_PAGES or total < 0 or len(rows) > PAGE_SIZE):
        raise AdapterError('pagination_contract_mismatch')
    return rows, total_pages, total


def read_inventory(fetch_page: Callable[[int], dict[str, Any]],
                   *, source_mode: str, observed_at: str | None = None) -> dict[str, Any]:
    """Read all pages atomically; never return a misleading partial fleet."""
    rows: list[Any] = []
    pages = 1
    reported_total = 0
    for page in range(1, MAX_PAGES + 1):
        batch, count_pages, count_total = parse_page(fetch_page(page), page)
        if page == 1:
            pages, reported_total = count_pages, count_total
        elif (pages != count_pages or reported_total != count_total):
            raise AdapterError('pagination_changed')
        rows.extend(batch)
        if page == pages:
            break
    if len(rows) != reported_total:
        raise AdapterError('incomplete_inventory')
    devices = [normalize_device(row) for row in rows]
    ids = [d['device_id'] for d in devices]
    if len(set(ids)) != len(ids):
        raise AdapterError('duplicate_device_id')
    devices.sort(key=lambda d: (d['display_name'].casefold(), d['device_id']))
    return {
        'schema': SCHEMA,
        'state': 'FIXTURE_ONLY' if source_mode == 'fixture' else 'CONNECTED',
        'source': 'cortendesk',
        'mode': source_mode,
        'observed_at': observed_at or datetime.now(timezone.utc).isoformat(),
        'devices': devices,
        'counts': {
            'total': len(devices),
            'online': sum(d['presence'] == 'ONLINE' for d in devices),
            'offline': sum(d['presence'] == 'OFFLINE' for d in devices),
            'unknown': sum(d['presence'] == 'UNKNOWN' for d in devices),
        },
    }


def live_inventory(base_url: str, token: str,
                   *, fetcher: Callable[[str, str, float], dict[str, Any]] = get_json,
                   observed_at: str | None = None) -> dict[str, Any]:
    origin = validate_origin(base_url)
    if not token or not token.strip():
        raise AdapterError('missing_read_token')

    def fetch(page: int) -> dict[str, Any]:
        url = origin + '/api/v1/devices?' + urlencode({'page': page, 'page_size': PAGE_SIZE})
        return fetcher(url, token, 5.0)

    return read_inventory(fetch, source_mode='live_read_only', observed_at=observed_at)


def fixture_inventory(path: Path, *, observed_at: str | None = None) -> dict[str, Any]:
    if path.stat().st_size > MAX_BODY_BYTES:
        raise AdapterError('fixture_too_large')
    with path.open('r', encoding='utf-8') as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise AdapterError('invalid_fixture')
    pages = payload.get('pages')
    if not isinstance(pages, list) or not pages:
        raise AdapterError('invalid_fixture')

    def fetch(page: int) -> dict[str, Any]:
        if page > len(pages):
            raise AdapterError('missing_fixture_page')
        return pages[page - 1]

    return read_inventory(fetch, source_mode='fixture', observed_at=observed_at)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Research-only CortenDesk inventory adapter')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--fixture', type=Path, help='Explicit offline fixture, never a live feed')
    mode.add_argument('--base-url', help='CortenDesk HTTPS origin; requires --allow-live-read')
    parser.add_argument('--allow-live-read', action='store_true', help='Explicit opt-in to GET requests')
    parser.add_argument('--token-env', default='CORTENDESK_READ_TOKEN',
                        help='Environment variable storing read-only API token')
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            result = fixture_inventory(args.fixture)
        else:
            if not args.allow_live_read:
                raise AdapterError('live_read_not_enabled')
            result = live_inventory(args.base_url, os.environ.get(args.token_env, ''))
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
        return 0
    except (AdapterError, FileNotFoundError, PermissionError, OSError, ValueError) as exc:
        # Deliberately no raw HTTP exception, response, URL, or token in output.
        code = str(exc) if isinstance(exc, AdapterError) else 'fixture_read_failed'
        print(json.dumps({'schema': SCHEMA, 'state': 'UNAVAILABLE',
                          'reason': code, 'devices': []}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
