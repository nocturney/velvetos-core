# Integration plan v0

Status: **NON_NORMATIVE_REFORM_PREPARATION**  
Current runtime change: **none**

## Phase 0 — preparation (this branch)

Deliver contracts, schema, provider interface and acceptance vectors only. Do not edit canonical runtime/policy surfaces.

Exit:
- all draft files internally consistent;
- no new authority/store/daemon/scheduler;
- no production flag enabled.

## Phase 1 — manifest builder + verifier

After Reform v2 closes, implement a small `vfharness` helper that **reads** existing checkpoint/HANDOFF/state/evidence and builds the draft manifest in memory or as an evidence-only debug artifact.

No provider compaction yet.

Verifier must check:
1. required checkpoint fields;
2. every resume-critical ref resolves or is explicit UNAVAILABLE/UNPROVEN;
3. open gate/blocker parity;
4. exact path/ID parity;
5. authorization refs are refs only;
6. summary cannot upgrade UNKNOWN/BLOCKED/UNPROVEN.

## Phase 2 — shadow compaction

Run provider compaction in shadow mode after eligible boundaries, but do not feed its output back into the active agent.

Compare:
- compacted manifest vs source manifest;
- next-step parity;
- blocker parity;
- exact-ref preservation;
- contradiction count;
- size/headroom change.

Any drift produces evidence only; it does not alter execution.

## Phase 3 — controlled dev continuation

Allow compacted context to drive only fixture/dev tasks with no external side effects. Recovery path must be proven by fault injection:
- provider timeout;
- malformed compacted result;
- missing ID;
- stale evidence;
- contradictory summary;
- verifier crash.

## Phase 4 — bounded production

Enable only at safe phase boundaries first. Keep mid-execution compaction disabled. Require:
- feature flag;
- kill switch;
- receipt/telemetry;
- deterministic recovery to checkpoint + canonical refs;
- zero authority semantics change.

## Phase 5 — pressure-triggered production

Only after phase-boundary parity is proven, allow context-pressure triggers. Provider-specific token/headroom thresholds are selected here, not in prep.

## Phase 6 — cleanup

Remove temporary shadow/debug glue after coverage proof. Do not remove checkpoint, HANDOFF or canonical state surfaces.

## Suggested future feature flags

```text
contextContinuity.enabled=false
contextContinuity.mode=off|shadow|controlled|active
contextContinuity.provider=native|fallback|none
contextContinuity.pressureTrigger=false
contextContinuity.phaseBoundaryTrigger=true
contextContinuity.killSwitch=true
```

Names are illustrative until the post-Reform config surface is selected.

## Required receipts/metrics

Evidence only:
- trigger reason;
- before/after provider measurement kind and headroom;
- source manifest digest;
- preserved ref count;
- missing ref count;
- contradictions;
- verifier result;
- provider/fallback used;
- recovery used;
- resume parity result.

Do not create a second Work Ledger to hold these. Use the retention/evidence architecture selected after Reform v2.
