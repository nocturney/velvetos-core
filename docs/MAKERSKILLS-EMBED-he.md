# דוח שתילה — makerskills לתוך HQ/OS

תאריך: 30 באוגוסט 2026  
מקור: https://github.com/coreyhaines31/makerskills (20 מיומנויות, MIT)  
סטודיו: Velvet Factory · שדרות · איסוף בלבד · וואטסאפ 050-2517000 · IG @velvets_cloud  
פק: `packages/vfmakers/` · הרצה: `@vfmakers`

## מה נקרא

הרשימה היא מיומנויות למפעיל אישי: החלטה, קיר, מוח צוות, רוטציית תוכן, CFO חברה, מחקר, מטא־כישורים. עובדת עם Claude Code / Cursor כפלאגין.

אצלנו לא הותקן הפלאגין. לא נפתח `~/.config/makerskills`. לא חובר Typefully / Stripe / Plaid. הוטמעו **דפוסים** על פקים קיימים — אותו כלל כמו `vfe2b`.

## חמשת הצוותים

| צוות | מקור | לאן נשתל | מושב |
|---|---|---|---|
| החלטה | `decide` | `vfbiz/hq/decisions/` | ראש צוות |
| קיר | `unstuck` | `vfops/hq/walls/` | ייצור / ראש צוות |
| דופק כסף | `company-cfo` | `vfbooks/hq/pulse/` | תפעול |
| רוטציית תוכן | `jab-hook` | `vfgrowth/hq/rotation/` | צמיחה |
| מוח סטודיו | `company-brain` | `vfcopy` + `vfsales` `hq/` | סטודיו |

`paste` (סריקת סודות) ו־`social-fetch` (קריאת פוסט ציבורי) נכנסו כצעד בתוך רוטציה / מחקר. בלי פרסום.

## מה דולג ולמה

| דולג | למה |
|---|---|
| הפלאגין + קונפיג אישי | Cursor כבר המשרד; סודות מחוץ לגיט |
| `loopify` | תזמורת על Grok; אין לולאת שליחה/גבייה |
| `personal-cfo` / בנק חי | ספרי סטודיו בלבד; Invoice4U נשאר |
| Typefully / X / LinkedIn | הערוץ הוא אינסטגרם; HQ לא שולח |
| `second-brain` / כספת שנייה | הזיכרון הוא הריפו |
| `domain` / `slide-deck` | לא עבודת הדפסה; אתר נעול ב־`vfbiz` |
| `maker-council` | ממציא אסטרטגיה בשם סלבס |
| B2B מ־`business-brainstorm` | הסט נעול (לוגו, QR, מפיות) עד ראש צוות |

## איך עובדים מחר

```
@vfmakers decide האם לפתוח את סט הלוגו
@vfmakers unstuck הסלייסר לא נותן זמן
@vfmakers cash
@vfmakers rotation
@vfmakers brain capture המשפט שהלקוח אמר
```

בדיקה: `python3 scripts/check-vfmakers.py`.
