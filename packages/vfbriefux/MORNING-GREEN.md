# Morning Green v3.1

המסלול הקנוני לבריף 09:00 של Velvet Factory. זהו מייל owner-only, RTL, Desktop-first ורספונסיבי, בעיצוב מגזיני ירוק/שמנת/זהב. החל מ־2026-09-23 הסטטוס הוא `LIVE / VERIFIED` עבור בריף הבוקר.

`MAIL.html` / `render_mail.py` נשארים זמינים ל־legacy/recovery owner surfaces בלבד; Morning Green הוא ברירת המחדל של בריף הבוקר.

## עקרונות תצוגה

- מעטפת המייל היא fluid עד 680px. במובייל שומרים על קומפוזיציות Hero/Story מפוצלות כמו במוקאפ המאושר, בלי לחזור ל־920px ובלי להפוך אותן אוטומטית לטור אחד.
- פתיחה editorial דו־עמודתית: טקסט חי על ירוק עמוק לצד still-life חם, כרטיסים מעוגלים, הרבה whitespace ותמונות בתוך המדורים.
- ה־TARGET-CONCEPT המאושר הוא סמכות העיצוב הראשית: שמנת חמה כ־canvas, כרטיסים נפרדים ומעוגלים, Hero ו־Story בירוק עמוק, היררכיה מגזינית וצילום editorial חם. שינוי שמרחיק מהמבנה הזה הוא regression גם אם ה־HTML תקין טכנית.
- שפת האווירה קבועה ומצומצמת: still-life בוקר, ענפי זית כהים, מחברת/קפה ונוף זיתים חם. אין איור, flat vector, placeholder מצויר, stock גנרי או imagery ילדותי. אם אין צילום מתאים - עדיף שטח שקט על visual חלש.
- חתימת ה־handwriting בתחתית היא האלמנט הטיפוגרפי הדקורטיבי הראשי; משפט הסיום אינו משוכפל שוב ככותרת HTML גדולה.
- אין navigation, menu, ellipsis, controls או כפתורים מדומים.
- אזור `בקרוב בפיד` נמצא בראש המייל כרצועת שבוע אחת.
- הרצועה מציגה תמיד את 7 הימים הקרובים, עמודה לכל יום, עם thumbnail קטן + שעה/סוג רק כשיש schedule חי; יום ללא פרסום נשאר תא שקט ולא מומצא.
- `Instagram` הוא מדור נפרד ללא thumbnails: עוקבים, מעורבות מאומתת בפוסט האחרון, שינוי מאז הבריף הקודם, והערת Insights/Reach רק אם המקור מספק אותם.
- QA חזותי אחרי שינוי תבנית חייב להריץ מחדש את `build_morning_green.py` ממקורות ה־brief העובדתיים + OpenPost העדכני. אסור לבדוק תבנית חדשה על JSON ביניים היסטורי ששמר כפילויות/מבנה ישן.

## אמת בפרסום

`scheduled != approved != published_verified`.

- `מתוזמן` מותר רק כאשר קיימת ראיית schedule חיה, למשל OpenPost publication עם `scheduled_at`.
- קובץ בתיקיית `Velvet Media / 04 - מאושר לפרסום` הוא `מאושר` בלבד. אם אין ראיית schedule הוא מוצג כ־`טרם שובץ`.
- תאריך בשם קובץ אינו ראיית תזמון.
- Calendar היסטורי/ישן אינו גובר על queue חי.
- publication response אינו live verification. Instagram live נשאר `list_media/get_media`.

## תמונות

