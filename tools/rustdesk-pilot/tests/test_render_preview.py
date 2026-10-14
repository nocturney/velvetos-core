"""Offline preview safety and output contract tests (no browser/network)."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_preview as preview
import cortendesk_inventory as adapter


class JSONScript(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.found = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'embedded-inventory':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.found.append(data)


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path(__file__).resolve().parents[1] / 'fixtures' / 'devices-page1.json'
        self.data = adapter.fixture_inventory(self.fixture, observed_at='2026-10-14T13:00:00Z')

    def test_demo_page_contains_valid_embedded_data(self):
        html = preview.render_html(self.data)
        self.assertIn('lang="he" dir="rtl"', html)
        self.assertIn('RESEARCH · NO LIVE CONTROL', html)
        self.assertIn("connect-src 'none'", html)
        self.assertNotIn(preview.MARKER, html)
        parser = JSONScript()
        parser.feed(html)
        self.assertEqual(len(parser.found), 1)
        decoded = json.loads(parser.found[0])
        self.assertEqual(decoded['state'], 'FIXTURE_ONLY')
        self.assertEqual(decoded['counts']['total'], 3)
        self.assertEqual(decoded['devices'][0]['device_id'], self.data['devices'][0]['device_id'])

    def test_snapshot_without_real_presence_is_supported(self):
        data = dict(self.data)
        data['state'] = 'SNAPSHOT_ONLY'
        data['source'] = 'rustdesk_oss_peer_snapshot'
        data['devices'] = []
        data['counts'] = {'total': 0, 'online': 0, 'offline': 0, 'unknown': 0}
        html = preview.render_html(data)
        self.assertIn('SNAPSHOT_ONLY', html)
        self.assertIn('SQLite Snapshot / RustDesk OSS', html)
        self.assertNotIn('src="', html)  # no image/font/network asset references

    def test_live_credentialed_state_is_never_rendered(self):
        data = dict(self.data)
        data['state'] = 'CONNECTED'
        with self.assertRaisesRegex(preview.PreviewError, 'live_data_not_permitted_in_preview'):
            preview.render_html(data)

    def test_invalid_counts_rejected(self):
        data = dict(self.data)
        data['counts'] = {'total': 4}
        with self.assertRaisesRegex(preview.PreviewError, 'invalid_preview_inventory'):
            preview.render_html(data)

    def test_html_injection_in_device_id_is_only_json_text(self):
        data = json.loads(json.dumps(self.data))
        attack = '</script><script>window.evil=1</script>'
        data['devices'][0]['device_id'] = attack
        data['devices'][0]['display_name'] = '<img src=x onerror=alert(1)>'
        html = preview.render_html(data)
        self.assertNotIn(attack, html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('\\u003c/script', html.lower())
        parser = JSONScript()
        parser.feed(html)
        decoded = json.loads(''.join(parser.found))
        self.assertEqual(decoded['devices'][0]['device_id'], attack)

    def test_output_generation_rejects_overwrite(self):
        with TemporaryDirectory() as folder:
            output = Path(folder) / 'demo.html'
            self.assertEqual(preview.main(['--fixture', str(self.fixture),
                                           '--output', str(output)]), 0)
            html = output.read_text(encoding='utf-8')
            self.assertIn('FIXTURE_ONLY', html)
            self.assertEqual(preview.main(['--fixture', str(self.fixture),
                                           '--output', str(output)]), 2)
            self.assertEqual(output.read_text(encoding='utf-8'), html)

    def test_output_missing_fixture_reports_failure(self):
        with TemporaryDirectory() as folder:
            out = Path(folder) / 'absent.html'
            src = Path(folder) / 'absent-fixture.json'
            self.assertEqual(preview.main(['--fixture', str(src),
                                           '--output', str(out)]), 2)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
