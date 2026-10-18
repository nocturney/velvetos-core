# Owner browser-automation workflow intake (2026-10-16)

**Status: RESEARCH_ROUTED_NOT_EXECUTED.** Twenty distinct upstream GitHub repositories from the owner's browser tabs, for personal/noncommercial use. The canonical source of truth is [Candidate Registry](candidate-registry-v0.json) plus [P0 shortlists](p0-shortlists-v0.json); [batch receipt](browser-automation-intake-2026-10-16.json) is a source-integrity witness, **not** a new router, authority or scheduler.

Existing owners: [#595 provenance/intake](https://github.com/nocturney/velvetos-core/issues/595), [#612 agents/worker pipeline](https://github.com/nocturney/velvetos-core/issues/612), [#604 fleet/browser/computer-use](https://github.com/nocturney/velvetos-core/issues/604). Active Fleet browser-auth worktrees are NOT modified by this intake.

## Natural workflow insertion points

| Owner task | Proposed first path | Comparison/fallback | Boundary |
| --- | --- | --- | --- |
| Site/service with supported typed API or MCP | Existing official API/MCP | Web UI only for unserved capability | Preserve canonical effect authority |
| Logged-in desktop browser | Pydoll for Edge; Browser Harness for Chrome | Scoped Playwright/CDP | Dedicated browser profile, CDP loopback |
| Dynamic multi-page tasks and test forms | Browser Use | Skyvern; OpenBrowser; Browser Agent | Validate outcome and exact postconditions |
| Repeatable workflows, documents and downloads | Skyvern hybrid Playwright | Browser Use; deterministic Playwright | Idempotency and crash/resume |
| Source-based supplier/product documentation | Crawlee | Moli, Lightpanda, Obscura | Provenance, retry, duplicate/freshness checks |
| Many short-lived browsers or parallel sessions | Browserless local candidate | Selenium Grid; Playwright contexts | #604 controls leases/host availability |
| Independent persistent test profiles | CloakBrowser Manager, Camofox | Native Chromium isolated profiles | No unscoped credential/cookie copying |
| Browser experiments and debugging | Browser Use Web UI | Existing Office UI | No second status authority |
| Optional hosted-browser target | Scrapeless CLI, conditional | Local pool first | Provider-specific cost/terms gate |
| Legacy/plugin compatibility | Puppeteer Extra, Rendertron reference | Modern supported engines first | Do not deploy deprecated software |

## Complete source-to-route map

| Repository | Registry ID | Evaluation route | Owner |
| --- | --- | --- | --- |
| [lexmount/moli](https://github.com/lexmount/moli) | `candidate-lexmount-moli` | Phase route: browser-crawl-extraction | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | `candidate-browser-use-browser-use` | P0 queued: agent-runtime | [#612](https://github.com/nocturney/velvetos-core/issues/612) |
| [browser-use/browser-harness](https://github.com/browser-use/browser-harness) | `candidate-browser-use-browser-harness` | Phase route: browser-attached-session | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [browser-use/web-ui](https://github.com/browser-use/web-ui) | `candidate-browser-use-web-ui` | Phase route: browser-ui-testbed | [#595](https://github.com/nocturney/velvetos-core/issues/595) |
| [browser-use/bux](https://github.com/browser-use/bux) | `candidate-browser-use-bux` | P0 queued: agent-runtime | [#612](https://github.com/nocturney/velvetos-core/issues/612) |
| [guycrespin/browser-agent](https://github.com/guycrespin/browser-agent) | `candidate-guycrespin-browser-agent` | Phase route: browser-attached-session | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [scrapeless-ai/scrapeless-agent-browser](https://github.com/scrapeless-ai/scrapeless-agent-browser) | `candidate-scrapeless-ai-scrapeless-agent-browser` | Phase route: browser-cloud-egress | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [pedro-scrapeless/scrapeless-playwright](https://github.com/pedro-scrapeless/scrapeless-playwright) | `candidate-pedro-scrapeless-scrapeless-playwright` | Source reference: browser-cloud-egress | [#595](https://github.com/nocturney/velvetos-core/issues/595) |
| [lightpanda-io/browser](https://github.com/lightpanda-io/browser) | `candidate-lightpanda-io-browser` | Phase route: browser-crawl-extraction | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser) | `candidate-cloakhq-cloakbrowser` | Phase route: browser-profile-session | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura) | `candidate-h4ckf0r0day-obscura` | Phase route: browser-crawl-extraction | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [apify/crawlee](https://github.com/apify/crawlee) | `candidate-apify-crawlee` | Phase route: web-data-crawl | [#595](https://github.com/nocturney/velvetos-core/issues/595) |
| [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) | `candidate-skyvern-ai-skyvern` | P0 queued: agent-runtime | [#612](https://github.com/nocturney/velvetos-core/issues/612) |
| [FlareSolverr/FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | `candidate-flaresolverr-flaresolverr` | Phase route: browser-protected-targets | [#595](https://github.com/nocturney/velvetos-core/issues/595) |
| [browserless/browserless](https://github.com/browserless/browserless) | `candidate-browserless-browserless` | P0 queued: worker-fleet-placement | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [jo-inc/camofox-browser](https://github.com/jo-inc/camofox-browser) | `candidate-jo-inc-camofox-browser` | Phase route: browser-profile-session | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [ntegrals/openbrowser](https://github.com/ntegrals/openbrowser) | `candidate-ntegrals-openbrowser` | P0 queued: agent-runtime | [#612](https://github.com/nocturney/velvetos-core/issues/612) |
| [berstend/puppeteer-extra](https://github.com/berstend/puppeteer-extra) | `candidate-berstend-puppeteer-extra` | Phase route: browser-compat-legacy | [#595](https://github.com/nocturney/velvetos-core/issues/595) |
| [autoscrape-labs/pydoll](https://github.com/autoscrape-labs/pydoll) | `candidate-autoscrape-labs-pydoll` | Phase route: browser-attached-session | [#604](https://github.com/nocturney/velvetos-core/issues/604) |
| [GoogleChrome/rendertron](https://github.com/GoogleChrome/rendertron) | `candidate-googlechrome-rendertron` | Source reference: browser-compat-legacy | [#595](https://github.com/nocturney/velvetos-core/issues/595) |

## Comparable synthetic fixtures (proposed, not yet run)

1. **BROWSER-01:** Public documentation/catalog extraction, source freshness, retries/deduplication; benchmark CPU/RAM/time with exact fixtures.
2. **BROWSER-02:** Dynamic menu + multi-step synthetic form, visual drift, exact completion readback; compare adaptive agents vs deterministic Playwright.
3. **BROWSER-03:** Disposable Chrome/Edge profiles, list tabs, form fill, file upload/download and reconnect. Reject cross-profile reads.
4. **BROWSER-04:** Interrupted multi-page synthetic invoices; resume, safe cancellation, idempotency and no repeated write.
5. **BROWSER-05:** Browserless vs Selenium Grid vs isolated Playwright context under bounded concurrent load and crash.
6. **BROWSER-06:** Chromium vs Moli/Lightpanda/Obscura on JavaScript, iframe, PDF, screenshot and layout compatibility.
7. **BROWSER-07:** Negative tests: untrusted page instructions, exposed local CDP, secret/log leakage, denied effects, unknown postconditions and paid failover.

## Execution and promotion gates

- Intake counts **20** = five P0 queue positions, thirteen routed phases and two source references; `132 -> 152` registry count. All new records carry `runtime_verification=NOT_RUN`, no authority or credential access. The active 2-3 challenger slots are unchanged.
- **Personal use does not imply unrestricted provider features or cost:** local first, compare measured outcomes; vendor hosted API, latest commercial binaries and model inference still require actual entitlement/zero-incremental-cost checks.
- Admission is under [Phase 2 policy](admission-policy-v0.md). Pin versions and dependencies, inspect upstream terms/security, name synthetic data and host, collect teardown and rollback evidence, then test one bounded candidate at a time.
- Do not disturb #612 P0 coding-worker baseline, #604 browser-session and fleet-auth worktrees, or the OfficeV2-Lab. Confirm free host/lease before any live GUI/WSL experiment.
- Use the existing Office scorecard, Golden Fixture contracts and policies. Candidate availability never becomes production truth, privilege, scheduler, publish/send/payment control or remote desktop entitlement.
- For Velvet Factory, Cloudflare Instagram Publisher remains the canonical scheduling writer, and official Instagram Graph/MCP retains publication verification; Browser Use/Crawlee may assist with research or synthetic testing only.
- Preserve historical 68 imported source rows, four incumbent entries and the protected 82-ID prefix. `scripts/check-office-v2-phase2.py` independently verifies batch source identities, routing, queue membership and false-promotion negatives.

**Next decision:** #595 records admission readiness per source; #604 owns browser execution substrates and personal browser access; #612 owns adaptive/long-running agent comparison. LAB/pilot happens only after host and benchmark acceptance, with no new parallel router.
