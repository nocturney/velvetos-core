# VelvetOS policy architecture registries

Stage 0 introduces inventories and integrity checks only. These files do not replace the authorities they point to and do not change runtime authorization.

## Ownership

- `policy-registry.json` maps `policy_id` to authority locations, risk class and enforcement points. Policy decisions remain in the referenced authority until a later migration makes a machine-readable policy canonical.
- `sensor-registry.json` inventories runnable `scripts/check-*.py` sensors. Stage 0A intentionally gives legacy sensors a conservative `triggered_by=["**"]` fallback until Stage 0B/2 maps ownership and dependencies precisely.
- `artifact-retention.json` classifies storage/retention families only. `deletion_authorized=false` is mandatory in Stage 0.
- `schema/` defines the machine-readable contracts. `scripts/check-policy-architecture.py` verifies registry integrity and references.

## Policy creation freeze

On pull requests, the same check can run with `--base <sha> --head <sha>`. New normative external-effect text added to noncanonical Markdown must point to an existing registry entry using a literal line such as:

`policy_id: instagram.publish`

Canonical Constitution authorities, `office/control/POLICY.md`, and this registry documentation are exempt from that documentation freeze. The freeze does not infer policy semantics from prose; it only prevents new unregistered authorization language from appearing silently.

## Temporary safety hotfixes

A `temporary_hotfix` registry entry must identify its source authority, migration target, `review_at`, and explicit expiry behavior. `review_at` is a maintenance checkpoint, not automatic policy expiry.

## Current Stage 0 finding

`instagram.publish` is deliberately marked `conflicted` because live sources currently expose both standing tool-publish authorization and legacy/manual approval wording. Stage 0 records the conflict without resolving it. Stage 1 owns that semantic migration.

## Stage 0 baseline reports

The `reports/` directory records the pre-change live baseline at commit `52bcb819c1a6d9924f0f2800340169df5f991e08` and the post-0A coverage point at `9217e172d4f11a01f5db124d7d811c7dcab6b9c5`.

- `baseline-snapshot.json` — pre-change sensor/workflow/authority facts.
- `conflict-report.json` — unresolved semantic/structural conflicts; recording is not resolution.
- `coverage-report.json` and `sensor-coverage-graph.json` — complete runnable-sensor inventory with conservative full-suite fallback.
- `authority-graph.json` — policy IDs to authority/enforcement locations.
- `artifact-inventory.json` — tracked artifact families and sizes; Stage 0 authorizes no move or deletion.
- `ci-baseline.json` — GitHub Actions workflow IDs, fixed cutoff, run IDs/results/durations and branch-protection/ruleset evidence.
- `migration-map.json` — stages 1–9 with explicit rollback paths.

The deterministic Git-derived reports can be checked with:

`python3 scripts/generate-policy-reports.py --check`

`ci-baseline.json` is an external GitHub Actions evidence snapshot. It carries its fixed cutoff and run IDs so individual runs can be re-read from GitHub without replacing the historical baseline with newer data.

## Stage 1 — `instagram.publish` canonical policy

`instagram.publish.json` owns the machine decision for organic Instagram publication. The single evaluator implementation is `instagram-publish-evaluator.mjs`; deterministic test vectors live in `instagram-publish-test-vectors.json`, and `scripts/vf_instagram_publish_policy.mjs` is the CLI bridge.

The Cloudflare publisher imports that evaluator through `src/policy_gate.js`. New jobs require `policy_authorization_v1`; the Worker derives exact content/package/caption/media bindings and standing authorization itself, evaluates before acceptance, then evaluates again after lease + HMAC verification and before `publishJob()`. The second decision receipt is written before any Meta Graph publish mutation. Legacy scheduled-job compatibility is explicit, bounded by job creation time, and only applies to stored jobs without the new policy context.

Production cutover is verified in `reports/stage1-instagram-publish-cutover.json`: Worker version `c4e82e25-2949-47ce-9446-4222012ff81e`, healthy cron/Meta read-back, zero scheduled jobs before and after deploy, and a negative control proving new legacy-form scheduling is rejected before persistence.


## Stage 2A — sensor registry completeness

Stage 2A narrowed registry metadata without reducing CI coverage; Stage 3 now consumes that mapping for affected pull-request CI.

- The live registry contains 116 runnable root sensors.
- All 116 runnable root sensors have explicit ownership/trigger mappings. Any selector uncertainty still fails broad through the Stage 2B fallback rules rather than through unmapped wildcard rows.
- The critical always-on set is deliberately small: `check-agent-surface-security`, `check-critical-syntax`, `check-machine-writers`, and `check-policy-architecture`.
- `check-critical-syntax` is a read-only tracked-Python syntax gate; it parses sources without importing or executing them.
- `reports/stage2-sensor-registry-audit.json` is generated by `scripts/generate-sensor-registry-audit.py` and records mapping coverage, nested sensor execution, and direct workflow duplicates.
- The refreshed audit records two nested sensor-invocation relationships and zero potential duplicate workflow runs after the Stage 3 duplicate-removal cutover.
- During Stage 2B, affected sensors were computed in shadow mode only. Unknown or unmapped changes expanded to the full suite, never narrowed by guess.

## Stage 2B — affected selector in shadow

The affected selector is intentionally non-authoritative in Stage 2B. `scripts/check-all.py` remains the merge authority.

- Stage 2 pinned `sensor-selection.json` to `mode=shadow` with fail-broad behavior and fixed exit criteria before observation began; Stage 3 now sets `mode=enforced` while preserving those fail-broad/rollback invariants.
- Unknown paths, sensor-registry/schema changes, evaluator-core changes, CI harness changes, and selector changes expand to `FULL_SUITE`.
- `triggered_by` is reserved for domain/contract surfaces; `depends_on` records technical implementation dependencies. The selector matches both without conflating their meaning.
- Current registry evidence contains 48 technical dependency edges across 27 sensors.
- A current `packages/vfcopy/VOICE.md` replay selects 14/116 sensors. The pinned Stage 2B opening baseline records the historical 14/95 post-refinement result versus 67/95 before refinement.
- During Stage 2, pull requests recorded the shadow selection/comparison in the GitHub job summary and emitted machine-readable markers; the authoritative full suite was compared against the would-select set to detect misses. Stage 3 removes that comparison and executes the selected suite directly on pull requests.
- Opening evidence is pinned in `reports/stage2-shadow-observation-baseline.json`: PR #398, its shadow/full comparison, the successful post-merge main run, and deterministic replay samples. It is a fixed baseline, not a live counter.
- `scripts/collect-sensor-shadow-observations.py` is the read-only live counter: it queries GitHub Actions through authenticated `gh`, counts each pull request once for volume while retaining every eligible run as historical evidence, extracts the machine-readable selector/comparison markers, and evaluates the fixed exit criteria. A later clean rerun cannot erase an earlier miss. Reviewed miss classifications are pinned in `reports/stage2-shadow-miss-classifications.json`. It never changes GitHub state or CI enforcement.
- Incomplete historical runs remain blocking unless they have an explicit reviewed recovery in `reports/stage2-shadow-incomplete-recoveries.json`. A recovery is fail-closed: the collector must match run/PR/head SHA, prove the original log executed the complete full suite with the recorded failures, and verify a later complete run from the same PR selected the full suite and emitted `NO_MISS`. The original run remains in history and is reported as recovered rather than erased.
- Exit criteria are fixed at at least 20 observed pull requests and 7 observation days, zero critical misses, classification of every noncritical miss, mapping repair for every relevant miss, deterministic replay, and a tested `FULL_SUITE_REQUIRED` rollback.
- Stage 2B does not change branch protection, remove duplicate checks, or activate affected-only enforcement.

## Stage 3 — affected CI active

Stage 3 is active in the repository. Pull requests use the deterministic affected-sensor selection, pushes to `main` keep the full suite, critical always-on sensors remain mandatory, and unknown or broad changes still expand to `FULL_SUITE`.

- The activation receipt is `reports/stage3-activation-receipt.json`, prepared against `main` `09f73c909e6583844d9ca80c192462369b13decf` from 69 pull requests / 129 runs with zero critical misses, zero unclassified misses, complete run history, and deterministic replay PASS.
- The fixed 7-day Stage 2 threshold remains documented. The owner explicitly authorized a **duration-only** exception at 5.8467 observed days because the accumulated evidence was judged sufficient. The exception is fail-closed: it applies only when `MINIMUM_OBSERVATION_DAYS_NOT_MET` is the sole blocker and every other exit invariant passes.
- `scripts/check-all.py --selection sensor-selection.json` is the pull-request runner; plain `scripts/check-all.py` remains the full-suite runner for `main` pushes and rollback.
- Repository ruleset `23284099` is live on the default branch with deletion + non-fast-forward protection and required `check-all`; `bypass_actors` is empty.
- `workflow_dispatch` on the Core Sensors workflow is reserved as the exact-SHA precheck surface for protected machine writers. It resolves live `origin/main` as base, evaluates the staging SHA with the same affected selector, and only after success publishes a legacy commit-status context `check-all` on that exact SHA. This status bridge exists because GitHub rulesets do not accept the non-main `workflow_dispatch` check-run itself as the required status for a direct default-branch push.
- Default-branch machine writers must call `scripts/push-main-with-check-all.sh`: rebase onto current `main`, push a temporary `machine-check/*` ref, dispatch/wait for successful `check-all` on the exact SHA, verify both the GitHub Actions check-run and the `check-all` commit status, then push that same SHA to `main`. After a successful machine push, the helper explicitly dispatches Core Sensors on live `main` with `execution=main_full` and requires proof of full-suite execution, because pushes authenticated by `GITHUB_TOKEN` do not reliably emit a new push-triggered workflow. A concurrent `main` advance invalidates the pre-push evidence and causes a bounded rebase/recheck retry; no force push or ruleset bypass is used. The publish-bridge writer remains isolated on its literal `publish-bridge` branch.
- `scripts/check-machine-writers.py` enforces this path plus explicit `contents: write` / `actions: write` permissions for default-branch writers.
- `.github/workflows/check-all.yml` no longer performs the Stage 2 shadow comparison or the two duplicate direct invocations (`check-policy-architecture.py`, `check-commission-isolation.py`). Those checks remain sensors and are selected through the registry when relevant.
- `sensor-selection.json.stage3_preparation` is `ACTIVE`, preserves the `FULL_SUITE_REQUIRED` rollback, and records the owner duration exception as auditable activation metadata.
- `scripts/check-policy-architecture.py` validates the active workflow shape and activation receipt; the duration exception cannot mask critical misses, incomplete/unresolved evidence, unclassified relevant misses, incomplete history, or deterministic replay failure.
- `reports/stage3-preactivation-plan.json` remains the historical preactivation transaction/snapshot; the activation receipt is the cutover evidence.

## Stage 4A — friction baseline pinned

Stage 4A is observation-only. It does not change request routing, authorization, tool execution or owner approvals; it freezes the pre-4B friction surface so later simplification is measurable rather than anecdotal.

- `reports/stage4a-friction-baseline.json` and its Markdown companion are pinned against pre-change `main` `9989f0ffd11b97a28da732c9fa6ddd234ba51d35` and inventory the 14 routine flows named by the Reform v2 Stage 4A plan.
- Baseline result: 8/14 flows fall to `general_business`; Instagram carousel is under-classified; 3 creative-prep flows block before execution without exact evidence; Gmail transport is currently ready; Maya is `READY_ACCEPTED_SURFACE`.
- Every sampled request pays the nine-source global baseline first. The measured burden is 10–22 authority files and 3–11 hard gates per flow (mean 13.29 sources / 5.14 gates). CAD read-only and CAD build receive the same six production gates.
- The report records the required gate dispositions `KEEP`, `INTERNALIZE`, `MERGE`, `ACTION_SCOPED`, and `REMOVE_AS_DUPLICATE` before any behavior changes; the explicit duplicate is `general_business.baseline_authority`, because the global baseline has already been resolved.
- `check-project-request-gate.py` protects the historical snapshot shape/metrics; it does not regenerate the baseline after later fast-path changes.
- Stage 4B target: known read-only / routine LOW-risk / already-authorized requests route with a minimal baseline and internal receipt; full preflight remains for unknown/high-risk/external-sensitive cases.

