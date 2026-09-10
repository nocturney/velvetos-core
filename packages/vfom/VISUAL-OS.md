# Velvet Visual OS

מושב: צמיחה · מודול `expert-media-director`. זהו מקור האמת הוויזואלי של Velvet Factory עבור תוכן אורגני. הוא מרחיב את חוקי המותג הקיימים; כשחסר צבע/פונט מאומת — לא ממציאים ערך חדש.

Machine-readable projection: `VISUAL-DNA.json`. אם יש סתירה, המסמך הזה וחוקי ה־constitution גוברים; ה־JSON נועד לאורקסטרציה/QA ולא ליצור מותג חדש.

## DNA

- תחושה: מעבדת חומרים חכמה, טקטית, חמה ולא תאגידית.
- צילום: מאקרו, close-up, ידיים עובדות, מוצר בתנועה, הוכחה פיזית אמיתית.
- רקעים: שולחן עבודה אמיתי, טקסטורת חומר, או שחור/אפור/לבן נקי.
- תאורה: אור קשה ומכוון או אור יום רך; לא ערבוב אקראי בתוך אותו נכס.
- טיפוגרפיה: היררכיה קבועה, מקסימום שני פונטים מאומתים. חסר פונט מאומת = להשתמש בתבנית קיימת, לא לבחור חדש.
- תנועה: hard cut כברירת מחדל. Slow motion רק ברגע הוכחה/מבחן משמעותי. אין intro לוגו ארוך.
- סאונד: רכיב קריאייטיב מלא, לא שכבת קישוט בסוף. עדיפות לסאונד אמיתי של הסטודיו כאשר הוא שימושי; מוזיקה/SFX תומכים בסיפור ולא מחליפים הוכחה.
- עברית: קצרה, טבעית, מדוברת ומדויקת. לא “שיווקית AI”.

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

- deterministic checks: ratio/resolution/safe zones/subtitle bounds/frame integrity/**audio stream/loudness/sync**.
- perceptual rubrics: Brand/Hook/composition/Reality/Originality/**audio story-fit**.
- reference checks: subject/material/geometry fidelity.
- artifact checks: flicker, malformed geometry, unreadable text, temporal jitter/**audio clipping/noise**.

כשל מקבל evidence + repair action אחת ברורה וחוזר ל־Artifact Repair Router; repair cycles bounded לפי `FOUNDRY.json`.

## Subject Lock

כאשר זהות המוצר קריטית, Content Contract כולל Subject Pack: reference assets, geometry/material/color invariants ו־`mustNotChange`. שוט סינתטי שנסחף מה־Subject Pack נכשל QA ואינו נכנס ל־master.

## Originality + fatigue guard

Reference הוא מכניקה, לא זהות. אפשר לקחת מבנה, קצב או רצף; חובה להחליף הקשר, חומר, צילום, עברית, הוכחה, צבעוניות ו־ending כך שהתוצאה מבוססת על חומר אמיתי של Velvet. אם reference יוצר סיכון זכויות או חיקוי זהותי — דחה אותו ובחר פורמט אחר.

לפני concept סופי יש להשוות להיסטוריית תוכן קיימת: מוצר, first frame, proof mechanic, story structure, זווית ו־reference mechanic. similarity גבוה מטופל לפי `FOUNDRY.json`: שינוי מכניקה, cooldown או series override מנומק. הצלחה קודמת היא preference, לא חוק שמייצר שכפול אינסופי.

## Synthetic role

AI מייצרת atmosphere, transitions ו־supporting visuals. המציאות של Velvet מספקת מוצר, חומר, כשל, מדידה והוכחה. טקסט עברי רגיש לעיוות נבנה כ־overlay deterministic דרך הכלים הקיימים במקום בתוך generation כשנדרש.
