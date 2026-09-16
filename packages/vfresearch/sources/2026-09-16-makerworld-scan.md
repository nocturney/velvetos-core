# סריקת MakerWorld · 2026-09-16 (רביעי)

מושב: מחקר · Asia/Jerusalem  
פלייבוק: `packages/vfresearch/hq/MAKERWORLD-SCAN.md`  
CLI: `python3 scripts/vfsku.py scan` → מדף 0/5 · אין שם להציע עד GATE+רישיון+סלייס

## גישה לדפים

| מקור | תוצאה |
|---|---|
| `https://makerworld.com/en/3dmodels` (WebFetch) | Cloudflare חומה / אין גוף מודל מלא |
| `https://www.printables.com/model` (WebFetch) | Cloudflare חומה / אין גוף |
| WebSearch `site:makerworld.com` | snippets עם URL + שורת רישיון — לא תחליף ל־GATE מלא |

אין המצאת שם מדף. אין הורדה מ־HQ. אין Print מ־HQ.

## כרטיסי מחקר (מועמדים מ־WebSearch בלבד — גוף עמוד לא נפתח ב־WebFetch)

| # | URL | רישיון (מ־snippet) | יוצר / הערה | מדף? |
|---|---|---|---|---|
| 1 | https://makerworld.com/en/models/2205301-sydney-opera-house | Standard Digital File License — snippet: אין מכירה/הפצה של קבצים או הדפסות בתשלום בלי אישור | דקורטיבי אדריכלי | **לא** — חומה על גוף מלא + רישיון לא מסחרי |
| 2 | https://makerworld.com/en/models/2529578-spider-man-no-ams-ams-friendly | Standard Digital File License — אין מכירה בלי אישור; IP מותג | דמות / מותג | **לא** — מותג + רישיון; עצירה לפי `vlicense` |
| 3 | https://makerworld.com/en/models/2029862-flame-horse-fire-horse-2026 | Personal use only · commercial = Patreon/creator | סוס 2026 | **לא** — personal-only / NC-adjacent |
| 4 | https://makerworld.com/en/models/2955110-tesla-model-y-2026 | Standard Digital File License (snippet) | רכב / מותג | **לא** — מותג + אין GATE+סלייס |
| 5 | https://makerworld.com/en/models/3133168-miniature-people-1000-low-poly-figures-5-10 | Personal use; commercial רק עם Patreon | מיניאטורות | **לא** — personal / Patreon |

## מדף (`vfsku`)

```
סריקת MakerWorld: יום סריקה · בלי שם מהאוויר · 2026-09-16
מדף: 0/5 · אין שם להציע עד GATE+רישיון+סלייס
```

## מסקנה

`worker_done` — ארטיפקט סריקה נכתב; explore Cloudflare; snippets מראים Standard Digital File / personal-only → **אין שם להציע** לחריץ 03.  
הצעד הבא: קישור שהבעלים/רצפה נותנים עם רישיון מפורש למכירה → אז `vlicense/GATE.md` לפני סלייס ברצפה.
