# effective-html · הטמעה לבריף מייל

מושב: ייצור · Asia/Jerusalem  
מקור: https://github.com/plannotator/effective-html  
רישום: `packages/vfresearch/LINKS.json` → `effective-html`

## מה זה

ספריית skills ל־HTML עצמאי (wireframe, prototype, plan, diagram).  
לבריף שלנו הרלוונטי במיוחד:

| skill | שימוש ב־VF |
|---|---|
| `html-plan` | שומר על 01–07 ומקורות — לא הופך לדשבורד |
| `html` + `documents-and-presentations` | מייל בריף RTL, היררכיה, טבלאות ספירה |
| `html-wireframe` | ניסוי פורמט לפני שינוי `vfops/BRIEF.md` |

מדריך: https://www.effectivehtml.com/  
השראה: [The unreasonable effectiveness of HTML](https://thariqs.github.io/html-effectiveness)

## מה הוטמע

| פק | קובץ | מה |
|---|---|---|
| `vfbriefux` | `hq/brief-email.html` | תבנית HTML עצמאית לבריף 07:00 — Grok מדביק / HQ ממלא טיוטה |
| `vfbriefux` | `hq/EFFECTIVE-HTML.md` | מפת skill → חריץ בריף |
| `.cursor/skills/vf-morning-brief` | `SKILL.md` | נתיב HTML אחרי מילוי נתונים |
| `.cursor/vf-desk.json` | `tools.mobbin.failover` | Mobbin חסום → `brief-email.html` |

## חוקים (לא משתנים)

- שבעה בלוקים קיימים (`vfops/BRIEF.md`) — לא מחליפים מבנה.
- HQ לא שולח את המייל. Grok שולח.
- שדות מנהל: «אין ספירה» עד סנאפשוט מאומת.
- בלי ₪ מומצא, בלי Insights מומצאים, בלי שמות לקוחות מיותרים.

## בלוק 05

```
05 · משרד
מה נבנה / יועל: effective-html → תבנית HTML לבריף מייל ב־vfbriefux/hq/brief-email.html
```
