# דוח שתילה — taste-skill לתוך HQ/OS

תאריך: 31 באוגוסט 2026  
מקור: https://github.com/Leonxlnx/taste-skill (MIT)  
סטודיו: Velvet Factory · שדרות · איסוף בלבד · וואטסאפ 050-2517000 · IG @velvets_cloud  
לא פק חדש. דפוסים על `vfharness`, `ui-finish-gate-reviewer`, `vfcovers`.

## מה נקרא

`taste-skill` הוא ספריית Agent Skills ל־**פרונטאנד web** (anti-slop): brief inference, שלושה dials (VARIANCE / MOTION / DENSITY), וריאנטים ויזואליים, skills ליצירת תמונות (brandkit / comps), ו־`output-skill` לאכיפת פלט מלא. יש גם תיקיית `research/laziness/` על קיצורי דרך של LLM.

אצלנו **לא** הורץ `npx skills add`. לא הותקן פלאגין. לא נפתח pack `vftaste`. הוטמעו **דפוסים נבחרים** — אותו כלל כמו `vfmakers` / `vfmskill`.

## מה נשתל

| מקור | לאן | מושב |
|---|---|---|
| `output-skill` | `packages/vfharness/playbooks/full-output-enforcement.md` | רתמה |
| Brief Inference (v2 §0) + anti-defaults | `.cursor/rules/ui-finish-gate-reviewer.mdc` | UX / finish gate |
| restraint / grid / negative space (brandkit logic) | `packages/vfcovers/hq/PLAYBOOK.md` | כריכות — בריף בלבד |
| research/laziness (מappings) | playbook הרתמה + דוח זה | ראש צוות |

## מה דולג ולמה

| דולג | למה |
|---|---|
| `npx skills add` / vendor מלא | skills מחוץ למבנה HQ; Cursor כבר המשרד |
| `taste-skill` v2 / gpt-taste / brutalist / image-to-code | web dev; לא עבודת הרצפה |
| `brandkit` / `imagegen-*` כ-generator | סותר «לא להמציא hex/fonts/brand» — Canva + brand-check |
| Sent.dm / Stitch | toolchain נפרד; WhatsApp נשאר אנושי |
| pack חדש | חוק AGENTS: ממפים על פק קיים |

## מתי כן taste-skill מלא

רק אם נפתח **אתר סטודיו** תחת `vfbiz` — אז vendor + overrides: עברית, WhatsApp `050-2517000`, איסוף שדרות, בלי משלוח ארצי. עד אז — finish gate + Canva.

## איך עובדים

```
@vfharness     — פלט מלא; checkpoint על [PAUSED]
@ux-architect  — Design Read לפני finish gate
@vfcovers      — restraint בכריכה; proof מהרצפה בלבד
```

בדיקה: `python3 scripts/check-all.py`.
