# vfe2b — Awesome-AI-agents desk

מפה של [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) אל משרד Velvet Factory.

הרשימה מונה **209** סוכנים (קוד פתוח + מוצרים). שכבת תזמורת נוספת: [awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) (**194**, 31.8.2026) על אותם צוותים. רובם מסגרות קידוד, אוטונומיה מלאה, או SaaS שדורש מנוי. אצלנו לא מתקינים את כולם. מטמיעים **דפוסים** על הפאקים הקיימים.

## מה כן אצלנו

| דפוס מהרשימה | פק | מה עושים |
|---|---|---|
| CrewAI / AutoGen | `vfops`, `vfbiz` | צוות תפקידים + אדם בשרשרת |
| Orca (ADE pattern) | `vfops` + צוות קיים | משמרת: תיק אחד, `worker_done` / `escalation` / `decision_gate`. בלי התקנה |
| Orchestrators overlay | אותה משמרת + `vfharness` | דופק / אימות / ארטיפקט / תקרת לולאה. בלי amux/OpenClaw |
| GPT Researcher / Aomni | `vfresearch` | מתכנן שאלות + אוספי מקורות |
| Lindy / Floode / Cal.ai / Taskuary | `vfbriefux`, `vfseason` | בריף בוקר; HQ שולח את 07:00 דרך כלי |
| Claygent / Docket | `vfsales`, `vfconvert` | מחקר פנייה; ₪ רק אחרי ראש צוות |
| Wordware / GoCharlie | `vfcopy`, `vfigos`, `vfgrowth` | טיוטה + שליחה דרך `vfigos/SEND.md` |
| Julius / Vanna / Wren | `vfcost`, `vfbooks`, `vfinsights` | שאלות רק על מספרים שכבר קיימים |
| MemGPT / Private GPT | HQ + `vfresearch` | זיכרון מהקטלוג; בלי להמציא |
| Zapier / Bardeen / Gumloop | `vfops` | נהלי צומת; אין Zap חי מ-HQ |
| Cursor / Superagent+E2B | המשרד הזה | כבר רץ כאן; אין ארגז חול שני |
| Diagram / v0 | `vfcovers`, `vfbriefux` | Superdesign / Canva; לא אתר חדש |

## מה לא

ראה [`LOCK.md`](LOCK.md): AutoGPT ומשפחת BabyAGI, מכירה אוטונומית, צ'אטבוט 24/7, אוטו־DM/בוסט, מחיר ₪ מומצא, שליטה במדפסת מהמשרד, התקנת Orca/amux/OpenClaw. HQ **כן** שולח ג׳ימייל/IG דרך כלים.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | בחירות + פסילות E2B, קריא למכונה |
| [`orchestrators.json`](orchestrators.json) | מפת 194 תזמורים על אותם צוותים |
| [`ORCHESTRATORS.md`](ORCHESTRATORS.md) | נוהל שכבת התזמורת |
| [`EMBED.md`](EMBED.md) | איך מריצים את חמשת הצוותים + משמרת + תזמורת |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`crews/`](crews/) | נהלי צוות להרצה ב-Cursor |
| [`fixtures/run-cards.json`](fixtures/run-cards.json) | כרטיסי משמרת לדוגמה — מצב אחד בלבד |
| [`scripts/check-vfe2b.py`](../../scripts/check-vfe2b.py) | בדיקת עקביות מול `packages/manifest.json` |

## איך מפעילים

ב-Cursor:

```
@vfe2b morning brief
@vfe2b research <topic>
@vfe2b inquiry <job or WhatsApp thread>
@vfe2b content <brief id>
@vfe2b books
@vfe2b run <job>
```

או פותחים את הקובץ ב-`crews/` ומריצים לפי הסדר.

`python3 scripts/check-vfe2b.py` — צפי: `OK picks packs crews locks`.
