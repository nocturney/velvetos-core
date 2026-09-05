# סקירת ai-copywriter · 2026-09-05

מושב: ייצור · `@research-synthesist` · Asia/Jerusalem  
רישום: `packages/vfresearch/LINKS.json`  
מקור: https://github.com/mikiarlo3/ai-copywriter (MIT · v1.6.0 · default branch skill)  
סטודיו: Velvet Factory · שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`  
לא פק חדש. לא `npx skills add`. לא Claude Code marketplace על Cloud Agent.

## מה זה

Skill נייד (Markdown בלבד): שני חצאים —

1. **COPYWRITING MODE** — כתיבה מבוססת קורא (enso.bot/research): שתי שאלות (תחושה ברגע + הסבר פשוט), קליטת ICP/קטגוריה/סיפור, בדיקת סיפור לפני טיוטה, פורמטים (כותרת, מיקרוקופי, subject, LinkedIn, בלוג).
2. **Humanizer** — 33 דפוסי AI מ־[blader/humanizer](https://github.com/blader/humanizer) / Wikipedia «Signs of AI writing» (אותו קו כמו write-better שכבר הוטמע).

## מה כבר יש אצלנו

| אצלם | אצלנו | דין |
|---|---|---|
| 33 AI patterns | `vfcopy/hq/ai-tells-he.md` (מ־write-better) | חיזוק נקודתי — לא תרגום מלא |
| copy-editing sweep | `vfmskill` `copy-editing` | כבר מכוסה |
| product marketing context | `.agents/product-marketing.md` | כבר מכוסה |

## מה הוטמע היום

| מקור | לאן | למה |
|---|---|---|
| COPYWRITING MODE (שתי שאלות + intake + story tests) | `packages/vfcopy/hq/reader-first-he.md` | החצי החדש — לפני טיוטה, לא רק לינט |
| הפניות + שורת «קורא» | `PLAYBOOK.md` · `SKILL.md` · `templates/` | מסלול משרד |
| דפוסי דרמה/מקף/clickbait ריק | `ai-tells-he.md` | חיזוק לינט עברי בלי 33 סעיפים |
| מסלול vfmskill | `packages/vfmskill/EMBED.md` | קוראים reader-first לפני ai-tells |

## מה לא הוטמע (מכוון)

| פריט | למה |
|---|---|
| `npx skills add mikiarlo3/ai-copywriter` | נגד «לא skill/פק חדש»; Cursor = משרד |
| `references/linkedin-virality.md` | ערוץ VF = IG + וואטסאפ, לא LinkedIn |
| `references/strategic-blog-template.md` | אתר שיווקי מ־HQ נעול |
| תרגום מילולי של 33 הסעיפים | כבר הוחלט ב־write-better; נלקחו כללים ל־IG/WhatsApp/הצעות |
| SaaS microcopy / error states כמערכת מוצר | אין UI מוצר ציבורי מ־HQ |

## מה חדש לחקור

- אין חובה היום. אם upstream מעדכן את COPYWRITING MODE (לא רק את 33 הדפוסים), pass שבועי ישווה שוב מול `reader-first-he.md`.

## בלוק 05

שבועי קישורים — הוטמע ai-copywriter ב־`vfcopy` (reader-first-he + ai-tells).
