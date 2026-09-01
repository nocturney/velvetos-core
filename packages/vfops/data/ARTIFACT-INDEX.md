# אינדקס תוצרים — איך המשרד שואב מידע

מסמך זה עונה: **האם Velvet Factory / VelvetOS יודעים לאגור תוצרים מכל הפעולות?**

## תשובה קצרה

**כן — דרך נתיבים מפורשים בגיט ובכלים.**  
לא סקריפט קסם שקורא כל צ'אט Cursor אוטומטית. כל פעולה שמשאירה ארטיפקט בנתיב למטה — נשאבת למחרת.

```
פעולה (סוכן + כלים)
  → ארטיפקט (קובץ / checkpoint / Drive / Gmail שנשלח)
  → אינדקס (קובץ זה + vfmem + בריף)
  → owner-memory.md (תמצית לכל המושבים)
  → בריף 07:00 / שיחה הבאה
```

## VelvetOS Core (backend) — הריפו הזה

| סוג | נתיב | מי כותב | מי קורא |
|---|---|---|---|
| זיכרון בעלים | `vfops/data/owner-memory.md` | רטרו יומי / ראשוני | בריף, כל מושב, vfmem |
| משימות ארוכות | `vfharness/state/<task>.json` | סוכן בסוף job | סוכן בפתיחה |
| משרד בבריף | `vfops/data/research.md` | הטמעות / מחקר | בריף חריץ 05 |
| חוקים | `AGENTS.md`, `constitution/` | ראש צוות | תמיד |
| היסטוריית שינוי | `CHANGELOG.md` | כל הטמעה | אדם + רטרו |
| קישורי השראה | `vfresearch/LINKS.json` | מחקר שבועי | trend explorer |
| מוזיקה IG | `vfresearch/sources/*-ig-music.md` | trend-researcher | vfom / vfigos |
| ניתוב job | `vfmem/catalog.json` | ראש צוות | `vfmem.py who` |
| מפת משרד | `vfgraft/MAP.md` | ארכיטקט | התחלת job |
| יכולות UI | `vfops/hq/capabilities.json` | ראש צוות | command surface עתידי |
| לוח צינור | `vfops/hq/PIPELINE-BOARD.md` | סטודיו / ייצור | ראש צוות |
| מסמכי עבודה | Drive `create_file` | כל מושב | חיפוש לפי job/SKU |
| מייל שנשלח | Gmail (thread id) | HQ send | vfconvert / מעקב |
| עיצוב IG | Canva (design id / URL אמיתי) | vfcanva | vfigos |
| mesh / 3D | Drive + 3D AI Studio dashboard | vfprod | ייצור |

## VelvetOS — Velvet Factory (frontend)

ריפו: `nocturney/velvetos-velvet-factory` · scaffold: `instances/velvet-factory/`

1. `attach-core.sh` מושך Core ל־`vendor/velvetos-core/`
2. אותם נתיבים יחסית: `vendor/velvetos-core/packages/vfops/data/owner-memory.md`
3. פרופיל מודולים: `instance/velvet-factory.json` → `modulesEnabled` (כולל `office-learning`, `expert-*`)
4. Cloud Agent: `.cursor/environment.json` → `install: ./scripts/attach-core.sh` בכל boot

**הפרונט לא מחזיק עותק שני של הזיכרון** — הוא קורא מ-Core המחובר.

## מומחים (`expert-*`) — איפה התוצר

| מומחה | תוצר טיפוסי | נתיב |
|---|---|---|
| Revenue loop | Offer card, pipeline `ig_post_ref`, weekly pulse | `vfgrowth/experts/REVENUE-LOOP.md`, `PIPELINE-BOARD.md`, `WEEKLY-REVENUE-PULSE.md` |
| Insights ingest | snapshot מאומת | `vfinsights/sources/*-ig-snapshot.md`, `templates/snapshot-ingest.md` |
| Instance onboard | פרונט + זיכרון נפרד | `velvetos/experts/INSTANCE-ONBOARD.md`, `owner-memory-<id>.md` |
| Social Booster | חבילת קרוסלה / הוקים | `vfgrowth/`, Canva, `vfigos` queue |
| 3D model | כרטיס כדאיות, mesh | `vfprod/`, Drive, checkpoint |
| Trend explorer | מפת מקורות, מוזיקה | `vfresearch/sources/`, `LINKS.json` |
| Media director | storyboard, ריל packet | `vfom/`, `vfcovers/`, Canva |

## מה עדיין לא אוטומטי

- היסטוריית צ'אט Cursor שלא נשמרה בגיט → **לא** נשאבת; רטרו ראשוני סוכם מ־CHANGELOG + checkpoints
- Insights IG בלי snapshot → «אין ספירה»
- תיבת דואר לבריף → **מכוון לא** (2026-08-31)

## פקודות

```bash
python3 scripts/vfmem.py who "daily retro"
python3 scripts/vfmem.py architecture
ls packages/vfharness/state/
```
