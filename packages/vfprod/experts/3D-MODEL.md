# 3D Model — מנתח / יוצר / בונה

מושב: ייצור. מודול: `expert-3d-model`.  
אין הדפסה מ־HQ. אין מפתח API בגיט.

## מתי

- קובץ STL/3MF/STEP חדש לבדיקה לפני תור
- קונספט מטקסט/תמונה (אחרי אישור ראש צוות)
- תיקון mesh / wall thickness / supports hint
- מק״ט חוזר (`#vfsku`) + רישיון (`#vlicense`)

## שלבים

### 1. Analyze (מנתח)

```
קלט: קובץ / קישור Drive / תיאור לקוח
  → ממדים, חומר, שימוש, כמות
  → סיכונים: דק מדי, overhang, support, זמן הדפסה
  → פלט: כרטיס כדאיות (hq/PLAYBOOK.md) — X ₪ רק אם יש מקור
```

### 2. Make (יוצר)

אחרי אישור ראש צוות בלבד:

```
טקסט/תמונה → 3D AI Studio MCP (3DAISTUDIO.md)
  → failover: אתר + Drive create_file
  → Meshy/Tripo: אותו שער vlicense
```

### 3. Build (בונה)

```
mesh מאושר → slicer (רצפה, לא HQ)
  → SKU card (#vfsku)
  → תור הדפסה על צינור «הדפסה»
```

## כרטיס mesh

| שדה | הערה |
|---|---|
| מקור | לקוח / AI / stock (רישיון!) |
| פורמט | STL · 3MF · OBJ |
| printability | ירוק / צהוב / אדום + סיבה |
| רישיון | `#vlicense` לפני reprint |
| קרדיטים 3DAI | לא מדווחים ₪ — רק «אין ספירה» אם חסר מקור מחיר |

## מומחים

- `@studio-producer` — תור ורצפה
- `@technical-artist` — shaders/VFX לא רלוונטי; כאן: mesh hygiene, LOD, export
- `@legal-compliance-checker` — שער רישיון

## לולאת שיפור

סוף יום: מה נכשל בסלייסר? איזה prompt 3DAI עבד? שורה ל־`owner-memory.md` + checkpoint אם job פתוח.

## חפיפה קיימת

- `3DAISTUDIO.md` · `CONNECT-3DAI.md` · `FLOOR.md` · `CHECKLIST.md`
