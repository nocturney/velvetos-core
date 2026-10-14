"""Validate a proposed CortenDesk stage; do not launch or configure anything.

Research only: reads one small explicit JSON plan, makes no network requests,
does not inspect secrets, and never invokes a container runtime or a service.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = 'velvetos.cortendesk.staging_plan.v1'
RELEASE_IMAGE = (
    'ghcr.io/marcpope/cortendesk@'
    'sha256:3f91c02180d6ed59bfa3d4a938b0a52cf01e8fd1e953799be05435234c062373'
)
REQUIRED_FIELDS = frozenset({
    'schema', 'source_release', 'image', 'colima_profile', 'containerd_namespace',
    'embedded_server', 'bind_address', 'host_ports', 'cpus', 'memory_mb',
    'data_mode', 'production_server_mounted', 'production_keys_reused',
    'production_clients_modified', 'test_client', 'secrets',
    'execution_status',
})
PORT_NAMES = frozenset({'console_tcp', 'nat_tcp', 'id_tcp', 'id_udp', 'relay_tcp'})
RESERVED_LIVE = frozenset(range(21115, 21120))


class StagingPlanError(ValueError):
    """Non-sensitive gate reason."""


def validate_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or set(plan) != REQUIRED_FIELDS:
        raise StagingPlanError('plan_schema_fields_invalid')
    if plan['schema'] != SCHEMA:
        raise StagingPlanError('plan_schema_version_invalid')
    if plan['source_release'] != 'v1.13.2' or plan['image'] != RELEASE_IMAGE:
        raise StagingPlanError('image_not_immutable_verified_release')
    if (plan['colima_profile'] != 'velvet-qa' or
            plan['containerd_namespace'] != 'vf-cortendesk-staging'):
        raise StagingPlanError('isolated_runtime_required')
    if plan['embedded_server'] is not True:
        raise StagingPlanError('staging_must_test_bundled_server')
    if plan['bind_address'] != '127.0.0.1':
        raise StagingPlanError('localhost_only')
    if (plan['data_mode'] != 'ephemeral_new_only' or
            plan['production_server_mounted'] is not False or
            plan['production_keys_reused'] is not False or
            plan['production_clients_modified'] is not False):
        raise StagingPlanError('production_state_must_remain_untouched')
    if plan['test_client'] != 'disposable_only':
        raise StagingPlanError('disposable_client_required')
    if plan['secrets'] != 'out_of_band_unique_random':
        raise StagingPlanError('no_default_or_committed_credentials')
    if plan['execution_status'] != 'blocked_pending_permitted_runner':
        raise StagingPlanError('execution_gate_not_cleared')
    if type(plan['cpus']) not in (int, float) or not (0 < plan['cpus'] <= 1):
        raise StagingPlanError('cpu_budget_invalid')
    if type(plan['memory_mb']) is not int or not (512 <= plan['memory_mb'] <= 1024):
        raise StagingPlanError('memory_budget_invalid')
    ports = plan['host_ports']
    if (not isinstance(ports, dict) or set(ports) != PORT_NAMES or
            any(type(port) is not int or port < 1024 or port > 65535 or
                port in RESERVED_LIVE or port in (8080, 8443)
                for port in ports.values())):
        raise StagingPlanError('port_plan_invalid')
    if ports['id_tcp'] != ports['id_udp']:
        raise StagingPlanError('tcp_udp_rendezvous_must_match')
    distinct = [ports['console_tcp'], ports['nat_tcp'], ports['id_tcp'], ports['relay_tcp']]
    if len(set(distinct)) != len(distinct):
        raise StagingPlanError('host_port_collision')
    return {
        'schema': SCHEMA,
        'state': 'STAGING_DESIGN_VALID_RUNTIME_BLOCKED',
        'image_immutable': True,
        'bundled_server_test': True,
        'loopback_only': True,
        'existing_rustdesk_unchanged': True,
        'may_execute': False,
        'reason': 'prior_remote_runtime_launch_denied',
        'next_gate': 'independent_authorized_test_runner_and_disposable_client',
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline CortenDesk staging design gate')
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.plan.stat().st_size > 32_768:
            raise StagingPlanError('plan_too_large')
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        result = validate_plan(plan)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (StagingPlanError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, StagingPlanError) else 'plan_unavailable'
        print(json.dumps({'schema': SCHEMA, 'state': 'REJECTED',
                          'reason': reason, 'may_execute': False}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
