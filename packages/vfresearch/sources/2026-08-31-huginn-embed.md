# Huginn — הטמעת דפוסים (לא Rails)

מקור: https://github.com/huginn/huginn  
נקרא: 2026-08-31 · Asia/Jerusalem  
מושב: ייצור · `@research-synthesist`

## מה זה

Huginn = IFTTT/Zapier self-hosted: סוכנים יוצרים וצורכים **Events** בגרף מכוון. Scenarios, schedule, memory, `working?`.

## מה **לא** מתקינים

- אפליקיית Rails + DB — runtime שני (נגד `vfe2b/LOCK.md`).
- אוטומציה ללקוח (Make/Zapier) — כבר נדחה ב-`vfops/ROUTINE.md`.
- ניטור מדפסת 24/7 מ-HQ — `vfprod/FLOOR.md`.

## מה **הוטמע**

| דפוס Huginn | אצלנו |
|---|---|
| Event payload | `vfharness/templates/checkpoint.schema.json` → `events[]` |
| Scenario (גרף שמור) | `vfe2b/scenarios/*.md` (4 תרחישים) |
| DigestAgent + schedule | `vfops` בריף 07:00 — כבר קיים |
| `working?` / staleness | `scripts/check-staleness.py` |
| DeDuplicationAgent | `vfconvert/hq/DEDUP.md` + `inquiry-chain` scenario |
| WebsiteAgent | `vfresearch/WEEKLY.md` — שבועי, לא דמון |
| Peak detection | `vfinsights` בלבד עם מקור אמיתי |

## מיפוי Cursor = Huginn

Cursor + משמרת `vfe2b` + `vfharness` = המשרד. אין dashboard נפרד.
