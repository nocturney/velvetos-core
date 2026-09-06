# Blender MCP — מקומי אופציונלי (לא Cloud)

מושב: **ייצור** (`vfprod`). לא פק חדש.  
מקור: [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) · רישום שוק: [mcpmarket.com/server/blender-model-context-protocol](https://mcpmarket.com/server/blender-model-context-protocol) (דף השוק עלול להיות מאחורי Cloudflare — גוף פתוח = GitHub).  
שער: `vlicense` · כרטיס: `vfsku` · קונספט מ־HQ: [`3DAISTUDIO.md`](3DAISTUDIO.md).

אין מפתח בגיט. אין הדפסה מ־HQ. אין ₪ מומצא.

## דין

| סביבה | סטטוס |
|---|---|
| **Cloud Agent** | **skip** — אין Blender GUI / addon / TCP מקומי ב־sandbox |
| **Desktop Mac (בעלים)** | **local optional** אחרי אישור ראש צוות |
| קונספט / STL מ־HQ | נשאר **3D AI Studio** (MCP `threedaistudio` או אתר) |

Blender MCP הוא עריכת סצנה מקומית (מודלים, חומרים, רנדור, קוד `bpy`) — לא מחליף סלייסר, לא מחליף שער רישיון, ולא מחליף הוכחת רצפה לאינסטגרם.

## מה זה נותן (כשמחובר במק)

1. Addon ב־Blender מאזין מקומית.
2. שרת MCP (`uvx blender-mcp`) מחובר ל־Cursor Desktop.
3. סוכן יכול ליצור/לשנות אובייקטים, חומרים, ולבדוק סצנה.

התקנה: לפי README של הריפו (`uv` → MCP client → `uvx blender-mcp install-addon` → Start MCP Server ב־viewport). לא מעתיקים את המדריך לכאן כחובת Cloud.

## צינור Velvet Factory

```
פנייה / קונספט
  → 3DAI (Cloud או Desktop) או מאגר ב־vlicense
  → STL בדרייב + CHECKLIST + סלייס
  → (אופציונלי, מק בלבד) Blender MCP לעריכה אמנותית לפני ייצוא חוזר
  → אדם מדפיס → איסוף שדרות
```

לא: באצ׳ מכירה מ־Blender · מחיר מקרדיטים · Print מ־HQ · addon ב־Cloud Agent · פק `vfblender`.

## אחים בשוק (2026-09-05)

וריאנטים נוספים מ־mcpmarket (`blender-open`, `blender-ai`, `blender-vxai`) — כולם **אותו דין**: Cloud skip; Desktop לא מתקינים במקביל ל־ahujasid בלי ראש צוות. פירוט משפחה: [`CAD-MCP.md`](CAD-MCP.md).

## Failover

| מה נפל | מעבירים מיד ל־ |
|---|---|
| Blender / MCP מקומי לא רץ | 3DAI MCP או אתר + דרייב |
| Cloud Agent בלי Blender | תמיד 3DAI / אתר — לא «מחכים למק» |
| אין רישיון מסחרי | `vlicense` עוצר — גם אם הסצנה יפה |
