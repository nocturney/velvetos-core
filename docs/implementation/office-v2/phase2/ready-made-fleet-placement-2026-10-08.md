# Ready-made worker placement alternatives — 2026-10-08

Status: SOURCE-RESEARCHED / TWO-HOST CLI BASELINE PASS / NO FLEET SCHEDULER YET.

Owner expectation: prefer existing tools and alternate architectures over building from scratch. Fleet roadmap: three Windows plus at least two Mac Minis; only current Chris Windows and MacMiniOffice.local are connected and verified. Workers can be per-process, browser context, Linux/WSL distro or an interactive native GUI helper; these are not equivalent. Restate won the durable-execution Phase 3A benchmark, but this does not prove hardware-aware fleet scheduling or production authority.

Prebuilt architectures, to compare fairly:
- Restate + existing remote bridge: minimum new infrastructure, remote agent service routing and durable workflows; placement/capacity/failover not proven yet. Restate license is BUSL-1.1 with internal-use grant.
- Restate + HashiCorp Nomad CE: ready-made resource-aware node placement, restart and cross-OS support; Windows service Session 0 cannot directly automate a real user GUI. Nomad CE license BUSL-1.1 permits internal use under additional grant; no new paid support.
- Windmill remote agents: ready-made jobs/worker groups, cross-platform executables; native Windows and remote agent workers are EE/Cloud licensed features. No paid evaluation without cost approval.
- Kestra 2.0: Apache-2.0 general workflow runner and Windows Java21 standalone JAR; requires plugin and community/Enterprise capability assessment.
- Ray 2.59: possible GPU/AI work subpool; Windows beta and multi-node Windows untested, not first choice for a heterogeneous native GUI fleet.

Proof: see worker-fleet-two-host-readback-2026-10-08.json. The same 884736 bytes were SHA256-hashed independently on both real hosts. Both returned sha256 d5d7a4ca0b3763074c62a08ba762c307ab2f986240bd9a267e3a4eed41783976 and postcondition true. This is a valid cross-host remote connector smoke, NOT a queue/placement/agent-failover benchmark.

Next: create equivalent synthetic workload fixture with target OS, capability tag, memory reservation, busy/idle status, exact final hash/readback, cancellation and missing-worker failure. Compare incumbent bridge + Restate-only remote services against Restate+Nomad CE placement and a competing complete workflow platform. Begin on two verified hosts; five-host topology may only be SIMULATED until more hardware is physically connected. Repeat 1/2/4 jobs and measure p50/p95 overall completion, false success, recovery, memory, CPU and human GUI interference. Native Windows GUI work requires an appropriate interactive-session helper; a system service alone cannot provide that. Prefer Playwright BrowserContexts or CLI over full VM per browser task. Add new components only if benchmarked improvements justify operational footprint. No fleet vendor has been installed as part of this research.

## New verified gate: Kestra 2.0 routing is not fully free

Official Kestra 2.0 documentation labels Worker Groups 2.0 (including tag-routed Worker Queues with `workerSelector.tags`) **Enterprise Edition**. Its new gRPC worker/controller transport and Windows Java 21 standalone JAR are real capabilities, but neither proves a free Community multi-host capability router. Keep Kestra queued with a documented EE entitlement/cost gate; do not equate Apache-2.0 core licensing with every distributed-placement feature. Sources: https://kestra.io/docs/whats-new-2-0 and https://kestra.io/docs/enterprise/scalability/worker-group and https://kestra.io/docs/installation/windows (verified 2026-10-08).

Nomad CE 2.0.7 released 2026-09-17. Its `raw_exec` driver is disabled by default, offers no filesystem isolation and is unsuitable as an independent Windows GUI Session 1 executor simply because the agent starts as a service. Use only after scoped LAB admission and a separate interactive helper plan. Sources: https://developer.hashicorp.com/nomad/docs/release-notes/v2-0-x and https://developer.hashicorp.com/nomad/docs/deploy/task-driver/raw_exec . Windmill native Windows and agent workers are EE/Cloud features per official docs: https://www.windmill.dev/docs/misc/windows_workers and https://www.windmill.dev/docs/core_concepts/agent_workers . Ray Windows multi-node is experimental/untested: https://docs.ray.io/en/latest/ray-overview/installation.html .

## Golden Fixture readiness boundary

The new vendor-neutral `golden-fixtures/worker-fleet-placement-loss-postcondition.json` is a **contract draft on the isolated fleet branch**, not an accepted scheduler, and must not be merged until the exact-set `scripts/check-office-v2-phase2.py` sensor is updated and its check-all passes. The existing `scripts/vf_office_v2_golden_fixture.py` performs shape/evidence-key validation but **does not prove the truth of a nested success assertion**: an independently verified SHA-256, host capability match, Session 0 GUI denial, deduplication, remote worker loss, automatic retry and false-success controls require an admitted adapter's postcondition verifier and full receipts. No production bridge/service should be disrupted to fake worker loss. The observed two-host SHA baseline remains manually orchestrated remote invocation, not placement or recovery proof.

Sources:
https://docs.restate.dev/ai/patterns/multi-agent
https://github.com/restatedev/restate/blob/main/LICENSE
https://developer.hashicorp.com/nomad/docs/what-is-nomad
https://github.com/hashicorp/nomad/blob/main/LICENSE
https://www.windmill.dev/docs/core_concepts/agent_workers
https://www.windmill.dev/docs/misc/windows_workers
https://kestra.io/docs/installation/windows
https://docs.ray.io/en/latest/ray-overview/installation.html
https://learn.microsoft.com/en-us/windows/desktop/Services/interactive-services
https://github.com/nocturney/velvetos-core/issues/604
