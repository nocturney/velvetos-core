# Implementation discipline — Karpathy-pattern embed

Source pattern: `multica-ai/andrej-karpathy-skills`. Adapted into `vfharness`; no vendor runtime or duplicate skill pack.

Use before material code changes, especially refactors, cross-package changes, and fixes that look deceptively small.

## Four rules

1. **Think before code.** State the requested outcome, the current source of truth, and the smallest credible change before editing.
2. **Prefer boring simplicity.** Reuse an existing pack, schema, handler, or sensor. Do not add an abstraction unless the present task demonstrably needs it.
3. **Make surgical changes.** Change only the files needed for the requested outcome. “While we are here” cleanup requires a separate reason and verification.
4. **Define proof before implementation.** Name the sensor, test, receipt, or observed behavior that will count as success. If proof cannot be named, the task is not ready to claim complete.

## Pre-edit card

```text
Outcome:
Source of truth:
Smallest change:
Files expected:
Verification:
Out of scope:
```

## Stop conditions

Stop and re-plan when the diff expands beyond the pre-edit card, a second runtime appears, a new pack is proposed for an existing domain, or success starts relying on “looks right” instead of evidence.
