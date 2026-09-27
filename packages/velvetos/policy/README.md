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
