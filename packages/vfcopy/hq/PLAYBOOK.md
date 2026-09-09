# לינט טיוטה

לפני טיוטה: `hq/reader-first-he.md` (שתי שאלות + קליטת למי/מדף/סיפור — מקור: mikiarlo3/ai-copywriter, מוטמע בפק, לא plugin).  
שכבת עברית (חובה): `skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.  
Pass אחרון: `hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint [--rewrite]` (סימני AI בעברית — מקור: plannotator/write-better + Humanizer + social-media-skills ideas, מוטמע בפק).  
Evals: `python3 scripts/check-vfcopy.py eval`.

## אנטומיית פרומפט (מ־prompts.chat פרק 02)

לפני טיוטה — בנה/י מהרכיבים, לא «act as X» גנéric:

| רכיב | במשרד |
|---|---|
| **תפקיד** | סטודיו הדפסה · שדרות · איסוף בלבד |
| **הקשר** | שדות מפנייה: חומר, כמות, גימור, מתי — «חסר» / `needs_input` אם אין מקור |
| **קורא** | תחושה ברגע + למי/מדף/סיפור מ־`reader-first-he.md` — גנרי מדי = שאל לפני טיוטה |
| **משימה** | פעולה אחת: תשובה / מעקב / כיתוב IG |
| **אילוצים** | `VOICE.md` · `velvet-hebrew-copy` · CTA אחד · בלי ₪ · בלי «שלחו DM» עירום · בלי דדליין לפני `#vfprod` |
| **פורmat** | טקסט גולמי / מבנה ריל — ראה `hq/templates/` |
| **דוגמה** | one-shot מ־`voice/approved/` או מתוך התבנית; לא מ־`prompts.csv`; לא מ־`voice/generated/` |

תבניות מוכנות: `hq/templates/README.md`. מקור מתודולוגיה: `packages/vfresearch/sources/2026-08-31-prompts-chat-embed.md`.

פרומפטי **תמונה/וידאו** חיצוניים (YouMind וכו׳): לא מחליפים את האנטומיה הזו — ראו `vfcovers/hq/PLAYBOOK.md` (Canva קודם; התאמת נושא לרצפה בלבד).

## בודקים

- עברית טבעית, בלי «נשמח לעמוד לשירותך» / «אנו גאים להציג» / «חוויה ייחודית»
- מבחן מאפייה: אם מחליפים את שם הסטודיו במאפייה והטקסט עדיין עובד — גנרי מדי
- יודעים מה הקורא מרגיש ברגע הזה (לא רק «מי הקהל»)
- CTA אחד — **PUBLIC_CURRENT_CTA** = הודעת Instagram בתוכן ציבורי (`constitution/PUBLIC_CTA.md`)
- BUSINESS_CONTACT_RECORD וואטסאפ `050-2517000` נשאר פנימי / סגירה אנושית — לא בכיתוב ציבורי כרגע
- איסוף שדרות כשזה מסר מכירה מוצר
- אין ₪ אלא ממקור מאומת (`X ₪` במשרד)
- אין הבטחת דדליין לפני `#vfprod`
- אין קריאת «שלחו DM»
- כיתוב IG: קודם `VOICE.md` — **תהליך-קצר** או **סיפור-מוצר**; אחר כך `velvet-hebrew-copy`. האשטאגים עד 5, בלי ספאם
- בלי פתיחה ב«מוכנים» / «בלי משלוח». בלי קופי דק כמו G004 המוקדם
- pass אחרון: `ai-tells-he.md` + lint CLI (בלי ultimate/game-changer/unlock בעברית או באנגלית)
- עובדה חסרה → `needs_input` — לא rewrite יצירתי

G005 חי (`Dc0cKegEbxd`) — לא נוגעים.  
G003 נעול «מה יוצא מהמדפסת?» — משובץ 7.9 16:00 (חריג נעול; ריל תהליך חדש = תהליך-קצר ב־`VOICE.md`). G004 = קטלבל-מחזיק (לא משקולת) בסיפור-מוצר. לוח: `vfgrowth/CALENDAR.md`. המרת פרופיל: `vfgrowth/hq/FOLLOWER-GROWTH.md`. לא מיישמים על חשבון חי מכאן. `#vfigos` לסקירה; שיבוץ ב־instagram.com.

שפת לקוח משיחה: `@vfmakers brain capture` → `hq/customer-language.md`. `trust: unreviewed` עד שאדם מאשר.
