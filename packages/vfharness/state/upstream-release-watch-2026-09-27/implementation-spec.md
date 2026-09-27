# Upstream / Toolchain Release Watch — implementation spec

## Goal
Create one VelvetOS-owned update-observation path that tracks both installed tools/packages and repository-only skill/agent/pattern upstreams, without adding a second scheduler or auto-upgrading production dependencies.

## Owner decisions
- Repository-only skills/agents must be tracked by their upstream repos even when they have no executable/package.
- OpenPost is frozen; its dedicated release watcher must be removed, not merely kept as a disabled watcher.
- Exact versions/commits may be recorded for rollback/reproduction, but normal execution must prefer current compatible versions and capability tests over exact-version locks.

## Non-goals
- No unattended upgrades.
- No new daemon/scheduler.
- No automatic vendor code import.
- No change to publication or customer-facing authority.

## Authority / SoT
- packages/velvetos/TOOL-STATUS.json
- packages/velvetos/UPSTREAM-WATCH.json
- existing Research Seat / Office Loop scheduler authority
- owner instruction in this task

## Acceptance criteria
1. OpenPost Release Watch is absent from active and retired Grok routine manifests/docs/sensors; OpenPost itself remains frozen and upgrade monitoring remains false.
2. A machine-readable upstream registry covers embedded/adapted skill/agent/pattern repos, tracked catalog sources, and managed executable/package upstreams.
3. A deterministic offline sensor validates registry coverage and rejects operational exact-version locks outside explicit recovery/reproducibility fields.
4. A networked on-demand checker can compare GitHub upstream heads/releases without modifying installs.
5. Research Seat owns recurring upstream checks; Office Loop consumes the report. No new scheduler entry is created.
6. HyperFrames runtime accepts newer compatible versions and records the actual version used; exact 0.8.34 becomes a recovery baseline only.

## Evidence
- RED before production edits: new sensor fails on current OpenPost retired watcher / exact HyperFrames runtime pin / missing upstream registry.
- GREEN: targeted sensors + check-tool-authority + check-hyperframes-backend + new upstream sensor pass.
- Full: python scripts/check-all.py.

## Risk / gates
Network checks are advisory evidence only. Upgrade application remains a separate reviewed change with smoke/compatibility proof.
