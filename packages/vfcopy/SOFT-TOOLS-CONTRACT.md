# Soft Tools Contract — human-visible AI text must pass the relevant chain

Canonical authority: `constitution/VISIBLE_TEXT.md`.

This contract is the `vfcopy` implementation invariant for **every prose or microcopy artifact created/rephrased by AI and intended for a human reader** — public, customer-facing, or owner-facing. It is channel-aware: the relevant tools depend on the surface; public Instagram rules are not forced onto private customer or owner text.

## Universal baseline

Before AI-authored human-visible text can be marked `final`, `ready`, `quality_checked`, `ready_for_publish`, `authorized_for_tool_publish`, `ready_to_send`, or equivalent:

1. **Verified context / provenance** — real source only; unknown fact stays unknown. Literal source values remain literal.
2. **Reader-first** — `hq/reader-first-he.md` before drafting: who reads, at what moment, what they need, and the simplest way to say it.
3. **Surface route** — choose `public-social`, `visual-microcopy`, `customer-message`, `sales-proposal`, `owner-brief`, `human-document`, `ui-microcopy`, or `desk`.
4. **Relevant domain tools** — apply the packs that own truth/intent for that surface; do not use irrelevant tools just to satisfy a checklist.
5. **velvet-hebrew-copy** — `.cursor/skills/vf-hebrew-copy/SKILL.md` → `skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
6. **Humanizer / AI-tells** — `hq/ai-tells-he.md`.
7. **Executable lint on the ACTUAL final text** — use `scripts/vf_visible_text.py` with the correct `--surface`; public-social may also use `python3 scripts/check-vfcopy.py lint`. A CI test of the linter is not evidence that a candidate passed.
8. **Factual/constraint gate** — price, turnaround, customer, shipping, status, Insights, license/privacy and other claims only from the relevant verified source.
9. **Surface-specific QA** — visual, sales, public, owner, document or UI requirements below.
10. **Evidence tied to the exact text/version** — where an existing manifest/preflight/artifact has a digest, the text gate is bound to that digest. Material rewrite invalidates it.

## Relevant-tool matrix

| Surface | Extra tools/authorities that are relevant |
|---|---|
| `public-social` | `VOICE.md` + `VOICE-CHART.md` + `PUBLIC_CTA.md`; `vfmskill` copywriting/copy-editing/marketing-psychology when promotional; vfgrowth rubric/preflight |
| `visual-microcopy` | public voice when public + Creative Director + Brand Guardian + 3–5 candidates + `NO_TEXT` baseline |
| `customer-message` | actual thread/card + `vfconvert`; add `vfsales`, `vfcost`, `vlicense` only when the message needs them; private CTA/channel from the real conversation |
| `sales-proposal` | `vfsales` + `vfconvert` + `vfcost`/price approval; `vfmskill` copywriting/copy-editing when persuasive/long-form; `vlicense` when relevant |
| `owner-brief` | vfops/domain sources + owner-reader-first + vfcopy/Humanizer; preserve IDs/hashes/status/numbers; no public CTA or Instagram voice |
| `human-document` | owning domain pack + vfcopy/Humanizer; marketing/sales document adds `vfmskill` aids; layout/render QA follows text QA |
| `ui-microcopy` | reader-first + vfcopy/Humanizer; canonical technical labels/source values stay literal |

## Public social chain

For caption, Reel/Story/Carousel copy, public bio/profile copy:

`verified context → reader-first → VOICE/VOICE-CHART/approved examples → relevant vfmskill writing aids → type template → velvet-hebrew-copy → Humanizer/AI-tells → surface-aware lint(actual final copy) → fact gate → CONTENT-RUBRIC → PREFLIGHT/exact digest → publish policy`

For cover/first-frame/overlay/slide text, add `NO_TEXT` comparison. Text must add value rather than decorate or restate the image.

## Customer chain

For Gmail/WhatsApp/IG private reply, quote or proposal:

`actual thread/card → relevant convert/sales/cost/license truth → reader-first → relevant sales/copywriting aids → velvet-hebrew-copy → Humanizer/AI-tells → surface-aware lint(actual final copy) → fact gate → ready_to_send/handoff`

A phone/WhatsApp reference in a private customer message is not rejected merely because it would be forbidden as a public Instagram CTA.

## Owner chain

For the 07:00 brief, direct office summary, status explanation, decision copy or owner-facing HTML:

`office truth → reader-first(owner-brief) → velvet-hebrew-copy operational mode → Humanizer/AI-tells → surface-aware lint → fact/status validation → owner surface`

Humanizer may remove filler; it may **not** soften a blocker, alter an ID/hash/number, or make a red sensor sound green.

## Human documents / UI

AI-authored prose in DOC/PDF/slide/HTML/Canva or dashboard UI passes the same baseline before layout is treated as final. Format/render QA is downstream of text QA. Literal technical labels and source payloads are not rewritten.

## Fail-closed rules

- `VOICE.md` alone is not a copy-quality pass.
- Brand Guardian does not replace copy lint; copy lint does not replace Brand Guardian on visual/public work.
- Successful CI/evals do not prove a specific candidate passed.
- `vfmskill`, reader-first, Humanizer and AI-tells are working methods, not reference shelves; when relevant they must affect/review the candidate.
- Text created by ChatGPT, Cursor, Gemini, Perplexity, Grok, Canva, scripts or templates gets no origin exemption.
- Copy written outside `packages/vfcopy` is raw input until it passes the relevant chain.
- Any rewrite after lint requires lint again. Material rewrite after rubric/preflight/render QA invalidates those approvals where applicable.
- Missing proof produces `needs_input` / `חסר` / blocked state — never an invented completion claim.
- `visible_text_gate: PASS` cannot be written just because the policy file exists. If actual execution is unproven, use `UNPROVEN`.

## Approved static copy

Stable text may be marked `approved_static_copy` only after a real pass. It may be reused without rerunning creative rewriting if and only if its exact text/digest is unchanged and its domain facts are still valid. Any material edit or stale fact reopens the gate.

## Evidence

Use the existing artifact/manifest/preflight for evidence; do not create a competing approval database. Where useful retain:

- `surface`
- `reader_first`
- `domain_tools` / `marketing_aids` with `APPLIED | N/A` and reason
- `copy_version` / `text_sha256`
- `humanizer_ai_tells`
- `vfcopy_lint` + surface
- `fact_gate`
- `visual_copy_decision` when applicable
- `surface_qa`
- `visible_text_gate`

## Scope boundary

The contract applies to AI-authored/rephrased text a human will read. It does **not** rewrite verbatim quotes, code, raw logs, filenames, IDs, hashes, URLs, machine JSON/CSV or canonical deterministic labels. AI-authored explanations/titles around those values are in scope.
