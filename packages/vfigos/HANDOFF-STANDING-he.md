# מסירה לסטודיו — Publisher + Calendar mirror

**מקור אמת לתזמון:** Cloudflare Publisher (`PUBLISHER.json`).
**יעד:** `@velvets_cloud` · `Asia/Jerusalem`.
**Google Calendar:** יומן `אינסטגרם` הוא mirror לקריאה בלבד לפי `vfgrowth/CALENDAR-OPS.md`.

אין שיבוץ חדש דרך `instagram.com`, OpenPost, Buffer או Meta Suite. Immediate publish נשאר דרך Instagram MCP עם authorization המתאים; future schedule נוצר כ־job immutable ב־Publisher.

## איך משבצים עכשיו

1. final media + caption עוברים את שערי האיכות/זכויות/PREFLIGHT ונבנה context מדויק ל־`policy_id: instagram.publish`.
2. ה־evaluator קובע `ALLOW` / `DENY` / `REQUIRE_OWNER_APPROVAL`. אישור בעלים נקודתי נדרש רק כאשר זו תוצאת המדיניות; standing authorization תקף יכול להספיק למסלול LOW-risk שגרתי.
3. המדיה המדויקת עולה ל־Publisher KV עם SHA-256 ומאומתת read-back.
4. נוצר D1 job עם `authorization.kind=policy_authorization_v1`, evidence ו־`policy_context`; ה־Worker מחשב בעצמו את digest הכיתוב ואת bindings של content/package/media ומריץ את ה־evaluator לפני acceptance.
5. קוראים את ה־job חזרה ומוודאים `scheduled_at`, status, media hashes ו־policy decision receipt.
6. Calendar mirror יוצר/מעדכן אירוע ביומן `אינסטגרם`; זה visibility בלבד ולא תנאי ל־schedule.
7. לאחר הזמן: `published_verified` דורש Graph read-back/permalink; אז Media Vault/ledger נסגרים.

שינוי זמן/קופי/מדיה אחרי enqueue = cancel + job חדש + authorization חדש. אין mutation שקט.

## היסטוריית Google Calendar הישנה

החלק הבא נשמר כ־provenance בלבד. מזהים ומשבצות היסטוריים אינם מקור אמת לתזמונים חדשים.

## אירועי Google Calendar — רשת #90 (תפעול 6.9, בלי לשאול משבצת)

`nocturney@gmail.com` · תזכורת לעין, לא תחליף לשיבוץ instagram.com.

| מזהה | event id | מתי (Asia/Jerusalem) |
|---|---|---|
| VF-G003 | `42c1st7oj0ksfrulajm5h5n8ms` | א׳ 7.9 16:00 ריל · משובץ |
| VF-G004 | `ggv7dl8ho0hekr45blroksrt6k` | סטוריז 7–11.9 20:30 · יומי ×5 · חסום שער עריכה |
| VF-G006 | `m68f495b040kv05lekduu7q8ho` | ה׳ 11.9 12:00 קרוסלה · מועמד G004 |

אירועי 5.9 על רשת 8.9/10.9/13.9 — מיושנים. לא לשבץ לפיהם.

## כבר חי — לא נוגעים

| מזהה | מועד שעבר | קישור |
|---|---|---|
| VF-G001 | א׳ 30.8 16:00 | `instagram.com/p/DcqkjOLlYVX/` |
| VF-G002 | ג׳ 1.9 16:00 | `instagram.com/p/DcvuJLxCJgU/` |
| VF-G005 | ה׳ 3.9 12:00 | `instagram.com/p/Dc0cKegEbxd/` |

## מה דולג / חסום

- Meta Suite / Creator Studio / Buffer / Later / Bolta / Metricool כמעלה
- אוטו־DM · follow-back · צפיית סטורי כטריק · בוסט בלי ראש צוות
- פיד **שישי–שבת**
- המצאת מדיה, טיימלאפס, או סצנת רצפה
- ₪ בכיתוב או בפריים
- וואטסאפ / `050-2517000` בכיתוב ציבורי · אוטו־DM / «שלחו DM» ככלי (CTA: שלחו לנו הודעה כאן באינסטגרם · איסוף שדרות)
- החלפת G001 / G002 / G005 החיים
- שינוי כיתוב מאושר בלי אישור חדש
- פק חדש
- שליחת Gmail/IG ממשימת הלוח הזו

## G003 / G004 (אחרי נעילת 6.9)

G003 כבר `#משובץ` — לא מבקשים גלם חדש לשיבוץ. נתיב מדפסת = גיבוי בלבד.  
G004: מדיה בתיבת Grok (`INSTA/media/kettlebells-pink-…`) · כיתוב **`vfcopy/G004.md`**.  
CTA: שלחו לנו הודעה כאן באינסטגרם · היילייטס (`PUBLIC_CURRENT_CTA`). פריים עם וואטסאפ על המסך = revised-media needed.
