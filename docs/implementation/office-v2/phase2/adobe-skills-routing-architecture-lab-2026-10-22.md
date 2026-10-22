# Adobe Skills isolated lab and routing-architecture review — 2026-10-22

**Status:** LOCAL LAB VERIFIED (bounded Adobe Web checks) / ARCHITECTURE COMPARISON OPEN / NOT PRODUCTION.  
**Owner scope:** Evaluate and selectively integrate `adobe/skills` as a reusable capability source; consider whether VelvetOS' capability architecture should change.  
**No production writer, publication, permission expansion, new recurring cost, global plugin rollout or policy bypass authorized by this record.**

## Sources and observed runtime

- Adobe upstream: <https://github.com/adobe/skills> (Apache-2.0); observed HEAD during review `a731f0af85460c6d7113fc5ca771e23c91ea4e8c`. HEAD observation is **not** a reproducible lock to plugin cache bytes.
- Impeccable dependency: <https://github.com/pbakaus/impeccable> (Apache-2.0); observed HEAD `8644175285360c166e57b1e35ecadfbc85ff5209`. VelvetOS already has its own pinned Impeccable wrapper; this lab is **not** approval to replace that pin.
- Host: `MacMiniOffice2.local`. Isolated directory: `~/Velvet/Pilots/AdobeSkillsLab-20261022`. Claude Code 2.1.304, Node 24.21.0, Chrome 155.
- **Installed with `--scope local` in lab only:** `web@adobe-skills` 1.0.0 (11 skills), `stardust@adobe-skills` 0.34.1 (16 skills), `impeccable@impeccable` 4.7.0 (1 skill). Verified via `claude plugin list` / `claude plugin details`. No settings edits outside the local lab installation scope were requested; downloaded marketplace and plugin caches live under Claude's shared user cache.
- Local supporting CLI: `@playwright/cli@0.1.22` (Apache-2.0), installed to lab `node_modules` with `--no-save --ignore-scripts --no-audit --no-fund`; not globally installed. It successfully opened and closed **nonpersistent headless Chrome** `about:blank`.
- Adobe Creative Cloud/Firefly connectors **not installed or authenticated**: Adobe account/entitlement/API cost unverified. No Creative Cloud asset editing, AEM deployment, customer operation or paid provider call in this lab.

### Executed synthetic checks (not production acceptance)

| Check | Observed result | Meaning |
| --- | --- | --- |
| `web site scan` using local synthetic sitemap | PASS; exit 0; 2 discovered URLs; language `en-US`; 256 ms | Static source discovery works on a controlled origin |
| `web site scan --strategy http` using same local fixture | PASS; exit 0; 2 discovered URLs; language `en-US`; 245 ms | Link-following works on the same fixture |
| `web page tree` using an ephemeral localhost HTML page | PASS; exit 0; rendered headings `Adobe Web Browser Test` and `Product Catalog`; 12,176 ms | Adobe Web + Playwright + Chrome rendered and parsed a controlled page |
| Stardust → Impeccable local dependency resolution | PASS; script `impeccable-version-check.mjs --where` found installed Skill directory | Dependency present, **not** a complete redesign or real-site success |

Local readback files: `adobe-web-smoke.json` and `adobe-web-browser-smoke.json` in the isolated lab. All transient browser sessions were closed. No live business account, owned website or real product asset was used.

**Projected always-on context cost, not measured billing or latency:** `claude plugin details` reported ~1,508 tokens (Web), ~3,503 (Stardust), ~439 (Impeccable), total ~5,450 **when all plugins load into a session**. This provides a reason to test lazy loading and scoped sessions; it does **not** prove a runtime orchestration bottleneck.

## Architecture facts already present

- `scripts/vf_skill_catalog.py` already provides **derived** discovery/search/route/compare/plan from source files and the Office v2 Candidate Registry; it does not authorize tool execution.
- `docs/implementation/office-v2/phase2/candidate-registry-v0.json` is the canonical Office v2 admission source, not a fleet installation/availability proof.
- `packages/velvetos/PROJECT-REQUEST-GATE.md` and `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json` route requests and map mandatory authorities; they are **not** a serialized central work queue.
- `packages/velvetos/LAYERS.md` already separates Edge, Kernel and Office/HQ. Existing distributed Claude/host execution can remain parallel without copying policy.
- Therefore **a central-executor bottleneck is not established**. Risks worth measuring are unnecessary always-on context, stale cross-host capability claims, duplicated specialist descriptions, and unnecessary gate traversal for read-only tasks.

### Existing-router bounded discovery checks (synthetic queries)

With the two new registry entries present, `python3.12 scripts/vf_skill_catalog.py route <query>` completed four isolated queries on MacMiniOffice2:

| Query | Measured wall time | Discovery result |
| --- | ---: | --- |
| `scan sitemap and enumerate pages of a website` | 525 ms | Adobe Web site-scan candidate selected |
| `redesign an existing website with stardust` | 534 ms | Adobe Stardust candidate appeared alongside plugin87 redesign challenger |
| `repair 3MF CAD mesh and supports` | 513 ms | CAD skills surfaced; neither Adobe candidate surfaced |
| `publish Instagram customer content` | 512 ms | Content skills surfaced; neither Adobe candidate surfaced |

