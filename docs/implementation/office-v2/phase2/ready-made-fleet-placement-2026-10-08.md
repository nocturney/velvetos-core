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

## Additional overlooked off-the-shelf systems (2026-10-08)

**Dagu 2.18.2**: self-hosted GPL-3.0 Community tool, one binary, runs on Windows/macOS/Linux; coordinator assigns runs to workers via labels/heartbeats and ships status/logs/artifacts through gRPC. Release provides checksum-pinned Windows AMD64 and macOS ARM64 standalone assets and Sigstore packslip. No required external database and no Community license key. Strong candidate for a 5-host mixed OS fleet; compare carefully against Nomad and Restate-only, especially cancellation, failure/recovery and workflow duplication. Official sources: https://github.com/dagucloud/dagu/releases/tag/v2.18.2 and https://docs.dagu.sh/overview/deployment-models . At candidate-record time NO Dagu binary was installed or tested locally.

**Selenium Grid 4.50**: Apache-2.0, ready-made cross-OS browser node/slot/distributor/queue layer, documented mixed Windows/Mac/Linux nodes; particularly relevant to browser-only computer-use. Unlike full-agent frameworks it controls browser session capacity, not the AI policy, workflow or native CAD GUI. Compare to native Playwright BrowserContexts and browser process pool; Java runtime and browser drivers are additional dependencies (Java not in default PATH/runtime on verified Chris and Mac Mini hosts). Official sources: https://www.selenium.dev/documentation/grid/components/ and https://github.com/SeleniumHQ/selenium/releases/tag/selenium-4.50.0 . At candidate-record time NOT installed/tested locally.

Both candidates are **queued, not rejected or promoted** in the existing Office v2 worker-fleet-placement comparison lane. Source discovery ≠ benchmark; do not claim their tasks succeeded in VelvetOS before measured runs.
