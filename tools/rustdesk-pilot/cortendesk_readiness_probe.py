"""Read-only Mac/Colima readiness survey for a CortenDesk staging design.

This tool NEVER starts, pulls, deletes or reconfigures a container, accesses
RustDesk databases, reads credentials or probes remote endpoints. The earlier
remote execution denial remains authoritative; output always forbids execute.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
from typing import Any, Callable

from cortendesk_staging_gate import (
    SCHEMA as STAGING_SCHEMA, StagingPlanError, validate_plan,
)

SCHEMA = 'velvetos.cortendesk.readiness.v1'
RESEARCH_NS = 'vf-rustdesk-pilot'
STAGING_NS = 'vf-cortendesk-staging'
PROD_PORTS = (21115, 21116, 21117, 21118, 21119)

# No shell text derived from outside: every command and parameter is fixed
# or strictly validated by validate_plan() before subprocess invocation.
IMAGE_COMMAND = (
    'sudo -n nerdctl -n vf-rustdesk-pilot images --digests '
    '--format "{{.Repository}} {{.Tag}} {{.Digest}}"'
)
NAMESPACE_COMMAND = 'sudo -n nerdctl namespace ls'
GUEST_SOCKET_COMMAND = 'ss -H -lntu'


class ProbeError(ValueError):
    pass


def _run(argv: list[str]) -> tuple[int | None, str]:
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=8, check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, ''
    return completed.returncode, completed.stdout[:32768]


def _port_status(
    port: int, protocol: str, runner: Callable[[list[str]], tuple[int | None, str]]
) -> str:
    if protocol == 'tcp':
        argv = ['lsof', '-nP', '-iTCP:' + str(port), '-sTCP:LISTEN', '-t']
    elif protocol == 'udp':
        argv = ['lsof', '-nP', '-iUDP:' + str(port), '-t']
    else:
        raise ProbeError('unexpected_protocol')
    code, stdout = runner(argv)
    # Exit code 1 means no matching handles for these lsof selectors.
    if code == 1 and not stdout.strip():
        return 'free_at_observation'
    if code == 0 and stdout.strip():
        return 'occupied_at_observation'
    return 'unknown'


def _guest_sockets(stdout: str, code: int | None,
                   ports: dict[str, int]) -> dict[str, str]:
    """Decode only local port occupation from Linux 'ss -H -lntu'.

    Never preserve source IPs, remote endpoints, PIDs, process names or sockets.
    On failure or unrecognized output shape, fail closed as UNKNOWN.
    """
    result = {role: 'unknown' for role in ports}
    if code != 0:
        return result
    observed: set[tuple[str, int]] = set()
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) < 5 or fields[0] not in ('tcp', 'udp'):
            # A nonempty unrecognized response is not proof ports are free.
            return result
        address = fields[4]
        if ':' not in address:
            return result
        port_text = address.rsplit(':', 1)[-1]
        if port_text.isdigit():
            observed.add((fields[0], int(port_text)))
    for role, port in ports.items():
        protocol = 'udp' if role == 'id_udp' else 'tcp'
        result[role] = ('occupied_at_observation'
                        if (protocol, port) in observed
                        else 'free_at_observation')
    return result


def _profile_status(text: str, name: str) -> bool:
    # Exact Colima profile name on an anchored table row; avoid fuzzy matches.
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == name:
            return fields[1].lower() == 'running'
    return False


def _has_namespace(stdout: str, name: str) -> bool:
    return any(line.split() and line.split()[0] == name
               for line in stdout.splitlines())


def _image_cached(stdout: str, digest: str) -> bool:
    # The immutable digest and the tagged upstream repository must match on
    # ONE row; substring-only SHA matches would create false confidence.
    for line in stdout.splitlines():
        parts = line.split()
        if (len(parts) >= 3 and
                parts[0] == 'ghcr.io/marcpope/cortendesk' and
                parts[1] == '1.13.2' and parts[2] == digest):
            return True
    return False


def inspect(
    plan: dict[str, Any],
    runner: Callable[[list[str]], tuple[int | None, str]] = _run,
    *,
    system: str | None = None,
    machine: str | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    # Always validate all plan inputs BEFORE calling any OS tool.
    valid = validate_plan(plan)
    if valid['may_execute'] is not False:
        raise ProbeError('execution_gate_must_remain_blocked')
    system = system if system is not None else platform.system()
    machine = machine if machine is not None else platform.machine()
    if system != 'Darwin' or machine.lower() not in ('arm64', 'aarch64'):
        raise ProbeError('mac_arm64_only')

    profile_code, profiles = runner(['colima', 'list'])
    if profile_code != 0:
        raise ProbeError('cannot_read_colima_profiles')
    qa_running = _profile_status(profiles, 'velvet-qa')
    rustdesk_running = _profile_status(profiles, 'rustdesk')

    ports = plan['host_ports']
    observations: dict[str, str] = {}
    for role in ('console_tcp', 'nat_tcp', 'id_tcp', 'id_udp', 'relay_tcp'):
        proto = 'udp' if role == 'id_udp' else 'tcp'
        observations[role] = _port_status(ports[role], proto, runner)
    production = {
        str(p): _port_status(p, 'tcp', runner) for p in PROD_PORTS
    }
    original_udp = _port_status(21116, 'udp', runner)

    image_cached = False
    staging_namespace_exists = False
    guest_observations = {role: 'unknown' for role in observations}
    if qa_running:
        prefix = ['colima', 'ssh', '-p', 'velvet-qa', '--', 'sh', '-lc']
        code, stdout = runner(prefix + [GUEST_SOCKET_COMMAND])
        guest_observations = _guest_sockets(stdout, code, ports)
        code, stdout = runner(prefix + [IMAGE_COMMAND])
        if code == 0:
            image_cached = _image_cached(stdout, plan['image'].split('@', 1)[1])
        code, stdout = runner(prefix + [NAMESPACE_COMMAND])
        if code == 0:
            staging_namespace_exists = _has_namespace(stdout, STAGING_NS)
    staging_free = (
        all(s == 'free_at_observation' for s in observations.values())
        and all(s == 'free_at_observation'
                for s in guest_observations.values())
    )
    production_present = (all(production[str(p)] == 'occupied_at_observation'
                              for p in (21115, 21116, 21117)) and
                          original_udp == 'occupied_at_observation')
    findings = []
    if not qa_running:
        findings.append('qa_profile_not_running')
    if not rustdesk_running or not production_present:
        findings.append('production_service_unverified')
    if not staging_free:
        findings.append('proposed_host_or_guest_port_conflict_or_unknown')
    if not image_cached:
        findings.append('pinned_image_not_verified_in_research_cache')
    if not staging_namespace_exists:
        findings.append('target_namespace_not_present')
    findings.append('runtime_launch_previously_denied')
    return {
        'schema': SCHEMA,
        'observed_at': observed_at or datetime.now(timezone.utc).isoformat(),
        'state': 'READ_ONLY_SURVEY_RUNTIME_BLOCKED',
        'target_architecture': 'darwin_arm64',
        'profiles': {
            'existing_rustdesk_running': rustdesk_running,
            'isolated_qa_running': qa_running,
        },
        'host_port_status': observations,
        'guest_port_status': guest_observations,
        'staging_ports_free_on_host_and_guest_at_observation': staging_free,
        'production_rendezvous_present_at_observation': production_present,
        'pinned_image_cached_in_research_namespace': image_cached,
        'target_namespace_exists': staging_namespace_exists,
        'findings': findings,
        'may_execute': False,
        'has_performed_mutation': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Safe read-only CortenDesk staging host survey (never deploys)'
    )
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.plan.stat().st_size > 32768:
            raise ProbeError('plan_too_large')
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        report = inspect(plan)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (StagingPlanError, ProbeError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, (StagingPlanError, ProbeError)) else 'survey_unavailable'
        print(json.dumps({
            'schema': SCHEMA, 'state': 'UNAVAILABLE', 'reason': reason,
            'may_execute': False, 'has_performed_mutation': False,
        }, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
