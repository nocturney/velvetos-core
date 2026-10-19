"""Hashed-ID friendly names for RustDesk local registry; no OS protocol launch."""
from contextlib import closing, redirect_stdout
from copy import deepcopy
from html.parser import HTMLParser
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import stat
import sys
from tempfile import TemporaryDirectory
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import local_aliases as aliases
import render_preview as preview
import rustdesk_oss_snapshot as registry


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_db(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE peer (id text NOT NULL, created_at text)")
    db.executemany("INSERT INTO peer(id,created_at) VALUES (?,?)", [
        ("MIXED-Case-01", "2026-10-14T00:00:00Z"),
        ("MiniPc_02", "2026-10-14T00:00:00Z"),
        ("unmapped-003", "2026-10-14T00:00:00Z"),
    ])
    db.commit()
    return db


def write_aliases(path, entries=None):
    if entries is None:
        entries = [
            {"id_sha256": digest("MIXED-Case-01"),
             "display_name": "Chris-3DPC",
             "evidence": "rustdesk_peer_cache_hostname"},
            {"id_sha256": digest("MiniPc_02"),
             "display_name": "Chris-Mini-PC",
             "evidence": "local_cli_get_id"},
        ]
    path.write_text(json.dumps({"schema": aliases.SCHEMA, "entries": entries}),
                    encoding="utf-8")
    if os.name == "posix":
        path.chmod(0o600)


class JSONScript(HTMLParser):
    def __init__(self):
        super().__init__()
        self.enabled = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "embedded-inventory":
            self.enabled = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.enabled = False

    def handle_data(self, data):
        if self.enabled:
            self.parts.append(data)


def read_inventory(html):
    parser = JSONScript()
    parser.feed(html)
    return json.loads("".join(parser.parts))


class LocalAliasTests(unittest.TestCase):
    def test_non_string_evidence_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            write_aliases(path, [{
                "id_sha256": digest("a"), "display_name": "Laptop",
                "evidence": ["local_cli_get_id"],
            }])
            with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_evidence"):
                aliases.load_aliases(path)

    def test_verified_names_resolve_only_on_exact_id_hash(self):
        with TemporaryDirectory() as folder:
            p = Path(folder) / "aliases.json"
            db = Path(folder) / "db.sqlite3"
            write_aliases(p)
            with closing(make_db(db)):
                inv = registry.local_registry_inventory(db)
            original = deepcopy(inv)
            out = aliases.apply_aliases(inv, aliases.load_aliases(p))
        lookup = {d["device_id"]: d for d in out["devices"]}
        self.assertEqual(lookup["MIXED-Case-01"]["display_name"], "Chris-3DPC")
        self.assertEqual(lookup["MiniPc_02"]["display_name"], "Chris-Mini-PC")
        self.assertEqual(lookup["unmapped-003"]["display_name"], "unmapped-003")
        self.assertEqual(lookup["unmapped-003"]["name_source"], "unmatched")
        self.assertEqual(out["named_devices"], 2)
        self.assertEqual(out["unnamed_devices"], 1)
        self.assertEqual(inv, original, "must not mutate original registry")
        for key in ("counts", "state", "source", "registry_read_at"):
            self.assertEqual(inv[key], out[key])
        for before, after in zip(inv["devices"], out["devices"]):
            for key in ("device_id", "presence", "last_seen_at", "platform"):
                self.assertEqual(before[key], after[key])
        self.assertTrue(all(d["presence"] == "UNKNOWN" for d in out["devices"]))

    def test_names_cannot_attach_to_wrong_id_with_different_case(self):
        with TemporaryDirectory() as folder:
            p = Path(folder) / "aliases.json"
            write_aliases(p)
            got = aliases.load_aliases(p)
        self.assertNotIn(digest("mixed-case-01"), got)
        self.assertIn(digest("MIXED-Case-01"), got)

    def test_unknown_digest_does_not_affect_machines(self):
        with TemporaryDirectory() as folder:
            db = Path(folder) / "db.sqlite3"
            with closing(make_db(db)):
                inv = registry.local_registry_inventory(db)
            result = aliases.apply_aliases(inv, {digest("NOT-REGISTERED"): "OtherPC"})
        self.assertEqual(result["named_devices"], 0)
        self.assertEqual(result["unnamed_devices"], 3)
        self.assertTrue(all(d["display_name"] == d["device_id"]
                            for d in result["devices"]))

    def test_duplicate_hash_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            row = {"id_sha256": digest("a"), "display_name": "PC-a",
                   "evidence": "local_cli_get_id"}
            write_aliases(path, [row, {**row, "display_name": "PC-b"}])
            with self.assertRaisesRegex(aliases.LocalAliasError, "ambiguous_alias_mapping"):
                aliases.load_aliases(path)

    def test_duplicate_name_rejected_case_insensitively(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            rows = [
                {"id_sha256": digest("a"), "display_name": "Laptop",
                 "evidence": "local_cli_get_id"},
                {"id_sha256": digest("b"), "display_name": "laptop",
                 "evidence": "local_cli_get_id"},
            ]
            write_aliases(path, rows)
            with self.assertRaisesRegex(aliases.LocalAliasError, "ambiguous_alias_mapping"):
                aliases.load_aliases(path)

    def test_non_hex_hash_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            write_aliases(path, [{
                "id_sha256": "raw-device-id", "display_name": "Laptop",
                "evidence": "local_cli_get_id",
            }])
            with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_hash"):
                aliases.load_aliases(path)

    def test_unverified_evidence_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            write_aliases(path, [{
                "id_sha256": digest("a"), "display_name": "Laptop",
                "evidence": "guessed_from_list_position",
            }])
            with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_evidence"):
                aliases.load_aliases(path)

    def test_script_html_or_control_in_name_rejected(self):
        for name in ("<script>alert(1)</script>", "A\nB", " Laptop "):
            with self.subTest(name=name), TemporaryDirectory() as folder:
                path = Path(folder) / "a.json"
                write_aliases(path, [{
                    "id_sha256": digest("a"), "display_name": name,
                    "evidence": "local_cli_get_id",
                }])
                with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_name"):
                    aliases.load_aliases(path)

    def test_unexpected_fields_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            write_aliases(path, [{
                "id_sha256": digest("a"), "display_name": "Laptop",
                "evidence": "local_cli_get_id", "password": "should-not-be-here",
            }])
            with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_entry"):
                aliases.load_aliases(path)

    def test_aliases_refused_inside_git(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "repo"
            root.mkdir()
            (root / ".git").mkdir()
            path = root / "aliases.json"
            write_aliases(path)
            with self.assertRaisesRegex(aliases.LocalAliasError, "alias_must_be_outside_git"):
                aliases.load_aliases(path)

    def test_symlink_alias_file_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "target.json"
            link = root / "shortcut.json"
            write_aliases(target)
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink privilege unavailable")
            with self.assertRaisesRegex(aliases.LocalAliasError, "alias_symlink_rejected"):
                aliases.load_aliases(link)

    @unittest.skipUnless(os.name == "posix", "POSIX-only file permission gate")
    def test_world_readable_alias_file_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            write_aliases(path)
            path.chmod(0o644)
            with self.assertRaisesRegex(aliases.LocalAliasError, "alias_file_not_private"):
                aliases.load_aliases(path)

    def test_invalid_schema_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "a.json"
            path.write_text(json.dumps({"schema": "old", "entries": []}),
                            encoding="utf-8")
            # POSIX private-file gate is checked *before* schema validation.
            # Make this malformed fixture private so the schema path is tested.
            if os.name == "posix":
                path.chmod(0o600)
            with self.assertRaisesRegex(aliases.LocalAliasError, "invalid_alias_schema"):
                aliases.load_aliases(path)

    def test_invalid_inventory_rejected(self):
        with self.assertRaisesRegex(aliases.LocalAliasError, "aliases_require_local_registry"):
            aliases.apply_aliases({"state": "FIXTURE_ONLY"}, {})

    def test_fixture_alias_cli_rejected_without_output(self):
        with TemporaryDirectory() as folder:
            p = Path(folder) / "aliases.json"
            out = Path(folder) / "preview.html"
            write_aliases(p)
            source = BASE / "fixtures" / "devices-page1.json"
            with redirect_stdout(StringIO()) as stream:
                exit_code = preview.main([
                    "--fixture", str(source), "--aliases-file", str(p), "--output", str(out),
                ])
            self.assertEqual(exit_code, 2)
            self.assertIn("aliases_require_private_registry", stream.getvalue())
            self.assertFalse(out.exists())

    def test_missing_alias_file_fails_closed(self):
        with TemporaryDirectory() as folder:
            db = Path(folder) / "db.sqlite3"
            out = Path(folder) / "report.html"
            with closing(make_db(db)), redirect_stdout(StringIO()) as stream:
                code = preview.main([
                    "--registry-db", str(db), "--allow-live-local-read",
                    "--aliases-file", str(Path(folder) / "missing.json"),
                    "--output", str(out),
                ])
            self.assertEqual(code, 2)
            self.assertIn("alias_file_unavailable", stream.getvalue())
            self.assertFalse(out.exists())

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_named_report_renders_friendly_titles_with_original_uris(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            db, names, out = (root / "db.sqlite3", root / "names.json", root / "named.html")
            write_aliases(names)
            with closing(make_db(db)), redirect_stdout(StringIO()):
                code = preview.main([
                    "--registry-db", str(db), "--allow-live-local-read",
                    "--enable-native-connect", "--aliases-file", str(names),
                    "--output", str(out),
                ])
            self.assertEqual(code, 0)
            js = BASE / "tests" / "native_launch_dom_check.js"
            result = subprocess.run([shutil.which("node"), str(js), str(out)],
                                    capture_output=True, text=True, timeout=8)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("NATIVE_LINK_DOM_OK links=3 manual=true", result.stdout)

    def test_real_report_uses_verified_names_but_preserves_native_ids(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            db = root / "db.sqlite3"
            alias_file = root / "aliases.json"
            out = root / "report.html"
            write_aliases(alias_file)
            with closing(make_db(db)), redirect_stdout(StringIO()) as stream:
                code = preview.main([
                    "--registry-db", str(db), "--allow-live-local-read",
                    "--enable-native-connect",
                    "--aliases-file", str(alias_file), "--output", str(out),
                ])
            self.assertEqual(code, 0)
            self.assertEqual(stream.getvalue().strip(),
                             "PREVIEW_CREATED_NATIVE_LINKS_MANUAL_ONLY")
            html = out.read_text(encoding="utf-8")
            inventory = read_inventory(html)
            self.assertEqual(inventory["named_devices"], 2)
            self.assertEqual(inventory["unnamed_devices"], 1)
            self.assertEqual(inventory["counts"]["unknown"], 3)
            lookup = {d["device_id"]: d for d in inventory["devices"]}
            self.assertEqual(lookup["MIXED-Case-01"]["display_name"], "Chris-3DPC")
            self.assertEqual(lookup["MIXED-Case-01"]["device_id"], "MIXED-Case-01")
            self.assertIn("manual=true", "manual=true" if inventory["native_connect"] else "")
            self.assertIn("connect-src 'none'", html)
            self.assertNotIn("raw-device-id", alias_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
