# Velvet Visual OS

מושב: צמיחה · מודול `expert-media-director`. זהו מקור האמת הוויזואלי של Velvet Factory עבור תוכן אורגני. הוא מרחיב את חוקי המותג הקיימים; כשחסר צבע/פונט מאומת — לא ממציאים ערך חדש.

Machine-readable projection: `VISUAL-DNA.json`. אם יש סתירה, המסמך הזה וחוקי ה־constitution גוברים; ה־JSON נועד לאורקסטרציה/QA ולא ליצור מותג חדש.

## Owner-approved visual reference · cold-start invariant

For Velvet Factory public visual work, `OWNER-APPROVED-GRID-STANDARD-2026-09-14.md` and `VELVET-VISUAL-SYSTEM-PROMPT.md` are mandatory instance authorities. The canonical public visual reference is `reference/velvet-approved-grid-2026-09-14.jpg` / Canva asset `MAHVL7PKpvE`, bound to SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. A cold-start conversation or agent must load and verify that identity before creative generation. Missing/mismatched identity is fail-closed; there is no fallback to generic model aesthetics. Product Truth, rights and factual source evidence remain higher authority than style.

## DNA

- תחושה: מעבדת חומרים חכמה, טקטית, חמה ולא תאגידית.
- צילום: מאקרו, close-up, ידיים עובדות, מוצר בתנועה, הוכחה פיזית אמיתית.
- רקעים: שולחן עבודה אמיתי, טקסטורת חומר, או שחור/אפור/לבן נקי.
- תאורה: אור קשה ומכוון או אור יום רך; לא ערבוב אקראי בתוך אותו נכס.
- טיפוגרפיה: היררכיה קבועה, מקסימום שני פונטים מאומתים. חסר פונט מאומת = להשתמש בתבנית קיימת, לא לבחור חדש.
- תנועה: hard cut כברירת מחדל. Slow motion רק ברגע הוכחה/מבחן משמעותי. אין intro לוגו ארוך.
- סאונד: רכיב קריאייטיב מלא, לא שכבת קישוט בסוף. עדיפות לסאונד אמיתי של הסטודיו כאשר הוא שימושי; מוזיקה/SFX תומכים בסיפור ולא מחליפים הוכחה.
- עברית: קצרה, טבעית, מדוברת ומדויקת. לא “שיווקית AI”.

## Reference-role separation · owner correction 2026-09-18

Product Truth is a **fidelity constraint, not an aesthetic reference**. Resolve look/feel only from the approved broad visual reference, editorial reference and current-creative reference. Resolve physical truth from the actual product source pixels plus the text Product Truth guide.

Do **not** pass Product Truth QA boards/teaching sheets into image-generation, style-transfer, moodboard or aesthetic-conditioning inputs. `Velvet-Factory-PRODUCT-TRUTH-REFERENCE-v2.png` is explicitly rejected for creative conditioning because it pushed results toward an unaesthetic technical-board look. Keep its lessons as text/QA rules only.

## Visual Finishing Protocol · always-on

כל נכס סטילס/פוסט/סטורי/קרוסלה/cover שעובר עיבוד חייב לעבור את ארבעת השלבים הבאים לפני שהוא נחשב final:

1. `photo_retouch` — איזון לבן, חשיפה, קונטרסט, highlights/shadows, ניקוי רעש, חידוד טבעי, ניקוי רקע, יישור פרספקטיבה, crop, subject separation ושיפור תאורה.
2. `brand_content_styling` — התאמה לשפת Velvet, היררכיה נקייה, מוקד מוצר ברור, שימוש בצבעים/פונטים מאומתים בלבד והתאמה לפורמט היעד.
3. `text_layout_qa` — עברית RTL, קריאות במובייל, contrast, safe margins, הימנעות מאזורים עמוסים, היררכיית כותרת/תמיכה/CTA ורק טקסט שמנצח `NO_TEXT` כאשר הוא באמת מוסיף ערך.
4. `final_visual_qa` — exact-final review על התוצר המרונדר, כולל Product Truth, Brand Guardian, קריאות, crop, safe areas, consistency ו־artifact checks.

הכלל העליון: **Retouch the photo, not the product.**

### Creative transformation floor · fail-closed

`Retouch the photo, not the product` does **not** mean `do almost nothing`. For publication-prep, preserve the physical product while deliberately transforming its presentation. Default to source-image edit/reference mode, not text-to-image recreation of the product. At least the hero/first slide must visibly improve two or more presentation dimensions such as environment/background, lighting/depth, composition/perspective, subject separation or atmosphere. A raw-photo carousel, resize-only sequence, or crop+exposure-only pass is not a finished Velvet creative unless the source was already at the owner-approved reference bar and that exception is explicitly documented. See `CREATIVE-TRANSFORMATION-LOCK.md`.


