# vfmskill — Marketing Skills desk

מפה של [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) אל משרד Velvet Factory.

הספרייה מונה **50** כישורי שיווק (CRO, קופי, SEO, מודעות, SaaS). רובם CMO של מוצר דיגיטלי. אצלנו לא מתקינים את כולם. מטמיעים **15** על הפקים הקיימים.

## מה כן אצלנו

| כישור | פק | מה עושים |
|---|---|---|
| `product-marketing` | הקשר משותף | `.agents/product-marketing.md` — עובדות בלבד |
| `copywriting` / `copy-editing` / `marketing-psychology` | `vfcopy` | טיוטה ולינט בעברית מדוברת |
| `social` / `content-strategy` / `video` | `vfgrowth`, `vfigos` | חבילת תוכן. Grok שולח |
| `image` | `vfcovers`, `vfcanva` | כריכות. לא פוסט חי |
| `customer-research` | `vfconvert` | בריף משרשור. אין לקוח מומצא |
| `offers` / `sales-enablement` | `vfsales` | מסגור הצעה אחרי `vfcost` |
| `competitor-profiling` | `vfresearch` | מקורות ציבוריים. אין Insights מומצא |
| `marketing-ideas` / `marketing-plan` / `launch` | `vfgrowth`, `vfbiz`, `vfsku` | רעיונות ותוכנית על הצינור האחד |

## מה לא

ראה [`LOCK.md`](LOCK.md): מודעות, שליחת מייל/SMS, מחירון SaaS, אתר, AutoQuote, attribution.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | 50 כישורים + פסילות, קריא למכונה |
| [`EMBED.md`](EMBED.md) | איך מריצים את חמשת המסלולים |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`VENDOR.md`](VENDOR.md) | SHA של המקור |
| [`vendor/`](vendor/) | 15 כישורים (MIT, בלי evals) |
| [`CONTEXT.md`](CONTEXT.md) | מצביע ל־`.agents/product-marketing.md` |
| [`hq/PLAYBOOK.md`](hq/PLAYBOOK.md) | לינט משרד |
| [`.cursor/skills/vf-marketing-skills/SKILL.md`](../../.cursor/skills/vf-marketing-skills/SKILL.md) | כישור Cursor |
| [`scripts/check-vfmskill.py`](../../scripts/check-vfmskill.py) | בדיקת עקביות |

## איך מפעילים

ב-Cursor:

```
@vfmskill קופי לריל
@vfmskill הצעה אחרי הסכום שאמר כריסטיאן
@vfmskill חבילת תוכן מהדפסה שסיימנו
```

או פותחים את הכישור `.cursor/skills/vf-marketing-skills`.

רענון vendor:

```bash
./scripts/install-marketing-skills.sh
python3 scripts/check-vfmskill.py
```
