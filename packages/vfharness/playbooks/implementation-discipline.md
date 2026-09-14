# Implementation discipline — Karpathy + Superpowers test-first embed

Source patterns: `multica-ai/andrej-karpathy-skills` + selected `obra/superpowers` v6.3 TDD guidance. Adapted into `vfharness`; no vendor runtime or duplicate skill pack.

Use before material code changes, especially refactors, cross-package changes, automation changes, and fixes that look deceptively small.

## Five rules

1. **Think before code.** State the requested outcome, the current source of truth, and the smallest credible change before editing.
2. **Prefer boring simplicity.** Reuse an existing pack, schema, handler, or sensor. Do not add an abstraction unless the present task demonstrably needs it.
3. **Make surgical changes.** Change only the files needed for the requested outcome. “While we are here” cleanup requires a separate reason and verification.
4. **Define proof before implementation.** Name the sensor, test, receipt, or observed behavior that will count as success. If proof cannot be named, the task is not ready to claim complete.
5. **Executable behavior is test-first when practical.** For code/bugfix/automation behavior, establish RED before production change, then GREEN, then REFACTOR while keeping proof green.

## Pre-edit card

```text
Outcome:
Source of truth:
Smallest change:
Files expected:
Behavior class: executable | structural | prose/data
Verification:
RED proof (if executable):
Expected RED reason:
GREEN proof:
Out of scope:
```

## RED → GREEN → REFACTOR

### RED

For executable behavior / bugfix / automation:

1. Write or select the smallest falsifiable test/reproduction/sensor.
2. Run it **before** the production change.
3. Confirm it fails for the expected reason, not because the test is broken or setup is missing.

A test is falsifiable only if you can name a realistic production change that would make it fail. Prefer assertions on real behavior over mocks/framework internals.

### GREEN

- Make the minimum production change that satisfies the named behavior.
- Run the same proof and confirm it passes.
- Run nearby regression proof / package sensor required by the task.

### REFACTOR

- Simplify only after GREEN.
- Keep the same behavior and proof green.
- If refactor changes observable behavior, return to RED with a new expectation.

## Bugfix rule

Reproduce the bug first whenever the behavior can be exercised deterministically. A fix without a pre-fix reproduction is allowed only when the environment/provider makes reproduction impossible; record the limitation and use the strongest available receipt instead.

## No test theater

Do **not** create ceremonial tests just to satisfy TDD language:

- Markdown, copy, static data/config or human prose may need schema/lint/diff/receipt, not a fake behavioral unit test.
- Grep/string-presence checks are acceptable for **wiring/structure**, but they are not sufficient proof of runtime behavior.
- A test that only asserts a mock was called or a string exists is not behavioral proof unless that is genuinely the contract.
- Existing required sensors/receipts remain authoritative even if a new unit test passes.

## Structural vs behavioral proof

| Change | Minimum proof |
|---|---|
| executable code/bugfix | observed RED → GREEN + regressions |
| automation/provider flow | deterministic local test where possible + provider/runtime receipt when claim is live |
| routing/wiring/docs | structural sensor/lint + diff/spec review |
| human-visible prose | `VISIBLE_TEXT` gate on the exact candidate; no fake unit test |

## Stop / re-plan conditions

Stop and re-plan when:

- the diff expands beyond the pre-edit card;
- a second runtime appears;
- a new pack is proposed for an existing domain;
- success starts relying on “looks right” instead of evidence;
- the supposed RED proof passes before the change (test does not demonstrate the missing behavior);
- the only available “test” is a counterfeit proxy that cannot falsify the claimed behavior.

A safe ruling from `executing-plans.md` may resolve local ambiguity, but it cannot declare a required test/sensor green or replace a runtime/provider receipt.
