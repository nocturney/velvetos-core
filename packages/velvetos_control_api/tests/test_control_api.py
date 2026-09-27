#!/usr/bin/env python3
"""Deterministic tests for VelvetOS Control API v1. No network. No send."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root (…/packages/velvetos_control_api/tests → ↑3)
PACKAGES = ROOT / "packages"
if str(PACKAGES) not in sys.path:
    sys.path.insert(0, str(PACKAGES))

from velvetos_control_api.actions import execute_action, idempotent_equal  # noqa: E402
from velvetos_control_api.app import create_server  # noqa: E402
from velvetos_control_api.auth import authorize  # noqa: E402
from velvetos_control_api.contributions.capabilities import (  # noqa: E402
    normalize_all_capabilities,
)
from velvetos_control_api.contributions.integrations import normalize_integrations  # noqa: E402
from velvetos_control_api.contributions.operational import (  # noqa: E402
    project_agents,
    project_content,
    project_files,
    project_models,
    project_production,
)
from velvetos_control_api.contributions.unavailable import V1_UNAVAILABLE  # noqa: E402
from velvetos_control_api.errors import ControlApiError  # noqa: E402
from velvetos_control_api.schema import SCHEMA  # noqa: E402
from velvetos_control_api.search import search, validate_destination  # noqa: E402
from velvetos_control_api.snapshot import build_snapshot  # noqa: E402


class SchemaTests(unittest.TestCase):
    def test_snapshot_schema(self) -> None:
        snap = build_snapshot(root=ROOT)
        self.assertEqual(snap["schema"], SCHEMA)
        for key in (
            "generatedAt",
            "connection",
            "freshness",
            "flags",
            "modules",
            "capabilities",
            "integrations",
            "health",
            "attention",
            "activity",
            "collections",
        ):
            self.assertIn(key, snap)
        fresh = snap["freshness"]
        self.assertIn(fresh["state"], {"live", "fresh", "stale", "unknown"})
        self.assertIn("verifiedAt", fresh)

    def test_operational_domains_are_ready_from_canonical_sources(self) -> None:
        snap = build_snapshot(root=ROOT)
        cols = snap["collections"]
        for name in V1_UNAVAILABLE:
            col = cols[name]
            self.assertEqual(col["state"], "ready", name)
            self.assertIsInstance(col["items"], list)

    def test_operational_domains_fail_closed_when_sources_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snap = build_snapshot(root=Path(td))
            for name in V1_UNAVAILABLE:
                col = snap["collections"][name]
                self.assertEqual(col["state"], "unavailable", name)
                self.assertIsNone(col["items"], msg=f"{name} must not invent []")
                self.assertIsNone(col["count"], msg=f"{name} must not invent 0")
                self.assertTrue(col.get("reason"))

    def test_jobs_ready_empty_vs_structure(self) -> None:
        snap = build_snapshot(root=ROOT)
        jobs = snap["collections"]["jobs"]
        self.assertIn(jobs["state"], {"ready", "needs_sync", "conflict", "unavailable", "unknown"})
        if jobs["state"] == "ready":
            self.assertIsInstance(jobs["items"], list)
            self.assertEqual(jobs["count"], len(jobs["items"]))
        else:
            self.assertIsNone(jobs["items"])
            self.assertIsNone(jobs["count"])

    def test_missing_source_sandbox(self) -> None:
        """When control-plane is absent, system is unavailable — not fake healthy."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # minimal empty tree — no control-plane
            snap = build_snapshot(root=root)
            system = (snap.get("flags") or {}).get("system") or {}
            # control plane contribution should mark unavailable
            self.assertIn(system.get("state"), {"unavailable", None, "unknown"})
            # unavailable collections stay null items
            for name in ("production", "models"):
                col = snap["collections"][name]
                self.assertIsNone(col["items"])


