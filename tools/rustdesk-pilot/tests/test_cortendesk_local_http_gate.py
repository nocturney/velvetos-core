"""Offline contract tests for a read-only future CortenDesk local staging probe."""
from contextlib import redirect_stdout
import copy
from io import StringIO
import json
from pathlib import Path
import sys
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_local_http_gate as probe
from cortendesk_staging_gate import StagingPlanError

PLAN_FILE = (Path(__file__).resolve().parents[1] /
             "fixtures" / "cortendesk-staging-plan.json")


def fake_responses(login=None, devices=None, webclient=None):
    return {
        "/login": login or probe.Response(200, "text/html; charset=UTF-8"),
        "/devices": devices or probe.Response(302, location="/login"),
        "/webclient": webclient or probe.Response(403),
    }


class StagingBrowserSmokeTests(TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))

    def run_probe(self, responses):
        calls = []
        def request(port, route):
            calls.append((port, route))
            return responses[route]
        report = probe.inspect(self.plan, requester=request)
        self.assertEqual(calls, [
            (18080, "/login"), (18080, "/devices"), (18080, "/webclient"),
        ])
        self.assertFalse(report["may_launch_container"])
        self.assertFalse(report["performed_mutation"])
        self.assertFalse(report["access_tokens_used"])
        self.assertFalse(report["mobile_safari_verified"])
        self.assertFalse(report["websocket_verified"])
        self.assertFalse(report["browser_remote_control_verified"])
        self.assertNotIn("private_id", json.dumps(report))
        return report

    def test_local_login_and_protected_devices_and_webclient(self):
        report = self.run_probe(fake_responses())
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE")
        self.assertEqual(report["login_route"], "present")
        self.assertEqual(report["anonymous_access"],
                         {"devices": "protected", "webclient": "protected"})

    def test_login_only_is_not_a_success(self):
        report = self.run_probe(fake_responses(
            webclient=probe.Response(200, "text/html")))
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_REJECTED")
        self.assertEqual(report["anonymous_access"]["webclient"],
                         "anonymous_page_exposed")

    def test_devices_public_is_rejected(self):
        report = self.run_probe(fake_responses(devices=probe.Response(200)))
        self.assertEqual(report["anonymous_access"]["devices"],
                         "anonymous_page_exposed")
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_REJECTED")

    def test_missing_webclient_is_rejected(self):
        report = self.run_probe(fake_responses(webclient=probe.Response(404)))
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_REJECTED")
        self.assertEqual(report["anonymous_access"]["webclient"],
                         "unexpected_status")

    def test_login_not_html_is_rejected(self):
        report = self.run_probe(fake_responses(login=probe.Response(
            200, "application/json")))
        self.assertEqual(report["login_route"], "unverified")
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_REJECTED")

    def test_forbidden_redirect_to_external_host(self):
        for target in (
            "https://example.invalid/login",
            "http://localhost:18080/login",
            "http://127.0.0.1:5000/login",
            "//127.0.0.1:18080/login",
            "http://127.0.0.1:notaport/login",
            "/admin",
            "javascript:alert(1)",
        ):
            with self.subTest(target=target):
                report = self.run_probe(fake_responses(
                    devices=probe.Response(302, location=target)))
                self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_REJECTED")
                self.assertEqual(report["anonymous_access"]["devices"],
                                 "unexpected_redirect")

    def test_same_origin_local_redirect_to_login_is_safe(self):
        report = self.run_probe(fake_responses(
            devices=probe.Response(302, location="http://127.0.0.1:18080/login"),
            webclient=probe.Response(302, location="/login")))
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE")

    def test_unauthenticated_denials_count_as_protection(self):
        report = self.run_probe(fake_responses(
            devices=probe.Response(401), webclient=probe.Response(403)))
        self.assertEqual(report["state"], "LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE")

    def test_inaccessible_stage_reports_no_runtime(self):
        def missing(_port, _route):
            raise probe.LocalGateError("localhost_not_reachable")
        report = probe.inspect(self.plan, requester=missing)
        self.assertEqual(report["state"], "STAGING_NOT_REACHABLE")
        self.assertEqual(report["login_route"], "unknown")
        self.assertFalse(report["may_launch_container"])

    def test_production_profile_or_public_bind_forbidden_before_requests(self):
        for key, value in (("colima_profile", "rustdesk"),
                           ("bind_address", "0.0.0.0")):
            with self.subTest(key=key):
                proposal = copy.deepcopy(self.plan)
                proposal[key] = value
                def raise_if_called(_port, _route):
                    self.fail("invalid plan must not issue any request")
                with self.assertRaises(StagingPlanError):
                    probe.inspect(proposal, requester=raise_if_called)

    def test_plan_runtime_execution_denial_remains(self):
        proposal = copy.deepcopy(self.plan)
        proposal["execution_status"] = "approved"
        with self.assertRaisesRegex(StagingPlanError, "execution_gate"):
            probe.inspect(proposal, requester=lambda _p,_r: None)

    def test_cli_without_explicit_flag_never_reads_plan_or_network(self):
        with patch.object(probe, "inspect") as inspector, redirect_stdout(StringIO()) as buffer:
            code = probe.main(["--plan", "totally-missing-private-config.json"])
        self.assertEqual(code, 2)
        inspector.assert_not_called()
        report = json.loads(buffer.getvalue())
        self.assertEqual(report["state"], "BLOCKED_EXPLICIT_OPT_IN_REQUIRED")
        self.assertFalse(report["may_launch_container"])

    def test_cli_with_optin_reports_missing_plan_safely(self):
        with redirect_stdout(StringIO()) as buffer:
            code = probe.main([
                "--plan", "sensitive-do-not-print-this.json",
                "--allow-local-staging-read",
            ])
        self.assertEqual(code, 2)
        self.assertNotIn("sensitive-do-not-print-this", buffer.getvalue())
        self.assertEqual(json.loads(buffer.getvalue())["state"], "REJECTED")

    def test_cli_success_does_not_claim_mobile_control(self):
        report = self.run_probe(fake_responses())
        with patch.object(probe, "inspect", return_value=report), redirect_stdout(StringIO()) as stream:
            code = probe.main([
                "--plan", str(PLAN_FILE), "--allow-local-staging-read",
            ])
        self.assertEqual(code, 0)
        parsed = json.loads(stream.getvalue())
        self.assertFalse(parsed["mobile_safari_verified"])
        self.assertFalse(parsed["browser_remote_control_verified"])

    def test_local_reader_refuses_unexpected_route_before_socket(self):
        with self.assertRaisesRegex(probe.LocalGateError, "unexpected_probe_route"):
            probe._read_local(18080, "/api/secrets")

    def test_credentials_not_accepted_as_probe_parameters(self):
        # A production token or user ID has no CLI or requester parameter.
        import inspect
        self.assertNotIn("token", inspect.signature(probe.inspect).parameters)
        self.assertNotIn("password", inspect.signature(probe.inspect).parameters)
        self.assertNotIn("username", inspect.signature(probe.inspect).parameters)


if __name__ == "__main__":
    main()
