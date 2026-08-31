# Office OS · CRM/ERP/Forum inspiration — 2026-08-31

מושב: ייצור · `@research-synthesist`  
Asia/Jerusalem · לא פק חדש · לא התקנת מוצר חי

מטרת הבעלים: ללמוד ממערכות ניהול/CRM/ERP/פורומים כדי לייעל את HQ היום, ולהכין מבנה לממשק ווב עתידי (צפייה / ניהול / שליחת פקודות).

## מה נבדק (גוף אמיתי)

| מקור | סוג | מה נלקח (דפוס) | Verdict |
|---|---|---|---|
| [twentyhq/twenty](https://github.com/twentyhq/twenty) | OSS CRM | Objects/views as code, pipeline kanban, ⌘K command palette, MCP לסוכנים | **Embed** |
| [frappe/erpnext](https://github.com/frappe/erpnext) | OSS ERP | Manufacturing + job cards + stock + DocType modules | **Embed** |
| [hcengineering/platform](https://github.com/hcengineering/platform) (Huly) | OSS suite | Inbox + planner + docs + issues באפליקציה אחת; API client | **Embed** |
| [monicahq/monica](https://github.com/monicahq/monica) | OSS PRM | Contact timeline, reminders, activity log על אדם | **Embed** |
| [nocobase/nocobase](https://github.com/nocobase/nocobase) | OSS no-code | Data model ≠ UI; plugins; AI employees + permissions | **Embed** (ארכיטקטורת אפליקציה עתידית) |
| [krayin/laravel-crm](https://github.com/krayin/laravel-crm) | OSS CRM | Lead → pipeline → activity; admin dashboard | **Embed** |
| [akaunting/akaunting](https://github.com/akaunting/akaunting) | OSS accounting | Invoices / expenses / modular apps; מספרים מאומתים | **Embed** → `vfbooks` |
| [idurar/idurar-erp-crm](https://github.com/idurar/idurar-erp-crm) | OSS ERP/CRM | Quote + invoice + customer — פשטות UI | **Partial** |
| [Dolibarr/dolibarr](https://github.com/Dolibarr/dolibarr) | OSS ERP/CRM | Enable-only modules; proposals + stock + agenda | **Embed** |
| [Odoo](https://www.odoo.com/) | Commercial/OSS | App-per-process; one platform many apps | **Embed** (מטאפורת פקים) |
| [Zoho One](https://www.zoho.com/all-products.html) | Suite | OS for business — אפליקציות מחוברות תחת זהות אחת | **Embed** (מושבים = מחלקות) |
| [Salesforce Pro Suite](https://www.salesforce.com/eu/small-business/pro-suite/) | Commercial | Role dashboards, quoting, forecasting, custom objects, flows+sandbox | **Embed** (דאשבורד לפי תפקיד) |
| [NetSuite](https://www.netsuite.com/portal/home.shtml) | Commercial | Role home + KPI portlets; order→fulfillment | **Embed** (portlets לבריף) |
| [monday.com](https://monday.com/) | Work OS | Boards by stage; agents + human-in-loop; activity log | **Embed** |
| XenForo / vBulletin / Invision / WoltLab | Forums | Thread=שיחה; mod queue=שער אישור; groups=מושבים; digest=בריף | **Embed** (דפוס שיחה) |

הערות גוף: XenForo.com החזיר 500 בזמן הסקירה — דפוסי פורום מבוססים על ידע מוצר כללי + דמיון ל־Invision/WoltLab (לא הומצא מספר/מחיר).

## מה לא עושים

- לא מתקינים Twenty / ERPNext / NocoBase / Odoo / Monday כראנטיים שני במשרד Cursor.
- לא בונים מושב שישי ולא פק «crm» / «erp» חדש.
- לא ממציאים ₪ / Insights.
- לא אתר שיווקי ציבורי ולא ווידג׳ט מחיר מ־HQ (נשאר נעול).
- **כן** מותר: משטח פקודות פנימי (owner-only) כ־*תצוגה* על פקים — ראו ADR ב־`docs/OFFICE-OS-EMBED-he.md`.

## מיפוי להטמעה במקום

| דפוס | פק / קובץ |
|---|---|
| Capability registry + ⌘K | `vfops/hq/COMMAND-SURFACE.md` + `capabilities.json` |
| Pipeline board (kanban) | `vfops/hq/PIPELINE-BOARD.md` |
| Role portlets → brief 01–07 | `vfbriefux/hq/PORTLETS.md` |
| Customer timeline | `vfsales/hq/CUSTOMER-TIMELINE.md` |
| Ledger views (invoice/expense) | `vfbooks/hq/LEDGER.md` (הפניה) |
| Office map / blast | `vfgraft` + חוקה |
| Research registry | `LINKS.json` + דוח זה |

## המלצות חוקה (שוחרר / הוחמר)

| נושא | לפני | אחרי (הצעה מיושמת) |
|---|---|---|
| «לא אתר מ־HQ» | נעילה גורפת | **אתר שיווקי / מחיר ציבורי** נשאר נעול. **קונסולת משרד פנימית** (צפייה+פקודות על capabilities) מותרת כתצוגה — לא מושב, לא runtime שני |
| נעילות ליבה | — | ללא שינוי: אין אוטו־DM, אין בוסט בלי ראש צוות, אין ₪ מומצא, איסוף שדרות בלבד, HQ שולח דרך כלים |

## מה לבנות בהמשך (לא היום)

1. UI ווב שקורא `capabilities.json` + checkpoints + לוח צינור.
2. MCP/API דק מעל Gmail/Canva/Drive (כבר קיימים ככלים) — לא מחליף את Cursor.
3. בחירת stack (Twenty schema / NocoBase plugins / custom) — רק אחרי שהבעלים מאשר מוצר.
