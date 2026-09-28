# מחקר יומי · Velvet Research Seat

מושב: **צמיחה** + ראש צוות קורא בבריף.  
בעל ריצה קבוע: **Velvet Research Seat** ב־02:00 Asia/Jerusalem.  
יעד סיום: עד **07:00** כ־`ready_for_brief`, `no_meaningful_findings` או blocker מפורש. בריף הבוקר קורא את התוצר ב־09:00.  
ה־Research Seat משתמש ב־WebSearch/מקורות ציבוריים וחיבורים מאומתים; מק ייעודי יכול להשלים מקורות מנוי, אבל אין תלות בו כדי שהמחקר היומי ירוץ.  
Cloud לא גולש ל־chatgpt.com / gemini.google.com / perplexity.ai. לא שומרים עוגיות ולא מתחזים להפעלת גוף שלא רץ.

## 02:00 — גוף מחקר אמיתי

1. לקרוא את הבריף הקודם, לוח `vfgrowth`, מצב `vfsku`/ייצור, והקשר משרד/הזמנות החי כשזמין.
2. להריץ מחקר Web אמיתי על אותות רלוונטיים לסטודיו: מוצרים חוזרים קלים להדפסה/מכירה, המרה מפנייה להזמנה, יעילות ייצור/משרד, תוכן מהעבודה עצמה, ומגמות maker/3D-print שימושיות.
3. להריץ `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json`. זהו read-only watch על כלים מותקנים וגם על repos שמספקים skills/agents/patterns; אין auto-upgrade. שינוי upstream נשאר `pendingUpdate` גם בריצות הבאות עד אימוץ שנבדק. רק אחרי compatibility/adoption evidence מפורש מותר `vf_upstream_watch.py ack`; עצם גילוי העדכון אינו אישור להתקנה או ack.
4. לכל `pendingUpdate` לבדוק release notes / diff רלוונטי, השפעה על ה־integration שלנו וראיות compatibility קיימות. לכתוב את ההחלטה ל־`packages/vfresearch/sources/upstream-review-latest.json` כ־`update`, `wait`, `review` או `ignore`, עם נימוק וראיות, ובנוסף `reviewedRemoteHead` ו־`reviewedRelease` שתואמים בדיוק לדוח הנוכחי. מייל אינו יכול להיחמש עד שכל ה־pending קיבלו review עדכני. כאשר review חסר/ישן הופך ל־current, לסמן `notifyOwner:true` לריצה אחת כדי שהפריט ייכלל במייל הראשון; אחרי הכנת request הדגל מתאפס.
5. להעדיף מקור ראשוני/עדכני; לשמור URL + תאריך מקור. לא להעתיק buzz ולא להציג אות כללי כאילו הוא Insight של `@velvets_cloud`.
6. להטמיע רק מה ששימושי בפק קיים (`constitution/ORCHESTRA.md`). בלי פק חדש רק כי נמצא רעיון.
7. לכתוב את התמצית הצרכנית ל־`packages/vfops/data/research.md` עבור בריף 09:00. **אין להכניס לתמצית הזו רשימת עדכוני כלים, מספר pending updates או החלטות update/wait/review/ignore.** כאשר המצב הוא `ready_for_brief`, גוף התמצית חייב להשתמש בכותרת הקנונית **`## מה נבנה / יועל`** לפני הממצאים. אם אין משהו מוצק: **«אין חדש במשרד»** בדיוק.
8. לשמור גוף מלא ב־`sources/YYYY-MM-DD-orchestra.md` עם מקורות, ממצאים, מגבלות, מה עושים עם זה, ומה דולג.

## חוזה freshness

מחקר יומי הוא GREEN רק אם קיים `sources/YYYY-MM-DD-orchestra.md` לאותו יום ובו הוכחה לגוף מחקר: לפחות URL חיצוני אמיתי + ממצאים, או `אין חדש במשרד` יחד עם תיעוד החיפוש שבוצע. אינדקס סמנטי, `check-all`, או workflow ירוק **אינם** הוכחה שהמחקר היומי עצמו רץ.

בדיקה: `python3 scripts/vfresearch_cadence.py freshness`.

`VelvetOS Research Cadence` ב־GitHub רץ אחרי ה־Research Seat כדי לאמת freshness, לבנות אינדקס ולהריץ sensors. הוא לא ממציא/מחליף גוף Web research.

בלי ₪. בלי Insights מומצאים. בלי שמות לקוח מיותרים. בלי אוטו־DM. בלי Meta Business Suite. בלי משלוח ארצי.

## מייל עדכוני כלים לבעלים

עדכוני toolchain / skills / agents **לא נכנסים ל־Morning Brief**. הם נשלחים במייל נפרד בלבד, דרך אותו Gmail Apps Script production sender אבל עם artifact ו־workflow נפרדים.

