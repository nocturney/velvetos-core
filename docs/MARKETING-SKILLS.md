# Marketing Skills — מה נכנס למשרד

מקור: [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT, נקרא 2026-08-30, pin `e55de88`).  
50 כישורי CRO / קופי / SEO / מודעות / SaaS. רובם CMO של מוצר דיגיטלי.

כאן זה **מפה + 15 כישורים** על החבילות הקיימות. אין התקנת כל ה־50 ב־`.cursor/skills/`. אין שליחת אינסטגרם או ג׳ימייל מ־HQ. אין ₪ מומצא. אין Insights מומצא.

פק הקטלוג: [`packages/vfmskill/`](../packages/vfmskill/).  
מפה מכונה: [`packages/vfmskill/catalog.json`](../packages/vfmskill/catalog.json).  
הקשר מוצר: [`.agents/product-marketing.md`](../.agents/product-marketing.md).  
כישור יומי: [`.cursor/skills/vf-marketing-skills/SKILL.md`](../.cursor/skills/vf-marketing-skills/SKILL.md).  
בדיקה: `python3 scripts/check-vfmskill.py`.

## כבר יש אצלנו — לא לשכפל

| כישור מהספרייה | חבילה אצלנו | למה לא פק חדש |
|---|---|---|
| `copywriting` / `copy-editing` | `vfcopy` | שיעורי בית, טיוטה, לינט |
| `social` / `content-strategy` / `video` | `vfgrowth`, `vfigos` | חבילה וסקירה. Grok שולח |
| `image` | `vfcovers`, `vfcanva` | כריכות. Canva קודם |
| `customer-research` | `vfconvert` | בריף משרשור |
| `offers` / `sales-enablement` | `vfsales` | הצעה אחרי `vfcost` |
| `competitor-profiling` | `vfresearch` | מקורות או «חסר» |
| `marketing-plan` / `launch` | `vfbiz`, `vfsku`, `vfseason` | תוכנית על הצינור האחד |
| `pricing` | `vfcost` | דולג ככישור. ₪ לא מומצא |
| `analytics` | `vfinsights` | later — רק סנאפשוט מאומת |
| `ads` / `emails` | — | skip. HQ לא שולח ולא מקדם |

## מה הוטמע

15 כישורים תחת `packages/vfmskill/vendor/` (בלי evals). שכבת משרד ב־`EMBED.md` + `LOCK.md`.  
רענון: `./scripts/install-marketing-skills.sh`.

## מה דולג

מודעות, מייל/SMS חי, מחירון SaaS, אתר, AutoQuote, attribution, רשימות קרות — [`packages/vfmskill/LOCK.md`](../packages/vfmskill/LOCK.md).
