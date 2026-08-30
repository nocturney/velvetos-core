# vfdsh — Awesome-DSH-plugin desk

מפה של [awesome-dsh-plugin/awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin) אל משרד Velvet Factory.

הרשימה מונה **2710** תוספים ל-[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh plugin add`). רובם כרום UI, ערכות נושא, או ראנטיים שני. אצלנו לא מתקינים את הרתמה. מטמיעים **דפוסים** על הפאקים הקיימים.

## מה כן אצלנו

| דפוס מהרשימה | פק | מה עושים |
|---|---|---|
| Modlens / Vision Toolkit / PictureReader | `vfprod`, `vfcovers` | קריאת צילום רצפה / WhatsApp שכבר בתיקייה. מה שלא נראה — «לא נראה» |
| pbr-render (GLB/GLTF) | `vfprod`, `vlicense` | הערות מודל לפני הדפסה. אין מיטה מומצאת |
| MinerU / PDF / Office → Markdown | `vfbooks`, `vfconvert` | חילוץ מחשבונית או בריף שצוין. אין ₪ מומצא |
| Engramory / MemSearch / project-memory | `vfresearch`, `vfsku` | זיכרון מקבצי HQ עם ציטוט. אין שרת זיכרון שני |
| dsh_workflow / Taskboard / verification | `vfops`, `vfprod` | לוח צינור + שער אדם. הסוכן מגיש לסקירה, לא ל«בוצע» |
| Superdesign / TongFlow / iPolloWork | `vfcovers`, `vfcanva` | Canva או Superdesign שכבר על השולחן. אין פוסט חי |
| Treg DSH | `vfresearch`, `vfinsights` | Treg שכבר מותקן; מחיר קטלוג לפני `call` |
| Ambiguity + negative ledger | `vfconvert`, `vfprod` | שואלים לפני ניחוש; נתיב שנכשל נשאר כתוב |

## מה לא

ראה [`LOCK.md`](LOCK.md): אין `dsh plugin add`, אין בוט WhatsApp, אין קרון בלי אדם, אין ערכות נושא, אין Pentest.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | בחירות + פסילות, קריא למכונה |
| [`EMBED.md`](EMBED.md) | איך מריצים את חמשת הצוותים |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`crews/`](crews/) | נהלי צוות להרצה ב-Cursor |
| [`scripts/check-vfdsh.py`](../../scripts/check-vfdsh.py) | בדיקת עקביות מול `packages/manifest.json` |

כתבה: [`docs/DSH-FIT.md`](../../docs/DSH-FIT.md).

## איך מפעילים

ב-Cursor:

```
@vfdsh floor <job or photo path>
@vfdsh docs <invoice or thread>
@vfdsh memory <SKU or question>
@vfdsh board
@vfdsh design <brief id>
```

או פותחים את הקובץ ב-`crews/` ומריצים לפי הסדר.

`python3 scripts/check-vfdsh.py` — צפי: `OK picks packs crews locks`.
