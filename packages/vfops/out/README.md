# בריף — transport current + historical audit

נתיב ש־Grok / Cloud / GitHub יכולים לקרוא.  
`/opt/cursor/artifacts` ו־Origin tmp **לא** נגישים אחרי הסשן.

Stage 7D מפריד בין **transport staging** לבין היסטוריה: Morning Green חדש נכתב רק ל־`morning-green-current.html/json/txt` ול־`morning-green-assets-current/`. הקבצים האלה מוחלפים בריצה הבאה ואינם archive או source of truth. היסטוריית delivery נשמרת ב־compact receipts / factual records / Gmail provider evidence; עותקי תמונות היסטוריים גדולים הועברו copy-first ל־artifact archive, עם manifest ו־SHA-256 ב־`packages/velvetos/policy/reports/stage7d-morning-green-asset-archive.json`.

אין ליצור מחדש `morning-green-assets-YYYY-MM-DD/` או rendered bundle מתוארך כדרך רגילה. rollback של Stage 7D הוא Git revert + archive receipt, לא המצאת evidence חסר.

| קובץ | מה | שליחה |
|---|---|---|
| `BRIEF-2026-09-08.html` | htmlBody מלא 62504 בתים · יום שלישי 8 בספטמבר 2026 · אותם בתים ב־`2026-09-08/brief-2026-09-08.html` · sha256 `443ff9ff4918a21e6560d01b327f08cda133ed6c6cdb7de7a032b0b52af1069f` · `cid:` placeholders · קופסה: `/workspace/INSTA/brief-2026-09-08/send/` | **READY** — לא נשלח מ־Cloud Agent |
| `BRIEF-2026-09-07.html` | htmlBody תצוגה 3 · יום שני 7 בספטמבר 2026 · אותם בתים ב־`2026-09-07/brief-2026-09-07.html` | **ארכיון ל־Grok** — לא נשלח מייל |
| `BRIEF-2026-09-06.html` | htmlBody תצוגה 3 שנשלח 6.9.2026 07:17 Asia/Jerusalem | **ארכיון בלבד** — לא לשלוח שוב |

מקור: Gmail thread `1a074ed8b8427e69`.  
עותק יום קצר: `../BRIEF-2026-09-06.md`. תבנית חיה: `vfbriefux/MAIL.html`.
