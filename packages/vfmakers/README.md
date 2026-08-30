# vfmakers — Maker-skills desk

מפה של [coreyhaines31/makerskills](https://github.com/coreyhaines31/makerskills) (20 מיומנויות, MIT) אל משרד Velvet Factory.

הרשימה בנויה למייסד אינדי: החלטות, מחקר, מוח שני, רוטציית תוכן, מודל תרחישים, CFO. אצלנו לא מתקינים את הפלאגין. מטמיעים **דפוסים** על הפאקים הקיימים.

## מה כן אצלנו

| דפוס מ-makerskills | פק | מה עושים |
|---|---|---|
| `decide` | `vfbiz`, `vfops` | 6–8 שאלות, קריאה ברורה, ארכיון עם תאריך חזרה |
| `unstuck` | `vfops`, `vfprod` | סיווג הקיר + זוויות. רישיון / «לא» של לקוח לא עוקפים |
| `company-cfo` | `vfbooks`, `vfcost` | דופק שבועי / צילום חודשי ממקור מאומת בלבד |
| `jab-hook` | `vfgrowth`, `vfcopy`, `vfigos` | ג׳אב (ערך) ואז הוק (וואטסאפ). HQ לא שולח |
| `company-brain` | HQ + `vfcopy` + `vfsales` | לכידת שפת לקוח / התנגדויות / FAQ לתוך `hq/` |
| `paste` (סודות) | `vfcopy` | לפני טיוטה שיוצאת מהמשרד — אין סודות בגיט |
| `social-fetch` | `vfresearch`, `vfgrowth` | קריאת פוסט ציבורי כעובדה. אין פוסט / DM |

## מה לא

ראה [`LOCK.md`](LOCK.md): הפלאגין, Typefully, Stripe/Plaid, `personal-cfo`, `loopify`, מועצת סלבס, כספת מחוץ ל־HQ.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | 20 המיומנויות + פסק דין |
| [`EMBED.md`](EMBED.md) | איך מריצים את חמשת הצוותים |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`crews/`](crews/) | נהלי צוות להרצה ב-Cursor |
| [`EXAMPLES.md`](EXAMPLES.md) | מה אומרים → מה יוצא |
| [`scripts/check-vfmakers.py`](../../scripts/check-vfmakers.py) | בדיקת עקביות מול `packages/manifest.json` |

## איך מפעילים

ב-Cursor:

```
@vfmakers decide <החלטה>
@vfmakers unstuck <קיר>
@vfmakers cash
@vfmakers rotation
@vfmakers brain capture|query
```

או פותחים את הקובץ ב-`crews/` ומריצים לפי הסדר.

`python3 scripts/check-vfmakers.py` — צפי: `OK picks embed crews locks`.
