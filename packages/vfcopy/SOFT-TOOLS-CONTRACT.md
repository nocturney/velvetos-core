# Soft Tools Contract — public copy must pass the full chain

This is the canonical invariant for every public-facing Hebrew content artifact produced by VelvetOS, regardless of which agent/tool starts the work.

## Mandatory chain

Every caption, Reel copy, Story copy, carousel copy, cover text, first-frame text, overlay, public bio/profile copy, or other customer-facing Hebrew text MUST pass this chain before it can be marked `quality_checked`, `ready_for_publish`, `authorized_for_tool_publish`, or equivalent:

1. **Verified context / claim provenance** — real source only; unknown fact stays unknown.
2. **Reader-first** — `hq/reader-first-he.md` before drafting. Record intended reader state / useful point / real story or proof.
3. **Voice** — `VOICE.md` + `VOICE-CHART.md` + examples from `voice/approved/` only.
4. **Type template / writing aid** — relevant `hq/templates/*`; optional `vfmskill` copywriting/copy-editing aids may strengthen the draft but never replace this contract.
5. **velvet-hebrew-copy** — `skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
6. **Humanizer / AI-tells** — `hq/ai-tells-he.md`.
7. **Executable lint on the ACTUAL final copy** — `python3 scripts/check-vfcopy.py lint` with the real text and verified context. A test of the lint implementation is not evidence that a candidate passed.
8. **Factual gate** — no invented price, turnaround, print duration, customer/testimonial, shipping, Insights, SKU or other unsupported claim. `needs_input` blocks progression.
9. **Visual-text decision** — for cover/first-frame/overlay, compare against `NO_TEXT`; text must add value, not decorate or restate the image.
10. **CONTENT-RUBRIC** — `packages/vfgrowth/CONTENT-RUBRIC.md`, >=20/25 and no red-flag condition.
11. **Written PREFLIGHT** — exact final text + exact visual/version digest. Any material copy change invalidates prior lint/rubric/preflight evidence.
12. **Publish policy + rights/privacy** — only then may the artifact advance to the existing publish authorization path.

## Fail-closed rules

- `VOICE.md` alone is not a copy-quality pass.
- A Brand Guardian pass does not replace copy lint.
- A successful CI/eval of `check-vfcopy.py` does not prove a specific caption passed; the final candidate itself must be linted.
- Text created by ChatGPT, Cursor, Gemini, Perplexity, Canva, Grok, scripts, templates, or a human is treated identically. Origin grants no exemption.
- Copy written outside `packages/vfcopy` is raw input until it has passed this chain.
- Any rewrite after lint requires lint again. Any material rewrite after rubric/preflight requires those gates again too.
- Missing proof produces `needs_input`, `waiting_for_media`, `blocked_policy`, or another truthful blocked state — never an invented completion claim.

## Required evidence on a content job

The job/manifest/preflight must retain enough evidence to prove the chain ran on the current version:

- `reader_first`: short recorded intent/reader state
- `voice_mode`
- `copy_version` or digest
- `vfcopy_lint`: `pass` with version/digest; or blocking status
- `fact_gate`: `pass` or `needs_input`
- `visual_copy_decision`: `TEXT_WINS` with reason or `NO_TEXT` when applicable
- `content_rubric`: score + result
- `preflight`: artifact path + digest

Exact storage shape may differ by existing manifest/schema; do not create a parallel database solely for this evidence.

## Scope

Mandatory for all public Hebrew copy. Internal logs, raw research notes, code comments and private operator notes are outside this contract unless they are promoted into public-facing copy.
