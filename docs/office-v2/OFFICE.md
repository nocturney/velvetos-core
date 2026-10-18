# Office 2.0 – חוקת המשרד

**תחולה:** צוות העבודה על Office 2.0 בריפו `nocturney/velvetos-core`. זהו חוזה תיאום ומסירה אנושי, **לא** מנוע משימות, אישורים, הרשאות או מקור אמת נוסף. הוא אינו מפעיל סוכן, אינו מעניק הרשאות ואינו משנה סביבת production.

**סדר סמכות:** הנחיה מפורשת ותחומה של Christian, `constitution/CONSTITUTION.md`, שער הפרויקט, `office/control/POLICY.md`, חוזי ה־GitHub/CI וגבולות ה־`policy_id` הקנוניים גוברים על טקסט זה. כאשר יש סתירה, ספק או ראיות חסרות – עוצרים את הפעולה המסוכנת ומבקשים הכרעה ממוקדת; לא מסיקים הרשאה מלוח או מהודעת סוכן.

## 1. האנשים והתפקידים

| משתתף | אחריות עבודה | גבול סמכות |
|---|---|---|
| **Christian** | בעל המוצר וההכרעות; קובע עדיפות, סיכון, scope, תקציב, הרשאות והעלאה לאוויר | אישורו אינו מחליף CI, סקירה בלתי תלויה, שער פעולה או readback |
| **ChatGPT** | פירוק דרישות, תכנון/תיעוד, אינטגרציה בין משימות, ביצוע תחום וביקורת QA של עבודת *אחרים* | אינו עושה QA או מיזוג ל־PR שכתב; אינו מפעיל פעולת עולם אמיתי מהתיעוד |
| **Cursor** | מימוש בקוד, בדיקות, תיקוני אינטגרציה ולוח התצוגה `docs/office-v2/board/latest.md` | הלוח לקריאה בלבד; Cursor אינו מאשר אוטומטית את עבודתו ואינו יוצר סמכות חדשה |
| **Claude** | מימוש, חקירה טכנית, בדיקות, תיעוד ו־QA עצמאי כשאינו המחבר | אין ביקורת עצמית ואין שינויי סכמה/הרשאות ללא שער מתאים |
| **Gemini** | מחקר, השוואת חלופות, כתיבת משימות/מימוש ו־QA עצמאי כשאינו המחבר | המלצה/מחקר אינם admission, אישור deployment או ראיית הצלחה |
| **auditor** | מבקר בלתי תלוי: בודק diff, head SHA, חיישנים, CI וגבולות סמכות; מפרסם verdict; עשוי לתאם מיזוג אם הוסמך ואינו המחבר | PASS אינו גובר על veto, אישור Christian, required checks או branch protection |

**עקרון צוותי:** אלה תחומי מומחיות, לא בלעדיות קבועה. לכל משימה יש **אחראי ביצוע אחד מוגדר** ו־**בודק בלתי תלוי שאינו אחראי הביצוע**. אותו חבר יכול למלא תפקיד אחר במשימה אחרת; אסור לאדם/סוכן לאשר לעצמו את ה־PR שלו. אפשר לעבוד במקביל על קבצים ומכונות נפרדים בלי להמתין לאישורי ביניים שאינם נדרשים.

## 2. מאין מתחילה משימה

