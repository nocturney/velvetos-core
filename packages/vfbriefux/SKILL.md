# vfbriefux — חבילת בריף הבוקר

מושב: ראש צוות. מחקר פורמט + חריצים. לא מייל חי.

הבריף הקיים (01–07) הוא החבילה. `hq/PACKET.md` מתאר את החריצים אחרי שתילת השיתוף.

**MORNING GREEN:** בריף הבוקר הקנוני: `MORNING-GREEN.html` + `render_morning_green.py` + `MORNING-GREEN.md`, עם נכסי CID ב־`assets/morning-green/`. `מתוזמן` דורש ראיית schedule חיה; `מאושר` אינו תזמון.
**HTML LEGACY/OTHER OWNER SURFACES:** `MAIL.html` + `render_mail.py` נשארים זמינים ל־research/weekly/legacy (`htmlBody`, `cid:`).
**DESIGN:** `hq/DESIGN.md` + `DESIGN-EMBED.md` — how the brief should look (tokens from MAIL.html).  
**DIAGRAM:** `hq/DIAGRAM-MAKER.md` + `hq/diagram-svg-template.html` — דיאגרמות לווין (openclaw diagram-maker). `render_mail.py --diagram pipeline|slots`. לא מחליף את המייל.  
**CHARTS:** `hq/CHARTS.md` — מספרים שנמדדו (lieflat-charts pattern · Glance לבריף). לא מחליף טבלאות במייל.  
**UI SYSTEM:** `hq/UI-SYSTEM.md` — internal product/UI design intelligence with Hebrew RTL + accessibility + Velvet constraints (UI/UX Pro Max pattern).  
**UI AUDIT:** `hq/UI-AUDIT.md` — Hallmark-style anti-slop audit; Taste-style creative spike is optional and gated, never default.  
**PORTLETS:** `hq/PORTLETS.md` — שמות דאשבורד עתידי על אותם חריצים (NetSuite/Salesforce), לא מבנה שני.  
**GROWTH BRIEF:** `hq/GROWTH-BRIEF.md` — 07:00 readiness Decision Pack (`vf_organic_growth.py`) consumed by the 09:00 Morning Brief. אישור ≠ פרסום. לא מחליף חריצי 01–07.
טיוטת effective-html: `hq/brief-email.html` — רפרנס/Wireframe; מקור [effective-html](https://github.com/plannotator/effective-html). Mobbin חסום → עובדים על הקובץ הזה או על דיאגרמת SVG.

לא ממציאים Insights. לא ממציאים מחיר.  
כריכות בגוף המייל (`cid:` בחריץ 07).  
HQ שולח `htmlBody` תצוגה 3 אל `nocturney@gmail.com` דרך המסלול הקנוני. Grok הוא גיבוי אופציונלי, לא sender authority. אין שליחה ללקוח.

**BENTO (דק שבועי, לא אימייל):** `hq/BENTO.md` + `scripts/vf_weekly_deck.py` — בונה JSON `bento/slides` מנתונים אמיתיים (LEARNINGS/LAST30/רטרו). נפתח ידנית פעם בשבוע בדפדפן, לא נכנס לצינור השליחה היומי.

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.
