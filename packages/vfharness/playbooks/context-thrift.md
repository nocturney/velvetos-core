# חיסכון הקשר — דפוס Headroom בלי runtime

מושב: ראש צוות (רתמה) + כל המושבים.  
מקור: [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) — **דפוס בלבד**, לא התקנה.  
לא פק חדש. לא orchestrator שני. Cloud Agent **לא** מריץ proxy מקומי.

## חוק אחד

לפני שמזרימים פלט כלי למודל — **סיכום בשיחה, מקור מלא בצד**.  
שחזור לפי דרישה (CCR). Failover ≠ המצאה — לא מדחיסים ₪, Insights, או גוף חסום.

## CCR — Compress · Cache · Retrieve

| שלב | מה | איפה |
|---|---|---|
| **Compress** | 5–15 שורות: מה רלוונטי לעבודה הנוכחית | תגובת הסוכן / checkpoint |
| **Cache** | מקור מלא | `vfharness/state/<task-id>.json` · Drive `create_file` · thread Gmail |
| **Retrieve** | שדה ספציפי חסר | קריאה נקודתית — לא dump חוזר |

דוגמה checkpoint:

```json
{
  "taskId": "inquiry-2026-08-31-abc",
  "status": "running",
  "summary": "פנייה ל-12 יחידות flexi; חומר PLA; איסוף שדרות",
  "artifacts": {
    "gmailThreadId": "…",
    "driveDocId": "…"
  }
}
```

## ContentRouter — לפי סוג artifact

| סוג | מה נכנס לשיחה | מה נשאר ב-cache |
|---|---|---|
| **Gmail thread** | subject · 3 הודעות אחרונות · CTA · שדות חסרים | thread מלא |
| **JSON / Sheets export** | שורות/שדות לעבודה · לא dump | קובץ / export מלא |
| **Canva / תמונה** | caption · edit URL · פורמט | metadata / export |
| **Drive doc** | כותרת · 10 שורות רלוונטיות | doc מלא |
| **WebSearch / orchestra** | 3 bullets + URL | לא גוף חסום — «אין גוף» |
| **Sensor output** | pass/fail + שורת שגיאה | stdout מלא ב-checkpoint |
| **273 rules warehouse** | **לא** — `@slug` מהשולחן בלבד | `vf-desk.json` |

## לפני grep ארוך

1. `python3 scripts/vfmem.py who <job>`
2. `packages/vfgraft/MAP.md` → 2–3 צמתים
3. רק אז מקור בפק

## גבול שלב — מתי לדחוס (phase-boundary)

מקור רעיון: [strategic-compact](https://mcpmarket.com/tools/skills/strategic-context-compaction-1787987503518) (Claude Code) — **דפוס בלבד**. לא מתקינים את הסקיל, לא `npx skills`, לא hook של Edit/Write, לא פקודת `/compact`. אצלנו הדחיסה = עדכון checkpoint והמשך מ-(P, Σ, O).

| מעבר שלב | לדחוס? | למה |
|---|---|---|
| מחקר → תכנון | כן | מחקר מנופח; התוכנית היא התמצית |
| תכנון → ביצוע | כן | התוכנית ב-checkpoint / קובץ; לפנות מקום לביצוע |
| ביצוע → בדיקה | אולי | לשמור אם הבדיקה נוגעת בקוד/שדות האחרונים; לדחוס בהחלפת פוקוס |
| דיבוג → משימה הבאה | כן | עקבות שגיאה מזהמים הקשר למשימה אחרת |
| **באמצע ביצוע** | **לא** | איבוד נתיבים, שדות חסרים ומצב חלקי עולה ביוקר |
| אחרי גישה שנכשלה | כן | לנקות dead-end לפני ניסיון חדש (בתוך תקרת 2 ניסיונות) |

### איך דוחסים אצלנו (בלי `/compact`)

1. כתוב/עדכן `vfharness/state/<task-id>.json` — `completed_steps` + `unresolved` (+ `execution_state` אם יש).
2. שמור ארטיפקטים כבדים ב-Drive / thread (CCR למעלה) לפני שמסכמים.
3. ב-turn הבא: קרא מדריך + checkpoint + תצפית אחרונה בלבד — לא replay של השיחה.
4. משפט פוקוס אופציונלי ב-`summary` / `next_step` (למשל: «ממשיכים הצעת מחיר — חסר חומר»).

משלים: `EMBED.md` § Compaction · `skillstate.md` · דפוס DeerFlow ב-`packages/vfe2b/DEER-FLOW-PATTERNS.md`.

## CacheAligner — בריף בוקר

`vfbriefux/MAIL.html` — template יציב; שדות volatile (תאריך, תור, שעות) **בסוף** או בבלוק נפרד.  
לא לערבב timestamp בתוך prefix שחוזר על עצמו — שובר cache ומייקר כל בריף.

## Output — פחות ceremony

- בלי «מצוין, בואו נ…» לפני כל צעד
- בלי להדפיס קוד/טקסט שהמשתמש כבר ראה
- צעד שגרתי (קריאת קובץ, sensor) → תשובה קצרה + מה השתנה
- שגיאה / החלטת ₪ → פירוט מלא

## Headroom כ-runtime (Mac בלבד, אופציונלי)

| סביבה | Headroom | למה |
|---|---|---|
| Cloud Agent | **לא** | sandbox — אין proxy מקומי |
| Mac מקומי | אופציונלי אחרי lead seat | `headroom wrap cursor` · MCP `headroom_compress` |

התקנה (Mac, לא בגיט):

```bash
uv tool install "headroom-ai[all]"
headroom doctor
headroom wrap cursor   # או proxy + הגדרות Cursor
```

`headroom learn --apply` → רק **preview**; תיקונים נכנסים ל-`AGENTS.md` ANTI-PATTERNS **ידנית** + סנסור.  
מפה: `packages/vfmcp/GAP.md` · חיסכון Cursor בלי Headroom: `vffcc/playbooks/cursor-thrift.md`.

## מה לא

| פעולה | למה |
|---|---|
| פק `vfheadroom` | embed בפלייבוק, לא פק |
| orchestrator / proxy על Cloud Agent | Cursor הוא המשרד |
| דחיסה שממציאה ₪ / Insights | חוק HQ |
| MCP Headroom + Gmail/Canva כפול | `docs/MCP-FIT.md` — אין כפילות |
