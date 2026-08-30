# מעבר Grok · failover מכסה · 2026-08-30 (Asia/Jerusalem)

## מה נשאל

הבעלים: אם תיגמר מכסת השימוש השבועית בגרוק בוט — האם HQ יכול לבצע את פעולות צוות הסוכנים שלו עד חידוש המכסה, בעזרת GPT / Gemini / Perplexity, ולהטמיע כפיילאובר כדי לא להישאר בלי תוצרים. **גם פרסומים חיים במידת הצורך.**

## מה הוטמע

- נוהל: `packages/vfharness/playbooks/grok-failover.md`
- מסמך קבע: `docs/GROK-FAILOVER.md`
- תור: `packages/vfigos/QUEUE.md` (`#מוכן-ל-Grok` + `#פרסום-חי-דחוף`)
- חבילת פרסום חי ליד אדם: `packages/vfigos/LIVE-PACKET.md`
- חוק + ANTI-PATTERN ב־`AGENTS.md`
- שולחן / גרף / צוות תוכן / תזמורת
- סנסור: `scripts/check-vfharness.py`

## Failover

| נפל | עבר ל־ |
|---|---|
| Grok Bot (מכסה / לא זמין) — טיוטות | Cursor HQ + תזמורת ChatGPT+Gemini+Perplexity |
| Grok Bot — פרסום לא־דחוף | תור `#מוכן-ל-Grok` |
| Grok Bot — **פרסום חי דחוף** | `LIVE-PACKET` → **אדם** מעלה ב־IG · סוכן HQ לא לוחץ Publish |

## מה דולג

- Publish אוטומטי מ־HQ / MCP Instagram send / בוסט / אוטו־DM.
- המצאת ₪ / Insights / גוף חסום.
- פק חדש ל«סוכן גיבוי גרוק».

## בלוק 05

מה נבנה / יועל: פיילאובר מכסת Grok — תוצרים ב־HQ; פרסום חי דחוף בידי אדם עם LIVE-PACKET (`docs/GROK-FAILOVER.md`).
