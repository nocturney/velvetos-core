# HQ Research Routine · מנדט חוקרים

מושב: **מחקר/אורקסטרציה** (`constitution/TEAM.md`).  
לא פק חדש. לא runtime שני. לא `npx skills` על Cloud Agent.  
החוקרים = skills קיימים על הדסק (`.cursor/skills/`) + packs קיימים (`packages/`).

מיומנויות: `vf-morning-brief` · `vf-best-skills` · `vf-weekly-links` · `vf-last30` · `vf-daily-learning` · `vf-hq-memory`  
חוקה: `constitution/ORCHESTRA.md` · שגרה/שעון: `vfops/ROUTINE.md` · בריף: `vfops/BRIEF.md`

## חוקים קשיחים

- אין פק חדש לכל רעיון — הטמעה במקום על פק קיים.
- אין Insights / ₪ / גוף מחומת מקור מומצאים. חסר = «אין ספירה» / «אין גוף» / `X ₪`.
- CTA ציבורי = הודעת Instagram (`PUBLIC_CTA.md`). BUSINESS_CONTACT_RECORD נשאר פנימי; אין auto-DM.
- כלי נפל (`needsAuth` / חומה / אין מפתח) → failover מיד (`ORCHESTRA.md` + `vfmcp/GAP.md`). תמיד ארטיפקט אמיתי או blocker אמיתי.
- אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
- תוצרים נכנסים ל־Git כשהם SoT/ארטיפקט repo, לא כדי להעמיד פנים ש-provider action בוצע.

## 1 · יומי — Research Seat ב־02:00, cutoff ב־07:00

### א. גוף המחקר

1. Skill `vf-morning-brief` + פלייבוק `DAILY.md`.
2. בעל הריצה החי הוא **Velvet Research Seat** ב־02:00 Asia/Jerusalem; היעד הוא סיום עד 07:00 כדי שה־Morning Brief של 09:00 יקבל גוף מוכן.
3. WebSearch / WebFetch / מקורות ציבוריים וחיבורים מאומתים הם ברירת המחדל. כלי מנוי/מק יכולים להשלים, לא להיות נקודת כשל יחידה.
4. הטמעה שימושית → פק קיים. ריק → בדיוק «אין חדש במשרד» עם הוכחת חיפוש.
5. כתיבה ל־`packages/vfops/data/research.md` עבור בריף 09:00.
6. ארטיפקט גולמי: `packages/vfresearch/sources/YYYY-MM-DD-orchestra.md`.

### ב. אינדקס + אימות

```bash
python3 scripts/vfresearch_cadence.py build-index
python3 scripts/vfresearch_cadence.py map
python3 scripts/vfresearch_cadence.py status
python3 scripts/vfresearch_cadence.py freshness
```

**Fail closed** — אל תסתירו כשל ב־`|| echo`. אינדקס מקומי (`semantic_index.pkl`, לא בגיט); CI יכול להעלות artifact לצרכנים. `VelvetOS Research Cadence` ב־GitHub הוא verifier/index/sensor path, לא תחליף לגוף Web research ולא cron כפול.

### ג. אחרי פרסום חי

1. לעדכן `packages/vfinsights/data/posts.csv` רק מנתוני Instagram מאומתים (`vf_insights_ingest.py`) או מקור בעלים מפורש.
2. `python3 packages/vfinsights/scripts/vf_insights_loop.py --data packages/vfinsights/data/posts.csv` → `LEARNINGS.md`.
3. בלי reach אמיתי — שדה ריק + «אין ספירה». לא לנחש ולא להסלים חולשה לבעלים.

## 2 · כל ~48 שעות (vf-best-skills)

1. `packages/vfresearch/TIMER.md` · שם `vf-best-skills-bi-daily` · `delaySeconds: 172800`.
2. Skill `vf-best-skills` על [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills).
3. עדכון `BEST-SKILLS.md` + `BEST-SKILLS.json` (`lastPass`, `dataDate`, movers).
4. הטמעת דפוסים לפקים קיימים בלבד — בלי פק חדש.
5. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
6. timer/provider renewal נחשב מוכח רק עם provider evidence. אם לא ניתן לאמת — `UNPROVEN`, לא `renewed` מומצא.
7. אין `npx skills add` על Cloud.

## 3 · פעם בשבוע (vf-weekly-links + Print·Demand·Sound)

1. `WEEKLY.md` + `LINKS.json` מלמעלה למטה.
2. לכל קישור: מקור / PDF / `sourceNote` · השוואה ל־`sources/`/`docs` · הטמעה או «ללא שינוי» / «דולג — חומה».
3. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-weekly-links.md`.
4. `hq/PRINT-DEMAND.md` → `sources/YYYY-MM-DD-print-demand.md`; אין Insights מומצאים ואין קפיצה מרעיון ל־SKU/מחיר.
5. MakerWorld/Printables candidates עוברים לפי `hq/MAKERWORLD-SCAN.md`: מקור אמיתי → רישיון → slice → test לפני promotion. אין SKU/מחיר רק כי נמצא דגם.
6. Social Intelligence כשנדרש: `SOCIAL-INTELLIGENCE.md` → `SocialResearchPacket` / `ReferencePattern` → `INSTAGRAM-CONTENT-DECISION.json`. נתוני החשבון שלנו נשארים בספק Instagram המאומת.
7. קישור חדש באמצע השבוע → `LINKS.json` באותו יום.

## 4 · פעם בחודש / לפי דרישה (vf-last30)

1. Skill `vf-last30` · פלייבוק `hq/LAST30.md`.
2. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-<topic>-last30.md`.
3. מסקנות → פקים קיימים בלבד, ורק עם מקור. מותר **nothing-solid**.

## 5 · סוף יום (vf-daily-learning)

ה־Office Loop של 18:30 הוא משטח התפעול הקנוני לרטרו/למידה כאשר יש חומר חדש:

1. Skill `vf-daily-learning` · `vfops/hq/DAILY-RETRO.md`.
2. promote רק עובדות עמידות ל־`vfops/data/owner-memory.md`.
3. לא להסלים לבעלים מדדים חלשים / «רמה נמוכה» / דוח בושה — רק החלטות וחסמים אמיתיים.

## אוטונומיה

- השעון החי נקבע ב־`vfops/ROUTINE.md` וב־protected automation inventory, לא בכותרות היסטוריות כאן.
- GitHub Actions `velvetos-research.yml` מאמת freshness/index/sensors; אינו מבצע או מוכיח את גוף המחקר עצמו.
- כל claim של send/publish/timer/provider state דורש provider evidence מתאים.

## מיפוי מושב ↔ skills

| קאדנס | Skill | פק |
|---|---|---|
| יומי 02:00 | `vf-morning-brief` + `DAILY.md` | `vfresearch` → `vfops/data/research.md` |
| כל יומיים | `vf-best-skills` | `vfresearch` |
| שבועי | `vf-weekly-links` + `PRINT-DEMAND.md` | `vfresearch` |
| חודשי | `vf-last30` | `vfresearch` |
| רבעוני | `OWNER-QUESTIONS-QUARTERLY.md` | `vfops` + `vfinsights` LEARNINGS |
| סוף יום | `vf-daily-learning` | `vfops` |
| ניתוב | `vf-hq-memory` | `vfmem` |
| דוח מנתונים קיימים | `python3 scripts/vf_office_report.py` | `CLIENT-REPORT-TEMPLATE.md` · `--fixture` לנתוני דמה |
