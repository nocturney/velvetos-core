# VelvetOS Office v2 — Deep Research Report

**Date:** 2026-10-05 (Asia/Jerusalem context; UTC research pass)  
**Role:** Independent technology scout / systems architect (`@research-synthesist` · pack `vfresearch`)  
**Mission:** Capability-first landscape scan for “Best Possible VelvetOS” — not brand nostalgia, not NIH.  
**Cost law:** Prefer free / OSS / self-host / already-paid (`constitution/NO_NEW_RECURRING_COST.md`). Paid products named with *verified model only*; never invent ₪.  
**Anti-bias:** Known list in the research prompt is *context only*. Tools already in that list are not “discoveries.”  
**Method:** Primary GitHub/docs + 2026 comparison sources; awesome-lists used as indexes only. Claims that could not be primary-verified are marked `CONFIDENCE: low` or deferred.

**Incumbent context (VelvetOS today):**
- Control plane / SoT map: `office/control-plane.json`, Living Studio, harness checkpoints — keep as *authority*, not as every implementation.
- Memory: `vfmem` canonical; Cognee derived-only; Deja Vu adjunct (Phase 7).
- Durable work: custom checkpoints + autonomy composition contracts — **no production durable engine**.
- Observability: OpenTelemetry + OpenInference local traces; Healthchecks/changedetection pilots; GlitchTip blocked pending WSL/Docker.
- Business SoT: pack JSON + Drive; CRM/ERP patterns embedded from Twenty/ERPNext/Huly research (2026-08-31) — **not installed as runtimes**.
- Host: Windows + RTX 4080 SUPER primary; Mac mini secondary; WSL2/Docker **planned, not installed** (zero-cost stack evidence).

---

## 1. EXECUTIVE SUMMARY

### 10 most important NEW discoveries

