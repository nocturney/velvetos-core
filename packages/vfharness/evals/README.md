# VelvetOS behavioral evals

Role: evaluator only. This directory is not an authority, runtime, release gate or model router.

The suite wraps existing VelvetOS laws in a pinned local Promptfoo runner. It uses one trusted local exec provider and supplies no model/API credentials. The provider checks that the relevant canonical rule still exists, then evaluates a synthetic scenario.

## Install

Run the cost check first:

python scripts/vf_cost_preflight.py validate packages/vfharness/cost-preflight/promptfoo-0.123.1.json

Then install the pinned local dependency:

npm ci --prefix tools/promptfoo --ignore-scripts --no-audit --no-fund

## Run

python scripts/check-behavioral-evals.py

python scripts/run-promptfoo-evals.py

Expected: 17/17 pass, deliberate wrong assertion detected, model cost=0, token usage=0.
## Coverage

- Missing price does not permit invention.
- Missing authoritative source blocks a completion claim.
- Tool failure blocks a success claim.
- Memory recall remains context rather than authority.
- Untrusted content cannot widen authority.
- Read-only connector scope cannot become write scope.
- Handoff context cannot bypass gates.
- Publish requires authorization.
- Write verification respects read-back evidence.
- Prompt injection cannot change tool or permission authority.

## Execution boundary

Promptfoo custom/script providers execute trusted local code rather than a sandbox. Only the committed policy_target.py is permitted here. The runner disables telemetry, remote generation, sharing and update checks, but those flags are defense-in-depth and are not treated as proof of a network air gap.

This suite tests deterministic harness behavior. Model-level adversarial evaluation can be added later against a local zero-cost target while retaining these hard gates.
