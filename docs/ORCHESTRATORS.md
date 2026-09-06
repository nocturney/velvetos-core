# Agent orchestrators fit — Velvet Factory

מקור: [andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators)  
ספירה: **194** רשומות (README, נקרא 31.8.2026).  
הטמעה: [`packages/vfe2b/`](../packages/vfe2b/) — שכבה על הצוותים הקיימים, לא פק חדש.  
מפה: [`packages/vfe2b/orchestrators.json`](../packages/vfe2b/orchestrators.json) · נוהל: [`ORCHESTRATORS.md`](../packages/vfe2b/ORCHESTRATORS.md).  
בדיקה: `python3 scripts/check-vfe2b.py`.

הרשימה היא כלי *תזמורת* (מה רץ, מתי, איפה, מה קורה לתוצר) — לא בוטים חד-תכליתיים ולא ספריות זיכרון/MCP.  
רוב הפריטים הם משרד קידוד שני (tmux, worktrees, ADE, נחילים, OpenClaw). **Cursor כבר המשרד.** מטמיעים דפוסים. לא מתקינים runtime.

## מה כן אצלנו

| דפוס | מקור | נפל ל־ |
|---|---|---|
| משמרת: תיק אחד, שלושה מצבים | Orca | `vfe2b/crews/run.md` |
| דופק working / blocked / idle | herdr | שדה `דופק` בכרטיס |
| תכנון → סקירה → ביצוע | Fusion, ivy-tendril | לולאת `vfharness` |
| אימות נפרד לפני סיום | kodo | שדה `אימות` |
| ארטיפקט על הדיסק | tutti, Crewplane | שדה `ארטיפקט` |
| תקרת לולאה + קבלה | fractal, MartinLoop | 2 ניסיונות · checkpoint |
| יציאה כשנגמר באמת | ralph-claude-code | `worker_done` אחרי אימות |
| הקשר טרי בניסיון | ralphex | קוראים שוב את המקור |
| תיבה → משמרת אחת | Taskuary | `crews/morning-brief.md` |
| מכונת מצבים | NEEDLE | מצב אחד בכרטיס |
| סיבוב מכסה | Claudexor | `SEND.md` + grok-failover |
| שער אדם / תקציב | 5dive, humanlayer, paperclip | וואטסאפ אדם · ₪ לראש צוות |
| שערי YAML + אישור אדם | Archon (patterns) | `vfharness` · `אימות` · `decision_gate` — **לא** install |

הפעלה: `@vfe2b run <עבודה>` או skill `vf-run`.

## ייעול תהליכים שהוטמע באותו יום

- בריף 07:00: HQ **שולח** ג׳ימייל אחרי המיון (`send_message`).
- פנייה בשרשור נקוב: HQ **`reply`** כשהטיוטה מוכנה. וואטסאפ לקוח נשאר אדם.
- תוכן: שליחה דרך `vfigos/SEND.md` (כלי או Canva+Drive+Gmail). לא ממציאים שעלה לפיד.
- `decision_gate` = ₪ לראש צוות. לא שער «חכה לגרוק».
- כרטיס משמרת דורש דופק + אימות + נתיב ארטיפקט.

## מה דולג בכוונה

- Multiplexers / ADE: `amux`, `dmux`, `claude-squad`, `Emdash`, `Garcon`, התקנת Orca.
- **Archon** (coleam00) — harness/CLI/Docker שני; דפוסי שערי אימות בלבד (2026-09-05).
- נחילים: `loki-mode` (41), `ClawTeam`, `Agent Teams`.
- לולאה בלי אדם: `bernstein`, Ralph unattended על ₪ או שליחה (`archon-ralph-dag`).
- עוזר אישי / OpenClaw / טלגרם / CRM אוטומטי (`takopi`, `denchclaw`).
- Resting / archived (נבדק במקור 28.7.2026).

פירוט: [`packages/vfe2b/LOCK.md`](../packages/vfe2b/LOCK.md).

## Later (ראש צוות)

GitHub Action רשמי (`claude-code-action` ודומיו) — רק אם ראש צוות פותח Actions על הריפו. לא עבודת רצפה.
