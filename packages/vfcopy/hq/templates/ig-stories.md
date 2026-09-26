# תבנית: סטוריז 20:30

## VF_PUBLICATION_ROUTE_V1 — current

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

## תפקיד
סדרת סטורי יומית `@velvets_cloud` — רק מקליפ/תמונה מאותו יום על המיטה.  
פלייבוק סטודיו: `vfgrowth/STORIES.md`. שער עריכה: `vfgrowth/EDIT-GATE.md`.

## הקשר
- מה רואים: `{קליפ_היום}` (חובה — בלי זה לא משבצים)
- שעה קבועה: 20:30 Asia/Jerusalem · ראשון–חמישי בלבד
- פלט: שפה חזותית נגזרת מהרפרנסים המאושרים של העבודה המדויקת; אין palette/provider preset מ־G004 legacy. כיתוב מלא עובר `vfcopy` ורק microcopy שמוסיף מידע נכנס לפריים.

## משימה
ארבעה פריימים. עברית חמה, משרד יקר. לא פותחים ב«מוכן» / «קיים» / «אין משלוח» / מגבלה.  
**פריט גמור = סיפור-מוצר** (`VOICE.md`) — לא תהליך-קצר, לא קופי דק.  
**תהליך-קצר** רק לריל חשיפה / טיימלאפס — לא לסטוריז מוצר.


## פורמט פלט — סיפור-מוצר (ברירת מחדל למוצר גמור)

```
1. {הוק אופי + אמוג׳י אחד}

2. הכירו את {הפריט} — מה רואים ומה מיוחד

3. מתאים כ{שימוש} / כ{מתנה} / או פשוט למי שנמשך לזה

4. רוצים אחד משלכם או בצבעים בהתאמה?
   לפרטים — שלחו הודעה כאן באינסטגרם
   היילייטס בפרופיל · איסוף שדרות
```

> LEGACY / provenance only — G004: `packages/vfcopy/G004-STORIES-FIX.md` נשמר כהיסטוריה בלבד. reuse דורש qualification חדש מול ה־LEDGER ו־VF_PUBLICATION_ROUTE_V1.

## פורמט פלט — תהליך-קצר (רק ריל/טיימלאפס)

```
1. {זמן/שכבות/חשיפה} + אמוג׳י אחד
2. {טיימלאפס קצר}
3. {מה ירד מהמיטה}
4. עקבו כדי לראות מה יוצא בשבוע הבא
   היילייטס בפרופיל
```

אחרי פרסום תהליך של מוצר אמיתי — follow-up `waiting_for_matching_print.done` (`PRODUCTION-CONTENT.md`).

## אילוצים
- בלי קליפ אותו יום = **לא משבצים** (חסום).
- CTA מוצר: הודעת Instagram + היילייטס + איסוף שדרות. אסור וואטסאפ / `050-2517000` בתוכן ציבורי. לא אוטו־DM. לא ₪. לא Insights.
- אין סטורי פיד בשישי–שבת מהלוח הקבוע.
- בלי edited review artifact + source/final evidence + publication evidence = חסום עריכה.

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
