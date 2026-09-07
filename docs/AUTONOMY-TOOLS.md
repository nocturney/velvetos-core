# כלי אוטונומיה — נוספו 2026-09-07

ארבע תוספות שכל סוכן (Cursor / Grok / ChatGPT / Gemini / Perplexity) צריך להכיר לפני עבודה במשרד.
לא פק חדש, לא סוכן חדש. סקריפטים בתוך packs קיימים.

| כלי | מיקום | פותר | הרצה |
|---|---|---|---|
| CI סנסורים | [`.github/workflows/check-all.yml`](../.github/workflows/check-all.yml) | בדיקה אוטומטית בכל push/PR — לא רק ידנית | רץ אוטומטית ב-GitHub |
| סינון agent rules | [`scripts/vf_relevant_agents.py`](../scripts/vf_relevant_agents.py) | 283 `.mdc` → 50 רלוונטיים ל-VF; לא מוחק, רק מסנן | `python3 scripts/vf_relevant_agents.py` |
| לופ מדידה→למידה | [`packages/vfinsights/scripts/vf_insights_loop.py`](../packages/vfinsights/scripts/vf_insights_loop.py) | vfinsights בלי מדידה בפועל («אין ספירה» תמיד) | `python3 packages/vfinsights/scripts/vf_insights_loop.py --init` ואז למלא CSV אמיתי |
| חיפוש סמנטי מקומי | [`packages/vfmem/scripts/vf_semantic_search.py`](../packages/vfmem/scripts/vf_semantic_search.py) | vfmem היה מפת טקסט בלבד; זה TF-IDF אמיתי, offline; כתיבה אטומית ל־pkl | `python3 packages/vfmem/scripts/vf_semantic_search.py --build` |
| פריפלייט שליחה | [`scripts/vf_send_preflight.py`](../scripts/vf_send_preflight.py) | desk+מפתח לפני Gmail/IG/API; יציאה 2=failover | `python3 scripts/vf_send_preflight.py --gate instagram` |
| סולם הסלמה | [`packages/vfharness/scripts/vf_graceful_escalation.py`](../packages/vfharness/scripts/vf_graceful_escalation.py) | לולאה בינארית (2 ניסיונות → עצור) → 4 שלבים לפני הסלמה לאדם | `python3 packages/vfharness/scripts/vf_graceful_escalation.py --self-test` |

## כללים

- שום מדד לא מומצא. `vf_insights_loop.py` קורא רק שדות שמולאו ידנית מ-Instagram Professional — שדה ריק נשאר ריק.
- שום API בתשלום. כל התוספות רצות מקומית (TF-IDF, CSV, JSON state) — אין מפתח, אין חיוב.
- לא מוחקים כלום. `vf_relevant_agents.py` רק כותב אינדקס; קבצי `.mdc` המקוריים נשארים.
- CHANGELOG הוא מקור האמת. כל שינוי עתידי בכלים האלה — לתעד שם קודם.

בדיקה: `python3 scripts/check-all.py` — 23/23 עברו אחרי הטמעת כל התוספות (2026-09-07).