### Product Truth · fail-closed

במוצר פיזי אמיתי, העורך רשאי לשפר את הצילום וההצגה בלבד. אסור לשנות או להמציא:

- product identity;
- geometry / silhouette / proportions;
- part count;
- visible surface pattern;
- material identity;
- צבע מוצר מאומת, אלא אם המשימה במפורש מבקשת וריאנט עיצובי/צבעוני מסומן שאינו מוצג כצילום אמת.

`synthetic_subject_change` חייב להיות `NONE`, ו־`source_subject_match` חייב לעבור. שינוי רקע, cleanup או תאורה מותר רק אם אינו משנה את המוצר, אינו מסתיר מידע מהותי ואינו יוצר claim פיזי מומצא.

**Owner correction · 2026-09-18:** עריכת צילום בסיסית של מקור מאומת אינה הפרת Product Truth בפני עצמה. מותר לבצע brightness/exposure, קונטרסט מתון, white balance/טמפרטורת צבע, איזון highlights/shadows, חידוד קל, ניקוי/הפחתת רעש עדינים, crop/יישור ושיפור מתון של הפרדת הנושא/התאורה. אין לסמן פעולות אלה כ־`synthetic_subject_change` כל עוד המוצר נשאר אותו אובייקט פיזי ואין שינוי מהותי בטקסטורה/חומר, אלמנטים, גיאומטריה, סילואט, פרופורציות, פרטים מזהים, pattern נראה, עיניים/פנים מוגנים או צבע המוצר האמיתי. ההיתר הזה אינו הופך crop/exposure/contrast-only ל־creative treatment מספיק בפני עצמו.

כשל בשלב כלשהו אינו “הערה”; הוא חוסם publish ומנותב ל־targeted repair. כשל איכות רגיל מתוקן אוטונומית ונבדק שוב. רק חסם פיזי/זכויות/עסקי אמיתי מגיע לבעלים.

## First-frame law

הפריים הראשון חייב להתחיל בפעולה, תוצאה, מתח, פרט ברור או הוכחה. אין פתיח לוגו ואין “היי חברים”. לכל Reel לייצר 3–5 candidates ולבחור אוטונומית את החזק ביותר לפי בהירות, תנועה, ניגוד, קריאות וסקרנות.

## Proof-first law

Storyboard מתחיל מהוכחה או מאירוע פיזי אמיתי כשיש כזה: עומס, תנועה, התקנה, לפני/אחרי, מדידה, כשל→תיקון או מעבר מהדפסה לשימוש. אם אין proof asset מתאים, אין להמציא מבחן AI; יש לשנות פורמט או להוציא `shotRequest` מינימלי.

כל claim פיזי חייב להיות מגובה ב־Content Contract לפי `CONTENT-CONTRACT.schema.json`. `verified_real` של נכס אינו מוכיח אוטומטית כל טענה עליו.

## Shot vocabulary

`hero` · `macro` · `process` · `failure` · `proof` · `human` · `b-roll`.

בכל creative plan לציין לכל shot: סוג, אוריינטציה, זווית, מרחק, משך משוער, פעולה, ומה הוא מוכיח. חומר פיזי שחסר הופך ל־`content.media_needed`; לא ממציאים scene.

## Audio Gate · חובה לכל Reel / וידאו Story

Audio נבחר בזמן ה־storyboard והעריכה, לא אחרי שהווידאו כבר “מוכן”. כל Creative Manifest של וידאו חייב להגדיר `audioStrategy` ולבחור בפועל אחת מהאפשרויות: source · music · SFX · source+music · source+SFX · intentional silence.

לפני exact-final QA חייבים לבדוק:
- האם קיים audio stream אמיתי בתוצר הסופי;
- loudness בפועל — stream שקיים אבל כמעט אילם אינו PASS;
- clipping/noise בסיסי;
- sync מול העריכה/תנועה;
- האם הקצב והאנרגיה תומכים ב־first frame, proof וה־ending;
- ducking כשיש VO/סאונד מקור חשוב.

**ברירת המחדל לשקט או near-silence היא FAIL → audio repair.** שקט יכול לעבור רק כהחלטה קריאייטיבית מכוונת עם סיבה כתובה ובדיקת Brand Guardian; אסור להגיע לשקט בגלל שחומר המקור לא הכיל סאונד או כי שלב האודיו נשכח.

כשנדרשת מוזיקה/סאונד לפלטפורמה, להשתמש ב־`.cursor/skills/vf-ig-music/SKILL.md` + `packages/vfresearch/MUSIC.md`. לא להמציא שם טרנד או להשתמש במוזיקה מוגנת מחוץ למסלול המותר. אם הבחירה נעשית מתוך ספריית Instagram בזמן הפרסום, היא עדיין חייבת להיות החלטה מתועדת מראש ולהיבדק כחלק מחבילת הפרסום/verification.

