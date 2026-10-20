#!/usr/bin/env python3
"""Offline checks for the Office 2.0 standalone smoke helper and its record.

Standard library only. No network, no subprocess, no install. The helper is
imported and its main() is called in-process.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts" / "office2" / "run_standalone_smokes.py"
DOC = ROOT / "docs" / "office2" / "standalone-candidate-tests-2026-10-19.md"
FRAGMENT = ROOT / "changelog.d" / "office2-standalone-candidate-tests.md"
CREWAI_RUNBOOK = "../office-v2/pilot-runbook-crewai.md"
ALLOWED_IMPORTS = {"__future__", "json", "sys", "pathlib"}


def load_helper():
    spec = importlib.util.spec_from_file_location("office2_run_standalone_smokes", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run(module, argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, env or {}, clear=False):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class HelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = load_helper()

    def test_execute_refused_without_env(self):
        code, out, err = run(self.helper, ["--execute"])
        self.assertEqual(code, 2)
        self.assertIn("EXECUTE_UNSUPPORTED", err)
        self.assertEqual(out, "")

    def test_execute_refused_with_old_arming_env(self):
        code, out, err = run(self.helper, ["--execute"], {"OFFICE2_STANDALONE_SMOKE": "1"})
        self.assertEqual(code, 2)
        self.assertIn("EXECUTE_UNSUPPORTED", err)
        self.assertNotIn("guard armed", out + err)

    def test_execute_refused_alongside_json(self):
        code, out, _ = run(self.helper, ["--json", "--execute"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_unknown_argument_refused(self):
        code, out, err = run(self.helper, ["--run"])
        self.assertEqual(code, 2)
        self.assertIn("unknown argument", err)
        self.assertEqual(out, "")

    def test_text_report_states_zero_smokes(self):
        code, out, _ = run(self.helper, [])
        self.assertEqual(code, 0)
        self.assertIn("status: REPORT_ONLY", out)
        self.assertIn("smokes run by this helper: 0", out)
        self.assertIn("author-reported", out)

    def test_json_report(self):
        code, out, _ = run(self.helper, ["--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["status"], "REPORT_ONLY")
        self.assertEqual(data["smokes_run_by_helper"], 0)
        self.assertEqual(data["result_provenance"], "AUTHOR_REPORTED_UNVERIFIED")
        self.assertTrue(data["doc_present"])
        self.assertEqual(data["pins"], list(self.helper.PINS))

    def test_missing_doc_fails_closed(self):
        with mock.patch.object(self.helper, "DOC", ROOT / "does-not-exist.md"):
            code, out, err = run(self.helper, [])
        self.assertEqual(code, 1)
        self.assertIn("missing", err)
        self.assertEqual(out, "")

    def test_socket_connect_untouched(self):
        before = socket.socket.connect
        for argv in ([], ["--json"], ["--execute"]):
            run(self.helper, argv, {"OFFICE2_STANDALONE_SMOKE": "1"})
        self.assertIs(socket.socket.connect, before)

    def test_helper_imports_are_inert(self):
        tree = ast.parse(HELPER.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertLessEqual(names, ALLOWED_IMPORTS)

    def test_helper_has_no_exec_or_env_reads(self):
        tree = ast.parse(HELPER.read_text(encoding="utf-8"))
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
        forbidden = {"environ", "getenv", "exec", "eval", "__import__", "system", "popen", "connect"}
        self.assertFalse(used & forbidden, used & forbidden)


class DocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.helper = load_helper()

    def test_author_reported_status(self):
        self.assertIn("**Evidence status: AUTHOR_REPORTED_UNVERIFIED.**", self.text)
        self.assertIn("## Cloud VM run (author-reported)", self.text)
        result = self.text.split("## Result line", 1)[1]
        self.assertIn("AUTHOR_REPORTED_UNVERIFIED", result)

    def test_guard_claim_is_narrowed(self):
        self.assertIn("does **not** prove egress denial", self.text)
        self.assertNotRegex(self.text, r"(?i)egress (is )?(denied|blocked)\b")

    def test_no_executable_blocks_or_tokens(self):
        self.assertNotIn("```bash", self.text)
        self.assertNotIn("```python", self.text)
        self.assertNotIn("kickoff()", self.text)
        self.assertNotRegex(self.text, r"api_key\s*=")
        self.assertNotIn("<< 'PY'", self.text)

    def test_spare_section_points_at_gated_runbook(self):
        spare = self.text.split("## Spare-machine rows (not run, not authorized)", 1)[1]
        spare = spare.split("## Result line", 1)[0]
        self.assertIn(CREWAI_RUNBOOK, spare)
        self.assertNotIn("pip install", spare)
        self.assertNotIn("curl ", spare)

    def test_every_pip_install_is_pinned_or_marked_unpinned(self):
        for line in self.text.splitlines():
            for cmd in re.findall(r"`pip install[^`]*`", line):
                if "==" not in cmd:
                    self.assertIn("unpinned", line, cmd)

    def test_relative_links_resolve(self):
        for target in re.findall(r"\]\((?!https?://|#)([^)#]+)", self.text):
            self.assertTrue((DOC.parent / target).resolve().is_file(), target)

    def test_spare_anchor_exists(self):
        self.assertIn("(#spare-machine-rows-not-run-not-authorized)", self.text)

    def test_pins_appear_in_doc(self):
        for pin in self.helper.PINS:
            version = re.split(r"==|@| v", pin)[-1]
            self.assertIn(version, self.text, pin)


class FragmentTests(unittest.TestCase):
    def test_fragment_is_utf8_lf_bullets(self):
        raw = FRAGMENT.read_bytes()
        self.assertNotIn(b"\r", raw)
        lines = [line for line in raw.decode("utf-8").splitlines() if line.strip()]
        self.assertTrue(lines)
        for line in lines:
            self.assertTrue(line.startswith("- "), line)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
