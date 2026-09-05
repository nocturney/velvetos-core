# Last 30 days — מחקר רשת (דפוס VF)

מקור השראה: [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) (v3 · Agent Skills).  
מיומנות Cursor: `.cursor/skills/vf-last30/SKILL.md`  
מושב: **ייצור** · `@research-synthesist` (סינתזה) + `@trend-researcher` (מגמה / עונה / discovery).

**לא** מתקינים את הפלאגין / `npx skills` / `last30days.py` על Cloud Agent.  
**לא** דורשים מפתחות X / TikTok / ScrapeCreators כאן. דפוס + כלי המשרד בלבד.

## רעיון

לחפש מה **אנשים** אמרו לאחרונה (engagement: upvotes, comments, stars, points) — לא רק מה שגוגל/עורכים מדגישים — ואז לסנתז בזהירות עם ציטוטים ומקורות.  
Google מצטבר עורכים. כאן — קהילה.

## מצבים

| מצב | מתי | פלט |
|---|---|---|
| **topic** | «מה קרה ב־30 יום האחרונים על X» | בריף `What I learned` + מקורות |
| **comparison** | «A vs B» (כלים / ריפוז / שיטות) | טבלת head-to-head + verdict קצר |
| **discovery** | «מה מתפוצץ ב־…» בלי נושא סגור | 3–7 מועמדים עם רצפה — או **nothing-solid** |

## כלי המשרד (מיפוי מקורות)

| מקור last30days | במשרד VF | הערה |
|---|---|---|
| Web / מאמרים | `WebSearch` / `WebFetch` | failover → תזמורת (`ORCHESTRA.md`) |
| GitHub | `gh api` | user / repo / issues / releases / stars |
| Hacker News | WebSearch `site:news.ycombinator.com` + WebFetch | points / comments אם גלויים |
| Reddit (ציבורי) | WebSearch + WebFetch לדף ציבורי | בלי scraping אגרסיבי; «אין גוף» אם חומה |
| arXiv / Techmeme | WebSearch / WebFetch | חינם; לא ממציאים כותרת נייר |
| Polymarket | WebFetch אם פתוח | odds רק עם URL; אחרת דולג |
| X / TikTok / IG Reels / LinkedIn | **לא** מפתחות כאן | מוזיקה: `MUSIC.md` · Insights: snapshot בעלים או «אין ספירה» |
| Perplexity / ChatGPT / Gemini | תזמורת | כשהווב נחסם — אותו נושא, לא גוף מומצא |

## צעדים (בלי מנוע Python)

### 0 — כוונה + מלכודת מילות מפתח

- נושא ריק → שאלה אחת קצרה; לא רצים מחקר.
- מלכודות: «מתנה לגיל X», ביטוי ליטרלי רחב מדי, שם עצם גנרי בודד → לנסח מחדש או לשאול הבהרה אחת לפני החיפוש.
- טווח ברירת מחדל: **~30 יום** (Asia/Jerusalem). לציין אם המשתמש ביקש חלון אחר.

### 1 — Pre-flight (לפני החיפוש)

| סוג נושא | לפתור לפני fan-out |
|---|---|
| אדם (מייסד / מפתח) | GitHub user (`gh` / WebSearch); קהילות רלוונטיות (subreddit / HN) אם ידועות |
| מוצר / ריפו | `owner/repo` מדויק; כוכבים / release אחרון מ־API חי |
| השוואה | אותם שדות לכל צד |
| עונה / פורמט תוכן VF | קישור ל־`vfseason` / `MUSIC.md` / `expert-trend-explorer` |

לא ממציאים handles. אין חשבון → רושמים «אין handle» וממשיכים.

### 2 — Fan-out מקבילי

לפחות **שלושה** מקורות בלתי תלויים כשאפשר (למשל: GitHub + HN + Web).  
כל מקור שנכשל פעמיים → failover מיד (מקור אחר / תזמורת). לא עוצרים עם ידיים ריקות.

### 3 — רצפת ביטחון (confidence floor)

מועמד / טענה נכנסים לבריף רק אם:

1. יש engagement גלוי **או** אימות חוצה־מקורות, **ו־**
2. הם על־נושא (לא וירוס off-topic).

אחרת — **nothing-solid** (תוצאה כשרה): «אין אות חזק בחלון» + האות החלש הקרוב ביותר (אם יש) בלי להמציא טרנד.

### 4 — סינתזה

- פתיחה: `What I learned:` (או בעברית: `מה למדתי:`) — פסקאות עם **lead-in מודגש**, לא כותרות בלוג מומצאות.
- כל טענה חזקה → קישור / תאריך / מדד engagement אם ידוע.
- מחלוקת → שני הצדדים + משקל יחסי; לא לכבס.
- סיום: מה להטמיע בפק קיים **או** «אין».

## תבנית ארטיפקט

`packages/vfresearch/sources/YYYY-MM-DD-<topic-slug>-last30.md`

```markdown
# last30 · <TOPIC> · YYYY-MM-DD

מושב: ייצור · @research-synthesist / @trend-researcher · Asia/Jerusalem
חלון: ~30 יום · מצב: topic | comparison | discovery
מקור דפוס: mvanhorn/last30days-skill (embed — no CLI)

## Pre-flight

| שדה | ערך |
|---|---|
| GitHub | user/repo או «אין» |
| קהילות | … |
| מלכודת מילות מפתח | עבר / reframed |

## מקורות

| מקור | URL / ref | engagement אם ידוע | משקל |
|---|---|---|---|
| … | … | … | ראשי / משני / דולג |

## What I learned

…

## Nothing-solid?

כן / לא — …

## מה להטמיע

- (פק + קובץ) או «אין»

## מסירה

@slug · pack · או בלוק 05 אם רלוונטי לבריף
```

## מתי להפעיל

- סקירת טרנד עונתי (`vfseason` / `expert-trend-explorer`)
- לפני חבילת תוכן בנושא חדש / השוואת כלים
- מעבר best-skills / weekly links כשצריך הקשר חי מהקהילה
- בעלים שואל «מה אומרים ברשת על… ב־30 יום האחרונים»

## נעול

- המצאת טרנד / שם טראק / Insights / ציטוט בלי מקור
- אוטו־פוסט / אוטו־DM / בוסט בלי ראש צוות
- התקנת last30days CLI / `npx skills` על Cloud Agent
- X/TikTok keys בגיט או על הסוכן
- פק חדש לרעיון מחקר
- הצגת WebSearch-בלבד כאילו רצו את מנוע last30days המלא — לציין במפורש: **דפוס VF / כלי משרד**
