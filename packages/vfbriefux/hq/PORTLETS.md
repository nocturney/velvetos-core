# Portlets — דאשבורד לפי תפקיד

דפוסים מ־NetSuite (role home + KPI portlets), Salesforce Pro (default dashboards), Odoo Dashboard, Monday status.

הבריף החי נשאר 01–07 (`BRIEF-SLOTS.md` + `MAIL.html`). Portlet = **שם נוסף** לאותו חריץ — לא מבנה שני.

## מיפוי

| Portlet (השראה) | חריץ VF | מקור אמת | ריק = |
|---|---|---|---|
| Decisions due | 01 קודם החלטה | ראש צוות / walls | אין החלטה פתוחה |
| AR / cash in work | 02 כסף בעבודה | `vfbooks` מאומת | אין ספירה |
| Print queue + publish queue | 03 מה להדפיס ולפרסם | סלייסר / `vfigos` | אין ספירה |
| Locked B2B / margin story | 04 איך הסטודיו מרוויח | `vfbiz` | נעול / בלי ₪ מומצא |
| Office upgrades | 05 משרד | `vfops/data/research.md` | אין חדש במשרד |
| Feed health | 06 מה קורה בעמוד | `vfinsights` אחרי פרסום+24ש | אין ספירה |
| Content tray | 07 פיד בסוף | `vfcovers` / `vfigos` | `#לא-זז` |

## כללי UI עתידי

1. Portlet בלי מקור מציג «אין ספירה» / «אין חדש» — לא אפס ירוק.
2. סינון לפי מושב (ראש צוות רואה הכל; צמיחה רואה 06–07; תפעול רואה 02+04).
3. עיצוב: `DESIGN.md` — לא סגול-SaaS, לא כרטיסי hero מיותרים בבריף המייל.
4. עדכון: אותו JSON/HTML של תצוגה 3; הקונסולה רק *קוראת* את הבריף.

## השראת layout (לא חובה)

```
[ 01 Decisions ] [ 02 Cash ]
[ 03 Queue              ]
[ 05 Office ] [ 06 Feed ]
[ 07 Content tray       ]
```

צפיפות כמו NetSuite portlets — לא Monday board מלא במסך הבית.
