# לולאת משרד — כל פק נצרך, לא נקרא

מושב: **תפעול**. לא פק חדש.  
המכונה: `LOOP.json` + `python3 scripts/vfops_loop.py`.  
הקטלוג לבד = כישלון. הבריף והמסירה חייבים **למשוך** שורות מהפקים.

## כל בוקר 06:15–07:00 (Asia/Jerusalem)

הפרדה קשיחה: **run** (משימות) → **brief** (הרכבה) → **check**/CI (תקינות).  
`run` לא מפעיל `check-all` (רקורסיה עם `check-vfops-loop`). לא מרנדר G005/Canva אוטומטית.

```
python3 scripts/vfops_loop.py run
python3 scripts/vfops_loop.py brief --write
python3 packages/vfbriefux/render_mail.py packages/vfops/hq/brief-YYYY-MM-DD.json \
  -o packages/vfops/out/BRIEF-YYYY-MM-DD.html
```

שליחת המייל: `constitution/SEND.md` — תצוגה 3 אל `nocturney@gmail.com` דרך `python -m vfops.gmail_brief_send` או 3־צעדי MCP (`docs/SEND-BRIEF-MCP.md`). לא `LOAD_FROM_FILE`.  
המשימה הזו **לא** שולחת (בריף 6.9 כבר יצא).

## מה נמשך אוטומטית

| חריץ | מקור |
|---|---|
| 01 | `GATES.json` שערי לחיצה + מחיר דחה + G004 · `vfops_loop.py gate` — אדם, לא וואטסאפ · Organic Growth [אישור/עריכה/דחייה] (`vf_organic_growth.py`) — אישור ≠ פרסום |
| 02 | `vfcost.py brief` + `vfbooks.py brief` — עלות חומר + חוב/חשבונית חסרה פנימי (בלי ₪ מכירה, בלי מייל גבייה) + `vfbooks/data/orders.json` / Invoice4U snapshot |
| 03 | `vfsku.py brief` + `vfsku.py scan` + `vfsku/week.md` + `vfprod.py brief` + `vfprod.py print-done` |
| 04 | `vfgrowth/hq/FOLLOWER-GROWTH.md` + `PROFILE-TO-WHATSAPP` + `vf_organic_growth.py brief` + `vfbiz/out/week.md` + B2B נעול + וואטסאפ |
| 05 | CLI אמיתי מ-24ש (`cli-runs.jsonl`) + סיכום `consumer-runs` מ־`run`, או «אין חדש במשרד» + שורות **פער** לפק יומי שלא הורץ. `on-content`/`on-inquiry` לא נחשבים פער בוקר. לא קטלוג מ-`research.md` · כספת מדיה `vfmedia.py validate` (תפעול קולט; GrokBot Drive MCP; Cursor סכמה) |
| 06 | `vfinsights` loop → `LEARNINGS.md` כשיש CSV; אחרת «אין ספירה». מדדים חלשים = לוג פנימי, לא אשמת בעלים |
| 07 | כיתובי `vfcopy` + `G004-STORIES-FIX.md` + `vfgrowth/HANDOFF-he.md` + נתיב `PREFLIGHT.md`. פער סוכנות = שורת פער למשרד |

## מסירה לסטודיו

```
python3 scripts/vfops_loop.py handoff
```

פותחים `vfgrowth/HANDOFF-he.md` — חבילת היום (עכשיו G004).  
בלי ארטיפקט `packages/vfgrowth/preflight/<id>.md` עבור = לא משבצים. אל תפנה לכריסטיאן על מדדים חלשים.

## Office Control Plane

לא מתזמן שני. מאחד מקורות אמת + watchdog:

```
python3 scripts/vf_control_plane.py status
python3 scripts/vf_control_plane.py watchdog
python3 scripts/vf_control_plane.py handoff
```

מפה: `office/control-plane.json` · מצב: `office/control/` · נכנס לבריף 01 (החלטות בעלים / dead-letter / WIP→finished) בלי רעש תפעולי.

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
