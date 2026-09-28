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

Stage 2A narrows registry metadata without reducing CI coverage. The full suite still runs exactly as before.

- The live registry contains 112 runnable root sensors.
- All 112 runnable root sensors now have explicit ownership/trigger mappings. Any selector uncertainty still fails broad through the Stage 2B fallback rules rather than through unmapped wildcard rows.
- The critical always-on set is deliberately small: `check-agent-surface-security`, `check-critical-syntax`, `check-machine-writers`, and `check-policy-architecture`.
- `check-critical-syntax` is a read-only tracked-Python syntax gate; it parses sources without importing or executing them.
- `reports/stage2-sensor-registry-audit.json` is generated by `scripts/generate-sensor-registry-audit.py` and records mapping coverage, nested sensor execution, and direct workflow duplicates.
- The audit currently records one nested instance bootstrap check and two potential duplicate runs in `.github/workflows/check-all.yml`; removal is explicitly deferred to Stage 3.
- Stage 2B may compute affected sensors in shadow mode only. Unknown or unmapped changes must expand to the full suite, never narrow by guess.

## Stage 2B — affected selector in shadow

The affected selector is intentionally non-authoritative in Stage 2B. `scripts/check-all.py` remains the merge authority.

- `sensor-selection.json` fixes shadow mode, fail-broad behavior, and the exit criteria before observation begins.
- Unknown paths, sensor-registry/schema changes, evaluator-core changes, CI harness changes, and selector changes expand to `FULL_SUITE`.
- `triggered_by` is reserved for domain/contract surfaces; `depends_on` records technical implementation dependencies. The selector matches both without conflating their meaning.
- Current registry evidence contains 47 technical dependency edges across 26 sensors.
- A current `packages/vfcopy/VOICE.md` replay selects 14/112 sensors. The pinned Stage 2B opening baseline records the historical 14/95 post-refinement result versus 67/95 before refinement.
- Pull requests record the shadow selection and comparison in the GitHub job summary and emit machine-readable log markers. The authoritative full-suite result is compared against the would-select set to detect misses without duplicating CI work.
- Opening evidence is pinned in `reports/stage2-shadow-observation-baseline.json`: PR #398, its shadow/full comparison, the successful post-merge main run, and deterministic replay samples. It is a fixed baseline, not a live counter.
- `scripts/collect-sensor-shadow-observations.py` is the read-only live counter: it queries GitHub Actions through authenticated `gh`, counts each pull request once for volume while retaining every eligible run as historical evidence, extracts the machine-readable selector/comparison markers, and evaluates the fixed exit criteria. A later clean rerun cannot erase an earlier miss. Reviewed miss classifications are pinned in `reports/stage2-shadow-miss-classifications.json`. It never changes GitHub state or CI enforcement.
- Exit criteria are fixed at at least 20 observed pull requests and 7 observation days, zero critical misses, classification of every noncritical miss, mapping repair for every relevant miss, deterministic replay, and a tested `FULL_SUITE_REQUIRED` rollback.
- Stage 2B does not change branch protection, remove duplicate checks, or activate affected-only enforcement.

## Stage 3 — preactivation prepared, not active

Stage 3 is prepared in the repository without changing current CI behavior. The selector remains `shadow`, the pull-request workflow still runs the full suite, the repository ruleset remains disabled, and the two Stage 2A duplicate direct sensor invocations remain in place until the Stage 2 exit gate passes.

- `scripts/check-all.py` now supports an exact `--selection` input while preserving full-suite execution as the default. A real 14-sensor selected-suite replay passes, but no workflow calls this mode yet.
- `sensor-selection.json.stage3_preparation` records the target contract: selected-suite PR CI, full-suite main pushes, preserved critical always-on sensors, fail-broad unknown/broad changes, required `check-all`, ruleset activation target, duplicate removals, and `FULL_SUITE_REQUIRED` rollback.
- `scripts/stage3_preflight.py` is read-only. It recomputes the fixed Stage 2 exit gate from an observation report and can emit `reports/stage3-activation-receipt.json` only when every criterion is satisfied.
- `reports/stage3-preactivation-plan.json` pins the non-active cutover transaction and the current disabled ruleset snapshot. It explicitly forbids workflow/ruleset mutation or duplicate removal before the gate passes.
- `scripts/check-policy-architecture.py` fail-closes accidental early activation: while the selector is in shadow, an activation receipt or a workflow `--selection` invocation is an error. Enforced mode is accepted only with a PASS activation receipt and the expected Stage 3 workflow shape.
