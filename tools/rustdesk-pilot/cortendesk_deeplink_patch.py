"""Offline, pinned CortenDesk 1.13.2 native RustDesk URI compatibility patch.

Generates a reviewable unified git diff, NEVER edits upstream source files or
any running server, never installs/runs CortenDesk, never opens a RustDesk
connection. Source file contents are not logged. No network use.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

SCHEMA = 'velvetos.cortendesk.deeplink_patch.v1'
RELEASE = 'v1.13.2'
CLIENT = 'rustdesk-1.5.0'
# Git blob SHAs from marcpope/cortendesk tag v1.13.2, verified by GitHub.
SOURCES: tuple[tuple[str, str, int, str], ...] = (
    ('resources/views/livewire/device-list.blade.php',
     'adbe587c43d7f6f10ba2af0c12cda283e0a440f4', 2, '$device'),
    ('resources/views/livewire/device-detail.blade.php',
     '7e3ce7e8678734501b15e55ac5039590090def44', 1, '$device'),
    ('resources/views/livewire/address-book-manager.blade.php',
     'b1676518bbc9f2cfcb744a7e968340352b3077dd', 2, '$entry'),
    ('resources/views/livewire/active-sessions.blade.php',
     '37adb5e439e06a7d9f1447fc74ce5058b9bbdc1f', 2, '$s'),
)
# Exact Blade interpolation: no arbitrary Blade evaluation.
LEGACY = re.compile(
    r'href="rustdesk://\{\{\s*(\$[a-z]+->rustdesk_id)\s*\}\}"'
)
MAX_TEMPLATE_BYTES = 120_000


class PatchError(ValueError):
    pass


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        ('blob ' + str(len(data)) + '\x00').encode('ascii') + data
    ).hexdigest()


def patch_template(
    path: str, source: bytes, expected_sha: str, expected_count: int,
    expected_variable: str,
) -> tuple[str, str, int]:
    """Verify source identity and rewrite only the expected seven links."""
    if len(source) > MAX_TEMPLATE_BYTES:
        raise PatchError('source_too_large')
    if blob_sha(source) != expected_sha:
        raise PatchError('unexpected_upstream_blob')
    try:
        old = source.decode('utf-8')
    except UnicodeError as exc:
        raise PatchError('non_utf8_source') from exc
    if '\r' in old or not old.endswith('\n'):
        raise PatchError('noncanonical_source_newlines')
    matches = list(LEGACY.finditer(old))
    if (len(matches) != expected_count or
            any(match.group(1) != expected_variable + '->rustdesk_id'
                for match in matches)):
        raise PatchError('unexpected_legacy_link_contract')
    if 'href="rustdesk://connection/new/' in old:
        raise PatchError('source_already_contains_new_style_links')
    modern = LEGACY.sub(
        lambda hit: 'href="rustdesk://connection/new/{{ rawurlencode(' +
        hit.group(1) + ') }}"', old,
    )
    if modern.count('href="rustdesk://connection/new/') != expected_count:
        raise PatchError('modern_link_count_mismatch')
    if 'href="rustdesk://{{' in modern:
        raise PatchError('legacy_link_not_fully_removed')
    if old == modern:
        raise PatchError('no_patch_needed')
    diff = ''.join(difflib.unified_diff(
        old.splitlines(keepends=True), modern.splitlines(keepends=True),
        fromfile='a/' + path, tofile='b/' + path,
        n=3,
    ))
    header = (
        f'diff --git a/{path} b/{path}\n'
        f'index {expected_sha}..{blob_sha(modern.encode("utf-8"))} 100644\n'
    )
    return header + diff, modern, len(matches)


def build_patch(root: Path) -> tuple[str, dict[str, Any]]:
    if not root.is_dir():
        raise PatchError('source_root_missing')
    chunks = []
    counts: dict[str, int] = {}
    # Every source path is a pinned literal, not a caller-supplied path.
    for rel, sha, expected, variable in SOURCES:
        file_path = root / rel
        if file_path.is_symlink() or not file_path.is_file():
            raise PatchError('missing_or_symlinked_source')
        try:
            src = file_path.read_bytes()
        except OSError as exc:
            raise PatchError('source_read_failed') from exc
        patch, _, number = patch_template(rel, src, sha, expected, variable)
        chunks.append(patch)
        counts[rel] = number
    return ''.join(chunks), {
        'schema': SCHEMA,
        'state': 'SOURCE_PATCH_VERIFIED_NOT_APPLIED',
        'upstream_release': RELEASE,
        'supported_client_source': CLIENT,
        'templates': len(counts),
        'links': sum(counts.values()),
        'template_counts': counts,
        'source_files_modified': False,
        'production_server_modified': False,
        'patch_applied': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline CortenDesk URI patch audit')
    parser.add_argument('--source-root', type=Path, required=True,
                        help='Explicit untouched CortenDesk v1.13.2 source tree')
    parser.add_argument('--patch-output', type=Path, help='Create a NEW diff, never overwrite')
    args = parser.parse_args(argv)
    try:
        patch, report = build_patch(args.source_root)
        if args.patch_output is not None:
            # The patch can be reviewed/applied separately later. We NEVER
            # call git apply or edit source files.
            destination = args.patch_output
            if not destination.parent.is_dir() or destination.is_symlink():
                raise PatchError('patch_destination_invalid')
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, 'O_NOFOLLOW'):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(destination, flags, 0o600)
            except OSError as exc:
                raise PatchError('patch_write_denied') from exc
            try:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                    stream.write(patch)
            except BaseException:
                try:
                    destination.unlink()
                except OSError:
                    pass
                raise
            report['patch_output_created'] = True
        else:
            report['patch_output_created'] = False
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0
    except (PatchError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, PatchError) else 'patch_check_unavailable'
        print(json.dumps({'schema': SCHEMA, 'state': 'REJECTED',
                          'reason': reason, 'patch_applied': False}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
