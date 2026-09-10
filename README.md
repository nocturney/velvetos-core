# VelvetOS Core

> **VELVET FACTORY HEADQUARTERS & OS** — an operational AI/business operating system for Velvet Factory, with a reusable Core, governed office control plane, sensors, automations, agents/skills, business memory, media/content pipelines and external-tool integrations.

VelvetOS is no longer just a backend scaffold. This repository is the **system of record for the operating model**: what the office can do, which actions are autonomous vs gated, how work moves from intake to execution, which integrations are actually live, and which sensors prove that the system still behaves as intended.

**Active tenant:** Velvet Factory · Sderot  
**Daily business channels:** Instagram `@velvets_cloud` · WhatsApp `050-2517000` · local pickup in Sderot  
**Start here (Hebrew):** [`docs/START-HERE-HE.md`](docs/START-HERE-HE.md)

---

## What VelvetOS is

VelvetOS is built as three cooperating layers:

1. **Core / Kernel** — reusable laws, modules, schemas, packs, sensors and contracts.
2. **Office / Control Plane** — the operational layer for the active business: intake, jobs, follow-ups, approvals, memory, briefs, media/content work and completion tracking.
3. **Edge (optional)** — machine/floor/host-side execution where a task must leave the office and touch real equipment or a local runtime.

Canonical architecture: [`docs/VELVETOS.md`](docs/VELVETOS.md) · [`packages/velvetos/LAYERS.md`](packages/velvetos/LAYERS.md) · [`packages/velvetos/ADR-THREE-LAYERS.md`](packages/velvetos/ADR-THREE-LAYERS.md)

The design rule is **one source of truth, many views/automations**. New ideas should extend existing SoTs and control planes rather than create parallel mini-systems.

---

## Capability status vocabulary

Status words in this README are deliberate:

- **LIVE / VERIFIED** — external path was verified against the real provider/runtime.
- **IMPLEMENTED** — code + local behavioral checks exist in this repo.
- **GATED** — implemented, but a human/owner or policy gate is intentionally required.
- **OPTIONAL / FAILOVER** — supported path, not the primary runtime.
- **PLANNED** — concept only. Planned work must never be described as operational capability.

---

## Current capability map

### Office Control Plane — IMPLEMENTED

Canonical office coordination lives under `office/control-plane.json`, `office/control/` and the existing VelvetOS packs.

It provides office status/watchdog views, gap detection, follow-ups, WIP → finished bridging, dead-letter handling, handoff/failover state, review, memory hygiene, risk-aware actions and integration with the operating brief.

CLI: `scripts/vf_control_plane.py`  
Sensor: `scripts/check-office-control-plane.py`

### Living Studio — IMPLEMENTED

`packages/velvetos/living-studio/` is the connective tissue between existing sources of truth, not a second operating system.

Its registry currently exposes **22 operational skills/capabilities**, including World Model, Signal Room, Studio Pulse, Universal Intake, Invisible Work, Failure Museum, Lab, Opportunity detection, Commercial QA, Content Universe, Work-to-Story and commissioning.

CLI: `scripts/vf_living_studio.py`  
Sensor: `scripts/check-living-studio.py`

### Universal Intake → existing handlers — IMPLEMENTED

Incoming work can be normalized and routed into existing domain handlers rather than copied into a parallel inbox. Intake is designed to be idempotent and preserve source identity/evidence.

### Jobs state + Google Sheet bridge — IMPLEMENTED / FAIL-CLOSED

VelvetOS has a canonical Velvet Factory jobs model plus a Sheet adapter with pull / push / reconcile behavior.

Important behavior:

- no guessed Sheet tab names
- pre-write remote digest/concurrency guard
- conflicts do not mutate remote state
- provider-unavailable writes remain honestly marked pending/needs-sync instead of pretending success

### Business memory (`vfmem`) — IMPLEMENTED

Memory is part of the workflow before notes, meetings and documents become operational state. Identity gates reduce the risk of attaching client notes to the wrong entity.

### Automation + risk gates — IMPLEMENTED

VelvetOS separates low-risk executable work from actions that require approval. Green/yellow action execution exists, with risk rules designed to tighten safely rather than silently expand authority.

“Autonomous” does **not** mean permission to mutate anything. External writes remain bounded by provider capability, verified auth and business policy.

### Instagram MCP + Insights — LIVE / VERIFIED for supported reads

The canonical Instagram MCP path supports verified Insights reads and public CTA auditing.

Honesty constraints are part of the capability model:

- unsupported profile/caption Graph mutations are not exposed as fake write tools
- publishing is not called live unless explicitly verified
- DM automation remains disabled
- period-incompatible Insights return structured partials instead of fabricated totals

Docs: `vfigos/CHATGPT-MCP.md` · `vfigos/GRAPH-MUTATIONS.md`

### Media Vault + vfmedia intake — IMPLEMENTED

The media flow keeps one catalog/source of truth and separates:

`incoming → source → work-in-progress → approved-for-publishing`

Core rules: upload ≠ approval; approved-folder membership ≠ proof of approval; real bytes/checksums are preserved; moves happen after persistence succeeds; permission changes/destructive cleanup are never inferred.

Docs: [`docs/MEDIA-VAULT.md`](docs/MEDIA-VAULT.md)  
Pack: `packages/vfmedia/`

### Hebrew copy / business-truth QA — IMPLEMENTED

The copy stack includes a Hebrew natural-writing layer with lint/evals and a strict **FACT vs INVENTED** gate.

It must not invent prices in ₪, turnaround, customer facts, print duration or unsupported business claims. Unverified facts become input/fact failures rather than polished fiction.

