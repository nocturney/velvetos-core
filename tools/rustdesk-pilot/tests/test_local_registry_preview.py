"""Local RustDesk registration viewer: real IDs stay private and presence unknown."""
from contextlib import closing
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_preview as preview
import rustdesk_oss_snapshot as registry
from cortendesk_inventory import AdapterError


def create_registry(path: Path, ids=('R-ID-2', 'R-ID-1')):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE peer ('
               'guid BLOB PRIMARY KEY NOT NULL, '
               'id varchar(100) NOT NULL, '
               'uuid BLOB NOT NULL, pk BLOB NOT NULL, '
               'created_at datetime NOT NULL DEFAULT(current_timestamp), '
               'user BLOB, status tinyint, note varchar(300), '
               'info text NOT NULL)')
    db.executemany(
        'INSERT INTO peer(guid,id,uuid,pk,user,note,info) '
        'VALUES(?,?,?,?,?,?,?)',
        [(bytes([i]), peer_id, b'SECRET_UUID', b'SECRET_PUBLIC_KEY',
          b'SECRET_USER', 'SECRET_NOTE', 'SECRET_INFO')
         for i, peer_id in enumerate(ids)]
    )
    db.commit()
    return db


class JsonTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'embedded-inventory':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.values.append(data)


class LiveRegistryTests(unittest.TestCase):
    def test_one_time_read_sees_wal_and_does_not_expose_sensitive_columns(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'live.sqlite3'
            with closing(create_registry(db_path)):
                mtime = db_path.stat().st_mtime_ns
                inventory = registry.local_registry_inventory(
                    db_path, read_at='2026-10-14T13:00:00+00:00'
                )
                self.assertEqual(db_path.stat().st_mtime_ns, mtime)
            self.assertEqual(inventory['state'], 'REGISTRY_READ_ONLY')
            self.assertIsNone(inventory['observed_at'])
            self.assertEqual(inventory['counts'],
                             {'total': 2, 'online': 0, 'offline': 0, 'unknown': 2})
            self.assertEqual([d['device_id'] for d in inventory['devices']],
                             ['R-ID-1', 'R-ID-2'])
            self.assertTrue(all(d['presence'] == 'UNKNOWN' and
                                d['last_seen_at'] is None and
                                d['platform'] is None for d in inventory['devices']))
            payload = json.dumps(inventory)
            for secret in ('SECRET_UUID', 'SECRET_PUBLIC_KEY',
                           'SECRET_USER', 'SECRET_NOTE', 'SECRET_INFO'):
                self.assertNotIn(secret, payload)

    def test_registry_without_opt_in_rejected_without_creating_file(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'db.sqlite3'
            out = Path(directory) / 'output.html'
            with closing(create_registry(db_path)):
                with patch('builtins.print') as printer:
                    rc = preview.main(['--registry-db', str(db_path), '--output', str(out)])
                self.assertEqual(rc, 2)
                self.assertEqual(printer.call_args.args[0],
                                 'PREVIEW_UNAVAILABLE:local_registry_requires_explicit_opt_in')
                self.assertFalse(out.exists())

    def test_registry_render_requires_explicit_private_flag(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'db.sqlite3'
            with closing(create_registry(db_path)):
                inv = registry.local_registry_inventory(db_path)
            with self.assertRaisesRegex(preview.PreviewError, 'live_data_not_permitted'):
                preview.render_html(inv)
            page = preview.render_html(inv, allow_private_registry=True)
            self.assertIn('REGISTRY_READ_ONLY', page)
            self.assertIn("connect-src 'none'", page)
            self.assertIn('רישום מקומית חד-פעמית', page)
            parser = JsonTagParser()
            parser.feed(page)
            embedded = json.loads(''.join(parser.values))
            self.assertEqual(embedded['devices'][0]['device_id'], 'R-ID-1')

    def test_generated_real_id_html_is_private_and_cannot_overwrite(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'db.sqlite3'
            output = Path(directory) / 'private.html'
            with closing(create_registry(db_path)):
                with patch('builtins.print') as printer:
                    args = ['--registry-db', str(db_path),
                            '--allow-live-local-read', '--output', str(output)]
                    self.assertEqual(preview.main(args), 0)
                    self.assertEqual(printer.call_args.args[0],
                                     'PREVIEW_CREATED_REGISTRY_READ_ONLY')
                    self.assertEqual(preview.main(args), 2)
            html = output.read_text(encoding='utf-8')
            self.assertIn('REGISTRY_READ_ONLY', html)
            self.assertIn('R-ID-1', html)
            self.assertNotIn('SECRET_PUBLIC_KEY', html)
            if os.name == 'posix':
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

    def test_refuse_sensitive_output_under_git_tree(self):
        with TemporaryDirectory() as directory:
            git_dir = Path(directory) / 'repo'
            git_dir.mkdir()
            (git_dir / '.git').mkdir()
            db_path = Path(directory) / 'db.sqlite3'
            out = git_dir / 'private.html'
            with closing(create_registry(db_path)):
                with patch('builtins.print') as printer:
                    rc = preview.main(['--registry-db', str(db_path),
                                       '--allow-live-local-read', '--output', str(out)])
            self.assertEqual(rc, 2)
            self.assertEqual(printer.call_args.args[0],
                             'PREVIEW_UNAVAILABLE:private_registry_output_must_be_outside_git')
            self.assertFalse(out.exists())

    def test_no_credentialed_api_data_accepted_as_live_registry(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'db.sqlite3'
            with closing(create_registry(db_path)):
                inv = registry.local_registry_inventory(db_path)
            inv['devices'][0]['presence'] = 'ONLINE'
            inv['counts']['online'] = 1
            with self.assertRaisesRegex(preview.PreviewError, 'registry_presence_must_be_unknown'):
                preview.render_html(inv, allow_private_registry=True)

    def test_script_injection_is_escaped_even_with_real_ids(self):
        malicious_id = '</script><script>alert(1)</script>'
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'db.sqlite3'
            with closing(create_registry(db_path, (malicious_id,))):
                inv = registry.local_registry_inventory(db_path)
            html = preview.render_html(inv, allow_private_registry=True)
            self.assertNotIn(malicious_id, html)
            self.assertIn('\\u003c/script', html.lower())
            parser = JsonTagParser()
            parser.feed(html)
            embedded = json.loads(''.join(parser.values))
            self.assertEqual(embedded['devices'][0]['device_id'], malicious_id)

    def test_missing_registry_does_not_create_database(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'not-present.sqlite3'
            with self.assertRaisesRegex(AdapterError, 'registry_missing'):
                registry.local_registry_inventory(db_path)
            self.assertFalse(db_path.exists())

    def test_bad_schema_is_not_a_fake_empty_inventory(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'wrong.sqlite3'
            with closing(sqlite3.connect(db_path)) as db:
                db.execute('CREATE TABLE not_a_peer(id TEXT)')
            with self.assertRaisesRegex(AdapterError, 'registry_schema_mismatch'):
                registry.local_registry_inventory(db_path)

    def test_peer_status_column_is_not_an_online_signal(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'local.sqlite3'
            with closing(create_registry(db_path)) as db:
                db.execute('UPDATE peer SET status=1')
                db.commit()
                inventory = registry.local_registry_inventory(db_path)
            self.assertEqual(inventory['counts']['online'], 0)
            self.assertTrue(all(d['presence'] == 'UNKNOWN'
                                for d in inventory['devices']))

    def test_too_many_registered_ids_fail_closed(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / 'limit.sqlite3'
            with closing(create_registry(db_path)):
                with patch.object(registry, 'MAX_PEERS', 1):
                    with self.assertRaisesRegex(AdapterError, 'registry_too_many_peers'):
                        registry.local_registry_inventory(db_path)


if __name__ == '__main__':
    unittest.main()
