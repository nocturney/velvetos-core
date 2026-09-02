# מעבר תזמורת · 2.9.2026 (Asia/Jerusalem)

מושב: ייצור + צמיחה קוראים בבריף.  
תבנית: `vfresearch/DAILY.md` — מערכות / מק״ט קל־להדפסה / המרה / בריף. לא האקי צמיחה.  
נתיב בלוק `05`: `packages/vfops/data/research.md`.

## מה נשאל

ולווט פקטורי — סטודיו קטן בשדרות, איסוף בלבד. מה לבנות או לייעל במשרד הקיים: מק״ט חוזר קל־להדפסה, המרה, איכות בריף, מערכות שחוסכות זמן. בלי ₪, בלי אוטו־DM, בלי שכפול חנות.

## שלושה שולחנות — גוף / דילוג

| שולחן | גוף |
|---|---|
| ChatGPT (צ'אט חדש) | **דולג — חומה.** `chatgpt.com` החזיר אימות JS/cookies. אין גוף חדש. לא הומצא. failover → WebSearch + פקים על הדיסק. |
| Gemini (צ'אט חדש) | **דולג — הזדהות.** `gemini.google.com/share/4f223bc1774c` → «direct access to Google AI» (סשן). אין גוף חדש. לא הומצא. failover → WebSearch. |
| Perplexity (צ'אט חדש) | **דולג — Cloudflare.** `perplexity.ai` Ray `a3496060b9b7e5b4`. אין גוף. לא הומצא. failover → WebSearch. |

אין MCP לשולחנות האלה על Cloud Agent. failover מיידי לפי `constitution/ORCHESTRA.md`.

## מה נבדק בגוף אמיתי (WebSearch / WebFetch)

| מקור | סוג | משקל | מה לקחנו |
|---|---|---|---|
| [Bambu Lab — Commercial License Membership](https://blog.bambulab.com/empowering-our-creators-with-new-commercial-license-membership/) (13.2.2025) | הודעת פלטפורמה | גבוה | מנוי יוצר ≠ רישיון אוטומטי לכל הדף. תנאים אצל היוצר. |
| [MakerWorld FAQ — Commercial License](https://makerworld.com/en/faq) | FAQ רשמי | גבוה | מנוי פעיל; ביטול = סוף מחזור החיוב. «Get Commercial License» בדף הדגם. |
| [PrintCal — sell prints from Printables/MakerWorld](https://printcal.co/en/blog/commercial-stl-license-printables-makerworld-sell-prints/) (11.6.2026) | מדריך תפעול | בינוני־גבוה | הפלטפורמה אינה הרישיון. לשמור URL + תנאים + תאריך. מנוי עלול לכסות רק חלק מהדגמים. |
| Printables / MakerWorld דפי דגמי PIP box (2025–2026) | דפי מוצר | נמוך לשם דגם | **קטגוריה** חיה: קופסה print-in-place / ציר מובנה. **לא** הועתק שם דגם לכרטיס. חלק דורשים מגנטים — חומרה = צהוב. |
| Quotruder / FocusSTL / GoldSTL / Get3DStl «best sellers 2026» | בלוגי מכירה / חבילות STL | דולג | האק קטלוג + ₪/$. לא בית. |
| Printago / Manuflo / Shopify print-farm | SaaS חווה | דולג | משלוח / חנות שנייה / runtime שני. דפוס «SKU = מוצר חוזר» כבר ב־GATE. |

גופי שיתוף 30.8 / 31.8 שכבר על הדיסק (`chatgpt-6a9445c1.md`, `chatgpt-6a94f50b.md`) — זהב למערכות: מדף 5, שער כדאיות, בריף 01–07. אין שינוי מבנה בריף.

## מה הוטמע (מגוף אמיתי + פער משרד)

| ממצא | פק | לא |
|---|---|---|
| מדף 5 משבצות כקובץ ריק | `vfsku/SHELF.json` | שמות/₪/כמויות מהאוויר |
| שעה אחת למשבצת + הוכחת רישיון | `vfsku/FIRST-PRINT.md` | הדפסה מ־HQ |
| סטטוס לבריף 03 | `scripts/vfsku.py` · `BRIEF.md` · `BRIEF-SLOTS.md` | בלוקים חלופיים ל־01–07 |
| סנסור מדף | `scripts/check-vfsku.py` | LLM-as-judge |
| הורדה ≠ רישיון; מנוי יוצר פעיל | `vlicense/GATE.md` · `GATE.md` | סכום מנוי כמחיר מכירה |
| כיוון קופסה PIP + חומרה=צהוב | `vfsku/LAB.md` | כרטיס בשם Flick/Flip |
| וי לפני באצ׳ מדף | `vfprod/CHECKLIST.md` | דמון מצלמה |
| ריל מדף רק אחרי `ready` | `vfgrowth/CALENDAR.md` | פוסט חי / בוסט |
| יכולת + אינדקס + זיכרון | `capabilities.json` · `ARTIFACT-INDEX.md` · `owner-memory.md` | קונסולה שישית |

## מה דולג

| מה | למה |
|---|---|
| גוף ChatGPT / Gemini / Perplexity חי | חומת JS / הזדהות / Cloudflare. אין גוף. לא הומצא. |
| שמות דגמים מ־Printables/MakerWorld | שער: לא ממלאים מהאוויר |
| חבילות flexi המוניות / Etsy niches | האק צמיחה + שכפול קטלוג |
| Printago / Shopify / חוות ענן | לא איסוף שדרות; runtime שני |
| ₪ / Insights / בוסט / אוטו־DM | נעול |
| שינוי סדר בריף 01–07 | נעול 30.8 |

## Failover שבוצע

ChatGPT → WebSearch + פקים.  
Gemini → WebSearch + פקים.  
Perplexity → WebSearch + פקים.  
Treg — לא בשימוש.

## בלוק 05

```
מה נבנה / יועל: מדף 5 מק״ט כקובץ + שער הדפסת ניסיון ורישיון (`vfsku`)
```
