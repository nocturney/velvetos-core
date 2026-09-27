# Tickets

## T1 — Remove OpenPost watcher
Outcome: remove the OpenPost Release Watch from repository scheduler authority while preserving OpenPost frozen state.
Depends on: none.
Area/files: automation/grok, vfops routine docs, tool-authority sensor.
Verify: check-tool-authority.py + search for active/retired watcher references.
Done when: no executable/scheduled watcher authority remains.

## T2 — Upstream registry + checker
Outcome: add one machine-readable registry and a read-only checker for repo/package upstreams.
Depends on: T1.
Area/files: packages/velvetos/UPSTREAM-WATCH.json, scripts/vf_upstream_watch.py, check-upstream-watch.py.
Verify: RED then GREEN sensor; on-demand network check is read-only.
Done when: embedded skill/agent/pattern repos are covered and OpenPost is excluded.

## T3 — Version policy / HyperFrames
Outcome: replace exact operational HyperFrames lock with latest-compatible/capability policy; retain exact baseline only for recovery.
Depends on: T2.
Area/files: vf_hyperframes.py, host bootstraps, hyperframes sensor.
Verify: newer simulated version accepted; older minimum rejected; actual version written to receipt.
Done when: normal work is not blocked by !=0.8.34.

## T4 — Existing scheduler integration
Outcome: Research Seat performs upstream observation; Office Loop consumes its artifact; no new scheduler.
Depends on: T2.
Area/files: vfresearch / vfops docs + Grok routine responsibility text if needed.
Verify: structural sensors + full check-all.
Done when: cadence ownership is explicit and no extra routine is added.
