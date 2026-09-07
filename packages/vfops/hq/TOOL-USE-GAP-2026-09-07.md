# פער שימוש בכלים · 7.9.2026

מושב: **תפעול**. תלונת כריסטיאן ~08:27 Asia/Jerusalem: הכלים מוטמעים בקטלוג אבל **לא נראים בפלט החי**; סטוריז אחרונות מתחת לרף סוכנות.

לא ממציאים ₪. לא ממציאים Insights. לא Publish מכאן.

מקורות שנקראו היום: `LOOP.json` · `vfops_loop.py assemble()` · בריף `hq/brief-2026-09-07.json` · `research.md` · `HANDOFF-he.md` · `EDIT-GATE.md` · `VOICE.md` · `vfcopy/G004.md` · `vfcanva/jobs/G004.md` · Canva MCP `get-design-content` על `DAHUaUo3bAk` + `DAHUacDGv9U` · `instances/velvet-factory/constitution/STUDIO.md`.

## הטבלה

| כלי / פק | מחובר לבריף / סטודיו / צמיחה? | ראיה חיה אחרונה | פער | תיקון |
|---|---|---|---|---|
| `vfcopy` | בריף 07 קורא `G004.md` / `G003.md` / `G005-d12b.md`. סטודיו: `HANDOFF` מדביק G004. | 6.9: `VOICE.md` + כיתוב G004. 7.9 בריף: הוק ישן. Canva חי: פריימים עדיין חידה+מגבלה. | הלולאה **קוראת** כיתוב; הסטוריז החיים לא עברו סיפור-מוצר. הוק+פריים נשארו קטלוג/מגבלה. | `G004-STORIES-FIX.md` = הדבקה חיה. `ig-stories.md` = נייבי-זהב + VOICE. |
| `vfcovers` | LOOP `on-content` → `g005/compose_slides.py`. חריץ 07 מזכיר «שער עריכה». | G005 `compose_slides.py` (קרוסלה פיד, לא סטוריז G004). | לא הורץ ל-G004. סטוריז יצאו בלי מעבר compose. | שער קשיח: בלי PNG מ-`compose_slides` / `render.py` / Canva `edit_url` = לא משבצים. פער מודפס בבריף אם לא הורץ. |
| `vfcanva` | LOOP `mcp-ready` → `studio/render.py`. עיצובי G004 קיימים. | 6.9: Canva `DAHUaelaug0` / `DAHUaUo3bAk` / `DAHUacDGv9U` + PNG ב-`/opt/cursor/artifacts/g004/` (לא בגיט). MCP נקרא 7.9. | עיצוב יש — **הטקסט על הפריים נכשל VOICE**. HANDOFF עדיין «חסם שער עריכה» בזמן שסטוריז כבר נראו חיים (כנראה JPEG מתיבה). | מסירה: תיקון טקסט ב-Canva לפי FIX. בלי ייצוא חדש היום — לא ממציאים פיקסלים. |
| `vfgrowth` | בריף 04 = `FOLLOWER-GROWTH`. מסירה = `HANDOFF-he.md`. שער = `EDIT-GATE.md`. | סנאפשוט 6.9: 80 עוקבים · DM 0 (בעלים). G004 מועמד סטוריז 20:30. | לוח+מסירה חיים; הרף לא עצר פלט חלש. | `STORIES.md` + שער JPEG. HANDOFF מצביע ל-FIX. |
| `vfcost` | בריף 02 = `vfcost.py brief` **כן רץ**. | 7.9: «עלות חומר: אין כרטיס עם גרמים · בלי ₪ מכירה». | מחובר ונצרך. אין גרמים = אין ₪. | להשאיר. חריץ 05 ירשום את ה-CLI הזה כשורה אמיתית. |
| `vfops` | הלולאה עצמה + `ROUTINE` 07:00. | בריף HTML 7.9 בארכיון (`BRIEF-2026-09-07.html`). | חריץ 05 הדביק קטלוג מ-`research.md` («קול פיד נעול») בלי CLI. פקים שלא הורצו — שקטים. | חריץ 05 = CLI מ-24ש או «אין חדש במשרד». פער מודפס. |
| `vfbiz` | בריף 04 קורא `out/week.md` + LOCK. | 7.9 `week.md`: אין באצ׳ לפני איסוף 10.9 · X ₪ · B2B נעול. | נצרך כנעילה, לא כהזדמנות מוצר. | להשאיר נעול. שורת פער אם הקובץ חסר. |
| `vfsales` | LOOP `on-inquiry` → `QUOTE.md`. לא בבריף. | אין פנייה חדשה בבריף 7.9 («אין ספירה»). | שקט מוחלט — נראה «לא בשימוש» גם כשאין פנייה. | שורת פער: `vfsales · לא הורץ · אין פנייה`. |
| `vfinsights` | בריף 06 קשיח «אין ספירה» + `CONNECT-IG.md`. | סנאפשוט בעלים 6.9 (80/0). ig-mcp `needsAuth`. | מחובר כחסימה. אין מספר חי. | להשאיר «אין ספירה». לא למלא. פער: חסום טוקן. |
| `vfresearch` | אמור לכתוב ל-`research.md` ב-06:15. | `DAILY.md` + `VOICE` 6.9 ב-`research.md`. אין `sources/2026-09-07-orchestra.md`. | חריץ 05 שימש כערימת הטמעות, לא כריצת CLI. | חריץ 05 מתעלם מקטלוג. פער אם אין ארטיפקט 06:15 מ-24ש. |
| `vfsku` | בריף 03 = `vfsku.py brief` **כן רץ**. | 7.9: מדף 0/5 · «אין שם להציע». | מחובר ונצרך. ריק עד GATE. | להשאיר. לרשום בחריץ 05 כ-CLI אמיתי. |
| `constitution/*` | `STUDIO` / `ORCHESTRA` / `INSTANCE` / `SEND`. | רף סוכנות + שער JPEG נכנסו 6.9. | השער היה טקסט. סטוריז עברו מתחת לרף. | שער קשיח: אין סטוריז/פיד בלי Canva MCP או vfcovers/vfcanva. |
| `instances/velvet-factory/constitution` | `STUDIO.md` משקף ליבה. | אותו רף 6.9. | אותו פער — הפרונט לא אוכף יותר מהליבה. | סנכרון שערי סטוריז + VOICE + JPEG. |

