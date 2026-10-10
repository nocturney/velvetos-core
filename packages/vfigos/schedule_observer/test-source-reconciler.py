#!/usr/bin/env python3
"""Offline regression suite: fail-closed source discovery and reconciliation."""
import copy
from datetime import datetime, timezone, timedelta
from importlib.machinery import SourceFileLoader
from pathlib import Path
import json
import unittest
import types

ROOT = Path(__file__).resolve().parent
r = SourceFileLoader("source_reconciler", str(ROOT / "source-reconciler.py")).load_module()
REG = json.loads((ROOT / "source-registry.json").read_text(encoding="utf-8"))
NOW = r.parse_time("2026-10-10T13:03:00Z")

def meta(rows, selected=True):
    return {
        "schema": "velvet.meta_planner_reader.scheduled.v3",
        "source": "meta_business_suite_visible_ui",
        "observed_at": "2026-10-10T13:02:54Z",
        "page_url": "https://business.facebook.com/latest/posts/scheduled_posts?business_id=ok",
        "account_expected": "velvets_cloud",
        "scheduled_selected": selected,
        "unique_rows": rows,
    }

def publisher(rows):
    return {
        "schema": "vf.instagram.schedule-snapshot.v1",
        "source": "cloudflare-instagram-publisher",
        "observed_at": "2026-10-10T13:02:57Z",
        "meta_health": {"ok": True, "username": "velvets_cloud"},
        "runtime": {"heartbeat_age_seconds": 30},
        "scheduled": rows,
    }

def row(caption, date="Sat Oct 10, 8:00pm", kind="Photo", boost=False):
    prefix = "Boost\n" if boost else ""
    return f"{caption}\n{kind} ·\nvelvets_cloud\n{prefix}Open Dropdown\n{date}\nPublic"

