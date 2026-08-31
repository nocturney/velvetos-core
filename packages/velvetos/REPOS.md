# ריפואים — Core (backend) מול Instances (frontend)

כן — המטאפורה **הגיונית**:

| שכבה | תפקיד | אנלוגיה |
|---|---|---|
| **VelvetOS Core** (הריפו הזה) | חוקים, מושבים, מודולים, פקים, סנסורים | באקאנד / ליבת OS |
| **VelvetOS — \<Business\>** | זהות עסק, ערוצים, CTA, כלי חיים, `modulesEnabled` | פרונט / משרד העסק |

זה לא HTTP API — זו ליבת Cursor-OS שמשותפת. כל עסק הוא workspace נפרד ששואב מהליבה.

## ריפואים

| ריפו | תפקיד |
|---|---|
| `nocturney/velvet-factory-headquarters-os` | **VelvetOS Core** (backend) |
| `nocturney/velvetos-velvet-factory` | **VelvetOS — Velvet Factory** (frontend) — scaffold ב־`instances/velvet-factory/` |
| `velvetos-<business>` | מופעים עתידיים מ־`presets/` (יופי multi-IG, פסיכיאטר…) |

## איך פרונט שואב באקאנד

```bash
# בתוך ריפו המופע
./scripts/attach-core.sh
# → vendor/velvetos-core/  (clone של הליבה)
```

המופע מפעיל תת־קבוצה של `modules/catalog.json` דרך `modulesEnabled`.

## פרסום מופע VF

1. צור ב־GitHub ריפו ריק פרטי `nocturney/velvetos-velvet-factory` (הסוכן בענן לא יכול `createRepository`).
2. מהליבה:

```bash
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

3. פתח את ריפו המופע ב־Cursor לניהול היומי של VF.
4. הליבה נשארת מקום העריכה של מודולים/פקים/סנסורים.

## מה לא

- לא שני עסקים חיים כ־frontend בתוך הליבה  
- לא לשכפל עץ `packages/vf*` לכל עסק — attach מהליבה  
- לא handles פיקטיביים כעובדות חיות  
