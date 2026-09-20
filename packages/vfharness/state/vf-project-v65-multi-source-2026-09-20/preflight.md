# Preflight — VF Project 6.5 multi-source composition

| Check | Producer / owner | Consumer | Shared surface | Finding | Action |
|---|---|---|---|---|---|
| Task 1 self-consistency | Task 1 | Task 1 | Project bundle identity/hashes | 6.5 must bind exact authority/instructions/reference hashes | create bundle first |
| Task 1 -> Task 2 | Task 1 | Task 2 | manifest paths + SHA constants | executable validators depend on exact 6.5 manifest bytes | update constants after bundle identity is fixed |
| Task 2 self-consistency | Task 2 | Task 2 | preflight/evidence/tests | current validators hardcode 6.4 and exactly three aesthetic refs | update to 6.5/four refs and dynamic error text |
| Task 2 -> Task 3 | Task 2 | Task 3 | visual enforcement + authority manifest | policy JSON is consumed by validators | keep one canonical policy, no parallel config |
| Task 3 self-consistency | Task 3 | Task 3 | visual/publication authority | owner correction extends, does not replace, current Product Truth rules | add scoped source-set/provenance/layout delta only |
| Task 4 self-consistency | Task 4 | Task 4 | branch/CI/search | completion requires proof on branch/main, not conversation memory | inspect checks and stale-reference search before merge |
