---
name: velvet-hebrew-copy
description: >-
  Authority for Velvet Factory Hebrew writing style and human-facing AI text quality. Use for
  any Hebrew prose or microcopy created/rephrased by AI that Christian, a customer, the public,
  a partner, or another human will read: Instagram copy, cover/overlay text, Gmail/WhatsApp
  drafts, quotes, proposals, owner briefs/reports, desk replies, documents and UI microcopy.
  Runs after verified context/reader-first and before final display/send/render/publish. Rejects
  ChatGPT-Hebrew, corporate tone, generic copy and invented facts.
license: MIT (VelvetOS Core; external ideas attributed in ADAPTATION.md)
---

# velvet-hebrew-copy

סמכות סגנון הכתיבה העברית של Velvet Factory **לכל טקסט אנושי נראה** שנכתב ב־AI.  
לא פק חדש. לא runtime מקביל. חיה בתוך `packages/vfcopy` ומיישמת את `constitution/VISIBLE_TEXT.md`.

מושב: סטודיו (`@content-creator` + specialist הדומיין לפי המשטח).  
חוקה + אמת המשימה מנצחות תמיד. `VOICE.md` ו־`PUBLIC_CTA.md` חלים על public/social כשמתאים — **לא** בכוח על בריף תפעולי או שיחה פרטית.  
בקופי public בלבד: דוגמאות one-shot / למידת קול מגיעות מ־`voice/approved/` בלבד; לעולם לא מ־`voice/generated/`.

## מתי — חובה

- כל טיוטת כיתוב / ריל / קרוסלה / סטוריז / cover / overlay / first-frame בעברית.
- כל Gmail / WhatsApp draft / IG reply / follow-up / quote / proposal שהמשרד ניסח ללקוח.
- כל בריף, מייל, סיכום, החלטה או prose תפעולי שהמשרד מייצר לכריסטיאן.
- כל טקסט שנכתב ב־AI בתוך מסמך, PDF, מצגת, HTML, Canva או UI/dashboard ונועד לעין אנושית.
- כל תשובת דלפק או הסבר human-facing שניסח ChatGPT/Cursor/Gemini/Perplexity/Grok עבור המשרד.
- כשטיוטה נשמעת כמו ChatGPT בעברית, כמו סלוגן גנרי, או כשהטקסט אינו מוסיף דבר.

לא משכתבים verbatim source, ID, hash, URL, filename, code, raw log, machine JSON/CSV או מספר שנשלף ממקור. אם AI מוסיף סביבם הסבר — ההסבר כן עובר כאן.

## מצבי משטח

| mode | קורא | סמכויות נוספות |
|---|---|---|
| `public-social` | קהל Instagram | `VOICE.md` + `VOICE-CHART.md` + `voice/approved/` + `PUBLIC_CTA.md` + vfgrowth |
| `visual-microcopy` | קהל על cover/overlay/slide | Creative Director + Brand Guardian + `NO_TEXT` baseline |
| `customer-message` | לקוח בשיחה פרטית | `vfconvert`; `vfsales`/`vfcost`/`vlicense` כשישים; בלי public CTA בכוח |
| `sales-proposal` | לקוח/ליד | `vfsales` + facts/price approval + `vfmskill` copywriting/copy-editing כשישים |
| `owner-brief` | כריסטיאן | מקורות אמת של המשרד + reader-first; קצר, בהיר, לא שיווקי, בלי public CTA |
| `human-document` | אדם שקורא מסמך/HTML/מצגת | פק הדומיין + copy-editing כשישים; פורמט QA אחרי text QA |
| `ui-microcopy` | משתמש בדאשבורד/ממשק | reader-first + literal technical labels; בלי סלוגנים |
| `desk` | אדם במשרד | הקשר המשימה + הטון המתאים |

## סדר חובה

ראו `PIPELINE.md`. בקצרה:

1. verified context / source truth  
2. surface + intent + reader  
3. business/domain truth + constitution  
4. `reader-first-he.md`  
5. channel/domain writer tools הרלוונטיים  
6. **velvet-hebrew-copy**  
7. Humanizer / AI-tells + lint  
8. factual / constraint validation  
9. surface-specific QA  
10. `visible_text_gate: PASS` רק אם השלבים הרלוונטיים בוצעו בפועל

אין שליחה מכאן. אין Publish. אין auto-DM.

## הקול הבסיסי

- עברית ישראלית טבעית — מדוברת, לא מתאמצת.
- משפטים קצרים כשזה מתאים. לא חובה לספר סיפור על כל דבר.
- פרט אמיתי עדיף על סלוגן.
- אין התלהבות מלאכותית, corporate filler או “עומק” מומצא.
- הטון מותאם למשטח: owner brief ≠ Instagram caption ≠ customer quote.

### מבחן מאפייה

אם אפשר להחליף «Velvet Factory» בשם מאפייה / מספרה / נגרייה / SaaS והטקסט עדיין עובד כמעט בלי שינוי — הקופי גנרי מדי. שכתבו עם פרט אמיתי או החזירו `needs_input`.

### מבחן שיחה

אם אדם סביר לא היה אומר את המשפט בקול באותו מצב — בדקו מחדש. אין חובה להפוך הכול לסלנג; המבחן הוא טבעיות, לא “צעירות”.

## Truth / business constraints

| חוק | פלט כשחסר |
|---|---|
| אין המצאת מחיר / מבצע / turnaround / לקוח / testimonial / Insights / סטטוס | `needs_input` / `חסר` / `fail_fact` |
| public social של VF | CTA לפי `PUBLIC_CTA.md`; בלי WhatsApp ציבורי |
| private customer message | CTA/ערוץ לפי השיחה וה־business record; לא להעתיק public CTA אוטומטית |
| owner brief | preserve IDs/נתונים; בלי לייפות מצב או להמציא “התקדמות” |
| sales/quote | סכום רק אחרי מקור/אישור; `vfsales`/`vfcost` קודמים לקופי |
| טקסט מקור/ציטוט | literal; לא “humanize” את המקור |

