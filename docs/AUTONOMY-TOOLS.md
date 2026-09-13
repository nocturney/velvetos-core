# כלי אוטונומיה — נוספו 2026-09-07

ארבע תוספות שכל סוכן (Cursor / Grok / ChatGPT / Gemini / Perplexity) צריך להכיר לפני עבודה במשרד.
לא פק חדש, לא סוכן חדש. סקריפטים בתוך packs קיימים.

כשמנהל ראשי אינו זמין: קרא קודם [`docs/FAILOVER.md`](FAILOVER.md) (מקור אמת + דוח השתלטות + בריף לבעלים).

| כלי | מיקום | פותר | הרצה |
|---|---|---|---|
| CI סנסורים | [`.github/workflows/check-all.yml`](../.github/workflows/check-all.yml) | בדיקה אוטומטית בכל push/PR — לא רק ידנית | רץ אוטומטית ב-GitHub |
| סינון agent rules | [`scripts/vf_relevant_agents.py`](../scripts/vf_relevant_agents.py) | 283 `.mdc` → 50 רלוונטיים ל-VF; לא מוחק, רק מסנן | `python3 scripts/vf_relevant_agents.py` |
| לופ מדידה→למידה | [`packages/vfinsights/scripts/vf_insights_loop.py`](../packages/vfinsights/scripts/vf_insights_loop.py) | vfinsights בלי מדידה בפועל («אין ספירה» תמיד) | `python3 packages/vfinsights/scripts/vf_insights_loop.py --init` ואז למלא CSV אמיתי |
| חיפוש סמנטי מקומי | [`packages/vfmem/scripts/vf_semantic_search.py`](../packages/vfmem/scripts/vf_semantic_search.py) | vfmem היה מפת טקסט בלבד; זה TF-IDF אמיתי, offline; כתיבה אטומית ל־pkl | `python3 packages/vfmem/scripts/vf_semantic_search.py --build` |
| פריפלייט שליחה | [`scripts/vf_send_preflight.py`](../scripts/vf_send_preflight.py) | desk+מפתח לפני Gmail/IG/API; יציאה 2=failover | `python3 scripts/vf_send_preflight.py --gate instagram` |
| סולם הסלמה | [`packages/vfharness/scripts/vf_graceful_escalation.py`](../packages/vfharness/scripts/vf_graceful_escalation.py) | לולאת retry בינארית → ladder של retry → fallback → downgrade → safe ruling opt-in → escalate | `python3 packages/vfharness/scripts/vf_graceful_escalation.py --self-test` |
| חיישן execution discipline | [`scripts/check-vfharness-execution-discipline.py`](../scripts/check-vfharness-execution-discipline.py) | מוכיח ש־safe ruling עובד רק עם guard מפורש, ו־blocked/malformed ruling נכשל סגור | `python3 scripts/check-vfharness-execution-discipline.py` |

## כללים

- שום מדד לא מומצא. `vf_insights_loop.py` קורא רק שדות שמולאו ידנית מ-Instagram Professional — שדה ריק נשאר ריק.
- שום API בתשלום. כל התוספות רצות מקומית (TF-IDF, CSV, JSON state) — אין מפתח, אין חיוב.
- לא מוחקים כלום. `vf_relevant_agents.py` רק כותב אינדקס; קבצי `.mdc` המקוריים נשארים.
- `safe_ruling` הוא **לא** דרך לעקוף authority: רק החלטה מקומית, הפיכה, בלי security/permissions/external-side-effect gate. required sensor/receipt אדום נשאר אדום.
- פורמט ruling קנוני: `Ruling: <decision> — <why> — <cost_if_wrong>`.
- לפני Task 1 בתוכנית מרובת משימות, `playbooks/executing-plans.md` דורש evidence-bearing preflight על shared files/interfaces + self-consistency.
- שינוי executable behavior / bugfix / automation משתמש ב־RED → GREEN → REFACTOR כשאפשר לבדוק התנהגות; אין test theater ל־prose/static config.
- CHANGELOG הוא מקור האמת. כל שינוי עתידי בכלים האלה — לתעד שם קודם.

בדיקה קנונית: `python3 scripts/check-all.py` — הסוויטה מריצה אוטומטית גם את `check-vfharness-execution-discipline.py` כי כל `check-*.py` תחת `scripts/` נכלל.
