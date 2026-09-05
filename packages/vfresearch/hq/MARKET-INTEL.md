# Market intel — איכות מחקר (דפוס)

מקור השראה: [Market Research Intelligence · MCP Market](https://mcpmarket.com/tools/skills/market-research-intelligence-1787987613965)  
(דף מקביל בלי הסיומת: [market-research-intelligence](https://mcpmarket.com/tools/skills/market-research-intelligence))  
**לא** `npx skills add` · **לא** פק חדש · **לא** תיקיות משקיעים כברירת מחדל.

גוף מלא של SKILL.md מהאתר: **«אין גוף»** (Vercel / Cloudflare checkpoint).  
מה הוטמע נשען על תיאור המוצר וה־FAQ הציבוריים מ־WebSearch/orchestra — לא על המצאת סעיפי SKILL.

## רעיון

לחתוך «research theater»: דוח מחקר חייב להיות **מכוון החלטה**, עם מקורות, גיל נתונים, וגם ראיות נגדיות — לא רק רשימת קישורים יפה.

## שערים במשרד VF

| שער | מה לעשות | כבר מיושר עם |
|---|---|---|
| ייחוס מקור | כל טענה → URL / paste בעלים / «אין גוף» | חוקת תזמורת · `TREND-EXPLORER` |
| גיל נתון | לציין תאריך מקור; אם ישן → «ייתכן שפג» | כרטיס מגמה · `תוקף` |
| ראיות נגדיות | לפחות מקור אחד שמערער / מגביל את המסקנה | LAST30 «מה דולג» |
| מבנה החלטה | סיכום → ממצאים → סיכונים/הסתייגויות → המלצה או «אין» | ארטיפקטי `sources/` |
| גודל שוק | אם נשאלים על TAM/SAM/SOM — **שתי שיטות** (top-down + bottom-up) או «אין מספר מאומת»; אסור מספר בודד בלי מקור | חוק «לא ממציאים ₪ / Insights» |
| תחרות | מציאות מוצר מול פער מיצוב — רק ממקור; בלי המצאת מחיר מתחרה | `vfsku` / `vfgrowth` בלי ₪ מומצא |

## מתי

- סקירת עונה / כניסה לקטגוריה חדשה (`vfseason` · `expert-trend-explorer`)
- השוואת פורמט תוכן או כלי (לפני הטמעה בפק)
- מעבר weekly links / best-skills כשצריך סינתזה ולא רק רשימה
- שאלת בעלים על שוק / מתחרים / גודל שוק (תעשייה — לא מחירון VF)

## פלט

ארטיפקט ב־`packages/vfresearch/sources/YYYY-MM-DD-<topic>-market-intel.md`:

```markdown
# Market intel · <topic> · YYYY-MM-DD

שאלה:
## ממצאים (עם מקור + תאריך)
## ראיות נגדיות / מגבלות
## סיכונים והסתייגויות
## המלצה למשרד (פק קיים) או «אין»
## מה דולג (חומה / בלי מקור / מנדט)
```

## נעול

- המצאת ₪ / Insights / גוף חסום
- תיקיית משקיע / check-size כברירת מחדל (רק אם הבעלים מבקש במפורש)
- התקנת Claude Code skill / Exa / vendor API על Cloud Agent
- פק מחקר חדש — רק `vfresearch` + פקים קיימים
- טענת «#1 בשוק» בלי מקור מאומת
