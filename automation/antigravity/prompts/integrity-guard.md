# Automation Integrity Guard

Read `automation/antigravity/CONTRACT.md` and `automation/antigravity/manifest.json`.

Inspect the live Antigravity sidecar inventory and current scheduler state. Verify every protected routine is enabled, has the exact manifest cron, and is bound to the intended repository/runtime. Check prompt/authority drift against current merged VelvetOS authority.

In shadow mode: report drift only; do not repair or notify. Return `SHADOW_PASS` when clean, otherwise `SHADOW_BLOCKED` plus exact drift and the safe repair that would be applied after cutover.

After cutover: repair only protected Antigravity routines, verify post-write state, never bulk-disable, and remain silent on a clean run.
