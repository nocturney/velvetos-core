# Morning Green v3.1

המסלול הקנוני החדש לבריף הבוקר של Velvet Factory. זהו מייל owner-only, RTL, Desktop-first ורספונסיבי, בעיצוב מגזיני ירוק/שמנת/זהב.

`MAIL.html` / `render_mail.py` נשארים זמינים ל־legacy owner/research surfaces; Morning Green מיועד לבריף הבוקר בלבד כדי לא לשבור משטחים אחרים.

## עקרונות תצוגה

- canvas דסקטופ עד 920px; מובייל נערם לטור אחד מתחת ל־680px.
- פתיחה מצולמת, hero ירוק, כרטיסים מעוגלים, הרבה whitespace, תמונות בתוך המדורים וחתימת סוף.
- אין navigation, menu, ellipsis, controls או כפתורים מדומים.
- אזור `בקרוב באינסטגרם` נמצא בראש המייל.
- עד 4 כרטיסי תוכן: thumbnail, תאריך/סטטוס, שעה וסוג.

## אמת בפרסום

`scheduled != approved != published_verified`.

- `מתוזמן` מותר רק כאשר קיימת ראיית schedule חיה, למשל OpenPost publication עם `scheduled_at`.
- קובץ בתיקיית `Velvet Media / 04 - מאושר לפרסום` הוא `מאושר` בלבד. אם אין ראיית schedule הוא מוצג כ־`טרם שובץ`.
- תאריך בשם קובץ אינו ראיית תזמון.
- Calendar היסטורי/ישן אינו גובר על queue חי.
- publication response אינו live verification. Instagram live נשאר `list_media/get_media`.

## תמונות

- נכסי אווירה קבועים מגיעים כ־CID מתוך `assets/morning-green/`: `morning-top.jpg`, `morning-story.jpg`, `morning-radar.jpg`, `morning-footer.jpg`.
- thumbnail חי של פוסט יכול להגיע כ־HTTPS ציבורי. מסלול Gmail הקנוני מוריד אותו וממיר ל־CID לפני שליחה.
- production renderer דוחה HTTP, נתיב מקומי או reference שאינו `cid:`/HTTPS.
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
- `scheduled_posts[]`: `image_url, image_alt, date_label, time_label, type_label, status_label`
- `story{title,body,image}`
- `morning_line{text,note}`
- `attention[]`, `progress[]`
- `radar{title,text,image}`
- `stats[]`
- `footer{quote,note,image}`

נכסי האווירה אינם חייבים להופיע ב־JSON; ה־renderer משתמש ב־CID defaults.

## Render

`python packages/vfbriefux/render_morning_green.py BRIEF.json -o OUT.html`

Self-check: `python packages/vfbriefux/render_morning_green.py --check`

## Send

השליחה ממשיכה במסלול Gmail הקנוני בלבד, עם owner-visible-text gate:

`PYTHONPATH=packages python -m vfops.gmail_brief_send --html OUT.html --images packages/vfbriefux/assets/morning-green --to nocturney@gmail.com --subject TEXT --embed-remote-images`

במסלול repo-backed production ניתן להשתמש ב־`gmail_brief_request.py` וב־GitHub Actions הקיימים. אין plugin fallback אוטומטי.

## Done

Morning Green נחשב production-ready רק אחרי:
1. renderer check;
2. sensor/check-all;
3. OpenPost read עובד ומחזיר schedule אמיתי או empty אמת;
4. email E2E נשלח לבעלים עם CID + thumbnails;
5. Gmail readback מאמת את ההודעה;
6. רק אז האוטומציה היומית הקיימת יכולה לעבור ל־Morning Green ולהיות enabled.