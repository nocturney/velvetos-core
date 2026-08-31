# DeerFlow 2.0 — דפוסים מוטמעים (לא runtime)

מקור: [bytedance/deer-flow](https://github.com/bytedance/deer-flow) (Deep Exploration and Efficient Research **Flow** — Super Agent harness 2.0, LangGraph + Gateway).  
נקרא: 2026-08-31.  
חוק: **מטמיעים דפוסים על `vfe2b` + `vfharness`. לא מתקינים DeerFlow.** Cursor הוא המשרד. `LOCK.md` נשאר.

DeerFlow ≠ BabyDeer (מוד AutoGPT ב־`LOCK.md`). DeerFlow הוא harness נפרד מבית ByteDance — אותו עיקרון נעילה: **אין runtime שני**.

## מה DeerFlow מציע (סיכום)

| יכולת DeerFlow | תיאור קצר |
|---|---|
| Skills | `SKILL.md` + טעינה פרוגרסיבית + `allowed-tools` |
| Sub-agents | delegation עם תקרות; לא fan-out על כל משימה |
| Session goals | `/goal` — תנאי סיום ל-thread + המשך עד מילוי |
| Context compaction | `/compact` — סיכום היסטוריה, שיח מלא נשאר |
| Sandbox | Docker / E2B / bash — סביבת הרצה לכל משימה |
| Long-term memory | DeerMem / mem0 / Honcho — facts בין סשנים |
| IM channels | Telegram, Slack, Feishu… |
| Gateway + cron | משימות מתוזמנות, PAT, observability |

## מה כבר קיים אצלנו

| DeerFlow | Velvet Factory HQ |
|---|---|
| Harness + loop bounds | `vfharness` · `AGENTS.md` |
| Sub-agents | Cursor Task · `crews/run.md` fan-out rules |
| Skills | `.cursor/skills/` · pack `SKILL.md` |
| Checkpoint | `packages/vfharness/state/*.json` |
| Verify before done | שדה `אימות` · `scripts/check-*.py` |
| Office routing | `vfmem` (גרף משרד — לא זיכרון משתמש) |
| Send | Gmail / IG דרך כלים · `constitution/SEND.md` |

## מה לקחנו (embed)

| דפוס DeerFlow | אצלנו | קובץ |
|---|---|---|
| Session goal | שדה `מטרה` בכרטיס משמרת + checkpoint אופציונלי | `crews/run.md` · `checkpoint.schema.json` |
| Sub-agent bounds | delegation רק לתועלת מקבילית/התמחות; fan-out ≤3 רק copy/covers | `crews/run.md` · `LOCK.md` |
| Progressive skills | קרא `SKILL.md` רק כשהמשימה דורשת; אל תטען את כל המחסן | `.cursor/skills/` · desk rule |
| allowed-tools (רעיון) | skill מציין כלים מותרים; שליחה/₪/Publish נשארים בחוקה | skill frontmatter (הנחיה) |
| Tool receipts | `אימות` מציין receipt: `message_id`, Canva URL, sensor name | `crews/run.md` |
| Context compaction | checkpoint מסכם `completed_steps`; לא לשחזר שיח שלם | `vfharness/EMBED.md` |
| Doctor / support bundle | `python3 scripts/check-all.py` לפני `worker_done` על שינוי קטלוג | sensors |

### מטרה (goal) — דוגמאות משרד

כותבים שורה אחת בעברית. נמחקת/מתקיימת לפני `worker_done`.

| משמרת | מטרה לדוגמה |
|---|---|
| פנייה | «Gmail reply נשלח בשרשור X» |
| בריף 07:00 | «send_message עם htmlBody תצוגה 3» |
| תוכן IG | «Publish MCP או failover Canva+Drive+Gmail על הדיסק» |
| מחקר | «ארטיפקט ב־`vfresearch/sources/` עם מקורות, בלי גוף חסום» |
| ₪ | **לא goal** — `decision_gate` לראש צוות |

כללי goal (מ DeerFlow, מותאם):

1. משתמש/ראש צוות מנצחים על goal חדש — לא continuation נסתר.
2. תקרה: 2 ניסיונות על אותה חסימה → `escalation` (כמו circuit breaker).
3. `worker_done` רק כשהמטרה **ומ** `אימות` מתקיימים.

### Sub-agents — מתי כן / לא

| כן (Cursor Task / מקביל) | לא |
|---|---|
| 2–3 וריאנטי copy/covers | ₪, שליחה, רישיון |
| מחקר מקבילי (WebSearch + orchestra) | fan-out על אותו שרשור Gmail |
| בדיקת pack נפרד (vfcanva brand-check) | BabyAGI / DeerFlow Gateway / swarm |

### אימות כ-receipt

```
אימות: Gmail reply message_id=18abc… · sensor check-vfe2b.py OK
אימות: Canva design_id=DAG… · Drive file … · #ממתין-ל-כלי-IG
אימות: python3 scripts/check-all.py — exit 0
```

בלי receipt בשם — לא `worker_done` על שליחה.

## מה לא מתקינים

| DeerFlow | למה |
|---|---|
| `make setup` / Gateway / Docker stack | runtime שני · `no-second-orchestrator` |
| Sandbox bash / E2B | רצפת הדפסה · שליחה דרך כלים |
| IM channels (Telegram, Slack…) | WhatsApp לקוח = אדם `050-2517000` |
| DeerMem / mem0 / Honcho | סיכון facts מומצאים על לקוח/₪; `vfmem` ≠ user memory |
| Scheduled cron tasks | בריף 07:00 = `vfops` + Calendar + Gmail |
| Agentic browser | נעול ב־`LOCK.md` (Self-operating computer) |
| «Ultra» sub-agent swarm | אוטונומיה מלאה — `LOCK.md` |

## קישורים פנימיים

- משמרת: [`crews/run.md`](crews/run.md)
- תזמורת קיימת: [`ORCHESTRATORS.md`](ORCHESTRATORS.md)
- נעילות: [`LOCK.md`](LOCK.md)
- רתמה: [`../vfharness/EMBED.md`](../vfharness/EMBED.md)
- שליחה: [`../../constitution/SEND.md`](../../constitution/SEND.md)

## בדיקה

```bash
python3 scripts/check-vfe2b.py
python3 scripts/check-all.py   # אחרי שינוי קטלוג
```
