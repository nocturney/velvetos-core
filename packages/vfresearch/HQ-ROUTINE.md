# HQ Research Routine · מנדט חוקרים

מושב: **מחקר/אורקסטרציה** (`constitution/TEAM.md`).  
לא פק חדש. לא runtime שני. לא `npx skills` על Cloud Agent.  
החוקרים = skills קיימים על הדסק (`.cursor/skills/`) + packs קיימים (`packages/`).

מיומנויות: `vf-morning-brief` · `vf-best-skills` · `vf-weekly-links` · `vf-last30` · `vf-daily-learning` · `vf-hq-memory`  
חוקה: `constitution/ORCHESTRA.md` · שגרה: `vfops/ROUTINE.md` · בריף: `vfops/BRIEF.md`

## חוקים קשיחים

- אין פק חדש לכל רעיון — הטמעה במקום על פק קיים.
- אין Insights / ₪ / גוף מחומת מקור מומצאים. חסר = «אין ספירה» / «אין גוף» / `X ₪`.
- CTA נשאר וואטסאפ `050-2517000` / איסוף שדרות. לא «שלחו DM».
- כלי נפל (`needsAuth` / חומה / אין מפתח) → failover מיד (`ORCHESTRA.md` + `vfmcp/GAP.md`). תמיד ארטיפקט.
- אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
- תוצרים נכנסים ל־Git (commit + push) כדי שהמערכת תמשיך.

## 1 · יומי (06:15–07:00 Asia/Jerusalem)

### א. אינדקס זיכרון

```bash
python3 scripts/vfresearch_cadence.py build-index
# equivalent: python3 packages/vfmem/scripts/vf_semantic_search.py --build
```

**Fail closed** — אל תסתירו כשל ב־`|| echo`. אינדקס מקומי (`semantic_index.pkl`, לא בגיט). CI מעלה artifact לצרכן. חסר `sklearn` → `pip install scikit-learn` או שורת פער בארטיפקט.

מפת מפעילים / DST / בעלות סביבה:

```bash
python3 scripts/vfresearch_cadence.py map
python3 scripts/vfresearch_cadence.py status   # evidence vs not-run-here — לא מסמנים «פעיל» בלי ארטיפקט
```

GrokBot `weekday-ops` 07:00 = בריף/תפעול — **לא** יוצרים cron מחקר כפול אצלו.

### ב. מחקר יומי (תזמורת)

1. Skill `vf-morning-brief` + פלייבוק `DAILY.md`.
2. שלושה שולחנות לפי `ORCHESTRA.md`: ChatGPT / Gemini / Perplexity.  
   Cloud בלי מפתח API → `WebSearch` / `WebFetch` / מקורות ב־`sources/` (לא דפדפן מנוי).
3. הטמעה שימושית → פק קיים. ריק → בדיוק «אין חדש במשרד».
4. כתיבה ל־`packages/vfops/data/research.md` (בלוק 05).
5. ארטיפקט גולמי: `packages/vfresearch/sources/YYYY-MM-DD-orchestra.md`.

### ג. אחרי פרסום חי

1. לעדכן `packages/vfinsights/data/posts.csv` מנתוני Instagram Professional Dashboard (בעלים / כלי מחובר).
2. `python3 packages/vfinsights/scripts/vf_insights_loop.py --data packages/vfinsights/data/posts.csv` → `LEARNINGS.md`.
3. בלי reach אמיתי — שדה ריק + «אין ספירה» בבריף 06. לא לנחש.

## 2 · כל ~48 שעות (vf-best-skills)

1. `packages/vfresearch/TIMER.md` · שם `vf-best-skills-bi-daily` · `delaySeconds: 172800`.
2. Skill `vf-best-skills` על [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills).
3. עדכון `BEST-SKILLS.md` + `BEST-SKILLS.json` (`lastPass`, `dataDate`, movers).
4. הטמעת דפוסים ל־`vfconvert` / `vfcopy` / `vfharness` / `vfops` / `vfgrowth` (ופקים קיימים אחרים) — בלי פק חדש.
5. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
6. **חובה:** `list_subscriptions` + חידוש `subscribe_timer` אם חסר/פג. לרשום `timer: renewed|ok`.
7. אין `npx skills add` על Cloud.

## 3 · פעם בשבוע (vf-weekly-links + print-demand)

1. `WEEKLY.md` + `LINKS.json` מלמעלה למטה.
2. לכל קישור: מקור / PDF / `sourceNote` · השוואה ל־`sources/`/`docs` · הטמעה או «ללא שינוי» / «דולג — חומה».
3. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-weekly-links.md`.
4. **Print · Demand · Sound:** `hq/PRINT-DEMAND.md` → `sources/YYYY-MM-DD-print-demand.md` (ויזואל 3D + ביקוש IL + סאונד). אין אוטו־DM · אין Insights מומצאים · חומרים רק מהמדף.
5. **סריקת MakerWorld א׳+ד׳** (אם היום ראשון או רביעי): `hq/MAKERWORLD-SCAN.md` + `python3 scripts/vfsku.py scan`. NC ≠ מכירה. אין שם מהאוויר.
6. שורת בלוק 05 בבריף הבא (קישורים + print-demand).
7. קישור חדש באמצע השבוע → `LINKS.json` **באותו יום**.
8. אם `standingForever: true` והטיימר חסר → לחדש לפי `TIMER.md` באותו מעבר.

## 4 · פעם בחודש (vf-last30)

1. Skill `vf-last30` · פלייבוק `hq/LAST30.md`.
2. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-<topic>-last30.md` (+ עדכון `hq/LAST30.md` כשיש מסקנות עמידות).
3. מסקנות → `vfcopy` / `vfgrowth` / `vfbiz` / `vfops` (סוגי פוסטים, שעות, מבנים) — רק עם מקור. מותר **nothing-solid**.

## 5 · סוף יום (vf-daily-learning)

אחרי 18:00 Asia/Jerusalem (או סגירת משמרת):

1. Skill `vf-daily-learning` · `vfops/hq/DAILY-RETRO.md`.
2. שורה ב־`vfops/data/owner-memory.md`.
3. לא להסלים לבעלים מדדים חלשים / «רמה נמוכה» / דוח בושה — רק החלטות, חסמים, פרסום חי שדורש אותו.

## אוטונומיה

- להריץ לפי הקאדנס בלי בקשה ידנית (טיימר + שגרת בוקר + GitHub Actions `velvetos-research.yml` כגיבוי סנסורים).
- סוף יום / סוף שבוע: ארטיפקטים מעודכנים ב־`sources/` ו־`hq/` · בריף 07:00 משקף בלוקים 05+06 · הכל ב־Git.

## מיפוי מושב ↔ skills

| קאדנס | Skill | פק |
|---|---|---|
| יומי תזמורת | `vf-morning-brief` + `DAILY.md` | `vfresearch` → `vfops/data/research.md` |
| כל יומיים | `vf-best-skills` | `vfresearch` |
| שבועי | `vf-weekly-links` + `PRINT-DEMAND.md` | `vfresearch` |
| חודשי | `vf-last30` | `vfresearch` |
| רבעוני | `OWNER-QUESTIONS-QUARTERLY.md` | `vfops` + `vfinsights` LEARNINGS — בלי המצאת מדדים |
| סוף יום | `vf-daily-learning` | `vfops` |
| ניתוב | `vf-hq-memory` | `vfmem` |
| דוח מנתונים קיימים | `python3 scripts/vf_office_report.py` | `CLIENT-REPORT-TEMPLATE.md` · `--fixture` לנתוני דמה |
