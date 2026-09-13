# Human-step wizard — bounded owner action, not task offload

Pattern source: [mattpocock/skills `wizard`](https://github.com/mattpocock/skills).

Use only when an otherwise executable task reaches a step that **cannot be completed by the active agent/tooling** and genuinely requires a person: login/consent, hardware permission, provider console click, physical device action, payment/legal approval, or another non-delegable gate.

The wizard exists to minimize owner work. It does **not** convert an implementation task into “here are instructions, do it yourself”.

## Before invoking the owner

1. Attempt every allowed autonomous path and documented failover first.
2. Verify the blocker is real and current (`needsAuth`, permission error, provider UI requirement, physical action, etc.).
3. Complete everything that can be completed **before** the human step.
4. Prepare the post-step command/check so work can resume immediately.
5. Never ask the owner to repeat information or actions already captured in current state/receipts.

## Wizard packet

Present only the minimum required action:

```text
Why this is needed:
Where to do it:
Exact action:
What success looks like:
Do NOT change:
Afterwards:
```

### Requirements

- **One gate at a time.** Do not dump a 15-step setup manual if only step 4 currently blocks progress.
- Prefer exact UI label / command / device name when known.
- State what the owner must *not* touch when accidental changes are risky.
- Never ask the owner to copy secrets into chat or commit them to Git.
- If the human step has security/financial/publish consequences, name that explicitly.
- If the user already performed the step and there is a receipt/state update, do not ask again.

## After the human step

The agent owns the continuation:

1. verify the expected receipt/state;
2. resume from the existing checkpoint;
3. complete remaining implementation/tests;
4. update runtime truth (`configured` / `verified` / `blocked`) honestly;
5. close the wizard gate in the checkpoint.

Do not require the owner to translate the result back into technical language; inspect the provider/state directly when tooling allows it.

## Good examples

- macOS asks for Accessibility permission for the worker: give the exact Settings path and app toggle, then re-run the worker doctor yourself.
- OAuth consent is required: provide the exact provider connection action, then verify the connector after consent.
- VoiceStudio first-run requires `Start installation`: ask for that single click, then re-run the existing bootstrap/doctor automatically.

## Bad examples

- “Clone the repo, edit these five files, run tests and open a PR.” → that is implementation offload, not a human-only gate.
- Asking for a token in chat when the provider has a secure connection flow.
- Repeating setup steps the state already marks as complete.
- Asking the owner to diagnose an error that the agent can inspect with logs/sensors.

## State

For long tasks, record the gate in the existing checkpoint using `gate` / `owner_blocked` with:

- reason;
- exact human action;
- expected evidence;
- resume command/check;
- status: `open | satisfied | superseded`.

Do not create a separate approval database.

## Related

- `degraded-mode.md`
- `engineering-delivery-chain.md`
- `verification-before-claim.md`
- `packages/vfharness/templates/escalation.md`