## Stage 4B — Project Request Fast Path active

Stage 4B keeps `project.request.preflight` as the single mandatory router but makes the amount of preflight scope-aware. The fast path is not a bypass and does not create a second authority engine.

- `FAST_PATH` is limited to known `operations`, `production` and `research` routes with scope `read_only`, `local_routine` or `internal_mutation`, and only when no full-preflight trigger is present.
- The fast path loads three universal authority files plus one domain profile instead of the nine-source global baseline plus every domain authority. It still validates every selected path and still requires domain/action postflight before a completion claim.
- `FULL` remains mandatory for external mutation, unknown domain, creative/publication, commercial/spend, rights/privacy, destructive/permission, physical-print and authority-conflict cases. `stale_critical_evidence` and `new_route` remain reserved full-preflight triggers for runtime/router callers.
- Natural-language routing now recognizes Instagram carousel as creative, Gmail/email/owner brief/Google Drive/internal status as operations, and Maya/Blender/3ds Max/ZBrush/DCC/3D-modeling as production.
- Project receipts now include `request_scope`, `preflight_mode`, `full_preflight_triggers` and `owner_surface`. The owner surface is `internal_unless_true_blocker`: a routine PASS, repair, retry, compatibility check or internal evidence blocker is not itself an owner prompt.
- `required_tools` / `required_skills` now expose canonical routes for Gmail, Google Drive, Office/owner brief, Research Seat/WebSearch, Creative Craft Maya/DCC and the Fabrication Router instead of leaving known routes blank.
- CAD read-only and CAD build are now scope-distinct: read-only keeps only routing/specialist gates; artifact build additionally keeps `verified_specs`; neither pays printer-control, price or print-authority gates until an actual physical-print/commercial action exists.
- `reports/stage4b-project-request-fast-path.json` replays the same 14 Stage 4A flows: 14/14 domain-aligned, 0 generic fallbacks, 7 `FAST_PATH` / 7 `FULL`, 10/14 with explicit tool routes, and all 14 with internal-by-default owner surface. The seven fast-path flows reduce mean authority sources from 11.429 to 5.429 (52.5%) and mean hard gates from 3.857 to 2.286 (40.7%).
- Seven negative controls prove price/spend, destructive/permission, privacy, physical print and unknown requests remain `FULL`; the four creative flows remain `FULL` and fail closed without exact creative evidence.

## Stage 4C — One Authority Gate

Stage 4C makes authorization ownership explicit without adding a policy service or second runtime. `project.request.preflight` remains a router; external-effect authorization belongs to one mapped effect-authority `policy_id`.

- `policy-registry.json.external_effect_contract` maps seven external effects one-to-one to `cost.recurring.new`, `instagram.publish`, `gmail.send`, `customer.whatsapp.send`, `advertising.boost`, `external.irreversible.delete`, and the new `external.permission.mutate` boundary.
- The normalized decision vocabulary is `ALLOW | DENY | REQUIRE_OWNER_APPROVAL`. Registry validation rejects duplicate effect classes, duplicate effect-authority policy IDs, missing authority paths, unknown evidence classes, or an effect policy that is not marked `effect_authority`.
- Brand, Product Truth, Visible Text, transport, QA, runtime health, rights/privacy, facts, target identity and cost/provider/billing checks are declared evidence inputs. Every evidence class is explicitly `can_authorize_external_effect=false`; `visible_text.finalization` and `public.cta` are enforced as `evidence_input` roles.
- Exact-action receipt modes are scoped rather than universal: cost/paid/delete/permission use `EXACT_ACTION_REQUIRED`; Gmail uses `EXACT_ACTION_ON_COMMITMENT`; WhatsApp remains `OWNER_RESERVED`; Instagram keeps its existing `POLICY_NATIVE_RECEIPT` and evaluator.
- `schema/action-receipt.schema.json` plus `scripts/vf_action_receipt.py` validate the binding of an already-made canonical policy decision to the exact action. The validator is not a decision engine and cannot turn evidence into authorization.
- `action-receipt-test-vectors.json` covers valid exact owner authorization plus unregistered policy, effect mismatch, missing binding, missing/expired owner approval, DENY, unresolved owner-approval decision, failing evidence and the Instagram native-receipt boundary.
- `scripts/check-policy-architecture.py` executes those vectors and enforces the single-authority/evidence-role contract on every CI run where policy architecture is selected; `check-risk-policy.py` protects the destructive-delete and permission-mutation owner boundaries.

## Stage 4D — Routine Instagram Happy Path

Stage 4D collapses routine publication readiness into one exact-bound `CONTENT_READY` evidence envelope while keeping `policy_id: instagram.publish` as the sole publication authority. Repository acceptance and the production cutover are both complete and pinned to live evidence.

- `schema/content-ready.schema.json` + `scripts/vf_content_ready.py` aggregate exact artifact identity, Product Truth, brand, copy, visual QA, rights/privacy and render/transport evidence. They explicitly claim no authorization capability.
- Routine LOW-risk quality failures route to `TARGETED_REPAIR`; retryable transport failures route to `RETRY_INTERNAL`; neither becomes an owner prompt. Rights/privacy ambiguity remains a `HARD_BLOCKER` and is owner-visible.
- `instagram.publish` machine policy is version 2 and consumes exactly one `content_ready` gate. Exact content/package/caption/media bindings must match; unresolved repair/retry/blocker state is DENY.
- With runtime standing authorization enabled, LOW risk + exact `CONTENT_READY=PASS` produces one `ALLOW` decision with `STANDING_AUTHORIZATION` and no per-asset owner approval. Medium/high or missing standing authorization keeps the existing owner path.
- `packages/vfigos/routine_publish.py` is the canonical routine scheduler client: it validates local evidence refs/digests, exact caption/media bytes, uploads SHA-bound media, creates the Cloudflare job, requires the Worker’s standing-authorized `ALLOW`, then reads the persisted job back. It never mints `velvet.delivery_approval.v1`.
- The Cloudflare publisher now has tested format contracts for image/post, carousel, Reel and Story. MIME is verified from stored media bytes/metadata before creation and again before publish; Reel requires MP4, carousel requires images, Story accepts one image or MP4.
- Direct/immediate MCP publication remains unchanged behind signed `velvet.delivery_approval.v1`. Stage 4D standing authorization applies to the canonical scheduled publisher, not to direct mutation tools.
- Previous seven-gate `policy_context` is a bounded compatibility path only for jobs created before `2026-10-03T15:58:09.874Z`; new routine jobs require `CONTENT_READY` after that cutoff. Older original scheduled-job authorization remains separately bounded by its pre-Stage-1 cutoff.
- The publication closure is unchanged: decision receipt precedes mutation; `published_verified` still requires a Meta provider media id plus live read-back/permalink. Failures at/after `media_publish` remain `reconcile_required` and are never blind-retried.
- `reports/stage4d-instagram-happy-path-cutover.json` is the immutable live cutover receipt. It records deployed `main` `fdc4a3cc1d46b43870e6c69ddcf36fc378a406e7`, Worker version `2390ee0e-6019-44c5-9832-e3d08689f440`, policy v2 / `CONTENT_READY` health, fresh cron/runtime state, Meta readback for `velvets_cloud`, GitHub live-read smoke run `37136222049`, five historical `published_verified` jobs, zero scheduled/retry jobs, and a non-persistent negative control returning `403 / DENY / CONTENT_READY_REQUIRED`. The implementation report embeds that receipt reproducibly and now reports production cutover `PASS`.

## Stage 4E - Gmail / External Send Simplification

Stage 4E keeps `policy_id: gmail.send` as the single Gmail external-effect authority while removing owner ceremony from ordinary communication. `constitution/SEND.md` remains canonical law; `packages/velvetos/policy/gmail.send.json` + `scripts/vf_gmail_send_policy.py` are its machine/runtime evaluator.

- `owner_brief`, `known_thread_reply` and `routine_forward` are routine scopes. Facts, exact reader-appropriate text readiness, verified target and transport are still mandatory, but no extra owner approval or exact-action receipt is required when no restricted trigger exists.
- `approved_static_copy` may reuse a previous text receipt when the exact `body_sha256` is unchanged and the facts remain current. That reuse explicitly avoids re-running the full rewrite/Humanizer pipeline merely because a routine send is happening again.
- `new_outbound`, new commercial commitment, price/spend and rights/privacy ambiguity return `REQUIRE_OWNER_APPROVAL`. An approved commitment must be bound to the exact body and re-evaluated to `ALLOW`; `velvetos.action-receipt.v1` remains `EXACT_ACTION_ON_COMMITMENT`.
- Unverified facts, blast behavior, unverified target, unavailable transport, body/text digest mismatch, or changed/stale static copy are `DENY`. Owner approval cannot make a blast valid.
- `scripts/vf_send_preflight.py --gate gmail` is transport diagnostics only and now prints `transport-ready authorization=policy_id:gmail.send-required`; it cannot authorize body/recipient/commitment/price/spend.
- `gmail-send-test-vectors.json` covers 19 cases: 5 ALLOW, 5 REQUIRE_OWNER_APPROVAL and 9 DENY. The four routine/static happy-path cases all prove `owner_prompt_count=0`; generic action-receipt vectors separately prove routine reply needs no exact binding while approved commitment does.
- `reports/stage4e-gmail-send-simplification.json` pins repository acceptance against pre-change `main` `6d7b48e5c5604673d63363927c3d0c69145282e9`; `check-gmail-brief-send.py` enforces the policy, vector distribution, static-copy reuse and transport/authorization separation without sending mail.

## Stage 4F — Runtime Receipt Scope

Stage 4F separates code validity from deployment/runtime truth. A runtime receipt is evidence for the component a live claim actually depends on; its age no longer gains blocking authority merely because CI was triggered by `push`, `schedule` or `workflow_dispatch`.

- `packages/vfharness/runtime/proof-scope.json` defines the three proof outcomes: ordinary `code` → `CODE_VALID`; `deployment` → `DEPLOYMENT_VALID`; `runtime`, `external_action` and `acceptance` → `RUNTIME_HEALTHY`.
- `scripts/check-runtime-doctor.py` defaults to `CODE_VALID`, validates the runtime contract/repository proof, and does not consume current provider/connector/host receipts. Live scopes require explicit `--require-component <id>` dependencies; a live scope with no dependency list fails closed instead of silently checking every runtime.
- For a named live dependency, stale, missing, malformed, component-mismatched, future-dated, evidence-less, non-healthy or unknown-component evidence remains a blocker. `anyOf` groups continue to pass with one fresh healthy member.
- `VF_RUNTIME_PROOF_SCOPE` + `VF_RUNTIME_REQUIRED_COMPONENTS` provide the same dependency-scoped contract to nested sensors/actions. `VF_RUNTIME_RECEIPTS_STRICT=1`, `VF_RUNTIME_STRICT=1` and `check-runtime-doctor.py --strict` remain migration-compatible repository-wide all-component proof, not normal CI behavior.
- `check-grok-provider-readback.py` now validates the retired Grok state confirmation and historical readback contract only. `grok-production-scheduler` is no longer a current runtime dependency; historical zero-cost/Stage 7 receipts remain immutable replay evidence while current full-suite execution defaults to `CODE_VALID`.
- Runtime receipt file changes now directly select `check-runtime-doctor`, not the historical zero-cost acceptance sensor. Other relevant package sensors may still run through their own mappings, but receipt freshness itself no longer broadens into historical acceptance.
- The `runtime_health` evidence class in the One Authority Gate registry is explicitly `dependency_scoped=true`, requires `RUNTIME_HEALTHY` when the dependency is real, and states that GitHub event type is not a dependency signal.
- `Runtime Receipts Refresh` is one ChatGPT automation at 19:15. It refreshes only real dependency-scoped evidence; there is no required Grok scheduler receipt and freshness is not a universal code/merge gate.
- `reports/stage4f-runtime-receipt-scope.json` pins repository acceptance against pre-change `main` `8081bfe62fe6c59e0e22798dda1d2469e5ee3742`. Fixture tests prove GitHub-event neutrality, unrelated stale evidence not blocking `CODE_VALID`, component-scoped live proof, fail-closed required evidence, anyOf fallback, unknown dependency rejection and legacy all-component strict compatibility.

