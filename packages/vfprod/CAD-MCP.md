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
| `excalidraw-4` | [excalidraw/excalidraw-mcp](https://github.com/excalidraw/excalidraw-mcp) | **optional later** (remote) | optional | דיאגרמות משרד פנימיות — לא מחליף Canva ל־IG |
| `blender-open` | [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp) (Ollama) | **skip** | sibling optional | אותו מעמד כמו Blender MCP + Ollama מקומי |
| `blender-ai` | משפחת Blender MCP (דף חסום; וריאנטי sandbox בשוק) | **skip** | sibling → `BLENDER-MCP.md` | לא מתקינים וריאנט שני במקביל ל־ahujasid בלי ראש צוות |
| `svgmaker` | [GenWaveLLC/svgmaker-mcp](https://github.com/GenWaveLLC/svgmaker-mcp) | **skip** | later + API key | מפתח ספק; Canva קודם למותג |
| `multicad` | [AnCode666/multiCAD-mcp](https://github.com/AnCode666/multiCAD-mcp) | **skip** | skip (אלא אם יש AutoCAD/ZWCAD במק) | COM/Windows CAD — לא רצפת ההדפסה של VF |
| `openscad-2` | משפחת OpenSCAD MCP ([petrijr/openscad-mcp](https://github.com/petrijr/openscad-mcp) ודומים) | **skip** | **local optional** אחרי ראש צוות | פרמטרי → STL; דורש OpenSCAD מקומי; עדיין `vlicense` + סלייס |
| `blender-vxai` | רשימת שוק בלבד; GitHub לא אומת | **skip** | skip עד זיהוי ריפו | אין גוף מאומת — לא ממציאים |
| `sketchup-1` | [russell-qca/sketchup-mcp](https://github.com/russell-qca/sketchup-mcp) | **skip** | skip אלא אם SketchUp במק | לא כלי הרצפה של VF |
| `freecad-1` | [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | **skip** | local optional אם FreeCAD במק | CAD פרמטרי; לא מחליף 3DAI לקונספט מהיר |

## כלל זהב ל־VF

```
פנייה → 3DAI (או מאגר vlicense) → STL + CHECKLIST + סלייס → אדם מדפיס → איסוף שדרות
         ↘ (מק בלבד, רשות) Blender / OpenSCAD / FreeCAD MCP לעריכה
         ↘ (אופציונלי) Excalidraw לדיאגרמת תהליך פנימית — לא פיד
```

**אסור:** באצ׳ CAD כפול על Cloud · מפתח SVGMaker בגיט · AutoCAD/SketchUp כחובת HQ · טענה ש־mcpmarket «אומר» משהו בלי גוף.

## Failover

| נפל | מיד ל־ |
|---|---|
| כל Blender*/FreeCAD/SketchUp/OpenSCAD על Cloud | 3DAI MCP או אתר + דרייב |
| SVGMaker בלי מפתח | Canva / Superdesign / `GenerateImage` |
| MultiCAD בלי AutoCAD | דילוג — לא ערימת VF |
| דף mcpmarket 429/Cloudflare | GitHub / «אין גוף» — ממשיכים |

מקור מפורט: `packages/vfresearch/sources/2026-09-05-mcpmarket-cad-nine.md`.
