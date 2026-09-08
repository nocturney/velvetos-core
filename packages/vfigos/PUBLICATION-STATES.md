# מצבי פרסום — prepared ≠ scheduled ≠ live

מושב: **צמיחה** (`vfigos` + `vfgrowth`). לא פק חדש.  
מכונה: [`PUBLICATION-STATES.json`](PUBLICATION-STATES.json).  
נעילה 8.9.2026 — Christian.

## חוק קשיח

אלה מצבים **שונים**:

`prepared` → `approved` → `scheduled` → `uploadAccepted` → `publishRequested` → `liveVerified`

או: `failed` → (retry/failover) → `deadLetter`

**LIVE רק אחרי `liveVerified`** — עם ראיית אימות אמיתית מהפלטפורמה.

אסור לסמן live בגלל:

- upload success
- scheduler accepted
- calendar event
- API container created
- publish requested

## קשר ל־Organic GATE

שער האורגני (`vfgrowth/GATE.md`) נשאר לאישור אדם לפני העלאה.  
מצבי הפרסום האלה מכסים את **נתיב השליחה/אימות** אחרי אישור.  
`approved_for_manual_posting` = `approved` כאן — **לא** live.  
`posted_manually` / verify כלי = `liveVerified` רק עם ראיה.  
**Calendar ≠ live.** `uploadAccepted` ≠ live.

## תגיות משרד

| תג | מצב |
|---|---|
| `#טיוטה` | prepared |
| `#לסקירה` | prepared |
| `#משובץ` | scheduled |
| `#נשלח-מ-HQ` | publishRequested או failover נשלח (לא בהכרח live) |
| `#ממתין-ל-כלי-IG` | waiting external tool |
| `#אחרי-פרסום` | רק אחרי liveVerified |

## בדיקה

`python3 scripts/check-publication-states.py`
