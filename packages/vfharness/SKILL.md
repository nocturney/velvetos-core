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
6. **Human-visible output:** אם המשימה מייצרת prose/microcopy שנכתב או שוכתב ב־AI ושכריסטיאן/לקוח/קהל/שותף יקראו, `constitution/VISIBLE_TEXT.md` הוא gate חובה לפני `final`/send/publish/render. Route דרך `vfcopy`, surface נכון, reader-first, כלי הדומיין/כתיבה הרלוונטיים, Humanizer/AI-tells, fact/surface QA. אם אין הוכחת ביצוע על התוצר המדויק — `UNPROVEN`; completion אינו `worker_done` כ־final human output. Literal source IDs/hashes/logs/code אינם משוכתבים.
7. מכסת Grok ריקה + צריך IG חי → `playbooks/grok-failover.md` + `vfigos/LIVE-PACKET.md` לאדם.
8. הקשר כבד (thread, JSON, Drive dump) → `playbooks/context-thrift.md` — סיכום בשיחה, מקור ב-checkpoint.
9. **סוף יום** — `playbooks/daily-learning.md` + `vfops/hq/DAILY-RETRO.md` (מודול `office-learning`).
10. סוכן «נהיה גרוע» / כלי נדלג / זיכרון דולף → `playbooks/agent-architecture-audit.md` (דפוס buildwithclaude; בלי ECC install).
11. לפני בנייה / פק חדש / שינוי צינור → `playbooks/brainstorm-gate.md` (דפוס obra brainstorming; אישור אנושי לפני יישום).
12. באג / סנסור אדום / כשל כלי → `playbooks/systematic-debugging.md` (שורש לפני תיקון; בלי ניחוש).
13. תוכנית מימוש כתובה → `playbooks/writing-plans.md` (צעדים קטנים ובטוחים על SoT קיים; בלי ראנטיים שני).
13b. ביצוע תוכנית → `playbooks/executing-plans.md` (משימה אחת + אימות; עצירה על חוסם; בלי ניחוש).
13c. מילון תחום → `playbooks/domain-glossary.md` (TEAM / pipeline / owner-memory — בלי מונחים מומצאים).
14. Living Studio → `python3 scripts/vf_living_studio.py` (World Model / Pulse / Intake) — שכבת חיבור, לא Control Plane שני.

צינור יחיד נשאר: פנייה · שיחה · הצעה · הדפסה · איסוף.

## Human-visible completion invariant

טקסט אנושי שנכתב ב־AI אינו נחשב artifact גמור בגלל שהקובץ קיים או בגלל שסנסור wiring ירוק. לפני סגירה:

- `visible_text_gate: PASS` חייב להתייחס ל־surface הנכון ולגרסת הטקסט המדויקת כאשר קיים digest/hash.
- כלי שלא רלוונטי יכול להיות `N/A` עם סיבה; כלי רלוונטי לא יכול להיות מדולג כדי להגיע ל־PASS.
- שינוי מהותי בטקסט אחרי gate מבטל את ה־PASS ואת האישורים התלויים בו.
- CI/eval/skill existence מוכיחים יכולת/wiring בלבד; **לא** ביצוע של candidate.
- עד ששכבת execution receipts יכולה להוכיח invocation ברמת הכלי, self-reported stage flags אינם שווי ערך ל־`EXECUTION_PROVEN`; downstream publish/send gate צריך להישאר fail-closed במקום שדורש receipt מחייב.

זה משתמש ב־checkpoint / execution_state הקיימים של `vfharness`; אין approval database או runtime שני.

## אסור

סוכן HQ לא לוחץ Publish / Send / Boost / DM. אדם כן יכול לפרסם חי בזמן failover עם LIVE-PACKET. אין להמציא ₪ / Insights, אין CrewAI/AutoGPT, אין פק כפול, אין להסתיר סנסור אדום. אין להציג human-visible AI prose כ־final עם `visible_text_gate=UNPROVEN`.

ראה `hq/PLAYBOOK.md`, `EMBED.md`, `constitution/VISIBLE_TEXT.md`.

## סולם הסלמה הדרגתי (2026-09-07)

`scripts/vf_graceful_escalation.py` — 4 שלבים לפני הסלמה לאדם, במקום עצירה בינארית. פירוט מלא: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).

## שימוש בלולאת הסלמה (2026-09-07)

משימות ארוכות ב-`vfcopy` / `vfconvert` / `vfsales` עוברות דרך `run_ladder` מ-`scripts/vf_graceful_escalation.py` (retry → fallback → downgrade → escalate) במקום עצירת ניסיון שני.
