# vfops — office operations local guide

Scope: office status, owner brief, canonical operational state, followups and internal coordination.

- Canonical office truth comes from `office/control-plane.json` and the source named by the relevant operation.
- Use `SKILL.md`, `ROUTINE.md` and `LOOP.json` only when the request needs them.
- Routine Gmail delivery follows `policy_id: gmail.send`; transport readiness is evidence, not authorization.
- Sync/write failures must remain explicit and unsynced; never claim a Sheet/Drive/provider mutation without receipt/readback.
- Office routing is not business policy authority and does not create new prices, deadlines, approvals or customer facts.
- Instance-specific operating facts belong to the Instance/owned SoT, not Core root.

Verification: `python3 scripts/check-vfops-loop.py`, `python3 scripts/check-office-control-plane.py`.