- נכסי אווירה קבועים מגיעים כ־CID מתוך `assets/morning-green/`: `morning-top.jpg`, `morning-story.jpg`, `morning-radar.jpg`, `morning-footer.jpg`.
- thumbnail של פוסט עתידי אינו נחשף לציבור רק בשביל המייל. ב־OpenPost local-storage, `public_url_ready` עם `/media/<id>` אינו נחשב URL ציבורי עד בדיקה אנונימית אמיתית.
- מסלול production המועדף: OpenPost `api:read` מוכיח `scheduled_at` + media ID; `packages/vfigos/run_openpost_morning_snapshot.ps1` קורא את ה־credential מ־DPAPI בלי להדפיס אותו; `packages/vfigos/materialize_openpost_morning_thumbnails.ps1` materializes רק את thumbnail ה־`sm_<media-id>.jpg` דרך GCP IAP; `prepare_morning_green.py --thumbnail-dir ...` מאחד אותו עם נכסי האווירה ל־CID bundle.
- HTTPS ציבורי אמיתי עדיין מותר, אבל production renderer דוחה HTTP, נתיב מקומי או reference שאינו `cid:`/HTTPS.
- local preview מותר רק עם `--allow-local-images`.

## מקורות אמת

ה־brief builder חייב לקרוא מחדש בכל ריצה:
- `VF HQ · jobs` + `VF HQ · books` לכסף/עבודות.
- OpenPost queue לתזמון עתידי, כאשר auth/runtime זמינים.
- `Velvet Media / 04 - מאושר לפרסום` למדיה שמוכנה אך עדיין לא הוכח ששובצה.
- Instagram MCP ל־live media/verification.
- מקורות נוספים לפי `packages/vfe2b/crews/morning-brief.md`.

חסר נשאר חסר. אין 0 במקום מידע חסר, אין ₪ מומצא ואין Insights מומצאים.

## Schema

ה־JSON ל־`render_morning_green.py` כולל:
- `date_label, greeting, daily_summary, preheader`
- `scheduled_posts[]`: בדיוק 7 תאי יום עם `day_label, date_label, has_post, time_label, type_label, extra_count`; בימים מתוזמנים נוספים גם `image_url, image_alt`.
- `instagram`: `followers, following, media_count, latest{likes,comments,date_label}, previous{likes,comments,date_label}, change_text, insights_available, insights_note`.
- `story{title,body,image}`
- `morning_line{text,note}`
- `attention[]`, `progress[]`
- `radar{title,text,image}`
- `stats[]`
- `footer{quote,note,image}`

נכסי האווירה אינם חייבים להופיע ב־JSON; ה־renderer משתמש ב־CID defaults.

## Render

`python packages/vfbriefux/prepare_morning_green.py --brief-json FACTUAL.json --brief-txt FACTUAL.txt --openpost OPENPOST-SNAPSHOT.json --thumbnail-dir MATERIALIZED-THUMBNAILS --request packages/vfops/out/gmail-send-request.json`

Render-only: `python packages/vfbriefux/render_morning_green.py BRIEF.json -o OUT.html`

Self-check: `python packages/vfbriefux/render_morning_green.py --check`

## Send

השליחה ב־production עוברת רק במסלול Gmail הקנוני עם owner-visible-text gate:

`prepare_morning_green.py ... --request packages/vfops/out/gmail-send-request.json`
→ `.github/workflows/gmail-brief-send.yml`
→ `packages/vfops/gmail_apps_script_request.py`
→ Apps Script Gmail bridge

הצלחה דורשת workflow success, Gmail `messageId`, readback כשמחבר Gmail זמין, והחזרת בקשת ה־one-shot ל־`enabled:false`. אין plugin fallback אוטומטי. `gmail_brief_send` המקומי נשאר כלי manual/diagnostic בלבד ואינו סמכות production.

## Done

שערי production של Morning Green:
1. renderer check;
2. sensor/check-all;
3. OpenPost read עובד ומחזיר schedule אמיתי או empty אמת;
4. email E2E נשלח לבעלים עם CID + thumbnails;
5. Gmail readback מאמת את ההודעה;
6. Apps Script bridge health תקין וה־one-shot חוזר ל־disabled.

כל ששת השערים עברו ב־2026-09-23. Apps Script deployment הקנוני עודכן לגרסה 5 והחזיר HTTP 200; QA production-path החזיר Gmail message ID `1a0ca4521ef56af0`; readback אימת 6 CID images, את התזמונים 09:00 ו־12:00 ואת היעדרם של template tokens פתוחים. לכן בריף 09:00 רשאי להשתמש ב־Morning Green כברירת המחדל.