- **[#612](https://github.com/nocturney/velvetos-core/issues/612)** הוא מרכז תיאום העבודה: הקשר, הקצאה/CLAIM, תלות, חסימה, סיום וקישורים לראיות. Issue ייעודי, כגון #604, ממשיך להחזיק את עובדות התחום שלו.
- לפני עריכה, אחראי הביצוע בודק טענות בעלות אחרונות ב־#612, PRs/ענפים פעילים, חפיפה בקבצים והוראות `AGENTS.md` וה־domain שנבחר. שתי עריכות לאותו קובץ/חוזה מתואמות; היעדר תגובה אינו שחרור CLAIM.
- לכל משימה מצמידים יעד ותנאי קבלה, בעלים, reviewer נפרד, scope של קבצים, תלות, base SHA, סביבת עבודה מבודדת וגבול פעולה/עלות. אין כתיבה ישירה ל־`main` ואין ערבוב worktrees.
- אל תתנו לדוח, ללוח או לשיחת צ'אט להיחשב כ־execution receipt, תור משימות שני או כהוכחת פעולה.

## 3. מסלול המסירה המחייב

1. **Intake ב־#612:** מגדירים פעולה קטנה עם outcome בדיק, מי אחראי לביצוע, מה מחוץ ל־scope, אילו שערי בעלים רלוונטיים ומה תנאי העצירה. אם יש Issue ייעודי – מקשרים אליו.
2. **CLAIM לפני שינוי:** אחראי הביצוע מפרסם ב־#612 הודעה שמתחילה `CLAIM`, ובה זהות, scope, קבצים/ענף מתוכנן, תלות ו־QA owner אם ידוע. בודקים שאין CLAIM חופף שלא שוחרר.
3. **ענף ו־PR:** יוצרים ענף מ־`main` טרי ו־worktree/clone מבודד; משנים רק קבצים בתחום, שומרים commit/parent SHA ופותחים PR יחיד וממוקד, **לא טיוטה כשהוא מוכן ל־QA**. מציינים ב־PR מה השתנה, מה נבדק, מה *לא* נבדק, וסיכון/rollback. שינוי capability מחייב README לפי חוזה ה־Living README.
4. **ראיות לפני מסירה:** אחראי הביצוע מריץ בדיקות ייעודיות וגם `python3 scripts/check-all.py` כשהמשימה דורשת, ורושם פקודה, תוצאה, סביבה וחריגות. אין המצאת PASS; כשל או חוסר סביבתי נשארים מפורשים. `README.md` ו־`scripts/readme_contract.py` הם חוזה חי, לא תחליף לבדיקות.
5. **בקשת QA על head מדויק:** אחרי push ועדכון ה־PR, מחבר ה־PR כותב עליו בדיוק `QA please @ <full sha>` כאשר ה־SHA הוא commit מלא בן 40 תווים. PR שנותר `draft` אינו תור סקירה מוכנה.
6. **ביקורת עצמאית:** הבודק שולף מחדש את **אותו head**; משווה diff ובעלות, בודק בדיקות עצמאיות/negative controls כשיש, בוחן CI של אותו SHA ואת ה־gates. בודק לא מניח ש־CI ירוק = אישור deployment או שמבחן סינתטי = הרצה חיה.
7. **Verdict:** הבודק מפרסם ב־PR `QA verdict (<reviewer>) @ <full sha>: PASS | PASS WITH NOTES | FAIL`, עם קישורים ל־CI/שורות/ראיות, גבולות הבדיקה וצעד תיקון קטן לכל blocker. ב־FAIL מתקנים ב־head חדש, מריצים בדיקות מחדש ומבקשים QA חדש; verdict ל־SHA קודם אינו נגרר הלאה.
8. **מיזוג מוגן:** רק מי שהוסמך ואינו מחבר ה־PR ממזג, אחרי verdict מספק **ללא חסם פתוח**, required reviews/checks ירוקים על **ה־head הנוכחי**, base/main תואם וכל אישורי Christian הנדרשים. שיטת המיזוג היא **merge commit בלבד**; ב־CLI משתמשים ב־`--match-head-commit <full sha>` כשזמין. אין squash, rebase merge, force-push, `--admin`, bypass או מיזוג אוטומטי מכוח הלוח.
9. **לאחר מיזוג:** מאמתים את merge commit, תוצאת בדיקות `main`/postcondition כשנדרשת, ומתעדים ב־#612 `DONE` עם PR, SHA, verdict וגבולות ההוכחה. בלי ראיית מיזוג/פריסה לא כותבים `MERGED`/`LIVE`.

**סמנטיקת מצבים:** `CLAIMED` = תפוס; `DRAFT` = טרם מוכן ל־QA; `QA REQUESTED` = בקשה ל־SHA מסוים; `QA FAIL` = תיקון נדרש; `QA PASS` = סקירה על SHA מסוים, עדיין לא מיזוג; `READY TO MERGE` = כל השערים מוכחים; `MERGED` = merge commit מאומת; `BLOCKED` / `WAITING ON CHRISTIAN` = השער והבעלים לצעד הבא רשומים. `DONE` אינו שם נרדף ל־PR ירוק.

## 4. מה דורש החלטה או אישור מפורש של Christian

| תחום מוגן | מותר להכין ללא הפעלה חיה | דורש אישור/הנחיה תחומה של Christian **וגם** שער המדיניות הרלוונטי |
|---|---|---|
| **Fleet / SYSTEM** | מחקר, מסמך, diff, בדיקות LAB מבודדות ללא הרשאות מערכת חיות | שינויי שרת/מחשב, LocalSystem/SYSTEM, autostart, שירותים, credentials, מדיניות הרשאות, הצבת agent על hosts או הוספת ממשק שליטה פעיל |
| **Production** | קוד, fixtures, סימולציה ובדיקת read-only מאומתת | פריסה, החלפת writer/authority, הפעלת מכונות/מדפסות/xTool, פעולה פיזית, שינוי נתיבי/סודות production או cutover |
| **Instagram** | רעיון, טיוטה, הכנת מדיה, תצפית מותרת ללא mutation | פרסום, תזמון או שינוי/מחיקה של תוכן, boost/קידום, שינוי מנגנון הפרסום והרשאות – אלא אם כבר יש אישור owner תחום ותקף לאותה פעולה בדיוק; תמיד עוברים `instagram.publish` ו־readback רלוונטיים |
| **כסף ותשלומים** | מחקר, ניתוח, תמחור כטיוטה ללא התחייבות | תשלום/רכישה, שינוי תמחור מחייב, חיוב, מנוי/API בתשלום, חשבונית/התחייבות כספית או עלות חוזרת חדשה, בכפוף ל־`NO_NEW_RECURRING_COST` ולמדיניות הכספית |

גם **מחיקה בלתי הפיכה, שינוי הרשאות, שימוש בסודות, הודעה חיצונית מחייבת ופעולת Computer Use בעלת השפעה חיצונית** חייבים לעבור את שער התחום שלהם; הרשאת Git אינה מאשרת אותם. אישור Christian לעבוד על קוד כולל פעולות Git רגילות באותו scope אחרי CI ו־QA, **לא** אישור אוטומטי לפריסה/פרסום/כסף/SYSTEM. אין לבקש אישור מחדש על כל push שגרתי שכבר הותר; מסלימים רק החלטה אמיתית או blocker קשיח.

## 5. איך קוראים את הלוח אחרי מיזוג #782

**מצב מוכח (18.10.2026):** [PR #782](https://github.com/nocturney/velvetos-core/pull/782) **מוזג** ב־[69395d40bb87787db960087e4dcb901ed14448ec](https://github.com/nocturney/velvetos-core/commit/69395d40bb87787db960087e4dcb901ed14448ec). סקריפט [office_v2_mvp.py](../../scripts/office_v2_mvp.py) קורא GitHub ב־GET בלבד; דוגמת [SAMPLE.md](board/SAMPLE.md) היא fixture סינתטי **ולא** מצב המשרד. הקבצים **board/latest.md** ו־**board/latest.json** נוצרים מקומית או ב־Actions, אך **מוחרגים מ־Git** ולא מוזגו כ־snapshot חי. ה־[workflow](../../.github/workflows/office-v2-board.yml) מופעל **רק ב־workflow_dispatch**, כותב artifact בלבד, ללא cron או הרשאות כתיבה; הוא לא מתזמן את עצמו. ראיות פרטיות של ריפו המפעל אינן מותרות בארטיפקט הציבורי. [QA עצמאי ותיקון החשיפה](https://github.com/nocturney/velvetos-core/pull/782#issuecomment-6249757109) · [כשל החשיפה שתוקן](https://github.com/nocturney/velvetos-core/pull/782#issuecomment-6249573484).

1. **מקור לפני תצוגה:** שואלים מתי snapshot נוצר, באיזה SHA/ריפו, האם היתה גישה למקור, והאם ה־workflow אכן הופעל. GitHub Issues, CLAIM, PR, head, CI, ביקורת עצמאית וה־receipts הקנוניים גוברים תמיד על כל טקסט בלוח. אם אין artifact או זמן יצירה – **UNKNOWN / NEEDS SYNC**, לא “הלוח ירוק”.
2. **קטגוריות תפעול:** Waiting on Christian = שער החלטה של בעלים; Waiting on QA = PR שאינו טיוטה עם בקשת SHA מדויקת; In progress = CLAIM בר־תוקף; Blocked = סיבה וצעד הבא קטן; Done today = ראיית merge/postcondition עדכנית. כל שורה נבחנת מול המקור שמאחוריה. היעדר שורות בגלל HTTP denied/גישה חסרה אינו מעיד שאין משימות.
3. **פרטיות והרשאות:** הלוח הציבורי מציג רק נתונים שמותר לחשוף. טוקן Actions אינו נותן גישה לריפו הפרטי. אל תעתיקו live board המכיל פרטי מפעל אל קובץ tracked, artifact ציבורי, issue או PR; אל תתייחסו ל־SAMPLE כנתוני אמת.
4. **הפעלת אירועים עתידית:** רצוי PR נפרד למימוש **אירוע push ל־main** לצד dispatch ידני, עם permissions לקריאה בלבד, בדיקת דלף, artifact-only ו־QA עצמאי; **האירוע הזה עדיין לא קיים**. אין cron, scheduler כפול, polling לא תחום, merge אוטומטי או פעולה מתוך צבע בלוח. הבעלות על מחולל הלוח ו־PR עתידי כזה היא של **Cursor**; מבקר שאינו הכותב יבקר. [המצב בפועל של ה־workflow](../../.github/workflows/office-v2-board.yml) · [NEXT](NEXT.md#3-priority-2--run-the-board-automatically-without-cron).

## 6. כללי תיאום והתאוששות

- לכל שינוי קוד/מסמך – **PR אחד למטרה אחת**. אין עבודה בשני worktrees על אותם קבצים, גניבת CLAIM, מחיקת ענף של אחר או דחיפת שינויים לא־קשורים.
- שיתוף בהערות GitHub הוא מסירה/תיעוד; הוא **אינו** מפעיל סוכן מתוזמן. כשבעל המשימה אינו זמין: בודקים owner, branch/head, receipts ו־CI; מחזירים למשימה קטנה ובטוחה ללא replay עיוור של side effects.
- לא חוסמים את כולם בגלל משימה אחת: משימות בלתי תלויות, עם בעלות נפרדת וללא contention על hosts, יכולות להתקדם במקביל; בעיה חסומה מתועדת עם smallest next step ו־executor.
- כשמחלוקת נוגעת לסמכות: פותחים החלטה ל־Christian עם חלופות והשלכה, לא משנים את מדיניות המקור דרך OFFICE.md.
- **בדיקות ואמת קודמות לנראות הלוח.** אם אי אפשר לקשור טענה ל־commit, PR, run או receipt אמיתי – מסמנים `UNVERIFIED`.

## 7. מפת מעבר לתוכנית השבוע (18.10.2026)

התמונה התפעולית המתוארכת ו־**מפת E1–E7 עם קבלות, חסמים, צעדים ובעלים לכל שער** נמצאות ב־[NEXT.md](NEXT.md). ה־CLAIM, מסמך התוכנית, לוח הבקרה או CI ירוק אינם משנים לבדם admission. בדיקת מצב בזמן הרצה תמיד נעשית מחדש מול הקישורים המקוריים.

| עדיפות ובעלות | מה עובד; מה חסום | מקור סמכות/ראיה |
| --- | --- | --- |
| **1. פיילוט CrewAI:** **Cursor** — [Draft #789 runner](https://github.com/nocturney/velvetos-core/pull/789) ו־fixture; **Christian** — GO תחום והחלטת סיכון; **מפעיל Chris שיוקצה** — lease/בקרות; **auditor/security** — QA והוכחת שערים | Runbook ו־preflight קיימים אך **המשימה NOT_RUN**. 154 wheels נעולים ו־pip check אומתו, וסריקת CVE זיהתה 5 התראות ב־chromadb/mcp. **Christian אישר E3 ACCEPT RISK WITH CONDITIONS בלבד**, מותנה באכיפת no-tools/no-MCP/no-Chroma-server ובבדיקות אמת על Chris; **אין E3 PASS אוטומטי**. Python על D: אך **E4 חסום** בלי ניטור/deny ל־C:. מודל qwen3.5:9b אכן עבד ב־**127.0.0.1:11435** והופסק; פורט 11434 הקודם תוקן ב־**Draft #789**, לא ב־runner מאושר. **E6 NOT_VERIFIED:** רק **12 issues פתוחים** ב־fixture הטיוטה לעומת דרישת **20+**. E1/E2/E5/E7 טרם הוכחו כ־PASS. | [preflight](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6249900804) · [E3/E4 audit](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6249982906) · [מחקר reachability](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250224612) · [החלטת E3](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075) · [Ollama](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250120048) · [Draft #789](https://github.com/nocturney/velvetos-core/pull/789). |
| **2. אוטומציית הלוח:** **Cursor**, עם **QA בלתי תלוי** | הלוח ממוזג. **workflow_dispatch קיים**, artifact לקריאה בלבד; **טריגר אירוע אוטומטי עדיין חסר**. אין cron. | [#782](https://github.com/nocturney/velvetos-core/pull/782) · [workflow](../../.github/workflows/office-v2-board.yml). |
| **3. CP057:** **מבצע #602 ב־Chris** ובודק עצמאי | [#786](https://github.com/nocturney/velvetos-core/pull/786) מוסיף זיהוי PLM. ניסיון 6: 0 פעולות UI ו־CalculatorApp מושעה. accepted on receipts of attempts 8+9; runtimeAuthority=false, activationAllowed=false. ניסיונות קודמים נשארים RED/UNVERIFIED. אין סמכות ריצה או הפעלה. | [#602 ניסיון 6](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6249903313) · [מיזוג #786](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250104404). |
| **4. CP083:** **מבצע full-chain של #604** עם **מבקר אבטחה עצמאי** | ראיית Linux guest אמיתית של שני 59-case runs קיימת, אך **SECURITY RED** עד ראיות ל־protected issuer, GitHub remote effects, cross-store, 51-case matrix וביקורת עצמאית. אין הסמכת worker או פריסה. | [קבלת guest ועדויות חסרות](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6249984760) · [תלויות PR](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6249275082). |

**כלל עצירה:** הצעת [Cursor המקורית](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250043562) הזכירה 11434, בעוד [קבלת Ollama](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250120048) אימתה **127.0.0.1:11435**. **Draft [#789](https://github.com/nocturney/velvetos-core/pull/789) תיקן את ה־endpoint בטיוטת קוד**, אך הוא עדיין דורש QA ואישור runtime; אין להשתמש ב־0.0.0.0:11434 (listener נפרד שנצפה). החלטת [E3 ACCEPT RISK WITH CONDITIONS](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075) אינה GO לריצה ואינה פוטרת מהוכחת מנגנוני ה־deny/no-server, ה־fixture בן 20+ issues, ה־C: monitor והיתר E1–E7. כל חריגה או היעדר קבלה = NO_GO. #612 ו־#604 נשארים מקורות הפעולה ולא מחליפים אישור אבטחה, תהליך עצירה או receipts.

**מקורות נורמטיביים:** [חוקת VelvetOS](../../constitution/CONSTITUTION.md) · [מדיניות Office](../../office/control/POLICY.md) · [תיאום משותף](../SHARED-WORK-COORDINATION.md) · [חוזה Living README](../../scripts/readme_contract.py) · [#612](https://github.com/nocturney/velvetos-core/issues/612).
