# Print-Done — כרטיס עבודה אחרי הדפסה תקינה

מושב: **ייצור** (`@studio-producer`) → **צמיחה** (`vfom` / `vfcopy` / `vfgrowth`) → **סקירה** (`vfigos`).  
לא פק חדש. HQ **לא** מתחבר למצלמת מדפסת ולא מדפיס מרחוק.  
אירוע קטלוג: `print.done` · אחרי טיוטה: `content.draft_ready` (`packages/velvetos/schema/events.catalog.json`).

## למה

סוגרים Print→Post **כגשר נתונים**, לא כמפרסם אוטומטי:

`הדפסה תקינה (רצפה/Edge)` → כרטיס + מדיה → טיוטת ריל/סטורי → `PREFLIGHT` → שיבוץ/שליחה דרך כלים.

## מתי

אחרי הדפסה תקינה עם Timelapse או סטיל אמיתי מהמיטה.  
חסר גלם = **חסר** — לא ממציאים סצנת רצפה.

## כרטיס (חובה לפני תוכן)

העתק ל־Drive `create_file` **או** `packages/vfprod/hq/cards/YYYY-MM-DD-<sku-or-job>.md`:

```markdown
# Print card · <job/sku>

producedAt: YYYY-MM-DD
layer: edge   # או office אם אדם מילא ידנית בלי host
event: print.done

## מטא
- sku / שם עבודה:
- חומר (מ־MATERIAL.md בלבד):
- גרמים (אם נמדד; אחרת חסר):
- דקות הדפסה (אם נמדד; אחרת חסר):
- מדפסת / מיטה (אם ידוע):
- רישיון (`vlicense`): OK / חסר

## מדיה
- timelapse path / Drive id:
- still path (אופציונלי):
- proof על המיטה: כן / חסר

## מסירה
- יעד תוכן: ריל / סטורי / דולג
- מסר לצמיחה: vfom hybrid-reel או clip-factory
- סטטוס: card_ready → draft → preflight → scheduled / blocked
```

Envelope מינימלי (checkpoint / קובץ אירוע):

```json
{
  "name": "print.done",
  "producedAt": "YYYY-MM-DD",
  "layer": "edge",
  "source": "vfprod/PRINT-DONE",
  "correlationId": "<job-or-sku>",
  "payload": {
    "sku": "",
    "material": "",
    "grams": null,
    "minutes": null,
    "mediaPath": "",
    "license": "OK|חסר"
  }
}
```

## צינור אחרי הכרטיס

| שלב | מי | קובץ | עושה | לא עושה |
|---|---|---|---|---|
| 1 כרטיס | ייצור | זה + `FLOOR.md` | ממלא מטא + נתיב מדיה | לא מפרסם |
| 2 חיתוך | צמיחה | `vfom/crews/clip-factory.md` / `hybrid-reel.md` | כרטיסי קליפ / ביטים | לא Veo; לא סצנה מומצאת |
| 3 כיתוב | סטודיו/צמיחה | `vfcopy` + `VOICE.md` | כיתוב + CTA וואטסאפ | לא «שלחו DM»; לא ₪ מומצא |
| 4 ויזואל | צמיחה | Canva / `vfcovers` | כריכה / טקסט על פריים | לא JPEG גולמי כ«מוכן» |
| 5 שער | צמיחה | `vfgrowth/PREFLIGHT.md` | ארטיפקט `preflight/<id>.md` | לא שיבוץ בלי עבור |
| 6 לוח | צמיחה | `vfigos` + `CALENDAR.md` | סקירה / שיבוץ / שליחה בכלים | לא אוטו־DM; לא בוסט |

אחרי טיוטה מוכנה לסקירה — אירוע `content.draft_ready` (payload: `jobId`, `format`, `preflightPath`).

## נעול

- אין חיבור HQ→מצלמת Bambu/Snapmaker/Elegoo כדמון בריפו Core (Edge עתידי / Grok־רצפה).
- Watchtower (דשבורד חווה) = מקור Edge אפשרי לכרטיס הזה — [`WATCHTOWER.md`](WATCHTOWER.md). לא Print מ־HQ; לא Publish אוטומטי.
- אין תזמון ישר לפיד בלי PREFLIGHT.
- אין Print מ־HQ · אין סקר→הדפסה · אין אוטו־DM.
- גרמים/דקות חסרים = `חסר` — לא ניחוש ל־`vfcost` / כיתוב.

## קישורים

- רצפה: `FLOOR.md`
- דשבורד חווה (Edge): `WATCHTOWER.md`
- חומרים: `MATERIAL.md`
- מחקר שבועי: `packages/vfresearch/hq/PRINT-DEMAND.md`
- שליחה: `packages/vfigos/SEND.md` · `constitution/SEND.md`
