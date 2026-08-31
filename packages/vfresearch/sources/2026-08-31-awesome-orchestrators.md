# מחקר · awesome-agent-orchestrators · 2026-08-31

נושא: רשימת כלי תזמורת לסוכנים — מה להטמיע במשרד Velvet Factory בלי runtime שני.

מקור: https://github.com/andyrewlee/awesome-agent-orchestrators  
גוף: README (raw, 31.8.2026). ספירה: **194** פריטי `- [name](url)` בשמונה מדורים.

| מדור | ספירה | דין HQ |
|---|---|---|
| Parallel Coding Agents — Terminal | 15 | skip כהתקנה. דופק herdr → כרטיס |
| Parallel Coding Agents — Desktop & Web | 56 | skip כהתקנה. Orca כבר דפוס משמרת |
| Multi-Agent Swarms | 25 | דפוסי שער/אימות/ארטיפקט. אין נחיל |
| Autonomous Loop Runners | 11 | תקרה + יציאה + הקשר טרי. אין Ralph בלי אדם |
| Autonomous Task Runners | 19 | תיבה→משמרת (Taskuary). אין drain אוטומטי |
| Agent Infrastructure & Primitives | 19 | checkpoint / resume / סיבוב מכסה |
| Personal Assistants | 32 | skip — אדם בוואטסאפ |
| Resting | 17 | skip — ישן / ארכיון |

שאלות המחקר:

1. האם זה פק חדש? — לא. נופל ל־`vfe2b` + `vfharness`. מקור: `AGENTS.md` «לא לפתוח פק כפול».
2. מה כבר יש? — חמישה צוותים + `crews/run.md` (Orca) + רתמה בת שישה שכבות. מקור: `packages/vfe2b/EMBED.md`.
3. מה חסר בכרטיס המשמרת? — דופק, אימות נפרד, נתיב ארטיפקט. מקור: herdr / kodo / tutti ב־README.
4. האם שולחים מ־HQ? — כן, דרך כלים. מקור: `constitution/SEND.md` (31.8). צוותי vfe2b הישנים עדיין אמרו «אל תשלח» — יושר באותו יום.
5. האם מתקינים amux/Orca/OpenClaw? — לא. מקור: `packages/vfe2b/LOCK.md` + anti-pattern סוכן-קידוד שני.

הטמעה: `packages/vfe2b/ORCHESTRATORS.md` + `orchestrators.json`.  
אין ₪. אין Insights. אין גוף מומצא.
