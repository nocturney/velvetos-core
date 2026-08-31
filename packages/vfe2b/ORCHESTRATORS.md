# vfe2b — שכבת תזמורת (orchestrators)

לא פק חדש. לא ADE שני. מקור: [andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) — **194** רשומות (נקרא 31.8.2026).

הרשימה מחליטה *על מה* סוכן עובד, *מתי*, *איפה*, ו*מה קורה לתוצר*. אצלנו זה כבר `crews/run.md` + `vfharness`. מטמיעים דפוסים. לא מתקינים את הכלים.

מפה מכונה: [`orchestrators.json`](orchestrators.json) · דוח: [`docs/ORCHESTRATORS.md`](../../docs/ORCHESTRATORS.md).

## מה לקחנו (ייעול משמרת)

| דפוס | מקור | אצלנו עכשיו |
|---|---|---|
| תיק אחד + שלושה מצבי סיום | Orca | `worker_done` / `escalation` / `decision_gate` |
| דופק working / blocked / idle | herdr | שדה `דופק` בכרטיס |
| תכנון → סקירה → ביצוע | Fusion, ivy-tendril | לולאת `vfharness` על צוות קיים אחד |
| אימות נפרד לפני «בוצע» | kodo | שדה `אימות` — סנסור או בדיקת שדה. בלי זה אין `worker_done` |
| ארטיפקט על הדיסק | tutti, Crewplane | שדה `ארטיפקט` — נתיב או «אין» |
| תקרה ללולאה + קבלה | fractal, MartinLoop | 2 ניסיונות ואז הסלמה. checkpoint = קבלה |
| יציאה כשבאמת נגמר | ralph-claude-code | `worker_done` רק אחרי אימות |
| הקשר טרי בניסיון חוזר | ralphex | קוראים שוב את המקור. לא מנחשים |
| תיבה → משמרת אחת | Taskuary | בריף בוקר ממיין, ואז צוות אחד |
| מכונת מצבים בלי ערוץ צד | NEEDLE | הכרטיס הוא התיאום |
| סיבוב מכסה | Claudexor | מכסת Grok → כלי HQ באותו תור (`SEND.md`) |
| שער אדם | 5dive, humanlayer, paperclip | וואטסאפ אדם · ₪ לראש צוות |

## מה לא מתקינים

TUI/tmux/worktree multiplexers (`amux`, `dmux`, `claude-squad`…).  
ADE שולחני (`Emdash`, `Garcon`, `Orca` כהתקנה).  
נחילי 20–41 סוכנים (`loki-mode`, `ClawTeam`).  
לולאת Ralph בלי אדם על ₪ או שליחה.  
עוזר אישי תמידי / OpenClaw / גשר טלגרם / אוטו־CRM.

Cursor הוא המשרד. `LOCK.md` + `skipFamilies` ב־`orchestrators.json`.

## איך רצים אחרי הייעול

1. `@vfe2b run <עבודה>` — תיק אחד, צוות קיים אחד.
2. ממלאים כרטיס עם `מצב` + `דופק` + `אימות` + `ארטיפקט`.
3. בריף 07:00: אחרי המיון — HQ שולח ג׳ימייל (`send_message`).
4. פנייה בשרשור נקוב: HQ `reply` כשהטיוטה מוכנה. וואטסאפ לקוח נשאר אדם.
5. תוכן: `vfigos/SEND.md` — כלי Publish או Canva+Drive+Gmail באותו תור. לא ממציאים שעלה לפיד.
6. `decision_gate` = ₪ לראש צוות בלבד. לא «מחכים לגרוק שישלח».

## בדיקה

```bash
python3 scripts/check-vfe2b.py
```
