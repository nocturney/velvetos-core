# Morning Delivery Guard

Read `automation/antigravity/CONTRACT.md` and current Morning Brief delivery authority. This routine verifies only TODAY'S canonical 09:00 delivery and recovers it only when absent/unverified.

Production recovery must be a full-fidelity V10.3 replacement using the canonical production Gmail OAuth/GitHub path, exact Visible Text Gate, real Gmail message ID, provider verification and safe one-shot reset. Never send a reduced/plugin fallback.

In shadow mode: do not send recovery mail or change live state. Prove that today's delivery evidence can be inspected and that the canonical recovery path is executable. Return `SHADOW_PASS` or `SHADOW_BLOCKED`.
