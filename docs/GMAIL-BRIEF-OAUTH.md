# Gmail Brief OAuth · one-time owner setup

מטרה: בריף הבוקר נשלח דרך Gmail API של `nocturney@gmail.com` ללא אישור ChatGPT לכל הודעה, עם תמונות CID אמיתיות בתוך הכרטיסים.

## מה נשמר ואיפה

- בריפו: **אין** access token / refresh token / client secret.
- מקומית: `~/.config/velvetos/gmail-oauth.json` עם הרשאת `gmail.send` בלבד, chmod 600.
- GitHub Actions: repository secret יחיד בשם `GMAIL_OAUTH_JSON` שמכיל את אותו JSON.
- workflow: `.github/workflows/gmail-brief-send.yml` קורא את הסוד, שולח, ולא מדפיס אותו ללוג.

## שלב חד-פעמי ב-Google Cloud

בפרויקט Google Cloud שבבעלות Christian (כיום `instamcp`):

1. לוודא ש-**Gmail API** פעיל.
2. להגדיר OAuth consent עבור החשבון `nocturney@gmail.com`.
3. **לשימוש קבוע:** לא להשאיר את OAuth app ב-`Testing`. Google מגבילה refresh tokens של אפליקציות External במצב Testing לכ-7 ימים. להעביר ל-`In production` לפני שמכריזים על המסלול כ-production. בהתאם להגדרות החשבון/scope, Google עשויה להציג אזהרת unverified או לדרוש verification; אנחנו מבקשים רק את scope המינימלי `gmail.send`.
4. ליצור OAuth Client מסוג **Desktop app**. אין צורך ב-client מסוג Web.
5. להוריד את קובץ ה-client JSON למחשב מהימן. הקובץ הוא סוד; לא להעלות לריפו/צ'אט.

## יצירת refresh token

מתוך clone עדכני של `velvetos-core`:

```bash
cd velvetos-core
PYTHONPATH=packages python3 -m vfops.gmail_oauth_bootstrap \
  --client-secrets ~/Downloads/client_secret_XXXXX.json
```

ייפתח חלון Google. מאשרים לחשבון `nocturney@gmail.com` את scope השליחה בלבד. בסיום ייווצר:

```text
~/.config/velvetos/gmail-oauth.json
```

הקובץ כולל refresh token. לא מוחקים אותו עד שה-secret ב-GitHub הוגדר ונבדק.

## GitHub secret

Repository → Settings → Secrets and variables → Actions → New repository secret:

- Name: `GMAIL_OAUTH_JSON`
- Value: **כל התוכן** של `~/.config/velvetos/gmail-oauth.json`

ה-connector של ChatGPT ל-GitHub אינו חושף Secrets API, ולכן שלב הוספת ה-secret הוא owner action חד-פעמי.

## איך השליחה עובדת

HQ/ChatGPT יוצר HTML ומעדכן `packages/vfops/out/gmail-send-request.json` עם `enabled: true`.
Push ל-main של קובץ הבקשה מפעיל `.github/workflows/gmail-brief-send.yml`.

`vfops.gmail_brief_send`:
1. קורא HTML.
2. מוריד `<img src="https://...">` ציבוריים בבטחה ובמגבלת גודל.
3. מחליף אותם ל-`cid:remote-XX.ext`.
4. בונה `multipart/related` עם Content-ID תואם.
5. מרענן access token דרך refresh token.
6. שולח דרך Gmail API.

המקבל אינו תלוי ב-Canva/Instagram CDN אחרי השליחה; התמונה כבר חלק מהודעת MIME.

## הגנות

- recipient נעול כברירת מחדל ל-`nocturney@gmail.com`.
- remote images חייבות HTTPS וכתובת IP ציבורית; localhost/private/reserved נחסמים.
- max 12 remote images כברירת מחדל.
- max 8 MiB לתמונה כברירת מחדל.
- MIME/credential path נבדקים offline ב-`scripts/check-gmail-brief-send.py`.
- אין fallback שקט ל-attachment: כשל embedding מפיל את השליחה כדי שלא יישלח בריף שנראה תקין אבל בלי תמונות.

## בדיקת smoke לאחר הוספת secret

לאחר שה-secret נוסף, Christian אומר ל-HQ/ChatGPT `הוספתי`. HQ יעדכן את request ל-smoke test/brief אמיתי, ימזג ל-main, יוודא workflow success ו-Gmail message ID, ורק אז יעביר את Morning Brief production לנתיב הזה.