## Stage 4G — Bounded Cost Envelopes

Stage 4G keeps `policy_id: cost.recurring.new` and `NO_NEW_RECURRING_COST` as the single cost authority while allowing one explicit owner approval to cover a tightly bounded sequence of paid-capable calls. The implementation ships **no active envelope and authorizes no spend**.

- `packages/velvetos/policy/schema/cost-envelope.schema.json` binds provider, exact product/plan, billing model, usage model, component/environment/action scope, aggregate ILS cap/period, hard-cap state, overage behavior, source-preflight SHA-256, owner approval reference and expiry.
- `scripts/vf_cost_preflight.py` remains the single runtime decision entrypoint. `scripts/vf_cost_envelope.py` is a helper only; there is no second cost policy engine.
- A matching call inside a valid envelope requires a fresh usage meter and proves `spent_before + projected_incremental_cost <= cap`. It does **not** repeat full cost preflight or owner approval, but it still requires an exact-action receipt before the paid external effect.
- Provider/plan/billing/usage/scope/cap/automatic-overage/overage-behavior drift or expiry returns `REQUIRE_OWNER_APPROVAL`; stale/missing meter evidence, broken hard cap, cap breach, source-preflight mismatch or `COST_UNKNOWN` fail closed.
- `cost-envelope-test-vectors.json` covers 22 cases: 2 ALLOW, 10 REQUIRE_OWNER_APPROVAL/revalidation and 10 DENY. The matching cases prove `owner_prompt_count=0`, `full_preflight_per_call=false` and `exact_action_receipt_required=true`.
- Generic `velvetos.action-receipt.v1` vectors prove an envelope-authorized cost call may skip a repeated owner gate while still requiring exact action binding.
- `reports/stage4g-cost-envelopes.json` is reproducible and pins repository acceptance against pre-change `main` `f0df1c7ea28aad1cbaa9d4752bb84bc6035735d5`; it records `active_envelope_count=0`, `external_paid_calls_performed=0` and `spend_authorized_by_stage4g_implementation=false`.

## Stage 4 Gate — Routine Operations & Policy Simplification CLOSED

`reports/stage4-acceptance.json` closes Reform v2 Stage 4 against merged `main` `5a5ebcb655856e758aed2b80ffcb0b683d1b18b3` and GitHub full-suite run `37142530441` / job `111259753445` (`SENSORS 116 mode=full` → `OK suite passed=116`). The receipt is observation-only, hashes every Stage 4 source receipt plus `policy-registry.json`, and `check-policy-architecture.py` regenerates it byte-for-byte in CI.

The gate is `PASS` on all eight integrated criteria:

- Project Request routing: 14/14 known flows aligned, 0 generic fallbacks, routine LOW-risk owner prompts 0, sensitive/unknown paths still FULL.
- One Authority Gate: each of the seven external effect classes has exactly one canonical effect-authority policy; Visible Text / CTA remain evidence-only and Project Request remains router-only.
- Routine Instagram: 0 owner prompts, exactly one `instagram.publish` decision per publish attempt, live Worker cutover PASS, provider receipt + live readback retained.
- Routine Gmail: owner brief / known-thread reply / routine forward stay at 0 owner prompts; commitment/price/spend/rights ambiguity remain owner-gated and provider receipt remains required.
- Runtime receipts: unrelated stale runtime evidence does not block code-only work; a real declared live dependency still fails closed on stale/missing/malformed/non-healthy proof.
- Cost envelopes: Stage 4G ships with 0 active envelopes and no spend authorization; matching owner-approved bounded calls reuse approval without repeated full preflight while retaining fresh meter, hard cap and exact-action receipt.
- Critical guardrails remain represented by canonical effect authorities for cost, Instagram, Gmail, customer WhatsApp, advertising/boost, irreversible delete and permission mutation.
- The post-4G main full sensor suite passed 116/116.

Stage 5 entry is therefore allowed. Constraint: do not build a second Agent Harness; reduce default context and capability loading to the smallest sufficient local authority while preserving deterministic routing and the Stage 4 safety boundaries.

## Stage 5A — Context and Instruction Locality

Stage 5A activates locality without adding a second Agent Harness, capability router or policy engine. The existing Project Request manifest remains the router; package-local `AGENTS.md` files are instruction surfaces only.

- The historical pre-change snapshot is `reports/stage5a-context-locality-baseline.json`, pinned to `main` `47f518e9b22bccd4b9fa43cc41336ce28ab701b2`: root `AGENTS.md` was 180 lines / 3,521 words with 41 VF/domain leakage markers, zero package-local guides and 25 check-script couplings.
- Root `AGENTS.md` is now Core-only: 56 lines / 453 words in the Stage 5A acceptance snapshot, an 87.1% word reduction. The 15 tracked VF/domain markers are all zero.
- Eighteen package-local `AGENTS.md` guides now sit beside their owning capability/domain. They point to existing canonical law/SoT and cannot authorize external effects.
- `PROJECT-AUTHORITY-MANIFEST.json#instructionLocality` maps all 10 routed domains to exactly one primary local guide. Runtime receipts expose `local_instructions`; known tasks load root plus the selected domain guide(s), while unknown domains load root only and remain `FULL`/blocked.
- Warehouse loading defaults to `off`; Core/system-engineering negative control loads only `AGENTS.md` + `packages/velvetos/AGENTS.md`, with no Creative Craft, VF creative or fabrication guide preloaded.
- Domain sensors were migrated from root-content assertions to their local guide / canonical registry. The policy registry SHA remains exactly equal to the Stage 4 acceptance hash, proving Stage 5A changed context loading rather than authorization semantics.
- `reports/stage5a-context-locality.json` is reproducible byte-for-byte from the pinned snapshot. `check-project-request-gate.py` protects the historical Stage 5A result and continuing root/locality budgets separately so later Stage 5 work may improve locality without rewriting the baseline.

## Stage 5B ? Harness consolidation

Stage 5B keeps the existing `vfharness` and removes duplicate global loop semantics rather than adding an orchestrator. `packages/vfharness/LOOP.md` is the sole global execution-loop contract. Five active secondary surfaces are pointer-only; specialized playbooks and historical state remain intact.

- `packages/vfharness/layers.json#executionContract` pins the canonical loop, SKILLSTATE surface, existing cross-tool handoff artifacts and `secondOrchestrator=FORBIDDEN`.
- `reports/stage5b-harness-consolidation.json` records duplicate active loop restatements **1 ? 0** and pointer coverage **3/5 ? 5/5**.
- Cross-tool continuation remains `office/control/HANDOFF.json` + `packages/vfmem/HANDOFF.md`; neither is authorization.
- The external-effect policy registry remains hash-identical to Stage 5A, so harness consolidation changes no authorization semantics.
- `check-vfharness.py` enforces the machine contract and regenerates the Stage 5B report byte-for-byte.

## Stage 5C — Workspace Distribution / Capability Routing

Stage 5C closes workspace distribution after Stage 5A locality and Stage 5B harness consolidation. It does not add a second router, increase the desired skill count, or create authorization semantics.

- Workspace distribution is pinned to `nocturney/velvetos-workspace-distribution` PR #3: head `de214771e3c64063f201359c58f918653a0bed05`, merge `4fa715dc78275b87a942658b26b74608932d8d50`, plugin version `1.6.0`.
- The desired Workspace skill set remains 35. `creative-craft` remains the ambient natural-language router; the eight professional Creative Craft specialists are available workspace-wide but **ROUTED_ONLY**.
- Routed specialists: `vf-cad-design-craft`, `vf-dcc-modeling-craft`, `vf-material-lookdev`, `vf-product-visualization-craft`, `vf-post-production-craft`, `vf-vfx-compositing-craft`, `vf-image-design-craft`, `vf-technical-illustration-craft`.
- The distribution desired state explicitly sets `warehousePreload=false`, selection to `intent -> creative-craft/router -> minimum matching specialist(s)`, and `authorizationEffect=NONE`.
- The workspace verifier enforces the exact routed-only specialist set, standards-compliant Skill frontmatter (`name` + `description` only), Creative Craft ambient-router continuity and Workspace Stack version `1.6.0`.
- Creative Craft candidate structural evals pass 56/56. Core specialist entrypoints carry the same routed-only trigger contract; `check-project-request-gate.py` regenerates the Stage 5C receipt byte-for-byte and blocks drift.
- `reports/stage5c-workspace-distribution.json` pins the external distribution Git identities/blobs and proves the Stage 5B external-effect authority registry is unchanged at Stage 5C entry.

## Stage 5 Gate — Context, Harness and Workspace Locality CLOSED

`reports/stage5-acceptance.json` closes Reform v2 Stage 5 against merged `main` `67bd5dc1bedfb98b850e4b5b09090dcd51598e48` and post-merge full-suite run `37175062910` / job `111355869001` (116/116 PASS). The receipt is observation-only, hashes the Stage 5A/5B/5C source receipts, and is regenerated byte-for-byte by `check-policy-architecture.py`.

The gate passes all seven integrated criteria:

- Core/system context is business-clean: root remains 56 lines / 453 words with zero tracked domain leakage, and system-engineering loads only root + Core instructions.
- Known routine requests load the minimum routed instruction set: root + one primary guide per selected domain; unknown domains remain root-only FULL/blocked.
- `packages/vfharness/LOOP.md` is the single global execution-loop authority; active secondary surfaces are pointer-only and no second orchestrator exists.
- Workspace Stack `1.6.0` keeps 35 desired Skills; `creative-craft` remains the ambient router while eight professional specialists are `ROUTED_ONLY` and never ambient-preloaded.
- Workspace availability and specialist selection have `authorizationEffect=NONE`; neither local guides nor harness/workspace state can replace a destination effect-authority policy.
- Context-warehouse regression is blocked across Core + Workspace distribution.
- The post-5C main full sensor suite passed 116/116.

Stage 6 entry is allowed. Stage 6 may reduce Visible Text / creative / DCC ceremony by surface and risk, but must preserve truth, rights/privacy, commercial commitment, public-publish, spend, destructive-action and exact-binding safeguards.

## Stage 6A — Visible Text risk tiers

Stage 6A replaces the former universal six-stage Visible Text ceremony with a fail-closed risk/surface tier model while preserving the same truth and external-effect authority boundaries. Acceptance evidence is `reports/stage6a-visible-text-tiers.json`, prepared against Stage 5 gate merge `c1959a6c663d8d363545b5bc9ed8f30a1758941a` and regenerated byte-for-byte by `check-visible-text-gate.py`.

- `DRAFT_INTERNAL`: truth/basic-safety evidence only; anti-slop/style findings are diagnostic and cannot hide a fact failure. Required evidence falls 6 → 1 (83.3% ceremony reduction).
- Routine `FINAL_INTERNAL`: truth + clarity/surface QA; reader-first/copy/Humanizer become mandatory only for sensitive or >800-character internal text. Routine evidence falls 6 → 2 (66.7% reduction).
- `EXTERNAL_COMMITMENT`: verified facts + reader-first + surface QA + exact body/hash binding. It does not load irrelevant writing aids merely to satisfy ceremony.
- `PUBLIC_PUBLISH`: retains the complete six-stage public chain plus existing marketing/`NO_TEXT`/publication evidence. Public ceremony reduction is 0.0%.
- Public/external surfaces cannot downgrade into an internal tier. Exact `approved_static_copy` reuse requires an unchanged SHA-256 and fresh fact validation; a changed hash fails closed.
- Nine deterministic behavior vectors pass. The two owner-brief Gmail workflows declare `FINAL_INTERNAL` explicitly. The external-effect policy registry hash is unchanged and Visible Text remains evidence/quality gating, not effect authority.

