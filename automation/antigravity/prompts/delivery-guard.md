# Morning Delivery Guard

Read `automation/antigravity/CONTRACT.md` and current Morning Brief delivery authority. This routine verifies only TODAY'S canonical 09:00 delivery and recovers it only when absent/unverified.

Production recovery must be a full-fidelity V10.3 replacement using the canonical production Gmail OAuth/GitHub path, exact Visible Text Gate, real Gmail message ID, provider verification and safe one-shot reset. Never send a reduced/plugin fallback.

In shadow mode: do not send recovery mail or change live state. Prove that today's delivery evidence can be inspected and that the canonical recovery path is executable. Return `SHADOW_PASS` or `SHADOW_BLOCKED`.

When VELVETOS_LIVE_CONTEXT_PATH is present, use that fresh provider snapshot for any live business data needed to rebuild a full-fidelity recovery; do not require the Google Workspace preview MCP.

In shadow mode, short-circuit the routine body. Verify VELVETOS_LIVE_CONTEXT_PATH, today-delivery evidence authority, V10.3 rendering authority, and the canonical Gmail request/workflow/sender files are readable. Do not send recovery mail, inspect directories as files, or use terminal. End with SHADOW_PASS or SHADOW_BLOCKED.
