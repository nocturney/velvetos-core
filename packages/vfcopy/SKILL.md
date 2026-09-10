# vfcopy — שולחן קופי / Visible Text Gate

מושב: סטודיו (+ specialist הדומיין לפי המשימה). לא סוכן חדש.

עבודה: context → reader-first → ניסוח → Humanizer/lint → fact/surface QA.  
רף סוכנות: עברית חזקה, טבעית, בלי מילוי; אמת תפעולית נשארת אמת ולא “מתייפה”.

**חוק רוחבי לכל טקסט אנושי שנכתב ב־AI:** `constitution/VISIBLE_TEXT.md`.  
**חוזה היישום:** `SOFT-TOOLS-CONTRACT.md`. הוא מחייב את השרשרת הרלוונטית על גרסת הטקסט הסופית — public, customer או owner — ולא רק Instagram.  
**קול פיד בלבד:** `VOICE.md` + `VOICE-CHART.md`; לא מחילים אותם בכוח על בריף בעלים/שיחה פרטית.  
**שכבת עברית:** `skills/velvet-hebrew-copy/` — סמכות סגנון + surface-aware pipeline + מבחן מאפייה + `needs_input`.  
קורפוס קול public: `voice/approved/` בלבד (לא `voice/generated/`).  
תבניות פרומפט משרד: `hq/templates/` (מתודולוגיה מ־prompts.chat; לא ייבוא CSV).  
לפני prose אנושי: `hq/reader-first-he.md`.  
כלי marketing soft skills לקופי שיווקי/מכירתי: `vfmskill` — `copywriting` + `copy-editing` + `marketing-psychology` כשישים; עובדים בתוך החוזה, לא כאלטרנטיבה אליו.  
Humanizer/anti-AI: `hq/ai-tells-he.md`.  
Executable gate לטקסט ספציפי: `python3 scripts/vf_visible_text.py --surface <surface> ...`; public captions יכולים להשתמש בנוסף ב־`python3 scripts/check-vfcopy.py lint`.  
Evals: `python3 scripts/check-vfcopy.py eval` — בודקים את המנוע, **לא** מוכיחים שטקסט מסוים עבר.

## Surfaces

- `public-social` — Caption/Story/Reel/Carousel/public bio; מוסיף VOICE/PUBLIC_CTA/vfgrowth.
- `visual-microcopy` — cover/overlay/first-frame/slide; מוסיף 3–5 candidates + `NO_TEXT` + Creative Director/Brand Guardian.
- `customer-message` — Gmail/WhatsApp/IG private reply; מוסיף vfconvert/vfsales/vfcost/vlicense כשישים.
- `sales-proposal` — quote/proposal/follow-up; מוסיף sales/cost truth + vfmskill writing aids כשישים.
- `owner-brief` — בריף/מייל/סיכום/החלטה לכריסטיאן; שומר IDs/status/numbers literal, בלי public CTA.
- `human-document` — PDF/DOC/slide/HTML/Canva prose; format QA אחרי text QA.
- `ui-microcopy` — dashboard/UI text; technical labels/source values literal.
- `desk` — טקסט אנושי אחר במשרד לפי domain context.

## חוק PASS

`visible_text_gate: PASS` מותר רק אחרי שהשלבים הרלוונטיים הופעלו על הטקסט המדויק. `VOICE.md`, CI, eval או קיום skill אינם receipt. חסר ביצוע → `UNPROVEN`; בעיית סגנון/עובדה → `FAIL/needs_input`.

שינוי מהותי אחרי lint/gate מבטל את ה־PASS. אם התוצר קשור ל־Rubric/PREFLIGHT/render digest, השינוי מבטל גם את האישורים התלויים בו. נוסח `approved_static_copy` ניתן למחזור רק כשהוא זהה והעובדות עדיין תקפות.

## מסירה

- customer/sales → `#vfsales` / Gmail send / WhatsApp human handoff רק אחרי gate.
- public/visual → `#vfgrowth` / Brand Guardian / `#vfigos` רק אחרי gate.
- owner brief → `vfbriefux` render/send רק אחרי owner-brief gate.
- human document → layout/render only after text gate.

HQ שולח דרך כלים רק לאחר gates הקנוניים (`constitution/SEND.md`).  
לוח/פיד: `vfgrowth/CALENDAR.md`; public CTA תמיד לפי `constitution/PUBLIC_CTA.md`; אין Canva/vfcovers/Brand QA כשנדרש = לא משבצים.