## Stage 6B — Creative Readiness and Authority Boundary

Stage 6B simplifies creative readiness without weakening Product Truth, rights/privacy or publish authority. Acceptance evidence is `reports/stage6b-creative-readiness.json`, prepared against Stage 6A merge `36a873248f02c24201ebfdf386636f2a96a3db43` and regenerated byte-for-byte by `check-creative-system.py`.

- The Creative Manifest is explicitly a per-job **coordination/evidence artifact**, not an approval database, policy authority, media catalog or Product Truth source. Writing `PASS`, `ready_for_publish` or `authorized_for_tool_publish` into it cannot mint that state.
- Product Truth remains higher authority than aesthetic references, Creative Craft, visual standards or quality scores.
- Creative Craft 2.0 is machine-declared as an authoring/quality system, not a policy hierarchy. It may produce, critique, diagnose and targeted-refine; it may not authorize publish/send/spend/rights/destructive effects or override Product Truth.
- `Produce → Critique → Targeted Refine` stays internal. Ordinary hook/cover/layout/grade/reference/provider/repair choices and routine quality repair do not ping the owner.
- The owner-approved grid remains a standing visual standard, not a per-job approval request.
- Owner escalation remains exactly exception-only for physical gaps, unclear rights/privacy, price/spend/ads, customer WhatsApp, Print from HQ, destructive action or a hard blocker after failover.
- The external-effect policy registry SHA is unchanged.

## Stage 6 Gate — Visible Text, Creative Readiness, DCC and Documentation CLOSED

`reports/stage6-acceptance.json` closes Reform v2 Stage 6 against merged `main` `efaaf2f127a17917dcc4a6506fb26548a8bde701` and post-merge full-suite run `37188157580` / job `111394483160` (116/116 PASS). The receipt is observation-only, SHA-binds Stage 6A/6B/6C/6D evidence, and is regenerated byte-for-byte by `check-policy-architecture.py`.

The integrated gate passes all nine criteria:

- Internal draft/status text uses proportional risk tiers: `DRAFT_INTERNAL` needs truth/basic safety instead of the full public-copy chain, while fact failures remain blocking.
- Public/customer text remains evidence-bound: commitments require exact body binding, `PUBLIC_PUBLISH` keeps the full chain, and downgrade to an internal tier fails closed.
- Creative Manifest remains coordination/evidence only; Creative Craft remains an authoring/quality system. Neither creates policy authority or overrides Product Truth.
- Produce → Critique → Targeted Refine and ordinary aesthetic/repair choices remain internal; owner escalation stays exception-only.
- DCC updates use `latest-compatible` + typed capability proof. Illustrator 30.8.2 and After Effects 26.5 both demonstrate newer-than-recovery-baseline `available` status after typed PASS.
- Recovery baselines remain recovery/drift evidence, not allowlists. Exact version equality is unnecessary; fail-closed behavior remains, arbitrary script escape is not wired, and auto-update/rollback/uninstall remain disabled.
- Stage 6D reports zero active authority-path violations across the checked documentation set.
- External-effect authorization semantics remain unchanged across Stage 6A/6B/6C.
- The post-6D main full sensor suite passed 116/116.

Stage 7 entry is allowed. Stage 7 may consolidate state/evidence/runtime/memory/research/scheduler/retention roles, but must not create a new database merely to rename existing state or weaken canonical effect-authority boundaries.

## Reform v2 Stage 7A — State / Evidence model

`state-evidence-model.json` is the canonical semantic map for operational artifacts. It does **not** create a database or move data. Every mapped surface is assigned one of exactly four roles:

- `CANONICAL_STATE` — current state for one bounded domain only.
- `EVIDENCE_RECEIPT` — proof/observation; never external-effect authority.
- `AUTHORIZATION_DECISION` — exact-action policy decision; currently bound only to `velvetos.action-receipt.v1`.
- `AUDIT_HISTORY` — append-only/superseded/generated history; cannot overwrite current state.

All nine artifact classes already present in `artifact-retention.json` have one semantic default. Compatibility caches, mirrors, projections and human-readable views are explicitly non-authoritative.

`office/control/HANDOFF.json` remains canonical only for the narrow handoff/continuation domain; it does not become authority over the jobs/media/policy sources it references. Task checkpoints remain current state by unique `task_id`; embedded artifact digests are evidence, and superseded checkpoints are history.

Work Ledger remains **unimplemented in 7A** and refs/index-only until Stage 7D: no full transcripts, no embedded media, no policy authority, no external-effect authority, and no second artifact store.

Acceptance evidence: `reports/stage7a-state-evidence-model.json` (10/10 PASS, reproducible by `check-policy-architecture.py`).

## Reform v2 Stage 7B — Memory / Learning lifecycle

`memory-learning-lifecycle.json` defines the canonical selective-learning flow:

`OBSERVATION → CANDIDATE → EVIDENCE_RECURRENCE → PROMOTED_DURABLE → SUPERSEDED_EXPIRED`.

`office-learning` owns the process only; it is not a memory store. Learning-candidates own candidate status/evidence refs only. `owner-memory.md` owns durable owner-specific facts only when no more-specific SoT owns them. `vfmem` is the canonical router/verifier across durable sources, not a duplicate fact store. Cognee stays a replaceable derived semantic index with no canonical writeback.

Promotion requires an `accepted` candidate, concrete evidence, one explicit `promote_to` destination, canonical re-read and contradiction/scope checks. Automatic CI ingest cannot change status or promote. There is **no forced daily learning quota**: a retro with no meaningful durable lesson may end without a memory write.

Existing `pruned` remains a terminal compatibility status; new lifecycle expiry uses `expired`. No data migration, new database, always-on runtime, recurring cost, deletion, or external-effect authority change is introduced.

Acceptance evidence: `reports/stage7b-memory-learning-lifecycle.json` (10/10 PASS, reproducible by `check-learning-lifecycle.py`).

## Reform v2 Stage 7C — Research / Scheduler consolidation

`research-scheduler-consolidation.json` and its Stage 7C receipt are **historical acceptance witnesses** for the scheduler architecture that existed when Stage 7C closed. They are replayed against their pinned Git/readback evidence and are not current scheduling policy.

Current owner-facing authority moved on 2026-10-06 to `automation/chatgpt/manifest.json`: only Cognee Memory Sync once daily, VelvetOS Office Loop at 18:30, and Runtime Receipts Refresh at 19:15 remain recurring. Morning Brief and research are manual/event-driven; all known Grok routines are paused. Repository-owned GitHub schedules remain machine execution/verifier clocks and do not become owner-facing routine authority.

Upstream research now follows cheap detection first. `vf_upstream_watch.py` records current HEAD/release evidence; `vfresearch_cadence.py review-routing` sends only missing/stale exact bindings or explicit review tasks to deep review. A still-pending update whose `reviewedRemoteHead` + `reviewedRelease` remain current reuses that review instead of paying daily deep-review cost.

Every new/refreshed research artifact follows `packages/vfresearch/ARTIFACT-CONTRACT.md` and records `as_of`, `provenance`, `uncertainty` and `refresh_target`. Historical dated evidence is not rewritten merely to add metadata. Provider readback proves provider state only; it does not create policy authority.

Acceptance evidence: `reports/stage7c-research-scheduler-consolidation.json` (11/11 PASS, reproducible by `check-vfresearch.py`).

## Reform v2 Stage 7D — Artifact retention

Stage 7D turns the Stage 0/7A artifact classification into bounded retention without adding a database or external-effect authority. All nine artifact classes now have concrete retention semantics; no `CLASSIFY_IN_STAGE_7` placeholder remains.

The first copy-first migration targets Morning Green generated transport images. Eighteen historical `morning-green-assets-*` directories (86 files / 5,953,075 bytes) were copied to the local artifact archive and SHA-256 verified before their tracked tree copies were removed. The compact archive receipt is `reports/stage7d-morning-green-asset-archive.json`. The active producer now maintains one rolling `morning-green-current.html/json/txt` + `morning-green-assets-current/` transport bundle; Gmail still consumes repo-relative files, while daily image-copy accumulation stops.

Active-code/workflow consumer scan has zero references to removed dated transport bundles. Historical Markdown/state/receipt records may still mention their original paths as audit history. Rollback is Git revert plus the copy-first archive receipt; no external irreversible-delete authority is introduced.

Transient classes are now bounded by destination/retention policy rather than silently growing forever: harness checkpoints target active/cited 90-day state-store retention, vfmedia operational data targets current-state plus rolling event archive, compact audit receipts stay in Git when small, and large/creative outputs target artifact/archive or Media Vault after consumer checks.

The Stage 7A Work Ledger question is resolved as **NO_NEW_WORK_LEDGER_STORE**. `office/control/HANDOFF.json` already provides the refs-only continuation/index view, so another ledger would duplicate state/index authority. No new store, policy authority or external-effect authority is created.

Acceptance evidence: `reports/stage7d-artifact-retention.json` (11/11 PASS; >5 MB generated-image Git-noise reduction; reproducible by `check-policy-architecture.py`).


## Reform v2 Stage 7 — Integrated acceptance

Stage 7 is closed by `reports/stage7-acceptance.json`, an observation-only aggregate over the immutable 7A/7B/7C/7D receipts plus the post-7D `main` sensor run. The gate adds no new authority, store, daemon, scheduler, retention engine, or runtime behavior.

The integrated gate requires all nine conditions simultaneously:

- one explicit four-role state/evidence semantic model with all nine retention classes mapped;
- selective evidence-gated memory/learning, no automatic promotion, no forced daily quota, no new always-on memory system, and zero incremental recurring cost;
- one owner-facing clock authority for all nine protected routines, with GitHub schedules limited to machine execution/verification;
- research truth metadata (`as_of`, `provenance`, `uncertainty`, `refresh_target`) and cheap-detection-first deep-review routing;
- concrete artifact retention with copy-first migration, clean active-consumer scan, rollback evidence, and no unclassified retention placeholders;
- the Stage 7A Work Ledger question resolved as **NO_NEW_WORK_LEDGER_STORE**, with `office/control/HANDOFF.json` remaining the refs-only continuation view;
- unchanged external-effect authority across Stage 7;
- no duplicate store, daemon, scheduler, or recurring cost introduced by Stage 7;
- post-7D merged `main` full suite at 116/116.

The source receipts are content-bound by canonical JSON hashes, and the integrated receipt is regenerated byte-for-byte by `check-policy-architecture.py`.

Stage 8 entry is allowed: **Core / Instance Separation + Capability Placement**. Migration must remain domain-by-domain: VF-specific facts/bindings move to canonical instance ownership; Core keeps generic schemas/interfaces/algorithms; consumers migrate through compatibility resolution + parity proof; legacy paths retire only after consumer scan and rollback window. No big-bang delete.


## Reform v2 Stage 8A — Core / Instance inventory

Stage 8A is an **observation-only placement inventory**. It does not move business facts, cut over an instance resolver, retire compatibility paths, delete files, or change external-effect authority.

The reproducible inventory is `reports/stage8a-core-instance-inventory.json` and is generated by `scripts/generate-stage8a-core-instance-inventory.py`. It classifies 14 Core/Instance surfaces and identifies 10 duplicate or mixed-placement debts. The canonical Velvet Factory ownership anchors are the instance profile and instance desk under `instances/velvet-factory/`; Core should retain generic schemas, interfaces, algorithms and compatibility resolution rather than duplicate business values.

The first machine-enforced migration spine is now explicit:
- the Core VF sample is still consumed by the offering validator;
- Living Studio still carries embedded instance business-rule values consumed by the autonomy validator;
- the root workspace desk remains a compatibility bind consumed by the desk validator and other workspace consumers;
- printer fleet values are still read from the Core-repo vfprod path by Control API and related consumers.

