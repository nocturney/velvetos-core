# HQ Research Routine · מחקר לפי צורך

מושב: **מחקר/אורקסטרציה**. אין כאן שעון עצמאי ואין Research Seat יומי.
החוקרים משתמשים ב־skills וב־packs הקיימים בלבד; אין runtime שני ואין `npx skills` על Cloud Agent.

חוקה: `constitution/ORCHESTRA.md` · scheduler חי: `automation/chatgpt/manifest.json` · חוזה מחקר: `packages/vfresearch/DAILY.md`.

Current skill/playbook map: `vf-best-skills` · `vf-weekly-links` · `vf-last30` · `vf-daily-learning`. Public CTA stays governed by `constitution/PUBLIC_CTA.md`; research does not change it.

## חוקים קשיחים

- מחקר מתחיל משאלה, החלטה, צורך תוכן או gate קונקרטי — לא מהגעת שעה בלוח.
- אין Insights / ₪ / גוף חסר־מקור מומצאים.
- אין auto-upgrade, auto-DM, Boost/Ads, Print מ־HQ או פק חדש לכל רעיון.
- כלי נפל → failover למקור אחר; אם אין evidence אמיתי, blocker אמיתי.
- artifact חדש/מרוענן שומר `as_of`, `provenance`, `uncertainty`, `refresh_target`.
- אחרי שינוי קטלוג/כלל/פק מריצים את החיישנים הרלוונטיים.

## מחקר עסקי / תוכן

כאשר יש צורך אמיתי, משתמשים ב־`DAILY.md` כ־playbook on-demand. WebSearch/WebFetch ומקורות ציבוריים/ראשוניים הם ברירת המחדל. תוצר שימושי יכול לעדכן `packages/vfops/data/research.md`; אין חובה לייצר artifact יומי כשאין שאלה.

## Upstream / toolchain

בעת החלטת כלי או update:
- `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json`
- `python3 scripts/vfresearch_cadence.py review-routing` רק כשנדרש review עדכני.
- recommendation אחת: update / wait / review / ignore.
- אימוץ הוא שלב נפרד עם compatibility/smoke evidence.

## Best Skills

`BEST-SKILLS.md` + `BEST-SKILLS.json` + `TIMER.md` הם on-demand. אין ~48h clock; גיל `lastPass` לבדו אינו trigger.

## Inspiration / Print · Demand · Sound

`WEEKLY.md`, `LINKS.json` ו־`hq/PRINT-DEMAND.md` נשארים playbooks למחקר כאשר משימה מצדיקה אותם; הכותרת “weekly” היא provenance היסטורי ולא יוצרת recurring job. `hq/MAKERWORLD-SCAN.md` נשאר שער מקור→רישיון→slice→test לפני promotion; אין SKU/מחיר רק כי נמצא דגם.

## Last30 / community research

`vf-last30` ו־`hq/LAST30.md` רצים לפי דרישה בלבד ומותר להם להסתיים ב־nothing-solid.

## אחרי פרסום חי

מעדכנים `vfinsights` רק מנתוני Instagram מאומתים או מקור בעלים מפורש. בלי reach אמיתי — אין ספירה.

## סוף יום

`VelvetOS Office Loop` של 18:30 הוא ה־recurring surface היחיד כאן לרטרו/למידה כאשר יש חומר חדש. Promote רק עובדות עמידות ל־owner-memory; אין דוח “בריאות” לבעלים לשם עצם הדוח.

## GitHub verifier

`.github/workflows/velvetos-research.yml` הוא verifier/index path להרצה ידנית אחרי מחקר רלוונטי. אין לו schedule והוא אינו מייצר גוף מחקר.

## מיפוי

| צורך | Skill / playbook |
|---|---|
| מחקר עסקי/תוכן | `DAILY.md` / research specialists |
| skill/tool landscape | `vf-best-skills` / `BEST-SKILLS.md` |
| inspiration / print-demand | `WEEKLY.md` / `PRINT-DEMAND.md` |
| community / last30 | `vf-last30` |
| רטרו/למידה | `vf-daily-learning` via Office Loop 18:30 |
| זיכרון/ניתוב | `vf-hq-memory` |

## Structured demand adapter

**DORMANT:** `DEMAND-SIGNALS.md` נשאר dormant עד שיש provider אמיתי. אין scheduler עבורו ואין דיווח על “missing” כשאין provider.
