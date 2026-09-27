# VelvetOS local observability

Role: **debug/evidence only**. This is not a Source of Truth, authorization layer,
Control Plane, queue, model gateway or release authority.

The implementation uses OpenTelemetry SDK 1.45.0 with OpenInference
instrumentation 0.1.66 and semantic conventions 0.1.39. All selected components
are FREE_LOCAL under Apache-2.0 and export only to an in-memory collector that is
materialized as a sanitized repo receipt.

## Install

Validate both cost preflights first:

- `packages/vfharness/cost-preflight/opentelemetry-python-sdk-1.45.0.json`
- `packages/vfharness/cost-preflight/openinference-instrumentation-0.1.66.json`

Then install the pinned local dependencies:

`python -m pip install --target tools/observability/python --requirement tools/observability/requirements.txt --disable-pip-version-check --no-input`

No collector, SaaS, account, API key or remote exporter is used.

## Acceptance flow

`python scripts/run-observability-acceptance.py`

The acceptance run exercises actual local VelvetOS components:

request → Project Request Gate routing → vfmem retrieval → local policy evaluator
→ zero-cost preflight tool → approval result → behavioral sensor execution
→ config read-back → result.

The committed receipt is
`packages/vfharness/state/observability-phase2-2026-09-27.json`.

It contains only allowlisted metadata. It does not store prompts, file bodies,
retrieved chunks, tool stdout/stderr, customer data, credentials or secrets.

## Verification

`python scripts/check-observability.py`

`python scripts/check-observability.py --strict`

Default verification is repository-portable and validates the committed acceptance
receipt. Strict mode also verifies the local installed distribution pins.
