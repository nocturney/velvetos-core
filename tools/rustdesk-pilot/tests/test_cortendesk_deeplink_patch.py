"""Offline tests for pinned, review-only CortenDesk 1.13.2 URL patch."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_deeplink_patch as links


class UriOverlayTests(unittest.TestCase):
    @staticmethod
    def original(variable='$device', count=2):
        lines = ['<html>\n']
        for _ in range(count):
            lines.append('  <a href="rustdesk://{{ ' + variable +
                         '->rustdesk_id }}">Open</a>\n')
        lines.append('</html>\n')
        return ''.join(lines).encode('utf-8')

    def test_patch_preserves_blade_expression_and_path_case(self):
        original = self.original('$device', 2)
        diff, changed, count = links.patch_template(
            'resources/views/livewire/device-list.blade.php', original,
            links.blob_sha(original), 2, '$device'
        )
        self.assertEqual(count, 2)
        self.assertEqual(changed.count(
            'href="rustdesk://connection/new/{{ rawurlencode($device->rustdesk_id) }}"'
        ), 2)
        self.assertNotIn('href="rustdesk://{{', changed)
        self.assertIn('diff --git a/resources/views/livewire/device-list.blade.php', diff)
        self.assertIn('--- a/resources/views/livewire/device-list.blade.php', diff)
        self.assertIn('+++ b/resources/views/livewire/device-list.blade.php', diff)
        self.assertEqual(original, self.original('$device', 2))

    def test_entry_and_session_ids_are_preserved_in_new_uri_path(self):
        for variable in ('$entry', '$s'):
            with self.subTest(variable=variable):
                original = self.original(variable, 1)
                _, changed, _ = links.patch_template(
                    'views/mocked.blade.php', original,
                    links.blob_sha(original), 1, variable
                )
                self.assertIn('rawurlencode(' + variable + '->rustdesk_id)', changed)

    def test_bad_upstream_sha_rejected_before_rewrite(self):
        original = self.original()
        with self.assertRaisesRegex(links.PatchError, 'unexpected_upstream_blob'):
            links.patch_template('x', original, '0' * 40, 2, '$device')

    def test_unexpected_link_count_rejected(self):
        original = self.original()
        with self.assertRaisesRegex(links.PatchError, 'unexpected_legacy_link_contract'):
            links.patch_template('x', original, links.blob_sha(original), 1, '$device')

    def test_wrong_variable_rejected(self):
        original = self.original('$entry', 2)
        with self.assertRaisesRegex(links.PatchError, 'unexpected_legacy_link_contract'):
            links.patch_template('x', original, links.blob_sha(original), 2, '$device')

    def test_mixed_new_and_old_links_rejected(self):
        original = self.original('$device', 1).replace(
            b'</html>\n',
            b'<a href="rustdesk://connection/new/{{ $device->rustdesk_id }}"></a>\n</html>\n'
        )
        with self.assertRaisesRegex(links.PatchError, 'source_already_contains_new_style_links'):
            links.patch_template('x', original, links.blob_sha(original), 1, '$device')

    def test_reject_noncanonical_line_endings(self):
        original = self.original().replace(b'\n', b'\r\n')
        with self.assertRaisesRegex(links.PatchError, 'noncanonical_source_newlines'):
            links.patch_template('x', original, links.blob_sha(original), 2, '$device')

    def test_reject_source_with_too_many_bytes(self):
        original = b'x' * (links.MAX_TEMPLATE_BYTES + 1)
        with self.assertRaisesRegex(links.PatchError, 'source_too_large'):
            links.patch_template('x', original, links.blob_sha(original), 1, '$device')

    def test_end_to_end_patch_report_does_not_modify_any_source(self):
        with TemporaryDirectory() as folder, patch.object(links, 'SOURCES', ()) as ignored:
            root = Path(folder)
            files = [('views/device.blade.php', '$device', 2),
                     ('views/entry.blade.php', '$entry', 1)]
            sources = []
            for filename, variable, count in files:
                path = root / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                original = self.original(variable, count)
                path.write_bytes(original)
                sources.append((filename, links.blob_sha(original), count, variable))
            ignored = sources
            with patch.object(links, 'SOURCES', tuple(sources)):
                diff, report = links.build_patch(root)
                self.assertEqual(report['state'], 'SOURCE_PATCH_VERIFIED_NOT_APPLIED')
                self.assertEqual(report['links'], 3)
                self.assertEqual(report['templates'], 2)
                self.assertFalse(report['source_files_modified'])
                self.assertFalse(report['production_server_modified'])
                self.assertFalse(report['patch_applied'])
                self.assertEqual(diff.count('diff --git a/'), 2)
            for filename, variable, count in files:
                self.assertEqual((root / filename).read_bytes(),
                                 self.original(variable, count))

    def test_exclusive_output_and_no_implicit_apply(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            original = self.original('$device', 1)
            source = root / 'test.blade.php'
            source.write_bytes(original)
            destination = root / 'review-only.patch'
            with patch.object(links, 'SOURCES', (
                ('test.blade.php', links.blob_sha(original), 1, '$device'),
            )), redirect_stdout(StringIO()) as output:
                rc = links.main([
                    '--source-root', str(root),
                    '--patch-output', str(destination),
                ])
                self.assertEqual(rc, 0)
                report = json.loads(output.getvalue())
                self.assertTrue(report['patch_output_created'])
                self.assertFalse(report['patch_applied'])
            self.assertTrue(destination.is_file())
            self.assertEqual(source.read_bytes(), original)
            with patch.object(links, 'SOURCES', (
                ('test.blade.php', links.blob_sha(original), 1, '$device'),
            )), redirect_stdout(StringIO()) as output:
                rc = links.main([
                    '--source-root', str(root),
                    '--patch-output', str(destination),
                ])
                self.assertEqual(rc, 2)
                report = json.loads(output.getvalue())
                self.assertEqual(report['state'], 'REJECTED')
                self.assertEqual(report['reason'], 'patch_write_denied')
            self.assertEqual(source.read_bytes(), original)

    def test_broken_input_never_leaks_path_or_source(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(links, 'SOURCES', (
                ('not-there-private-info.blade.php', '0' * 40, 2, '$device'),
            )), redirect_stdout(StringIO()) as output:
                rc = links.main(['--source-root', str(root)])
            self.assertEqual(rc, 2)
            txt = output.getvalue()
            self.assertNotIn('not-there-private-info', txt)
            self.assertEqual(json.loads(txt)['reason'], 'missing_or_symlinked_source')

    def test_symlink_source_rejected_even_if_target_has_expected_blob(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.blade.php'
            source.write_bytes(self.original())
            link = root / 'shortcut.blade.php'
            try:
                link.symlink_to(source)
            except (NotImplementedError, OSError):
                self.skipTest('symlink privilege unsupported')
            with patch.object(links, 'SOURCES', (
                ('shortcut.blade.php', links.blob_sha(source.read_bytes()), 2, '$device'),
            )):
                with self.assertRaisesRegex(links.PatchError, 'missing_or_symlinked_source'):
                    links.build_patch(root)


if __name__ == '__main__':
    unittest.main()
