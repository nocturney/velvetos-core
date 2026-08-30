# Crew: decide

Source pattern: [makerskills `decide`](https://github.com/coreyhaines31/makerskills/blob/main/skills/decide/SKILL.md) — 37signals questions, triaged to 6–8, archive + revisit.
Packs: `vfbiz`, `vfops`. Seat: ראש צוות.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Framer | `vfbiz` | One-sentence fork, stakes, reversibility, deadline | Invent a third option that was not on the table |
| Questioner | `vfbiz` | 6–8 load-bearing questions | The full 38 |
| Decider | — | Human / lead seat on ₪, B2B, ads, TikTok | Agent as closer |
| Archivist | `vfbiz` | Write `hq/decisions/` | Fill sale ₪ |

## Capture

Get, then stop if any are missing:

- **The decision** in one Hebrew sentence (בין מה למה)
- **Stakes:** low / medium / high
- **Reversibility:** easy / hard / one-way door
- **Deadline:** date or «פתוח»
- **Context:** 1–3 sentences, cited if they mention a number

## Default questions (always)

1. האם בכלל צריך להחליט עכשיו?
2. האם האדם הנכון מחליט? (₪ / B2B / בוסט / טיקטוק = ראש צוות בלבד)
3. אינסטינקט ראשון — לפני ניתוח.
4. כמה קל להפוך?
5. מה נעקור אם נגיד כן? (עלות הזדמנות)

## Add at most three more

| If… | Add |
|---|---|
| Money / price | האם זה בעצם ויכוח על כסף? חסר → `X ₪` / «אין במקור» |
| Customer-facing | מי בחוץ תלוי בזה? איסוף שדרות / וואטסאפ |
| Print / license | האם `#vlicense` כבר עבר? מותג ישראלי לא מעתיקים |
| Recurring | מה החלטנו בפעם הקודמת? קרא את `hq/decisions/INDEX.md` |
| Stuck | למה זה לא הוחלט? אם הקיר הוא «אי אפשר» → `crews/unstuck.md` |

## Call (pick one, no hedge)

- **Decide now**
- **Decide smaller** (2–3 forks)
- **Wait** (what info would change it — then `vfresearch` or `vfcost`, not invention)
- **Don't decide**
- **Wrong person** — kick to lead seat / Christian / Grok

## Archive

Write `packages/vfbiz/hq/decisions/YYYY-MM-DD-<slug>.md` and append `INDEX.md`.

```markdown
# החלטה: <משפט>

**Date:** YYYY-MM-DD
**Decide by:** <date or פתוח>
**Reversibility:** easy / hard / one-way door
**Stakes:** low / medium / high

## הקשר
<1–3 משפטים>

## שאלות
### <נוסח השאלה>
<תשובה מילולית>

## החלטה
**<הקריאה>**

## נימוק
<2–3 משפטים>

## חזרה
**YYYY-MM-DD** — מה לבדוק (בלי Insights בדויים)
```

Revisit defaults: process 30 days · strategy / B2B lock 90 days · SKU / launch 30–60 days after a real floor proof.

## Done when

The call is written, the revisit date exists, and no sale ₪ was invented.
