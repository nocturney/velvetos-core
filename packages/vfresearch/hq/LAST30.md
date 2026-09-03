# Last 30 days — מחקר רשת (דפוס)

מקור השראה: [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) (Top repos ב־LinklyAI/best-skills).  
**לא** מתקינים את הפלאגין / לא דורשים מפתחות X/TikTok על Cloud Agent.

## רעיון

לחפש מה **אנשים** אמרו לאחרונה (engagement), לא רק מה שגוגל מדגיש — ואז לסנתז בזהירות עם ציטוטים.

## במשרד VF (כלים שיש)

| מקור | כלי | הערה |
|---|---|---|
| ווב / מאמרים | `WebSearch` / `WebFetch` | failover → תזמורת |
| GitHub | `gh api` | ריפוז / issues / stars |
| HN | WebSearch `site:news.ycombinator.com` | |
| Reddit (ציבורי) | WebSearch | בלי scraping אגרסיבי |
| IG / TikTok / X | **לא** מפתחות כאן | מוזיקה: `MUSIC.md` · טרנדים: snapshot בעלים או «אין ספירה» |

## מתי

- סקירת טרנד עונתי (`vfseason` / `expert-trend-explorer`)
- לפני חבילת תוכן בנושא חדש
- מעבר best-skills / weekly links כשצריך הקשר חי

## פלט

ארטיפקט ב־`packages/vfresearch/sources/YYYY-MM-DD-<topic>-last30.md`:

- שאלה
- מקורות עם קישורים / תאריכים
- מה חזק (engagement אם ידוע) vs מה דולג
- מה להטמיע בפק קיים — או «אין»

## נעול

- המצאת טרנד / שם טראק / Insights
- אוטו־פוסט לרשתות
- התקנת last30days CLI על Cloud Agent
