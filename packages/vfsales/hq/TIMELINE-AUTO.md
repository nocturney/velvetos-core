# Timeline Auto — מילוי אוטומטי אחרי אינטראקציה

מודול: `expert-revenue-loop`.  
בסיס: `CUSTOMER-TIMELINE.md`.

## טריגרים (חובה)

| אירוע | מי כותב | kind |
|---|---|---|
| פנייה נקראה | `@email-intelligence-engineer` | `inquiry` |
| הצעה נוסחה | `@sales-engineer` | `quote_drafted` |
| Gmail נשלח (הצעה) | HQ tool | `quote_sent` |
| תשלום אומת | `@bookkeeper-controller` / אדם | `payment_verified` |
| נכנס לתור | `@studio-producer` | `print_queued` |
| איסוף | אדם | `picked_up` |
| 7 ימים אחרי איסוף | `@customer-success-manager` | `followup_draft` |
| פוסט IG שיצר פנייה | `@pipeline-analyst` | `inquiry` + `ig_post_ref` |

## איפה

- Drive doc: `job/<שם-קצר>/timeline.md`
- או שורה בכרטיס pipeline (`PIPELINE-BOARD.md`)

## תבנית אירוע מינימלית

```markdown
| 2026-09-01 | quote_sent | הצעה X ₪ | Gmail msg … |
```

## אסור

- אירוע `dm_sent` אוטומטי
- ₪ שלא מאומת
- שם מלא / ת״ז

## קישור ל-IG

אם `ig_post_ref` ידוע — הוסף בעמודת note: `ig:YYYY-MM-DD-hook`
