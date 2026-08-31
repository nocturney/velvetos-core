# ריפואים — ליבה מול מופעים

המודל המועדף (ראש צוות):

| ריפו | תפקיד |
|---|---|
| `velvetos-core` | ליבת OS: חוקים, מושבים, מודולים, presets, סנסורי ליבה |
| `velvetos-velvet-factory` | מופע: VelvetOS — Velvet Factory (המשרד החי היום) |
| `velvetos-<business>` | מופע חדש לכל עסק — שואב מודולים מהליבה |

## היום (מונוריפו)

הריפו `velvet-factory-headquarters-os` הוא:

1. **מופע** VelvetOS — Velvet Factory  
2. **מארח זמנית את הליבה** (`INSTANCE.json` → `hostsCore: true`) תחת `packages/velvetos/`

אין שני tenants חיים באותו ריפו. אין מתג active/example לעסקים אחרים.

## מחר (פיצול)

1. חילוץ `packages/velvetos/{modules,presets,schema,KERNEL,PIPELINE,CHANNELS,LOCK,REPOS}` → ריפו `velvetos-core`.
2. מופע VF נשאר עם `instance/` + packs + constitution/STUDIO + desk, ומושך ליבה ב־git subtree / submodule / vendor script.
3. מופע חדש (יופי / פסיכיאטר): ריפו ריק + vendor ליבה + `INSTANCE.json` + בחירת מודולים מ־preset + עובדות אמיתיות בלבד.

## איך מופע שואב מהליבה

```
instance/
  PROFILE.json     ← id, displayName, modulesEnabled[], studio facts
packages/          ← vf* packs (משותפים או מועתקים לפי צורך)
constitution/      ← STUDIO של העסק הזה בלבד
vendor/velvetos/   ← עותק/subtree של הליבה (אחרי הפיצול)
```

`modulesEnabled` חייב להיות תת־קבוצה של `modules/catalog.json`.  
Preset בליבה אומר *אילו מודולים רלוונטיים לאנכי* — לא יוצר סביבה חיה בריפו הזה.

## מה לא עושים

- לא מפעילים «tenant שני» ליד VF באותו ריפו  
- לא משאירים handles פיקטיביים כעובדות חיות  
- לא פק חדש לכל עסק — מודול + פקים קיימים  
