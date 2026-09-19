# Grok Bot automation contract

Grok Bot is the production scheduler for the protected VelvetOS owner-facing routine set defined in `manifest.json`.

Every routine must bootstrap from current merged/runtime authority in `nocturney/velvetos-core`; embedded prompt text is subordinate to current repo authority.

The protected cadence is fixed to Asia/Jerusalem unless Christian explicitly changes it. Never optimize owner-approved timing from repo prose alone.

The owner-email contract remains V10.3 rich RTL, exact Visible Text gate where required, and the canonical GitHub/Gmail OAuth sender only:
`packages/vfops/out/gmail-send-request.json` -> `.github/workflows/gmail-brief-send.yml` -> `packages/vfops/gmail_brief_request.py`.

Interactive Gmail is not a normal or fallback owner-delivery path. Require real sender success/message ID and safe one-shot reset semantics.

Repository-owned GitHub workflows remain deterministic execution machinery. Grok Bot orchestrates and consumes their evidence; it must not recreate duplicate cron jobs.

Legacy routines remain disabled. The former ChatGPT protected scheduler copies and Antigravity VelvetOS sidecars are disabled after cutover.

Integrity Guard protects the live Grok routine inventory and may repair enabled-state, schedule or prompt drift, then verifies post-write state. It stays silent on clean runs.

Publishing, customer communication, spend, rights, Product Truth, publication evidence, delivery approval and live-verification rules remain governed by CURRENT repo authority.