# Office v2 Phase 0 — execution preflight

Canonical project preflight: PASS (system_engineering, FULL) before worktree creation.

| Check | Producer / Owner | Consumer / Dependent | Shared surface | Finding | Action |
|---|---|---|---|---|---|
| P0-A self consistency | live providers + Git | capability manifest | observed state | current observations available; mutations intentionally not run | continue |
| P0-B self consistency | Reform v2 policy/state model | Office v2 contracts | policy/state semantics | must extend/reference; must not create parallel authority | continue |
| P0-B ↔ P0-C | Project State schema | continuity tool | project-state manifest | producer/consumer contract is explicit | continue |
| P0-B ↔ P0-D | Correlation + migration schema | migration report | migration ledger | shared IDs/schema | continue |
| P0-B ↔ P0-E | Node/Evidence/Artifact contracts | admission/trust policy | restore/trust metadata | shared trust/provenance vocabulary | continue |
| P0-A ↔ P0-F | baseline logs | regression comparison | sensor outputs | baseline captured off-repo | continue |
| P0-C ↔ P0-F | verifier proof | completion claim | continuity receipt | positive + negative controls required | continue |
| P0-D ↔ P0-F | migration report | review | read-only projection | no writer path allowed | continue |

Ruling: the seven Office v2 state classes are a storage/lifecycle axis mapped onto the existing four Reform v2 semantic categories, not a replacement state authority. This avoids a parallel state model while satisfying START HERE.

Ruling: Drive/orders mutation smoke remains BLOCKED until a canonical effect-authority mapping exists; creating a local Office v2 permission would violate the single-authority gate.

## Pre-edit card
- Outcome: Phase-0 contracts + continuity proof + read-only migration evidence.
- Source of truth: START HERE + current origin/main + live provider/runtime readback.
- Smallest change: versioned definitions and two bounded read-only/local scripts; no daemon/store/writer.
- Behavior class: executable + structural.
- Verification: RED targeted sensor → GREEN, positive/negative continuity drill, existing repository checks.
- RED proof: sensor must fail while required Phase-0 files/scripts are absent.
- GREEN proof: sensor passes and negative continuity drift fails closed.
- Out of scope: Phase 1 prerequisites/installations and any production cutover.
