# PIPELINE — Visible Text Gate

אין runtime חדש. זה סדר העבודה הקנוני לכל agent שמפיק prose/microcopy אנושי נראה דרך `vfcopy`.
Authority: `constitution/VISIBLE_TEXT.md`.

## שלבים

| # | שלב | מקור אמת | פלט חלקי |
|---|---|---|---|
| 1 | הקשר מאומת | Drive / order / media / Calendar / thread / domain pack | עובדות + מה אסור להמציא |
| 2 | Surface + intent | public / visual / customer / sales / owner / document / UI | `mode` + מי קורא ולמה |
| 3 | Domain truth | `constitution/` + הפק הרלוונטי | אילוצים, מחיר/CTA/סטטוס/רישיון כשישים |
| 4 | Reader-first | `hq/reader-first-he.md` | מה האדם מרגיש/צריך · הדרך הפשוטה להגיד |
| 5 | Writer לפי surface | templates + domain tools | שלד |
| 6 | Relevant specialist tools | social→VOICE/vfgrowth; sales→vfsales/vfcost; visual→Creative Director; marketing→vfmskill כשישים | context-aware draft constraints |
| 7 | **velvet-hebrew-copy** | `skills/velvet-hebrew-copy/SKILL.md` | טיוטה בעברית טבעית |
| 8 | Style / Humanizer / AI-tells | `hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint` | lint · rewrite אחד · מבחן מאפייה |
| 9 | Factual validation | source/domain truth | pass או `needs_input` |
| 10 | Surface QA | לפי mode | public/visual/customer/owner/document/UI pass |
| 11 | Visible Text decision | artifact/preflight קיים | `visible_text_gate: PASS|FAIL|UNPROVEN` |
| 12 | מסירה | הערוץ הבא | final candidate בלבד אחרי PASS |

`reader-first-he.md` הוא baseline לכל prose שנכתב ב־AI לעין אנושית.  
`vfmskill` copywriting/copy-editing מתווסף כאשר הוא רלוונטי, בעיקר marketing/sales/long-form; הוא אינו עוקף `velvet-hebrew-copy`, `ai-tells-he.md` או אמת הדומיין.

## Routing לפי mode

### `public-social`
`VOICE.md` + `VOICE-CHART.md` + `PUBLIC_CTA.md` + vfgrowth. Caption/Story/Reel/Carousel עוברים גם את שערי הפרסום הרגילים.

### `visual-microcopy`
1. `NO_TEXT` baseline.
2. 3–5 candidates אם יש ערך להוסיף.
3. reader-first + velvet-hebrew-copy + Humanizer/AI-tells.
4. Creative Director/Brand Guardian.
5. `TEXT_WINS` רק עם נימוק; אחרת `NO_TEXT`.

### `customer-message`
1. thread/card אמיתי.
2. `vfconvert` לחסרים; `vfsales` אם מכירתי; `vfcost` למחיר/עלות; `vlicense` רק כשישים.
3. reader-first + velvet-hebrew-copy + Humanizer.
4. CTA/ערוץ לפי השיחה הפרטית — לא PUBLIC_CURRENT_CTA בכוח.

### `sales-proposal`
כמו customer-message + מבנה `vfsales`; מסגרת `vfmskill` copywriting/copy-editing כשמועילה. מחיר רק ממקור/אישור.

### `owner-brief`
1. מקורות אמת של המשרד.
2. reader-first: מה כריסטיאן צריך לדעת/להחליט עכשיו.
3. velvet-hebrew-copy במצב תפעולי + Humanizer.
4. preserve literal IDs/hashes/status/numbers.
5. אין public CTA ואין שיווקיות. חסם נשאר חסם.

### `human-document`
פק הדומיין → reader-first → vfcopy/Humanizer → copy-editing כשישים → רק אז layout/render QA.

### `ui-microcopy`
reader-first + vfcopy/Humanizer. labels טכניים קנוניים/נתוני source אינם משוכתבים.

## Visual copy law

טקסט על cover / first frame / carousel slide / overlay אינו קישוט ואינו ברירת מחדל.

1. מתחילים מ־`NO_TEXT`.
2. מייצרים 3–5 ניסוחים רק אם יש פואנטה.
3. כל ניסוח עובר reader-first + velvet-hebrew-copy + Humanizer/AI-tells.
4. ניסוח שניתן להלביש על מאפייה/מספרה/פוסט אחר כמעט בלי שינוי נכשל.
5. ניסוח שרק מתאר את מה שכבר רואים נכשל.
6. אם אף ניסוח לא משפר את העצירה/בהירות/פואנטה — `NO_TEXT`.
7. בחירת בעלים מפורשת נרשמת כ־preference חזקה.

## Approved static copy

נוסח קבוע שכבר עבר את השער יכול להיות `approved_static_copy`. reuse מותר רק אם הטקסט זהה; שינוי מהותי מחייב gate מחדש.

## פלטים חוקיים

- `content_candidate` / `draft` — עדיין לא final אם Visible Text Gate לא עבר.
- `needs_input` — חסרה אמת הכרחית; לא ממציאים.
- `TEXT_WINS` / `NO_TEXT` — visual decision בלבד.
- `visible_text_gate: PASS` — רק אחרי ביצוע אמיתי של השלבים הרלוונטיים.
- `visible_text_gate: UNPROVEN` — אם אין הוכחה שהשלבים הופעלו; אסור להמיר ידנית ל־PASS.

## אחרי candidate

- social visual → `vfcanva`/`vfcovers` → exact render → Brand Guardian → `vfigos`.
- customer/quote → send/human handoff לפי `constitution/SEND.md` רק אחרי text gate.
- owner brief → HTML/layout רק אחרי text gate; transport אחריו.
- human document → format QA אחרי text QA.

שינוי מהותי בטקסט מבטל gate/QA שקשור ל־digest הקודם. אין auto-DM. אין boost בלי ראש צוות. אין Print מ־HQ.
