# מפת הפעלה לראש צוות · Chief of Staff

סטטוס: **docs-only** · 2026-09-15  
ריפו: `nocturney/velvetos-core`  
Tenant ייחוס: Velvet Factory · שדרות · `@velvets_cloud`

חבילת הידע הזו היא **מפת קריאה** מעל מקורות הסמכות שכבר קיימים.  
היא **אינה** מקור אמת, אינה Control Plane שני, ואינה מאשרת LIVE בלי ראיה.


## מצב נוכחי (רענון 2026-09-26)

- **מסירה:** `office/control/HANDOFF.json` הוא ערוץ המסירה היחיד (`vf_control_plane.py handoff`). ה־CLI הישן מוקפא, ושום מסמך/skill/workflow לא מפנה אליו (נאכף בסנסור).
- **קצבי workflows (#357):** `vfmedia-intake` `23 */3 * * *`, `jobs-write-through` `53 1-23/3 * * *` (8 ביום כל אחד, מיושר למה ש־GitHub באמת מריץ), control plane `0 2,8,14,20 * * *` (05:00/11:00/17:00/23:00 IDT, מחוץ לחלונות Office Loop 10:30/18:30), research 04:30 UTC, pulse כל שעה.
- **Pins (#355):** בסיס Docker `python:3.12.14-slim-trixie@sha256:…` וחבילות מוצמדות; Actions `checkout`/`setup-python`/`upload-artifact` @v7, `google-github-actions/auth@v3`.
- **Instagram:** `instagram-read-smoke.yml` (04:41 UTC, קריאה בלבד) מאמת MCP מרוחק: 401 בלי טוקן, profile, media, insights, בלי כלי כתיבה מטעים.
- **למידה:** `vf_learning.py ingest-ci` רושם ריצות main שנכשלו כ־learning candidates תחת `packages/vfharness/state/learning-candidates/`. מועמד ≠ חוק; קידום דרך האוטומציות / הבעלים.
- **Frontend:** `nocturney/velvetos-velvet-factory` מסונכרן לתבנית (union), `core.lock.yml` עוקב אחרי core `main` בכוונה. CI של ה־frontend צריך את `VELVETOS_CORE_READ_TOKEN` (ליבה פרטית).
- **OpenPost:** paused (publishing frozen), staging v6.2.0, LIVE לא מאומת. בבריף מסומן "מושהה".
- **Research Seat** הוא סמכות התזמון (due 44h / stale >52h); אין טיימר חיצוני.

## למי זה

סוכן `@chief-of-staff` (מושב ראש צוות ב־`.cursor/vf-desk.json`) שצריך לתאם פקים, משרד ושערים — בלי להמציא SoT, מחיר, Insights, לקוח או Origin slug.

## סדר קריאה

1. **`README.md` (קובץ זה)** — מה מותר לעשות עם החבילה.
2. **`SOT-INDEX.md`** — לכל דומיין, איזה קובץ מנצח.
3. **`GATES-AND-ESCALATION.md`** — מתי לבצע, מתי להכין, מתי להסלים לכריסטיאן.
4. **`LOOPS.md`** — לולאות יום/שבוע ו־workflows.
5. **`PACKS-CATALOG.md`** — מלאי פקים + מצביעי סמכות.
6. **`SYSTEM-MAP.md`** — מפת הפעלה מלאה, כולל מתחים מתועדים ו־UNKNOWN.

לפני עבודה חיה: `packages/velvetos/PROJECT-REQUEST-GATE.md` + `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`.  
לפני חיפוש במחסן Agency: `packages/vfgraft/MAP.md` ואז 2–3 צמתים.  
לשאלה «מי מטפל»: `python3 scripts/vfmem.py who <job>`.

## חוקים קשיחים (לא להרחיב כאן)

- לא ממציאים ₪ / Insights / לקוחות / Origin slugs / LIVE.
- לא יוצרים SoT מקביל.
- לא מדפיסים מ־HQ. לא אוטו־DM. לא בוסט בלי ראש צוות.
- `PUBLIC_CURRENT_CTA` = הודעת Instagram. WhatsApp `050-2517000` = `BUSINESS_CONTACT_RECORD` בלבד.
- אם לא ברור — `UNKNOWN` / `UNPROVEN` / `BLOCKED`. לא ניחוש.

סמכות: `AGENTS.md` · `constitution/` · `office/control/POLICY.md`. אם מסמך זה סותר אותם — **הם מנצחים**.

## מה החבילה הזו לא עושה

- לא משנה התנהגות runtime, סנסורים, חוקה או אינטגרציות חיות.
- לא מחליפה את `office/control-plane.json`.
- לא מחליפה את `packages/manifest.json` כקטלוג מכונה.
- לא מאשרת שכלי MCP חי בסשן הנוכחי — ראה `CAPABILITIES.json` / HANDOFF / pulse כראיות **שמורות בריפו**, לא כקריאה חיה.

## כרטיס תפעול קצר

| מצב | פעולה |
|---|---|
| עבודה פנימית שגרתית | לבצע (GREEN) לפי `office/control/POLICY.md` |
| תוכן / מדיה / לוח | לבצע ולדווח בבריף (YELLOW) |
| הודעה חיצונית / טענה ציבורית / שינוי מדיניות | להכין בלבד (ORANGE) |
| מחיר, תשלום, מחיקה, Print מ־HQ, חסם בלי failover | כריסטיאן (RED) |
| כלי נפל | failover באותו תור (`constitution/ORCHESTRA.md`) — לא סרק, לא המצאה |

## ראיות מול כוונות

קיום קובץ / skill / workflow ≠ LIVE.  
`prepared` ≠ `scheduled` ≠ `publishRequested` ≠ `published_verified`.  
ראיה: sensor, receipt, `list_media`/`get_media`, או `sync-receipt.json`.