1. **Hatchet** — MIT, Postgres-backed durable task engine; smallest serious self-host footprint vs Temporal cluster. Strong candidate to replace custom checkpoint/retry glue for long agent jobs. https://github.com/hatchet-dev/hatchet  
2. **DBOS** — Library-embedded durable execution on Postgres (TS/Python/Go/Java). Eliminates a separate workflow *server* for office automation. https://github.com/dbos-inc/dbos-transact-py (and sibling SDKs)  
3. **ToolHive (Stacklok)** — Full MCP platform: registry + gateway + container runtime + Cedar authz + OTel. Goes far beyond “MCP proxy.” https://github.com/stacklok/toolhive  
4. **LiteLLM** — De-facto OSS LLM gateway (MIT core): unified OpenAI API, fallbacks, budgets, virtual keys, local+cloud models. Category killer for custom model routing. https://github.com/BerriAI/litellm  
5. **Bifrost** — Go LLM gateway, Apache-2.0, microsecond overhead claims, single-container; challenger when LiteLLM Python ops feel heavy. (Comparisons: https://api7.ai/self-hosted-llm-gateway)  
6. **Spoolman** — Self-hosted filament inventory with Moonraker/OctoPrint integration + MCP server — directly adjacent to `vfprod` filament remainder. https://github.com/Donkie/Spoolman  
7. **PrintFarmer / Teila print-farm-manager** — Self-hosted multi-brand print-farm dashboards (Moonraker, PrusaLink, Bambu, Elegoo). Missing category in VF research. https://github.com/OlyForge3D/PrintFarmer · https://github.com/Teila/print-farm-manager  
8. **Manyfold** — Self-hosted DAM *for 3D print files* (STL/OBJ), not generic photos — complements `vfmedia` creative vault. https://github.com/manyfold3d/manyfold  
9. **Langfuse** — MIT self-host LLM/agent observability + evals (Docker/K8s). Stronger product UI than raw OTel alone; heavier than Phoenix for ops. https://langfuse.com/ · https://github.com/langfuse/langfuse  
10. **OpenFGA + SPIFFE/SPIRE (+ Cedar)** — Agent identity/authorization stack that VelvetOS has not treated as a first-class category. https://openfga.dev/ · https://spiffe.io/ · Cedar policy language

### 5 strongest CATEGORY_KILLER_CANDIDATES

| # | Candidate | Stop building… | Why |
|---|---|---|---|
| 1 | **Hatchet** (bake-off vs DBOS) | Custom durable workflow / resume engine | MIT + Postgres; durable tasks without Temporal ops tax |
| 2 | **LiteLLM** | Custom model router / orchestra glue for provider failover | Already solves fallbacks, keys, budgets, local+API |
| 3 | **ToolHive** | Custom MCP registry + authz + container isolation | Registry API + Cedar + gateway in one OSS platform |
| 4 | **Spoolman + farm manager** | Custom filament/farm telemetry UI | Domain-native; Moonraker/Bambu/Prusa already exist |
| 5 | **Langfuse** (or keep Phoenix-light) | Custom agent observability console | Traces/evals/prompts; OTel-compatible |

### 5 areas where custom is still justified

1. **VelvetOS Control Plane / policy / promotion / rollback** — business locks (CTA, pickup-only, no auto-DM, no invented ₪). No product encodes these laws.  
2. **Hebrew product voice + PUBLIC_CTA + content preflight** (`vfcopy`, `vfgrowth/PREFLIGHT`) — studio-specific quality gates.  
3. **Office graph / seat routing (`vfmem` + `vfgraft`)** — thin, deterministic routing over packs beats a generic knowledge graph *as authority*.  
4. **Organic Growth Decision Pack** — drafts + 07:00 approval; never autopost — intentional anti-bot product.  
5. **Creative Visual OS / Media Vault *policy*** — Asset Truth ≠ Claim Truth; rights/approval semantics are business IP. Storage may be composeable; *authority* stays VelvetOS.

### 5 areas to STOP building until bake-off

1. Any new **durable workflow runtime** inside `vfharness` — evaluate Hatchet vs DBOS first.  
2. Any new **model router / orchestra proxy** — evaluate LiteLLM (primary) vs Bifrost.  
3. Any new **MCP authz/registry** — evaluate ToolHive vs agentgateway (already known) + Docker MCP Gateway.  
4. Any new **print-farm / filament ledger** — evaluate Spoolman + PrintFarmer/Teila before more `vfprod` UI.  
5. Any new **observability product UI** — evaluate Langfuse vs expanding OpenInference+Phoenix before GlitchTip-or-custom.

### Critical answers (short)

| # | Question | Answer |
|---|---|---|
| 1 | Wasting time building? | Durable exec, model gateway, MCP governance, farm telemetry, obs UI, generic CRM/ERP shells |
| 2 | Most custom-code elimination? | LiteLLM + Hatchet/DBOS + ToolHive + Spoolman |
| 3 | Missed categories? | Print-farm MES, filament inventory, 3D-specific DAM, agent identity (SPIFFE/OpenFGA), feature flags, CDC/sync, GPU cluster managers |
| 4 | Re-open? | Temporal (now vs Hatchet), GlitchTip (with WSL), ERPNext/Twenty (as *data SoT*, not Cursor runtime), Windmill (with WSL), Infisical Agent Vault |
| 5 | Explicitly reject (for VF now)? | CrewAI/LangGraph as second office runtime; OpenClaw-family as Production authority; hosted-only gateways that break zero-cost; national-shipping ERPs; auto-DM social agents |
| 6 | Useful after WSL2? | Hatchet/DBOS workers, ToolHive containers, Langfuse stack, Spoolman/Manyfold/PrintFarmer, OpenBao, Redpanda/Debezium, GPUStack, Reef sandbox (already LAB-blocked on Windows) |
| 7 | Windows? | Cursor/HQ desk, DCC (Blender/Adobe/Fusion), slicers, Orca, local GPU inference (Ollama/vLLM-win), Playwright desktop |
| 8 | Mac? | Plus/Pro browser subscriptions host (`vfmcp/HOST.md`), secondary coding agents, light services, Canva-adjacent creative |
| 9 | Linux/WSL? | Containers, durable engines, MCP gateways, observability stacks, farm managers, secrets, CDC |
| 10 | Containers? | All self-host services above; never the Control Plane authority itself |
| 11 | Stateful? | Job/order SoT, media catalog, filament, farm telemetry, secrets, workflow history, CRM/ERP if adopted |
| 12 | Stateless/replaceable? | Model gateway, MCP gateway, workers, renderers, research scrapers |
| 13 | Real SoTs? | VelvetOS policy + business locks; orders/jobs/SKU/media/approvals in *one* domain system each; never duplicate authorities |
| 14 | Reinventing mature software? | Filament inventory, print farm, CRM/ERP/MRP, LLM gateway, durable workflows, DAM for STLs |
| 15 | Strongest architecture today? | See §7 Dream Office |

---

## 2. MISSING CATEGORIES

| Category | Why it matters | Solves | Representative tools |
|---|---|---|---|
| **Print-farm / device fleet management** | Studio has printers; HQ must not Print from agents, but *telemetry + queue* is real | Live status, dispatch, multi-brand | PrintFarmer, Teila print-farm-manager, SimplyPrint (commercial), Obico |
| **Filament / consumable inventory** | `vfprod` tracks remainder ad-hoc | Spool weight, usage CDC from printers | Spoolman (+ SpoolmanDB) |
| **3D-model DAM (not creative DAM)** | `vfmedia` is creative vault; STL libraries are different | Catalog STL/OBJ, tags, ActivityPub optional | Manyfold |
| **Agent identity / workload identity** | Agents ≠ users; long-lived API keys are a time bomb | Short-lived SVIDs, attestation | SPIFFE/SPIRE |
| **Relationship-based agent authorization** | “Agent acting for user on job X” | Delegation, list-objects | OpenFGA, SpiceDB |
| **Credential brokering (not just vault)** | Secrets managers still deliver keys into agent process | Proxy injects creds at boundary | Infisical Agent Vault (known family), Arcade patterns |
| **Feature flags / staged promotion** | LAB/SHADOW/PROD needs mechanical gates | Kill switches, gradual rollout | Flagsmith, Unleash, Flipt, GrowthBook |
| **GPU cluster / multi-machine serving** | RTX 4080 + Mac + future boxes | Schedule models, not ad-hoc | GPUStack, SkyPilot, vLLM, Ray Serve |
| **CDC / operational data sync** | Multiple systems → one office view without glue | Change streams | Debezium+Redpanda, Airbyte, dlt |
| **HITL product (generic)** | Approvals exist but are custom JSON | Channel approvals (Slack/email) | HumanLayer, Arcade templates |
| **Internal knowledge wiki (human)** | Owner memory ≠ searchable ops wiki | Docs for humans + MCP | BookStack, Outline |
| **MES (shop floor execution)** | Between CRM quote and printer G-code | Work orders, job cards | OpenMES, ERPNext Manufacturing |
| **Policy-as-code for tools** | Seat laws hard-coded in sensors | Declarative allow/deny on tool calls | Cedar (in ToolHive), OPA/Rego |

---

## 3. CAPABILITY LANDSCAPE

Scoring scale 0–10 across 20 dimensions (see § scoring legend). **TOTAL VALUE** is a weighted judgment for VelvetOS Office v2 under zero-new-recurring-cost + Windows→WSL path — not a star count.

### Scoring legend (dimensions abbreviated)
Depth · Fit · Modular · Local · AgentNative · API · Reliable · Security · Observ · MaintBurden*(inverse in TOTAL)* · IntegrDiff*(inverse)* · MultiMachine · Win · WSL · Mac · Health · License · RecurringCost*(inverse)* · Lockin*(inverse)* · CodeReduction

### 3.1 Durable workflows / resume

| Candidate | License | Self-host | OS | Strength | Weakness | TOTAL | Conf. |
|---|---|---|---|---|---|---|---|
| **Hatchet** | MIT | Engine + Postgres | Win clients; Linux server best | Small footprint, OTel, agent-oriented | Younger than Temporal | **8.4** | med |
| **DBOS** | OSI (check current) | Library-in-app + Postgres | All | Near-zero infra | Less “ops console” | **8.1** | med |
| Temporal | MIT server | Heavy cluster | Linux | Most mature | Ops tax; known already | 7.2 | high |
| Restate | BSL→Apache | Single binary | Linux | Virtual objects | BSL; not pure OSS | 6.5 | med |
| Inngest | SSPL | Dev server / cloud-first | — | Best DX | Self-host not primary | 5.5 | med |
| Windmill *(known)* | AGPL | Yes | Linux | Scripts+UI | Already explored | — | — |

**Incumbent:** VelvetOS checkpoints + `AUTONOMY-COMPOSITION` contracts.  
**Best:** Hatchet · **Runner-up:** DBOS · **Keep custom?** Policy/state *schema* yes; engine no · **Replace?** Engine yes after bake-off · **Compose?** Hatchet/DBOS *under* VelvetOS control plane · **Benchmark?** Crash-mid-job resume for inquiry→quote→pickup · **Defer?** Temporal until Hatchet fails scale.

### 3.2 Model gateway / orchestra

| Candidate | License | Self-host | Strength | Weakness | TOTAL | Conf. |
|---|---|---|---|---|---|---|---|
| **LiteLLM** | MIT (+ enterprise extras) | Docker+Postgres | Breadth, fallbacks, budgets | Python ops; feature sprawl | **8.6** | high |
| **Bifrost** | Apache-2.0 | Single container | Latency, Go | Smaller ecosystem | **7.9** | med |
| Portkey Gateway | MIT core | Yes | Guardrails+MCP | Enterprise features hosted | 7.0 | med |
| OpenRouter | Hosted | No | Zero ops | Recurring + lock-in | 3.5 | high |

**Incumbent:** `vf_gemini.py` / `vf_chatgpt.py` + orchestra docs.  
**Best:** LiteLLM · **Runner-up:** Bifrost · **Keep custom?** Thin policy adapter only · **Replace?** Provider routing yes · **Compose?** LiteLLM behind VelvetOS failover laws · **Reject:** OpenRouter as primary (cost law).

### 3.3 MCP / A2A gateway & registry

| Candidate | License | Self-host | Strength | Weakness | TOTAL | Conf. |
|---|---|---|---|---|---|---|---|
| **ToolHive** | OSS (verify components) | Docker/K8s | Registry+gateway+Cedar+runtime | Young enterprise platform | **8.3** | med |
| agentgateway *(known)* | Apache-2.0 LF | Binary/K8s | CEL policies, MCP+A2A+LLM | Ops/Rust skill | 7.8 | med |
| Docker MCP Gateway | — | Desktop/containers | Isolation | Weak enterprise RBAC | 6.5 | med |
| IBM ContextForge | Apache-2.0 | Yes | Gateway | Heavier | 6.0 | low |

**Best:** ToolHive (platform) or agentgateway (thin proxy) · **Compose:** ToolHive for governance; keep Cursor MCP binds for HQ send · **Reject:** Building a third custom MCP registry in Core.

### 3.4 Agent identity & authorization

| Candidate | License | Role | TOTAL | Conf. |
|---|---|---|---|---|
| **OpenFGA** | Apache-2.0 | ReBAC for agent-as-principal | **8.0** | med |
| **SPIFFE/SPIRE** | Apache-2.0 | Workload identity | **7.5** | med |
| Cedar | Apache-2.0 | Policy language | **7.2** | med |
| Permit.io | Commercial | Productized PDP | — | — (paid; model not verified here) |

**Incumbent:** Desk laws + sensors (code).  
**Best compose:** SPIFFE for workloads + OpenFGA for app relations + Cedar in MCP gateway · **Keep custom?** Business lock *content* · **Replace?** Ad-hoc permission strings · **Defer:** Full SPIRE until multi-machine containers exist.

### 3.5 Credentials / secrets

| Candidate | Notes | TOTAL | Conf. |
|---|---|---|---|
| OpenBao | LF OSS Vault fork; dynamic leases | **7.8** | med |
| Infisical Agent Vault *(known family)* | Credential *proxy* — key never in agent | **8.2** | med |
| Google Secret Manager *(known)* | Already in ecosystem | 6.0 | high |

**Recommendation:** COMPOSE OpenBao/Infisical storage + Agent Vault-style broker; do not invent Gatehouse-2.

### 3.6 Browser / computer-use

| Candidate | Self-host | TOTAL | Conf. |
|---|---|---|---|
| **Stagehand** | Local Chromium | **7.7** | med |
| Kernel | OSS infra + managed | **7.0** | low |
| Browserbase | Managed | 4.5 | med |
| Steel *(known)* | Self-host option | — | — |
| Playwright *(known)* | Local | — | — |

**Best:** Stagehand + local Playwright for HQ; managed browsers only if lead seat accepts cost · **Keep custom?** Isolation policy yes.

### 3.7 Observability

| Candidate | License | Self-host | TOTAL | Conf. |
|---|---|---|---|
| **Langfuse** | MIT | Docker/K8s (ClickHouse stack) | **8.0** | med |
| Arize Phoenix | ELv2 | Easy local | **7.2** | med |
| OpenTelemetry *(known)* | — | Collector | — | — |
| Opik / OpenLIT *(known)* | — | — | — | — |
| GlitchTip *(known)* | — | Blocked without Docker | — | — |

**Best:** Keep OTel instrumentation; **ADOPT Langfuse or Phoenix for UI/evals** — do not build custom obs console · Phoenix easier pre-WSL; Langfuse better long-term MIT product.

### 3.8 Print farm / filament / MES

| Candidate | Role | TOTAL | Conf. |
|---|---|---|---|
| **Spoolman** | Filament inventory + MCP | **8.5** | high |
| **PrintFarmer** | Farm dashboard + dispatch | **7.6** | med |
| **Teila print-farm-manager** | Multi-brand self-host | **7.5** | med |
| Obico | Failure detection | **6.8** | med |
| OpenMES | Generic MES | **6.5** | low |
| ERPNext Manufacturing *(known)* | MRP/job cards | **7.0** | med |

**Incumbent:** `vfprod` routing docs, no farm product.  
**Best:** Spoolman P0; farm manager P0 bake-off · **Keep custom?** “No Print from HQ” gate forever · **Replace?** Filament remainder tracking.

### 3.9 DAM / PIM / media

| Candidate | Role | TOTAL | Conf. |
|---|---|---|---|
| **Manyfold** | 3D model DAM | **8.0** | high |
| ResourceSpace | General DAM | **6.5** | med |
| Pimcore | DAM+PIM open-core | **5.5** | med |
| Directus / UnoPim *(known)* | Headless/PIM | — | — |
| `vfmedia` | Creative vault + rights | **Keep authority** | high |

**Compose:** Manyfold for printable models; `vfmedia` remains creative/rights SoT · **Reject:** Second creative catalog.

### 3.10 CRM / ERP / MRP / finance

| Candidate | Verdict for VF |
|---|---|
| Twenty / ERPNext / Huly / Monica / Akaunting / Dolibarr / Odoo / NocoBase *(known)* | Patterns already embedded; **re-open as data SoT bake-off**, not Cursor second runtime |
| OpenMES | Interesting MES if ERPNext too heavy |
| MRPeasy / Katana | Paid SaaS — only if lead seat accepts recurring cost (model: vendor SaaS; ₪ not invented) |

**Recommendation:** BENCHMARK Twenty (CRM) + ERPNext Manufacturing *or* OpenMES against pack JSON before writing more pipeline boards.

### 3.11 Knowledge / search / memory

| Layer | Best candidate | Note |
|---|---|---|
| Office routing memory | **vfmem keep** | Already beat Cognee on Phase 7 for *canonical* |
| Human ops wiki | BookStack or Outline | Outline has MCP (2026 claim — verify on install) |
| Vector/hybrid search | Qdrant or pgvector | Infrastructure, not SoT |
| Session continuity | Deja Vu adjunct OK | Do not multiply Mem0 clones |

### 3.12 Skill lifecycle / evals

**Incumbent:** Promptfoo installed (Phase 1).  
**Challengers:** Langfuse experiments, NVIDIA SkillEvaluator *(known)*, agent-skill-eval *(known)*.  
**Recommendation:** KEEP Promptfoo; COMPOSE Langfuse evals later; REJECT building SkillOpt-clone.

### 3.13 Automation / integrations

**Known:** Windmill, Activepieces.  
**New angle:** Hatchet/DBOS for *code-first durable*; keep Activepieces/Windmill for human-visible zaps only after WSL.  
**Reject:** n8n as second brain (license/ops unless lead seat).

### 3.14 Multi-machine / GPU

| Candidate | Fit |
|---|---|
| **GPUStack** | Best small-studio GPU cluster manager |
| SkyPilot | Multi-cluster/cloud — overkill now |
| Ollama / vLLM | Serving engines under gateway |
| KAI Scheduler | Needs Kubernetes — defer |

**Windows:** local Ollama/vLLM · **WSL/Linux:** GPUStack workers · **Mac:** light models / Apple Silicon secondary.

### 3.15 Feature flags / promotion

| Candidate | License | Fit |
|---|---|---|
| Flagsmith | BSD-3 | Best permissive self-host |
| Unleash | AGPL | Mature; enterprise gates SSO |
| Flipt | — | GitOps-light |

**Recommendation:** ADOPT Flagsmith (or Flipt) for LAB→SHADOW→PROD *mechanical* gates; VelvetOS keeps semantic authority.

### 3.16 HITL approvals

| Candidate | Fit |
|---|---|
| HumanLayer | Generic approval channels |
| Arcade templates | MCP-gated tools + approval |
| VelvetOS approval-queue.json | Keep as *SoT projection* |

**Compose:** HumanLayer/Arcade for delivery channels; do not replace business approval *states*.

### 3.17 Social / publishing / intelligence

**Known:** Agent-Reach, OpenShorts, social skill repos.  
**VF law:** HQ sends via tools; no auto-DM; Organic Growth never marks posted.  
**Recommendation:** REJECT autonomous marketing systems that publish without Decision Pack; keep `vfigos` + Canva failover.

### 3.18 Backup / DR / identity infra

- Backup: existing HQ backup routines — COMPOSE restic/Borg or Drive export; do not invent.  
- OpenBao for secrets/PKI.  
- SPIRE when multi-host.

---

## 4. NEW TOOLS NOT ALREADY IN OUR RESEARCH

*(Only architecture-affecting tools **absent** from the prompt’s known list and absent from repo grep 2026-10-05.)*

### 4.1 Hatchet
- **URL:** https://github.com/hatchet-dev/hatchet  
- **Does:** Durable background tasks / agent workflows on Postgres.  
- **Missed because:** Temporal/Windmill crowded the category; Hatchet is the lightweight 2026 default in multiple FOSS comparisons.  
- **Replaces:** Custom resume/retry engines, ad-hoc cron state.  
- **Complements:** VelvetOS control plane, autonomy contracts.  
- **Maturity:** Active (8k+ stars); younger than Temporal.  
- **License:** MIT · **Self-host:** Yes · **OS:** Linux server preferred; clients Win/Mac.  
- **Deps:** Postgres · **Cost:** Free OSS; cloud optional (not required).  
- **Recommendation:** **P0 BENCHMARK** — CATEGORY_KILLER_CANDIDATE.

### 4.2 DBOS Transact
- **URL:** https://github.com/dbos-inc (multi-lang SDKs)  
- **Does:** Durable execution as library on Postgres.  
- **Missed because:** Framed as “library” not “workflow product.”  
- **Replaces:** Same as Hatchet for Python/TS office jobs.  
- **Complements:** Existing Python CLIs (`scripts/vf_*.py`).  
- **Maturity:** Growing; strong architectural fit.  
- **License:** Check current per SDK · **Self-host:** Embedded.  
- **Recommendation:** **P0 BENCHMARK** vs Hatchet.

### 4.3 ToolHive
- **URL:** https://github.com/stacklok/toolhive (+ registry-server)  
- **Does:** MCP registry, gateway, container runtime, Cedar authz, OTel.  
- **Missed because:** Research stopped at agentgateway/9router concepts.  
- **Replaces:** Custom MCP allowlists, ad-hoc server spawn.  
- **Complements:** Cursor MCP binds; Instagram/Gmail tools stay HQ-owned.  
- **Maturity:** Active Stacklok; still young as a platform.  
- **Recommendation:** **P0 LAB** after WSL/Docker.

### 4.4 LiteLLM
- **URL:** https://github.com/BerriAI/litellm  
- **Does:** Unified LLM gateway, fallbacks, budgets, local+API.  
- **Missed because:** Treated as “SDK” not infrastructure.  
- **Replaces:** Custom orchestra routing code paths.  
- **Complements:** `vf_gemini.py` / `vf_chatgpt.py` as thin clients; Ollama/vLLM backends.  
- **License:** MIT core · **Self-host:** Yes · **Cost:** Free; enterprise extras optional.  
- **Recommendation:** **P0 ADOPT** behind VelvetOS laws — CATEGORY_KILLER_CANDIDATE.

### 4.5 Bifrost
- **URL:** (see Maxim/API7 comparisons; project under active Go gateway space)  
- **Does:** High-performance self-host LLM gateway.  
- **Recommendation:** Runner-up bake-off vs LiteLLM if Python proxy latency/ops hurts.

### 4.6 Spoolman
- **URL:** https://github.com/Donkie/Spoolman  
- **Does:** Filament spool inventory; Moonraker/OctoPrint; MCP.  
- **Replaces:** Ad-hoc filament remainder tracking.  
- **Complements:** `vfprod`, farm managers.  
- **License:** Check repo · **Self-host:** Yes · **OS:** Linux/Docker best.  
- **Recommendation:** **P0 ADOPT** (read-only from HQ; humans restock).

### 4.7 PrintFarmer
- **URL:** https://github.com/OlyForge3D/PrintFarmer  
- **Does:** Multi-printer dashboard, discovery, dispatch, Spoolman integration.  
- **Replaces:** Custom farm UI.  
- **Recommendation:** **P0 BENCHMARK** vs Teila; HQ must keep print-start gated.

### 4.8 Teila print-farm-manager
- **URL:** https://github.com/Teila/print-farm-manager  
- **Does:** Multi-brand (Prusa, Bambu, Elegoo, Klipper) self-host farm manager.  
- **Recommendation:** **P0 BENCHMARK** alongside PrintFarmer.

### 4.9 Manyfold
- **URL:** https://github.com/manyfold3d/manyfold  
- **Does:** Self-hosted DAM for 3D print files.  
- **Replaces:** Drive folders as STL library.  
- **Complements:** `vfmedia` (creative) — do not merge SoTs.  
- **Recommendation:** **P1 ADOPT** for printable library.

### 4.10 Langfuse
- **URL:** https://github.com/langfuse/langfuse · https://langfuse.com/docs/deployment/self-host  
- **Does:** Traces, evals, prompts, sessions.  
- **Replaces:** Custom observability UI.  
- **Complements:** Existing OTel/OpenInference.  
- **License:** MIT · **Deps:** ClickHouse+Postgres+Redis (heavier).  
- **Recommendation:** **P1** after WSL; Phoenix as lighter P1 interim.

### 4.11 OpenFGA
- **URL:** https://openfga.dev/docs/use-cases/ai-agent-authorization  
- **Does:** ReBAC including agent principals & MCP authz patterns.  
- **Replaces:** Scattered allow/deny strings.  
- **Recommendation:** **P1 COMPOSE** with control plane.

### 4.12 SPIFFE/SPIRE
- **URL:** https://spiffe.io/  
- **Does:** Workload identity / short-lived SVIDs.  
- **Recommendation:** **P2** until multi-machine container mesh exists; design APIs for it now.

### 4.13 GPUStack
- **URL:** https://github.com/gpustack/gpustack  
- **Does:** GPU cluster manager for vLLM/SGLang etc.  
- **Recommendation:** **P1** when local models become always-on.

### 4.14 Stagehand
- **URL:** https://www.stagehand.dev/ · https://docs.stagehand.dev/  
- **Does:** AI-resilient browser automation on Playwright/Browserbase.  
- **Recommendation:** **P1** for brittle web admin UIs; keep Playwright for deterministic tests.

### 4.15 HumanLayer
- **URL:** https://www.humanlayer.dev/ (YC launch) · GitHub humanlayer/humanlayer  
- **Does:** Approval queues across Slack/SMS/email for agents.  
- **Recommendation:** **P1 COMPOSE** with existing approval-queue SoT.

### 4.16 OpenMES
- **URL:** https://github.com/Mes-Open/OpenMes · https://getopenmes.com/  
- **Does:** Small-manufacturer MES (work orders, MQTT).  
- **Recommendation:** **P2** if ERPNext too heavy for shop floor.

### 4.17 OpenBao
- **URL:** https://openbao.org/  
- **Does:** OSS secrets manager (Vault fork, LF).  
- **Recommendation:** **P1** vs Infisical for local dynamic secrets.

### 4.18 Flagsmith / Unleash / Flipt
- **URLs:** https://www.flagsmith.com/ · https://www.getunleash.io/ · https://www.flipt.io/  
- **Does:** Feature flags / staged rollout.  
- **Recommendation:** **P1** Flagsmith (BSD) for LAB/SHADOW/PROD mechanical gates.

### 4.19 BookStack / Outline
- **URLs:** https://www.bookstackapp.com/ · https://www.getoutline.com/  
- **Does:** Human knowledge base; Outline claims MCP (verify).  
- **Recommendation:** **P2** human wiki; not a replacement for `vfmem`.

### 4.20 Qdrant
- **URL:** https://qdrant.tech/  
- **Does:** Self-host vector+hybrid search.  
- **Recommendation:** **P2** infra under retrieval; never SoT.

### 4.21 Obico
- **URL:** https://www.obico.io/ · https://github.com/TheSpaghettiDetective/moonraker-obico  
- **Does:** AI failure detection for prints.  
- **Recommendation:** **P2** — useful, not control plane.

### 4.22 Redpanda + Debezium
- **URLs:** https://www.redpanda.com/ · https://debezium.io/  
- **Does:** CDC streaming for Postgres → consumers.  
- **Recommendation:** **P2** when multiple domain DBs exist; overkill for JSON packs alone.

### 4.23 Airbyte / dlt
- **URLs:** https://airbyte.com/ · https://dlthub.com/  
- **Does:** ELT/CDC connectors.  
- **Recommendation:** **P2** for SaaS→warehouse; not office kernel.

### 4.24 ResourceSpace / Pimcore
- **URLs:** https://www.resourcespace.com/ · https://pimcore.com/  
- **Does:** General DAM / PIM.  
- **Recommendation:** Prefer Manyfold for 3D; Pimcore only if PIM+DAM unification becomes a lead-seat product (open-core restrictions apply).

---

## 5. RE-OPEN LIST

| Item | Why reopen |
|---|---|
| **Temporal** | Still best maturity; but Hatchet/DBOS change the “too heavy” rejection — bake-off required, not auto-pick Temporal. |
| **Windmill / Activepieces** | WSL/Docker unlocks self-host; keep as *human automation UI*, not agent brain. |
| **GlitchTip** | Explicitly blocked pending containers — revisit with WSL batch. |
| **Twenty / ERPNext** | Pattern-only embed was right for Cursor; wrong if Office v2 needs real CRM/MRP SoT. Reopen as **data systems**, not second orchestrator. |
| **Infisical / Agent Vault** | Credential *broker* thesis matured in 2026 — more important than “another secrets UI.” |
| **Reef** | Already LAB_ONLY; WSL+local model endpoint changes feasibility. |
| **agentgateway** | Still strong; ToolHive may subsume more of the registry story — compare, don’t ignore. |
| **Phoenix / OpenInference** | Already in stack path; decide UI product (Phoenix vs Langfuse) instead of infinite custom spans. |
| **Ollama / local models** | Host baseline noted “not installed”; GPUStack+LiteLLM make them first-class. |

---

## 6. BUILD / ADOPT / COMPOSE MATRIX

| Subsystem | Verdict | Notes |
|---|---|---|
| Memory (office graph) | **KEEP_CUSTOM** | vfmem SoT; Cognee derived-only |
| Session/context continuity | **COMPOSE** | Deja Vu/session tools + durable engine checkpoints |
| Agent runtime | **KEEP_CUSTOM** (Cursor/HQ) + **REJECT** second swarm | No CrewAI/OpenClaw Production |
| Durable workflows | **BENCHMARK** → likely **REPLACE** engine | Hatchet vs DBOS |
| Browser runtime | **COMPOSE** | Playwright + Stagehand; managed only if paid OK |
| Model gateway | **ADOPT** | LiteLLM (Bifrost alt) |
| MCP/A2A gateway | **ADOPT/COMPOSE** | ToolHive or agentgateway |
| Skill lifecycle | **KEEP_CUSTOM** + Promptfoo | No SkillOpt clone |
| Credentials | **ADOPT/COMPOSE** | OpenBao/Infisical + broker pattern |
| Observability | **ADOPT** UI + **KEEP** OTel | Langfuse/Phoenix |
| Automation/integrations | **DEFER** Windmill | After WSL; code-first durable first |
| Internal apps | **COMPOSE** | NocoBase/Twenty UI patterns on capabilities.json |
| CRM | **BENCHMARK** | Twenty vs pack JSON |
| ERP/MRP/MES | **BENCHMARK** | ERPNext vs OpenMES vs packs |
| PIM | **DEFER** | UnoPim/Pimcore only if SKU explosion |
| DAM creative | **KEEP_CUSTOM** policy | vfmedia |
| DAM 3D models | **ADOPT** | Manyfold |
| Finance | **COMPOSE** | Akaunting patterns / vfbooks; no invented ₪ |
| Knowledge/search | **COMPOSE** | BookStack human + Qdrant infra |
| Scheduler | **COMPOSE** | Existing calendar ops + durable engine timers |
| Multi-machine execution | **ADOPT** | GPUStack when local models live |
| Control center | **KEEP_CUSTOM** | VelvetOS control plane authority |
| Publishing | **KEEP_CUSTOM** | vfigos + SEND.md |
| Social intelligence | **KEEP_CUSTOM** | vfresearch; reject autopost agents |
| Device/factory | **ADOPT** | Spoolman + farm manager |
| Feature flags | **ADOPT** | Flagsmith/Flipt |
| HITL delivery | **COMPOSE** | HumanLayer channels + VF approval SoT |
| CDC/sync | **DEFER** | Until multi-DB |
| Backup/DR | **COMPOSE** | Existing HQ backup |

---

## 7. DREAM OFFICE ARCHITECTURE (if inheriting today)

```
User / Chat / Owner (Cursor · Grok Bot · Mac Plus/Pro host)
        │
        ▼
┌───────────────────────────────────────────┐
│ VelvetOS CONTROL PLANE (KEEP)             │
│ policy · seats · CTA · SoT map · gates    │
│ promotion LAB→SHADOW→PROD · Flagsmith     │
│ approval states · organic growth locks    │
└───────────────────────────────────────────┘
        │
        ├─► Agent runtimes (Cursor HQ; optional LAB Reef/Laya SHADOW)
        │
        ├─► Durable execution: Hatchet OR DBOS (REPLACE custom engine)
        │
        ├─► Gateways
        │     · LiteLLM (models: API keys + Ollama/vLLM via GPUStack)
        │     · ToolHive / agentgateway (MCP/A2A + Cedar)
        │     · Credential broker (Infisical Agent Vault / OpenBao)
        │
        ├─► Domain systems (ONE SoT each)
        │     · CRM: Twenty (or keep packs until bake-off)
        │     · Jobs/MRP: ERPNext Manufacturing OR OpenMES
        │     · Filament: Spoolman
        │     · Farm telemetry: PrintFarmer/Teila (start gated)
        │     · Creative media: vfmedia
        │     · 3D library: Manyfold
        │     · Finance: vfbooks + Akaunting-class (verified numbers only)
        │
        ├─► Execution workers
        │     · Windows: DCC, slicers, Playwright/Stagehand, GPU inference
        │     · WSL/Linux: containers for gateways, farm, obs, secrets
        │     · Mac: subscription browsers, secondary agents
        │
        ├─► Observability: OTel → Langfuse/Phoenix + Healthchecks
        │
        ├─► Data/memory
        │     · vfmem (routing SoT) · BookStack (human wiki)
        │     · Qdrant/pgvector (derived retrieval only)
        │
        └─► Infra: Docker/WSL · Postgres · OpenBao · optional Redpanda later
```

**Authority rule:** VelvetOS decides *whether*; products decide *how*. Never two SoTs for the same domain.

---

## 8. THINGS VELVETOS SHOULD PROBABLY STOP BUILDING ITSELF

1. Another durable workflow / checkpoint *engine* — buy Hatchet/DBOS semantics.  
2. Another LLM provider router — LiteLLM.  
3. Another MCP registry/authz layer — ToolHive/agentgateway.  
4. Filament inventory UI — Spoolman.  
5. Print-farm dashboard — PrintFarmer/Teila.  
6. Custom observability product UI — Langfuse/Phoenix.  
7. Generic CRM/ERP screens that reinvent Twenty/ERPNext DocTypes.  
8. Second creative media catalog.  
9. Autopost/auto-DM “growth runtime.”  
10. Skill-optimizer product when Promptfoo+Langfuse exist.  
11. Multi-machine GPU scheduler from scratch — GPUStack.  
12. Secrets UI / lease engine — OpenBao/Infisical.  
13. Feature-flag service — Flagsmith/Flipt.  
14. STL Drive-folder “DAM” — Manyfold.

---

## 9. THINGS THAT SHOULD REMAIN VELVETOS-NATIVE

| Native | Challenge |
|---|---|
| Control plane / SoT map / Don’t-Bother-Christian policy | Could UI be NocoBase? Yes. Could *authority* leave? **No.** |
| Business locks (pickup, CTA, no ₪ invent, no Insights invent) | No external product will encode Hebrew studio law correctly |
| Organic Growth Decision Pack semantics | External “marketing agents” violate by default |
| Hebrew voice + preflight fail-closed | Keep |
| vfmem office graph for *who handles* | Generic RAG is not a seat map — keep thin |
| SEND.md HQ-send-via-tools discipline | Productize as policy, don’t outsource publishing brain |
| Asset Truth ≠ Claim Truth (vfmedia) | Storage can be S3; policy stays |
| Sensors (`check-*.py`) as computational law | Keep; don’t replace with LLM judges for ILS/send |

**Challenge to native assumptions:** Pipeline board + customer timeline *views* are not sacred — Twenty/Monica patterns may replace the *UI* while VelvetOS keeps event contracts.

---

## 10. EXPERIMENTAL SHORTLIST

### P0 — before Office v2 architecture freezes

| Item | Setup | OS | WSL/Docker | Payoff | Incumbent | Bake-off test |
|---|---|---|---|---|---|---|
| LiteLLM | Low | Win OK / Linux better | Nice | Kill custom model router | vf_chatgpt/gemini scripts | Fail over Gemini↔ChatGPT↔Ollama on one OpenAI-compatible client; budget cap works |
| Hatchet vs DBOS | Med | Linux server | **Yes** | Kill custom durable engine | vfharness checkpoints | Kill worker mid-inquiry workflow; resume exactly once; idempotency key honored |
| Spoolman | Low | Docker | **Yes** | Real filament SoT | vfprod remainder notes | Printer usage decrements spool; MCP read from HQ; no invented grams |
| PrintFarmer vs Teila | Med | Docker/Win? | Likely | Farm visibility | none | Discover printers; show status; **refuse start-print from agent role** |
| ToolHive (or agentgateway) | Med | Linux | **Yes** | MCP governance | ad-hoc MCP binds | Register 3 MCP servers; Cedar deny on publish_story; audit log |

### P1 — high value

| Item | Setup | OS | WSL | Payoff | Incumbent | Bake-off |
|---|---|---|---|---|---|---|
| Langfuse or Phoenix | Med–High | Linux | Yes | Obs UI + evals | OTel local | Trace one HQ send path end-to-end; PII redacted |
| Manyfold | Med | Docker | Yes | 3D library | Drive folders | Import 20 STLs; tag SKU; search; no rights claim without vfmedia |
| OpenBao or Infisical + broker | Med | Linux | Yes | Short-lived creds | env keys | Agent tool call never sees raw API key |
| Flagsmith/Flipt | Low | Docker | Yes | LAB/SHADOW gates | docs/json | Flag blocks Production publish path |
| GPUStack + Ollama/vLLM | Med | Win GPU + Linux | Partial | Local model lane | none | Serve one model; LiteLLM routes to it |
| HumanLayer compose | Low | SaaS/self | Optional | Approval channels | approval-queue.json | Orange approval reaches Slack; state remains VF SoT |
| Twenty CRM shadow | High | Docker | Yes | Real CRM | pack JSON | Import 10 leads; no second pipeline authority |

### P2 — interesting

| Item | Notes |
|---|---|
| OpenMES | If manufacturing DocTypes needed without full ERPNext |
| BookStack/Outline | Human wiki + optional MCP |
| Qdrant | Derived retrieval only |
| Obico | Failure detection |
| Redpanda+Debezium | After multi-DB |
| SPIFFE/SPIRE | Multi-machine identity |
| Stagehand | Brittle web UIs |
| OpenFGA | When agent principals multiply |
| ResourceSpace/Pimcore | Only if general DAM/PIM mandated |

---

## POPULAR TOOLS TO EXPLICITLY REJECT (for Production Office v2 now)

| Tool | Why |
|---|---|
| CrewAI / LangGraph / AutoGen as office runtime | Second brain; violates harness lock |
| OpenClaw-family as Production authority | Known/explored; not VF control plane |
| OpenRouter as primary gateway | Recurring + lock-in vs LiteLLM self-host |
| Autopost Instagram agents | Violates ORGANIC_GROWTH |
| National-shipping ERP modules as default | Business lock: pickup Sderot only |
| Building GlitchTip before Docker/WSL | Already correctly blocked |
| Replacing vfmem with Mem0/Supermemory as SoT | Phase 7 evidence says no |
| Treg | Constitution: not relevant |

---

## SOURCES (primary + 2026 comparisons)

- Hatchet: https://github.com/hatchet-dev/hatchet  
- Durable comparisons: https://turion.ai/blog/temporal-vs-restate-vs-hatchet-vs-inngest-durable-execution-agents-2026/ · https://systhoughts.com/posts/durable-workflows-for-architects · https://cloudrps.com/blog/durable-execution-restate-dbos-hatchet-beyond-temporal/  
- ToolHive: https://github.com/stacklok/toolhive · https://github.com/stacklok/toolhive-registry-server  
- MCP gateway landscape: https://vdf.ai/blog/mcp-gateway-comparison/  
- LiteLLM: https://github.com/BerriAI/litellm · https://contabo.com/blog/best-llm-gateways/ · https://api7.ai/self-hosted-llm-gateway  
- Spoolman: https://github.com/Donkie/Spoolman  
- PrintFarmer: https://github.com/OlyForge3D/PrintFarmer  
- Teila farm: https://github.com/Teila/print-farm-manager  
- Manyfold: https://github.com/manyfold3d/manyfold  
- Langfuse self-host: https://langfuse.com/ · https://github.com/langfuse/langfuse-docs  
- OpenFGA agents: https://openfga.dev/docs/use-cases/ai-agent-authorization  
- SPIFFE agents: https://uberether.com/from-long-lived-api-keys-to-short-lived-svids/  
- GPUStack: https://github.com/gpustack/gpustack  
- Stagehand: https://www.stagehand.dev/  
- OpenMES: https://github.com/Mes-Open/OpenMes  
- OpenBao: https://openbao.org/  
- Feature flags: https://abtesting.cc/blog/open-source-feature-flags/  
- Infisical Agent Vault: https://infisical.com/blog/agent-vault-the-open-source-credential-proxy-and-vault-for-agents  
- Prior VF research: `packages/vfresearch/sources/2026-08-31-office-os-crm-erp.md` · `docs/implementation/velvetos-zero-cost-agent-stack.md` · `docs/AUTONOMY-COMPOSITION.md`

---

## CHECKPOINT / CONFIDENCE

- **Research confidence overall:** medium-high on category gaps; medium on individual TOTAL scores (desktop bake-offs not run in this pass).  
- **Not done in this pass:** live installs, license SPDX deep-dive for every dependency, verified paid pricing tables, Windows-native farm manager install tests.  
- **Next session:** P0 bake-offs only after WSL/Docker authority; do not freeze Office v2 architecture without LiteLLM + durable-engine decision.

**Status:** `component_state: Idle` after report delivery · Research artifact ready for synthesis into VelvetOS Office v2.