The inventory also classifies mixed tool/account bindings, VF-specific ChatGPT/project distribution, value-bearing expert-module content, host/path bindings, and Control API instance defaults. Stage 8 preparation drafts remain non-normative design inputs only.

Placement classes distinguish generic Core contract from Instance public config, internal/private binding, runtime state, documentation distribution and explicit compatibility references. Every inventory row has a target owner/class and migration wave; no row authorizes deletion.

Next stage: **8B — Canonical Instance Config + Resolver Foundation**. Migration remains domain-by-domain: establish canonical instance values and a generic resolver first; prove parity and consumer behavior; migrate readers in 8C; retire legacy compatibility only after clean consumer scan and rollback window. No big-bang move/delete.


## Reform v2 Stage 8B — Resolver foundation slice

This slice establishes the generic instance-resolution contract before any broad consumer cutover.

`packages/velvetos/instance_resolver.py` resolves either the current instance workspace or an explicitly selected instance from Core. Core requires `--instance-id` or `VELVETOS_INSTANCE_ID`; there is no silent Velvet Factory default. Modern manifests are fail-closed on `surfaceContractVersion=1`, unsafe/absolute paths and parent traversal. A non-VF fixture with only a `profile` surface is part of the executable proof, so the resolver cannot accidentally require printing-specific surfaces.

`packages/velvetos/schema/instance-manifest.schema.json` is generic: only `profile` is a mandatory surface. `toolDesk` and `fleet` are optional surface vocabulary owned by instances that need them. The Velvet Factory manifest explicitly binds all three surfaces.

Printer fleet values now also exist at the canonical instance path `instances/velvet-factory/instance/fleet.json`. Stage 8B requires exact canonical-JSON parity with the legacy compatibility copy at `packages/vfprod/FLEET.json`; no Control API, Living Studio, vfprod or root-desk consumer is cut over in this slice, and the legacy file is not deletion-authorized.

The Stage 8A generator is snapshot-bound to its signed `prepared_against` Git tree. Later-stage code/references therefore cannot mutate Stage 8A historical consumer counts or inventory evidence.

Acceptance evidence: `reports/stage8b-instance-resolver-foundation.json` (9/9 PASS, regenerated by `check-policy-architecture.py`).

This does **not** close all of Stage 8B. Next is the remaining canonical-instance-config work, especially mixed tool/runtime bindings, before Stage 8C consumer migration. Consumer cutover and legacy retirement still require parity proof, clean consumer scan and rollback window.


## Reform v2 Stage 8B — Canonical instance config CLOSED

Stage 8B closes the canonical-placement work identified by the Stage 8A inventory before any reader migration.

The four `8B_CANONICAL_INSTANCE_CONFIG` surfaces are now resolved:

- `canonical-instance-profile` stays at `instances/velvet-factory/instance/velvet-factory.json`;
- `canonical-instance-desk` stays at `instances/velvet-factory/.cursor/vf-desk.json`;
- `vfprod-fleet-registry` now has a canonical instance copy at `instances/velvet-factory/instance/fleet.json`, parity-equal to the legacy compatibility file;
- `tool-status-mixed-registry` is split into generic Core semantics at `packages/velvetos/tool-status-contract.json` and VF-owned live/binding state at `instances/velvet-factory/instance/tool-status.json`.

`packages/velvetos/tool_status_resolver.py` composes Core rules + the selected instance `toolStatus` surface into the legacy `velvetos.tool-status.v1` shape. For Velvet Factory the composed object is exactly equal to the unchanged `packages/velvetos/TOOL-STATUS.json`. Core cannot invoke the resolver without an explicit instance id or `VELVETOS_INSTANCE_ID`.

The generic tool-status contract contains no Velvet Factory, Sderot, handle or provider-endpoint values. The instance state contains the ten current tool records but not generic rule semantics, and no secret-bearing key names are permitted by the Stage 8B receipt.

This is placement, not consumer cutover. The six known direct readers of the legacy tool-status composite remain byte-identical to the pre-8B main commit and still use the legacy path. The compatibility composite and legacy fleet file remain present and are not deletion-authorized.

Acceptance evidence: `reports/stage8b-canonical-instance-config.json` (10/10 PASS, regenerated by `check-policy-architecture.py`).

Stage 8C may now migrate readers domain-by-domain through the generic resolvers. Every cutover requires semantic parity, a compatibility fallback/rollback window and a clean consumer scan before legacy retirement. Control API and Living Studio remain projections rather than sources of truth, and external-effect authority must not change.


## Reform v2 Stage 8C — Sample/profile consumer cutover

The first Stage 8C domain removes machine/runtime dependence on the duplicate Core Velvet Factory sample profile. Runtime business facts now resolve from the canonical instance profile surface through `instance_resolver.py`.

`CORE.json` no longer carries a Velvet Factory `referenceProfile`. Core retains only a generic sample-directory policy: samples are documentation/rollback compatibility, never runtime authority. `check-vf-offering.py` resolves the explicit `velvet-factory` profile surface, `check-velvetos.py` validates only the canonical instance frontend, and `scripts/velvetos.py` is generic when no instance is selected. Enabled-module marks require `--instance-id` or `VELVETOS_INSTANCE_ID`.

The rollback sample remains present and byte-unchanged for this slice. Canonical and rollback module sets are still identical, so the prior VF module-marking behavior is preserved when the instance is selected explicitly. No deletion is authorized while the rollback window is open.

The active consumer scan is clean. The only remaining source references to the old sample path are the repository policy guard and two snapshot-bound historical Stage 8 generators; active docs no longer teach that path.

Acceptance evidence: `reports/stage8c-sample-profile-consumers.json` (10/10 PASS, regenerated by `check-policy-architecture.py`). External-effect policy is unchanged.

Stage 8C continues domain-by-domain with root desk, Living Studio, Control API/fleet projection, ChatGPT project distribution, expert-module instance values and Windows host binding. Each domain keeps its own parity proof and rollback window.


## Reform v2 Stage 8C — Root-desk direct-reader cutover

This Stage 8C slice migrates the remaining direct machine readers of the root reference desk to the canonical Velvet Factory `toolDesk` surface without deleting the root desk.

Before cutover, the canonical instance desk is enriched only with the exact instance-owned subtrees required by those readers. Gmail, Instagram, Gemini, ChatGPT, Drive and the `ops` seat are parity-equal to the unchanged root desk for the fields consumed by the migrated readers.

`scripts/check-vfmedia.py` and `scripts/vf_send_preflight.py` now resolve `toolDesk` through `instance_resolver.py` with explicit `velvet-factory` selection. `scripts/check-vf-offering.py` no longer treats `.cursor/vf-desk.json` as an active authority surface. The visual-standard guard was already bound to the canonical instance desk.

The root `.cursor/vf-desk.json` remains byte-unchanged from the pre-slice main commit and remains available during the rollback window. No delete is authorized, and external-effect policy is unchanged.

Acceptance evidence: `reports/stage8c-root-desk-readers.json` (9/9 PASS, regenerated by `check-policy-architecture.py`). Remaining root-desk references in vfmem/vfgraft/vfharness catalogs, documentation/rules and historical receipts are separate consumer domains and migrate independently.


## Reform v2 Stage 8C — Desk catalog/graph binding cutover

This slice migrates non-runtime catalog/graph references in vfmem, vfgraft and vfharness from the root `.cursor/vf-desk.json` path to the canonical instance desk at `instances/velvet-factory/.cursor/vf-desk.json`.

Eleven target files now contain 18 canonical desk bindings in total: vfmem 3, vfgraft 12 and vfharness 3. No root-only desk binding remains in those targets.

The root desk remains byte-unchanged from the pre-slice main commit for rollback; no delete is authorized and external-effect policy is unchanged.

Acceptance evidence: `reports/stage8c-desk-catalog-bindings.json` (8/8 PASS, regenerated by `check-policy-architecture.py`). Remaining Stage 8C domains continue independently.


## Reform v2 Stage 8C — Living Studio business-rule projection

`packages/velvetos/living-studio/AUTONOMY.json` no longer embeds Velvet Factory location, fulfillment, CTA or compliance values. It carries only a generic `businessRulesResolution` contract pointing at `packages/velvetos/living_studio_rules.py` and the selected instance `profile` surface.

The resolver is read-only and has no Velvet Factory default. From a Core checkout it requires an explicit instance id or `VELVETOS_INSTANCE_ID`. For Velvet Factory it projects the canonical profile into the same seven-field `businessRules` object that existed before the cutover; the Stage 8C receipt compares that projection directly with the pre-cutover AUTONOMY rules and requires exact equality.

`vf_autonomy.py` is intentionally unchanged in this slice because the embedded business rules were not part of its action execution path. `office/control-plane.json` is also unchanged. Living Studio remains a projection/router over canonical sources rather than a new source of truth, store, queue or approval authority.

Acceptance evidence: `reports/stage8c-living-studio-rules.json` (10/10 PASS, regenerated by `check-policy-architecture.py`). External-effect policy is unchanged.

Stage 8C continues with the remaining consumer domains, each with its own parity proof and rollback window.


## Reform v2 Stage 8C — Control API fleet/instance cutover

The Control API now resolves instance-owned production, agent and integration data through the canonical VelvetOS instance resolver rather than direct VF paths.

`production` resolves the selected instance `fleet` surface; `agents` and `integrations` resolve the selected instance `toolDesk` surface. When `VELVETOS_INSTANCE_ID` is absent in a Core checkout, these projections fail closed as `unavailable`; there is no silent Velvet Factory fallback.

The current VF Cloud Run deployment remains tenant-specific by setting `VELVETOS_INSTANCE_ID=velvet-factory` explicitly in `deploy.sh`. The image packages `instance_resolver.py`, the VF `INSTANCE.json`, profile, fleet, tool-status and desk surfaces. It no longer packages `packages/vfprod/FLEET.json` as the production authority.

The legacy vfprod fleet remains present and canonical-JSON equal to the instance fleet for rollback and non-migrated consumers. No delete is authorized in this slice. Print-event and maintenance history remain in vfprod because they are operational history/state, not fleet identity/config.

Acceptance evidence: `reports/stage8c-control-api-fleet.json` (9/9 PASS, regenerated by `check-policy-architecture.py`). `check-control-api.py` and all 40 Control API tests pass. External-effect policy is unchanged.


## Reform v2 Stage 8C — Expert-module parameterization

The three generic Core expert modules now keep only reusable methods. Velvet Factory CTA, pickup/location, phone/handle and exact visual-standard values remain instance-owned.

`expert-revenue-loop` resolves CTA and fulfillment semantics from the selected instance profile. `expert-social-booster` resolves CTA, location/fulfillment, contact and boost/approval semantics from the selected instance. `expert-media-director` resolves `creativeAutonomy.ownerApprovedVisualStandard`, including the required document/reference and artifact digest, from the selected instance profile.

The legacy machine marker `VF_VISUAL_STANDARD_GATE` remains as a compatibility identifier only. `check-visual-surface-enforcement.py` now treats the media-director module as a parameterized Core surface: it requires the marker, instance-profile authority semantics, artifact-digest validation, `visual_standard_unavailable` fail-closed behavior and no generic fallback, while explicitly forbidding the VF-specific standard path and digest inside the Core module.

The canonical Velvet Factory profile still owns the real CTA, fulfillment/location and approved visual-standard values. `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json` continues to reference the generic media-director module in both expected machine surfaces.

Acceptance evidence: `reports/stage8c-expert-modules.json` (8/8 PASS, regenerated by `check-policy-architecture.py`). External-effect policy is unchanged.

Stage 8C migration domains are now represented by their individual receipts; after the ChatGPT distribution and Windows host-binding slices, the next action is the Stage 8C closure receipt.


## Reform v2 Stage 8C — ChatGPT Project distribution consumers

This slice creates an instance-owned executable ChatGPT Project distribution at `instances/velvet-factory/distribution/chatgpt-project` while retaining `packages/velvetos/chatgpt-project` as rollback compatibility; only the required runtime/asset trust pins are refreshed in that compatibility chain.

