# הצעה אחרי סלייס

מושב: **תפעול**.  
מקור Gemini: STL Quote Agent.  
מקור Perplexity: Spoolworth / AutoQuote3D (משקל, זמן, חשמל, רווח — ווידג׳ט תשלום).  
אין הצעת ₪ עד שראש הצוות נתן סכום.  
כל טקסט שהלקוח קורא כפוף ל־`constitution/VISIBLE_TEXT.md`, mode `sales-proposal` / `customer-message`.

## כשלקוח שולח STL/3MF (וואטסאפ, לא בוט)

1. לקבל קובץ בוואטסאפ 050-2517000. לא טופס, לא ווידג׳ט AutoQuote3D.
2. אם חסר בירור — `vfconvert/PATH.md` (חומר · כמות · מתי · גימור).
3. סלייס ב־Orca או Prusa (`vfcost/SLICE.md`): משקל, זמן, תקינות, שכבה/מילוי/תמיכות אם הסלייסר הראה.
4. רישיון (`vlicense`) רק כשהמסלול/המודל מחייב בדיקה לפי המדיניות הפעילה; לא ממציאים gate שאינו רלוונטי.
5. לכתוב לראש צוות: משקל · זמן · חומר · האם תקין · האם תוקן קובץ. **בלי מחיר.** טקסט הסיכום לבעלים עובר `owner-brief` Visible Text Gate; הנתונים עצמם נשארים literal.
6. אחרי סכום ממנו — בונים הצעה אנושית, מריצים **sales-proposal Visible Text Gate**, ורק אחר כך Gmail send / WhatsApp handoff + Invoice4U. איסוף שדרות.
7. קו B2B נעול. אם ראש צוות פתח — תבנית מקומית ב־`hq/B2B-QUOTE.md` (לוגו/QR/מפיות = דוגמאות) + אותו text gate.

אין «הצעת מחיר מדויקת תוך שניות» מהמשרד הזה.  
אין ווידג׳ט שהלקוח מעלה מודל, מקבל ₪, ומשלם.

## SLA תגובה (לפני מחיר)

ראו `packages/vfsales/SLA.md`: תגובה ראשונה ≤15 דק׳ בשעות פעילות — **בלי ₪**, עם 1–2 שאלות GRILL.  
המסמך מחייב תהליך פנימי. **אין** שליחת הודעות אוטומטיות / בוטים / התחייבות חדשה מול לקוח בלי אדם ב־`050-2517000` כאשר הערוץ הוא WhatsApp. Gmail יכול להישלח מ־HQ לפי `constitution/SEND.md`, אבל רק אחרי Visible Text Gate.

## לפני טיוטת הצעה — חובה מהקלט

דפוס [proposal-drafter](https://buildwithclaude.com/skill/proposal-drafter) (buildwithclaude, 2026-09-05) מותאם ל־VF:

| חובה מהקלט / הסלייס | אם חסר |
|---|---|
| מה ביקש הלקוח (מהכרטיס / השרשור) | לא לפתוח בהצגה עצמית — לשאול / לסמן חסר |
| חומר · כמות · גודל · מועד (או «גמיש») | `vfconvert/PATH.md` לפני מחיר |
| משקל · זמן · תקינות מסלייסר | בלי מספרים מומצאים |
| סכום מראש צוות | `X ₪` — לא מנחשים |
| רישיון/פרטיות כשישים | עוצרים רק אם המדיניות/המקור באמת מחייבים |

## Visible Text Gate — חובה לפני לקוח

הסדר לכל גוף הצעה/מייל/WhatsApp שנכתב או שוכתב ב־AI:

1. **Truth:** thread/card + slicer + verified amount + constraints.
2. **Reader-first:** `packages/vfcopy/hq/reader-first-he.md` — מה הלקוח שאל ומה הוא צריך לדעת עכשיו.
3. **Sales/domain:** `vfsales` + `vfconvert`; `vfcost` למחיר/עלות; `vlicense` רק כשישים.
4. **Writing aids:** `vfmskill` `copywriting` + `copy-editing` כשמדובר בהצעה שיווקית/מכירתית; `marketing-psychology` רק אם הוא באמת מועיל ולא מייצר לחץ/הבטחה מלאכותית.
5. **Hebrew authority:** `.cursor/skills/vf-hebrew-copy/SKILL.md` / `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` mode `sales-proposal`.
6. **Humanizer:** `packages/vfcopy/hq/ai-tells-he.md` + surface-aware lint על הגוף הסופי.
7. **Fact gate:** סכום, זמן, מפרט, pickup וכל claim חייבים להתאים למקור.
8. רק אז: `visible_text_gate: PASS` עבור **הגרסה המדויקת**. שינוי מהותי מחייב gate מחדש.

Private customer message אינו מקבל `PUBLIC_CURRENT_CTA` של Instagram בכוח; הערוץ והצעד הבא נקבעים לפי השיחה האמיתית.

## מבנה טיוטה

1. **פתיחה** — התשובה/ניסוח קצר של מה שביקש, לא «נשמח לעמוד לשירותך».
2. **מה אנחנו יודעים** — חומר/גודל/כמות/איסוף רק אם אומתו.
3. **הוכחה אחת אמיתית** — רק אם יש מקור (למשל סלייס שעבר); בלי מדד מומצא.
4. **מחיר/מועד** — רק מהמקור שאושר.
5. **צעד הבא אחד** — לאשר / לשלוח מידה / לקבוע איסוף בערוץ שבו מתנהלת השיחה.

אם חסר רקע אמיתי לטיוטה — **לא כותבים הצעה “בטוחה”**. מחזירים `needs_input`/`חסר`/`X ₪` בהתאם לחסר.

## סולם הסלמה (רתמה)

כשהטיוטה נתקעת על שדות חסרים — לא מנחשים. מריצים:

```bash
python3 packages/vfsales/scripts/vf_quote_ladder.py --task-id <id> --known "material=PETG"
```

הסולם (`vfharness` `run_ladder`) מוריד לטיוטה חלקית עם `חסר:` ו־`X ₪`. אין מחיר מומצא. טיוטה חלקית היא `DRAFT`, לא `visible_text_gate: PASS` למסירה ללקוח עד שהחסרים הרלוונטיים נסגרו.
