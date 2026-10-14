# Owner-submitted assurance, security and binary tools — routed intake (2026-10-14)

**Action:** The owner requested integration of three repositories into the existing work pipeline. **State:** RESEARCH_ROUTED_NOT_EXECUTED. This is a capability/evidence intake, not a download, installation, credential grant, pentest authorization, new scheduler, production writer, tool-effect policy or completed LAB benchmark.

**Canonical registry:** [`candidate-registry-v0.json`](candidate-registry-v0.json) (128 -> 131). **Immutable source receipt:** [`owner-assurance-binary-tools-intake-2026-10-14.json`](owner-assurance-binary-tools-intake-2026-10-14.json) (three source identities and exact pinned commits, not a second registry). Historical source import of 68 and 82-item sensor prefix remain unchanged. No P0 shortlist changes.

## Existing workstream placement

| Candidate / immutable upstream | Existing owner / workstream | Concrete next gate | Safety and cost limitation |
| --- | --- | --- | --- |
| [iFixAi agent assurance and governance evaluator](https://github.com/ifixai-ai/iFixAi/tree/d86ba616fa4736b1239e63dd2422fa152cebf7da) (`candidate-ifixai-ai-ifixai`) | [#612](https://github.com/nocturney/velvetos-core/issues/612) / `agent-quality` | After the verified #612 reference run, compare pinned iFixAi mock/no-telemetry synthetic permission, prompt-injection and destructive-action fixtures against Promptfoo and canonical postcondition checks; collect same-task false-positive/false-negative, evidence coverage, operator time and incremental resource cost. | Evaluators are not effect authorities; no production enforcement replacement, no paid provider/judge calls and no scorecards with customer/secret material. |
| [PentAGI isolated autonomous penetration-testing system](https://github.com/vxcontrol/pentagi/tree/843dfeb4bfc809c09d1bc5022e567c602d8fc9dd) (`candidate-vxcontrol-pentagi`) | [#595](https://github.com/nocturney/velvetos-core/issues/595) / `security-assurance` | Audit pinned v2.2.0+ release, CVE-2026-14784 remediation and Docker worker/network defaults; cost/license review, then design an isolated no-credential/no-production-target synthetic security fixture with explicit scope and teardown; score against deterministic existing security checks. | Security-critical: do not install on the privileged primary workstation/production hosts, attach host docker.sock, expose callback ports, scan live systems, or launch autonomous tools from a registry entry. |
| [Ghidra native binary reverse-engineering toolkit](https://github.com/NationalSecurityAgency/ghidra/tree/918acd744d17e3b95fbde44ec6ab3e59b6dbd45f) (`candidate-nsa-ghidra`) | [#606](https://github.com/nocturney/velvetos-core/issues/606) / `shipped-artifact-analysis` | When #606 has a concrete shipped-binary integration blocker, benchmark pinned Ghidra headless/PyGhidra versus the existing REA/read-only deterministic path on the same authorized PE subset: decompilation fidelity, evidence/provenance, false positives, CPU/RAM, time and safe teardown. | Not a CAD tool and not a production agent; no binary mutation, firmware exploitation, privilege escalation, unnecessary installation or automatic startup. |

These are **phase-routed only** (`evaluation_route`), not additional `p0-shortlists-v0.json` active or queued agent-runtime challengers. The canonical Phase 2 `COMPETITOR_NEUTRAL_ADMISSION_V1` permits component replacement and hybrid comparisons when target-specific evidence warrants them. Existing #612 P0 execution, #606 parked P1 status, production effect policies and the `NO_NEW_RECURRING_COST` gate retain precedence.

## iFixAi — agent and policy quality (existing QA owner #612)

- Source: `ifixai-ai/iFixAi` at `d86ba616fa4736b1239e63dd2422fa152cebf7da` (observed 2026-10-14); Apache-2.0; Python 3.10+. Repository HEAD advertises 60 inspections, 10 default, and exposes an HTTP test endpoint or in-process `ChatProvider` hooks.
- Baseline: retain existing Promptfoo, Office Golden Fixture `agent-approval-effect-reconciliation`, exact postcondition evidence and policy decision authority. Compare on identical synthetic role/tool restrictions, destructive-action denial, prompt injection, ungrounded claim, failure disclosure and recovery fixtures.
- Start with local/mock and `IFIXAI_TELEMETRY=0` / `--no-telemetry`. No remote agent or judge call without an independent, scoped cost/data preflight. A default suite may make hundreds of model/judge calls; do not assume a free tool equals free inference.
- A fixture-declared policy, self-judge and `insufficient_evidence` result cannot establish live enforcement; require trusted authorization/audit-trail capability hooks and measured negative controls. Reports/checkpoints may contain full prompts/responses: store only in access-controlled LAB artifacts.
- Next owner: [#612](https://github.com/nocturney/velvetos-core/issues/612). First independently verified source-to-PR baseline, then bounded comparison and standard scorecard with false passes/fails, judged coverage, operator effort and incremental spend.

## PentAGI — authorized security LAB (existing intake owner #595)

- Source: `vxcontrol/pentagi` at `843dfeb4bfc809c09d1bc5022e567c602d8fc9dd`; MIT source with EULA/third-party service constraints requiring review. Documented minimum: Docker/Compose, 2 vCPU, 4 GB RAM, 20 GB free disk. Optional stacks can use substantially more.
- **Security gate:** v2.2.0 release (2026-10-05) states the fix for `CVE-2026-14784`, affecting <=2.1.0 with `DOCKER_INSIDE=true` host socket exposure. The worker must not mount the primary/host Docker socket. Require isolated hardened dind/TLS, deny-by-default egress, no production secrets, policy attestation, constrained CPU/RAM/storage, teardown and verified patched release.
- Beware callback ports (`DOCKER_PUBLIC_IP=0.0.0.0` default in project documentation) even if the Web UI is loopback-only. Prove firewall isolation before LAB. No live scanner, production target, privilege-bearing connection or broad credentials are authorized by source intake.
- Only a synthetic owned target and explicit permitted test scope qualify for later independent admission. Compare with incumbent deterministic checks, record true/false finding rates and full resource/network accounting. Cloud model/search/premium endpoints are never inferred free.
- Next owner: [#595](https://github.com/nocturney/velvetos-core/issues/595), Phase 3B/4 security-assurance triage; no contention with [#612](https://github.com/nocturney/velvetos-core/issues/612) P0 capacity.

## Ghidra — parked shipped-app binary investigation (#606)

- Source: `NationalSecurityAgency/ghidra` at `918acd744d17e3b95fbde44ec6ab3e59b6dbd45f`; Apache-2.0. The latest inspected official release was `12.1.4` (2026-09-21), requiring 64-bit JDK 25. Check upstream security advisories and licenses again before any install.
- Place beside the already completed read-only `REA 5.0.0` pilot and signed PE sidecar reconciliation in [#606](https://github.com/nocturney/velvetos-core/issues/606); **do not** replace CUA/Windows UIA investigations or treat availability as an independent reason to unpark the P1 issue.
- Trigger only on a concrete authorized shipped binary or firmware-analysis blocker. Run on a copy, preferably bounded offline headless/PyGhidra, compare native decompilation evidence/coverage/false positives/time/memory with existing deterministic/REA methods, and preserve original file, signatures, hashes and source attribution.
- Do not install an autostart service, instrument another user's binaries without rights, execute/modify target code, or displace Office P0 host/worktree capacity. Any integration into STOW/LOCAL3D requires an independently owned, concrete issue.

## Common admission and evidence checkpoints

1. **Research now:** the canonical registry has exactly three new `RESEARCHED / BENCHMARK_REQUIRED / NOT_RUN / NONE` records, explicit comparison rationale, immutable upstream commit pins, issue owner, phase route, next action and unlock gate.
2. **Before LAB:** confirm executable contract and incumbent baseline, pinned license/dependency trust, threat model and target rights, hardware/isolation/resources, zero-incremental-cost evidence, rollback/teardown, scoped artifact paths, and direct owner/admission authority. A workflow reference or public GitHub source is not proof of installation.
3. **During isolated LAB:** use synthetic data, no new paid model/API calls, no production credentials/writers, bounded egress, CPU/RAM and storage capture, identical Golden Fixture semantics wherever applicable and negative controls.
4. **Promotion:** only through the existing `RESEARCHED -> CANDIDATE -> ADMITTED -> LAB -> SHADOW -> PILOT -> PRODUCTION` gate. Record a comparative scorecard and verified receipt; no silent installation, daemon, scheduler, security authority or production writer.

**Local policy references:** [candidate admission](admission-policy-v0.md) · [Phase 2 overview](README.md) · [`NO_NEW_RECURRING_COST`](../../../../constitution/NO_NEW_RECURRING_COST.md) · [#595](https://github.com/nocturney/velvetos-core/issues/595) · [#612](https://github.com/nocturney/velvetos-core/issues/612) · [#606](https://github.com/nocturney/velvetos-core/issues/606).
