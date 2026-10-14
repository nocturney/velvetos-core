"""Simulated host read-only CortenDesk readiness probes; no real runtime commands."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_readiness_probe as probe

PLAN = Path(__file__).resolve().parents[1] / 'fixtures' / 'cortendesk-staging-plan.json'
EXPECTED_SHA = 'sha256:3f91c02180d6ed59bfa3d4a938b0a52cf01e8fd1e953799be05435234c062373'


class TestHostReadiness(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_text(encoding='utf-8'))
        self.commands = []
        self.qa_on = True
        self.prod_on = True
        self.available_image = True
        self.ns_exists = False
        self.busy_staging = None
        self.busy_guest = None
        self.guest_invalid = False
        self.errors_on = None

    def runner(self, argv):
        self.commands.append(tuple(argv))
        if self.errors_on and self.errors_on in argv:
            return None, ''
        if argv == ['colima', 'list']:
            qa = 'Running' if self.qa_on else 'Stopped'
            prod = 'Running' if self.prod_on else 'Stopped'
            return 0, (
                'PROFILE STATUS ARCH CPUS MEMORY DISK RUNTIME ADDRESS\n'
                'rustdesk ' + prod + ' aarch64 2 2GiB 10GiB containerd\n'
                'velvet-qa ' + qa + ' aarch64 2 4GiB 30GiB containerd\n'
            )
        if argv[:4] == ['colima', 'ssh', '-p', 'velvet-qa']:
            if argv[-1] == probe.GUEST_SOCKET_COMMAND:
                if self.guest_invalid:
                    return 0, 'unexpected unparseable socket response'
                if self.busy_guest:
                    proto, port = self.busy_guest
                    return 0, (
                        f'{proto} LISTEN 0 128 0.0.0.0:{port} 0.0.0.0:*\\n'
                    )
                return 0, ''
            if argv[-1] == probe.IMAGE_COMMAND:
                if not self.available_image:
                    return 0, ''
                return 0, ('ghcr.io/marcpope/cortendesk 1.13.2 ' +
                           EXPECTED_SHA + '\n')
            if argv[-1] == probe.NAMESPACE_COMMAND:
                text = 'NAME CONTAINERS IMAGES\ndefault 0 1\nvf-rustdesk-pilot 0 1\n'
                if self.ns_exists:
                    text += 'vf-cortendesk-staging 0 1\n'
                return 0, text
        if argv[0] == 'lsof':
            if argv[2].startswith('-iTCP:'):
                port = int(argv[2].split(':', 1)[1])
                protocol = 'tcp'
            elif argv[2].startswith('-iUDP:'):
                port = int(argv[2].split(':', 1)[1])
                protocol = 'udp'
            else:
                self.fail('nonwhitelisted lsof selector')
            if self.busy_staging == (protocol, port):
                return 0, '123\n'
            if port in probe.PROD_PORTS or (protocol == 'udp' and port == 21116):
                return 0, '456\n'
            return 1, ''
        self.fail('unapproved command: ' + str(argv))

    def inspect(self):
        return probe.inspect(self.plan, runner=self.runner,
                             system='Darwin', machine='arm64',
                             observed_at='2026-10-14T15:00:00Z')

    def test_all_clear_ends_with_may_execute_false(self):
        report = self.inspect()
        self.assertEqual(report['state'], 'READ_ONLY_SURVEY_RUNTIME_BLOCKED')
        self.assertFalse(report['may_execute'])
        self.assertFalse(report['has_performed_mutation'])
        self.assertTrue(report['profiles']['existing_rustdesk_running'])
        self.assertTrue(report['staging_ports_free_on_host_and_guest_at_observation'])
        self.assertTrue(report['production_rendezvous_present_at_observation'])
        self.assertTrue(report['pinned_image_cached_in_research_namespace'])
        self.assertFalse(report['target_namespace_exists'])
        self.assertIn('runtime_launch_previously_denied', report['findings'])
        self.assertIn('target_namespace_not_present', report['findings'])

    def test_all_invoked_commands_are_getters_not_mutators(self):
        self.inspect()
        for args in self.commands:
            self.assertIn(args[0], ('lsof', 'colima'))
            text = ' '.join(args)
            for forbidden in (' nerdctl run ', ' nerdctl pull ', ' nerdctl stop ',
                              ' nerdctl rm ', ' systemctl ', ' docker run ',
                              ' colima start ', ' sudo chmod ', ' cp '):
                self.assertNotIn(forbidden, ' ' + text + ' ')
        self.assertEqual(sum(x == ('colima', 'list') for x in self.commands), 1)

    def test_staging_port_busy_is_a_blocker(self):
        self.busy_staging = ('tcp', 18080)
        report = self.inspect()
        self.assertFalse(report['staging_ports_free_on_host_and_guest_at_observation'])
        self.assertIn('proposed_host_or_guest_port_conflict_or_unknown', report['findings'])

    def test_staging_udp_busy_is_a_blocker(self):
        self.busy_staging = ('udp', 22116)
        report = self.inspect()
        self.assertEqual(report['host_port_status']['id_udp'], 'occupied_at_observation')
        self.assertFalse(report['staging_ports_free_on_host_and_guest_at_observation'])

    def test_guest_port_conflict_is_blocker_even_when_host_is_free(self):
        self.busy_guest = ('tcp', 22116)
        report = self.inspect()
        self.assertFalse(report['staging_ports_free_on_host_and_guest_at_observation'])
        self.assertEqual(report['guest_port_status']['id_tcp'],
                         'occupied_at_observation')
        self.assertEqual(report['host_port_status']['id_tcp'],
                         'free_at_observation')

    def test_guest_unparseable_socket_output_is_not_free(self):
        self.guest_invalid = True
        report = self.inspect()
        self.assertEqual(report['guest_port_status']['console_tcp'], 'unknown')
        self.assertFalse(report['staging_ports_free_on_host_and_guest_at_observation'])

    def test_staging_probe_error_is_not_reported_as_free(self):
        self.errors_on = '-iTCP:18080'
        report = self.inspect()
        self.assertEqual(report['host_port_status']['console_tcp'], 'unknown')
        self.assertFalse(report['staging_ports_free_on_host_and_guest_at_observation'])

    def test_qa_down_does_not_invoke_ssh(self):
        self.qa_on = False
        report = self.inspect()
        self.assertIn('qa_profile_not_running', report['findings'])
        self.assertFalse(report['pinned_image_cached_in_research_namespace'])
        self.assertFalse(any(args[0:2] == ('colima', 'ssh')
                             for args in self.commands))

    def test_production_down_does_not_false_assert_serving(self):
        self.prod_on = False
        report = self.inspect()
        self.assertIn('production_service_unverified', report['findings'])

    def test_image_cache_absence_reported(self):
        self.available_image = False
        report = self.inspect()
        self.assertFalse(report['pinned_image_cached_in_research_namespace'])
        self.assertIn('pinned_image_not_verified_in_research_cache', report['findings'])

    def test_staging_namespace_existence_detected(self):
        self.ns_exists = True
        report = self.inspect()
        self.assertTrue(report['target_namespace_exists'])
        self.assertFalse(report['may_execute'])

    def test_reject_invalid_plan_before_any_host_probe(self):
        self.plan['bind_address'] = '0.0.0.0'
        with self.assertRaisesRegex(Exception, 'localhost_only'):
            self.inspect()
        self.assertEqual(self.commands, [])

    def test_unsupported_platform_does_not_probe_host(self):
        with self.assertRaisesRegex(probe.ProbeError, 'mac_arm64_only'):
            probe.inspect(self.plan, runner=self.runner,
                          system='Windows', machine='AMD64')
        self.assertEqual(self.commands, [])

    def test_no_identity_ip_secrets_or_process_output(self):
        report = self.inspect()
        payload = json.dumps(report)
        for marker in ('rustdesk_id', 'device_id', 'password', 'public_key',
                       '192.168.', 'ghcr.io/marcpope/cortendesk@sha256:'):
            self.assertNotIn(marker, payload)

    def test_image_check_requires_correct_image_row(self):
        self.assertTrue(probe._image_cached(
            'ghcr.io/marcpope/cortendesk 1.13.2 ' + EXPECTED_SHA, EXPECTED_SHA))
        self.assertFalse(probe._image_cached(
            'other/repo 1.13.2 ' + EXPECTED_SHA, EXPECTED_SHA))
        self.assertFalse(probe._image_cached(
            'ghcr.io/marcpope/cortendesk latest ' + EXPECTED_SHA, EXPECTED_SHA))

    def test_profile_name_must_match_exactly(self):
        rows = 'velvet-qa-backup Running aarch64\nvelvet-qa Running aarch64\n'
        self.assertTrue(probe._profile_status(rows, 'velvet-qa'))
        self.assertFalse(probe._profile_status(rows, 'rustdesk'))

    def test_cli_missing_plan_fails_without_leaking_path(self):
        with TemporaryDirectory() as folder, redirect_stdout(StringIO()) as output:
            rc = probe.main(['--plan', str(Path(folder) / 'private-token-name.json')])
            self.assertEqual(rc, 2)
            value = json.loads(output.getvalue())
            self.assertFalse(value['may_execute'])
            self.assertNotIn('private-token-name', json.dumps(value))

    def test_lsof_nonstandard_code_is_unknown(self):
        runner = lambda _: (99, '')
        self.assertEqual(probe._port_status(22117, 'tcp', runner), 'unknown')

    def test_invalid_protocol_rejected(self):
        with self.assertRaisesRegex(probe.ProbeError, 'unexpected_protocol'):
            probe._port_status(22116, 'sctp', self.runner)


if __name__ == '__main__':
    unittest.main()
