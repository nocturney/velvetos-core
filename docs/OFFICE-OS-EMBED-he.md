# Office OS — מפת הטמעה · 2026-08-31

השראה מ־18 מוצרי CRM / ERP / Work OS / פורומים. **דפוסים על פקים קיימים** — לא התקנת מוצר, לא מושב שישי, לא ראנטיים שני.

מקור מלא: `packages/vfresearch/sources/2026-08-31-office-os-crm-erp.md`

## מה למדנו (בקצרה)

| משפחה | דוגמאות | לקח ל־VF |
|---|---|---|
| CRM מודרני | Twenty, Krayin, Salesforce Pro | אובייקטים (פנייה/לקוח/הזדמנות), לוח צינור, לוח פקודות (⌘K), דאשבורד לפי תפקיד |
| ERP | ERPNext, Dolibarr, NetSuite, Odoo, IDURAR | מודולים שמדליקים לפי צורך; ייצור=תור הדפסה; מלאי=מק״ט/חומר; הצעה→חשבונית |
| Accounting | Akaunting, NetSuite financials | תצוגות חוב/שולם/הוצאה — רק מספרים מאומתים |
| Work OS | Monday, Huly, Zoho One | לוחות לפי שלב; סוכנים עם אדם בשער; זהות אחת לכל האפליקציות |
| No-code / AI infra | NocoBase, Twenty apps | מודל נתונים ≠ UI; פלאגינים; AI עם הרשאות כמו אדם |
| PRM | Monica | ציר זמן על לקוח (שיחות, איסוף, מעקב) |
| Forums | XenForo, vBulletin, Invision, WoltLab | שיחה=thread; תור מודרציה=שער אישור; קבוצות=מושבים; digest=בריף |

## מה הוטמע היום

| ארטיפקט | פק |
|---|---|
| `COMMAND-SURFACE.md` + `capabilities.json` | `vfops` |
| `PIPELINE-BOARD.md` | `vfops` |
| `PORTLETS.md` | `vfbriefux` |
| `CUSTOMER-TIMELINE.md` | `vfsales` |
| ADR פנימי + עדכון «לא אתר» | `constitution` + `AGENTS.md` |
| רישום קישורים | `vfresearch/LINKS.json` |

## ADR — קונסולת משרד פנימית

**סטטוס:** מקובל (2026-08-31)

**החלטה:** מותר לתכנן ולבנות **ממשק ווב פנימי** (owner / ראש צוות) ש:

1. מציג מה המערכות יודעות (צינור, בריף, ספרים, תור תוכן, checkpoints).
2. שולח **פקודות** רק דרך ה־capability registry (`vfops/hq/capabilities.json`) — אותן פעולות שכבר מותרות בחוקה (Gmail tool, Canva, Drive create_file, וכו׳).
3. **אינו** מושב שישי, **אינו** runtime שני, **אינו** מחליף את Cursor כמשרד.

**נשאר נעול:** אתר שיווקי ציבורי, ווידג׳ט מחיר, אוטו־DM, בוסט בלי ראש צוות, משלוח ארצי, המצאת ₪/Insights.

**למה:** Twenty/NocoBase/Monday מראים ש־command surface + human-in-loop מאיצים צמיחה בלי לוותר על גבולות. נעילת «לא אתר» הייתה רחבה מדי — פיצול ל־*ציבורי נעול* / *פנימי מותר* מייעל בלי לשבור מנדט.

## מפת UI עתידית (השראה, לא ספק)

```
┌─────────────────────────────────────────────┐
│  Velvet Factory · Command Surface (owner)   │
│  ⌘K · capabilities.json · seat switcher     │
├──────────┬──────────────────────────────────┤
│ Pipeline │  פנייה → שיחה → הצעה → הדפסה → איסוף │
│ Board    │  (כרטיסים מ־Drive/Gmail/job folder) │
├──────────┼──────────────────────────────────┤
│ Portlets │  01 החלטה · 02 כסף · 03 תור · …   │
│ (=brief) │  «אין ספירה» כשאין מקור            │
├──────────┼──────────────────────────────────┤
│ Timeline │  לקוח / פנייה — אירועים אמיתיים   │
├──────────┼──────────────────────────────────┤
│ Agents   │  הרץ skill / crew · activity log  │
│          │  human-in-loop על ₪ ופרסום        │
└──────────┴──────────────────────────────────┘
```

עיצוב: לשמור על שפת `vfbriefux/hq/DESIGN.md` (RTL, navy/cream/gold) — לא סגול-SaaS גנרי.

## מה לא לבחור עכשיו

- להתקין Odoo/ERPNext/Twenty כמערכת חיה במקום ה־catalog.
- Monday/Salesforce כמקור אמת ל־₪.
- פורום קהילתי ציבורי — לא רלוונטי לסטודיו איסוף-בלבד.

## צעד הבא (ראש צוות)

1. לאשר את ה־ADR (או לדחות את קונסולת הפנים).
2. כשמוכנים למוצר: לבחור stack (custom על capabilities / Twenty schema / NocoBase) — החלטת מוצר, לא אוטומטית מ־HQ.
