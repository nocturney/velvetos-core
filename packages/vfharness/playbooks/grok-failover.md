# פיילאובר מכסת Grok Bot

מושב: ראש צוות (רתמה) + כל המושבים על פקים קיימים.  
טריגר: «נגמרה מכסת Grok השבועית» / Grok לא זמין / הבעלים מבקש failover לגרוק.

לא פק חדש. לא מושב שישי.  
**HQ שולח דרך כלים** (`constitution/SEND.md`) — ג׳ימייל `send_message` ואינסטגרם לפי `vfigos/SEND.md`.  
לא מחכים לגרוק. לא מחכים לכריסטיאן. Grok הוא גיבוי אופציונלי.

## חוק אחד

כש־Grok נגמר — **HQ ממשיך לייצר ושולח**. ידיים לא ריקות.

| מסלול | מתי | מי שולח |
|---|---|---|
| `#נשלח-מ-HQ` | יש כלי (Gmail תמיד; IG Publish אם מחובר) | סוכן HQ |
| `#ממתין-ל-כלי-IG` | אין MCP Publish לפיד — אחרי Gmail+Drive+Canva | סוכן HQ (failover) |
| `#מוכן-ל-Grok` | רק אם ראש צוות מבקש גיבוי Grok | Grok אחרי חידוש |

דחוף ללקוח (שיחה, לא פיד) → אדם בוואטסאפ `050-2517000`.

## מה HQ לוקח על עצמו

| עבודה | פק | כלי |
|---|---|---|
| כיתוב | `vfcopy` + `vfgrowth` | Cursor · תזמורת |
| כריכה | `vfcanva` · `vfcovers` | Canva → `studio/render.py` → Superdesign |
| שליחת IG | `vfigos/SEND.md` | Publish אם יש · אחרת Drive+Gmail |
| בריף 07:00 | `vfops` | **Gmail send_message** |
| פנייה / הצעה | `vfconvert` → `vfsales` | Gmail **reply** / send (בלי ₪ מומצא) |
| מחקר | `vfresearch` | WebSearch + תזמורת. **לא Treg** |
| מסמך משרד | `vfbooks` / `vfops` | Drive `create_file` |

## מה לא עוברים (גם במכסה ריקה)

| פעולה | מי | למה |
|---|---|---|
| בוסט / אוטו־DM | — | נעול תמיד |
| וואטסאפ ללקוח | אדם `050-2517000` | אין MCP וואטסאפ |
| הדפסה / עצירת מדפסת | רצפה | `vfprod/FLOOR.md` |
| טענה שעלה לפיד בלי Publish | — | אסור להמציא |

## הפעלה (אותו רגע)

1. Checkpoint: `packages/vfharness/state/grok-failover-<YYYY-MM-DD>.json`
2. כל טיוטה רצה על הפק כרגיל.
3. שליחה מ־HQ דרך הכלים **עכשיו** — לא תור המתנה.
4. מחקר: תזמורת ChatGPT + Gemini + Perplexity (`ORCHESTRA.md`). בלי Treg.
5. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-grok-failover.md`.

## Failover ≠ המצאה

אין ₪ מכירה בלי ראש צוות. אין Insights. אין גוף Perplexity חסום. אין קישור Canva מומצא. אין «שלחו DM». אין «עלה לפיד» בלי כלי Publish.

## קישורים

- חוקת שליחה: `constitution/SEND.md`
- תזמורת: `constitution/ORCHESTRA.md`
- תור: `packages/vfigos/QUEUE.md`
- חבילת פרסום: `packages/vfigos/LIVE-PACKET.md` · `vfigos/SEND.md`
- מסמך קבע: `docs/GROK-FAILOVER.md`
