# DeerFlow 2.0 — קליטת דפוסים היסטורית + מועמד להשוואה מלאה

מקור: [bytedance/deer-flow](https://github.com/bytedance/deer-flow) (Super Agent harness, LangGraph + Gateway).  
מחקר דפוסים ראשוני: 2026-08-31. בדיקת התאמת הגרסה הנוכחית: 2026-10-08.

**COMPETITOR_NEUTRAL_ADMISSION_V1:** ההחלטה מאוגוסט "דפוסים בלבד" הייתה גבול שימוש שגרתי, ולא הוכחת עליונות של המימוש שלנו. אין לפסול DeerFlow בגלל חפיפה, השקעה קיימת, או `no-second-orchestrator`. הוא זכאי למבחן השוואתי הוגן כאפשרות **להחליף את ליבת הסוכנים בשלמותה**, להחליף תת־מערכות או להשתלב כהרכבה. `no-second-orchestrator` ממשיך לאסור deployment מקביל ב־production ללא קידום/authority, אך **אינו** מונע רישום או LAB מבודד אחרי admission. DeerFlow ≠ BabyDeer; אין כאן אישור להפעלת swarm בלתי מבוקר.

רישום השוואה: `docs/implementation/office-v2/phase2/candidate-registry-v0.json#candidate-deerflow`; מסלול `agent-runtime` נשמר בתור `queued_challengers` עד לבחינת מקום הוגנת. נסרק/תועד, **לא** הותקן, לא הושווה ב־Golden Fixtures ולא נבחר כמנצח.

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
| Context compaction | checkpoint מסכם `completed_steps`; לא לשחזר שיח שלם; גבול שלב (לא באמצע ביצוע) | `vfharness/EMBED.md` · `context-thrift.md` § phase-boundary |
| Doctor / support bundle | `python3 scripts/check-all.py` לפני `worker_done` על שינוי קטלוג | sensors |

### מטרה (goal) — דוגמאות משרד

כותבים שורה אחת בעברית. נמחקת/מתקיימת לפני `worker_done`.

| משמרת | מטרה לדוגמה |
|---|---|
| פנייה | «Gmail reply נשלח בשרשור X» |
| Morning Brief (manual/event-driven) | «send_message עם htmlBody תצוגה 3» |
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

### אימות כ-receipt

```
אימות: Gmail reply message_id=18abc… · sensor check-vfe2b.py OK
אימות: python3 scripts/check-all.py — exit 0
```

בלי receipt בשם — לא `worker_done` על שליחה.

## מה לא מפעילים בייצור ללא שער קידום

| DeerFlow | למה |
|---|---|
| `make setup` / Gateway / Docker stack | לא כ־runtime production נוסף ללא קידום. LAB מבודד אפשרי אחרי admission; אין פסילה מראש · `no-second-orchestrator` |
| Sandbox bash / E2B | רצפת הדפסה · שליחה דרך כלים |
| IM channels (Telegram, Slack…) | WhatsApp לקוח = אדם `050-2517000` |
| DeerMem / mem0 / Honcho | סיכון facts מומצאים על לקוח/₪; `vfmem` ≠ user memory |
| Scheduled cron tasks | Morning Brief אינו cron; `vfops` + Calendar + Gmail פועלים רק בהפעלה ידנית/אירועית, ללא readiness cutoff שעוני |
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
