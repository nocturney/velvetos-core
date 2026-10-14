"""Synthetic SQLite snapshot tests; never touch real RustDesk databases."""
from pathlib import Path
from contextlib import closing
import json
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rustdesk_oss_snapshot as oss
from cortendesk_inventory import AdapterError


def create_sample(path: Path, ids=('DEMO-A', 'DEMO-B')):
    with closing(sqlite3.connect(path)) as db:
        db.execute('CREATE TABLE peer('
                   'guid BLOB PRIMARY KEY NOT NULL, '
                   'id varchar(100) NOT NULL, '
                   'uuid BLOB NOT NULL, pk BLOB NOT NULL, '
                   'created_at datetime NOT NULL DEFAULT(current_timestamp), '
                   'user BLOB, status tinyint, note varchar(300), '
                   'info text NOT NULL)')
        db.executemany(
            'INSERT INTO peer(guid, id, uuid, pk, info) VALUES(?, ?, ?, ?, ?)',
            [(bytes([n % 256]), uid, b'no-read-uuid', b'no-read-pk',
              'no-read-extra') for n, uid in enumerate(ids)]
        )
        db.commit()


class OssSnapshotTests(unittest.TestCase):
    def test_reads_only_registered_ids_no_online_guess(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / 'snapshot.sqlite3'
            create_sample(source, ('PC-2', 'PC-1'))
            result = oss.snapshot_inventory(source, read_at='2026-10-14T13:00:00Z')
            self.assertEqual(result['schema'], 'velvetos.remote_inventory.v0')
            self.assertEqual(result['state'], 'SNAPSHOT_ONLY')
            self.assertEqual(result['source'], 'rustdesk_oss_peer_snapshot')
            self.assertIsNone(result['observed_at'])
            self.assertEqual(result['counts'], {'total': 2, 'online': 0, 'offline': 0, 'unknown': 2})
            self.assertEqual([d['device_id'] for d in result['devices']], ['PC-1', 'PC-2'])
            self.assertTrue(all(d['presence'] == 'UNKNOWN' and
                                d['last_seen_at'] is None and
                                d['platform'] is None for d in result['devices']))
            self.assertNotIn('no-read-', json.dumps(result))

    def test_missing_path_does_not_create_a_database(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'absent.sqlite3'
            with self.assertRaisesRegex(AdapterError, 'snapshot_missing'):
                oss.snapshot_inventory(path)
            self.assertFalse(path.exists())

    def test_refuses_directory_instead_of_database(self):
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(AdapterError, 'snapshot_not_file'):
                oss.snapshot_inventory(Path(folder))

    def test_table_missing_fails_closed(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.sqlite3'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE something_else (id TEXT)')
            with self.assertRaisesRegex(AdapterError, 'snapshot_schema_mismatch'):
                oss.snapshot_inventory(path)

    def test_id_column_without_created_at_not_accepted(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'bad-schema.sqlite3'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE peer (id TEXT)')
            with self.assertRaisesRegex(AdapterError, 'snapshot_schema_mismatch'):
                oss.snapshot_inventory(path)

    def test_view_named_peer_is_not_supported(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'view.sqlite3'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE VIEW peer AS SELECT 1 AS id, 2 AS created_at')
            with self.assertRaisesRegex(AdapterError, 'snapshot_schema_mismatch'):
                oss.snapshot_inventory(path)

    def test_bad_sqlite_bytes_have_safe_error(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'corrupt.sqlite3'
            path.write_bytes(b'NOT A SQLITE DATABASE')
            with self.assertRaisesRegex(AdapterError, 'snapshot_read_failed'):
                oss.snapshot_inventory(path)

    def test_empty_valid_registry_is_not_a_live_offline_fleet(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'no-peers.sqlite3'
            create_sample(path, ())
            result = oss.snapshot_inventory(path)
            self.assertEqual(result['state'], 'SNAPSHOT_ONLY')
            self.assertEqual(result['counts']['total'], 0)

    def test_over_limit_returns_error_not_partial_data(self):
        with TemporaryDirectory() as folder, patch.object(oss, 'MAX_PEERS', 1):
            path = Path(folder) / 'two.sqlite3'
            create_sample(path)
            with self.assertRaisesRegex(AdapterError, 'snapshot_too_many_peers'):
                oss.snapshot_inventory(path)

    def test_duplicate_peer_ids_fail_closed(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'duplicates.sqlite3'
            create_sample(path, ('A', 'A'))
            with self.assertRaisesRegex(AdapterError, 'snapshot_duplicate_peer_id'):
                oss.snapshot_inventory(path)

    def test_invalid_peer_id_fails_closed(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'empty-id.sqlite3'
            create_sample(path, ('',))
            with self.assertRaisesRegex(AdapterError, 'snapshot_invalid_peer_id'):
                oss.snapshot_inventory(path)

    def test_cli_error_never_discloses_private_path(self):
        with TemporaryDirectory() as folder:
            missing = Path(folder) / 'private-secret-path.sqlite3'
            with patch('builtins.print') as output:
                rc = oss.main(['--snapshot', str(missing)])
            self.assertEqual(rc, 2)
            data = json.loads(output.call_args.args[0])
            self.assertEqual(data['state'], 'UNAVAILABLE')
            self.assertEqual(data['devices'], [])
            self.assertNotIn('private-secret', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
