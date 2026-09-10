# Visible Text Gate — כל טקסט שנכתב לעין אנושית

נעילת בעלים: 2026-09-11 · Asia/Jerusalem.

## החוק

כל טקסט ש־AI יצר, ניסח מחדש או השלים ושמיועד להיראות על־ידי **כריסטיאן, לקוח, קהל, שותף או כל אדם אחר** חייב לעבור את כלי הכתיבה והאימות הרלוונטיים **לפני** שהוא מסומן final / ready / send / publish / render.

החוק חל על ChatGPT, Cursor, Gemini, Perplexity, Grok וכל סוכן/סקריפט שמייצר prose או microcopy עבור VelvetOS / Velvet Factory.

`vfcopy` הוא שכבת הכתיבה הקנונית; אין להקים writer/runtime מקביל.

## מה נחשב Visible Text

- תשובה/המלצה/סיכום שמוצגים לבעלים במשרד, בדאשבורד, בבריף או במייל.
- Gmail ללקוח או לבעלים, WhatsApp draft, Instagram reply/caption/Story/Reel/Carousel copy.
- הצעת מחיר, הצעה מסחרית, מסמך ללקוח, הודעת סטטוס, follow-up.
- cover headline, overlay, first-frame text, slide copy, CTA, UI microcopy שנוצרו או שוכתבו ב־AI.
- טקסט בתוך PDF/DOCX/מצגת/HTML/Canva שנועד להיקרא בידי אדם.

## מה לא עובר "האנשה"

מקור חייב להישאר מקור: ציטוט verbatim, ID, hash, URL, filename, קוד, JSON/CSV מכונה, לוג גולמי, ערך מספרי שנשלף ממקור, או label דטרמיניסטי קנוני. אם AI מוסיף סביבם הסבר/כותרת/סיכום — החלק שנכתב ב־AI כן עובר את השער.

טקסט סטטי שאושר מראש יכול להישמר כ־`approved_static_copy` ולהיות ממוחזר רק כשהטקסט זהה. שינוי תו מהותי מחזיר אותו לשער.

## Baseline חובה לטקסט עברי שנכתב ב־AI

1. **Truth/context first** — לקרוא את מקורות האמת של המשימה; אין השלמת עובדות יצירתית.
2. **Reader-first** — `packages/vfcopy/hq/reader-first-he.md`: מי קורא, באיזה רגע, ומה הדרך הפשוטה לומר את הדבר.
3. **Surface/intent route** — לבחור את מסלול הערוץ למטה; לא להלביש קול Instagram על בריף תפעולי.
4. **velvet-hebrew-copy** — `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` דרך `.cursor/skills/vf-hebrew-copy/SKILL.md`.
5. **Humanizer / AI-tells** — `packages/vfcopy/hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint --text '…'`.
6. **Factual/constraint validation** — מחיר, זמן, לקוח, claim, סטטוס, CTA, רישיון/פרטיות או נתון אחר רק ממקור/פק רלוונטי.
7. **Surface-specific QA** — visual, sales, brief, public, document או UI לפי הטבלה.

`vfmskill` `copywriting` / `copy-editing` הוא כלי נוסף כאשר הטקסט שיווקי/מכירתי/ארוך ודורש מסגרת כזו; הוא לא מחליף את `velvet-hebrew-copy` או את Humanizer.

## מסלולים לפי משטח

| משטח | כלים/מקורות נוספים שחובה כשישים |
|---|---|
| Instagram caption / Story / Reel / Carousel | `VOICE.md` + `VOICE-CHART.md` + `PUBLIC_CTA.md` + `CONTENT-RUBRIC.md`; visual copy עובר גם Brand Guardian |
| Cover / overlay / first-frame / slide text | `reader-first` → `velvet-hebrew-copy` → Humanizer → 3–5 candidates + `NO_TEXT` → Creative Director/Brand Guardian; טקסט שלא מנצח ויזואל נקי לא נכנס |
| Gmail / WhatsApp / IG reply ללקוח | `vfconvert`/Client Record + `vfsales` כשמכירתי + `vfcost` למחיר/עלות + `vlicense` רק אם רלוונטי; אחר כך `vfcopy` + Humanizer; אין public-CTA rules בכוח על שיחה פרטית |
| Quote / proposal / sales follow-up | `vfsales` + `vfconvert` + facts/price approval + `vfmskill` copywriting/copy-editing כשמועיל + `vfcopy` + Humanizer |
| בריף/מייל/סיכום/החלטה לבעלים | מקורות אמת של המשרד + `reader-first` במצב `owner-brief` + `velvet-hebrew-copy` במצב תפעולי + Humanizer; בלי סלוגנים, בלי public CTA, בלי לשנות IDs/נתונים |
| מסמך/מצגת/HTML שנועדו לאדם | פק הדומיין + `vfcopy`; marketing/sales document מוסיף `vfmskill` copywriting/copy-editing; QA של הפורמט בא אחרי QA הטקסט |
| UI/dashboard microcopy שנכתב ב־AI | `reader-first` + `vfcopy` + Humanizer; labels טכניים קנוניים נשארים literal |

## פלט/סטטוס

טקסט חדש שנכתב ב־AI אינו `ready` רק משום שהוא קיים. לפני surface final נדרש לפחות:

```yaml
visible_text_gate: PASS
surface: <public-social|visual-copy|customer-message|sales-proposal|owner-brief|human-document|ui-microcopy>
language: <he|en|mixed>
truth_checked: PASS
reader_first: PASS
copy_authority: PASS
humanizer_ai_tells: PASS
surface_qa: PASS
```

במסלול שיש בו artifact/preflight קיים, השדות נרשמים **שם** ולא נוצרת מערכת approvals שנייה. אם קיים digest לטקסט/חבילה, ה־PASS חייב להיות קשור ל־digest המדויק. שינוי מהותי בטקסט מבטל אותו.

אין לכתוב `PASS` אם הכלי/שלב לא הופעל בפועל. בלי הוכחת ביצוע: `UNPROVEN` / `BLOCKED`, לא סימון ידני מזויף.

## Owner preference

ניסוח שהבעלים בחר מפורשות הוא preference חזקה. הוא עדיין עובר אמת/קריאות/Humanizer, אבל אין "לשפר" אותו חזרה לניסוח שיווקי גנרי או לשנות את הפואנטה בלי סיבה.

## Fail closed

- מותר להחזיק `DRAFT` פנימי לפני השער.
- אסור לשלוח ללקוח, לפרסם, לרנדר כ־final, או להציג לבעלים כטקסט גמור אם ה־Visible Text Gate נכשל.
- אם כלי כתיבה רלוונטי לא זמין: לא ממציאים PASS; משתמשים ב־failover הקיים או מסמנים שהטקסט עדיין draft.
- שער תפעולי זה אינו תחליף לבדיקות חוק, מחיר, פרטיות, brand, visual או publish; הוא מצטרף אליהן לפי המשטח.
