# VelvetOS — ליבה

**VelvetOS** הוא כלי ניהול עסק + עמודי סושיאל אוטונומיים.  
הריפו הזה הוא המשרד. **Velvet Factory** הוא ה־tenant הפעיל הראשון — לא נמחק ולא נשבר.

## שכבות

```
VelvetOS (kernel)
  ├── laws          — שליחה דרך כלים, בלי ₪/Insights מומצאים, בלי אוטו־DM
  ├── seats         — 5 מושבים אוניברסליים (ראש צוות / סטודיו / צמיחה / תפעול / ייצור)
  ├── packs         — packages/* — אותם פקים; התנהגות לפי tenant
  ├── tenant        — ACTIVE.json → tenants/<id>.json
  └── harness       — AGENTS.md + vfharness
```

## מה אוניברסלי (kernel)

| רכיב | כלל |
|---|---|
| מושבים | תמיד 5. אין מושב שישי. |
| שליחה | Gmail + Instagram דרך כלים (`constitution/SEND.md`) |
| מחיר / Insights | רק ממקור מאומת; אחרת `X ₪` / «אין ספירה» |
| CTA | מה־tenant (וואטסאפ / מיקום / מסלול מסמך) — לא «שלחו DM» |
| ערוצים | 1+ חשבונות Instagram (ואחרים בעתיד) לפי tenant |
| צינור | 5 שלבים קנוניים; תוויות בעברית לפי tenant — ראו `PIPELINE.md` |
| אספקה | `pickup` / `appointment` / `document` / `hybrid` |
| ייצור | `print` / `appointment` / `document` / `custom` |

## מה ספציפי ל־tenant

זהות, צינור בעברית, ערוצי סושיאל, נעילות עסק, שפת מוצר, אזור זמן, סגירת עסקה, תיקיות אסורות.

## כלל ברזל

1. `ACTIVE.json` מצביע על tenant אחד. היום: `velvet-factory`.
2. סוכן קורא את ה־tenant הפעיל לפני עובדות סטודיו.
3. דוגמאות תחת `tenants/_examples/` הן **טיוטות** — לא מופעלות.
4. לא פק חדש לכל עסק. מפעילים tenant + מטמיעים על פקים קיימים.
5. שינוי ACTIVE בלי ראש צוות = אסור.

## דוגמאות יעד (לא פעילים)

| Tenant (דוגמה) | למה זה בודק אוניברסליות |
|---|---|
| מניקור/קעקועים · 2 IG | multi-channel + appointment + שני מותגים |
| פסיכיאטר · חוות דעת | document fulfill + compliance רפואי/משפטי |

פרופילים: `tenants/_examples/`.
