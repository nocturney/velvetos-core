import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_inventory as adapter

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'devices-page1.json'
STAMP = '2026-10-14T11:00:00+00:00'


def envelope(rows, page=1, total_pages=1, total=None):
    return {'code': 0, 'data': rows, 'current': page,
            'total_pages': total_pages, 'total': len(rows) if total is None else total,
            'message': ''}


class TestContract(unittest.TestCase):
    def test_fixture_is_explicitly_non_live(self):
        output = adapter.fixture_inventory(FIXTURE, observed_at=STAMP)
        self.assertEqual(output['state'], 'FIXTURE_ONLY')
        self.assertEqual(output['counts'], {'total': 3, 'online': 1, 'offline': 1, 'unknown': 1})
        self.assertEqual(output['observed_at'], STAMP)
        self.assertEqual([d['display_name'] for d in output['devices']], ['demo-mac', 'Unknown demo', 'Workshop PC'])
        self.assertFalse(any('password' in row for row in output['devices']))

    def test_allow_https_and_only_loopback_http(self):
        self.assertEqual(adapter.validate_origin('https://desk.example.test:8443/'),
                         'https://desk.example.test:8443')
        self.assertEqual(adapter.validate_origin('http://127.0.0.1:8080'),
                         'http://127.0.0.1:8080')
        self.assertEqual(adapter.validate_origin('http://[::1]:8080'),
                         'http://[::1]:8080')
        for bad in ('http://example.org', 'http://localhost.evil.test',
                    'https://u:pwd@example.org', 'https://example.org/other',
                    'https://example.org/?token=abc', 'file:///etc/passwd',
                    'http://[::bad]'):
            with self.subTest(bad=bad), self.assertRaises(adapter.AdapterError):
                adapter.validate_origin(bad)

    def test_live_requires_token_before_transport(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'missing_read_token'):
            adapter.live_inventory('https://example.org', '', fetcher=lambda *x: self.fail('called'))

    def test_live_sends_only_get_devices_pages(self):
        seen = []
        p1 = {'rustdesk_id': 'A', 'online': True, 'status': 'active'}
        p2 = {'rustdesk_id': 'B', 'online': False, 'status': 'active'}
        responses = [envelope([p1], 1, 2, 2), envelope([p2], 2, 2, 2)]
        def fake(url, token, timeout):
            seen.append((url, token, timeout))
            return responses.pop(0)
        out = adapter.live_inventory('https://desk.example.test', 'supersecret', fetcher=fake,
                                     observed_at=STAMP)
        self.assertEqual(out['state'], 'CONNECTED')
        self.assertEqual(out['counts']['total'], 2)
        self.assertEqual(len(seen), 2)
        self.assertEqual([x[0] for x in seen], [
            'https://desk.example.test/api/v1/devices?page=1&page_size=100',
            'https://desk.example.test/api/v1/devices?page=2&page_size=100'])
        self.assertEqual([x[1] for x in seen], ['supersecret', 'supersecret'])
        self.assertNotIn('supersecret', json.dumps(out))

    def test_empty_fleet_is_not_a_failure(self):
        out = adapter.read_inventory(lambda page: envelope([]), source_mode='fixture')
        self.assertEqual(out['counts']['total'], 0)

    def test_refuses_mismatched_total(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'incomplete_inventory'):
            adapter.read_inventory(lambda _: envelope([{'rustdesk_id': 'A'}], total=2),
                                   source_mode='fixture')

    def test_refuses_changed_pagination(self):
        def fake(page):
            return envelope([{'rustdesk_id': str(page)}], page, 2, 2 if page == 1 else 3)
        with self.assertRaisesRegex(adapter.AdapterError, 'pagination_changed'):
            adapter.read_inventory(fake, source_mode='fixture')

    def test_refuses_duplicate_id(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'duplicate_device_id'):
            adapter.read_inventory(lambda _: envelope([
                {'rustdesk_id': 'A'}, {'rustdesk_id': 'A'}]), source_mode='fixture')

    def test_rejects_error_envelope(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'upstream_rejected'):
            adapter.read_inventory(lambda _: {'code': 403, 'message': 'No permission'},
                                   source_mode='fixture')

    def test_rejects_invalid_presence(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'invalid_presence'):
            adapter.normalize_device({'rustdesk_id': 'X', 'online': 'true'})

    def test_rejects_too_many_pages(self):
        with self.assertRaisesRegex(adapter.AdapterError, 'pagination_contract_mismatch'):
            adapter.read_inventory(lambda _: envelope([], 1, 11), source_mode='fixture')

    def test_no_url_no_live_read(self):
        with patch('builtins.print') as output:
            rc = adapter.main(['--base-url', 'https://desk.example.test'])
        self.assertEqual(rc, 2)
        payload = json.loads(output.call_args.args[0])
        self.assertEqual(payload['reason'], 'live_read_not_enabled')
        self.assertEqual(payload['devices'], [])

    def test_never_returns_partial_on_fault(self):
        def fake(page):
            if page == 1:
                return envelope([{'rustdesk_id': 'A'}], 1, 2, 2)
            raise adapter.AdapterError('request_failed')
        with self.assertRaisesRegex(adapter.AdapterError, 'request_failed'):
            adapter.read_inventory(fake, source_mode='live_read_only')


if __name__ == '__main__':
    unittest.main()
