# vfe2b — שכבת תזמורת (orchestrators)

לא פק חדש. לא ADE שני. מקור: [andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) — **194** רשומות (נקרא 31.8.2026).

הרשימה מחליטה *על מה* סוכן עובד, *מתי*, *איפה*, ו*מה קורה לתוצר*. אצלנו זה כבר `crews/run.md` + `vfharness`. מטמיעים דפוסים. לא מתקינים את הכלים.

מפה מכונה: [`orchestrators.json`](orchestrators.json) · דוח: [`docs/ORCHESTRATORS.md`](../../docs/ORCHESTRATORS.md) · DeerFlow patterns: [`DEER-FLOW-PATTERNS.md`](DEER-FLOW-PATTERNS.md).

## מה לקחנו (ייעול משמרת)

| דפוס | מקור | אצלנו עכשיו |
|---|---|---|
| תיק אחד + שלושה מצבי סיום | Orca | `worker_done` / `escalation` / `decision_gate` |
| דופק working / blocked / idle | herdr | שדה `דופק` בכרטיס |
| תכנון → סקירה → ביצוע | Fusion, ivy-tendril | לולאת `vfharness` על צוות קיים אחד |
| אימות נפרד לפני «בוצע» | kodo | שדה `אימות` — סנסור או בדיקת שדה. בלי זה אין `worker_done` |
| ארטיפקט על הדיסק | tutti, Crewplane | שדה `ארטיפקט` — נתיב או «אין» |
| תקרה ללולאה + קבלה | fractal, MartinLoop | 2 ניסיונות ואז הסלמה. checkpoint = קבלה |
| תכנון מקדים + שער עמיד | Open Multi-Agent | `planned_steps` + `gate` ב-checkpoint; `oma-patterns.md` |
| יציאה כשבאמת נגמר | ralph-claude-code | `worker_done` רק אחרי אימות |
| הקשר טרי בניסיון חוזר | ralphex | קוראים שוב את המקור. לא מנחשים |
| תיבה → משמרת אחת | Taskuary | בריף בוקר ממיין, ואז צוות אחד |
| מכונת מצבים בלי ערוץ צד | NEEDLE | הכרטיס הוא התיאום |
| סיבוב מכסה | Claudexor | מכסת Grok → כלי HQ באותו תור (`SEND.md`) |
| שער אדם | 5dive, humanlayer, paperclip | וואטסאפ אדם · ₪ לראש צוות |
| Connector priority + seat scope | LobeHub ToolsEngine | `vfmcp/GAP.md` — מושב → namespace → failover |
| White-box memory (לא צ'אט גלובלי) | LobeHub Personal Memory | `vfharness/state/` + checkpoint schema |
| Agent Groups / Project משותף | LobeHub Pages | fan-out max 3 על `vfcopy`/`vfcovers` בלבד |
| Schedule registry (לא cron אוטונומי) | LobeHub Operator | `vfops/ROUTINE.md` + בריף 07:00 + `decision_gate` |
| setup / teardown / run ל-workspace | [Superset](https://github.com/superset-sh/superset) lifecycle scripts | Cloud Agent `environment.json` — לא IDE שני |
| Session goal | DeerFlow `/goal` | שדה `מטרה` בכרטיס · checkpoint `goal` |
| Sub-agent bounds | DeerFlow task | fan-out ≤3 · לא על ₪/שליחה |
| Tool receipts | DeerFlow verification | `אימות` + message_id / design URL |
| YAML phases + validation + human approve | [Archon](https://github.com/coleam00/Archon) (2026-09) | `vfharness` loop · `אימות` · `decision_gate` · תיק משמרת אחד — **לא** install Archon |

## מה לא מתקינים

TUI/tmux/worktree multiplexers (`amux`, `dmux`, `claude-squad`…).  
ADE שולחני (`Emdash`, `Garcon`, `Orca`, `Superset` כהתקנה).  
**Archon** (CLI/Docker/Web harness builder) — דפוסי שערי אימות בלבד; לא runtime שני.  
**LobeHub** (Docker / Vercel / IM Gateway / marketplace 10k MCP) — דפוסים בלבד.  
נחילי 20–41 סוכנים (`loki-mode`, `ClawTeam`).  
לולאת Ralph בלי אדם על ₪ או שליחה (`archon-ralph-dag` ודומיהם).  
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
