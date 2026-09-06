# Market Research Intelligence — סקירת הטמעה · 2026-09-05

מושב: ייצור · `@research-synthesist`  
מקור שנשלח: https://mcpmarket.com/tools/skills/market-research-intelligence-1787987613965  
דף מקביל: https://mcpmarket.com/tools/skills/market-research-intelligence  
סטודיו: Velvet Factory · שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`  
לא פק חדש. לא `npx skills add`. לא marketplace של Claude Code על Cloud Agent.

## מצב גוף

| ניסיון | תוצאה |
|---|---|
| WebFetch / curl לדף | **אין גוף** — Vercel Security Checkpoint |
| WebSearch על אותו slug / כותרת | תיאור מוצר + Key Features + Use Cases (ציבורי) |

לא הומצא תוכן SKILL.md מלא. ההטמעה היא **דפוסי איכות** מהתיאור הציבורי בלבד.

## מה הסקיל מציע (ממקור ציבורי)

- דוחות מכווני החלטה (סיכונים, הסתייגויות, המלצות) — לא «research theater»
- ייחוס מקור קפדני + סימון נתונים ישנים
- ראיות נגדיות / contrarian
- גודל שוק TAM/SAM/SOM בשיטות top-down ו־bottom-up
- מיפוי תחרות (מציאות מוצר מול פער מיצוב)
- תיקיות משקיע (fund history / stage / check size) — **לא ל־VF יומי**

## מיפוי למשרד

| דפוס | לאן | דין |
|---|---|---|
| ייחוס + גיל נתון + נגדי + מבנה החלטה | `packages/vfresearch/hq/MARKET-INTEL.md` | **הוטמע** |
| כרטיס מגמה כבר דורש מקור/תוקף | `experts/TREND-EXPLORER.md` | חיזוק הפניה |
| מחקר 30 יום | `hq/LAST30.md` | משלים — engagement; MARKET-INTEL = איכות סינתזה |
| גודל שוק / תחרות עם ₪ | `vfcost` / `vfsku` | רק מספר מאומת; אחרת `X ₪` / «אין» |
| תיקיית משקיע | — | **דולג** — לא מנדט VF |
| התקנת skill / Exa API | — | **דולג** — Cloud Agent |

## מה הוטמע היום

1. פלייבוק `packages/vfresearch/hq/MARKET-INTEL.md`
2. רישום ב־`LINKS.json` (`mcpmarket-market-research-intelligence`)
3. שורת מיפוי ב־`BEST-SKILLS.md` + הפניה ב־`SKILL.md` / Trend Explorer
4. רשומת `embedded` ב־`BEST-SKILLS.json`

## אסור שנשמר

אין ₪ · אין Insights · אין גוף מומצא לדף החסום · אין Print מ־HQ · אין אוטו־DM · אין runtime שני.
