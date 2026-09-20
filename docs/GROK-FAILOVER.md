# Grok Bot failover

**Date:** 2026-09-20  
**Owner intent:** HQ remains the primary publisher; Grok Bot is an emergency
delivery executor, never a separate approval authority.

For full management failover see [`docs/FAILOVER.md`](FAILOVER.md).

## Instagram delivery failover

Grok Bot may preserve a scheduled Instagram delivery window when OpenPost is
failed, missed, or cannot be repaired quickly. It must use the canonical
VelvetOS failover runner described in
[`packages/vfigos/failover/README.md`](../packages/vfigos/failover/README.md).

The Grok path is not a second unrestricted Instagram credential:

- the exact package must already pass Instagram PREFLIGHT;
- a duplicate/live-media check happens before any fresh approval;
- the same signed delivery-approval gate applies;
- the Instagram MCP bearer remains on `openpost-prod`;
- `publish_image` still waits for Meta container `FINISHED`;
- the resulting media id is verified live with `get_media`;
- ambiguous media-publish timeout/network outcomes require reconciliation and
  are never blindly retried.

Grok Bot's local shell is the execution transport. It does not need a Meta token
or Team Bot Secret.

## Other Grok outage behavior

If Grok Bot itself is unavailable or out of quota:

1. generate outputs on the existing packs;
2. send from HQ through canonical tools — Gmail send/reply and Instagram per
   `packages/vfigos/SEND.md`;
3. use Drive for office documents as needed;
4. ChatGPT + Gemini + Perplexity remain the backup research/orchestration set;
5. no boost, no auto-DM, no invented "published" state;
6. customer conversation remains human-routed.

Related: [`packages/vfharness/playbooks/grok-failover.md`](../packages/vfharness/playbooks/grok-failover.md) ·
[`constitution/SEND.md`](../constitution/SEND.md).
