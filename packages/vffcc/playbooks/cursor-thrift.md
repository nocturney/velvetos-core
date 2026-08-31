# חיסכון מכסת Cursor — בלי FCC

זה מה שכן מוריד שימוש **במשרד הזה**, היום, בלי התקנה.

## 1. שולחן, לא מחסן

273 סוכני Agency ב־`.cursor/rules/` עם `alwaysApply: false`. מפעילים רק `@slug` מהשולחן (`.cursor/vf-desk.json`).  
Godot / GIS / healthcare / סין-סושיאל נשארים במחסן. כל `@slug` מיותר שורף טוקנים.

## 2. אין MCP כפול

`docs/MCP-FIT.md`: Gmail, Drive, Calendar, Canva, Treg, Mobbin כבר מחוברים. שרת שני לאותה עבודה שורף טוקנים ולא חוסך.

## 3. אל תפתח Cloud Agent לשאלת קטלוג

«יש כבר פק לזה?» / «מה נעול?» — קוראים `packages/manifest.json`, `docs/AGENCY-TOOLS.md`, את ה־LOCK של הפק. לא ריצה חדשה.

## 4. תזמורת במקום מודל יקר לכל מחקר

06:15: Cursor פותח ChatGPT + Gemini + Perplexity ומטמיע בפק קיים. ריק = «אין חדש במשרד».  
לא סוכן ענן לכל רעיון מהרשת.

## 5. Treg רק אחרי מחיר קטלוג

Treg חי רק אחרי login. אומרים את מחיר הקטלוג **לפני** `call`. אין Insights מהאוויר כתחליף.

## 6. בריף קצר, מקור אחד

חסר מספר → «אין ספירה» / `X ₪`. לא לסרוק את כל ה־Drive. לא לטעון 273 כללים.

## 7. FCC לא נכנס לרשימה הזו

התקנת פרוקסי מקומי **לא** מקטינה את החשבון של Cloud Agent. מי שרוצה הורדה למק — `local-offload.md` אחרי ראש צוות.

## 8. הקשר לפני grep — vfmem → MAP → 2 nodes

לפני `grep` על המחסן או dump של כלי:

1. `python3 scripts/vfmem.py who <job>`
2. `packages/vfgraft/MAP.md` — פתח **שניים–שלושה** צמתים בלבד
3. רק אז מקור בפק

דחיסת artifact (Gmail thread, JSON, Drive): סיכום בשיחה, מקור מלא ב-checkpoint / Drive.  
פלייבוק מלא: `packages/vfharness/playbooks/context-thrift.md` (דפוס Headroom, בלי runtime על Cloud Agent).

## 9. Headroom — Mac בלבד, אופציונלי

[Headroom](https://github.com/headroomlabs-ai/headroom) proxy/MCP **לא** על Cloud Agent.  
Mac מקומי אחרי lead seat: `vffcc/playbooks/local-offload.md` + `vfmcp/GAP.md`.