## Covers

לכל Reel להכין 3 כיווני cover ולבחור אחד לפי התאמה לגריד ולסיפור. טקסט cover: 2–5 מילים. המוצר/הפעולה חייבים להיות קריאים במסך קטן וב־crop של הפיד. לא להשתמש בצבע/פונט שלא קיים במקור מותג מאומת.

## Brand QA

`brandScore` הוא 0–100. מעבר אוטונומי דורש `>=80` ובמקביל `CONTENT-RUBRIC >=20/25`, policy pass, Content Contract pass ו־PREFLIGHT כתוב. Hero/experimental work יכול לדרוש threshold גבוה יותר לפי `FOUNDRY.json`. אם הציון נמוך: לתקן ולבדוק שוב בתוך המשרד; לא להסלים לבעלים רק בגלל איכות נמוכה.

בדוק לפחות: first frame, קריאות, עומס טקסט, צילום/תאורה, consistency, cover, **audio presence/loudness/story-fit**, CTA, claims, זכויות רלוונטיות, safe-area, subject fidelity והאם התוכן עדיין נראה Velvet בלי שם המשתמש.

## Rights / privacy scope

ה־rights gate של שכבת הקריאייטיב מיועד למדיה של צד ג׳, UGC, אדם מזוהה/פרטיות או מגבלת זכויות ידועה. הוא **אינו gate רישיון-מודל אוטומטי** לכל צילום שאנחנו צילמנו של הדפסה שביצענו.

בהתאם להחלטת הבעלים מ־10.9.2026: owner-captured showcase/editorial content אינו נחסם רק מפני שמקור המודל אינו מתועד כרישיון מסחרי. רישיון מודל עובר למסלול מסחרי/הסלמה כאשר התוכן הציבורי מציע במפורש את המודל המצולם למכירה, כאשר מדובר בקידום ממומן של אותו מודל, או כשידועה מגבלת רישיון/מחלוקת. זו מדיניות workflow פנימית, לא קביעה משפטית.

## Evaluation split

אל תשתמש ב־VLM יחיד לכל QA. הפרד בין:

- deterministic checks: ratio/resolution/safe zones/subtitle bounds/frame integrity/**audio stream/loudness/sync**/mobile preview.
- perceptual rubrics: Brand/Hook/composition/Reality/Originality/**audio story-fit**.
- reference checks: subject/material/geometry fidelity + source-subject match.
- artifact checks: flicker, malformed geometry, unreadable text, temporal jitter/**audio clipping/noise**/broken Hebrew typography/bad crop/weak contrast.

כשל מקבל evidence + repair action אחת ברורה וחוזר ל־Artifact Repair Router; repair cycles bounded לפי `FOUNDRY.json`.

## Subject Lock

כאשר זהות המוצר קריטית, Content Contract כולל Subject Pack: reference assets, geometry/material/color invariants ו־`mustNotChange`. שוט סינתטי שנסחף מה־Subject Pack נכשל QA ואינו נכנס ל־master.

## Originality + fatigue guard

Reference הוא מכניקה, לא זהות. אפשר לקחת מבנה, קצב או רצף; חובה להחליף הקשר, חומר, צילום, עברית, הוכחה, צבעוניות ו־ending כך שהתוצאה מבוססת על חומר אמיתי של Velvet. אם reference יוצר סיכון זכויות או חיקוי זהותי — דחה אותו ובחר פורמט אחר.

לפני concept סופי יש להשוות להיסטוריית תוכן קיימת: מוצר, first frame, proof mechanic, story structure, זווית ו־reference mechanic. similarity גבוה מטופל לפי `FOUNDRY.json`: שינוי מכניקה, cooldown או series override מנומק. הצלחה קודמת היא preference, לא חוק שמייצר שכפול אינסופי.

## Synthetic role

AI מייצרת atmosphere, transitions ו־supporting visuals. המציאות של Velvet מספקת מוצר, חומר, כשל, מדידה והוכחה. טקסט עברי רגיש לעיוות נבנה כ־overlay deterministic דרך הכלים הקיימים במקום בתוך generation כשנדרש.


## Brand identity asset lock

For Velvet Factory public visuals, branding is source-locked. Never invent, redraw or approximate a logo/wordmark/emblem. If no exact owner-approved logo asset is available to the job, omit the logo. If one is available, overlay that exact asset deterministically after image generation/editing. Generative base frames must contain no logo, no wordmark, no phone number, no WhatsApp and no contact bar. See `packages/vfom/BRAND-ASSET-LOCK.md`.