class ObserverContract(unittest.TestCase):
    def test_missing_is_not_empty(self):
        d = r.reconcile(REG, {}, asof=NOW)
        self.assertEqual(d["counts"]["meta_scheduled_lower_bound"], 0)
        self.assertEqual(d["source_health"][0]["state"], "UNAVAILABLE")
        self.assertEqual(d["source_health"][1]["state"], "UNAVAILABLE")
        self.assertIn("INCOMPLETE_SOURCE_COVERAGE", [a["code"] for a in d["alerts"]])
        self.assertEqual(d["policy"]["external_mutations_performed"], False)

    def test_virtualized_meta_duplicates_and_title(self):
        docs={"meta-business-suite":meta([
            "Title\nDate scheduled\nPrivacy\nStatus",
            row("Gold object", boost=False),
            row("Gold object", boost=True),
            row("Blue object", boost=True)])}
        d = r.reconcile(REG, docs, asof=NOW)
        self.assertEqual(d["counts"]["meta_scheduled_lower_bound"], 2)
        self.assertEqual(d["diagnostics"]["meta-business-suite"]["duplicate_rows"],1)
        self.assertTrue(all(x["source_id"]=="meta-business-suite" for x in d["scheduled"]))
        self.assertEqual(len({x["caption_sha256"] for x in d["scheduled"]}),2)

    def test_meta_tab_unselected_invalid(self):
        d=r.reconcile(REG,{"meta-business-suite":meta([row("object")],False)},asof=NOW)
        self.assertEqual(d["source_health"][0]["state"],"INVALID")
        self.assertEqual(d["counts"]["meta_scheduled_lower_bound"],0)

    def test_wrong_meta_account_invalid(self):
        bad=meta([row("object")])
        bad["account_expected"]="wrong-account"
        d=r.reconcile(REG,{"meta-business-suite":bad},asof=NOW)
        self.assertEqual(d["source_health"][0]["state"],"INVALID")

    def test_stale_meta_fails_visible(self):
        d=r.reconcile(REG,{"meta-business-suite":meta([row("object")])},asof=NOW+timedelta(hours=3))
        self.assertEqual(d["source_health"][0]["state"],"STALE")
        self.assertEqual(d["counts"]["meta_scheduled_lower_bound"],0)

    def test_publisher_empty_and_meta_not_mirrored(self):
        d=r.reconcile(REG,{"meta-business-suite":meta([row("object")]),"cloudflare-publisher":publisher([])},asof=NOW)
        self.assertEqual(d["counts"]["cloudflare_scheduled"],0)
        self.assertEqual(d["source_health"][1]["state"],"EMPTY")
        self.assertIn("EXTERNAL_SCHEDULES_NOT_IN_CANONICAL_QUEUE",[a["code"] for a in d["alerts"]])

    def test_publisher_stale_does_not_prove_gap(self):
        stale=publisher([])
        stale["observed_at"]="2026-10-10T12:00:00Z"
        d=r.reconcile(REG,{"meta-business-suite":meta([row("object")]),"cloudflare-publisher":stale},asof=NOW)
        self.assertNotIn("EXTERNAL_SCHEDULES_NOT_IN_CANONICAL_QUEUE",[a["code"] for a in d["alerts"]])
        self.assertEqual(d["source_health"][1]["state"],"STALE")

    def test_publisher_health_guard(self):
        p=publisher([])
        p["runtime"]["heartbeat_age_seconds"]=200
        d=r.reconcile(REG,{"cloudflare-publisher":p},asof=NOW)
        self.assertEqual(d["source_health"][1]["state"],"INVALID")

    def test_calendar_mirror_drift(self):
        p=publisher([{
            "publication_id":"job-42","scheduled_at":"2026-10-11T17:00:00Z",
            "title":"test","content_profile":"photo","status":"scheduled"
        }])
        cal={"schema":"velvet.google_calendar.instagram_snapshot.v1",
             "observed_at":"2026-10-10T13:02:50Z","events":[]}
        d=r.reconcile(REG,{"cloudflare-publisher":p,"google-calendar-mirror":cal},asof=NOW)
        self.assertIn("CALENDAR_MIRROR_MISSING_PUBLISHER_JOBS",[x["code"] for x in d["alerts"]])

    def test_graph_published_never_scheduled(self):
        graph={"schema":"velvet.instagram_graph.media_snapshot.v1",
               "observed_at":"2026-10-10T13:02:56Z",
               "media":[{"id":"123","timestamp":"2026-10-01T12:00:00+0000","permalink":"https://www.instagram.com/p/abc/"}]}
        d=r.reconcile(REG,{"instagram-graph":graph},asof=NOW)
        self.assertEqual(d["counts"]["graph_published"],1)
        self.assertEqual(d["counts"]["observed_scheduled"],0)

    def test_dst_israel_transition(self):
        before=r.parse_meta_date("Sat Oct 24, 8:00pm",NOW,"Asia/Jerusalem")
        after=r.parse_meta_date("Mon Oct 26, 8:00pm",NOW,"Asia/Jerusalem")
        self.assertEqual(before,"2026-10-24T17:00:00Z")
        self.assertEqual(after,"2026-10-26T18:00:00Z")

    def test_side_effect_policy_fail_closed(self):
        bad=copy.deepcopy(REG)
        bad["policy"]["allow_side_effects"]=True
        with self.assertRaises(ValueError):
            r.reconcile(bad,{},asof=NOW)

    def test_approved_external_provider_extensible(self):
        registry=copy.deepcopy(REG)
        ext=next(s for s in registry["sources"] if s["id"]=="other-approved-provider")
        ext["active"]=True
        snapshot={
            "schema":"velvet.read_source_snapshot.v1",
            "observed_at":"2026-10-10T13:02:54Z",
            "source_id":"other-approved-provider",
            "scheduled":[{"native_id":"ext-123","scheduled_at":"2026-10-11T17:00:00Z",
                          "title":"Approved external future post","format":"photo","status":"scheduled"}]
        }
        d=r.reconcile(registry,{"other-approved-provider":snapshot},asof=NOW)
        state=next(s for s in d["source_health"] if s["source_id"]=="other-approved-provider")
        self.assertEqual(state["state"],"AVAILABLE")
        self.assertEqual(state["count"],1)
        self.assertTrue(any(s["source_id"]=="other-approved-provider" for s in d["scheduled"]))

    def test_external_provider_identity_mismatch_fails(self):
        registry=copy.deepcopy(REG)
        ext=next(s for s in registry["sources"] if s["id"]=="other-approved-provider")
        ext["active"]=True
        snapshot={
            "schema":"velvet.read_source_snapshot.v1",
            "observed_at":"2026-10-10T13:02:54Z",
            "source_id":"different-service",
            "scheduled":[]
        }
        d=r.reconcile(registry,{"other-approved-provider":snapshot},asof=NOW)
        state=next(s for s in d["source_health"] if s["source_id"]=="other-approved-provider")
        self.assertEqual(state["state"],"INVALID")

    def test_real_v3_capture_lower_bound(self):
        path=Path(r"D:\Velvet\Artifacts\MetaPlannerReader\scheduled-v3-snapshot.json")
        if not path.exists(): self.skipTest("runtime UI fixture not mounted")
        doc=json.loads(path.read_text(encoding="utf-8-sig"))
        observed=r.parse_time(doc["observed_at"])
        d=r.reconcile(REG,{"meta-business-suite":doc},asof=observed)
        self.assertEqual(d["counts"]["meta_scheduled_lower_bound"],51)
        self.assertGreater(d["diagnostics"]["meta-business-suite"]["duplicate_rows"],0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