The instance manifest exposes `chatgptProject` through `distribution/chatgpt-project/LATEST.json`. The generic helper `scripts/vf_project_distribution.py` resolves that surface through `instance_resolver.py`; a Core checkout without explicit instance selection fails closed.

`scripts/check-chat-cold-start-preflight.py` now reads the explicit Velvet Factory instance distribution. `scripts/vf_chat_cold_start_preflight.py` no longer embeds the VF 6.6.4 contract/revision/bundle/authority filename; it discovers bundle identity from `LATEST.json` when present, otherwise from a unique asset manifest. The synthetic cold-start preflight remains PASS.

The instance distribution contains the same 33 files and is byte-equal to the active Core compatibility bundle. All compatibility payload files remain unchanged except the required trust-pin refresh: the `vf_chat_cold_start_preflight.py` runtime SHA inside `ASSET-MANIFEST-v6.6.4.json`, plus the resulting `assetManifestSha256` in `PROJECT-AUTHORITY-MANIFEST.json`. No business payload changed, and deletion remains unauthorized during this rollback window.

Acceptance evidence: `reports/stage8c-chatgpt-distribution-consumers.json` (10/10 PASS, regenerated by `check-policy-architecture.py`). Stage 8B canonical-config regeneration is snapshot-bound and remains byte-identical. External-effect policy is unchanged.

This consumer-cutover slice is complete. The Core compatibility bundle remains intentionally available for rollback until Stage 8D retirement; Windows host binding is the final separate Stage 8C migration domain.

## Reform v2 Stage 8C — Windows host binding

Concrete Windows deployment values are instance-owned. Velvet Factory exposes `windowsHostBinding` at `instances/velvet-factory/instance/windows-host-binding.json`, containing the current Windows host id, machine-scoped environment values and lane names.

`packages/velvetos/WINDOWS-PATH-CONTRACT.md` is generic Core policy: it defines required variables, ownership lanes, fail-closed semantics and forbidden fallbacks without embedding a drive letter, business location, username or host id. The always-on Windows Cursor rule follows the same generic contract.

Edge, Speech and Manim Windows bootstraps resolve host identity from `VELVETOS_HOST_ID` and stop when it is missing. Path resolution remains explicit through `VELVET_ROOT`, `VELVETOS_REPO_ROOT`, `VELVETOS_RUNTIME_ROOT` and `VELVETOS_STATE_ROOT`; no user-profile or temporary-directory fallback is reintroduced. vfmem/Cognee Windows consumers remain variable-driven and fail closed.

`packages/vfmcp/RENDER-HOSTS.json` and `packages/vfigos/OPENPOST.json` remain the unchanged operational registries. The acceptance gate verifies their values still agree with the selected instance binding rather than moving those registries in this slice.

Acceptance evidence: `reports/stage8c-windows-host-binding.json` (8/8 PASS, regenerated by `check-policy-architecture.py`). Historical Stage 8B canonical-config evidence remains source-commit-bound and byte-reproducible. With ChatGPT distribution already merged, this closes the final separate Stage 8C migration domain; `remaining_domains=[]`. External-effect policy is unchanged.

## Reform v2 Stage 8C — Integrated closure

Stage 8C is closed only by aggregate evidence, not by deleting compatibility surfaces. The closure receipt maps all seven `8C_CONSUMER_MIGRATION` surfaces from the Stage 8A inventory to their passed domain receipts, requires the domain-level direct-consumer scans to be clean, and verifies explicit fail-closed instance resolution across the migrated paths.

Rollback compatibility remains intentionally present for Stage 8D: the legacy Velvet Factory sample, root desk, vfprod fleet, TOOL-STATUS compatibility composite and Core ChatGPT compatibility bundle are all still available. The closure gate sets deletion authority to false and does not reinterpret compatibility files as runtime authority.

Acceptance evidence: `reports/stage8c-closure.json` (9/9 PASS). It is bound to post-merge main `11ce1ca3a44cb21af24add900ab6b0e9d9e0a47e` and GitHub Actions full suite run `37221071250` / job `111491351299`, which passed 116/116 sensors. The receipt is regenerated byte-for-byte by `check-policy-architecture.py`.

Stage 8D may begin, but legacy retirement is a separate deletion stage. It still requires clean consumer scan, parity proof, rollback-window evidence and explicit deletion evidence. No big-bang delete is authorized.

## Reform v2 Stage 8D — Retirement readiness

Stage 8D begins with an observation-only readiness gate, not deletion. `reports/stage8d-retirement-readiness.json` classifies the five retained compatibility surfaces and requires the post-Stage-8C `main` full sensor suite to be green before any retirement work is considered.

Current result: **BLOCKED_PENDING_MIGRATION_OR_ROLLBACK_WINDOW** and `retirement_authorized=false`. The legacy sample has no active runtime consumer but its rollback window is still explicitly open. Root desk, fleet, TOOL-STATUS and the Core ChatGPT compatibility bundle still have active compatibility consumers and also lack explicit rollback-window closure evidence.

No path may be deleted while `retirement_authorized=false`. Remaining consumers must migrate domain-by-domain with parity and fail-closed behavior preserved; rollback windows close only through explicit evidence, never by elapsed-time inference.

## Reform v2 Stage 8D — Fleet compatibility consumer migration

The first Stage 8D migration slice removes the sole active Living Studio dependency on the legacy vfprod fleet path. `production-planner` now declares `instance:surface:fleet`, matching the canonical instance surface already used by Control API and other instance-aware consumers.

The legacy `packages/vfprod/FLEET.json` file remains present and parity-equal to `instances/velvet-factory/instance/fleet.json`. The rollback window remains open and deletion is still unauthorized; this slice removes an active compatibility consumer only.

The initial Stage 8D readiness receipt is now replayed from the Git snapshot where it was created, so later migrations cannot rewrite that historical baseline. New progress is recorded separately in `reports/stage8d-fleet-consumer-migration.json` (8/8 PASS).

## Reform v2 Stage 8D — Root desk compatibility consumer migration

The active root-desk compatibility consumers are migrated without deleting the retained root desk. The always-on Velvet Factory Cursor rule now names the selected instance `toolDesk` surface, and visual-standard enforcement resolves `toolDesk` through the generic instance resolver rather than constructing an ambiguous desk path.

The Stage 8C root-desk receipt remains the parity proof for Gmail, Instagram, Gemini, ChatGPT, Drive and the ops seat. The root desk stays present while the rollback window remains open; deletion is not authorized. Progress is recorded separately in `reports/stage8d-root-desk-consumer-migration.json`.

## Reform v2 Stage 8D — Tool-status compatibility consumer migration

Active tool authority now resolves from the selected `instance:surface:toolStatus` through `packages/velvetos/tool_status_resolver.py`. The generic Core contract defines semantics while the selected instance owns current tool state; Core execution still fails closed without explicit instance selection.

The six Stage 8B direct-reader bindings have been retired from the legacy composite: five real status readers compose through the resolver, while the unused `check-vfmcp.py` compatibility binding was removed rather than replaced by a fake read. Active Cursor, instance, operations, OpenPost and MCP authority surfaces now point at the instance tool-status authority.

`packages/velvetos/TOOL-STATUS.json` remains physically present and is still exactly parity-equal to the composed contract + instance state. It is rollback/parity evidence only; the rollback window remains open and deletion is not authorized. `legacy-parity` remains the bounded diagnostic verifier.

Progress is recorded in `reports/stage8d-tool-status-consumer-migration.json` (12/12 PASS). `check-policy-architecture.py` regenerates it byte-for-byte and verifies zero active-authority legacy references, exact composition parity, retained rollback compatibility and unchanged external-effect policy.

## Reform v2 Stage 8D - ChatGPT Core compatibility consumer migration

Active Project/ChatGPT runtime authority now resolves from the selected `instance:surface:chatgptProject` distribution. `PROJECT-AUTHORITY-MANIFEST.json` stores logical surface references, while `scripts/vf_project_bundle.py` maps them through the generic instance/distribution resolver without embedding a Velvet Factory default. VF runtime callers select `velvet-factory` explicitly and Core checkout without an instance remains fail-closed.

The Reel route, visual product-truth guide, Project bundle/request-gate sensors and isolated Chat runtime checks all resolve the instance-owned distribution. The retained `packages/velvetos/chatgpt-project` tree remains physically present and byte-equal to `instances/velvet-factory/distribution/chatgpt-project` across all 33 files, so rollback compatibility is preserved without treating the Core copy as active authority.

Historical Stage 8C ChatGPT evidence is replayed from its approved source snapshot and remains byte-for-byte reproducible even after this Stage 8D authority cutover. Progress is recorded in `reports/stage8d-chatgpt-core-consumer-migration.json` (12/12 PASS, active legacy references 0, parity true). The rollback window remains open and deletion remains unauthorized.

## Reform v2 Stage 8D - Post-migration retirement readiness

After the four Stage 8D consumer-migration slices, all five retained compatibility surfaces are now free of active migration blockers. The sample profile remains non-runtime authority, and the fleet, root desk, tool-status and ChatGPT Core receipts each prove their active consumer cutovers while preserving parity or equivalent rollback evidence.

`reports/stage8d-post-migration-readiness.json` records this state as `BLOCKED_ROLLBACK_WINDOWS_ONLY`: all five compatibility paths remain present, all five rollback windows remain explicitly open, and no surface has rollback-window closure evidence yet. Consumer migration completion therefore does **not** authorize deletion. `retirement_authorized=false` and every surface keeps `delete_authorized=false`.

The gate is prepared against merged main `aa6e163fa635a540e11bd8f40fd65d08bc0c4ade`, which passed the full 116/116 sensor suite after PR #527. The next action is evidence-only: collect explicit rollback-window closure evidence per surface. No window may close by elapsed time or inference, and no big-bang delete is authorized.

## Reform v2 Stage 8D - Sample-profile rollback closure

`reports/stage8d-sample-profile-rollback-closure.json` closes only the `sample_profile` rollback observation window. This is a later evidence layer; it does not rewrite the historical post-migration baseline above. The closure is based on a clean current consumer scan, byte-stability of the retained sample since PR #510, canonical/legacy module parity, unchanged external-effect authority and downstream main full-suite observation.

The observation window contains 18 `VelvetOS Core Sensors` main-push runs: 17 successful and one failure. The failure was `check-vfresearch.py` after a provider-readback pointer refresh, explicitly unrelated to `sample_profile`; PR #519 snapshot-bound the historical Stage 7C replay and all 10 observed main runs from that repair through `c344ecb1` are green. Closure authority therefore comes from classified operational evidence, not from elapsed time.

The legacy sample remains physically present. `rollback_window_closed=true` means the observation window is explicitly closed for this one surface; it does **not** mean the file is deleted or that deletion is already authorized. `delete_authorized=false` and `retirement_authorized=false` remain in force. A separate isolated retirement gate must revalidate consumers, parity/closure evidence, current main CI and external-effect authority before it can authorize deletion.

## Reform v2 Stage 8D - Sample-profile hidden-consumer correction

A retirement preflight found that `scripts/check-public-cta.py` still read the legacy sample through a path assembled from `Path` segments. The earlier exact-string scan therefore undercounted active consumers. The hidden consumer is now migrated to the canonical instance profile, and `reports/stage8d-sample-profile-consumer-correction.json` records a semantic scan that proves one active reference before the fix and zero after it.

PR #529's rollback-closure receipt remains preserved as historical evidence, but it is explicitly superseded for retirement authority. The `sample_profile` rollback window is reopened, `retirement_ready_for_deletion_gate=false`, and `delete_authorized=false`. Fresh downstream main full-suite observations after this corrective cutover are required before a new explicit re-closure receipt may make this surface eligible for deletion.

## Reform v2 Stage 8D - Retirement semantic audit

