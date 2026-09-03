# מעבר תזמורת · 3.9.2026 (Asia/Jerusalem)

מושב: ייצור + צמיחה קוראים בבריף.  
תבנית: `vfresearch/DAILY.md` — מערכות / מק״ט קל־להדפסה / המרה / בריף / חנות מחר. לא האקי צמיחה.  
נתיב בלוק `05`: `packages/vfops/data/research.md`.

## מה נשאל

ולווט פקטורי — סטודיו קטן בשדרות, איסוף בלבד. מה לבנות או לייעל במשרד הקיים: מק״ט חוזר קל־להדפסה, המרה, איכות בריף, מערכות שחוסכות זמן, **מה מקל על החנות מחר** (מדף 5, מינימום התאמה). בלי ₪, בלי אוטו־DM, בלי שכפול חנות.

Gmail: אין שיתוף מחקר חדש (3.9). לא מולא בריף מתיבה.

## שלושה שולחנות — גוף / דילוג

| שולחן | גוף |
|---|---|
| ChatGPT (צ'אט חדש, Plus) | **דולג — הזדהות.** `chatgpt.com` — «Log in or sign up». אין גוף. לא אורח. לא הומצא. `chatgpt-2026-09-03-skip.md` |
| Gemini (צ'אט חדש, Plus) | **דולג — אורח.** Sign in גלוי. מודל **Flash-Lite**. מענה אורח ב־`gemini.google.com/app/bc4c25f36d3f2937` **לא הוטמע** (`DAILY.md`: לא אורח). `gemini-2026-09-03-guest-skip.md` |
| Perplexity (צ'אט חדש, Pro) | **דולג — Cloudflare + חומת הרשמה.** Ray `a351ac363a7ef10f`. אחרי שליחה: «הירשם וחזור על הבקשה שלך.» אין גוף. לא הומצא. `perplexity-2026-09-03-wall.md` |

אין MCP לשולחנות האלה על Cloud Agent. סשן Chrome נקי — אין עוגיות Plus.  
2FA לא הופיע (התחברות לא הושלמה).

### מה צריך לחבר מחדש (ראש צוות)

1. ChatGPT Plus — Christian Velvet (Google / Apple / טלפון / אימייל).
2. Gemini Plus — אותו חשבון Google.
3. Perplexity Pro — Google / Apple / אימייל. Cloudflare עלול לחזור.

## מה נבדק בגוף אמיתי (WebSearch + פקים על הדיסק)

| מקור | סוג | משקל | מה לקחנו |
|---|---|---|---|
| זהב 30.8 / 31.8 על הדיסק (`chatgpt-6a9445c1.md`, `chatgpt-6a94f50b.md`, `gemini-92fe6256.md`) | שיתופי מנוי | גבוה | מדף 5 → וואטסאפ → איסוף. תשלום לפני מסירה. בלי שינוי 01–07. |
| [MakerWorld FAQ — Commercial License](https://makerworld.com/en/faq) | FAQ רשמי | גבוה | ללא שינוי מ־2.9: מנוי יוצר לפי דגם. Standard Digital File ≠ מכירה. לא כפילות סריקת ראשון/רביעי. |
| [ModelRover — SDFL 2026](https://modelrover.com/g/makerworld-standard-digital-file-license) | הסבר רישיון | בינוני | Fidget print-in-place תחת SDFL = אישי, לא מדף בלי רישיון מסחרי. כבר ב־`LAB.md`. |
| Made-by-Rice / Yorkshire3D (דפי שירות 2026) | תפעול חנות | נמוך־בינוני | דפוס: יחידה ארוזה/מסומנת לפי מק״ט + QC. **לא** ציטוט מחיר/משלוח. |
| Printie / print-farm SaaS | חוות ענן + משלוח | דולג | שכפול חנות / runtime שני / משלוח ארצי. |

גופי אורח Gemini 3.9 (מחירון קבוע, G-code מ־HQ, «3–5 רבי-מכר» בלי קישור) — **דולג.** לא הועתקו.

## מה הוטמע (מזהב 30.8 + פער משרד + failover ציבורי)

| ממצא | פק | לא |
|---|---|---|
| פנייה = מדף `ready` קודם, אחר כך מינימום התאמה, אחר כך מותאם | `vfconvert/PATH.md` · `CARD.md` | שם מק״ט כשהמדף ריק |
| טיוטות «יש במדף» / «מדף ריק» | `vfcopy/DESK.md` | אוטו־DM |
| סגירת יום: שקית + תווית + ספירה + תור מהזמנות | `vfprod/SHOP-CLOSE.md` | Printie / Shopify |
| `vfsku.py shop` — רק משבצות ready | `scripts/vfsku.py` | המצאת שם |
| תשלום + שקית לפני חלון איסוף | `vfbooks/PICKUP.md` | ₪ על תווית בלי סכום |
| יכולת + אינדקס + זיכרון | `capabilities.json` · `ARTIFACT-INDEX.md` · `owner-memory.md` | קונסולה שישית |

## מה דולג

| מה | למה |
|---|---|
| גוף ChatGPT Plus / Gemini Plus / Perplexity Pro | חומת הזדהות / אורח / Cloudflare. אין גוף מנוי. לא הומצא. |
| מחירון קבוע / נוסחת ₪ | נעול בלי ראש צוות |
| G-code / פרופיל סלייס מ־HQ | רצפה בלבד |
| שמות דגמי MakerWorld (fidget click / bearing spinner) | שער: לא ממלאים מהאוויר; SDFL לרוב |
| Printie / חוות ענן / משלוח | לא איסוף שדרות |
| שינוי סדר בריף 01–07 | נעול 30.8 |
| סריקת MakerWorld סיטונאית / מחקר רווח | ראשון+רביעי / שני — לא היום |

## Failover שבוצע

ChatGPT → פקים על הדיסק + WebSearch.  
Gemini אורח → **לא** failover-גוף; דילוג + פקים.  
Perplexity Cloudflare → דילוג גוף + WebSearch.  
Treg — לא בשימוש.

## סנסורים

`python3 scripts/check-all.py` — 19/19.  
סגירת hygiene: `access-blockers-2026-09-01.json` (JSON שבור מ־merge) + `grok-failover-2026-08-31.json` (`running` → `done`). לא שינוי מדיניות שליחה.

## בלוק 05

```
מה נבנה / יועל: מסלול מדף-קודם + סגירת חנות למחר (`vfconvert` / `vfprod`)
```
