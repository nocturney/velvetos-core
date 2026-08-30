# vfmem — HQ memory graph

מפה של [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) אל משרד Velvet Factory.

הריפו שם הוא שרת MCP ב־C: אינדקס AST, 15 כלים, פחות טוקנים מ־grep. **אצלנו לא מתקינים את הבינארי.** מטמיעים את **שאילתות הגרף** על המפות שכבר יש (`vf-desk.json`, `manifest.json`, Agency catalog).

## למה זה עוזר

המשרד גדול: 273 סוכנים, ~20 פקים, חמישה מושבים. סוכן שקורא הכל שורף טוקנים וממציא מסלול. שאילתה אחת מחזירה פק + `@slug` + כלי.

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
