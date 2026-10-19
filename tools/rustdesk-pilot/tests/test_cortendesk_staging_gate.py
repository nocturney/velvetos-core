"""Offline CortenDesk test-plan checks; no container is started."""
import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_staging_gate as gate

PLAN_FILE = Path(__file__).resolve().parents[1] / 'fixtures' / 'cortendesk-staging-plan.json'


class StagingPlanTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(PLAN_FILE.read_text(encoding='utf-8'))

    def expect_rejection(self, changes: dict, expected: str):
        plan = copy.deepcopy(self.base)
        plan.update(changes)
        with self.assertRaisesRegex(gate.StagingPlanError, expected):
            gate.validate_plan(plan)

    def test_safe_fixture_is_plan_only_and_never_execution(self):
        result = gate.validate_plan(self.base)
        self.assertEqual(result['state'], 'STAGING_DESIGN_VALID_RUNTIME_BLOCKED')
        self.assertIs(result['may_execute'], False)
        self.assertTrue(result['existing_rustdesk_unchanged'])
        self.assertNotIn('host_ports', result)
        self.assertNotIn('secret', json.dumps(result).lower())

    def test_pinned_arm64_image_must_not_float(self):
        self.expect_rejection({'image': 'ghcr.io/marcpope/cortendesk:latest'},
                              'image_not_immutable')
        self.expect_rejection({'image': 'ghcr.io/marcpope/cortendesk:1.13.2'},
                              'image_not_immutable')
        self.expect_rejection({'image': 'ghcr.io/marcpope/cortendesk:1.14.0'},
                              'image_not_immutable')
        self.expect_rejection({'source_release': 'v1.13.2'},
                              'image_not_immutable')
        self.expect_rejection({'image': 'ghcr.io/marcpope/cortendesk@sha256:3f91c02180d6ed59bfa3d4a938b0a52cf01e8fd1e953799be05435234c062373'},
                              'image_not_immutable')

    def test_cannot_take_over_production_colima_or_server(self):
        self.expect_rejection({'colima_profile': 'rustdesk'}, 'isolated_runtime')
        self.expect_rejection({'containerd_namespace': 'default'}, 'isolated_runtime')
        self.expect_rejection({'embedded_server': False}, 'bundled_server')

    def test_cannot_bind_public_network(self):
        for ip in ('0.0.0.0', '192.168.0.31', '::', 'localhost'):
            with self.subTest(ip=ip):
                self.expect_rejection({'bind_address': ip}, 'localhost_only')

    def test_production_state_must_be_inaccessible(self):
        for field, value in (
            ('production_server_mounted', True),
            ('production_keys_reused', True),
            ('production_clients_modified', True),
            ('data_mode', 'live_bind_mount'),
        ):
            with self.subTest(field=field):
                self.expect_rejection({field: value}, 'production_state')

    def test_disposable_client_only(self):
        self.expect_rejection({'test_client': 'Chris'}, 'disposable_client')
        self.expect_rejection({'test_client': 'all_live_clients'}, 'disposable_client')

    def test_no_default_admin_password_or_token_in_manifest(self):
        self.expect_rejection({'secrets': 'admin/changeme'}, 'no_default')
        x = copy.deepcopy(self.base)
        x['admin_password'] = 'some-secret-string'
        with self.assertRaisesRegex(gate.StagingPlanError, 'schema_fields'):
            gate.validate_plan(x)

    def test_runtime_denial_cannot_be_dropped(self):
        self.expect_rejection({'execution_status': 'approved'}, 'execution_gate')
        self.expect_rejection({'execution_status': True}, 'execution_gate')

    def test_prod_ports_are_reserved(self):
        for number in (8080, 8443, 21115, 21116, 21117, 21118, 21119, 80):
            with self.subTest(number=number):
                x = copy.deepcopy(self.base['host_ports'])
                x['console_tcp'] = number
                self.expect_rejection({'host_ports': x}, 'port_plan_invalid')

    def test_no_host_port_collisions(self):
        p = copy.deepcopy(self.base['host_ports'])
        p['relay_tcp'] = p['console_tcp']
        self.expect_rejection({'host_ports': p}, 'host_port_collision')

    def test_rendezvous_tcp_udp_match(self):
        p = copy.deepcopy(self.base['host_ports'])
        p['id_udp'] = 22122
        self.expect_rejection({'host_ports': p}, 'tcp_udp_rendezvous')

    def test_port_boolean_is_not_a_valid_port(self):
        p = copy.deepcopy(self.base['host_ports'])
        p['console_tcp'] = True
        self.expect_rejection({'host_ports': p}, 'port_plan_invalid')

    def test_extra_port_labels_rejected(self):
        p = copy.deepcopy(self.base['host_ports'])
        p['prod_rustdesk_port'] = 21116
        self.expect_rejection({'host_ports': p}, 'port_plan_invalid')

    def test_resource_limits_are_bounded(self):
        for cpus in (0, 1.1, True, -1, '0.5'):
            with self.subTest(cpus=cpus):
                self.expect_rejection({'cpus': cpus}, 'cpu_budget')
        for memory in (256, 2048, True, '768'):
            with self.subTest(memory=memory):
                self.expect_rejection({'memory_mb': memory}, 'memory_budget')

    def test_required_manifest_keys_complete(self):
        x = copy.deepcopy(self.base)
        del x['image']
        with self.assertRaisesRegex(gate.StagingPlanError, 'schema_fields'):
            gate.validate_plan(x)

    def test_cli_rejects_missing_plan_without_leaking_path(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'do-not-print-secret-name.json'
            with patch('builtins.print') as printer:
                code = gate.main(['--plan', str(path)])
            self.assertEqual(code, 2)
            result = json.loads(printer.call_args.args[0])
            self.assertEqual(result['state'], 'REJECTED')
            self.assertFalse(result['may_execute'])
            self.assertNotIn('do-not-print-secret-name', json.dumps(result))

    def test_cli_reads_valid_plan_and_blocks_runtime(self):
        with patch('builtins.print') as printer:
            code = gate.main(['--plan', str(PLAN_FILE)])
        self.assertEqual(code, 0)
        out = json.loads(printer.call_args.args[0])
        self.assertEqual(out['state'], 'STAGING_DESIGN_VALID_RUNTIME_BLOCKED')

    def test_large_plan_is_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'giant.json'
            path.write_text(' ' * 33000, encoding='utf-8')
            with patch('builtins.print') as printer:
                code = gate.main(['--plan', str(path)])
            self.assertEqual(code, 2)
            out = json.loads(printer.call_args.args[0])
            self.assertEqual(out['reason'], 'plan_too_large')


if __name__ == '__main__':
    unittest.main()
