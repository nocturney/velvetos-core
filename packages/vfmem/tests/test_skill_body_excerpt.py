"""Regression: body-only words in a repository Skill stay searchable; external candidates stay unbodied.

Synthetic temporary roots only. The real repository is never mutated.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import vfmem  # noqa: E402

BODY_TOKEN = "quillfarrow"
TAIL_TOKEN = "tailmarker"
OUTSIDE_TOKEN = "outsidebeacon"
GENERIC = "Generic helper for routine checks."


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _skill_md(name: str, description: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"


class SkillBodyExcerptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.outside = Path(self._tmp.name) / "outside"
        self.root.mkdir()
        self.outside.mkdir()

        desk = self.root.parent / "desk.json"
        _write(desk, json.dumps({"tools": {}, "desk": [], "seats": [], "skills": [], "pipeline": []}))
        _write(self.root / "packages" / "manifest.json", json.dumps({"packs": []}))
        _write(self.root / ".cursor" / "agency-agents.json", json.dumps({"agents": []}))
        _write(self.root / "packages" / "vfmem" / "catalog.json", json.dumps({"adrs": [], "routes": []}))

        # Body token sits inside the 800-char excerpt; tail token sits past it.
        filler = "Routine words. " * 60
        body = f"Use the {BODY_TOKEN} procedure for checks.\n{filler}\n{TAIL_TOKEN} appears only far below."
        _write(self.root / ".cursor" / "skills" / "synth-body-probe" / "SKILL.md",
               _skill_md("synth-body-probe", GENERIC, body))

        # Same name and identical bytes under two source roots: one identity, alias preserved.
        alias = _skill_md("synth-alias", GENERIC, f"Alias body {BODY_TOKEN}.")
        _write(self.root / ".cursor" / "skills" / "synth-alias" / "SKILL.md", alias)
        _write(self.root / ".claude" / "skills" / "synth-alias" / "SKILL.md", alias)

        # Symlink escaping the root: must never be read into graph text.
        outside_file = self.outside / "SKILL.md"
        _write(outside_file, f"---\nname: synth-escape\ndescription: {GENERIC}\n---\n\n{OUTSIDE_TOKEN}\n")
        escape_dir = self.root / ".cursor" / "skills" / "synth-escape"
        escape_dir.mkdir(parents=True)
        self._symlink_ok = True
        try:
            os.symlink(outside_file, escape_dir / "SKILL.md")
        except (OSError, NotImplementedError):
            self._symlink_ok = False

        # External candidate: metadata only, never a repository body.
        registry = self.root / "docs" / "implementation" / "office-v2" / "phase2" / "candidate-registry-v0.json"
        _write(registry, json.dumps({"items": [{
            "candidate_id": "candidate-synth-external",
            "name": "vendor:synth-external",
            "category": "EXTERNAL_SKILL",
            "lifecycle_state": "RESEARCHED",
            "authority_role": "NONE",
            "evidence_refs": ["https://example.invalid/blob/main/SKILL.md"],
            "notes": [f"DESCRIPTION: {GENERIC}"],
        }]}))

        self._patch = mock.patch.object(vfmem, "resolve_surface", lambda *a, **k: desk)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def _skill_nodes(self, graph):
        return [n for n in graph.nodes.values() if n.label == "Skill"]

    def test_repository_body_word_is_searchable(self):
        graph = vfmem.build_graph(self.root)
        hits = [n.id for _, n in vfmem.search(graph, BODY_TOKEN, labels=["Skill"])]
        self.assertIn("Skill:synth-body-probe", hits)

    def test_excerpt_is_bounded(self):
        graph = vfmem.build_graph(self.root)
        node = graph.nodes["Skill:synth-body-probe"]
        self.assertIn(BODY_TOKEN, node.text)
        self.assertNotIn(TAIL_TOKEN, node.text)

    def test_alias_dedup_preserved(self):
        graph = vfmem.build_graph(self.root)
        aliases = [n for n in self._skill_nodes(graph) if n.name == "synth-alias"]
        self.assertEqual(len(aliases), 1)
        self.assertEqual(aliases[0].props["path"], ".cursor/skills/synth-alias/SKILL.md")
        self.assertIn(BODY_TOKEN, aliases[0].text)

    def test_outside_root_symlink_body_never_enters_graph(self):
        if not self._symlink_ok:
            self.skipTest("symlinks unavailable on this host")
        graph = vfmem.build_graph(self.root)
        for node in self._skill_nodes(graph):
            self.assertNotIn(OUTSIDE_TOKEN, node.text)
        self.assertEqual(vfmem.search(graph, OUTSIDE_TOKEN, labels=["Skill"]), [])

    def test_external_candidate_is_description_only_and_not_run_ready(self):
        graph = vfmem.build_graph(self.root)
        node = graph.nodes["Skill:candidate-synth-external"]
        self.assertEqual(node.props["origin"], "EXTERNAL_CANDIDATE")
        self.assertEqual(node.text, f"candidate-synth-external {GENERIC}")
        self.assertNotIn(BODY_TOKEN, node.text)
        from vf_skill_catalog import catalog
        record = next(x for x in catalog(self.root) if x["id"] == "candidate-synth-external")
        self.assertFalse(record["availability"]["execution_ready"])
        self.assertFalse(record["availability"]["source_in_repository"])


if __name__ == "__main__":
    unittest.main()
