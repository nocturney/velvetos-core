# חריצי בריף — בלי תבנית מתחרה

הבריף החי כבר מסודר 01–07 (תצוגה 3 vfops). לא מחליפים מבנה. רק ממלאים שדות מהשרשרת כשיש מקור.

| חריץ קיים | מה נכנס מהשיתוף |
|---|---|
| 01 קודם החלטה | מחיר חסר, אישור תוכן, היילייטס — כן/לא/דחה · **שערי לחיצה** `GATES.json` · **אותות רטרו** מ־`vfops/data/retro-signals.json` (`kind` ל־slot 01; `RETRO-SIGNALS.md`) |
| 02 כסף בעבודה | הזמנות, חוב, שולם מ־`vfbooks/data/orders.json` + Invoice4U snapshot (אין ספירה אם ריק; לא inbox) + שורת עלות חומר `python3 scripts/vfcost.py brief` + ספר `python3 scripts/vfbooks.py brief` דרך `vfops_loop.py` (בלי ₪ מכירה, בלי מייל גבייה) |
| 03 מה להדפיס ולפרסם | מוכנים להדפסה + שעות תור מאומתות + הצעות `#vfresearch` + מדף `python3 scripts/vfsku.py brief` + `python3 scripts/vfsku.py scan` + `vfsku/week.md` + צי `python3 scripts/vfprod.py brief` + `python3 scripts/vfprod.py print-done` דרך `python3 scripts/vfops_loop.py brief` + חנות מחר `python3 scripts/vfsku.py shop` |
| 04 איך הסטודיו מרוויח | `#vfbiz` נעול + `vfbiz/out/week.md` + `FOLLOWER-GROWTH` + `PROFILE-TO-WHATSAPP` היילייטס/וואטסאפ, בלי ₪ מומצא |
| 05 משרד | CLI אמיתי מ-24ש (`vfops_loop` → `data/cli-runs.jsonl`) או **אין חדש במשרד**. פק יומי/`on-content` שלא הורץ = שורת פער. `research.md` = תזמורת 06:15 בלבד, לא פעילות מזויפת · **אותות רטרו** slot 05 מ־`retro-signals.json` |
| 05a זיכרון | `packages/vfops/data/owner-memory.md` — תמצית רטרו (יומי או catch-up). קרא לפני מילוי 05 |
| 06 מה קורה בעמוד | `#vfinsights` אחרי פרסום+24ש. לא ממציאים. מדדים חלשים = לוג פנימי, לא אשמת בעלים ולא «רמה נמוכה» |
| 07 פיד בסוף | כריכות `#vfcovers`, `#משובץ` `#לא-זז` `#לא-בוסט` + נתיב `PREFLIGHT.md`. פער סוכנות = שורת **פער** למשרד, לא חדשות רעות לבעלים |

כותרת קבועה: ולווט פקטורי · סטודיו להדפסות תלת־ממד · שדרות · בריף הבוקר.  
סגירה: איסוף משדרות · בלי סיסמאות, קודי אימות או שמות לקוחות מיותרים.

HTML: `packages/vfbriefux/MAIL.html` (תצוגה 3). לא שולחים טקסט.  
בפיילאובר Grok: HQ ממלא JSON → `render_mail.py` → `send_message` + `htmlBody` + כריכות `cid`.  
כש־Grok חי: Grok שולח את אותו HTML. HQ לא לוחץ Publish לאינסטגרם.

Portlets (שמות לדאשבורד עתידי על אותם חריצים): `packages/vfbriefux/hq/PORTLETS.md`.