`reports/stage8d-retirement-semantic-audit.json` is an observation-only, fail-closed preflight over the five retained compatibility surfaces. It catches both literal legacy paths and paths assembled from components, classifies evidence/history/documentation separately from machine/config candidates, and never closes a rollback window or authorizes deletion.

Against merged main `30d72da6`, only `sample_profile` had no machine/config candidate blockers. `fleet`, `root_desk`, `tool_status` and `chatgpt_core_bundle` remained blocked pending surface-by-surface review/migration of their candidate references. Ambiguity blocks retirement; it is never interpreted as proof of safety.

## Reform v2 Stage 8D - Root desk semantic correction

`reports/stage8d-root-desk-runtime-consumer-correction.json` records the corrective root-desk pass after the semantic audit exposed readers missed by the earlier narrow migration receipt. Ten live readers now resolve the selected `toolDesk` surface explicitly; the canonical Velvet Factory desk preserves every legacy operational tool, seat, specialist, skill and note required by those readers while keeping instance identity and fail-closed creative gates intact.

The root compatibility desk remains byte-unchanged and present. The regenerated semantic audit now reports `sample_profile` and `root_desk` preflight-clear (2/5), with `fleet`, `tool_status` and `chatgpt_core_bundle` still blocked. This correction does **not** close the root-desk rollback window and does not authorize deletion; fresh downstream main evidence plus a later explicit rollback-closure/deletion gate are still required.

## Reform v2 Stage 8D - Fleet semantic correction

`reports/stage8d-fleet-runtime-consumer-correction.json` records the corrective fleet pass after the semantic audit exposed remaining runtime and active-documentation references. `vfprod`, its validator, Living Studio and the Core validator now resolve the canonical instance fleet; active operational documentation points to `instance:surface:fleet` or the canonical instance fleet path. The two legacy-path assertions in tests remain explicit negative controls.

The retained root desk is a separate rollback surface and still contains its historical fleet reference. That cross-surface reference is classified as non-runtime only when the same Git snapshot contains a passing root-desk correction receipt with zero semantic blockers and deletion still unauthorized. The regenerated semantic audit therefore reports `sample_profile`, `root_desk` and `fleet` preflight-clear (3/5), leaving only `tool_status` and `chatgpt_core_bundle` blocked. Fleet rollback remains open and the legacy `packages/vfprod/FLEET.json` remains byte-unchanged and parity-equal; no deletion is authorized.

## Reform v2 Stage 8D - Tool-status semantic correction

`reports/stage8d-tool-status-semantic-correction.json` proves that the remaining six semantic references to `packages/velvetos/TOOL-STATUS.json` are not active authority consumers. `CORE.json` and the generic tool-status contract retain only rollback metadata, the contract schema constrains that metadata, the resolver exposes a dedicated `legacy-parity` command, `check-velvetos.py` is a parity sensor, and the sensor registry uses the legacy path only as `owns`/`triggered_by` input for the two already-migrated status sensors. Each classification is validated from the file contents at the audited Git snapshot; a role change falls back to a blocker.

Canonical tool status remains `instance:surface:toolStatus`, composition is exactly parity-equal to the retained compatibility composite, and the legacy file remains byte-unchanged. The regenerated semantic audit now reports four preflight-clear surfaces (`sample_profile`, `root_desk`, `fleet`, `tool_status`), leaving only `chatgpt_core_bundle` blocked. This does not close the tool-status rollback window and does not authorize deletion.

## Reform v2 Stage 8D - ChatGPT semantic correction

`reports/stage8d-chatgpt-semantic-correction.json` closes the final semantic-preflight gap without deleting the retained Core bundle. Brand provenance now points to the canonical instance distribution and all 18 ChatGPT-related sensor-registry bindings follow `instances/velvet-factory/distribution/chatgpt-project`. `check-project-bundle.py`, `check-reel-route-sync.py` and `check-velvetos.py` are verified from their source contents as instance-surface consumers rather than legacy readers. The legacy-specific `.gitattributes` entries remain in place only to preserve rollback bytes while the compatibility bundle still exists.

The canonical instance distribution and the retained Core bundle remain exactly 33/33 files byte-equal. The regenerated semantic audit now reports **5/5 preflight-clear surfaces with zero candidate blockers**. This is not deletion authority: all rollback windows remain explicitly open, `retirement_authorized=false`, and `delete_authorized=false` until fresh downstream main evidence and later per-surface rollback-closure/deletion gates are recorded.

## Reform v2 Stage 8D - Sample-profile rollback re-closure v2

`reports/stage8d-sample-profile-rollback-reclosure.json` is the current rollback-closure authority for `sample_profile` after the hidden-consumer correction. The original PR #529 closure remains preserved as historical evidence but is explicitly superseded; it is never reused as deletion authority.

The re-closure is evidence-driven rather than time-driven. It requires the corrected sample semantic preflight to remain clear, all five Stage 8D semantic surfaces to be 5/5 clear, the retained sample bytes to remain unchanged since PR #531, canonical/legacy module parity, unchanged external-effect policy authority, and six distinct successful `VelvetOS Core Sensors` main-push full-suite observations from `44a2546a` through `b722f622`.

This receipt closes only the observation window. The legacy sample remains physically present; `rollback_window_closed=true` and `retirement_ready_for_deletion_gate=true`, while `delete_authorized=false` and `retirement_authorized=false` remain enforced. Any deletion must happen in a later isolated sample-only gate that revalidates current main, semantic state, this re-closure receipt, and external-effect authority.

## Reform v2 Stage 8D - Root-desk rollback closure

`reports/stage8d-root-desk-rollback-closure.json` closes the `root_desk` observation window after the PR #533 runtime-consumer correction. Closure requires all ten known runtime readers to remain on explicit `instance:surface:toolDesk` resolution, the retained root desk bytes to remain unchanged, operational parity to remain intact, all five Stage 8D semantic preflights to stay clear, external-effect policy authority to remain unchanged, and seven distinct successful exact-main-head `VelvetOS Core Sensors` observations through `8aa691f9`. The first six are push-triggered; the latest scheduled VF Media head is exact-SHA verified by two successful `workflow_dispatch` full-suite runs.

The fleet correction intentionally changed one canonical desk note from the retained legacy `FLEET.json` authority hint to `instance:surface:fleet`. The closure treats that note as equivalent only when the rest of the note is byte-equivalent after the authority prefix and the passing fleet-correction receipt proves the instance desk was part of the canonical fleet documentation migration. Every other legacy note must still be preserved.

This closure does not delete the compatibility desk and does not authorize deletion. `rollback_window_closed=true` and `retirement_ready_for_deletion_gate=true`; `delete_authorized=false` and `retirement_authorized=false` remain enforced until a later isolated root-desk deletion gate revalidates current main, semantic state, parity, closure evidence and policy authority.

## Reform v2 Stage 8D - Fleet rollback closure

`reports/stage8d-fleet-rollback-closure.json` closes the `fleet` rollback observation window after the PR #534 corrective consumer migration. The closure revalidates the four live fleet readers, all seven active-documentation bindings, exact JSON equality between the canonical instance fleet and retained compatibility fleet, unchanged legacy bytes, 5/5 Stage 8D semantic clearance and unchanged external-effect policy authority.

The observation window uses eight distinct exact-main-head successful full-suite boundaries from `027700b3` through `840206d0`. The scheduled VF Media head `8aa691f9` is represented by a successful exact-SHA workflow-dispatch run, with a second successful run recorded as corroborating evidence; the remaining boundaries are push-triggered main runs.

This closure does not delete `packages/vfprod/FLEET.json` and does not authorize deletion. `rollback_window_closed=true` and `retirement_ready_for_deletion_gate=true`; `delete_authorized=false` and `retirement_authorized=false` remain enforced until a later isolated fleet deletion gate revalidates current main, semantic state, exact parity, closure evidence and policy authority.

## Reform v2 Stage 8D - Tool-status rollback closure

`reports/stage8d-tool-status-rollback-closure.json` closes the `tool_status` rollback observation window after the PR #536 semantic correction. Closure revalidates all six reviewed machine/config references from their current contents, requires active authority to remain `instance:surface:toolStatus`, requires the canonical contract + instance state composition to remain exactly parity-equal to the retained `TOOL-STATUS.json`, requires the legacy bytes and external-effect policy authority to remain unchanged, and binds the evidence to seven successful exact-main-head `VelvetOS Core Sensors` runs through `e853c049`.

The six retained references are still compatibility-only: Core/contract rollback metadata, the schema constraint for that metadata, the dedicated parity implementation, the parity sensor and the two status-sensor registry bindings. A role change in any of them fails closed through the semantic classifier.

This closure does not delete `TOOL-STATUS.json` and does not remove rollback metadata. `rollback_window_closed=true` and `retirement_ready_for_deletion_gate=true`; `delete_authorized=false` and `retirement_authorized=false` remain enforced until a separate isolated tool-status deletion gate revalidates current main, classification, parity, closure evidence and policy authority.

## Reform v2 Stage 8D - ChatGPT rollback closure

`reports/stage8d-chatgpt-rollback-closure.json` closes the final Stage 8D rollback observation window, `chatgpt_core_bundle`, after the PR #538 semantic correction. Closure requires the retained Core bundle and canonical instance distribution to remain exactly 33/33 files byte-equal, the legacy tree and rollback `.gitattributes` to remain unchanged, brand provenance and all 18 sensor bindings to remain canonical, all six reviewed candidate references to keep their content-validated safe roles, all five semantic preflights to remain clear, and external-effect authority to remain unchanged.

The observation window is bound to six successful exact-main-head `VelvetOS Core Sensors` push runs from `b722f622` through `725d2e92`. Closure is evidence-driven rather than elapsed-time-driven.

This closure does not delete the Core bundle and does not remove rollback `.gitattributes`. After this receipt lands, all five Stage 8D compatibility surfaces have explicit rollback-window closure evidence and are individually eligible to enter their separate deletion gates. `delete_authorized=false` and `retirement_authorized=false` remain enforced; deletion must still happen one surface at a time after revalidating current main, semantic state, the surface-specific closure receipt, parity/immutability requirements and external-effect authority.

## Reform v2 Stage 8D - sample_profile deletion gate

`reports/stage8d-sample-profile-deletion-gate.json` is the evidence-only deletion gate for the retained Velvet Factory sample-profile compatibility file. It authorizes deletion of exactly that single compatibility target on a later isolated PR; it does not delete the file itself and does not authorize deletion of any other compatibility surface.

The gate revalidates the authoritative sample re-closure, all five rollback-closure receipts, current 5/5 semantic clearance, zero active sample legacy consumers, exact-main `VelvetOS Core Sensors` success on `495a6c91` (run `37277013397`), unchanged external-effect policy authority, and canonical coverage of every retained business/config field. Only the sample-only metadata `role=sample` and the explicit Core compatibility note are excluded from canonical coverage. The exact legacy blob is anchored as Git blob `7ffc401ef4ce87acd25c48a2d095ab82eca8f76b`, SHA-256 `01a792c229721fa95590636a645aab8d46439d6efd523c48b6ee6b73ca366f5d`, 5214 bytes, restorable from `495a6c91`.

The resulting authority is intentionally narrow: `delete_authorized=true` only for `sample_profile` and only for the exact legacy path; `deletion_performed=false` and `retirement_authorized=false`. A separate deletion PR must revalidate the gate and remove exactly that path.

## Reform v2 Stage 8D - sample_profile deletion

`reports/stage8d-sample-profile-deletion.json` records the isolated retirement of the sample-profile compatibility file after PR #546 merged the evidence-only deletion gate. The deletion base is merge `94d70732`; its `VelvetOS Core Sensors` main-push run `37280812073` succeeded before the deletion candidate was prepared.

The deletion removes exactly `packages/velvetos/samples/velvet-factory.json`. The canonical profile at `instances/velvet-factory/instance/velvet-factory.json` remains present and continues to cover all business/config fields and all 18 enabled modules. The other four Stage 8D compatibility surfaces remain present, byte-unchanged from the deletion base and deletion-unauthorized by this receipt.

