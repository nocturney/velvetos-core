# DESIGN.md — מפת הטמעה

מקור: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) · פורמט [Google Stitch DESIGN.md](https://stitch.withgoogle.com/docs/design-md/overview/)

## מתי

- HQ בונה או מעדכן HTML לבריף (`MAIL.html`, `brief-email.html`, `render_mail.py`).
- Wireframe כש-Mobbin חסום.
- **לא** מחליף Canva brand kit לפיד — `@velvets_cloud` נשאר ב-`vfcanva`.

## skill → קובץ

| מושג ב-awesome-design-md | אצלנו |
|---|---|
| `AGENTS.md` = how to build | `AGENTS.md` + `vfbriefux/SKILL.md` |
| `DESIGN.md` = how it looks | `hq/DESIGN.md` (זה) |
| Community brand extract | **לא** — בנינו מ-`MAIL.html` + BRIEF-SLOTS |
| `design-md lint` / Tailwind export | אופציונלי מקומי; HQ לא תלוי ב-npm |

## מה לא הוטמע

- העתקת Stripe/Vercel/Linear מהקטלוג — לא מותג VF
- `DESIGN.md` בשורש הריפו — יושב תחת `vfbriefux/hq/` כי אין אפליקציית web אחת
- Figma / JSON schema נפרד — markdown+YAML מספיק

## סנסור

אין סנסור ייעודי. שינוי ב-`DESIGN.md` או `MAIL.html` → `python3 scripts/check-all.py` אם נגעו בקטלוג.