**FACT CLAIM ≠ INVENTED FACT:** עובדה מותרת כשה־context מאמת ותואם. בלי verification → `needs_input`; סתירה → `fail_fact`.

## Public/social

### Caption

- בדרך כלל 2–5 שורות כשמתאים.
- CTA רק כשיש סיבה.
- עד 5 hashtags ורק אם מועילים.
- `VOICE.md` + `VOICE-CHART.md` + `voice/approved/` + `PUBLIC_CTA.md` מחייבים.

### Carousel / Reel

מבנה הקריאייטיב קודם; הקופי מוסיף פואנטה ולא מחליף ויזואל. Reel sound מטופל ב־`vfresearch/MUSIC.md`.

### Cover / Overlay microcopy

- טקסט על תמונה **אינו ברירת מחדל**.
- 3–5 ניסוחים + `NO_TEXT` baseline.
- כל ניסוח: reader-first → velvet-hebrew-copy → Humanizer/AI-tells.
- הטקסט חייב להוסיף פואנטה/פרט/מתח/payoff/סיבה להמשיך.
- תיאור מילולי של מה שכבר רואים, “משפט אווירה” או ניסוח שניתן להחלפה בין מוצרים = FAIL.
- אם הטקסט לא מנצח את הוויזואל הנקי → `NO_TEXT`.
- בחירת בעלים מפורשת היא preference חזקה; לא מחזירים אותה אוטומטית לשיווק גנרי.

## Customer messages / quote / proposal

1. התחילו ממה שהלקוח שאל בפועל.
2. `vfconvert` מספק missing fields/context; `vfsales` את מבנה המכירה; `vfcost` את המספרים; `vlicense` רק כשישים.
3. כתבו תשובה אחת ברורה, לא “נאום שירות”.
4. מחיר/מועד/יכולת רק אם אומתו.
5. persuasive/long-form יכול להוסיף `vfmskill` copywriting/copy-editing — לא במקום Humanizer.
6. private customer thread אינו מחויב ל־PUBLIC_CURRENT_CTA של הפיד.

## Owner brief / report / direct office prose

- פותחים במה שכריסטיאן צריך לדעת/להחליט/לעשות — לא ברקע ארוך.
- שומרים IDs, hashes, סטטוסים, תאריכים ומספרים בדיוק.
- מפרידים עובדה / inference / recommendation כשזה משנה החלטה.
- אין corporate filler, אין “הכול מצוין” אם sensor אדום, ואין סלוגנים.
- Humanizer משפר טבעיות בלבד; אסור לו לרכך חסם אמיתי או לשנות משמעות טכנית.

## Human documents / UI

- טקסט שנועד לקריאה במסמך/HTML/מצגת עובר כאן לפני layout final.
- UI microcopy AI-authored עובר reader-first + Humanizer; labels טכניים קנוניים נשארים literal.
- שינוי טקסט אחרי QA של מסמך/ויזואל עשוי לבטל render QA לפי מערכת הפורמט.

## Approved static copy

נוסח קבוע יכול לקבל `approved_static_copy` לאחר מעבר מלא. reuse מותר רק כשהטקסט זהה. שינוי מהותי → gate מחדש. זה מאפשר תבניות יציבות בלי “להריץ יצירתיות” על כל render.

## QA

1. `hq/reader-first-he.md` לפני ניסוח.  
2. `python3 scripts/check-vfcopy.py lint --text '…'` או `scripts/vf_visible_text.py --surface <surface>` על המועמד בפועל.  
3. Pass ידני/agent: `hq/ai-tells-he.md`.  
4. `vfmskill` copywriting/copy-editing כשסוג הטקסט מצדיק.  
5. factual/domain validation אחרי style.  
6. surface-specific QA.  
7. אין `visible_text_gate: PASS` אם שלב רלוונטי לא הופעל בפועל.

## פלט

```yaml
status: content_candidate | needs_input | draft
mode: public-social | visual-microcopy | customer-message | sales-proposal | owner-brief | human-document | ui-microcopy | desk
visible_text_gate: PASS | FAIL | UNPROVEN
truth_checked: PASS | FAIL
reader_first: PASS | FAIL
copy_authority: PASS | FAIL
humanizer_ai_tells: PASS | FAIL
surface_qa: PASS | FAIL
body: |
  …
notes: …
```

במסלול שיש בו preflight/artifact קיים, רושמים את השדות שם; לא בונים approval queue חדש. אם יש digest — ה־PASS קשור לטקסט/חבילה המדויקים ושינוי טקסט מבטל אותו.

## אל

- פק writing חדש מחוץ ל־vfcopy
- PASS ידני בלי ביצוע
- Publish/send מתוך skill זה
- המצאת ₪ / משלוח / turnaround / לקוח / סיפור / סטטוס
- טקסט על cover רק כדי שיהיה משהו כתוב
- להפעיל public social voice על בריף תפעולי או שיחה פרטית

## קישורים

- חוק רוחבי: `../../../constitution/VISIBLE_TEXT.md`
- צינור: `PIPELINE.md`
- קול public: `../../VOICE.md` · `../../VOICE-CHART.md` · `../../voice/approved/`
- reader-first: `../../hq/reader-first-he.md`
- Humanizer/AI-tells: `../../hq/ai-tells-he.md`
- תבניות: `../../hq/templates/`
- מסגרות marketing: `../../../vfmskill/EMBED.md`
