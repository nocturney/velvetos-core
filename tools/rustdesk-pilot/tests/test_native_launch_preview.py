"""Operator-gated one-click RustDesk URI links in a local, private registry report.

No test launches an OS handler, connects to RustDesk, or opens a network socket.
"""
from contextlib import closing, redirect_stdout
from html.parser import HTMLParser
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import cortendesk_inventory as adapter
import render_preview as viewer
import rustdesk_oss_snapshot as registry

NODE = shutil.which('node')
DOM_CHECK = Path(__file__).with_name('native_launch_dom_check.js')


def create_db(path: Path, ids=('MIXED-Case-A1', 'PCLAB-02')):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE peer (id text NOT NULL, created_at text)')
    db.executemany('INSERT INTO peer(id, created_at) VALUES (?,?)',
                   [(i, '2026-10-14T13:00:00Z') for i in ids])
    db.commit()
    return db


class EmbeddedData(HTMLParser):
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

    def handle_data(self, text):
        if self.inside:
            self.found.append(text)


def read_data(page: str):
    parser = EmbeddedData()
    parser.feed(page)
    return json.loads(''.join(parser.found))


class TestNativeLaunchGate(unittest.TestCase):
    def setUp(self):
        self.fixture = BASE / 'fixtures' / 'devices-page1.json'

    def test_synthetic_or_offline_snapshot_never_enable_native_launch(self):
        data = adapter.fixture_inventory(self.fixture)
        with self.assertRaisesRegex(viewer.PreviewError, 'native_connect_requires_private_registry'):
            viewer.render_html(data, enable_native_connect=True)
        data['state'] = 'SNAPSHOT_ONLY'
        with self.assertRaisesRegex(viewer.PreviewError, 'native_connect_requires_private_registry'):
            viewer.render_html(data, enable_native_connect=True, allow_private_registry=True)

    def test_caller_supplied_native_flag_cannot_enable_launch(self):
        data = adapter.fixture_inventory(self.fixture)
        data['native_connect'] = True
        self.assertFalse(read_data(viewer.render_html(data))['native_connect'])

    def test_private_registry_requires_separate_explicit_opt_in(self):
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            with closing(create_db(dbpath)):
                data = registry.local_registry_inventory(dbpath)
                with self.assertRaisesRegex(viewer.PreviewError, 'native_connect_requires_private_registry'):
                    viewer.render_html(data, enable_native_connect=True)
                parsed = read_data(viewer.render_html(data, allow_private_registry=True))
                self.assertFalse(parsed['native_connect'])
                parsed = read_data(viewer.render_html(
                    data, allow_private_registry=True, enable_native_connect=True
                ))
                self.assertTrue(parsed['native_connect'])
                self.assertEqual(parsed['state'], 'REGISTRY_READ_ONLY')
                self.assertTrue(all(row['presence'] == 'UNKNOWN' for row in parsed['devices']))

    def test_flag_requires_real_registry_and_read_permission(self):
        with TemporaryDirectory() as folder:
            out = Path(folder) / 'out.html'
            variants = [
                ['--fixture', str(self.fixture)],
                ['--registry-db', str(Path(folder) / 'not-read.sqlite3')],
            ]
            for spec in variants:
                with self.subTest(source=spec), redirect_stdout(StringIO()) as output:
                    rc = viewer.main(spec + ['--enable-native-connect', '--output', str(out)])
                self.assertEqual(rc, 2)
                self.assertIn('native_connect_requires_private_registry', output.getvalue())
                self.assertFalse(out.exists())

    def test_registry_cli_creates_private_report_with_manual_links_only(self):
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            outfile = Path(folder) / 'private.html'
            with closing(create_db(dbpath)):
                with redirect_stdout(StringIO()) as output:
                    rc = viewer.main([
                        '--registry-db', str(dbpath), '--allow-live-local-read',
                        '--enable-native-connect', '--output', str(outfile),
                    ])
                self.assertEqual(rc, 0)
                self.assertEqual(output.getvalue().strip(),
                                 'PREVIEW_CREATED_NATIVE_LINKS_MANUAL_ONLY')
                self.assertNotIn('MIXED-Case-A1', output.getvalue())
                page = outfile.read_text(encoding='utf-8')
                data = read_data(page)
                self.assertEqual(data['counts']['total'], 2)
                self.assertTrue(data['native_connect'])
                self.assertIn("connect-src 'none'", page)
                self.assertIn('data-manual-native-launch', page)
                self.assertIn('MIXED-Case-A1', json.dumps(data))
                if os.name == 'posix':
                    self.assertEqual(stat.S_IMODE(outfile.stat().st_mode), 0o600)
                self.assertEqual(viewer.main([
                    '--registry-db', str(dbpath), '--allow-live-local-read',
                    '--enable-native-connect', '--output', str(outfile),
                ]), 2)

    def test_bare_registry_mode_remains_read_only(self):
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            outfile = Path(folder) / 'private.html'
            with closing(create_db(dbpath)):
                with redirect_stdout(StringIO()) as output:
                    rc = viewer.main([
                        '--registry-db', str(dbpath),
                        '--allow-live-local-read', '--output', str(outfile)
                    ])
            self.assertEqual(rc, 0)
            self.assertEqual(output.getvalue().strip(),
                             'PREVIEW_CREATED_REGISTRY_READ_ONLY')
            self.assertFalse(read_data(outfile.read_text(encoding='utf-8'))['native_connect'])

    def test_native_preview_stays_outside_git_tree(self):
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            gitroot = Path(folder) / 'repo'
            gitroot.mkdir()
            (gitroot / '.git').mkdir()
            outfile = gitroot / 'private.html'
            with closing(create_db(dbpath)):
                with redirect_stdout(StringIO()) as output:
                    rc = viewer.main([
                        '--registry-db', str(dbpath), '--allow-live-local-read',
                        '--enable-native-connect', '--output', str(outfile),
                    ])
            self.assertEqual(rc, 2)
            self.assertIn('private_registry_output_must_be_outside_git', output.getvalue())
            self.assertFalse(outfile.exists())

    def test_weird_ids_are_escaped_even_in_manual_mode(self):
        malicious = '</script><script>window.evil=true</script>'
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            with closing(create_db(dbpath, (malicious, 'ABC-case-42'))):
                data = registry.local_registry_inventory(dbpath)
                html = viewer.render_html(
                    data, allow_private_registry=True, enable_native_connect=True)
            self.assertNotIn(malicious, html)
            self.assertIn('\\u003c/script', html.lower())
            self.assertEqual(read_data(html)['devices'][0]['device_id'], malicious)

    @unittest.skipUnless(NODE, 'Node.js unavailable for DOM behavior check')
    def test_live_dom_has_one_manual_link_for_each_safe_id(self):
        with TemporaryDirectory() as folder:
            dbpath = Path(folder) / 'reg.sqlite3'
            output = Path(folder) / 'manual.html'
            with closing(create_db(dbpath, (
                'mixedCase-ABC_47', '555-222', 'malicious/path?param=evil',
            ))):
                self.assertEqual(viewer.main([
                    '--registry-db', str(dbpath), '--allow-live-local-read',
                    '--enable-native-connect', '--output', str(output),
                ]), 0)
            result = subprocess.run([NODE, str(DOM_CHECK), str(output)],
                                    capture_output=True, text=True, timeout=6)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('NATIVE_LINK_DOM_OK links=2 manual=true', result.stdout)

    @unittest.skipUnless(NODE, 'Node.js unavailable for DOM behavior check')
    def test_demo_dom_cannot_offer_native_links(self):
        with TemporaryDirectory() as folder:
            out = Path(folder) / 'fixture.html'
            self.assertEqual(viewer.main([
                '--fixture', str(self.fixture), '--output', str(out)
            ]), 0)
            result = subprocess.run([NODE, str(DOM_CHECK), str(out)],
                                    capture_output=True, text=True, timeout=6)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('NATIVE_LINK_DOM_OK links=0 manual=false', result.stdout)


if __name__ == '__main__':
    unittest.main()
