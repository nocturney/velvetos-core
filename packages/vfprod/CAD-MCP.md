# משפחת CAD / DCC MCP — דין HQ (לא פק חדש)

מושב: **ייצור** (`vfprod`) + רישום `vfmcp`.  
תאריך: 2026-09-05.  
מקורות: תשעה קישורי [mcpmarket.com](https://mcpmarket.com) (דפים 429/Cloudflare → **אין גוף**). גופים פתוחים מ־GitHub / חיפוש בלבד.  
לא ממציאים גוף חסום. לא ₪. לא Insights. לא Print מ־HQ.

קונספט/STL מ־Cloud Agent נשאר **3D AI Studio** ([`3DAISTUDIO.md`](3DAISTUDIO.md)).  
עריכת Blender במק: [`BLENDER-MCP.md`](BLENDER-MCP.md) (ahujasid כברירת מחדל אחרי ראש צוות).

## טבלת דין (2026-09-05)

| mcpmarket slug | גוף פתוח (מיפוי סביר) | דין Cloud | דין Desktop | למה |
|---|---|---|---|---|
| `blender-open` | [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp) (Ollama) | **skip** | sibling optional | אותו מעמד כמו Blender MCP + Ollama מקומי |
| `blender-ai` | משפחת Blender MCP (דף חסום; וריאנטי sandbox בשוק) | **skip** | sibling → `BLENDER-MCP.md` | לא מתקינים וריאנט שני במקביל ל־ahujasid בלי ראש צוות |
| `multicad` | [AnCode666/multiCAD-mcp](https://github.com/AnCode666/multiCAD-mcp) | **skip** | skip (אלא אם יש AutoCAD/ZWCAD במק) | COM/Windows CAD — לא רצפת ההדפסה של VF |
| `openscad-2` | משפחת OpenSCAD MCP ([petrijr/openscad-mcp](https://github.com/petrijr/openscad-mcp) ודומים) | **skip** | **local optional** אחרי ראש צוות | פרמטרי → STL; דורש OpenSCAD מקומי; עדיין `vlicense` + סלייס |
| `blender-vxai` | רשימת שוק בלבד; GitHub לא אומת | **skip** | skip עד זיהוי ריפו | אין גוף מאומת — לא ממציאים |
| `sketchup-1` | [russell-qca/sketchup-mcp](https://github.com/russell-qca/sketchup-mcp) | **skip** | **integration pending** on active Windows host | SketchUp 2026 + LayOut are installed and now have first-class craft via `.cursor/skills/vf-sketchup-layout-craft`; do not claim live MCP/Ruby automation until a separate local integration is accepted |
| `freecad-1` | [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | **skip** | local optional אם FreeCAD במק | CAD פרמטרי; לא מחליף 3DAI לקונספט מהיר |

## כלל זהב ל־VF

```
פנייה → 3DAI (או מאגר vlicense) → STL + CHECKLIST + סלייס → אדם מדפיס → איסוף שדרות
         ↘ (local host only, optional) Blender / OpenSCAD / FreeCAD / SketchUp — only through an accepted local adapter; craft guidance alone is not runtime proof
         ↘ (אופציונלי) Excalidraw לדיאגרמת תהליך פנימית — לא פיד
```

**אסור:** באצ׳ CAD כפול על Cloud · מפתח SVGMaker בגיט · AutoCAD/SketchUp כחובת HQ · טענה ש־mcpmarket «אומר» משהו בלי גוף.

## Failover

| נפל | מיד ל־ |
|---|---|
| כל Blender*/FreeCAD/SketchUp/OpenSCAD על Cloud | 3DAI MCP או אתר + דרייב |
| MultiCAD בלי AutoCAD | דילוג — לא ערימת VF |
| דף mcpmarket 429/Cloudflare | GitHub / «אין גוף» — ממשיכים |

מקור מפורט: `packages/vfresearch/sources/2026-09-05-mcpmarket-cad-nine.md`.
