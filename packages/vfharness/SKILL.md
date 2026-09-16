# vfharness — רתמת המשרד

מושב: ראש צוות (תשתית לכל המושבים). לא שולח אינסטגרם / ג׳ימייל / DM.

הפק הזה הוא ה-outer harness — לא סוכן מוצר חדש ולא ראנטיים שני. Cursor כבר המשרד.

## מתי

כשל שחוזר, משימה רב-שלבית, בדיקת מוכנות, כשהמשתמש אומר רתמה / harness / AGENTS.md, או **מכסת Grok נגמרה** (failover + פרסום חי דחוף).

## שרשרת

1. קרא `AGENTS.md` (המדריך מנצח את השיחה).
2. תכנן צעדים קצרים על **פק קיים** וקשר ל־Spec/אישור קנוני כשיש שינוי מהותי.
3. בצע. אחרי כל שינוי קטלוג/כלל — `python3 scripts/check-all.py`.
4. כשל/פער → ladder קנוני: retry → fallback → downgrade scope → **safe ruling רק אם מקומי+הפיך וללא gate** → escalation. Required sensor/receipt/human/constitutional gate לעולם אינם נעקפים ב־ruling.
5. כתוב נקודת ביקורת ב-`state/<task-id>.json` לפני סגירת סשן ארוך. משימה ארוכה: כל צעד = \(P,\Sigma,O\) — `playbooks/skillstate.md` (לא replay שיחה).
6. **Human-visible output:** אם המשימה מייצרת prose/microcopy שנכתב או שוכתב ב־AI ושכריסטיאן/לקוח/קהל/שותף יקראו, `constitution/VISIBLE_TEXT.md` הוא gate חובה לפני `final`/send/publish/render. Route דרך `vfcopy`, surface נכון, reader-first, כלי הדומיין/כתיבה הרלוונטיים, Humanizer/AI-tells, fact/surface QA. אם אין הוכחת ביצוע על התוצר המדויק — `UNPROVEN`; completion אינו `worker_done` כ־final human output. Literal source IDs/hashes/logs/code אינם משוכתבים.
7. מכסת Grok ריקה + צריך IG חי → `playbooks/grok-failover.md` + `vfigos/LIVE-PACKET.md` לאדם.
8. הקשר כבד (thread, JSON, Drive dump) → `playbooks/context-thrift.md` — סיכום בשיחה, מקור ב-checkpoint.
9. **סוף יום** — `playbooks/daily-learning.md` + `playbooks/learning-lifecycle.md` + `vfops/hq/DAILY-RETRO.md`; observation נשאר candidate עד שיש evidence/gate מתאים.
10. סוכן «נהיה גרוע» / כלי נדלג / זיכרון דולף → `playbooks/agent-architecture-audit.md` (דפוס buildwithclaude + codebase navigability; בלי ECC install).
11. לפני בנייה / פק חדש / שינוי צינור → `playbooks/brainstorm-gate.md` (דפוס obra brainstorming; אישור אנושי לפני יישום).
12. באג / סנסור אדום / כשל כלי → `playbooks/systematic-debugging.md` (אבחון מדורג; שחזור ושורש לפני תיקון; בלי ניחוש).
13. תוכנית מימוש כתובה → `playbooks/writing-plans.md` (Spec כסמכות, steps קטנים, dependencies/producer-consumer, בלי runtime שני).
13a. רב־סשן אחרי החלטות → `playbooks/to-spec.md` (סינתזת החלטות + seams; בלי ראיון חדש; בלי npx; שמירה ב־`state/`).
13b. ביצוע תוכנית → `playbooks/executing-plans.md`: evidence-bearing preflight לפני Task 1; safe rulings במקום stalls כשבטוח; fan-out רק למשימות עצמאיות; fan-in עם integration proof; fresh whole-plan review לפני claim.
13c. מילון תחום → `playbooks/domain-glossary.md` (TEAM / pipeline / owner-memory — בלי מונחים מומצאים).
14. Living Studio → `python3 scripts/vf_living_studio.py` (World Model / Pulse / Intake) — שכבת חיבור, לא Control Plane שני.
15. שינוי קוד/bugfix/automation מהותי → `playbooks/implementation-discipline.md` — think first, boring simplicity, surgical diff, proof-before-code; executable behavior משתמש ב־RED → GREEN → REFACTOR כשאפשר לבדוק בפועל. אין test theater ל־prose/static config.
16. שינוי מהותי רגיל → fresh-context reviewer אחד לפי `playbooks/critique-review.md` עם Goal+Spec+diff+proof בלבד, לא כל history. שינוי רגיש/רחב → high-risk mode עם שני reviewers עצמאיים + deterministic proof; receipt תחת `state/reviews/` נבדק ע״י `check-review-convergence.py`.
17. worker-to-worker בלבד → `playbooks/terse-worker-output.md` — פלט קצר ומבני; לעולם לא על טקסט אנושי.
18. Agent/MCP/rules surface → `AGENT-SURFACE-SECURITY.md` + `python3 scripts/check-agent-surface-security.py` (AgentShield pattern).
19. מעבר עבודה בין harnesses → `vfmem/HANDOFF.md` + `python3 scripts/vf_handoff.py new|ack|consume|reject|doctor`; handoff הוא context, לא authority.
20. לפני טענה ש״הוטמע/רץ״ על worker/automation/connector → `python3 scripts/check-runtime-doctor.py --strict`. `check-all` בודק רק את חוזה ה־runtime offline; strict דורש receipts אמיתיים.
21. סקירת בריאות מערכת → `python3 scripts/check-velvet-health.py`; הפלט דטרמיניסטי ומורכב מחיישנים, בלי ציוני LLM מומצאים.
22. תחזוקת Skills/docs → `python3 scripts/check-skill-health.py` + `python3 scripts/check-living-docs.py`; warnings הם חומר לתיקון/קונסולידציה, לא success-rate מומצא.
23. שינוי קוד/אוטומציה/מדיניות/אינטגרציה מהותי → `playbooks/engineering-delivery-chain.md`: החלטה → spec → tickets אנכיים → branch → implementation+proof → review איכות **וגם** התאמה ל-spec → PR/CI → runtime verification. לא Issue tracker שני.
24. יצירה/עריכה מהותית של `AGENTS.md` / `SKILL.md` / rules / prompts → `playbooks/agent-instruction-qa.md` + `python3 scripts/check-skill-health.py`; פחות הוראות, סמכות אחת, trigger/action/evidence מפורשים.
25. שלב שבאמת רק אדם יכול לבצע → `playbooks/human-step-wizard.md`: השלם קודם כל מה שאפשר אוטונומית, בקש פעולה אנושית מינימלית אחת, ואז אמת והמשך בעצמך.

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

## סולם הסלמה הדרגתי

`scripts/vf_graceful_escalation.py` — ladder של retry → fallback → downgrade scope → **safe ruling אופציונלי** → escalation. `safe_ruling` הוא fail-closed: ללא `safe_to_rule=True` הוא לא רץ. פירוט מלא: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).

## שימוש בלולאת הסלמה

משימות ארוכות ב־`vfcopy` / `vfconvert` / `vfsales` ממשיכות להשתמש ב־`run_ladder`. callers קיימים נשארים backward-compatible; safe ruling הוא keyword-only opt-in. required sensor/receipt ו־authority gates נשארים מחוץ לסמכות ruling.
