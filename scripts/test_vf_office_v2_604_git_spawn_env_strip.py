#!/usr/bin/env python3
"""The spawned git env drops parent loader and git-context names.

Live git_subprocess_env() builds a literal and require_git_env() returns
only GIT_ENV_REQUIRED. Each name below has a mutant that copies that one
name from os.environ into the literal and adds it to GIT_ENV_REQUIRED.
The mutant leaks. The live spawn does not. This does not admit.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import vf_office_v2_604_native_git_crash_reconcile_offline as native

STRIPPED = (
    "GIT_ASKPASS",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "DYLD_INSERT_LIBRARIES",
)

_REQUIRED_TAIL = '    "XDG_CONFIG_HOME",\n)\n'
_DICT_TAIL = '        "GIT_COMMITTER_EMAIL": "vf604@example.invalid",\n    })\n'
_CHILD = (
    "import json, os, sys\n"
    "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))\n"
)


def _mutant_source(name):
    source = Path(native.__file__).read_text(encoding="utf-8")
    if source.count(_REQUIRED_TAIL) != 1 or source.count(_DICT_TAIL) != 1:
        raise AssertionError("git env needles drifted")
    if name in source:
        raise AssertionError(name + " is already in the live git module")
    return source.replace(_REQUIRED_TAIL, '    "XDG_CONFIG_HOME",\n    "' + name + '",\n)\n', 1).replace(
        _DICT_TAIL,
        '        "GIT_COMMITTER_EMAIL": "vf604@example.invalid",\n'
        '        "' + name + '": os.environ["' + name + '"],\n    })\n',
        1,
    )


def _load_mutant(name, source):
    root = Path(tempfile.mkdtemp(prefix="vf604-git-strip-"))
    path = root / ("mutant_" + name + ".py")
    path.write_text(source, encoding="utf-8")
    module_name = "vf604_git_strip_mutant_" + name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load " + name + " mutant")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


class GitSpawnEnvStripTests(unittest.TestCase):
    def _pin(self, name):
        self.assertNotIn(name, native.GIT_ENV_REQUIRED)
        canary = "vf604-strip-" + name
        with mock.patch.dict(os.environ, {name: canary}, clear=False):
            built = native.git_subprocess_env()
            closed = native.require_git_env(built)
            self.assertNotIn(name, built)
            self.assertNotIn(name, closed)
            self.assertNotIn(canary, closed.values())
            proc = subprocess.run(
                [sys.executable, "-c", _CHILD],
                env=closed,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            child = json.loads(proc.stdout)
            self.assertNotIn(name, child)
            self.assertEqual(set(child), set(native.GIT_ENV_REQUIRED))
            mutant = _load_mutant(name, _mutant_source(name))
            try:
                leaked = mutant.git_subprocess_env()
            finally:
                sys.modules.pop(mutant.__name__, None)
        self.assertEqual(leaked[name], canary)
        self.assertIn(name, mutant.GIT_ENV_REQUIRED)

    def test_git_askpass_stripped(self):
        self._pin("GIT_ASKPASS")

    def test_git_dir_stripped(self):
        self._pin("GIT_DIR")

    def test_git_work_tree_stripped(self):
        self._pin("GIT_WORK_TREE")

    def test_git_index_file_stripped(self):
        self._pin("GIT_INDEX_FILE")

    def test_git_object_directory_stripped(self):
        self._pin("GIT_OBJECT_DIRECTORY")

    def test_git_alternate_object_directories_stripped(self):
        self._pin("GIT_ALTERNATE_OBJECT_DIRECTORIES")

    def test_ld_preload_stripped(self):
        self._pin("LD_PRELOAD")

    def test_ld_library_path_stripped(self):
        self._pin("LD_LIBRARY_PATH")

    def test_dyld_insert_libraries_stripped(self):
        self._pin("DYLD_INSERT_LIBRARIES")

    def _homes(self):
        root = Path(tempfile.gettempdir())
        return {path for path in root.glob("vf604-git-home-*") if path.is_dir()}

    def _child(self, script):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(native.__file__).resolve().parent)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_import_leaves_no_git_home(self):
        source = Path(native.__file__).read_text(encoding="utf-8")
        self.assertNotIn("\nENV = git_subprocess_env()\n", source)
        before = self._homes()
        proc = self._child(
            "import vf_office_v2_604_native_git_crash_reconcile_offline\n"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._homes(), before)

    def test_git_home_removed_at_exit(self):
        proc = self._child(
            "import vf_office_v2_604_native_git_crash_reconcile_offline as native\n"
            "print(native.git_subprocess_env()['HOME'])\n"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        home = Path(proc.stdout.strip())
        self.assertTrue(home.name.startswith("vf604-git-home-"))
        self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