## מה הלולאה **לא** מריצה ב-07:00

| consume ב-`LOOP.json` | רץ ב-`assemble()`? |
|---|---|
| `velvetos.py modules` | לא |
| `vfcanva/studio/render.py` | לא |
| `vfcovers/g005/compose_slides.py` | לא |
| `vfresearch/DAILY.md` | לא (רק קריאת `research.md`) |
| `vfsales/QUOTE.md` | לא |
| `vfinsights/READ.md` | לא (שורת חסימה) |
| `check-all.py` | לא |

מלאי ≠ צריכה. מ-7.9 הלולאה מדפיסה **פער** לכל פק יומי/`on-content` שלא הורץ.

## סטוריז G004 — ראיה

Canva MCP 7.9 על `DAHUaUo3bAk`: הוק חידה + מגבלה על הפריים, לא «הכירו את… / מתאים כ…».  
`VOICE.md`: G004 = סיפור-מוצר. אסור לפתוח במגבלה.  
HANDOFF עדיין מתייג «חסם שער עריכה» — אם עלה JPEG מתיבת Grok, זה בדיוק השער שנשבר.

תיקון כיתוב+פריימים: `packages/vfcopy/G004-STORIES-FIX.md`.  
ייצוא פיקסלים: Canva MCP `export-design` או `vfcanva/studio/render.py` — **לא** בגיט היום.

## נעול

אין ₪ מכירה. אין Insights מומצאים. אין מייל. אין Publish.
