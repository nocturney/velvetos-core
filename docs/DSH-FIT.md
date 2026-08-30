# DSH plugin fit — Velvet Factory

מקור: [awesome-dsh-plugin/awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)  
ספירה רשמית: **2710** תוספים ([count.json](https://awesome-dsh-plugin.com/count.json), 2026-08-30).  
פק: [`packages/vfdsh/`](../packages/vfdsh/).  
בדיקה: `python3 scripts/check-vfdsh.py`.

DeepSeek Harness הוא סוכן קידוד שני. **לא מתקינים אותו ב-HQ.** הרשימה עצמה מזהירה שתוסף רץ עם הרשאות המארח. מטמיעים דפוסים על הפאקים הקיימים — כמו `vfe2b`.

## חמישה צוותים שכן עוזרים

| צוות | דפוס מהרשימה | פק | נעילה |
|---|---|---|---|
| ראיית רצפה | Modlens, Vision Toolkit, PictureReader, pbr-render | `vfprod` `vfcovers` `vlicense` | צילום שצוין. אין סצנה מומצאת |
| מסמכים בתיבה | MinerU, PDF/Office → Markdown | `vfbooks` `vfconvert` `vfsales` | Gmail קריאה. אין ₪ מומצא |
| זיכרון קטלוג | Engramory, MemSearch, project-memory | `vfresearch` `vfsku` `vfops` | ציטוט קובץ. אין שרת זיכרון |
| לוח צינור | dsh_workflow, Taskboard (רק in_review), verification | `vfops` `vfprod` `vfconvert` | אדם על «בוצע». אין מדפסת מ-HQ |
| נכסי עיצוב | Superdesign (כבר כאן), TongFlow/iPolloWork אחר כך | `vfcopy` `vfcovers` `vfcanva` `vfigos` | Canva או Superdesign. HQ לא שולח |

הפעלה: `@vfdsh floor` / `docs` / `memory` / `board` / `design`.

## כבר על השולחן

Treg ו-Superdesign מופיעים ברשימת DSH. אצלנו הם כבר skill. אין חבילת `dsh.bundle`.

273 סוכני Agency כבר ב-`.cursor/rules/`. פורט DSH של אותה רשימה מיותר.

## מה דולג בכוונה

- `dsh plugin add`, dsh-market, dsh-find-plugin — ראנטיים שני.
- DSH IM / scheduled send / QQ / Lark חי — HQ לא שולח.
- קרון, אוטו-המשך, בוט 24/7 — אדם בשרשרת.
- ערכות נושא, חיות מחמד, מניית A, pentest, צעצועים.
- OpenViking / WeKnora / MemOS כשרת — הקטלוג ב-git מספיק.

פירוט: [`packages/vfdsh/LOCK.md`](../packages/vfdsh/LOCK.md), [`packages/vfdsh/catalog.json`](../packages/vfdsh/catalog.json).
