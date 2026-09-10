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
- סאונד: לתת מקום לסאונד אמיתי של הסטודיו; מוזיקה תומכת ולא מחליפה הוכחה.
- עברית: קצרה, טבעית, מדוברת ומדויקת. לא “שיווקית AI”.

## First-frame law

הפריים הראשון חייב להתחיל בפעולה, תוצאה, מתח, פרט ברור או הוכחה. אין פתיח לוגו ואין “היי חברים”. לכל Reel לייצר 3–5 candidates ולבחור אוטונומית את החזק ביותר לפי בהירות, תנועה, ניגוד, קריאות וסקרנות.

## Proof-first law

Storyboard מתחיל מהוכחה או מאירוע פיזי אמיתי כשיש כזה: עומס, תנועה, התקנה, לפני/אחרי, מדידה, כשל→תיקון או מעבר מהדפסה לשימוש. אם אין proof asset מתאים, אין להמציא מבחן AI; יש לשנות פורמט או להוציא `shotRequest` מינימלי.

כל claim פיזי חייב להיות מגובה ב־Content Contract לפי `CONTENT-CONTRACT.schema.json`. `verified_real` של נכס אינו מוכיח אוטומטית כל טענה עליו.

## Shot vocabulary

`hero` · `macro` · `process` · `failure` · `proof` · `human` · `b-roll`.

בכל creative plan לציין לכל shot: סוג, אוריינטציה, זווית, מרחק, משך משוער, פעולה, ומה הוא מוכיח. חומר פיזי שחסר הופך ל־`content.media_needed`; לא ממציאים scene.

## Covers

לכל Reel להכין 3 כיווני cover ולבחור אחד לפי התאמה לגריד ולסיפור. טקסט cover: 2–5 מילים. המוצר/הפעולה חייבים להיות קריאים במסך קטן וב־crop של הפיד. לא להשתמש בצבע/פונט שלא קיים במקור מותג מאומת.

## Brand QA

`brandScore` הוא 0–100. מעבר אוטונומי דורש `>=80` ובמקביל `CONTENT-RUBRIC >=20/25`, policy pass, Content Contract pass ו־PREFLIGHT כתוב. Hero/experimental work יכול לדרוש threshold גבוה יותר לפי `FOUNDRY.json`. אם הציון נמוך: לתקן ולבדוק שוב בתוך המשרד; לא להסלים לבעלים רק בגלל איכות נמוכה.

בדוק לפחות: first frame, קריאות, עומס טקסט, צילום/תאורה, consistency, cover, סאונד, CTA, claims, זכויות, safe-area, subject fidelity והאם התוכן עדיין נראה Velvet בלי שם המשתמש.

## Evaluation split

אל תשתמש ב־VLM יחיד לכל QA. הפרד בין:

- deterministic checks: ratio/resolution/safe zones/subtitle bounds/frame integrity/audio loudness.
- perceptual rubrics: Brand/Hook/composition/Reality/Originality.
- reference checks: subject/material/geometry fidelity.
- artifact checks: flicker, malformed geometry, unreadable text, temporal jitter.

כשל מקבל evidence + repair action אחת ברורה וחוזר ל־Artifact Repair Router; repair cycles bounded לפי `FOUNDRY.json`.

## Subject Lock

כאשר זהות המוצר קריטית, Content Contract כולל Subject Pack: reference assets, geometry/material/color invariants ו־`mustNotChange`. שוט סינתטי שנסחף מה־Subject Pack נכשל QA ואינו נכנס ל־master.

## Originality + fatigue guard

Reference הוא מכניקה, לא זהות. אפשר לקחת מבנה, קצב או רצף; חובה להחליף הקשר, חומר, צילום, עברית, הוכחה, צבעוניות ו־ending כך שהתוצאה מבוססת על חומר אמיתי של Velvet. אם reference יוצר סיכון זכויות או חיקוי זהותי — דחה אותו ובחר פורמט אחר.

לפני concept סופי יש להשוות להיסטוריית תוכן קיימת: מוצר, first frame, proof mechanic, story structure, זווית ו־reference mechanic. similarity גבוה מטופל לפי `FOUNDRY.json`: שינוי מכניקה, cooldown או series override מנומק. הצלחה קודמת היא preference, לא חוק שמייצר שכפול אינסופי.

## Synthetic role

AI מייצרת atmosphere, transitions ו־supporting visuals. המציאות של Velvet מספקת מוצר, חומר, כשל, מדידה והוכחה. טקסט עברי רגיש לעיוות נבנה כ־overlay deterministic דרך הכלים הקיימים במקום בתוך generation כשנדרש.
