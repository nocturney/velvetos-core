# רתמה · Harness Engineering ב-HQ

תאריך קריאה: 30 באוגוסט 2026  
מקור: קובץ שהבעלים העלה — *Production Agent Engineering Practice 2026 — Harness Engineering* (`harness_final_ea2c.pdf`).  
המסמך מצהיר שהוא ליקוט עצמאי, לא מזוהה עם Google / OpenAI / Anthropic / HashiCorp ולא מאושר על ידם.

סוכן = מודל + רתמה. המודל מספק חשיבה. הרתמה מספקת מדריכים, סנסורים, לולאה חסומה, זיכרון, הרשאות, ויומן.

## למה זה שייך למשרד

המשרד כבר סוכן: Cursor + 273 חוקים + פקים + כלים חיים. בלי רתמה כל סשן מתחיל מאפס, אותם כשלים חוזרים (₪, שליחה, פק כפול, גוף חסום ש«הושלם»).

לא בונים CrewAI. לא פק לכל שכבה. מטמיעים על הקיים — כמו שתילת שיתוף ChatGPT, בניגוד לקטלוגים `vfe2b` / `vfagents` שרק ממפים רשימות חיצוניות.

## מה הוטמע

| שכבה | קובץ ראשי |
|---|---|
| Guides | [`AGENTS.md`](../AGENTS.md) |
| Sensors | [`scripts/check-all.py`](../scripts/check-all.py) |
| Loop | [`packages/vfharness/LOOP.md`](../packages/vfharness/LOOP.md) |
| Memory | [`packages/vfharness/state/`](../packages/vfharness/state/) |
| Permissions | [`packages/vfharness/PERMISSIONS.md`](../packages/vfharness/PERMISSIONS.md) |
| Observability | `CHANGELOG.md` + סנסורי trip-wire (₪, שליחה, פק לא מוכר) |

מפה למכונה: [`packages/vfharness/layers.json`](../packages/vfharness/layers.json).  
נוהל: [`packages/vfharness/EMBED.md`](../packages/vfharness/EMBED.md).  
פיילאובר מכסת Grok (+ פרסום חי דחוף בידי אדם): [`docs/GROK-FAILOVER.md`](GROK-FAILOVER.md).  
מצע ביצוע ארוך (SKILLSTATE, arXiv 2608.26263): [`packages/vfharness/playbooks/skillstate.md`](../packages/vfharness/playbooks/skillstate.md) — \(A_t=(P,\Sigma,O)\); בלי runtime שני.

## מה דולג מהפלייבוק

- שופט-LLM כשער (יקר ולא דטרמיניסטי) — אצלנו סנסור חישובי קודם.
- תקציב דולר למשימה כמספר ₪ — אין המצאת מחיר. Treg: מחיר קטלוג לפני קריאה.
- גרף ידע / מחסן וקטורים כזיכרון ראשון — קובץ JSON מספיק.
- מסגרת סוכנים שנייה.

## בדיקה

```bash
python3 scripts/check-vfharness.py
python3 scripts/check-all.py
```

אין UI חי. אין דפדפן לאמת שליחה. העקביות היא מול המדריך, הנעילות, והמניפסט.
