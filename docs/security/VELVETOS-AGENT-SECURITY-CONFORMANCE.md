# VelvetOS Agent Security Conformance

Status: implementation evidence, **not** a competing policy or approval authority.

Upstream reference: OWASP Secure Agent Playbook, `https://github.com/OWASP/secure-agent-playbook`, CC-BY-4.0.
Reviewed: 2026-09-27. Relevant standalone plays: agent-security-audit, mcp-server-review, prompt-injection-testing, agentic-ai-risk-assess and ai-security-verification.

Canonical machine-readable evidence: `packages/vfharness/security/agent-security-conformance.json`.
Sensor: `python scripts/check-agent-security-conformance.py`.

## Mapped surfaces

| Surface | State | VelvetOS evidence | Notes |
|---|---|---|---|
| MCP | PASS | `check-agent-surface-security.py`, `.cursor/mcp.json`, Project Request Gate | Secret/url checks and authority routing are deterministic. |
| Plugins/connectors | PASS | Project Request Gate, Office policy, behavioral evals | Tool availability does not widen authority; read-only cannot silently become write. |
| Agents | PASS | `vfharness/SKILL.md`, three-layer law, behavioral evals | Handoff is context, not authority; no second production runtime. |
| Control APIs | PASS | `velvetos_control_api` + `check-control-api.py` | Read-first projection; actions fail closed. |
| Browser automation | PARTIAL | AGENTS/ORCHESTRA restrictions + untrusted-content eval | No general browser sandbox/content-isolation enforcement is proven in this phase. |
| Memory | PASS | vfmem/Cognee authority split + `check-vfmem.py` | Recall must map back to canonical evidence before action. |
| Approval boundaries | PASS | Office policy, SEND, delivery approval sensor | Publish/send readiness is distinct from approval. |
| External ingestion | PASS | Project Request Gate + source-ingest contracts | File/web/tool content cannot widen authority. |
| Local eval runner | PARTIAL | pinned Promptfoo + local exec-only config | Script providers are trusted local code, not sandboxed; opt-out flags are not treated as a network sandbox. |

## Prompt-injection scope

The Phase 1 suite covers the authorization consequences that matter to VelvetOS:
untrusted content cannot add authority; memory cannot become authority; a handoff cannot bypass gates; a read-only connector cannot become a writer; publish requires authorization; tool failure cannot be called success; and prompt injection cannot change tool authority.

This is not a claim that every language-model jailbreak technique has been exhaustively defeated. The current suite is a deterministic harness regression layer. Model-level adversarial testing can be added later against a local model or approved zero-incremental-cost target without weakening these hard rules.

## Findings

1. **Browser isolation — PARTIAL.** Policy and behavioral tests are present, but this phase does not prove a general-purpose browser sandbox. Keep browser-fetched content untrusted and require normal authority/read-back gates.
2. **Promptfoo local runner — PARTIAL.** Promptfoo documents custom/script providers as unsandboxed local code. VelvetOS therefore permits only the committed local provider in this suite and supplies no model/API credentials.
3. **Promptfoo network controls are defense-in-depth, not an air gap.** Telemetry, remote generation, sharing and update paths are disabled by the runner, but the integration does not treat those flags as proof of zero network egress. Cost remains zero because no paid provider is configured or called.

## Verification

Run:

`python scripts/check-behavioral-evals.py`

`python scripts/run-promptfoo-evals.py`

`python scripts/check-agent-security-conformance.py`

The Promptfoo run must report 17/17 PASS, a deliberately wrong assertion must fail, reported model cost must remain 0 and token usage must remain 0.
