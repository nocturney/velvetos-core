---
name: vf-weekly-links
description: Weekly pass over Velvet Factory inspiration and embed links — re-read registered URLs, embed updates into existing packs, note new research. Use when the user asks for סקירת קישורים, weekly inspiration, refresh shares, or קישורי השראה.
---

# Weekly inspiration links

Use when the user asks for סקירת קישורים שבועית, refresh of ChatGPT/Gemini/Perplexity shares, or «מה חדש בקישורים להטמעה».

## Packs and specialists

- Pack: `vfresearch` (existing — do not open a new pack)
- Mention: `@research-synthesist` (and `@trend-researcher` if season/trend)
- Lead seat reads the brief line in block `05`

## Run

1. Read `packages/vfresearch/WEEKLY.md` and `packages/vfresearch/LINKS.json`.
2. For each link: open URL (or source note / PDF if walled). Compare to last embed. Embed useful updates **in place**. Never invent a blocked body, ₪, or Insights.
3. Write `packages/vfresearch/sources/YYYY-MM-DD-weekly-links.md`.
4. Set brief `05` line: embed summary or «שבועי קישורים — אין חדש במשרד».
5. After catalog/pack edits: `python3 scripts/check-all.py` (includes `check-vfresearch.py`).
6. New URL mid-week: append to `LINKS.json` the same day.

## Forbidden

Instagram/Gmail/WhatsApp send, new pack per idea, invented Perplexity/Cloudflare body, Calendar create without lead ask, installing FCC/Graft/CBM binaries from HQ.
