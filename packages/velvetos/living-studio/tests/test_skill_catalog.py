"""Regression vectors for the single, derived Skill discovery used by vfmem and Living Studio."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from vf_skill_catalog import audit, compare, discover, get_skill, route, search

ROOT = Path(__file__).resolve().parents[4]


class CatalogTests(unittest.TestCase):
    def test_hebrew_maqaf_splits_ui_terms_for_both_routers(self):
        from vfmem import _tokens as memory_tokens
        from vf_skill_catalog import _tokens as catalog_tokens
        ui = "\u05de\u05de\u05e9\u05e7"
        who = "\u05de\u05e9\u05ea\u05de\u05e9"
        phrase = ui + "\u05be" + who
        self.assertIn("ui", catalog_tokens(phrase))
        self.assertEqual(memory_tokens(phrase), {ui, who})
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            skill = root / ".cursor" / "skills" / "compound" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: compound\ndescription: " + phrase +
                             "\n---\n", encoding="utf-8")
            self.assertEqual(search(ui, root)[0]["id"], "compound")

    def test_crlf_frontmatter_preserves_windows_skill_metadata(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            target = root / ".cursor" / "skills" / "example" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(
                b"---\r\nname: windows-native\r\ndescription: Windows line endings\r\n"
                b"---\r\nNever use for public launch\r\n"
            )
            records = discover(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["name"], "windows-native")
            self.assertEqual(records[0]["description"], "Windows line endings")
            self.assertEqual(records[0]["negative_triggers"], ["Never use for public launch"])

    def test_real_repo_discovery_and_cross_router_agreement(self):
        from vf_living_studio import skill_route, skill_list
        from vfmem import build_graph

        records = discover(ROOT)
        ids = {x["id"] for x in records}
        self.assertEqual(len(ids), len(records))
        self.assertIn("vf-web-ui-quality", ids)
        self.assertIn("vf-cad-design-craft", ids)
        self.assertIn("candidate-skill-plugin87-design-screen", ids)
        self.assertEqual(skill_route("vf-web-ui-quality")["id"], "vf-web-ui-quality")
        self.assertEqual(get_skill("vf-web-ui-quality", ROOT)["id"], "vf-web-ui-quality")
        graph = build_graph(ROOT)
        self.assertIn("Skill:vf-web-ui-quality", graph.nodes)
        self.assertIn("Skill:candidate-skill-plugin87-design-screen", graph.nodes)
        self.assertEqual(skill_list()["catalog_count"], len(records))

    def test_external_is_cataloged_not_installed(self):
        row = get_skill("candidate-skill-plugin87-design-screen", ROOT)
        self.assertEqual(row["status"], "RESEARCHED")
        self.assertEqual(row["license"], "MIT")
        self.assertEqual(row["version"], "2.10.0")
        self.assertIsNone(row["canonical_file"])
        self.assertFalse(row["availability"]["source_in_repository"])
        self.assertEqual(row["availability"]["installed_on_host"], "UNKNOWN")
        self.assertFalse(row["availability"]["execution_ready"])
        self.assertFalse(row["availability"]["executed_and_verified"])
        self.assertTrue(route(row["id"], ROOT)["skills"][0]["requires_admission"])

    def test_no_web_ui_on_instagram_creative(self):
        ids = {x["id"] for x in route("Instagram product post", ROOT)["skills"]}
        self.assertNotIn("vf-web-ui-quality", ids)
        self.assertIn("vf-web-ui-quality", {x["id"] for x in route("web ui dashboard", ROOT)["skills"]})

    def test_non_ui_cad_search(self):
        ids = {x["id"] for x in search("CAD OpenSCAD 3D", ROOT)}
        self.assertIn("vf-cad-design-craft", ids)
        self.assertFalse(any(x.startswith("candidate-skill-plugin87") for x in ids))
        self.assertTrue(any(not x.startswith("candidate-skill-plugin87") for x in ids))

    def test_ui_design_does_not_select_cad_by_word_overlap(self):
        ids = {x["id"] for x in search("ui design accessibility", ROOT)}
        self.assertNotIn("vf-cad-design-craft", ids)
        self.assertIn("candidate-skill-plugin87-design-review", ids)

    def test_proposed_agents_are_real_registry_entries(self):
        from vf_skill_catalog import plan

        row = plan("ui design accessibility", ROOT)
        agency = json.loads((ROOT / ".cursor/agency-agents.json").read_text(encoding="utf-8"))
        valid = {a["slug"] for a in agency["agents"]}
        self.assertTrue(row["agent_candidates"])
        self.assertTrue(all(a["slug"] in valid and (ROOT / a["rule_file"]).is_file()
                            for a in row["agent_candidates"]))
        self.assertEqual(row["execution"], "NOT_STARTED")
        self.assertIsNone(row["receipt"])

    def test_hebrew_cross_language_lookup(self):
        ids = {x["id"] for x in search("עיצוב ממשק נגישות", ROOT)}
        self.assertTrue(any("ui" in x or "a11y" in x for x in ids))

    def test_comparison_preserves_competitors_without_pretend_scores(self):
        result = compare("design review accessibility", ROOT)
        ids = {r["id"] for r in result["candidates"]}
        self.assertIn("candidate-skill-plugin87-design-review", ids)
        self.assertGreaterEqual(len(ids), 2)
        self.assertTrue(all(x["quality"] == "NOT_BENCHMARKED" for x in result["candidates"]))

    def test_alias_dedup_and_distinct_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (".cursor", ".agents", ".grok"):
                (root / name / "skills" / "demo").mkdir(parents=True)
            body = "---\nname: demo\ndescription: Make UI components\n---\nBody.\n"
            a = root / ".cursor/skills/demo/SKILL.md"
            b = root / ".agents/skills/demo/SKILL.md"
            c = root / ".grok/skills/demo/SKILL.md"
            a.write_text(body)
            b.write_text(body)
            c.write_text(body.replace("Body.", "A distinct contract."))
            found = discover(root)
            self.assertEqual(len(found), 2)
            self.assertEqual(len([r for r in found if r["alternate_paths"]]), 1)
            self.assertTrue(all("variant_of" in r for r in found))
            self.assertEqual(get_skill("demo", root)["error"], "ambiguous_skill")
            self.assertEqual(len({r["sha256"] for r in found}), 2)

    def test_fixture_negative_trigger_bilingual_and_no_hallucinated_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / ".cursor/skills/ui-gate/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: ui-gate\ndescription: Design UI and test accessibility\n---\n"
                             "# Gate\n\n## Hard stops\n- Do not use for Instagram product posts.\n")
            self.assertEqual(route("Instagram product posts", root)["skills"], [])
            self.assertEqual(route("בדיקות ממשק", root)["skills"][0]["id"], "ui-gate")
            x = audit(root)
            self.assertEqual(x["source_files"], 1)
            self.assertEqual(x["unique_records"], 1)
            self.assertIn("UNVERIFIED", x["host_availability"])


    def test_incremental_index_and_modified_source(self):
        from unittest.mock import patch
        from vf_skill_catalog import catalog, update_index

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            source = root / ".cursor/skills/dummy/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: dummy\ndescription: Test design\n---\nOne.\n")
            index = Path(tmp) / "cache.json"
            initial = update_index(root, index)
            self.assertTrue(initial["updated"])
            self.assertEqual(initial["records"], 1)
            with patch("vf_skill_catalog._index_path", return_value=index):
                before = catalog(root)
                self.assertEqual(before[0]["name"], "dummy")
                self.assertFalse(update_index(root, index)["updated"])
                stat = source.stat()
                source.write_text("---\nname: dummy\ndescription: Test design\n---\nTwo.\n")
                # A malicious/restored mtime and identical byte count must not defeat hash validation.
                os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                self.assertEqual(source.stat().st_size, stat.st_size)
                # Stale derived index is never authoritative on read.
                altered = catalog(root)
                self.assertNotEqual(altered[0]["sha256"], before[0]["sha256"])
                after = update_index(root, index)
                self.assertTrue(after["updated"])
                self.assertEqual(after["changed_hashes"], [".cursor/skills/dummy/SKILL.md"])
                self.assertEqual(catalog(root)[0]["sha256"], altered[0]["sha256"])
                source.unlink()
                removed = update_index(root, index)
                self.assertEqual(removed["removed_sources"], [".cursor/skills/dummy/SKILL.md"])
                self.assertEqual(catalog(root), [])

    def test_host_probe_does_not_claim_executed(self):
        from vf_skill_catalog import host_probe

        row = host_probe()
        self.assertIn("hostname", row)
        self.assertFalse(row["execution_verified"])
        self.assertEqual(row["execution_readiness"], "NOT_ASSESSED")

    def test_nested_synced_claude_and_codex_host_discovery(self):
        from unittest.mock import patch
        from vf_skill_catalog import host_probe

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude = home / ".claude/skills/synced/workspace/pdf/SKILL.md"
            codex = home / ".codex/skills/.system/review-agent/SKILL.md"
            claude.parent.mkdir(parents=True)
            codex.parent.mkdir(parents=True)
            claude.write_text("Portable PDF skill")
            codex.write_text("Portable reviewer skill")
            with patch("vf_skill_catalog.Path.home", return_value=home):
                found = host_probe()
            self.assertEqual(found["source_present_count"], 2)
            self.assertEqual({x["skill"] for x in found["local_skills"]}, {"pdf", "review-agent"})
            self.assertFalse(found["execution_verified"])


    def test_empty_candidate_evidence_and_authority_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "docs/implementation/office-v2/phase2/candidate-registry-v0.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"items": [{
                "category": "EXTERNAL_SKILL", "name": "upstream:fixture",
                "candidate_id": "fixture-candidate", "evidence_refs": [],
                "notes": [], "lifecycle_state": "RESEARCHED",
                "authority_role": "NONE", "capability_tags": ["web-ui"]
            }]}))
            item = get_skill("fixture-candidate", root)
            self.assertEqual(item["source_refs"], [
                "docs/implementation/office-v2/phase2/candidate-registry-v0.json"])
            self.assertEqual(item["authority_role"], "NONE")
            self.assertTrue(route("fixture-candidate", root)["skills"][0]["requires_admission"])

    def test_negative_file_symlink_escaping_root_is_rejected_not_indexed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            canary = Path(outside) / "SKILL.md"
            canary.write_text("---\nname: outside-leak\ndescription: Synthetic canary outside root\n---\nBody.\n")
            link = root / ".cursor/skills/outsider/SKILL.md"
            link.parent.mkdir(parents=True)
            try:
                os.symlink(canary, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertEqual(discover(root), [])
            self.assertEqual(audit(root)["rejected_outside_root"], [".cursor/skills/outsider/SKILL.md"])
            self.assertEqual(audit(root)["unique_records"], 0)

    def test_negative_nested_directory_symlink_escaping_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            inside = root / "packages/vfok/skills/ok/SKILL.md"
            inside.parent.mkdir(parents=True)
            # Bytes, not write_text: Windows text mode writes CRLF, which the LF-only frontmatter parser skips.
            inside.write_bytes(b"---\nname: inrepo-ok\ndescription: In-root control skill\n---\nBody.\n")
            deep = Path(outside) / "deep"
            (deep / "vendor").mkdir(parents=True)
            (deep / "vendor" / "SKILL.md").write_bytes(
                b"---\nname: outside-leak\ndescription: Synthetic canary\n---\nBody.\n")
            (root / ".cursor/skills").mkdir(parents=True)
            try:
                # packages/** is walked with rglob, which does not descend into symlinked directories.
                os.symlink(deep, root / "packages/vfok/nested", target_is_directory=True)
                # .cursor/skills/*/*/SKILL.md does follow a symlinked directory: the nested path must be rejected.
                os.symlink(deep, root / ".cursor/skills/nested", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertEqual([r["name"] for r in discover(root)], ["inrepo-ok"])
            self.assertEqual(audit(root)["rejected_outside_root"], [".cursor/skills/nested/vendor/SKILL.md"])

    def test_negative_host_probe_skill_symlink_leaving_adapter_root_is_rejected(self):
        from unittest.mock import patch
        from vf_skill_catalog import host_probe

        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            home = Path(tmp)
            canary = Path(outside) / "SKILL.md"
            canary.write_text("Synthetic canary outside adapter root")
            link = home / ".cursor/skills/leak/SKILL.md"
            link.parent.mkdir(parents=True)
            try:
                os.symlink(canary, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with patch("vf_skill_catalog.Path.home", return_value=home):
                found = host_probe()
            self.assertEqual(found["local_skills"], [])
            self.assertEqual([x["path"] for x in found["outside_root"]], [str(link)])
            self.assertEqual(found["outside_root"][0]["reason"], "OUTSIDE_SKILL_ROOT")

    def test_ui_source_intake_complete_and_nonexecuting(self):
        from vf_skill_catalog import ui_resources
        items = ui_resources(ROOT)
        self.assertEqual(len(items), 42)
        self.assertEqual(len({r["id"] for r in items}), 42)
        self.assertEqual(len({r["url"] for r in items}), 42)
        groups = {g: len([r for r in items if r["category"] == g])
                  for g in ("skills", "components", "motion", "inspiration", "design_systems")}
        self.assertEqual(groups, {"skills": 1, "components": 18, "motion": 8,
                                  "inspiration": 11, "design_systems": 4})
        self.assertTrue(all(r["installed"] is False and r["stage"] == "DISCOVERED" for r in items))
        self.assertTrue(all(r["usage_rights"]["state"] in
                            {"REVIEW_REQUIRED", "VERIFIED_UPSTREAM_SCOPE_ONLY"} for r in items))
        self.assertNotIn("ui-skills", {x["id"] for x in discover(ROOT)})
        self.assertNotIn("ui-skills", {x["id"] for x in route("ui-skills", ROOT)["skills"]})

    def test_resource_search_stack_compatibility(self):
        from vf_skill_catalog import ui_resource_search
        angular = ui_resource_search("originui-ng", ROOT, stack="Angular")
        self.assertEqual(angular[0]["id"], "originui-ng")
        self.assertEqual(ui_resource_search("originui-ng", ROOT, stack="React"), [])
        self.assertEqual(ui_resource_search("ui-skills", ROOT)[0]["id"], "ui-skills")
        self.assertEqual(ui_resource_search("Lucide", ROOT)[0]["id"], "lucide")
        self.assertTrue(any(r["id"] == "motion" for r in ui_resource_search("motion", ROOT)))

    def test_resource_facets_are_comparable_but_not_preapproved(self):
        from vf_skill_catalog import ui_resources
        result = compare("React components", ROOT)
        self.assertTrue(result["supporting_resources"])
        self.assertTrue(all(r["execution"] == "NOT_APPLICABLE_SOURCE_ONLY"
                            for r in result["supporting_resources"]))
        by_id = {r["id"]: r for r in ui_resources(ROOT)}
        self.assertEqual(by_id["shadcn-ui"]["usage_rights"]["license"], "MIT")
        self.assertEqual(by_id["lottiefiles"]["usage_rights"]["state"],
                         "VERIFIED_UPSTREAM_SCOPE_ONLY")
        self.assertEqual(by_id["gsap"]["usage_rights"]["state"], "REVIEW_REQUIRED")
        self.assertEqual(audit(ROOT)["ui_resources"], 42)
        self.assertEqual(audit(ROOT)["ui_rights_review_required"], 37)

    def test_living_studio_uses_shared_ui_resource_catalog(self):
        from vf_living_studio import skill_list, skill_route, skill_ui_resources, skill_ui_source_search
        listing = skill_list()
        self.assertEqual(listing["ui_resource_count"], 42)
        self.assertEqual(skill_ui_resources()["count"], 42)
        self.assertFalse(skill_ui_resources()["executable"])
        found = skill_ui_source_search("originui-ng", "Angular")
        self.assertEqual(found["results"][0]["id"], "originui-ng")
        self.assertFalse(found["executable"])
        self.assertEqual(skill_route("ui-skills").get("error"), "unknown_skill")

    def test_bad_external_resource_cannot_silently_enter_catalog(self):
        from vf_skill_catalog import UI_SOURCES, ui_resources
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / UI_SOURCES
            src.parent.mkdir(parents=True)
            row = {"id": "valid", "url": "https://example.org", "installed": False,
                   "runtime": "NOT_INSTALLED_OR_VERIFIED", "stage": "DISCOVERED",
                   "usage_rights": {"state": "REVIEW_REQUIRED"}}
            doc = {"schema": "velvetos.ui-ecosystem-source-intake.v1",
                   "source_count": 2, "sources": [row, dict(row)]}
            src.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                ui_resources(root)
            doc["sources"][1]["id"] = "different"
            doc["sources"][1]["url"] = "http://example.org"
            src.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "invalid UI resource URL"):
                ui_resources(root)
            doc["sources"][1]["url"] = "https://example.org/second"
            doc["sources"][1]["stage"] = "PRODUCTION"
            src.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "status"):
                ui_resources(root)

    def test_resource_input_changes_invalidate_derived_index(self):
        from vf_skill_catalog import UI_SOURCES, update_index
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            path = root / UI_SOURCES
            path.parent.mkdir(parents=True)
            example = {"id": "demo", "name": "Demo", "url": "https://example.org",
                       "installed": False, "runtime": "NOT_INSTALLED_OR_VERIFIED",
                       "stage": "DISCOVERED", "category": "components",
                       "usage_rights": {"state": "REVIEW_REQUIRED"}}
            doc = {"schema": "velvetos.ui-ecosystem-source-intake.v1",
                   "source_count": 1, "sources": [example]}
            path.write_text(json.dumps(doc))
            index = Path(tmp) / "index.json"
            self.assertTrue(update_index(root, index)["ui_resources_changed"])
            self.assertFalse(update_index(root, index)["updated"])
            doc["sources"][0]["distinctive"] = "changed source fact"
            path.write_text(json.dumps(doc))
            changed = update_index(root, index)
            self.assertTrue(changed["updated"])
            self.assertTrue(changed["ui_resources_changed"])
            self.assertEqual(changed["ui_resource_count"], 1)


    def _ui_doc(self, root, rows):
        from vf_skill_catalog import UI_SOURCES
        path = root / UI_SOURCES
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema": "velvetos.ui-ecosystem-source-intake.v1",
                                    "source_count": len(rows), "sources": rows}))
        return path

    def test_verified_rights_require_license_and_https_evidence(self):
        from vf_skill_catalog import ui_resources
        base = {"id": "verified", "name": "Verified", "url": "https://example.org", "installed": False,
                "runtime": "NOT_INSTALLED_OR_VERIFIED", "stage": "DISCOVERED", "category": "components",
                "usage_rights": {"state": "VERIFIED_UPSTREAM_SCOPE_ONLY", "license": "MIT",
                                 "evidence_url": "https://example.org/LICENSE"}}
        cases = {
            "nonempty license": ({"license": ""}, "nonempty license"),
            "license missing": ({"license": None}, "nonempty license"),
            "evidence missing": ({"evidence_url": None}, "https evidence_url"),
            "evidence http": ({"evidence_url": "http://example.org/LICENSE"}, "https evidence_url"),
            "evidence relative": ({"evidence_url": "LICENSE"}, "https evidence_url"),
        }
        for label, (override, message) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                row = json.loads(json.dumps(base))
                row["usage_rights"].update(override)
                self._ui_doc(root, [row])
                with self.assertRaisesRegex(ValueError, message):
                    ui_resources(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._ui_doc(root, [base])
            self.assertEqual(len(ui_resources(root)), 1)

    def test_source_only_row_cannot_approve_source_code_integration(self):
        from vf_skill_catalog import ui_resources
        row = {"id": "fit", "name": "Fit", "url": "https://example.org", "installed": False,
               "runtime": "NOT_INSTALLED_OR_VERIFIED", "stage": "DISCOVERED", "category": "components",
               "usage_rights": {"state": "REVIEW_REQUIRED"},
               "slicebridge_fit": {"role": "SOURCE_REFERENCE_NOT_DROP_IN",
                                   "source_code_integration_approved": True}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._ui_doc(root, [row])
            with self.assertRaisesRegex(ValueError, "cannot approve source code integration"):
                ui_resources(root)
            row["slicebridge_fit"] = "approved"
            self._ui_doc(root, [row])
            with self.assertRaisesRegex(ValueError, "invalid UI resource slicebridge_fit"):
                ui_resources(root)
            row["slicebridge_fit"] = {"role": "RESEARCH_REFERENCE", "source_code_integration_approved": False}
            self._ui_doc(root, [row])
            self.assertEqual(len(ui_resources(root)), 1)
            # slicebridge_fit is optional: a row without it stays valid.
            del row["slicebridge_fit"]
            self._ui_doc(root, [row])
            self.assertEqual(len(ui_resources(root)), 1)

    def test_hebrew_ui_terms_route_to_direct_resource_search(self):
        from vf_skill_catalog import _tokens, ui_resource_search
        self.assertEqual(_tokens("אנימציה"), {"animation"})
        self.assertEqual(_tokens("אייקונים"), {"icon"})
        self.assertEqual(_tokens("רכיבים"), {"components"})
        self.assertEqual(_tokens("ממשקי משתמש"), {"ui", "user"})
        # Prefixed forms map only through their bare known term; unrelated words keep their spelling.
        self.assertEqual(_tokens("באנימציה"), {"animation"})
        self.assertEqual(_tokens("לאייקונים"), {"icon"})
        self.assertEqual(_tokens("ולרכיבים"), {"components"})
        self.assertEqual(_tokens("כבדיקות"), {"test"})
        self.assertEqual({r["id"] for r in ui_resource_search("אנימציה", ROOT)} & {"gsap", "motion", "lottiefiles"},
                         {"gsap", "motion", "lottiefiles"})
        icons = [r["id"] for r in ui_resource_search("אייקונים", ROOT, limit=3)]
        self.assertIn("lucide", icons)
        self.assertEqual(ui_resource_search("באייקונים", ROOT), ui_resource_search("אייקונים", ROOT))
        components = {r["id"] for r in ui_resource_search("רכיבים", ROOT, limit=20)}
        self.assertIn("shadcn-ui", components)
        self.assertIn("originui-ng", {r["id"] for r in ui_resource_search("ממשקי משתמש", ROOT, limit=20)})

    def test_invalid_ui_source_degrades_mixed_commands_without_approval(self):
        from vf_skill_catalog import UI_SOURCES, audit, compare, plan, update_index, ui_resource_search, ui_resources
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / ".cursor/skills/web-gate/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: web-gate\ndescription: Design UI and test accessibility\n---\nBody.\n")
            src = root / UI_SOURCES
            src.parent.mkdir(parents=True)
            src.write_text("{not json")
            # UI-specific commands stay fail-closed.
            with self.assertRaises(ValueError):
                ui_resources(root)
            with self.assertRaises(ValueError):
                ui_resource_search("ui", root)
            # Unrelated Skill commands still answer, with explicit degradation metadata.
            self.assertEqual(search("ui accessibility", root)[0]["id"], "web-gate")
            self.assertEqual(route("web-gate", root)["skills"][0]["id"], "web-gate")
            found = compare("ui accessibility", root)
            self.assertEqual(found["supporting_resources"], [])
            self.assertIsInstance(found["ui_resources_error"], str)
            planned = plan("ui accessibility", root)
            self.assertEqual(planned["ui_resource_suggestions"], [])
            self.assertIsInstance(planned["ui_resources_error"], str)
            audited = audit(root)
            self.assertEqual(audited["ui_resources"], 0)
            self.assertIsInstance(audited["ui_resources_error"], str)
            self.assertEqual(audited["unique_records"], 1)
            index = Path(tmp) / "index.json"
            result = update_index(root, index)
            self.assertIsInstance(result["ui_resources_error"], str)
            self.assertEqual(result["ui_resource_count"], 0)
            self.assertEqual(json.loads(index.read_text())["ui_resources_error"], result["ui_resources_error"])

    def test_negative_ui_source_symlink_outside_root_is_rejected(self):
        from vf_skill_catalog import UI_SOURCES, audit, ui_resources, update_index
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_doc = Path(outside) / "ui.json"
            outside_doc.write_text(json.dumps({"schema": "velvetos.ui-ecosystem-source-intake.v1",
                                               "source_count": 0, "sources": []}))
            src = root / UI_SOURCES
            src.parent.mkdir(parents=True)
            try:
                os.symlink(outside_doc, src)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "inside the root"):
                ui_resources(root)
            self.assertIn("inside the root", update_index(root, Path(tmp) / "index.json")["ui_resources_error"])
            self.assertIn("inside the root", audit(root)["ui_resources_error"])
            self.assertEqual(audit(root)["ui_resources"], 0)
            src.unlink()
            # Dangling links fail closed too, never silently reading as an absent source.
            os.symlink(Path(outside) / "missing.json", src)
            with self.assertRaises(ValueError):
                ui_resources(root)


if __name__ == "__main__":
    unittest.main()
