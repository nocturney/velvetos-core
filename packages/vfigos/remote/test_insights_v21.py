#!/usr/bin/env python3
"""Unit tests for Graph v21 Insights partitioning + CTA audit (no network)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "vfigos" / "remote"))

from insights_v21 import (  # noqa: E402
    DEFAULT_ACCOUNT_METRICS_V21,
    fetch_account_insights,
    media_default_metrics,
    normalize_account_metrics,
    partition_account_metrics,
)
from cta_audit import audit_caption, audit_list_media_payload, audit_profile  # noqa: E402
from mutations import MATRIX, _unsupported  # noqa: E402


class FakeGraphError(Exception):
    pass


class InsightsV21Tests(unittest.TestCase):
    def test_default_excludes_impressions(self):
        names = normalize_account_metrics(None)
        self.assertNotIn("impressions", names)
        self.assertIn("reach", names)
        self.assertTrue(names)
        # Regression: upstream DEFAULT was reach,impressions,profile_views,follower_count
        self.assertNotEqual(
            DEFAULT_ACCOUNT_METRICS_V21,
            "reach,impressions,profile_views,follower_count",
        )

    def test_impressions_alias_to_views(self):
        names = normalize_account_metrics("reach,impressions")
        self.assertEqual(names, ["reach", "views"])
        ts, tv, unk = partition_account_metrics(names)
        self.assertEqual(ts, ["reach"])
        self.assertEqual(tv, ["views"])
        self.assertEqual(unk, [])

    def test_chatgpt_failure_1_default_no_longer_invalid_metric(self):
        """Failure 1: metric[1] impressions invalid — defaults must not include it."""
        names = normalize_account_metrics(None)
        self.assertNotIn("impressions", names)

    def test_chatgpt_failure_2_mixed_metrics_split(self):
        """Failure 2: profile_views,total_interactions need metric_type=total_value."""
        names = normalize_account_metrics(
            "reach,profile_views,follower_count,total_interactions"
        )
        ts, tv, unk = partition_account_metrics(names)
        self.assertEqual(unk, [])
        self.assertEqual(ts, ["reach", "follower_count"])
        self.assertEqual(tv, ["profile_views", "total_interactions"])

    def test_fetch_merges_two_requests(self):
        calls: list[dict] = []

        def getter(path: str, **params):
            calls.append({"path": path, **params})
            metric = params.get("metric", "")
            rows = [{"name": m, "period": params.get("period")} for m in metric.split(",")]
            return {"data": rows}

        out = fetch_account_insights(
            client=None,
            ig_user_id="17841407772120429",
            metrics="reach,profile_views,follower_count,total_interactions",
            period="day",
            get_fn=getter,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(len(calls), 2)
        # First call: time-series cohort, no metric_type=total_value
        self.assertEqual(calls[0]["metric"], "reach,follower_count")
        self.assertNotEqual(calls[0].get("metric_type"), "total_value")
        # Second call: total_value cohort
        self.assertEqual(calls[1]["metric"], "profile_views,total_interactions")
        self.assertEqual(calls[1]["metric_type"], "total_value")
        names = {row["name"] for row in out["insights"]}
        self.assertEqual(
            names, {"reach", "follower_count", "profile_views", "total_interactions"}
        )

    def test_fetch_surfaces_meta_error_cleanly(self):
        def getter(path: str, **params):
            raise FakeGraphError(
                "(#100) metric[1] must be one of the following values: reach, follower_count"
            )

        out = fetch_account_insights(
            None,
            "1",
            metrics="reach,impressions",  # remapped to views → still will call
            period="day",
            get_fn=getter,
        )
        # reach+views → two cohorts; both fail → ok False
        self.assertFalse(out["ok"])
        self.assertIn("#100", out["error"])

    def test_partial_follower_floor(self):
        def getter(path: str, **params):
            metric = params.get("metric", "")
            if "follower_count" in metric:
                raise FakeGraphError(
                    "(#100) follower_count requires 100 followers"
                )
            return {"data": [{"name": m} for m in metric.split(",")]}

        out = fetch_account_insights(
            None,
            "1",
            metrics="reach,follower_count,profile_views",
            period="day",
            get_fn=getter,
        )
        # ts cohort fails, tv may succeed → partial
        self.assertTrue(out["ok"])
        self.assertTrue(out.get("partial"))
        names = {r["name"] for r in out["insights"]}
        self.assertIn("profile_views", names)

    def test_media_defaults_by_type(self):
        self.assertIn("views", media_default_metrics({"media_type": "IMAGE"}))
        reels = media_default_metrics(
            {"media_type": "VIDEO", "media_product_type": "REELS"}
        )
        self.assertIn("reach", reels)
        story = media_default_metrics({"media_product_type": "STORY"})
        self.assertIn("replies", story)


class CtaAuditTests(unittest.TestCase):
    def test_phone_in_caption(self):
        r = audit_caption("הזמנות בוואטסאפ 050-2517000 #a #b")
        self.assertFalse(r["compliant"])
        self.assertIn("forbidden_public_cta", r["violations"])
        codes = {h["code"] for h in r["forbidden_cta"]}
        self.assertIn("phone_cta", codes)

    def test_hashtag_over_limit(self):
        cap = "שלום " + " ".join(f"#t{i}" for i in range(6))
        r = audit_caption(cap)
        self.assertIn("hashtag_over_limit", r["violations"])

    def test_historical_bucket(self):
        report = audit_list_media_payload(
            {
                "media": [
                    {
                        "id": "1",
                        "caption": "WhatsApp 050-2517000",
                        "permalink": "https://www.instagram.com/reel/DdAPhozlNe2/",
                        "media_type": "VIDEO",
                        "media_product_type": "REELS",
                    },
                    {
                        "id": "2",
                        "caption": "לפרטים — שלחו הודעה כאן",
                        "permalink": "https://www.instagram.com/p/DcqkjOLlYVX/",
                        "media_type": "IMAGE",
                    },
                ]
            },
            profile={
                "username": "velvets_cloud",
                "biography": "📍 איסוף משדרות | WhatsApp 050-2517000",
                "name": "Velvet Factory | הדפסות תלת־ממד",
            },
        )
        self.assertEqual(report["counts"]["historical_violations"], 1)
        self.assertFalse(report["profile"]["compliant"])
        self.assertEqual(report["historical_live"][0]["shortcode"], "DdAPhozlNe2")
        self.assertEqual(report["historical_live"][0]["bucket"], "historical_live")
        self.assertFalse(report["historical_live"][0]["editable_via_official_graph"])


class MutationMatrixTests(unittest.TestCase):
    def test_unsupported_ops(self):
        for op in (
            "update_biography",
            "update_website",
            "update_name",
            "update_media_caption",
            "update_profile",
            "archive_media",
        ):
            self.assertEqual(MATRIX[op]["status"], "unsupported_by_official_graph")
            self.assertIs(MATRIX[op]["supported"], False)
            self.assertIsNone(MATRIX[op].get("mcp_tool"))
            out = _unsupported(op)
            self.assertFalse(out["mutated"])
            self.assertIs(out["supported"], False)
            self.assertEqual(out["status"], "unsupported_by_official_graph")

    def test_misleading_write_tools_not_registered(self):
        from mutations import NEVER_EXPOSE_AS_WRITE_TOOLS, apply_mutation_tools
        from instagram_mcp.server import mcp
        import asyncio

        apply_mutation_tools(mcp)
        names = {t.name for t in asyncio.run(mcp.list_tools())}
        for banned in NEVER_EXPOSE_AS_WRITE_TOOLS:
            self.assertNotIn(banned, names)
        self.assertIn("graph_mutation_matrix", names)
        self.assertIn("delete_media", names)

    def test_delete_supported_but_destructive(self):
        self.assertIs(MATRIX["delete_media"]["supported"], True)
        self.assertEqual(MATRIX["delete_media"]["mcp_tool"], "delete_media")
        self.assertIn("instagram_manage_contents", MATRIX["delete_media"]["permissions"])


if __name__ == "__main__":
    unittest.main()
