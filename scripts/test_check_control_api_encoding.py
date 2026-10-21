#!/usr/bin/env python3
"""Regression: check-control-api.py decodes child JSON as strict UTF-8 (Windows cp1252 default)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SENSOR_PATH = ROOT / "scripts" / "check-control-api.py"

_spec = importlib.util.spec_from_file_location("check_control_api", SENSOR_PATH)
sensor = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(sensor)

# U+05DD (ם) encodes to D7 9D in UTF-8; 0x9D is undefined in cp1252 and raised the reported error.
HEBREW_JSON = '{"title": "שלום", "final": "ם"}'


class ChildEncodingTests(unittest.TestCase):
    def test_fixture_reproduces_cp1252_failure_byte(self) -> None:
        raw = HEBREW_JSON.encode("utf-8")
        self.assertIn(b"\x9d", raw)
        with self.assertRaises(UnicodeDecodeError):
            raw.decode("cp1252")

    def test_child_env_forces_utf8_child_streams(self) -> None:
        self.assertEqual(sensor.child_env()["PYTHONIOENCODING"], "utf-8")

    def test_real_child_hebrew_json_round_trips_without_replacement(self) -> None:
        child = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.stdout.write({HEBREW_JSON!r})"],
            capture_output=True,
            env=sensor.child_env(),
        )
        self.assertEqual(child.returncode, 0, child.stderr)
        value = sensor.parse_child_json(child.stdout, "fixture")
        self.assertEqual(value, {"title": "שלום", "final": "ם"})
        self.assertNotIn("�", value["title"])

    def test_snapshot_requests_bytes_not_locale_text(self) -> None:
        fake = subprocess.CompletedProcess(args=[], returncode=0, stdout=HEBREW_JSON.encode("utf-8"), stderr=b"")
        with mock.patch.object(sensor.subprocess, "run", return_value=fake) as run:
            value = sensor.snapshot_projection(sensor.child_env())
        self.assertEqual(value["final"], "ם")
        kwargs = run.call_args.kwargs
        self.assertNotIn("text", kwargs)
        self.assertNotIn("encoding", kwargs)
        self.assertTrue(kwargs.get("capture_output"))

    def test_malformed_utf8_fails_closed_without_replacing(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            sensor.parse_child_json(b'{"t": "\x9d"}', "snapshot")
        self.assertEqual(ctx.exception.code, 1)

    def test_non_json_and_non_object_fail_closed(self) -> None:
        for data in (b"", b"not json", b"[1, 2]"):
            with self.subTest(data=data), self.assertRaises(SystemExit):
                sensor.parse_child_json(data, "snapshot")

    def test_nonzero_snapshot_exit_fails_closed(self) -> None:
        fake = subprocess.CompletedProcess(args=[], returncode=2, stdout=b"", stderr=b"boom \x9d")
        with mock.patch.object(sensor.subprocess, "run", return_value=fake), self.assertRaises(SystemExit):
            sensor.snapshot_projection(sensor.child_env())


if __name__ == "__main__":
    unittest.main()
