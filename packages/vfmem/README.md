# vfmem — HQ memory graph

מפה של [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) אל משרד Velvet Factory.

הריפו שם הוא שרת MCP ב־C: אינדקס AST, 15 כלים, פחות טוקנים מ־grep. **אצלנו לא מתקינים את הבינארי.** מטמיעים את **שאילתות הגרף** על המפות שכבר יש (`vf-desk.json`, `manifest.json`, Agency catalog).

## למה זה עוזר

המשרד גדול: 273 סוכנים, ~20 פקים, שישה מושבים. סוכן שקורא הכל שורף טוקנים וממציא מסלול. שאילתה אחת מחזירה פק + `@slug` + כלי.

זה אותו לקח מהמאמר שלהם (arXiv:2603.27277): שאילתה מבנית במקום קובץ־אחרי־קובץ.

## מה כן אצלנו

| כלי CBM | פקודה אצלנו |
|---|---|
| `get_architecture` | `python3 scripts/vfmem.py architecture` |
| `search_graph` | `python3 scripts/vfmem.py who <job>` |
| `trace_path` | `python3 scripts/vfmem.py impact <pack>` |
| `detect_changes` | `python3 scripts/vfmem.py impact --git` |
| `manage_adr` | `python3 scripts/vfmem.py adr` |
| dead-code | `python3 scripts/vfmem.py dead` |
| Route nodes | `python3 scripts/vfmem.py route <stage>` |

## מה לא

ראה [`LOCK.md`](LOCK.md): אין `curl \| bash`, אין דמון, אין UI 9749, אין מחיקת מחסן Agency.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | מיפוי כלי CBM + נתיבי שולחן + ADR |
| [`EMBED.md`](EMBED.md) | איך מריצים |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`queries/`](queries/) | נהלי שאילתה |
| [`scripts/vfmem.py`](../../scripts/vfmem.py) | גרף חי + CLI |
| [`scripts/check-vfmem.py`](../../scripts/check-vfmem.py) | בדיקת עקביות |

## קטלוג Skills אחוד (נגזר, לא מקור אמת נוסף)

`python3 scripts/vf_skill_catalog.py index` מעדכן cache מקומי ואטומי לפי שינויי קבצים ו־SHA256; כל שאילתה בודקת שה־cache עדיין תואם למקורות. בהיעדר cache פועלים ישירות מהמקורות. `list`, `show <id>`, `search <query>`, `compare <query>`, `route <query>`, `plan <query>`, `audit`, `host` זמינים ללא API חיצוני וללא התקנה.

**מקורות UI/UX שאינם Skills:** `python3 scripts/vf_skill_catalog.py sources` מציג 42 מקורות מהפוסט (ספריות, אנימציה, השראה ומערכות עיצוב), ו־`python3 scripts/vf_skill_catalog.py source-search "Angular" --stack Angular` מחפש בהם. `compare` ו־`plan` מחזירים אותם כ־`supporting_resources` בלבד. Living Studio משתמש באותה שכבה באמצעות `python3 scripts/vf_living_studio.py skill resources` ו־`skill source-search`; שום מקור לא הופך אוטומטית ל־Skill מותקן, לתוסף פעיל או להרשאת ביצוע. מצב הרישוי וההתאמה מפורטים ב־[`ui-ecosystem-sources-2026-10-20.json`](../../docs/implementation/office-v2/phase2/ui-ecosystem-sources-2026-10-20.json) וב־[`ui-ecosystem-comparison-2026-10-20.md`](../../docs/implementation/office-v2/phase2/ui-ecosystem-comparison-2026-10-20.md).
 תוצאות זמינות וביצוע הן UNKNOWN/NOT_STARTED ללא ראיות ריצה.

`vfmem` ו־`vf_living_studio.py skill` קוראים את אותה שכבת גילוי. המועמדים החיצוניים נשמרים ב־Office v2 Candidate Registry, לא נטענים כרכיבי runtime. ראו את [פיילוט ההשוואה](../../docs/implementation/office-v2/phase2/skill-comparison-pilot-20261020.md).

## איך מפעילים

```
@vfmem who בריף בוקר
@vfmem architecture
```

או:

```bash
python3 scripts/vfmem.py who inquiry
python3 scripts/check-vfmem.py
```

## חיפוש סמנטי מקומי (2026-09-07)

`scripts/vf_semantic_search.py` — אינדקס TF-IDF אמיתי על כל ה-Markdown, offline, בלי API. פירוט מלא: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).
