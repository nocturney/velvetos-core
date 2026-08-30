# vfharness — רתמת סוכן למשרד

`Agent = Model + Harness`. המודל חושב. הרתמה קובעת מה מותר, מה נבדק, ומה נשאר אחרי הסשן.

הפלייבוק שהבעלים העלה (אוגוסט 2026) מתאר שש שכבות. אצלנו **לא** מרימים מסגרת סוכנים שנייה. מטמיעים את השכבות על הפאקים, החוקה, והסקריפטים שכבר רצים.

## שש שכבות אצלנו

| שכבה | תפקיד | איפה אצלנו |
|---|---|---|
| Guides | מונע כשל ידוע לפני ריצה | `AGENTS.md`, חוקה, `SKILL.md` |
| Sensors | תופס כשל אחרי ריצה | `scripts/check-*.py` |
| Loop | תכנון → ביצוע → בדיקה → תיקון / הסלמה | `LOOP.md` + כישורי היום |
| Memory | הסשן שוכח; הקובץ זוכר | `state/` + ארטיפקטים בפק |
| Permissions | המודל לא אוכף בטיחות | `PERMISSIONS.md` + חוקי השולחן |
| Observability | אפשר לאבחן כשל | `CHANGELOG.md`, `ORIGIN.md`, סנסורים |

## מה כן / מה לא

כן: קובץ מדריך, סנסור חישובי, תקציב ניסיונות, נקודת ביקורת, שער אישור, יומן.

לא: CrewAI / AutoGPT / שופט-LLM לכל פלט, שליחה חיה, ₪ מומצא, פק חדש לכל «סוכן» מהשיתוף.

ראה [`LOCK.md`](LOCK.md).

## קבצים

| קובץ | תפקיד |
|---|---|
| [`layers.json`](layers.json) | מפת שכבות, קריא למכונה |
| [`LAYERS.md`](LAYERS.md) | אותה מפה בעברית |
| [`EMBED.md`](EMBED.md) | איך מריצים את הרתמה על פק קיים |
| [`LOOP.md`](LOOP.md) | לולאה + גבולות + הסלמה |
| [`PERMISSIONS.md`](PERMISSIONS.md) | Allow / Ask / Deny |
| [`CHECKLIST.md`](CHECKLIST.md) | מוכנות ייצור (12) |
| [`hq/PLAYBOOK.md`](hq/PLAYBOOK.md) | נוהל ראש צוות |
| [`scripts/check-vfharness.py`](../../scripts/check-vfharness.py) | סנסור הרתמה |
| [`scripts/check-all.py`](../../scripts/check-all.py) | כל הסנסורים |

## איך מפעילים

ב-Cursor:

```
@vfharness
@vfharness checkpoint <task>
@vfharness escalate <why>
```

או: קרא `AGENTS.md`, הרץ את הלולאה ב-`LOOP.md`, בדוק ב-`python3 scripts/check-all.py`.

`python3 scripts/check-vfharness.py` — צפי: `OK harness layers=6 sensors=…`.
