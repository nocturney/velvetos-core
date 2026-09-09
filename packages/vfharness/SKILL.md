# vfharness — רתמת המשרד

מושב: ראש צוות (תשתית לכל המושבים). לא שולח אינסטגרם / ג׳ימייל / DM.

הפק הזה הוא ה-outer harness — לא סוכן מוצר חדש ולא ראנטיים שני. Cursor כבר המשרד.

## מתי

כשל שחוזר, משימה רב-שלבית, בדיקת מוכנות, כשהמשתמש אומר רתמה / harness / AGENTS.md, או **מכסת Grok נגמרה** (failover + פרסום חי דחוף).

## שרשרת

1. קרא `AGENTS.md` (המדריך מנצח את השיחה).
2. תכנן צעדים קצרים על **פק קיים**.
3. בצע. אחרי כל שינוי קטלוג/כלל — `python3 scripts/check-all.py`.
4. כשל סנסור → תקן פעם אחת → אם נכשל שוב, הסלם עם `templates/escalation.md`.
5. כתוב נקודת ביקורת ב-`state/<task-id>.json` לפני סגירת סשן ארוך. משימה ארוכה: כל צעד = \(P,\Sigma,O\) — `playbooks/skillstate.md` (לא replay שיחה).
6. מכסת Grok ריקה + צריך IG חי → `playbooks/grok-failover.md` + `vfigos/LIVE-PACKET.md` לאדם.
7. הקשר כבד (thread, JSON, Drive dump) → `playbooks/context-thrift.md` — סיכום בשיחה, מקור ב-checkpoint.
8. **סוף יום** — `playbooks/daily-learning.md` + `vfops/hq/DAILY-RETRO.md` (מודול `office-learning`).
9. סוכן «נהיה גרוע» / כלי נדלג / זיכרון דולף → `playbooks/agent-architecture-audit.md` (דפוס buildwithclaude; בלי ECC install).
10. לפני בנייה / פק חדש / שינוי צינור → `playbooks/brainstorm-gate.md` (דפוס obra brainstorming; אישור אנושי לפני יישום).
11. באג / סנסור אדום / כשל כלי → `playbooks/systematic-debugging.md` (שורש לפני תיקון; בלי ניחוש).
12. תוכנית מימוש כתובה → `playbooks/writing-plans.md` (צעדים קטנים ובטוחים על SoT קיים; בלי ראנטיים שני).
13. Living Studio → `python3 scripts/vf_living_studio.py` (World Model / Pulse / Intake) — שכבת חיבור, לא Control Plane שני.

צינור יחיד נשאר: פנייה · שיחה · הצעה · הדפסה · איסוף.

## אסור

סוכן HQ לא לוחץ Publish / Send / Boost / DM. אדם כן יכול לפרסם חי בזמן failover עם LIVE-PACKET. אין להמציא ₪ / Insights, אין CrewAI/AutoGPT, אין פק כפול, אין להסתיר סנסור אדום.

ראה `hq/PLAYBOOK.md` ו-`EMBED.md`.

## סולם הסלמה הדרגתי (2026-09-07)

`scripts/vf_graceful_escalation.py` — 4 שלבים לפני הסלמה לאדם, במקום עצירה בינארית. פירוט מלא: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).

## שימוש בלולאת הסלמה (2026-09-07)

משימות ארוכות ב-`vfcopy` / `vfconvert` / `vfsales` עוברות דרך `run_ladder` מ-`scripts/vf_graceful_escalation.py` (retry → fallback → downgrade → escalate) במקום עצירת ניסיון שני.
