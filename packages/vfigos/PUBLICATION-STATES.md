# מצבי פרסום — prepared ≠ scheduled ≠ live

מושב: **צמיחה** (`vfigos` + `vfgrowth`). לא פק חדש.  
מכונה: [`PUBLICATION-STATES.json`](PUBLICATION-STATES.json).  
נעילה 8.9.2026 — Christian · עדכון תחבורה 10.9.2026.

## חוק קשיח

אלה מצבים **שונים**:

`prepared` → `approved` → `approved_export_local` → `staged` → `fetch_verified` → `scheduled` → `uploadAccepted` → `publish_requested` / `published` → `publish_pending_verification` → `published_verified` / `liveVerified`

או חוסמים מפורשים (לא למוטט ל־`blocked_publish_transport` מיד):

| חוסם | מתי |
|---|---|
| `blocked_creative_preflight` | PREFLIGHT / CTA / rights |
| `blocked_artifact_retrieval` | אין ייצוא מאושר אחרי ניסיון שחזור |
| `blocked_bridge_staging` | stage ל־publish-bridge נכשל |
| `blocked_public_fetch` | HTTPS fetch/SHA נכשל |
| `blocked_instagram_publisher` | `publish_*` נכשל |
| `blocked_live_verification` | יש receipt בלי get_media |
| `blocked_publish_transport` | **רק** אחרי שכל נתיבי השחזור נכשלו |

**LIVE רק אחרי `published_verified` / `liveVerified`** — עם ראיית אימות אמיתית מהפלטפורמה (`list_media` / `get_media`).

אסור לסמן live בגלל:

- upload success
- scheduler accepted
- calendar event
- API container created
- publish requested
- **publish_* tool success בלי אימות חי** → זה `publish_pending_verification` בלבד
- staged / fetch_verified בלבד

ייצוא מאושר מקומי (`approved_export_local`) בלי נכס bridge → מריצים `vf_publish_handoff.py recover` לפני חסימת תחבורה.

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
| `#אחרי-פרסום` | רק אחרי liveVerified / published_verified |

## בדיקה

`python3 scripts/check-publication-states.py`  
`python3 scripts/check-publish-handoff.py`
