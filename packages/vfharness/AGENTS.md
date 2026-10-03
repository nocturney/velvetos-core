# vfharness — local agent guide

PROJECT: VelvetOS harness discipline
TEST: `python3 scripts/check-vfharness.py`
LINT: `python3 scripts/check-all.py`

This guide applies only to `packages/vfharness/**`. Root `AGENTS.md` owns Core-wide identity and boundaries; this file owns harness-specific execution discipline.

## RULES

- Canonical execution loop: `LOOP.md`. This guide may route to it but must not restate or override its retry/ruling/checkpoint algorithm. Do not install or create a second agent runtime.
- Harness state is task state, never policy authority. A checkpoint, plan, skillstate or worker self-report cannot mint `ALLOW`, waive a receipt, or authorize send/publish/spend/delete/permission mutation.
- `SKILLSTATE` / `skillstate` semantics live in `playbooks/skillstate.md`; checkpoints remain under `state/`.
- Missing sale price stays `X ₪`; harness work never invents money, provider state, Insights or receipts.
- `send_message` and other external effects follow the canonical destination policy and receipt contract; the harness only routes/executes after policy allows.
- Office-manager failover: `docs/FAILOVER.md`. Grok Bot quota failover: `playbooks/grok-failover.md` + `docs/GROK-FAILOVER.md`. Urgent publication continuity uses `packages/vfigos/LIVE-PACKET.md`; failover never becomes a new authority.
- Retry with an approach change, not identical tool-call thrash. Preserve the existing capped retry/escalation rules in `LOOP.md` and `layers.json`.
- Run `python3 scripts/check-all.py` after harness/catalog/rule changes. Sensor inventory is `packages/velvetos/policy/sensor-registry.json`, not this guide.

## ANTI-PATTERNS

- Second orchestrator/runtime instead of extending vfharness.
- Closing from worker self-report without required evidence.
- Loading every specialist/skill “just in case”.
- Treating failover, checkpoint or memory as owner approval.
- Replaying the whole conversation when guide + checkpoint + latest observation are sufficient.
Policy routing reference: `policy_id: project.request.preflight` is router-only; harness plans/checkpoints cannot authorize an external effect.
