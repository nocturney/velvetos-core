# חוקת משרד — VelvetOS Core

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

מוצר: **VelvetOS Core** (backend).  
Bind ייחוס (תאימות): Velvet Factory — שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`

פרונט VF: [`instances/velvet-factory/`](../instances/velvet-factory/) · ריפואים: [`REPOS.md`](../packages/velvetos/REPOS.md) · [`INSTANCE.md`](INSTANCE.md)

המשרד חי ב־Cursor packs. **שליחת ג׳ימייל ואינסטגרם — מ־HQ דרך כלים** (`SEND.md`). לא דרך כריסטיאן ולא דרך Grok Bot. מדפסות נשארות ברצפה.  
**PUBLIC_CURRENT_CTA** = הודעת Instagram (`PUBLIC_CTA.md`). **BUSINESS_CONTACT_RECORD** = וואטסאפ `050-2517000` (לא CTA ציבורי כרגע; שליחה ללקוח נשארת אנושית).

**NO_NEW_RECURRING_COST:** מקור הסמכות הקנוני הוא [`NO_NEW_RECURRING_COST.md`](NO_NEW_RECURRING_COST.md). ברירת המחדל היא אפס עלות חדשה חוזרת. לפני התקנה/חיבור/credential/קריאה ראשונה לשירות חיצוני חדש נדרש Cost Preflight; ספק לגבי חיוב נכשל-סגור. אין subscription, trial שהופך לתשלום, paid API call, resource מחויב או הרחבת usage שעלולה להעלות חשבון בלי אישור מפורש מראש של הבעלים.

**Visible Text Gate:** כל prose/microcopy שנוצר או שוכתב ב־AI ושאדם עתיד לקרוא — כריסטיאן, לקוח, קהל או שותף — עובר את כלי הכתיבה והאימות הרלוונטיים לפני final/send/publish/render. סמכות: [`VISIBLE_TEXT.md`](VISIBLE_TEXT.md); יישום קנוני: `packages/vfcopy`. טקסט תפעולי לבעלים אינו מקבל קול Instagram בכוח, וטקסט מקור/ID/hash/log נשאר literal. אין `PASS` בלי ביצוע בפועל.


**NO_NEW_RECURRING_COST:** יעד ברירת המחדל הוא אפס עלות חדשה חוזרת. לפני התקנה, חיבור, credentials, קריאה ראשונה שעלולה להיות מחויבת או production, מפעילים cost preflight ונכשלים-סגור כשהעלות בתשלום או לא ידועה. סמכות קנונית: [`NO_NEW_RECURRING_COST.md`](NO_NEW_RECURRING_COST.md).

מפעל צמיחה אורגני: [`ORGANIC_GROWTH.md`](ORGANIC_GROWTH.md) — טיוטות + readiness pack לפי צורך/אירוע לצריכת Morning Brief ידני/אירועי. ה־Control Plane אינו Publish API ישיר; פרסום מורשה עובר רק דרך `vfigos` + `policy_id: instagram.publish`. לא אוטו־DM.

מאגר מדיה משותף: [`docs/MEDIA-VAULT.md`](../docs/MEDIA-VAULT.md) · קטלוג אחד `packages/vfmedia/catalog.json`. תפעול קולט נכנס→מקור; העלאה ומיקום בתיקייה אינם אישור לפרסום.

בקרת משרד (איחוד מקורות אמת, לא מערכת שנייה): [`office/control-plane.json`](../office/control-plane.json) · `office/control/` · `python3 scripts/vf_control_plane.py` · מדיניות Don't Bother Christian ב־`office/control/POLICY.md`.

## COMPETITOR_NEUTRAL_ADMISSION_V1 — הגנה גלובלית מפני פסילת חלופות

**מבחן התאמה לפני נאמנות למימוש קיים:** חפיפה ל־VelvetOS, לכלי שכבר מותקן, לספק נבחר, ל־Core, ל־Office או ל־Tenant אינה סיבה לפסול טכנולוגיה. גם השקעה קודמת, יתרון זמני למימוש קיים, או הכותרת "runtime שני"/"משרד שני" אינם ראיית פסילה. כל מועמד רציני יכול להחליף רכיב, תת־מערכת או את בסיס המערכת כולו, או להשתלב בארכיטקטורה משולבת — אם השוואה חוזרת ומוכחת מצביעה על עדיפות.

**רישום בלי לאבד אופציות:** לכל ריפו/כלי/פתרון חדש בעל התאמה אפשרית יש לרשום מקור, יכולת, השוואה אפשרית למימוש הקיים, חסמים אמיתיים, evidence, מצב ומעשה הבא בתוך Candidate Registry הקנוני של Office v2 (לא קטלוג מקביל). מועמד שלא נכנס ל־2–3 מתחרים בבנצ'מרק הנוכחי נשמר ב־`queued_challengers` ברשימת הנתיב שלו; מגבלת קיבולת אינה `REJECTED`. מועמד לא נעלם בשל "כבר בדקנו משהו דומה".

**סיבות החלטה ראייתיות:** `REJECTED_WITH_REASON`, `DEFERRED_WITH_REASON` או `BENCHMARKED_AND_LOST` מחייבים סיבה קונקרטית וראיות לגבי בטיחות, רישוי, יכולת, תחזוקה, חומרה, עלות או Golden Fixture; לא סיבה שמבוססת רק על חפיפה, פחד ממיגרציה, "שני orchestrators" או sunk cost. החלטות שננעלו נפתחות מחדש כאשר מגיע מתחרה אמין או ראיה מהותית חדשה לאותו חוזה.

**הפרדה הכרחית:** אין פסילה של *השוואה* בגלל איסור על שני רכיבי production מקבילים. סקירת קוד ומחקר מותרים; התקנה/הרצה ב־LAB כפופות ל־admission, sandbox, הרשאות ועלות. מעבר ל־SHADOW/PILOT/PRODUCTION מחייב את שערי הבטיחות, מדידות, rollback, authority ו־readback הרגילים. רישום או Benchmark אינם הרשאת הוצאה, קרדנצ'לים, כתיבה ללקוח, פרסום או החלפת מערכת חיה.

סמכות תהליך/אימות: [Office v2 Phase 2](../docs/implementation/office-v2/phase2/README.md) · [Admission](../docs/implementation/office-v2/phase2/admission-policy-v0.md) · `scripts/check-office-v2-phase2.py`. מסמכי Legacy ובהם `packages/vfe2b/LOCK.md` משמשים גבול שימוש **שגרתי/ייצורי**, ואינם יכולים לבטל את הזכות לרשום, להשוות ולבחון מתחרים.

## Standing implementation authorization — Git delivery

כאשר הבעלים מאשר במפורש עבודה/פעילות ל־**יישום / הטמעה / ביצוע**, האישור כולל מראש גם את פעולות ה־Git הנדרשות כדי להביא את אותה עבודה לסיום: יצירת branch/worktree, commit, `git push`, פתיחה/עדכון של PR, פתרון conflicts שאינו מרחיב את ה־scope, וה־merge לאחר שכל CI, required checks, reviews ו־branch protections החלים עברו. **אין לבקש מהבעלים אישור נוסף רק עבור push או merge בתוך ה־scope שכבר אושר.**

האישור אינו מתיר להרחיב scope, לעקוף CI/rulesets/branch protection, לבצע force-push או history rewrite, לצרף שינויים לא קשורים, או לעקוף שערים נפרדים של עלות/כסף, credentials/security, מחיקה/פעולה הרסנית או external business authority. אם אחד מאלה נדרש — חל השער הספציפי שלו. אם GitHub דורש reviewer/approval בלתי תלוי ברמת הפלטפורמה, מכבדים אותו ולא עוקפים אותו.