This is **routing/discovery only**, not a model execution or capability quality score. The Adobe entries are correctly marked `candidate: true`, `run_ready: false` and `requires_admission: true` in routed results. Four local samples are not a latency distribution. They show that the existing derived router can discover scoped candidates without automatically activating them and provide **no evidence yet for a centralized execution bottleneck**.

## Architectural alternatives for the same fixtures

1. **A — current derived router + existing execution:** use existing `vf_skill_catalog`, project authority gates and host-specific tools; keep lab plugins local. Baseline.
2. **B — federated execution, centralized identity/authorization:** retain canonical source/admission and external-effect policy; expose per-host signed/verified capability availability, load **only** the selected specialist(s), run independent workers with isolated inputs/outputs, reconcile exact postconditions. Candidate for a bounded adapter, **not** an additional registry, authority or scheduler.
3. **C — independent local routers with replicated policy copies:** comparison only. This could remove decision latency, but introduces drift, duplicate authority and stale approval risks. Only advance if security and correction/rollback metrics justify replacing current authority mechanisms.

Neither B nor C is approved for production by this note. In particular, **decentralizing task execution does not decentralize permission for payments, Instagram publication, customer messages, printer control, credentials or other effects.**

### Shared benchmark and acceptance plan

Run the same small fixture bundle under A, B and (only in a sealed simulation) C:

- Public/synthetic site extraction and sitemap reconciliation, including HTML language and provenance.
- Mock website UX analysis with a visual-diff report, Hebrew RTL, small viewport and keyboard/a11y checks.
- Agent choice from a mixed task set: site scan, redesign, 3D CAD, office task, customer publish; ensure unrelated skills are **not** loaded.
- Two-host availability/change detection, interrupted worker/resume, host-offline failover and conflicting evidence.
- Negative cases: prompt injection in page content, denied publish attempt, missing rights/cost evidence, stale host registration and failed browser teardown.

For each route capture exact versions/input hashes, selection accuracy, completed outputs, measured median/tail latency, total context tokens, number of unnecessary skill loads, CPU/RAM, retry rate, cost, authority escape count, human handoffs, rollback and maintenance complexity. Compare against **measured** baseline, not a claimed theoretical speedup. Keep golden fixtures and scorecards in the existing Office v2 process.

**Decision gate:** Refactor only if a demonstrated gain in completed work/latency/maintainability outweighs regression or governance risk, and the candidate passes existing admission, isolation, independent QA, and rollback/authority gates. No arbitrary improvement threshold or auto-promotion. The immediate useful improvement is **on-demand invocation inside an isolated environment**, not automatically installing all 27 Adobe specialists on every host.

### Branch-local sensor readback

On the branch's changed file contents in the isolated Core checkout:

- `python3.12 scripts/check-office-v2-phase2.py`: **PASS**; registry 250, lifecycle PASS, shortlist and fixture gates PASS.
- `python3.12 scripts/check-living-studio.py`: **PASS**; registry/projection/skills and 34 catalog regressions.
- `PYTHONPATH=scripts python3.12 packages/velvetos/living-studio/tests/test_skill_catalog.py`: **PASS, 34/34**.
- `python3.12 scripts/check-all.py`: **NOT GREEN / stopped after unrelated host-environment failures**. The lab clone was shallow and lacked historic Git objects required by `check-learning-lifecycle.py`; local Python had no `yaml` module for `check-machine-writers.py`; platform-specific FFmpeg capability tests reported missing zoompan/libass prerequisites. This is **not** a claim that the full repository suite passed or that branch CI is clear. Validate full CI on the GitHub PR before merge.

## Practical use and rollback

- To run the already installed lab, open `~/Velvet/Pilots/AdobeSkillsLab-20261022` on `MacMiniOffice2` and use Claude Code there; `web` and `stardust` plugins are locally enabled.
- The manual Web CLI can be invoked with `node ~/.claude/plugins/cache/adobe-skills/web/1.0.0/cli/dist/web.mjs` and local `node_modules/.bin` on PATH. Do not attach to existing user browser profiles or authenticated sessions without the per-task authority.
- Rollback from the lab directory: `claude plugin uninstall web@adobe-skills --scope local`, `claude plugin uninstall stardust@adobe-skills --scope local`, `claude plugin uninstall impeccable@impeccable --scope local`. Remove the lab's `node_modules` only after evidence is retained; do not bulk-delete the shared Claude cache.
- Adobe for Creativity social editing and InDesign merge remain **separate entitlement/cost checks**, not part of this technical plugin acceptance.

**Next evidence needed:** one owner-selected actual UI/website task for Stardust (no publishing), a comparable incumbent-only run, and routed multi-host execution with readback. No unattended job or further installation is scheduled.