- אחרי בדיקת ה־upstreams וה־review, להריץ `python3 scripts/vf_upstream_email.py render --arm --consume-notify`.
- המייל נשלח רק אם יש `newDetection` או `notifyOwner:true` בגלל שינוי המלצה. Pending ישן שלא השתנה לא מייצר מייל יומי חוזר.
- כל פריט במייל כולל upstream, baseline→latest, איפה הוא משמש אצלנו, והמלצה אחת: **מומלץ לעדכן / להמתין / לבדוק לפני החלטה / אין פעולה כרגע**.
- אין שדרוג, `git pull`, `pip install -U`, `npm update` או ack כתוצאה מהמייל. אימוץ נשאר שלב נפרד עם compatibility/smoke evidence.
- artifacts: `packages/vfresearch/out/tool-updates-latest.txt`, `tool-updates-latest.html`, `tool-updates-send-request.json`.
- שליחה: `.github/workflows/gmail-tool-updates-send.yml` → `vfops.gmail_apps_script_request` → owner Apps Script bridge → Gmail API.
- אם אין עדכון חדש או שינוי החלטה — **לא נשלח מייל**.
- אין claim של delivery בלי workflow success + Gmail message ID.

## מייל מחקר לבעלים

מייל המחקר הכללי נשאר נפרד ממייל עדכוני הכלים ונשלח רק אם יש מחקר חדש משמעותי או blocker אמיתי. אחרת לא שולחים.

- רינדור: Morning Brief V10.3 — `packages/vfbriefux/MAIL.html` + `render_mail.py`; לא plain text/Markdown ולא HTML נחות.
- כל ממצא במייל כולל קישור חיצוני ישיר ולחיץ למקור הרלוונטי.
- prose לבעלים עובר `constitution/VISIBLE_TEXT.md` עם `scripts/vf_visible_text.py --surface owner-brief --gate` על הטקסט המדויק; שינוי טקסט מבטל PASS.
- שליחה רק בנתיב production: `packages/vfops/out/gmail-send-request.json` → `.github/workflows/gmail-brief-send.yml` → `vfops.gmail_apps_script_request` → owner Apps Script bridge → Gmail API; לא דרך Gmail connector אינטראקטיבי.
- אין claim של delivery בלי workflow success + Gmail message ID. אחרי one-shot מחזירים `enabled:false`.

## תבנית שאלה

```text
Velvet Factory — סטודיו קטן להדפסות תלת־ממד בשדרות.
איסוף בלבד. אינסטגרם @velvets_cloud. אין משלוח ארצי. אין מחיר מומצא. אין אוטו-DM.

יש כבר מערכת משרד: קליטת לקוח, תמחור בלי המצאת ₪,
בדיקת כדאיות הדפסה, טיוטות מכירה, תוכן מהעבודה עצמה, לוח ייצור,
בריף בוקר ודשבורד בעלים.

מה לבנות או לייעל עכשיו — לא טריקי צמיחה.
1. מוצרים קלים להדפסה וקלים למכירה (מק״ט חוזר, לא רק מותאם)
2. המרת פנייה להזמנה
3. איכות תמונת המצב לבעלים
4. מערכות שחוסכות זמן / מונעות טעויות / קשורות להכנסה
5. תוכן שנובע מעבודות אמיתיות ומשרת מכירה

תן 3–7 ממצאים קונקרטיים. לכל ממצא: מקור ותאריך, מה למדנו,
מה עושים עם זה ב־Velvet Factory, ומה רמת הביטחון/המגבלה.
```

## חומות + failover

| מצב | מה עושים |
|---|---|
| מקור אחד חסום / Cloudflare / רובוט | דולגים עליו ומיד עוברים למקור ציבורי/ראשוני אחר. לא ממציאים. |
| חסר מפתח ChatGPT / Gemini | לא נדרש לריצת הבסיס. WebSearch נשאר מסלול ברירת המחדל. |
| כלי מנוי במק זמין | אפשר להשלים/להצליב, אבל מסמנים provenance. |
| אין שום אות מוצק | `אין חדש במשרד` + רשימת מקורות/חיפושים שנבדקו. |
| ריצה לא התבצעה | freshness נכשל; בריף מסמן Research YELLOW ומבצע fallback בלי לטעון שה־Research Seat רץ. |

פלייבוק מלא: `constitution/ORCHESTRA.md` → Failover.

## Ideation (ממופה, לא בוט חי)

לקוח אומר «אני צריך מעמד ל…»:

1. לתרגם את התיאור לעברית קצרה (`vfcopy`).
2. לחפש דגם במאגר פתוח. **נעילת בעלים למחקר:** מגבלת רישיון של יוצר זר אינה קריטריון פסילה/דירוג ב־Research Seat; יוצר/מותג ישראלי → `vlicense` / stop לפני שימוש בקובץ. זהו כלל triage מחקרי, לא קביעה משפטית לגבי שימוש בפועל.
3. אם אין דגם: הדמיה דו־ממדית לאישור. מידול או 3D AI Studio / Meshy/Tripo — רק אחרי אישור ראש צוות (`vfprod/3DAISTUDIO.md`).
4. מודל שנוצר ב־AI עדיין עובר סלייס; אם הוא מבוסס על יוצר/מותג ישראלי → `vlicense` / stop. לא נכנס לקטלוג לבד (`vfsku`).
5. סגירה מסחרית נשארת במסלול האנושי/המורשה; אין auto-DM.
