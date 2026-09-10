# Creative Autopilot — Velvet Factory

מושב: צמיחה + Office Control Plane. זהו overlay על המערכת הקיימת; **לא** orchestrator שני, לא pack חדש ולא runtime חדש.

## מטרה

להפוך `print.done` / מוצר חדש / חומר מעניין / כשל שימושי / media intake להזדמנות תוכן שמתקדמת אוטונומית עד תוצר ופרסום דרך כלי מחובר, בלי לבקש מהבעלים החלטות יצירתיות שגרתיות.

הבעלים נדרש רק כשאין דרך אמיתית להשלים את העולם הפיזי או כשקיים שער עסקי/משפטי אמיתי.

## Pipeline

```text
real event / opportunity
  -> opportunity triage
  -> Creative Director
  -> shot-gap check
  -> media ready?
       no  -> waiting_for_media + minimal shotRequest -> HUMAN_REQUIRED
       yes -> asset ingest/classification
  -> Edit Director / EDL
  -> cover + caption
  -> Visual OS QA + CONTENT-RUBRIC + policy + PREFLIGHT
  -> failed quality? -> AUTO_FIX -> QA again
  -> feed/slot decision
  -> publish authorization
  -> connected Instagram publish tool
  -> live verification / honest failover
  -> performance ingest when evidence exists
  -> daily learning
```

## Creative Director

אחד את `Visual Director` + `First-Frame Hunter` + `Shot Gap Detector` לתפקיד אחד. הפלט חייב לכלול:

- concept + objective + audience.
- visual emotion / proof story.
- 3–5 first-frame candidates + בחירה מנומקת אחת.
- shot list מדויק: type, angle, distance, orientation, duration, action, proof.
- background + lighting direction.
- on-film text hierarchy.
- cover direction.
- missing shots only when באמת חסר חומר פיזי.

אין להסלים לבעלים “איזה Hook אתה מעדיף?” או “איזה cover אתה אוהב?”. לבחור לבד לפי `VISUAL-OS.md` והוכחת רצפה.

## Asset Library

Media Vault הוא מקור הנכסים הקנוני. סיווג תוכן משתמש ב־`hero|macro|process|failure|proof|human|b-roll`, orientation, quality, rights/approval, project/job/SKU/material. אין קטלוג מדיה מקביל.

## Edit Director

`EDIT-DIRECTOR.md` מייצר EDL אופרטיבי: asset refs אמיתיים, in/out, crop, speed, cut, overlay, audio. אם חסר shot קריטי — בקשה מינימלית אחת במקום שאלה יצירתית.

## Publishing Director

אחד `Cover Art Director` + `Feed Architect` + Brand QA:

1. ליצור 3 cover directions ולבחור אחד.
2. לבדוק Visual OS + CONTENT-RUBRIC + policy + rights.
3. לתקן אוטונומית כשאפשר.
4. לבחור slot מתוך `vfgrowth/CALENDAR.md`; לא להמציא cadence חדש.
5. לפרסם דרך כלי Instagram מחובר רק אם ה־instance מאפשר standing authorization וכל שערי ה־preflight עברו.
6. אין receipt אמיתי / live verification -> לא לטעון שפורסם; להיכנס ל־Degraded/failover לפי `constitution/SEND.md`.

## Human Intervention Policy

### AUTO

- concept, hook, shot ordering, edit plan, captions, cover direction.
- media classification / archive / search.
- quality repair and re-review.
- feed balancing and slot choice within the locked calendar.
- tool failover that does not change business terms.

### AUTO_WITH_GUARDRAILS

- routine Instagram publish when instance `creativeAutonomy.publish.standingAuthorization=true`, all gates pass, rights are known, and a real publish tool exists.
- factual claims only when backed by floor proof/source.
- customer-visible assets only when customer/media rights are explicitly clear.

### HUMAN_REQUIRED

- missing physical footage / reshoot / product staging that the office cannot create truthfully.
- unclear customer permission, private CAD/customer identity, or rights uncertainty.
- price, spend, boost/ads, purchase, irreversible destructive action.
- customer WhatsApp send / commercial commitment.
- Print from HQ.
- hard blocker after documented failover.

## Don't Bother Christian

Low quality is not a human gate. A failed hook, cover, caption, crop or edit is an internal repair loop. Escalate only a `HUMAN_REQUIRED` condition. When asking for footage, ask for the smallest concrete shot package possible.

## Standing authorization

An instance may opt in once through its profile. Opt-in removes per-asset creative approval, not constitutional locks. It never authorizes auto-DM, boost, invented ₪/Insights, customer WhatsApp send, Print from HQ, or publication without rights/tool receipt.

## Done

A content job is done only when one of these is true:

- `published_verified` — real tool receipt + live verification/evidence.
- `ready_for_publish` — gates passed but no publish tool; honest failover packet exists.
- `waiting_for_media` — exact physical shotRequest exists.
- `human_required` — named non-creative gate with evidence.

Never end as “waiting for owner approval” merely because a normal creative choice exists.
