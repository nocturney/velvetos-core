# velvetos — איך מטמיעים

לא פק מוצר לכל עסק. ליבה + tenant על הפקים הקיים.

## 1. זהות מוצר

- שם המוצר: **VelvetOS**
- הריפו / המשרד החי: נשאר משרד VF כשה־tenant פעיל הוא `velvet-factory`
- מדריך: `AGENTS.md` (מנצח שיחה) + `KERNEL.md`

## 2. הפעלת tenant חדש (רק ראש צוות)

1. העתק מ־`tenants/_examples/` → `tenants/<id>.json`
2. מלא handles אמיתיים, CTA, where — בלי המצאה
3. `status: ready` → אחרי אימות סנסור `status: active` רק דרך החלפת `ACTIVE.json`
4. עדכן `constitution/STUDIO.md` **או** שמור STUDIO כ־VF ועבוד רק מפרופיל ה־tenant (מומלץ: קובץ STUDIO נשאר VF עד שיש משרד נפרד)
5. `python3 scripts/check-velvetos.py`

## 3. מה לא נוגעים בו ביום הראשון

- שמות פקים `vf*`
- חמישה מושבים
- `SEND.md` / איסור אוטו־DM
- סנסורי VF שבודקים `@velvets_cloud` כל עוד ACTIVE=velvet-factory

## 4. מיפוי אנכי → פקים

| אנכי | fulfill | הערות |
|---|---|---|
| maker / print | `vfprod` הדפסה | VF היום |
| beauty / appointment | `vfprod`+`vfops` כתור | multi-IG ב־CHANNELS |
| clinical-legal / document | `vfprod` כמסמך | PHI מחוץ לגיט |

## 5. אחרי שינוי

```
python3 scripts/check-velvetos.py
python3 scripts/check-all.py
```

שורה ב־`CHANGELOG.md`. Checkpoint ב־`packages/vfharness/state/`.
