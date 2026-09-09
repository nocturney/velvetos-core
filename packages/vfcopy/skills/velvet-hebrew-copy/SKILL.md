---
name: velvet-hebrew-copy
description: >-
  Authority for Velvet Factory Hebrew writing style — natural Israeli Hebrew for a small
  3D-print studio in Sderot. Use when drafting or editing Instagram captions, Reels, carousels,
  stories, desk replies, or any public Hebrew copy for @velvets_cloud. Runs after brand/voice
  context and before vfigos review. Rejects ChatGPT-Hebrew, corporate tone, and invented facts.
license: MIT (VelvetOS Core; external ideas attributed in ADAPTATION.md)
---

# velvet-hebrew-copy

סמכות סגנון הכתיבה העברית של Velvet Factory.  
לא פק חדש. לא runtime מקביל. חיה בתוך `packages/vfcopy`.

מושב: סטודיו (`@content-creator` + `@brand-guardian`).  
חוקה + `VOICE.md` מנצחים תמיד. CTA ציבורי: `constitution/PUBLIC_CTA.md`.

## מתי

- כל טיוטת כיתוב / ריל / קרוסלה / סטוריז / תשובת דלפק בעברית ל־`@velvets_cloud` או למשרד.
- אחרי שיש הקשר מוצר/מדיה מאומת — לפני `#vfigos`.
- כשטיוטה «נשמעת כמו ChatGPT בעברית».

## סדר חובה (pipeline)

ראו `PIPELINE.md`. בקצרה:

1. verified media / product / order context  
2. business truth + constitution  
3. brand + Velvet voice (`VOICE.md` · `VOICE-CHART.md` · `voice/approved/`)  
4. writer לפי type (caption / carousel / reel)  
5. hook כשמתאים  
6. **velvet-hebrew-copy** (שכבה זו)  
7. style / AI-tells QA (`hq/ai-tells-he.md` + lint)  
8. factual / constraint validation  
9. **content candidate** | **needs_input**

אין שליחה מכאן. אין Publish. אין auto-DM.

## הקול

- עברית ישראלית טבעית — מדוברת, לא מתאמצת.
- סטודיו קטן להדפסות תלת־ממד בשדרות — לא משרד פרסום, לא corporate, לא «ChatGPT Hebrew».
- משפטים קצרים כשזה מתאים. לא חובה לספר «סיפור» על כל מוצר.
- פרט אמיתי מהרצפה עדיף על סלוגן. אין התלהבות מלאכותית.
- שני מצבים בלבד (`VOICE.md`): **תהליך-קצר** | **סיפור-מוצר**.

### מבחן מאפייה

אם אפשר להחליף «Velvet Factory» בשם מאפייה / מספרה / נגרייה / SaaS והטקסט עדיין עובד כמעט בלי שינוי — הקופי גנרי מדי. שכתבו עם פרט מהרצפה או החזירו `needs_input`.

## Business truth (חובה)

| חוק | פלט כשחסר |
|---|---|
| סטודיו קטן · שדרות · איסוף עצמי | הזכירו איסוף רק כשצריך CTA מוצר |
| אין משלוח ארצי | אל תמציאו משלוח |
| אין מחיר / מבצע / זמן הכנה / לקוח / testimonial / Insights **מומצאים** | claim מותר רק עם context מאומת (`price_verified` / `verified_facts`) שתואם; אחרת `needs_input` או `fail_fact` |
| אין auto-DM · אין Meta Business Suite | — |
| אין «שלחו DM» כברירת מחדל | PUBLIC_CURRENT_CTA = הודעת Instagram בעברית |
| אל תמציאו מידע חסר | `needs_input` — לא השלמה יצירתית |

**FACT CLAIM ≠ INVENTED FACT:** מספר/מחיר/זמן/שם לקוח בטקסט מותרים כשה־context מאמת ותואם. בלי verification → `needs_input`. סתירה ל־context → `fail_fact`.

מספר טלפון / handle: קחו מ־`constitution/PUBLIC_CTA.md` / desk / STUDIO — לא hardcode חדש.

## ברירות מחדל לפי פורמט

### Caption רגיל

- בדרך כלל 2–5 שורות.
- עברית טבעית. לא כרטיס ביקור. לא רשימת שירותים.
- CTA רק כשיש סיבה. אין חובת emoji / CTA / hashtags.
- עד 5 hashtags — רק אם באמת מועילים.

### Carousel

מבנה קרוסלה (שקופית כיסוי = הוק + הבטחה, רעיון אחד לשקופית) → hook → **velvet-hebrew-copy**.  
כיתוב נפרד לפי Caption. ויזואל: Canva (`vfcanva`).

### Reel

לוגיקת ריל (הוק ~3 שנ׳, עובד גם בלי סאונד, תהליך-קצר או סיפור-מוצר) → hook → **velvet-hebrew-copy**.  
כיתוב לפי Caption. סאונד: `vfresearch/MUSIC.md` — לא ממציאים שם track.

### SEO

השבחה בלבד (מילת חיפוש טבעית בשורה הראשונה כשמתאים). **אסור** לפגוע בטבעיות הקופי או לדחוס מילות מפתח.

## Voice learning

| Corpus | נתיב | שימוש |
|---|---|---|
| **approved / published** | `voice/approved/` | אימון קול · דוגמאות one-shot |
| **generated / unapproved** | `voice/generated/` | ארכיון טיוטות בלבד — **לא** ללמוד מהן |

רק תוכן שאישר אדם או שפורסם נכנס ל־`approved/`. אל תלמדו אוטומטית מטיוטות AI.

## QA

1. הרצה סטטית: `python3 scripts/check-vfcopy.py lint --text '…'`  
2. Eval suite: `python3 scripts/check-vfcopy.py eval`  
3. Pass אחרון ידני: `hq/ai-tells-he.md`  
4. בעיה סגנונית → rewrite אחד ממוקד (`lint --rewrite`).  
5. בעיה עובדתית → `needs_input`. אין loop אינסופי.

## פלט

```text
status: content_candidate | needs_input
mode: תהליך-קצר | סיפור-מוצר | desk
body: |
  …
notes: חסר / לינט / rewrite
```

## אל

- vendoring של social-media-skills / humanizer
- פק writing חדש מחוץ ל־vfcopy
- Publish / שינוי bio / captions חיים / secrets
- המצאת ₪ / משלוח / turnaround / לקוח / סיפור

## קישורים

- התאמת מקורות חיצוניים: `ADAPTATION.md`
- צינור: `PIPELINE.md`
- קול נעול: `../../VOICE.md` · `../../VOICE-CHART.md`
- לינט עברי: `../../hq/ai-tells-he.md`
- תבניות: `../../hq/templates/`
