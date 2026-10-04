# Tenant → Instance (legacy redirect)

המונח הישן **tenant** נשאר רק לתאימות/היסטוריה ולמונחים טכניים חיצוניים. בארכיטקטורת VelvetOS העסק הפעיל הוא **instance**.

הריפו הזה הוא **VelvetOS Core**. Velvet Factory הוא מופע/Office binding נפרד, עם scaffold ב-`instances/velvet-factory/` ופרופיל ב-`instances/velvet-factory/instance/velvet-factory.json`.

Instance מחזיק זהות עסק, ערוצים, CTA, `modulesEnabled` ו-bindings לכלים חיים. הוא **אינו** מקור סמכות חלופי ל-Core policy.

ראו [`INSTANCE.md`](INSTANCE.md) + [`packages/velvetos/REPOS.md`](../packages/velvetos/REPOS.md).
