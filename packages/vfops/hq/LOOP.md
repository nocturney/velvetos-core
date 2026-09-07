# לולאת משרד — כל פק נצרך, לא נקרא

מושב: **תפעול**. לא פק חדש.  
המכונה: `LOOP.json` + `python3 scripts/vfops_loop.py`.  
הקטלוג לבד = כישלון. הבריף והמסירה חייבים **למשוך** שורות מהפקים.

## כל בוקר 07:00 (Asia/Jerusalem)

```
python3 scripts/vfops_loop.py brief --write
python3 packages/vfbriefux/render_mail.py packages/vfops/hq/brief-YYYY-MM-DD.json \
  -o packages/vfops/out/BRIEF-YYYY-MM-DD.html
```

שליחת המייל: `constitution/SEND.md` — `htmlBody` תצוגה 3 אל `nocturney@gmail.com`.  
המשימה הזו **לא** שולחת (בריף 6.9 כבר יצא).

## מה נמשך אוטומטית

| חריץ | מקור |
|---|---|
| 02 | `vfcost.py brief` — עלות חומר חיה (בלי ₪ מכירה) |
| 03 | `vfsku.py brief` + `vfsku/week.md` |
| 04 | `vfgrowth/hq/FOLLOWER-GROWTH.md` + `vfbiz/out/week.md` + B2B נעול + וואטסאפ |
| 05 | CLI אמיתי מ-24ש (`cli-runs.jsonl`) או «אין חדש במשרד» + שורות **פער** לפק שלא הורץ. לא קטלוג מ-`research.md` |
| 06 | `vfinsights` — «אין ספירה» עד סנאפשוט / טוקן. מדדים חלשים = לוג פנימי, לא אשמת בעלים |
| 07 | כיתובי `vfcopy` + `G004-STORIES-FIX.md` + `vfgrowth/HANDOFF-he.md` + נתיב `PREFLIGHT.md`. פער סוכנות = שורת פער למשרד |

## מסירה לסטודיו

```
python3 scripts/vfops_loop.py handoff
```

פותחים `vfgrowth/HANDOFF-he.md` — חבילת היום (עכשיו G004).  
בלי ארטיפקט `packages/vfgrowth/preflight/<id>.md` עבור = לא משבצים. אל תפנה לכריסטיאן על מדדים חלשים.

## מלאי

```
python3 scripts/vfops_loop.py inventory
```

כל תיקייה תחת `packages/` חייבת שורה ב־`LOOP.json`. חסר = סנסור אדום.

## סטטוס עברית + שבוע

```
python3 scripts/vfops_loop.py status
python3 scripts/vfops_loop.py weekly
```

## רף סוכנות

בריף בטון סוכנות (`STUDIO.md` / `INSTANCE.md` / `ORCHESTRA.md`).  
לפני שיבוץ — שער עריכה + `PREFLIGHT.md`. נכשל-סגור = חסום. משבצות בלי לשאול. לא חצי-פק. לא «רמה נמוכה» לבעלים.

## נעול

אין ₪ מומצא. אין Insights מומצאים. אין Publish IG מכאן. סטוריז = instagram.com.  
`vfcost` CLI חי מ־main — `python3 scripts/vfcost.py brief` בחריץ 02. לא ממציאים ₪ מכירה.
