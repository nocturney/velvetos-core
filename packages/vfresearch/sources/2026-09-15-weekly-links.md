# סקירת קישורים שבועית · 2026-09-15

מושב: מחקר/אורקסטרציה · Asia/Jerusalem
רישום: `packages/vfresearch/LINKS.json`

## מצב הסקירה

הסקירה המחזורית הייתה באיחור ביחס ל־`WEEKLY.md`, ולכן הושלמה בתוך Research Seat זה. נבדקו 74 רשומות שה־`lastReviewed` שלהן היה ישן מ־2026-09-08. קישורי ChatGPT/Gemini/Perplexity משותפים לא נפתחו; נבדק רק ה־`sourceNote` הקיים. מקורות GitHub נבדקו דרך GitHub ציבורי/מורשה ומקורות Web פתוחים דרך HTTP ציבורי.

- 26 ריפוזיטוריז רשומים הראו push חדש מאז 2026-09-08.
- 6 מקורות Web נשארו מאחורי 403/429 ולכן סומנו כחומה, בלי להמציא גוף.
- evidence machine-readable: `packages/vfresearch/sources/2026-09-15-weekly-links-scan.json`.

## שינוי שימושי שהוטמע

**planning-with-files v3.18.0** — פורסם 2026-09-13. הגרסה מוסיפה inventory קריא של saved plans לפני בחירת `PLAN_ID`. לקחנו רק את הדפוס: לפני פתיחת `vfharness/state/<task-id>` חדש, בודקים state קיים וממשיכים task מתאים במקום ליצור כפילות. אין התקנת upstream, אין pointer/runtime חדש.

מקור: https://github.com/OthmanAdi/planning-with-files/releases/tag/v3.18.0

הוטמע ב־`packages/vfharness/PLANNING-FILES.md` כ־read-only inventory לפני יצירה.
## שינויים שנבדקו ולא הוטמעו

- **VoiceStudio v0.5.2** — release יציב אחרון עדיין 2026-09-10. upstream `main` קיבל ב־2026-09-14 עבודת Electron desktop, אבל אין release חדש. VelvetOS נשאר pinned ל־v0.5.2; אין upgrade על commit לא משוחרר. מקור: https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.2
- **last30days v3.24.0** — פורסם 2026-09-09 ומוסיף X search דרך X API / Grok Bot connector. אין צורך בחיבור/Runtime נוסף למחקר Velvet Factory. מקור: https://github.com/mvanhorn/last30days-skill/releases/tag/v3.24.0
- **agency-agents** — עדכוני 2026-09-08–12 מחזקים invariants ו־regression tests של outputs; הדפוס כבר מכוסה אצלנו בסנסורים/verification, ולכן אין מערכת נוספת. מקור: https://github.com/msitarzewski/agency-agents
- **codebase-memory-mcp** — עדכון 2026-09-14 מוסיף memory core מרכזי ו־spill-to-disk תחת budget; אין הצדקה ל־runtime זיכרון מקביל לצד האינדקס/הזיכרון הקיימים. מקור: https://github.com/DeusData/codebase-memory-mcp
- **OpenPost** — נצרך רק ה־state המקומי העדכני; לא בוצעה בדיקת upstream כפולה משום ש־`OpenPost Release Watch` הוא הבעלים של המעקב.

## דולג — חומה / rate limit

`netsuite-home`, `vbulletin`, `invisioncommunity` → HTTP 403.
`strategic-compact`, `mcpmarket-blender-vxai`, `mcpmarket-market-research-intelligence` → HTTP 429.
אין claim על תוכן שלא נקרא.

## Best Skills / timers

`standingForever=true`, אבל `lastPass=2026-09-14`; חלון ~48 השעות לא הגיע בריצה של 2026-09-15, ולכן Best Skills לא הורץ שוב ולא נוצר timer נוסף.

## בלוק 05

שבועי קישורים — review overdue תוקן; דפוס אחד הוטמע בתוך `vfharness`, בלי pack/runtime חדש. יתר העדכונים שנבדקו לא מצדיקים שינוי production כרגע.
