# vfmem — איך מטמיעים

שאילתות מבניות. לא מוצר חדש. מקור הרעיון: DeusData/codebase-memory-mcp. הביצוע: המפות שכבר יש.

אם Agency desk כבר ממוזג, אפשר `@studio-operations` אחרי `who`. הגרף לא תלוי בזה כדי לרוץ.

## 1. מפה — `queries/architecture.md`

**מהריפו:** `get_architecture` / `get_graph_schema`.

**אצלנו:**

```bash
python3 scripts/vfmem.py architecture
```

מושבים, פקים, כלים, צינור. בלי לקרוא 273 כללים.

## 2. מי מטפל — `queries/who.md`

**מהריפו:** `search_graph` / `semantic_query`.

**אצלנו:**

```bash
python3 scripts/vfmem.py who "בריף בוקר"
python3 scripts/vfmem.py who inquiry
```

שורת desk + `@slug` אחד. לא מחסן.

## 3. רדיוס — `queries/impact.md`

**מהריפו:** `trace_path` / `detect_changes`.

**אצלנו:**

```bash
python3 scripts/vfmem.py impact vfsales
python3 scripts/vfmem.py impact --git
```

## 4. צינור — `queries/route.md`

**מהריפו:** Route nodes.

**אצלנו:** `פנייה → שיחה → הצעה → הדפסה → איסוף`. איסוף שדרות. אין משלוח ארצי.

## 5. מחסן — `queries/dead.md`

**מהריפו:** dead-code degree 0.

**אצלנו:** מחסן = כבוי בכוונה. באג אמיתי רק אם חסר קובץ כלל לשולחן.

## 6. החלטות — `queries/adr.md`

**מהריפו:** `manage_adr`.

**אצלנו:** קריאה מהחוקה / השולחן. הסקריפט לא כותב ADR חדש.

## SaaS / בינארי אחר כך (לא עכשיו)

התקנת codebase-memory-mcp במחשב המקומי — רק אם ראש צוות רוצה אינדקס AST לסקריפטים. עד אז הדפוס רץ כ־`scripts/vfmem.py`.

## בדיקה

```bash
python3 scripts/check-vfmem.py
```

אין UI חי. אין דפדפן. העקביות היא מול המניפסט והמפות.
