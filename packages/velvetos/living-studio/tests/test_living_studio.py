#!/usr/bin/env python3
"""Behavioral tests for Living Studio connective tissue."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))

SPEC = importlib.util.spec_from_file_location(
    "vf_living_studio", ROOT / "scripts" / "vf_living_studio.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class LivingStudioTests(unittest.TestCase):
    def test_registry_has_22_skills(self):
        reg = json.loads((ROOT / "packages/velvetos/living-studio/REGISTRY.json").read_text())
        self.assertEqual(len(reg["skills"]), 22)

    def test_world_model_is_projection(self):
        wm = mod.world_model()
        self.assertEqual(wm["kind"], "velvet-world-model-projection")
        self.assertIn("sourcesOfTruth", wm)
        self.assertNotIn("database", json.dumps(wm).lower())

    def test_pulse_answers_core_questions(self):
        pulse = mod.studio_pulse()
        for key in (
            "what_happening_now",
            "what_moved_since_last",
            "what_stuck",
            "what_requires_christian",
            "what_office_can_solve",
            "ready_to_publish",
            "do_not_do_now",
        ):
            self.assertIn(key, pulse)

    def test_intake_idempotent(self):
        text = "unique living studio idempotency " + next(tempfile._get_candidate_names())
        a = mod.universal_intake("note", text)
        b = mod.universal_intake("note", text)
        self.assertEqual(a["kind"], "note")
        inbox = json.loads((ROOT / "office/control/inbox.json").read_text())
        notes = inbox.get("buckets", {}).get("notes", [])
        hashes = [n.get("textHash") for n in notes if isinstance(n, dict)]
        import hashlib

        th = hashlib.sha256(text.encode()).hexdigest()[:16]
        self.assertEqual(hashes.count(th), 1)

    def test_intake_routes_meeting_to_decisions(self):
        text = "סיכום פגישה: להכין טיוטת תוכן לכדורגל אחרי print.done " + next(
            tempfile._get_candidate_names()
        )
        r = mod.universal_intake("meeting", text)
        self.assertEqual(r["route"]["skill"], "meeting-to-execution")
        self.assertTrue(r.get("decision_id"))

    def test_commercial_qa_blocks_bare_dm_and_ils(self):
        qa = mod.commercial_qa("devil", None, "שלחו DM במחיר 99 ₪ עכשיו")
        self.assertTrue(qa["findings"] or qa["blocked_fields"])
        self.assertTrue("cta" in qa["blocked_fields"] or "sale_price" in qa["blocked_fields"])

    def test_quote_confidence_missing_grams(self):
        qa = mod.commercial_qa("quote-confidence", None, "הצעה ללקוח בלי מספרים")
        self.assertIn("grams", qa["missing_inputs"])

    def test_invisible_work_returns_list(self):
        items = mod.invisible_work(write=False)
        self.assertIsInstance(items, list)

    def test_work_to_story_close_rule(self):
        w = mod.work_to_story()
        self.assertIn("scheduling", w["do_not_close_on"])
        self.assertTrue(any("live verify" in step.lower() for step in w["pipeline"]))

    def test_skill_route_brand_voice(self):
        s = mod.skill_route("brand-voice-guardian")
        self.assertEqual(s["id"], "brand-voice-guardian")
        self.assertIn("velvet-hebrew-copy", json.dumps(s))

    def test_forge_needs_input(self):
        f = mod.one_hour_forge("")
        self.assertEqual(f["status"], "needs_input")

    def test_no_second_decision_journal(self):
        banned = ROOT / "office/control/decision-journal.json"
        self.assertFalse(banned.exists())

    def test_signal_room_normalizes(self):
        room = mod.signal_room(5)
        self.assertEqual(room["kind"], "signal-room")
        self.assertIn("event_contract_count", room)


if __name__ == "__main__":
    unittest.main()
