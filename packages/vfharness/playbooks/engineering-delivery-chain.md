# Engineering delivery chain — decision → shipped proof

Pattern source: [mattpocock/skills](https://github.com/mattpocock/skills) `to-spec` → `to-tickets` → `implement` → `code-review`.

Adapted into the existing `vfharness`. This is **not** a second issue tracker, agent runtime, handoff system, or source of truth.

## Purpose

Close the gap between “we discussed/approved this” and “the change exists, was reviewed, and is proven”. Use for material code, automation, policy, integration, or multi-file changes. A one-line typo, read-only spike, or purely explanatory answer does not need the full chain.

## Canonical chain

### 1. Decision → implementation spec

Recover what is already settled from the conversation, checkpoint, ADR, issue, and canonical files. **Do not re-interview the owner for decisions that are already known.**

For a material change, write `packages/vfharness/state/<task-id>/implementation-spec.md` (or use the existing `task_plan.md` for a small bounded change) with:

- **Goal** — observable outcome, one paragraph.
- **Non-goals** — what this change intentionally does not build.
- **Authority / SoT** — which existing files, provider state, or owner decision wins.
- **Acceptance criteria** — externally testable behavior, not implementation wishes.
- **Evidence** — sensor/test/receipt required for each criterion.
- **Risk / gates** — human, provider, security, finance, publish, or runtime gates.
- **Open questions** — only unresolved decisions that materially block implementation.

If the spec contradicts an existing authority, resolve the contradiction before implementation; do not silently fork policy.

### 2. Spec → dependency-aware tickets

Split the accepted spec into **vertical slices** that can be implemented and verified independently.

Each ticket must contain:

```text
Outcome:
Depends on:
Area/files:
Acceptance criteria:
Verify:
Done when:
```

Use GitHub Issues when an issue tracker is part of the current workflow. Otherwise keep `tickets.md` beside the task checkpoint. The tracker is a projection of the spec, not a second source of truth.

Prefer slices such as “ingest → validate → persist → prove” over layer tickets such as “backend”, “frontend”, “docs”. A ticket is small enough when a reviewer can accept/reject it without having to accept its neighbours.

### 3. Tickets → implementation

- Branch from the current target branch; direct-to-`main` is not the default.
- Read the relevant skill/playbook first.
- Execute **one ticket at a time** through `executing-plans.md`.
- Run the ticket’s targeted proof immediately after the change.
- Keep the diff surgical; do not opportunistically redesign adjacent systems.
- A failed proof routes to `systematic-debugging.md`, not to speculative edits.
- A step only a person can perform routes to `human-step-wizard.md` instead of offloading the whole task.

### 4. Implementation → independent review

Review against **two separate questions**:

1. **Code/change quality:** correctness, regression risk, safety/authority, maintainability, operator clarity.
2. **Spec compliance:** does every acceptance criterion have implementation **and evidence**?

Review the branch/PR against the target **merge-base/base SHA**, not only the working tree. Uncommitted/unstaged state is never the whole review surface.

For broad/high-risk changes, use `critique-review.md`. Missing acceptance evidence is `UNPROVEN`, not “close enough”.

### 5. Review → PR / CI

The PR body should map:

```text
Acceptance criterion → changed path → proof / receipt
```

Before completion:

- required targeted checks pass;
- `python3 scripts/check-all.py` passes when repository contracts changed;
- required CI is green;
- README/changelog contracts are satisfied when applicable;
- high-risk review/human gates are satisfied;
- unresolved blockers are explicit.

A PR existing is not proof of completion. A merge is not proof that an external provider/runtime is live.

### 6. Merge → runtime truth

When the claim is “deployed”, “active”, “connected”, “published”, or “running on worker/automation”, run the relevant provider/runtime proof. For VelvetOS-wide activation claims use `python3 scripts/check-runtime-doctor.py --strict` when applicable.

Keep states distinct:

`implemented` ≠ `merged` ≠ `deployed` ≠ `provider_verified`.

### 7. Close the loop

After verified completion:

- mark tickets complete;
- update checkpoint / canonical operational state;
- write changelog/README evidence required by the repo;
- promote only durable, generalized learning to `vfmem`/owner-memory;
- do not preserve private chain-of-thought or duplicate the entire conversation.

## Anti-patterns

- Treating a conversation decision as if code was changed.
- Turning every idea into a new pack/runtime/tracker.
- Re-asking the owner questions already answered by existing context.
- Tickets split by technical layer instead of verifiable outcome.
- Author self-review that checks style but never checks spec compliance.
- Reviewing only dirty/uncommitted files and missing committed branch changes.
- “CI green” used as proof of provider/runtime activation.
- Direct `main` edits for material work when a reviewable branch is available.

## Related

- `brainstorm-gate.md` — unresolved design decisions.
- `writing-plans.md` — detailed file/step plan after the spec.
- `executing-plans.md` — one verified task at a time.
- `critique-review.md` — independent/high-risk review.
- `verification-before-claim.md` — evidence before completion language.
- `human-step-wizard.md` — bounded human-only action.
- `vfmem/HANDOFF.md` — context transfer only; never replaces the spec/authority.