class CapabilityTests(unittest.TestCase):
    def test_normalize_from_canonical(self) -> None:
        caps = normalize_all_capabilities(ROOT)
        self.assertGreater(len(caps), 5)
        by_id = {c["id"]: c for c in caps}
        self.assertIn("auto.dm", by_id)
        self.assertEqual(by_id["auto.dm"]["status"], "BLOCKED")
        self.assertEqual(by_id["auto.dm"]["risk"], "RED")
        # gate=lead → APPROVAL_REQUIRED + ORANGE
        if "price.set" in by_id:
            self.assertEqual(by_id["price.set"]["status"], "APPROVAL_REQUIRED")
            self.assertEqual(by_id["price.set"]["risk"], "ORANGE")
        for c in caps:
            self.assertIn(c["status"], {
                "AVAILABLE", "DEGRADED", "NEEDS_AUTH", "UNAVAILABLE", "BLOCKED", "APPROVAL_REQUIRED"
            })
            self.assertIn(c["risk"], {"GREEN", "YELLOW", "ORANGE", "RED"})
            self.assertIn("provenance", c)

    def test_no_invented_numeric_prices_in_caps(self) -> None:
        caps = normalize_all_capabilities(ROOT)
        # Normalized capability objects must not invent a numeric sale price field
        for c in caps:
            self.assertNotIn("priceIls", c)
            self.assertNotIn("salePrice", c)
            if "price" in c and c["price"] not in (None, "X ₪"):
                # Only allow absence or explicit placeholder — never a fabricated number
                self.fail(f"capability {c.get('id')} must not invent price={c.get('price')}")


class IntegrationProjectionTests(unittest.TestCase):
    def test_instance_tools_project_from_canonical_desk(self) -> None:
        rows, envelope = normalize_integrations(ROOT)
        self.assertEqual(envelope["state"], "ready")
        self.assertGreaterEqual(len(rows), 10)
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id["gmail"]["status"], "AVAILABLE")
        self.assertEqual(by_id["threedaistudio"]["status"], "AVAILABLE")
        self.assertEqual(by_id["studiomcphub"]["status"], "NEEDS_AUTH")
        self.assertEqual(by_id["treg"]["status"], "BLOCKED")
        self.assertEqual(by_id["mcp-gsheets"]["status"], "UNAVAILABLE")
        self.assertIn("provenance", by_id["whatsapp"])

    def test_snapshot_includes_integration_collection(self) -> None:
        snap = build_snapshot(root=ROOT)
        self.assertIsInstance(snap["integrations"], list)
        self.assertEqual(snap["collections"]["integrations"]["state"], "ready")
        self.assertEqual(
            snap["collections"]["integrations"]["count"],
            len(snap["integrations"]),
        )

    def test_missing_instance_desk_is_honestly_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rows, envelope = normalize_integrations(Path(td))
            self.assertEqual(rows, [])
            self.assertEqual(envelope["state"], "unavailable")
            self.assertIsNone(envelope["items"])
            self.assertIsNone(envelope["count"])

    def test_cloud_run_image_packages_canonical_instance_desk(self) -> None:
        dockerfile = (ROOT / "packages" / "velvetos_control_api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY instances/velvet-factory/.cursor/vf-desk.json "
            "/app/instances/velvet-factory/.cursor/vf-desk.json",
            dockerfile,
        )

    def test_control_center_deploy_keeps_app_token_topology_reachable(self) -> None:
        deploy = (ROOT / "packages" / "velvetos_control_api" / "deploy.sh").read_text(encoding="utf-8")
        self.assertIn("--allow-unauthenticated", deploy)
        self.assertNotIn("--no-allow-unauthenticated", deploy)


