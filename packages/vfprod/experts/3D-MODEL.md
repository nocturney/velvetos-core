# 3D Model — מנתח / יוצר / בונה

מושב: ייצור. מודול: `expert-3d-model`.  
לפני כל משימת CAD/ייצור יש לפתור `../FABRICATION-ROUTER.md` ולקרוא את ה־Skill שנבחר מ־`.agents/skills/<skill>/SKILL.md`.
אין שליטה/שליחה למדפסת מ־HQ. אין מפתח API בגיט.

## מתי

- קובץ STL/3MF/STEP חדש לבדיקה לפני תור
- CAD פונקציונלי פרמטרי מטקסט/מידות דרך `cad`
- חלקי מדף/ברגים/מיסבים/מנועים דרך `step-parts` לפני placeholder
- צפייה ובקרת artifact דרך `cad-viewer`
- קונספט אורגני/סקלפטורלי מטקסט/תמונה דרך 3D AI Studio כשה־router מעדיף mesh
- DfAM: wall thickness / overhang / supports / orientation דרך `dfam-check`
- DFM ל־CNC/sheet-metal/injection דרך `dfm`
- DXF / flat pattern דרך `dxf`; שרטוט PDF ממודד דרך `engineering-drawing`
- URDF/SRDF/SDF רק כשמדובר ברובוטיקה/סימולציה
- slicing מאומת דרך `gcode` + OrcaSlicer וה־printer matrix הקיים
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
