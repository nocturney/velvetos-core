# P0 Office 2.0 — local-first, subscription-backed fallback laboratory (2026-10-08)

Canonical implementation/continuation owner: [#612](https://github.com/nocturney/velvetos-core/issues/612). Fleet placement and concurrency remain exclusively [#604](https://github.com/nocturney/velvetos-core/issues/604); Cua stays #602. This is a narrow **LAB decision + comparator** addition, **not** a new task queue, credential authority, runtime scheduler, gateway provider, production model router or autonomous promotion.

## Owner-requested preference

Use local models first where independent postconditions prove they are good enough. Fall back **selectively** to already-owned subscription interfaces if that route has bounded, independently verified value.

- **Code executor ladder:** local Ollama Qwen + OpenCode may fail at tool invocation; treat a 240-second OpenCode no-edit timeout as a **harness-level failure**, not proof the underlying Qwen model cannot code. Try the already-verified **Aider 0.86.2 + Qwen** fixture route before consuming Cursor quota. If Aider's actual code diff fails independent tests/quality, its provider fails in a conclusively retryable state, or a measured task-specific budget expires, offer **Cursor CLI / Composer 2.5** in a separate owned worktree, as a **manual LAB admission**. Do not use Codex CLI (separate scarce quota) or independent paid model API.
- **Research/source ladder:** use local model when known/factual content is independently verified. If fresh external sources, explicit cited provenance, or new repository documentation are missing, offer **Perplexity official macOS Search GUI** via the existing Accessibility bridge, only with Search On and Computer Off. Return a candidate answer and source URLs. The output remains untrusted until URL/document claims are independently corroborated. Perplexity is *not* a code-writing agent nor a drop-in OpenAI-compatible model-gateway endpoint.
- **No automatic provider switch** on policy DENY, unresolved external effects, UNKNOWN executor outcome, unverified quality, unavailable account, exhausted subscription quota, or production actions.
- Existing Cursor subscription and the GUI user session are metered/limited resources. Their effective remaining quota, plan entitlement and any extra charges **were not independently read back**. A successful existing-login test does not mean unlimited or zero-billing. Do not auto-expand spend or switch billing products.
- The Phase 3C vendor-neutral gateway still requires fallback **only on retryable provider failure**. The separate agent-level QA/source-gap admission *is not that gateway retry path*, and is deliberately not integrated into its provider routing logic.

## Independently verified October 8 reference measurements

| Lane | Host / task | Outcome | Elapsed | Proof scope |
|---|---|---|---:|---|
| Local OpenCode + Qwen | Windows 9B + Mac 4B, own disposable coding fixture | BLOCKED / no edit or tool event | ~240s each | Earlier LAB receipts, no verified code |
| Local Aider 0.86.2 + Qwen 3.5:4B | Mac, `slug.py`, base `9727db8e...` | **PASS** | 95.26s | Real edit, 3/3 unit tests and 10 additional edge cases; independent replay/receipt |
| Cursor CLI / Composer 2.5, existing account | Mac, **same exact base** `slug.py` | **PASS** | 20.27s | Real only-file edit; independently replayed patch in fresh Git clone; 3/3 unit + 12/12 independent edge cases and diff check |
| Local Aider 0.86.2 + Qwen 3.5:9B | Windows, *different* `clamp.py` task | **PASS** | 23.74s | Real edit, 4/4 tests and five independent edge cases |
| Perplexity 26.39.0, Search via native Accessibility | Mac, official Git `git worktree --lock` document | **URL + flag VERIFIED** | 18.87s | Returned explicit `https://git-scm.com/docs/git-worktree`; answer SHA-256 read back; official HTTPS page fetched HTTP 200 and contains `--lock` |

The Mac `slug.py` comparison is a **one-run comparison**, not p50/p95, no repeated trials or confidence interval. The Windows `clamp.py` task cannot be used for direct speed comparison with Mac `slug.py`. Cursor stream-json metadata for this run recorded **8,859 input tokens, 815 output tokens, 39,127 cache-read tokens**, but did not establish an invoice amount. Aider Mac previous receipt recorded **930 tokens sent / ~1.9k received**. Differences in provider token accounting, prompt and tool behavior mean these token numbers are not apples-to-apples. Perplexity graphical citation chips `U+FFFC` were not fully exported; only explicit visible text URL and official document presence were independently verified.

Source locations and SHA-256 sealed receipt references are recorded in [local-first fallback evidence](p0-local-first-subscription-fallback-evidence-2026-10-08.json); actual raw local/private account logs are **not** imported into Git.

## Offline decision control and tests

Run:

```sh
python3 scripts/vf_office_v2_local_first_fallback_lab.py selftest
python3 scripts/vf_office_v2_local_first_fallback_lab.py evaluate --request /path/to/reviewed-lab-evaluation.json
```

The script is **pure decision-support**; it never calls a provider, runs an agent or starts a service. It is deliberately separate from `vf_office_v2_p0_worker.py` (pinned fixture executor), `vf_office_v2_continuity.py` (canonical durable state), `vf_office_v2_model_gateway.py` (Phase3C synthetic provider routing) and #604 fleet scheduling.

Expected outcomes include `KEEP_LOCAL`, `LOCAL_AIDER_FIRST`, `CURSOR_CLI_CODING_LAB`, `PERPLEXITY_GUI_RESEARCH_LAB`, `RECONCILE` and `NONE`. Both cloud-backed outcomes are **MANUAL_LAB_ONLY** and `automatic_dispatch_authorized=false`. All decisions preserve single production writer, existing budget policy, and independent output QA.

22 deterministic offline test cases cover local success, verified coding QA failure, verified research source gap, OpenCode harness failure -> Aider first, policy DENY, UNKNOWN no retry, active external effect, concurrent writer, production scope, consent, separate paid API, quota exhausted, prohibited Codex CLI, wrong Cursor model, login failure, absence of independent QA, Computer enabled, source-gap absence, malformed schema, and plan quota available still manual.

## Remaining promotion gates (not passed)

1. Independent repeatable per-task family tests for Cursor and local Qwen/Aider, same machine/base/fixture prompts, at least a small replicated sample before comparing p50/p95 and quality; measure Cursor subscription meter/remaining quota and average consumed tokens. Do not infer no cost from an existing account.
2. Source-rich Perplexity research with a larger answer, several links, live search citations, PDF and long context; reconcile U+FFFC citation chips with actual traceable source URLs and independent verification. Confirm Pro entitlement separately. Do not activate Computer.
3. Test false-positive QA escalation, provider exception, canceled run, UNKNOWN crash, max-attempt cutoff, quota exhaustion, operator minutes, frozen branch/base, no overlap with another writer, and protected GitHub PR/CI feedback.
4. If LAB gates remain green, prepare a **separate** reviewed executor adapter that produces canonical Task Envelope / Worker Receipt and Project State checkpoints. No automatic enrollment, production credential, self-update or merge. Real two-physical-host PR/CI/serial-merge and kill/resume are still pending under #612.

**Decision now:** LAB comparator **validated for one case per route**, offline admission contract **tested**, production/automatic failover **NOT ENABLED**.
