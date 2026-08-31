# פיילאובר מכסת Grok Bot — תחליף מלא

מושב: ראש צוות (רתמה) + כל המושבים.  
מודל: [`constitution/GROK.md`](../../constitution/GROK.md) — Grok **מנהל ראשי**, לא גיבוי.

טריגר: מכסה שבועית 100% · Grok לא זמין · בעלים מבקש החלפה.

לא פק חדש. לא מושב שישי.

## חוק אחד

כש־Grok במכסה — **Cursor HQ + תזמורת מחליפים אותו לגמרי**. ידיים לא ריקות.  
**לא מחכים לגרוק.** לא מחכים לכריסטיאן.

| מסלול | מתי | מי |
|---|---|---|
| `#נשלח-בידי-Grok` | שוטף, מכסה חיה | Grok Bot |
| `#נשלח-מ-HQ` | מכסה ריקה — Gmail ו/או **Publish IG** | סוכן HQ |
| `#ממתין-ל-כלי-IG` | Publish MCP לא ירה — אחרי Gmail+Drive+Canva | HQ (failover) |
| `#מוכן-ל-Grok` | **אחרי חידוש מכסה** — מה שנשאר | Grok Bot |
| `#פרסום-חי-דחוף` | עכשיו | Grok אם חי · אחרת HQ Publish מיד (`SEND.md` / `LIVE-PACKET`) |

דחוף ללקוח (שיחה) → אדם `050-2517000`.

## מה HQ לוקח במכסה (תחליף מלא)

| עבודה | פק | כלי |
|---|---|---|
| כיתוב | `vfcopy` + `vfgrowth` | Cursor · תזמורת |
| כריכה | `vfcanva` · `vfcovers` | Canva → `render.py` → Superdesign |
| **פרסום IG ישיר** | `vfigos/SEND.md` | **Publish MCP** · Canva export |
| בריף 07:00 | `vfops` + `vfbriefux` | Gmail `send_message` + `htmlBody` תצוגה 3 |
| פנייה / הצעה | `vfconvert` → `vfsales` | Gmail reply/send |
| מחקר | `vfresearch` | WebSearch + תזמורת |
| מסמך | `vfbooks` / `vfops` | Drive `create_file` |

## הרשאות Publish IG

חובה לחבר: Cursor Team MCP / Canva Publish ל-`@velvets_cloud`.  
מפת: `docs/MCP-FIT.md` · `packages/vfmcp/GAP.md`. סודות מחוץ לגיט.

**אדם** מעלה ב-IG **רק** אם Publish + Gmail נפלו — לא ברירת מחדל.

## מה לא עוברים

בוסט / אוטו־DM · וואטסאפ MCP · Print מ-HQ · «עלה לפיד» בלי receipt.

## הפעלה

1. Checkpoint: `packages/vfharness/state/grok-failover-<YYYY-MM-DD>.json`
2. שליחה + **Publish IG** מ-HQ **עכשיו** — לא תור `#מוכן-ל-Grok`.
3. מחקר: תזמורת (`ORCHESTRA.md`).
4. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-grok-failover.md`.

## Failover ≠ המצאה

אין ₪ · אין Insights · אין גוף חסום · אין «שלחו DM».

## קישורים

- [`constitution/SEND.md`](../../constitution/SEND.md)
- [`constitution/ORCHESTRA.md`](../../constitution/ORCHESTRA.md)
- [`packages/vfigos/QUEUE.md`](../vfigos/QUEUE.md)
- [`docs/GROK-FAILOVER.md`](../../docs/GROK-FAILOVER.md)
