"""Loopback-only HTTP transport tests. No external connection or RustDesk target."""
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_inventory as adapter


def envelope(devices, *, current=1, total_pages=1, total=None):
    return {
        'code': 0, 'data': devices, 'current': current,
        'total_pages': total_pages,
        'total': len(devices) if total is None else total,
        'message': '',
    }


@contextmanager
def fake_api(responder):
    """Spawn and fully shut down a localhost-only, ephemeral HTTP test server."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            self.server.seen.append({
                'path': self.path,
                'method': 'GET',
                'authorization': self.headers.get('Authorization'),
                'accept': self.headers.get('Accept'),
            })
            code, headers, body = responder(self.path)
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode('utf-8')
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.send_response(code)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (ConnectionResetError, BrokenPipeError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    server.seen = []
    server.responder = responder
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port), server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


class LiveTransportTests(unittest.TestCase):
    def test_verified_get_and_bearer_header(self):
        example = envelope([{
            'rustdesk_id': 'FIXTURE-LOCAL-001', 'online': True,
            'alias': 'Loopback synthetic', 'status': 'active',
            'last_online_at': '2026-10-14T10:00:00+00:00',
        }])
        with fake_api(lambda _: (200, {'Content-Type': 'application/json'}, example)) as (base, server):
            result = adapter.live_inventory(base, 'synthetic-token',
                                            observed_at='2026-10-14T11:00:00Z')
            self.assertEqual(result['state'], 'CONNECTED')
            self.assertEqual(result['counts']['total'], 1)
            self.assertEqual(result['devices'][0]['last_seen_at'], '2026-10-14T10:00:00+00:00')
            self.assertEqual(server.seen, [{
                'path': '/api/v1/devices?page=1&page_size=100',
                'method': 'GET',
                'authorization': 'Bearer synthetic-token',
                'accept': 'application/json',
            }])
            self.assertNotIn('synthetic-token', json.dumps(result))

    def test_real_http_multi_page_pagination(self):
        def route(path):
            if 'page=1&' in path:
                return 200, {}, envelope([{'rustdesk_id': 'A', 'online': True}],
                                         current=1, total_pages=2, total=2)
            if 'page=2&' in path:
                return 200, {}, envelope([{'rustdesk_id': 'B', 'online': False}],
                                         current=2, total_pages=2, total=2)
            return 404, {}, 'unknown page'
        with fake_api(route) as (base, server):
            data = adapter.live_inventory(base, 'synthetic-token')
            self.assertEqual(data['counts'], {'total': 2, 'online': 1, 'offline': 1, 'unknown': 0})
            self.assertEqual(len(server.seen), 2)

    def test_redirect_not_followed_even_with_bearer(self):
        with fake_api(lambda _: (200, {}, envelope([]))) as (dest, dest_server):
            with fake_api(lambda _: (302, {'Location': dest + '/api/v1/devices'}, b'')) as (source, source_server):
                with self.assertRaisesRegex(adapter.AdapterError, 'request_failed'):
                    adapter.live_inventory(source, 'synthetic-token')
                self.assertEqual(len(source_server.seen), 1)
                self.assertEqual(dest_server.seen, [])

    def test_http_401_is_unavailable_not_empty_success(self):
        with fake_api(lambda _: (401, {'Content-Type': 'application/json'}, {'error': 'Unauthorized'})) as (base, _):
            with self.assertRaisesRegex(adapter.AdapterError, 'request_failed'):
                adapter.live_inventory(base, 'synthetic-token')

    def test_server_error_is_unavailable_not_empty_success(self):
        with fake_api(lambda _: (503, {}, b'service unavailable')) as (base, _):
            with self.assertRaisesRegex(adapter.AdapterError, 'request_failed'):
                adapter.live_inventory(base, 'synthetic-token')

    def test_oversize_body_is_rejected(self):
        payload = b' ' * (adapter.MAX_BODY_BYTES + 1)
        with fake_api(lambda _: (200, {}, payload)) as (base, _):
            with self.assertRaisesRegex(adapter.AdapterError, 'response_too_large'):
                adapter.live_inventory(base, 'synthetic-token')

    def test_json_parse_error_is_unavailable(self):
        with fake_api(lambda _: (200, {}, b'not-json')) as (base, _):
            with self.assertRaisesRegex(adapter.AdapterError, 'invalid_response'):
                adapter.live_inventory(base, 'synthetic-token')

    def test_bogus_boolean_success_is_not_success(self):
        invalid = envelope([])
        invalid['code'] = False  # Python False == 0, but it is not the CortenDesk API success code.
        with fake_api(lambda _: (200, {}, invalid)) as (base, _):
            with self.assertRaisesRegex(adapter.AdapterError, 'upstream_rejected'):
                adapter.live_inventory(base, 'synthetic-token')

    def test_reject_naive_or_corrupted_last_seen_timestamp(self):
        for stamp in ('2026-10-14T15:00:00', 'never', 1234, ''):
            with self.subTest(stamp=stamp), self.assertRaisesRegex(
                adapter.AdapterError, 'invalid_last_seen_at'
            ):
                adapter.normalize_device({'rustdesk_id': 'A', 'last_online_at': stamp})
        self.assertIsNone(adapter.normalize_device({'rustdesk_id': 'A'})['last_seen_at'])


if __name__ == '__main__':
    unittest.main()
