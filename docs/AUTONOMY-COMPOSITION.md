# VelvetOS Autonomy Composition

מטרה: להעלות אוטונומיה בלי לבנות runtime/queue/database/approval system נוסף.

ההטמעה נשענת על ה־Office Control Plane, ה־Living Studio וה־SoTs הקיימים. היא מאגדת את הרעיונות Next Best Action, Auto-Router, Missing Information Chaser, Waiting Room Manager, Approval Bundler, Exception Resolver, Context Pack Builder ו־Quiet Hours Executor לשמונה רכיבים משותפים במקום עשרים Skills נפרדות.

## רכיבים

1. `foundation-runtime-contract` — חוזה אחיד ל־`run_id`, `idempotency_key`, `correlation_id`, states, checkpoints ו־reconciliation לפני retry.
2. `router-context-engine` — routing + source-linked context pack מעל Universal Intake וה־SoTs הקיימים.
3. `blocker-waiting-engine` — waiting כחלק מנוהל: מה חסר, ממי, מה נחסם, מה הצעד הבא ומה הסיכון.
4. `project-lifecycle-engine` — intake → order/job → production → QA → completion במבנים הקיימים.
5. `approval-system` — projection שמאגד orange/red approvals; אינו מקור אמת חדש.
6. `reliability-exception-engine` — dead-letter, watchdog, QA gates, reconciliation ו־handoff.
7. `work-prioritization` — Next Best Action כ־projection, לא Skill/DB נפרד.
8. `background-executor-policy` — עבודה שקטה רק לפעולות פנימיות, הפיכות ובטוחות.

## קבצים

- config: `packages/velvetos/living-studio/AUTONOMY.json`
- CLI: `scripts/vf_autonomy.py`
- sensor: `scripts/check-vf-autonomy.py`
- projection: `packages/velvetos/living-studio/data/autonomy-latest.json`
- control plane: `office/control-plane.json`

## פקודות

```bash
python3 scripts/vf_autonomy.py status
python3 scripts/vf_autonomy.py next-action
python3 scripts/vf_autonomy.py blockers
python3 scripts/vf_autonomy.py approvals
python3 scripts/vf_autonomy.py context <id>
python3 scripts/vf_autonomy.py quiet-plan
python3 scripts/vf_autonomy.py snapshot
python3 scripts/vf_autonomy.py selftest
```

`context` מבצע retrieval קטן ומקושר למקורות מתוך inbox, followups, dead-letter, approvals, jobs ו־decisions. חוסר תוצאה = unknown; אסור להשלים עובדות.

`next-action` מעדיף החלטת approval קיימת, אחריה blocker בעל `next_action` קנוני, ורק אחר כך item פתוח ב־inbox. הוא לא ממציא impact/urgency/effort כשהנתונים אינם קיימים.

`quiet-plan` הוא projection בלבד. הוא לא שולח, לא מוחק, לא מחייב, לא משנה מחיר ולא מבצע WhatsApp ללקוח.

## חוזה אמינות

כל workflow שמשנה state צריך לשאת:

- `run_id`
- `idempotency_key`
- `correlation_id`
- state מפורש: `queued → running → waiting_approval → completed|failed`
- checkpoint אחרי שינוי state, ניסיון external tool או boundary של approval
- בדיקת המצב בפועל לפני retry
- retry אוטומטי אחד לכל היותר
- receipt עם `input_ref`, החלטה, פעולה, evidence ו־result_state

אין blind retry. אם אין דרך לבצע reconciliation, עוברים ל־exception/dead-letter במקום לנסות שוב אוטומטית.

## Business locks — Velvet Factory

- איסוף: שדרות בלבד.
- אין משלוח ארצי.
- CTA ציבורי: הודעה באינסטגרם.
- WhatsApp ללקוח: human send.
- אין המצאת ₪.
- אין המצאת Insights.
- אין destructive autonomy.

## QA

`scripts/check-vf-autonomy.py` נכלל אוטומטית ב־`scripts/check-all.py` כי הסוויטה מריצה כל `check-*.py`. הסנסור בודק את שמונת הרכיבים, חוזה idempotency/state/retry, business locks, projection write ownership ואת `vf_autonomy.py selftest`.
