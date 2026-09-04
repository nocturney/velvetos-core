# מעבר תזמורת · 4.9.2026 (Asia/Jerusalem)

מושב: ייצור + צמיחה קוראים בבריף.  
תבנית: `vfresearch/DAILY.md` — מערכות / מק״ט קל־להדפסה / המרה / בריף. לא האקי צמיחה.  
נתיב בלוק `05`: `packages/vfops/data/research.md`.  
סוכן: `bc-6d489ef4-35d5-4d0e-915a-c3f067c44ac1`.  
Grok Bot = החלטות בלבד.

כריסטיאן זמין ללוגין חד־פעמי (4.9 ~10:05 Asia/Jerusalem: try again).

## מה נשאל

ולווט פקטורי — סטודיו קטן בשדרות, איסוף בלבד. מה לבנות או לייעל במשרד הקיים: מק״ט חוזר קל־להדפסה, המרה, איכות בריף, מערכות שחוסכות זמן. בלי ₪, בלי אוטו־DM, בלי שכפול חנות.

## שלושה שולחנות — גוף / דילוג

אין MCP ל־ChatGPT / Gemini / Perplexity על Cloud Agent. נפתח בדפדפן.

| שולחן | גוף |
|---|---|
| ChatGPT Plus (Christian Velvet Plus) | **דולג — חומת גוגל.** `chatgpt.com` → Log in → Continue with Google → `nocturney@gmail.com` → Try another way → «Check your phone» (Gmail app) → speedbump `accounts.google.com/v3/signin/speedbump/endsession` · `app_domain=auth.openai.com`. טקסט: «You're already signed in on another device or browser» · «After 48 hours, check nocturney@gmail.com … for a link to help you sign in here.» אין גוף צ'אט. לא הומצא. |
| Gemini Plus | **דולג — אותה חומה.** אורח Flash-Lite קודם — **לא אורח.** Sign in → אותו חשבון גוגל → אותו speedbump (`checkedDomains=youtube`). אין גוף. לא הומצא. |
| Perplexity Pro | **דולג — Cloudflare ואז אותה חומה.** Ray `a35b2b88946d314f` (צ'קבוקס עבר). Continue with Google → speedbump `app_domain=perplexity.ai`. אין גוף. לא הומצא. |

לחיצה לכריסטיאן: אחרי 48 שעות מ-~10:26 Asia/Jerusalem (4.9) — `nocturney@gmail.com` (וגם ספאם) → קישור גוגל «help you sign in here». אין קוד מכשיר. אין סיסמה בצ'אט.

צילומים: `/opt/cursor/artifacts/chatgpt-login-4sep.webp`, `gemini-login-4sep.webp`, `perplexity-signin-4sep.webp`, `chatgpt-google-4sep.webp`, `chatgpt-phone-prompt-4sep.webp`, `desk1-chatgpt-after-wait-4sep.webp` (ומקבילים).

Gmail `#נשלח-מ-HQ` thread `1a06b4731aeaf4dc` (שלוש הודעות: סיסמה → Yes בטלפון → חומת 48ש׳).

## מה נבדק בגוף אמיתי (WebSearch / FAQ)

| מקור | סוג | משקל | מה לקחנו |
|---|---|---|---|
| [MakerWorld FAQ — Commercial License Membership](https://makerworld.com/en/faq) | FAQ רשמי | גבוה | «Get Commercial License» בדף הדגם. ביטול: גישה עד סוף מחזור החיוב, אין החזר. יוצר שמשנה תנאים → התראת מערכת עם השוואת ישן/חדש. PayPal בלבד אצלם — לא ממירים ל־₪ מכירה. |
| [Membership Agreement](https://makerworld.com/en/commercial-license-membership-agreement) | הסכם רשמי | גבוה | MakerWorld לא מעניקה רישיון; היוצר מעניק ישירות למנוי. |
| [Bambu Lab — Commercial License Membership](https://blog.bambulab.com/empowering-our-creators-with-new-commercial-license-membership/) | הודעת פלטפורמה | גבוה | כבר הוטמע 2.9 (מנוי ≠ רישיון לכל הדף). אין שינוי מבנה. |
| פוסט קהילה MakerWorld `1115817` (חיוב חודשי/רבעוני/שנתי) | WebSearch snippet | דולג | WebFetch לגוף מלא נכשל (timeout). אין גוף מלא — לא הומצא מחזור חיוב חדש. |
| MyMiniFactory / Cults fidget-clicker + מתג MX | דפי מוצר | דולג | חומרה = צהוב ב־`LAB.md` כבר. לא שם דגם. לא כרטיס. |
| Quotruder / Printago / Shopify / ManyChat | האקי קטלוג / חווה / אוטו־DM | דולג | לא בית. |

גופי שיתוף 30.8 / 31.8 על הדיסק — זהב למערכות. אין שינוי סדר בריף 01–07.

## מה הוטמע (מגוף אמיתי + פער משרד)

| ממצא | פק | לא |
|---|---|---|
| MakerWorld לא מעניקה רישיון; «Get Commercial License» בדף | `vlicense/GATE.md` | סכום מנוי כמחיר מכירה |
| ביטול = עד סוף מחזור החיוב ואז `waiting-license` | `vlicense/GATE.md` · `vfsku/FIRST-PRINT.md` | באצ׳ אחרי ביטול |
| שינוי תנאי מנוי → התראת מערכת → `licenseChecked` מחדש | `vlicense/GATE.md` · `FIRST-PRINT.md` · סנסור `check-vfsku.py` | באצ׳ על תנאים ישנים |
| מדף 0/5: אין שם מק״ט בטיוטת וואטסאפ | `vfcopy/DESK.md` | שם MakerWorld מהאוויר |
| נתיב הזדהות Cloud Agent (גוגל מכשיר חדש / 48ש׳) | `ORCHESTRA.md` · `DAILY.md` · `ROUTINE.md` · `vfgraft` blast/tools · `vfmcp/GAP.md` | המתנה בסרק בלי failover |
| זיכרון בעלים | `owner-memory.md` | סיסמה בגיט |

## מה דולג

| מה | למה |
|---|---|
| גוף ChatGPT / Gemini / Perplexity חי | חומת גוגל 48ש׳. אין גוף. לא הומצא. |
| אורח Gemini Flash-Lite | `DAILY.md`: לא אורח |
| חיוב רבעוני/שנתי מפוסט 1115817 | אין גוף מלא (timeout) |
| שמות fidget / clicker / מתג MX | חומרה צהובה; שער לא ממלא שם |
| #70 מדף-קודם / SHOP-CLOSE | כבר PR פתוח; לא כפילות היום |
| ₪ / Insights / בוסט / אוטו־DM / פרסום | נעול |
| שינוי סדר בריף 01–07 | נעול 30.8 |

## Failover שבוצע

ChatGPT → WebSearch + FAQ MakerWorld + פקים.  
Gemini → WebSearch + פקים.  
Perplexity → Cloudflare checkbox עבר, ואז אותה חומת גוגל → WebSearch.  
Treg — לא בשימוש.

## בלוק 05

```
מה נבנה / יועל: שער רישיון אחרי שינוי תנאי מנוי + נתיב הזדהות Cloud (`vlicense` / `vfresearch`)
```
