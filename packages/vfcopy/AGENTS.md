# vfcopy — local copywriting guide

Scope: human-visible copy, captions, customer/owner messages and text QA.

- Canonical gate: `constitution/VISIBLE_TEXT.md`.
- Load `SKILL.md`, `VOICE.md` and only the surface-specific writing tools needed for the routed request.
- Preserve literal source facts, IDs, URLs and quoted/verbatim material; do not “humanize” machine payloads or source text that must stay exact.
- AI-authored text is not final from skill existence alone. Use the actual surface gate and exact text/version evidence; unproven execution remains `UNPROVEN`.
- Public CTA, offering shape and commercial facts come from their canonical authorities, not memory.
- This guide provides text evidence only; it cannot authorize send, publish, spend or external mutation.

Verification: `python3 scripts/check-visible-text-gate.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; text evidence never authorizes send/publish/spend by itself.
