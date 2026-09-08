# מצבי פרסום — prepared ≠ scheduled ≠ live

מושב: **צמיחה** (`vfigos` + `vfgrowth`). לא פק חדש.  
מכונה: [`PUBLICATION-STATES.json`](PUBLICATION-STATES.json).  
נעילה 8.9.2026 — Christian.

## חוק קשיח

אלה מצבים **שונים**:

`prepared` → `approved` → `scheduled` → `uploadAccepted` → `publishRequested` → `publish_pending_verification` → `liveVerified`

או: `failed` → (retry/failover) → `deadLetter`

**LIVE רק אחרי `liveVerified`** — עם ראיית אימות אמיתית מהפלטפורמה (`list_media` / `get_media`).

אסור לסמן live בגלל:

- upload success
- scheduler accepted
- calendar event
- API container created
- publish requested
- **publish_* tool success בלי אימות חי** → זה `publish_pending_verification` בלבד

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
| `#נשלח-מ-HQ` | publishRequested / publish_pending_verification או failover נשלח (לא בהכרח live) |
| `#ממתין-ל-כלי-IG` | waiting external tool או ממתין לאימות חי |
| `#אחרי-פרסום` | רק אחרי liveVerified |

## בדיקה

`python3 scripts/check-publication-states.py`
