# Preflight — Superpowers v6.3 harness delta

**Authority:** user-approved 2026-09-13 conversation + `AGENTS.md` / constitution.  
**Plan:** `task_plan.md` in this state directory.  
**Rule:** rows below are evidence; a prose-only “clean” statement is not.

| Check | Producer / Owner | Consumer / Dependent | Shared surface | Finding | Action |
|---|---|---|---|---|---|
| self-consistency | Task 1 safe ruling | Task 1 | `vf_graceful_escalation.py` ↔ behavioral sensor | API can stay backward-compatible by adding keyword-only `ruling_fn` / `safe_to_rule`; behavior is testable independently | continue |
| self-consistency | Task 2 execution semantics | Task 2 | `executing-plans.md`, `writing-plans.md`, `LOOP.md`, `EMBED.md`, `SKILL.md` | same semantics must replace binary-stop wording everywhere canonical | continue |
| self-consistency | Task 3 TDD + review | Task 3 | implementation + critique playbooks ↔ `SKILL.md` routing | executable behavior gets RED/GREEN; prose/config avoids test theater; ordinary material review stays lighter than high-risk dual review | continue |
| self-consistency | Task 4 provenance/verification | Task 4 | research note, AUTONOMY-TOOLS, sensors, CHANGELOG, CI | docs cannot be completion evidence; full suite/PR CI required | continue |
| producer→consumer | Task 1 | Task 2 | `SAFE_RULING`, `safe_to_rule`, ruling receipt shape | Task 2 documentation must use exact fail-closed code semantics, not invent a broader policy | continue |
| producer→consumer | Task 2 | Task 3 | execution routing / task lifecycle | implementation discipline and review must plug into task step + fan-in flow, not form a second workflow | continue |
| producer→consumer | Task 1 | Task 4 | behavioral checker output | provenance and claim language must distinguish behavioral proof from structural wiring | continue |
| shared file | Task 2 | Task 3 | `packages/vfharness/SKILL.md` | both modify routing; later edit must preserve preflight/ruling/fan-out text while adding RED/GREEN + fresh review | sequential; review integrated final file |
| shared interface | Task 2 | Task 4 | `scripts/check-skill-pattern-embeds.py` ↔ canonical playbook markers | structural checker may assert wiring only; it must not claim runtime behavior | continue with separate behavioral sensor |
| shared state | all tasks | final fan-in | `packages/vfharness/state/superpowers-v63-harness-2026-09-13/` | one task state directory, no parallel writer needed | sequential checkpoint updates |

## Stop-class scan

- No destructive/irreversible action required.
- No secrets/auth/permissions change.
- No publish/DM/payment/external business side effect.
- Branch/PR only; no merge to `main` in this execution without the repository's normal gate.
- Required sensors remain authoritative; a ruling cannot convert a failed sensor into PASS.

## Result

No stop-class conflict. Shared-file edits are intentionally sequential. Parallel dispatch is documented as a harness capability, but this implementation itself does not parallel-write shared vfharness files.