The deleted sample remains recoverable from Git using the gate restore anchor: blob `7ffc401ef4ce87acd25c48a2d095ab82eca8f76b`, SHA-256 `01a792c229721fa95590636a645aab8d46439d6efd523c48b6ee6b73ca366f5d`, 5214 bytes, sourced from `495a6c91`. Historical Stage 8C sample and closure receipts remain byte-reproducible from their creation commits after their generators were snapshot-bound. External-effect authority is unchanged.

This receipt sets `deletion_performed=true` and `retirement_authorized=true` only for `sample_profile`. It does not authorize deletion of `root_desk`, `fleet`, `tool_status` or `chatgpt_core_bundle`; each remaining surface still requires its own evidence-only deletion gate followed by a separate isolated deletion PR.

## Reform v2 Stage 8D - root_desk deletion gate

`reports/stage8d-root-desk-deletion-gate.json` is the evidence-only deletion gate for the retained root desk compatibility file. It is prepared against exact main `dfd699dc` after the isolated `sample_profile` retirement merged and passed post-merge `VelvetOS Core Sensors` run `37284249359`.

The gate accepts the already-missing sample only through its authoritative retirement receipt; physical absence alone is insufficient. The other three retained compatibility surfaces remain closure-complete, present and deletion-unauthorized. Current semantic audit remains 5/5 clear with exactly `sample_profile` retired, while all ten root-desk runtime readers continue resolving the canonical `toolDesk` surface with no direct root compatibility reads.

Operational parity is revalidated before authorization: all 18 legacy tool rows, 6 seats and 38 specialists are preserved by the canonical instance desk, legacy skills remain covered, non-fleet notes remain present, and the legacy fleet note is accepted only through its explicit canonical `instance:surface:fleet` supersession. External-effect authority is unchanged.

The exact retained root desk is restore-anchored as Git blob `30ddd380f1d556dd1b444c3ca6b153f6d6188e1f`, SHA-256 `702695ffa72b8f0e56738cc533cc95ee2d6a6cd76c66cf58f2a84d3658a1116b`, 34186 bytes, sourced from `dfd699dc`. This gate sets `delete_authorized=true` only for `root_desk`; `deletion_performed=false` and `retirement_authorized=false` remain enforced until a separate isolated deletion PR.

## Reform v2 Stage 8D - root_desk deletion

`reports/stage8d-root-desk-deletion.json` records the isolated retirement completed by PR #550. The deletion was prepared against exact gate-merge main `98ac4ce1`, after `VelvetOS Core Sensors` run `37286661000` succeeded on that exact SHA, and removes only `.cursor/vf-desk.json`.

The canonical desk at `instances/velvet-factory/.cursor/vf-desk.json` remains authoritative. All ten runtime readers continue resolving the explicit instance `toolDesk` surface, while parity remains 18 tools, 6 seats and 38 specialists with legacy skills covered and notes preserved or explicitly superseded. The prior `sample_profile` retirement remains authoritative; `fleet`, `tool_status` and `chatgpt_core_bundle` remain present and deletion-unauthorized.

The retired root desk remains recoverable as Git blob `30ddd380f1d556dd1b444c3ca6b153f6d6188e1f`, SHA-256 `702695ffa72b8f0e56738cc533cc95ee2d6a6cd76c66cf58f2a84d3658a1116b`, 34186 bytes. Historical Stage 8C desk receipts remain byte-reproducible from their creation snapshots. External-effect authority is unchanged.

## Reform v2 Stage 8D - fleet deletion gate

`reports/stage8d-fleet-deletion-gate.json` is the evidence-only deletion gate for `packages/vfprod/FLEET.json`. It is prepared against exact main `12e8ea4c` after the isolated `root_desk` retirement merged and the exact-main `VelvetOS Core Sensors` run `37294141817` succeeded.

The gate accepts the already-missing `sample_profile` and `root_desk` only through their authoritative retirement receipts. Current semantic audit remains 5/5 clear with exactly those two surfaces retired. The retained fleet remains exactly byte/content equal to `instances/velvet-factory/instance/fleet.json`; all four live fleet readers and all seven active-documentation bindings remain canonical, and the fleet rollback-closure evidence remains valid.

The retained fleet is restore-anchored as Git blob `d76126ce8ac08b5faf86b5069df18886118b8f1a`, SHA-256 `baffa4db8f61d33339f89161155e620d0914a802fe230b241a566bdadb085f3c`, 1364 bytes, sourced from `12e8ea4c`. This gate sets `delete_authorized=true` only for `fleet`; `deletion_performed=false` and `retirement_authorized=false`. `tool_status` and `chatgpt_core_bundle` remain deletion-unauthorized, and external-effect authority is unchanged.

## Reform v2 Stage 8D - tool_status deletion gate

`reports/stage8d-tool-status-deletion-gate.json` is the evidence-only deletion gate for `packages/velvetos/TOOL-STATUS.json`. It is prepared against exact main `3f7bd148` after the isolated `fleet` retirement merged and exact-main `VelvetOS Core Sensors` run `37301696406` succeeded.

The gate accepts the already-missing `sample_profile`, `root_desk` and `fleet` surfaces only through their authoritative retirement receipts. Current semantic audit remains 5/5 clear with exactly those three surfaces retired. Active tool-status authority remains `instance:surface:toolStatus`; the canonical generic contract plus Velvet Factory instance state still composes exactly to the retained compatibility composite, and all six remaining machine/config references remain content-validated rollback/parity metadata.

The retained composite is restore-anchored as Git blob `e5bb196c5bfd0a0bd5b6fe95df1549de9b1d2372`, SHA-256 `0b1f082887c9e4d5367574b746bee36f62f4aced0f8cf631a08551e553030add`, 6753 bytes, sourced from `3f7bd148`. This gate sets `delete_authorized=true` only for `tool_status`; `deletion_performed=false` and `retirement_authorized=false`. `chatgpt_core_bundle` remains deletion-unauthorized, and external-effect authority is unchanged.

## Reform v2 Stage 8D - tool_status retirement

`reports/stage8d-tool-status-deletion.json` records the isolated removal of `packages/velvetos/TOOL-STATUS.json` after PR #553 merged the evidence-only gate at exact main `376652dc`. Post-gate `VelvetOS Core Sensors` run `37310304615` initially hit a GitHub-runner dependency failure when `packages.microsoft.com` returned HTTP 403 during `apt-get update`, preventing ffmpeg/ffprobe installation; rerun attempt 2 on the same merge SHA completed successfully. Local post-merge verification on that same SHA also passed 116/116.

The deletion is limited to the compatibility composite. Active authority remains `instance:surface:toolStatus`; `packages/velvetos/tool-status-contract.json` plus `instances/velvet-factory/instance/tool-status.json` still compose exactly to the deleted legacy JSON. The six reviewed references remain bounded rollback/parity metadata. The live Core validator and `legacy-parity` diagnostic no longer dereference the retired file: when it is absent they validate the canonical composition against the authoritative deletion-receipt hash/Git anchor. The restore anchor remains Git blob `e5bb196c5bfd0a0bd5b6fe95df1549de9b1d2372` / SHA-256 `0b1f082887c9e4d5367574b746bee36f62f4aced0f8cf631a08551e553030add` / 6753 bytes from `3f7bd148`, and the historical migration/correction/closure receipts remain byte-anchored to their creation commits.

This receipt sets `deletion_performed=true` and `retirement_authorized=true` only for `tool_status`. `sample_profile`, `root_desk` and `fleet` remain retired, `chatgpt_core_bundle` remains present and deletion-unauthorized, and external-effect authority remains unchanged.

## Reform v2 Stage 8D - chatgpt_core_bundle deletion gate

`reports/stage8d-chatgpt-deletion-gate.json` is the evidence-only deletion gate for the retained Core ChatGPT compatibility bundle. It is prepared against exact main `774d4e61` after the isolated `tool_status` retirement merged and exact-main `VelvetOS Core Sensors` run `37319349828` succeeded.

The gate accepts the already-missing `sample_profile`, `root_desk`, `fleet` and `tool_status` surfaces only through their authoritative retirement receipts. Current semantic audit remains 5/5 clear with exactly those four surfaces retired. Active ChatGPT Project authority remains `instance:surface:chatgptProject`; the retained Core bundle and the canonical Velvet Factory distribution remain exactly 33/33 files byte-equal, all 18 sensor bindings and brand-asset provenance remain canonical, and the six remaining references are content-validated compatibility/canonical metadata rather than runtime authority.

The exact retained legacy tree is restore-anchored as Git tree `d7961fe63ff483b0085d9689b8b3c1b4d35a35f4` with manifest SHA-256 `9d99f8dc6f7f5dc0972cb66dcc3dbba38e5ba5e272d7a3aed4588acfb26193bb`. The 24 legacy-specific `.gitattributes` byte-preservation lines are separately anchored by SHA-256 `dd0fe2cd643d43a7eae46b016e4403856f6f74dc9a64b414e2a64ad9326a530f`; the canonical instance distribution rule must remain. This gate sets `delete_authorized=true` only for `chatgpt_core_bundle` and those recorded legacy attribute lines. `deletion_performed=false` and `retirement_authorized=false` remain enforced until a separate isolated deletion PR. External-effect authority is unchanged.

## Reform v2 Stage 8D - chatgpt_core_bundle retirement

`reports/stage8d-chatgpt-deletion.json` records the final isolated Stage 8D compatibility retirement after PR #555 merged the evidence-only gate at `b3af7b9e`. The deletion is prepared against exact current main `d593f1b6`, after `VelvetOS Core Sensors` run `37335910275` succeeded on that SHA. The change removes exactly the 33 tracked files under `packages/velvetos/chatgpt-project` and exactly the 24 gate-recorded legacy-only `.gitattributes` lines; no other tracked path is deleted and the canonical instance distribution rule remains.

Active authority remains `instance:surface:chatgptProject`. The canonical Velvet Factory distribution remains 33/33 files with bytes equal to the retired legacy tree, while remaining direct legacy-path references are bounded to historical state, documentation, policy evidence and Stage 8 generators. The exact legacy tree remains recoverable from Git tree `d7961fe63ff483b0085d9689b8b3c1b4d35a35f4`, manifest SHA-256 `9d99f8dc6f7f5dc0972cb66dcc3dbba38e5ba5e272d7a3aed4588acfb26193bb`; the removed attribute set remains anchored by SHA-256 `dd0fe2cd643d43a7eae46b016e4403856f6f74dc9a64b414e2a64ad9326a530f`.

This receipt sets `deletion_performed=true` and `retirement_authorized=true` for `chatgpt_core_bundle`. Together with the prior four authoritative deletion receipts, all five Stage 8D compatibility surfaces are retirement-complete pending the integrated Stage 8D final acceptance. Historical ChatGPT receipts remain byte-anchored and external-effect authority is unchanged.


## Reform v2 Stage 8D - Final acceptance / Reform v2 closure

`reports/stage8d-final-acceptance.json` is the integrated evidence-only closure for Stage 8D and Reform v2. It is prepared against exact main `87f02307` after PR #558 merged the final isolated `chatgpt_core_bundle` retirement and PR #559 refreshed runtime receipts without reopening compatibility authority. Exact-main `VelvetOS Core Sensors` run `37342022333` passed the full 116/116 suite without repository mutation, and README System Pulse workflow-dispatch run `37343038165` succeeded on the same SHA.

The final semantic audit reports all five compatibility surfaces retired and 5/5 preflight-clear with zero candidate blockers. Each physical absence is accepted only through its authoritative deletion receipt. The final receipt revalidates every restore anchor against Git history and every recorded historical-replay receipt against its anchored commit bytes; all checks pass.

Canonical Velvet Factory instance surfaces remain authoritative, explicit instance selection remains fail-closed, the canonical ChatGPT distribution remains 33 files with its canonical `.gitattributes` rule, and external-effect policy authority is unchanged. The receipt records `stage8d_complete=true` and `reform_v2_complete=true`. No runtime authority or business behavior is changed by final acceptance.
