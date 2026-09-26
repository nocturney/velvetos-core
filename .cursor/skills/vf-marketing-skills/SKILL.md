---
name: vf-marketing-skills
description: Route a Velvet Factory marketing task through curated Corey Haines skills (copy, social, offer, research) onto existing packs. HQ sends via tools (constitution/SEND.md); no invented ₪ or Insights.
---

# Marketing skills (curated)

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Use when the user asks for קופי, כיתוב, הצעה, חבילת תוכן, ריל, מסגור הצעה, מחקר לקוח/מתחרה, תוכנית שיווק, or mentions `marketingskills` / Corey Haines / `@vfmskill`.

Do **not** activate the full 50-skill upstream set. Ads, email send, SaaS CRO, and pricing stay skipped unless the lead seat opens them.

## First

1. Read `.agents/product-marketing.md`. Missing field = «חסר». Do not invent proof, ₪, or Insights.
2. Read `packages/vfmskill/EMBED.md` and `packages/vfmskill/LOCK.md`.
3. Read the matching vendored `SKILL.md` under `packages/vfmskill/vendor/<skill>/`.

## Route

| Ask | Vendor skill | Pack | Stop |
|---|---|---|---|
| כיתוב / קופי / לינט | `copywriting` `copy-editing` `marketing-psychology` | `vfcopy` | HQ sends via tools |
| ריל / סטורי / לוח תוכן | `social` `content-strategy` `video` | `vfgrowth` → `vfigos` | `SEND.md` |
| מוזיקה / סאונד לריל | (frame) `social` Audio Strategy | `vfresearch` → `vfom` → `vfigos` | `@trend-researcher`; HeyOrca / IG paste (no Treg) |
| פנייה / VOC | `customer-research` | `vfconvert` | Gmail read then reply via tool |
| הצעה / התנגדות | `offers` `sales-enablement` | `vfsales` | After `vfcost`; human WhatsApp |
| מתחרה / רעיון / תוכנית / השקה | `competitor-profiling` `marketing-ideas` `marketing-plan` `launch` | `vfresearch` `vfbiz` `vfsku` | Sources or «חסר» |

Specialists on the desk: `@content-creator` `@brand-guardian` `@instagram-curator` `@sales-engineer` `@growth-hacker`. Warehouse China-social / TikTok agents stay off.

## Laws (win over upstream)

- HQ **sends Instagram and Gmail via tools** (`constitution/SEND.md`). Customer WhatsApp stays human. No auto-DM.
- CTA is **PUBLIC_CURRENT_CTA** = Instagram message / איסוף שדרות. Not bare «שלחו DM». Not WhatsApp phone in public copy. Business phone `050-2517000` = BUSINESS_CONTACT_RECORD only (`constitution/PUBLIC_CTA.md`).
- No TikTok, ads, boost, or follow-back without the lead seat.
- No invented ₪ (`X ₪`) or Insights («אין ספירה»).
- One pipeline: פנייה → שיחה → הצעה → הדפסה → איסוף. No national shipping.
- Floor scenes only from a named Drive job/SKU. Partial pack if proof is missing.


## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)



## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
