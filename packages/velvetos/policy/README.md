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
- `workflow_dispatch` on the Core Sensors workflow is reserved as the exact-SHA precheck surface for protected machine writers. It resolves live `origin/main` as base, evaluates the staging SHA with the same affected selector, and only after success publishes a legacy commit-status context `check-all` on that exact SHA. This status bridge exists because GitHub rulesets do not accept the non-main `workflow_dispatch` check-run itself as the required status for a direct default-branch push.
- Default-branch machine writers must call `scripts/push-main-with-check-all.sh`: rebase onto current `main`, push a temporary `machine-check/*` ref, dispatch/wait for successful `check-all` on the exact SHA, verify both the GitHub Actions check-run and the `check-all` commit status, then push that same SHA to `main`. A concurrent `main` advance invalidates the evidence and causes a bounded rebase/recheck retry; no force push or ruleset bypass is used. The publish-bridge writer remains isolated on its literal `publish-bridge` branch.
- `scripts/check-machine-writers.py` enforces this path plus explicit `contents: write` / `actions: write` permissions for default-branch writers.
- `.github/workflows/check-all.yml` no longer performs the Stage 2 shadow comparison or the two duplicate direct invocations (`check-policy-architecture.py`, `check-commission-isolation.py`). Those checks remain sensors and are selected through the registry when relevant.
- `sensor-selection.json.stage3_preparation` is `ACTIVE`, preserves the `FULL_SUITE_REQUIRED` rollback, and records the owner duration exception as auditable activation metadata.
- `scripts/check-policy-architecture.py` validates the active workflow shape and activation receipt; the duration exception cannot mask critical misses, incomplete/unresolved evidence, unclassified relevant misses, incomplete history, or deterministic replay failure.
- `reports/stage3-preactivation-plan.json` remains the historical preactivation transaction/snapshot; the activation receipt is the cutover evidence.
