# תזמורת יומית · 2026-09-07

מושב: מחקר/אורקסטרציה · Asia/Jerusalem  
שני מעברים: #106 (~13:45, HQ-ROUTINE) + research-seat (הרצת כל החוקרים)

## מעבר A — #106 (~13:45)

מושב: מחקר/אורקסטרציה · Asia/Jerusalem ~13:45 (מעבר ערב — תוצר לבריף מחר)  
פלייבוק: `DAILY.md` · `ORCHESTRA.md` · `HQ-ROUTINE.md`

## שולחנות

| שולחן | סטטוס | הערה |
|---|---|---|
| ChatGPT API | חסר מפתח | `OPENAI_API_KEY` אין · לא נפתח chatgpt.com |
| Gemini API | חסר מפתח | `GEMINI_API_KEY` אין · לא נפתח gemini.google.com |
| Perplexity | לא מ־Cloud | failover → WebSearch |
| WebSearch | פעיל | failover נשא את העומס |

## מה נקרא (גוף אמיתי)

1. Versely — AI video for 3D printing / maker businesses 2026: קצב לולאת הדפסה / reveal / custom pitch; אורך ריל ~15–25ש לולאה, ~12–18ש reveal.
2. Reepli / Instagram Business Messaging 2026: IG לגילוי → המשך ב־WhatsApp להמרה (לא אוטו־DM).
3. מדריכי WhatsApp automation / n8n bots — **דולג מנדט** (סגירה אנושית `050-2517000`).

## מה הוטמע

- חיזוק יישור: לוח `vfgrowth/CALENDAR.md` כבר נועל ריל א׳/ג׳ + קרוסלה ה׳ — תואם דפוס maker cadence (בלי TikTok / בלי DM אוטומטי).
- אין שינוי קוד לוח — כבר קיים. שורת מחקר לבריף בלבד.

## מה דולג

| מה | למה |
|---|---|
| אוטו־DM / ManyChat / n8n WhatsApp bot | מנדט — אדם ב־050-2517000 |
| Meta Suite / TikTok | נעול |
| גוף ChatGPT/Gemini מנוי בדפדפן | Cloud אסור · חסר מפתח API |

## Insights

`posts.csv` — reach ריק ל־`DcqkjOLlYVX`. `vf_insights_loop.py` רץ: measured 0 · «אין ספירה».

## בלוק 05

מה נבנה / יועל: HQ-ROUTINE מולא + מושב מחקר על הדסק · failover WebSearch (חסר מפתח ChatGPT/Gemini) · insights loop בלי מספרים מומצאים

---

## מעבר B — research-seat (הרצת חוקרים מלאה)

מושב: מחקר/אורקסטרציה · Asia/Jerusalem  
טריגר: הרצת כל החוקרים (לא 06:15 בוקר — מעבר מלא לפי `HQ-ROUTINE` / `ROUTINE`)

## מה נשאל / מה רץ

| כלי | תוצאה | failover |
|---|---|---|
| `vf_semantic_search.py --build` | 3938 chunks · pkl מקומי | pip scikit-learn (תלות קיימת של הסקריפט) |
| `vf_insights_loop.py` | LEARNINGS נכתב · 0 measured | אין — ממתין ל־Dashboard בעלים |
| weekly links (`gh` + sourceNote) | 72 ללא שינוי · 4 חומות | לא chatgpt.com / gemini.google.com |
| LinklyAI best-skills `data/2026-09-07` | דירוג חי | `gh api` |
| LAST30 WebSearch + HN | ארטיפקט maker-IG | אין מפתחות X/TikTok |
| `vf_graceful_escalation --self-test` | OK downgrade | — |
| `vf_quote_ladder --known material=PETG` | partial + `חסר:` | — |

## מה הוטמע

- `vfconvert/hq/TRIAGE.md`
- `vfsales/scripts/vf_quote_ladder.py` + מצביע ב־`QUOTE.md`
- ארטיפקטים: weekly-links · best-skills · last30 · research.md

## מה דולג

| מה | למה |
|---|---|
| גוף ChatGPT/Gemini live | Cloud לא פותח מנוי |
| Insights / ₪ | אין מקור |
| npx skills / Orca / herdr | מנדט |

## בלוק 05

ראו `vfops/data/research.md` — שורות CLI אמיתיות מהמעבר הזה.