class OperationalProjectionTests(unittest.TestCase):
    def test_production_projects_known_fleet_without_fake_telemetry(self) -> None:
        col = project_production(ROOT)
        self.assertEqual(col["state"], "ready")
        printers = [item for item in col["items"] if item.get("kind") == "printer"]
        self.assertEqual(len(printers), 4)
        self.assertTrue(all(item.get("status") == "unknown" for item in printers))
        self.assertFalse(col["hqPrints"])

    def test_content_projects_canonical_approval_queue(self) -> None:
        col = project_content(ROOT)
        self.assertEqual(col["state"], "ready")
        self.assertEqual(col["count"], 1)
        self.assertEqual(col["items"][0]["disposition"], "stale_orphan")
        self.assertFalse(col["items"][0]["ownerSurface"])

    def test_files_projects_bounded_media_catalog_with_true_total(self) -> None:
        col = project_files(ROOT)
        self.assertEqual(col["state"], "ready")
        self.assertGreater(col["totalCount"], 100)
        self.assertLessEqual(col["projectedCount"], 60)
        self.assertEqual(col["count"], col["totalCount"])
        self.assertTrue(col["truncated"])

    def test_agents_project_canonical_specialist_roster(self) -> None:
        col = project_agents(ROOT)
        self.assertEqual(col["state"], "ready")
        self.assertGreaterEqual(col["count"], 20)
        self.assertGreaterEqual(col["seatCount"], 5)
        self.assertTrue(all("id" in item and "job" in item for item in col["items"]))

    def test_models_project_five_explicit_empty_slots(self) -> None:
        col = project_models(ROOT)
        self.assertEqual(col["state"], "ready")
        self.assertEqual(col["count"], 5)
        self.assertEqual(col["occupiedCount"], 0)
        self.assertEqual(col["readyCount"], 0)
        self.assertTrue(all(item["status"] == "empty" for item in col["items"]))

    def test_search_allows_integration_and_operational_routes(self) -> None:
        self.assertTrue(validate_destination("/integrations/threedaistudio"))
        self.assertTrue(validate_destination("/agents/studio-operations"))
        self.assertTrue(validate_destination("/models/1"))

    def test_cloud_run_image_packages_operational_sources(self) -> None:
        dockerfile = (ROOT / "packages" / "velvetos_control_api" / "Dockerfile").read_text(encoding="utf-8")
        for source in (
            "packages/vfprod/FLEET.json",
            "packages/vfprod/data/print-events.jsonl",
            "packages/vfprod/data/maintenance-snapshot.json",
            "packages/vfsku/SHELF.json",
        ):
            self.assertIn(f"COPY {source}", dockerfile)


class AuthActionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("VELVETOS_CONTROL_API_TOKEN")
        os.environ["VELVETOS_CONTROL_API_TOKEN"] = "unit-test-secret-token"

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("VELVETOS_CONTROL_API_TOKEN", None)
        else:
            os.environ["VELVETOS_CONTROL_API_TOKEN"] = self._prev

    def test_anonymous_denied(self) -> None:
        with self.assertRaises(ControlApiError) as ctx:
            authorize({})
        self.assertEqual(ctx.exception.status, 401)

    def test_invalid_token_denied(self) -> None:
        with self.assertRaises(ControlApiError):
            authorize({"Authorization": "Bearer wrong"})

    def test_valid_token(self) -> None:
        authorize({"Authorization": "Bearer unit-test-secret-token"})
        authorize({"X-Api-Key": "unit-test-secret-token"})

    def test_unknown_action(self) -> None:
        r = execute_action(
            {"actionId": "no.such.capability", "idempotencyKey": "idempotency-key-01"},
            root=ROOT,
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"]["code"], "UNKNOWN_ACTION")
        self.assertIn("receipt", r)

    def test_hard_deny_shell(self) -> None:
        r = execute_action(
            {
                "actionId": "shell.exec",
                "objectId": "id",
                "confirmation": "yes",
                "idempotencyKey": "idempotency-key-02",
            },
            root=ROOT,
        )
        self.assertEqual(r["error"]["code"], "CAPABILITY_DENIED")

    def test_path_injection(self) -> None:
        r = execute_action(
            {
                "actionId": "gmail.read",
                "objectId": "../../../etc/passwd",
                "idempotencyKey": "idempotency-key-03",
            },
            root=ROOT,
        )
        self.assertFalse(r.get("ok", True))
        # either invalid objectId or injection denied
        self.assertIn(r.get("error", {}).get("code"), {
            "BAD_REQUEST", "CAPABILITY_DENIED", "CAPABILITY_UNAVAILABLE", "APPROVAL_REQUIRED", "CONFIRMATION_REQUIRED"
        })

    def test_command_field_rejected(self) -> None:
        r = execute_action(
            {
                "actionId": "gmail.read",
                "idempotencyKey": "idempotency-key-04",
                "command": "rm -rf /",
            },
            root=ROOT,
        )
        self.assertEqual(r["error"]["code"], "CAPABILITY_DENIED")

    def test_idempotency_contract(self) -> None:
        body = {
            "actionId": "auto.dm",
            "idempotencyKey": "idempotency-key-05",
        }
        a = execute_action(body, root=ROOT)
        b = execute_action(body, root=ROOT)
        self.assertTrue(idempotent_equal(a, b))
        self.assertFalse(a.get("accepted"))
        self.assertFalse(a.get("completed"))

    def test_denied_capability_auto_dm(self) -> None:
        r = execute_action(
            {"actionId": "auto.dm", "idempotencyKey": "idempotency-key-06"},
            root=ROOT,
        )
        self.assertEqual(r["error"]["code"], "CAPABILITY_DENIED")

    def test_no_secret_leakage_in_action(self) -> None:
        r = execute_action(
            {"actionId": "auto.dm", "idempotencyKey": "idempotency-key-07"},
            root=ROOT,
        )
        blob = json.dumps(r)
        self.assertNotIn("unit-test-secret-token", blob)


class SearchTests(unittest.TestCase):
    def test_destination_validation(self) -> None:
        self.assertTrue(validate_destination("/jobs/VF-1"))
        self.assertFalse(validate_destination("https://evil.test/x"))
        self.assertFalse(validate_destination("/jobs/../../etc/passwd"))
        self.assertFalse(validate_destination("javascript:alert(1)"))

    def test_search_results_destinations(self) -> None:
        # Search for a known capability fragment
        out = search("gmail", root=ROOT)
        self.assertIn("results", out)
        for hit in out["results"]:
            self.assertTrue(validate_destination(hit["destination"]), hit)

    def test_integration_search_is_not_filtered_by_destination_policy(self) -> None:
        out = search("threedaistudio", root=ROOT)
        hits = [hit for hit in out["results"] if hit.get("type") == "integration"]
        self.assertTrue(hits)
        self.assertTrue(all(validate_destination(hit["destination"]) for hit in hits))

    def test_operational_search_finds_agent_roster(self) -> None:
        out = search("studio-operations", root=ROOT)
        hits = [hit for hit in out["results"] if hit.get("type") == "agents"]
        self.assertTrue(hits)
        self.assertTrue(all(validate_destination(hit["destination"]) for hit in hits))


class HttpIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.token = "http-integ-token-xyz"
        os.environ["VELVETOS_CONTROL_API_TOKEN"] = cls.token
        cls.httpd = create_server("127.0.0.1", 0, root=ROOT, check_isolation=False)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()

    def _conn(self) -> HTTPConnection:
        return HTTPConnection("127.0.0.1", self.port, timeout=5)

    def test_health_no_auth(self) -> None:
        c = self._conn()
        c.request("GET", "/health")
        r = c.getresponse()
        body = json.loads(r.read().decode())
        self.assertEqual(r.status, 200)
        self.assertEqual(body["service"], "ready")
        self.assertIn(body["velvetos"], {"ok", "degraded", "unknown"})
        self.assertNotEqual(body["service"], body.get("velvetos") == "ready" and "all-healthy")

    def test_snapshot_requires_auth(self) -> None:
        c = self._conn()
        c.request("GET", "/v1/snapshot")
        r = c.getresponse()
        self.assertEqual(r.status, 401)
        body = json.loads(r.read().decode())
        self.assertNotIn(self.token, json.dumps(body))

    def test_snapshot_with_auth(self) -> None:
        c = self._conn()
        c.request("GET", "/v1/snapshot", headers={"Authorization": f"Bearer {self.token}"})
        r = c.getresponse()
        body = json.loads(r.read().decode())
        self.assertEqual(r.status, 200)
        self.assertEqual(body["schema"], SCHEMA)
        self.assertNotIn(self.token, json.dumps(body))

    def test_actions_anonymous_denied(self) -> None:
        c = self._conn()
        payload = json.dumps(
            {"actionId": "gmail.read", "idempotencyKey": "idempotency-http-01"}
        ).encode()
        c.request(
            "POST",
            "/v1/actions",
            body=payload,
            headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
        )
        r = c.getresponse()
        self.assertEqual(r.status, 401)

    def test_wrong_method(self) -> None:
        c = self._conn()
        c.request("POST", "/v1/snapshot", headers={"Authorization": f"Bearer {self.token}"})
        r = c.getresponse()
        self.assertEqual(r.status, 405)


if __name__ == "__main__":
    unittest.main(verbosity=2)
