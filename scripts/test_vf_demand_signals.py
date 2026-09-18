#!/usr/bin/env python3
import unittest

from vf_demand_signals import normalize_packet, validate_packet


class DemandSignalsTest(unittest.TestCase):
    def test_normalizes_series_terms_and_metrics_without_inventing_zero(self):
        raw = [{
            "source_url": "https://example.com/trends?q=lamp",
            "provider": "fixture",
            "kind": "search_interest",
            "query": "3d printed lamp",
            "geo": "IL",
            "observed_at": "2026-09-18T07:00:00Z",
            "metrics": {"result_count": "12", "missing": None},
            "series": [{"date": "2026-09-01", "value": "42"}],
            "related_terms": ["3d lamp shade", "printed lamp"]
        }]
        packet = normalize_packet(raw, "2026-09-01", "2026-09-18", "fixture", None, None)
        self.assertEqual(packet["signals"][0]["metrics"]["result_count"], 12)
        self.assertIsNone(packet["signals"][0]["metrics"]["missing"])
        self.assertEqual(packet["signals"][0]["series"][0]["value"], 42)
        self.assertEqual(packet["signals"][0]["related_terms"][0], "3d lamp shade")
    def test_rejects_synthetic_demand_score(self):
        packet = normalize_packet([{
            "source_url": "https://example.com/x",
            "provider": "fixture",
            "kind": "search_suggestion",
            "query": "owl",
            "observed_at": "2026-09-18T07:00:00Z",
            "metrics": {}
        }], "2026-09-01", "2026-09-18", "fixture", None, None)
        packet["signals"][0]["demand_score"] = 99
        errors = validate_packet(packet)
        self.assertTrue(any("demand_score" in e for e in errors))

    def test_requires_public_source_url(self):
        with self.assertRaises(SystemExit):
            normalize_packet([{
                "source_url": "file:///private/raw.json",
                "provider": "fixture",
                "kind": "serp_observation",
                "query": "3d print israel",
                "observed_at": "2026-09-18T07:00:00Z",
                "metrics": {}
            }], "2026-09-01", "2026-09-18", "fixture", None, None)


if __name__ == "__main__":
    unittest.main()