### Organic Growth / content factory — IMPLEMENTED / HUMAN-GATED

Real work/completion events can become draft Reel/Story ideas, certificates and community-poll candidates, with approval choices in the operating brief.

This does **not** equal automatic publishing: no default autopost, no auto-DM, no invented attribution and no invented prices.

### Production/floor support — IMPLEMENTED as governed planning data

Existing production packs cover machine/material routing, spool/slice balance and maintenance signals from Edge snapshots. Headquarters planning does not imply HQ can physically start a printer without the appropriate Edge/runtime path.

### Gmail operating brief — IMPLEMENTED

The repo contains a Gmail brief path that can produce/send the operating brief when valid Google credentials are available, including HTML + inline media handling.

Workflow: `.github/workflows/gmail-brief-send.yml`  
Module: `packages/vfops/gmail_brief_send.py`  
MCP fallback: [`docs/SEND-BRIEF-MCP.md`](docs/SEND-BRIEF-MCP.md)

### Failover office manager — OPTIONAL / GOVERNED

If the primary ChatGPT operating path is unavailable, VelvetOS defines a controlled takeover/handoff process for other supported assistants/tools without creating a second source of truth.

Docs: [`docs/FAILOVER.md`](docs/FAILOVER.md)

### Agents / skills / specialist rules — AVAILABLE TOOLING

The repository includes a large specialist-agent/rule catalog under `.cursor/rules/`, plus Velvet-specific agents, packs and skill registries.

**Presence alone is not proof of active capability.** README claims must be backed by an active registry, workflow, CLI/handler, source of truth, sensor or verified provider path — not merely by a prompt/rule file sitting in the repo.

### Sensors + CI — ACTIVE

`scripts/check-all.py` discovers and runs the repository's `check-*.py` computational sensors. GitHub Actions runs the sensor suite on pushes and pull requests to `main`, including commission-isolation checks.

Workflow: `.github/workflows/check-all.yml`

Sensors are the executable evidence layer: when documentation says a behavior is implemented, there should ideally be a deterministic check proving its contract.

---

## Operational GitHub workflows

Current workflows include:

- full sensor suite
- Gmail brief send
- Office Control Plane loop
- publish-bridge cleanup
- VelvetOS research
- weekly deck generation
- vfmedia intake

See `.github/workflows/` for the executable list. A workflow file proves the automation exists; a provider-dependent action is only **LIVE** when credentials/runtime have also been verified.

---

## Sources of truth

| Area | Canonical location |
|---|---|
| Core identity | `packages/velvetos/CORE.json` |
| Layer model | `packages/velvetos/LAYERS.md` |
| Event contracts | `packages/velvetos/schema/events.catalog.json` |
| Core modules | `packages/velvetos/modules/` |
| Office control | `office/control-plane.json` + `office/control/` |
| Living Studio | `packages/velvetos/living-studio/` |
| Media catalog | `packages/vfmedia/` |
| Constitution / laws | `constitution/` |
| Sensors | `scripts/check-*.py` |
| Automations | `.github/workflows/` |
| Implemented-change history | [`CHANGELOG.md`](CHANGELOG.md) |
| Agent operating guidance | [`AGENTS.md`](AGENTS.md) |

When two documents disagree, prefer the executable/canonical SoT and fix stale documentation in the same change.

---

## Non-negotiable Velvet Factory constraints

- do not invent ₪ prices
- do not invent customer/order facts
- do not claim external mutation succeeded without provider evidence
- do not invent Origin slugs; keep `unknown` when unknown
- do not silently create a parallel source of truth
- publishing/external communication must respect approval and capability gates
- fulfillment remains local pickup in Sderot unless the canonical business record changes

Origin rules: [`docs/ORIGIN-SLUGS.md`](docs/ORIGIN-SLUGS.md)  
Owner-only operations: [`docs/OWNER-ACTIONS-he.md`](docs/OWNER-ACTIONS-he.md)

---

## Living README contract

**This README is part of the product, not a one-time description.**

Any merged change that materially adds, removes or changes a user/business-facing capability must update this README in the **same change** and normally `CHANGELOG.md` as well.

A README update is required when a change affects one or more of:

- `packages/` capability/runtime behavior
- `office/` operating behavior or source of truth
- `scripts/` operational CLIs, handlers or sensors
- `.github/workflows/` automations
- external integrations or verified status
- autonomy / approval / risk boundaries
- active skills / registries
- business constraints or canonical channels

Documentation-only fixes, formatting, tests that do not change behavior and purely internal refactors may be exempt.

**Definition of Done:** implementation + evidence/sensor + changelog + README capability/status update when applicable.

The README must never upgrade a concept to “implemented” just because scaffolding exists. Use the status vocabulary above and keep provider-dependent claims honest.

---

## Quick health check

```bash
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py instances
python3 scripts/check-all.py
python3 scripts/check-commission-isolation.py
```

---

## Read next

- [`CHANGELOG.md`](CHANGELOG.md) — chronological truth of what changed
- [`AGENTS.md`](AGENTS.md) — operating instructions for AI/dev agents
- [`docs/HARNESS.md`](docs/HARNESS.md) — harness/tooling model
- [`docs/FAILOVER.md`](docs/FAILOVER.md) — controlled office-manager failover
- [`docs/MEDIA-VAULT.md`](docs/MEDIA-VAULT.md) — media source-of-truth workflow
- [`constitution/`](constitution/) — operating laws and authority constraints
- [`packages/velvetos/`](packages/velvetos/) — Core architecture, modules and schemas

---

> **If VelvetOS can really do it, the README should say so. If it cannot prove it, the README should not pretend it can.**
