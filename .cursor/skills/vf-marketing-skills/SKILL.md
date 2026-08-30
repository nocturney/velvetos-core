---
name: vf-marketing-skills
description: Route a Velvet Factory marketing task through curated Corey Haines skills (copy, social, offer, research) onto existing packs. HQ does not send; no invented ₪ or Insights.
---

# Marketing skills (curated)

Use when the user asks for קופי, כיתוב, הצעה, חבילת תוכן, ריל, מסגור הצעה, מחקר לקוח/מתחרה, תוכנית שיווק, or mentions `marketingskills` / Corey Haines / `@vfmskill`.

Do **not** activate the full 50-skill upstream set. Ads, email send, SaaS CRO, and pricing stay skipped unless the lead seat opens them.

## First

1. Read `.agents/product-marketing.md`. Missing field = «חסר». Do not invent proof, ₪, or Insights.
2. Read `packages/vfmskill/EMBED.md` and `packages/vfmskill/LOCK.md`.
3. Read the matching vendored `SKILL.md` under `packages/vfmskill/vendor/<skill>/`.

## Route

| Ask | Vendor skill | Pack | Stop |
|---|---|---|---|
| כיתוב / קופי / לינט | `copywriting` `copy-editing` `marketing-psychology` | `vfcopy` | Do not send |
| ריל / סטורי / לוח תוכן | `social` `content-strategy` `video` | `vfgrowth` → `vfigos` | Grok sends |
| כריכה / גרפיקה | `image` | `vfcovers` `vfcanva` | Canva first |
| פנייה / VOC | `customer-research` | `vfconvert` | Gmail read only |
| הצעה / התנגדות | `offers` `sales-enablement` | `vfsales` | After `vfcost`; human WhatsApp |
| מתחרה / רעיון / תוכנית / השקה | `competitor-profiling` `marketing-ideas` `marketing-plan` `launch` | `vfresearch` `vfbiz` `vfsku` | Sources or «חסר» |

Specialists on the desk: `@content-creator` `@brand-guardian` `@instagram-curator` `@sales-engineer` `@growth-hacker`. Warehouse China-social / TikTok agents stay off.

## Laws (win over upstream)

- HQ does not send Instagram, Gmail, WhatsApp, or DMs.
- CTA is WhatsApp `050-2517000` / איסוף שדרות. Not «שלחו DM».
- No TikTok, ads, boost, or follow-back without the lead seat.
- No invented ₪ (`X ₪`) or Insights («אין ספירה»).
- One pipeline: פנייה → שיחה → הצעה → הדפסה → איסוף. No national shipping.
- Floor scenes only from a named Drive job/SKU. Partial pack if proof is missing.

If Canva MCP is `needsAuth`, say `Canva לא מחובר` and use Superdesign / `packages/vfcanva/studio/render.py`.
