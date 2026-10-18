# CrewAI pilot E5 - network evidence specification (ChatGPT-060)

Status: SPEC_ONLY / NO_RUNTIME_ADMISSION. Host: Windows Chris. Pilot root: `D:\Velvet\Pilots\OfficeV2-VerifiedTrio`. Ollama: `127.0.0.1:11435`, `qwen3.5:9b`.

Authority: [#612 owner E3 accept-risk with mandatory zero pilot listeners](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075), [runner PR #789](https://github.com/nocturney/velvetos-core/pull/789), [pilot runbook](pilot-runbook-crewai.md).

## E5 admission contract

E5 is PASS only with (1) independently verified OS-level deny-by-default ingress and egress, except the single loopback Ollama peer; (2) effective process-tree coverage including short-lived children; (3) no pilot-owned TCP Listen sockets, UDP binds, or remote endpoint other than exact IPv4 `127.0.0.1:11435`; (4) valid before, during and after snapshots; (5) independently reviewed process identity, firewall and event evidence. Inherited pre-existing connections and unknown endpoints fail. The Ollama *server* listener is a separate non-pilot process, not an exception for pilot-owned listeners. Do not allow IPv6 `::1`, `localhost`, proxy endpoints, or another Ollama port by alias.

`Get-NetTCPConnection` and `Get-NetUDPEndpoint` are instantaneous views. Sampling at 250 ms (or any interval) can miss transient sockets, processes that exit between enumeration and snapshot, and outbound attempts denied before a socket appears. Therefore **snapshot-only evidence cannot establish E5 PASS**. The supplied PowerShell collector deliberately produces `FAIL_CLOSED_OBSERVATION_ONLY`, never `enforcement_proven=true` or `process_tree_complete=true`. No fabricated continuous monitoring. The Python validator refuses these flags unless a separately reviewed enforcement/monitoring implementation establishes them. A JSON flag alone is not proof; the reviewer must verify provenance and OS enforcement evidence.

## Evidence acquisition and interpretation

The operator must obtain explicit runtime authorization and E1-E7 admission before starting pilot #1. Use a preapproved least-privileged process identity; do not install, modify firewall rules, touch C:, use SYSTEM/admin, or run an unreviewed executable. This script is observational and must not be treated as permission to run the pilot.

PowerShell 5.1+ collector: `scripts/collect-crewai-e5-network.ps1 -PilotPid <pid> -ReceiptDirectory D:\Velvet\Pilots\OfficeV2-VerifiedTrio\receipts -DuringSeconds 10`. It collects a process-tree snapshot before, repeated during, and after the requested interval; it does **not** launch or stop the runner. Start it while the pilot PID exists, before the authorized workload, and ensure the run fits inside the observation window. The caller must additionally retain trusted start/exit times and PID birth identities; PID reuse and exited descendants remain unproven by this collector. If the root is absent, any snapshot is missing, cmdlet fails, process lineage is ambiguous, or monitoring is incomplete: FAIL. A TCP `Listen`, any UDP binding, any non-loopback remote or wrong port: FAIL. A lack of observed violations is **not** E5 PASS.

The receipt `e5-network-observation.json` includes UTC start/end and per-phase timestamps, PIDs, TCP/UDP records, errors and explicit non-admission flags. `e5-network-hash.json` stores SHA-256 of the exact receipt bytes and UTC creation time (not a self-referential hash). Verify the hash independently and retain original bytes on D:. Never commit real host receipts, process inventories or secrets.

Offline sensor: `python3 scripts/check-crewai-e5-network.py --selftest` or `python3 scripts/check-crewai-e5-network.py <fixture.json>`. Fixtures cover listener, non-loopback, wrong port, missing phase, UDP, coverage and enforcement failures. Synthetic PASS tests only the predicate; they do not attest a real run. Integrate in `check-all` as a DOMAIN sensor. CI cannot prove Windows host behavior, OS enforcement, C: containment or actual E5 admission.

## Stop and rollback

On any listener, unauthorized remote, wrong port, UDP endpoint, missing phase, monitor failure, unknown child, absent OS denial evidence, or mismatched receipt SHA: **STOP / E5 BLOCKED**. The authorized operator stops only pilot-owned processes using the reviewed kill harness, preserves the original receipts and independent deny logs on D:, and requests fresh owner review. Do not reconfigure Ollama, global firewall, system services, C:, Fleet/SYSTEM, or production resources. E3 accept-risk is not an E5 waiver.
