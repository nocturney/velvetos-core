# prompts.chat · הטמעה 2026-08-31

מושב: ייצור · Asia/Jerusalem  
מקור: https://github.com/f/prompts.chat (לשעבר Awesome ChatGPT Prompts)

## מה נבדק (גוף אמיתי)

| רכיב | מה נלקח |
|---|---|
| README | ספר אינטראקטיבי, MCP (`/api/mcp`), self-host, CC0 על prompts.csv |
| ספר פרק 02 | אנטומיית פרומפט: תפקיד · הקשר · משימה · אילוצים · פורmat · few-shot |
| prompts.csv | **לא יובא** — ~20K פרומפטים גנéric; סיכון ל-DM / ₪ / שפה לא משרדית |
| Self-host (`npx prompts.chat new`) | **דילוג** — runtime שני; הקטלוג הוא המוצר |

## מה הוטמע

| פק | קובץ |
|---|---|
| `vfcopy` | `hq/templates/` — 3 תבניות משרד (פנייה, מעקב הצעה, IG) |
| `vfcopy` | `hq/PLAYBOOK.md` — בלוק אנטומיית פרומפט + הפניה לתבניות |
| `vfcopy` | `SKILL.md` — שורת מסלול |
| `vfmcp` | `docs/MCP-FIT.md` — MCP אופציונלי למחקר (לא חובה) |
| `vfresearch` | `LINKS.json` — רישום שבועי |

## מה לא הוטמע (מכוון)

- פק `vfprompts` — נגד «אין פק לרעיון»
- ייבוא bulk מ־`prompts.csv` / PROMPTS.md
- Self-host Next.js + PostgreSQL
- Claude plugin / `npx prompts.chat` CLI כתלות
- פרומפטים קהילתיים שלא עברו חוקה (CTA, ₪, DM)

## MCP (אופציונלי)

Remote: `https://prompts.chat/api/mcp` — `search_prompts`, `get_prompt`, `improve_prompt`, `search_skills`.  
שימוש: **מחקר בלבד** → סינון דרך `constitution/` → הטמעה ב־`vfcopy` / `vfmskill`. לא העתקה ישירה ללקוח.

## מה חדש לחקור

- פרקי ספר 06 (CoT) / 07 (few-shot) — אם `vfconvert` / `vfcost` צריכים חילוץ שדות טוב יותר
- `improve_prompt` MCP כלינט שני אחרי `ai-tells-he.md`

## בלוק 05

שבועי קישורים — הוטמע prompts.chat ב־`vfcopy` (תבניות + PLAYBOOK); MCP אופציונלי ב־`MCP-FIT`.
