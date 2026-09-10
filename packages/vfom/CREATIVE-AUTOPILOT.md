# Creative Autopilot — Velvet Factory

מושב: צמיחה + Office Control Plane. זהו overlay על המערכת הקיימת; **לא** orchestrator שני, לא pack חדש ולא runtime חדש.

## מטרה

להפוך `print.done` / מוצר חדש / חומר מעניין / כשל שימושי / media intake להזדמנות תוכן שמתקדמת אוטונומית עד תוצר ופרסום דרך כלי מחובר, בלי לבקש מהבעלים החלטות יצירתיות שגרתיות.

הבעלים נדרש רק כשאין דרך אמיתית להשלים את העולם הפיזי או כשקיים שער עסקי/משפטי אמיתי.

ה־control contract המכני של ה־Foundry נמצא ב־`FOUNDRY.json`. חוזה תוכן לכל job נבנה לפי `CONTENT-CONTRACT.schema.json`. שניהם מרחיבים את המערכת הקיימת ואינם יוצרים SoT או runtime מקביל.

## Pipeline — Reference → Generate → Critique → Repair → Rank → Learn

```text
real event / opportunity
  -> discovered
  -> opportunity triage + novelty/fatigue check
  -> qualified | archived
  -> Asset Truth lookup + Claim Provenance
  -> Content Contract
  -> contracted
  -> Creative Director / proof-first concepts
  -> concepted
  -> cheap storyboard candidates
  -> storyboarded
  -> shot-gap check
  -> media ready?
       no  -> waiting_for_media + minimal shotRequest -> HUMAN_REQUIRED only for physical gap
       yes -> media_ready
  -> progressive variants: storyboard -> rough cuts -> max 2 final renders
  -> rough_generated
  -> Evaluation Engine: deterministic + perceptual + reference + artifact checks
  -> visually_scored
  -> failed quality? -> targeted AUTO_FIX -> QA again (bounded repair loop)
  -> repaired
  -> render master + derivatives
  -> rendered
  -> authorization / Exception Queue
  -> authorized_for_tool_publish | human_required | ready_for_publish
  -> connected Instagram publish tool
  -> published_verified only with receipt + live evidence
  -> performance ingest when evidence exists
  -> performance_learned
```

## Content Contract — חובה לפני storyboard/render

לכל job קבע חוזה שמגדיר לפחות:

- `objective` + `format` + target duration כשיש וידאו.
- `truthClaims`: כל טענה עובדתית וה־evidence שמוכיח אותה.
- `requiredSubject` + Subject Pack כאשר זהות/גאומטריית מוצר קריטית.
- `syntheticPolicy`: למה AI מותר לשמש ומה אסור להציג באמצעותה.
- `successDefinition`: ספי Brand / Reality / Artifact.
- novelty decision מול תכנים דומים כשיש history.

`Asset Truth` אומר מה מקור הנכס; `Claim Provenance` אומר מה מותר לטעון באמצעותו. גם `verified_real` אינו הוכחה אוטומטית לכל claim. טענה על עומס, מדידה, כשל, הצלחה או תוצאה חייבת evidence מתאים.

ברירת אמת: נכס Media Vault בלי `truth` = `unverified` לצורכי טענה ציבורית. `illustrative_ai`/`synthetic` רשאים לשמש אווירה, רקע, transition או support; אינם proof לתוצאה פיזית.

## Creative Director

אחד את `Visual Director` + `First-Frame Hunter` + `Shot Gap Detector` + Proof-First Storyboarder לתפקיד אחד. הפלט חייב לכלול:

- concept + objective + audience.
- visual emotion / proof story.
- 3–5 first-frame candidates + בחירה מנומקת אחת.
- shot list מדויק: type, angle, distance, orientation, duration, action, proof.
- background + lighting direction.
- on-film text hierarchy.
- cover direction.
- missing shots only when באמת חסר חומר פיזי.

אין להסלים לבעלים “איזה Hook אתה מעדיף?” או “איזה cover אתה אוהב?”. לבחור לבד לפי `VISUAL-OS.md`, חוזה התוכן והוכחת רצפה.

## Asset Library + Subject Lock

Media Vault הוא מקור הנכסים הקנוני. סיווג תוכן משתמש ב־`hero|macro|process|failure|proof|human|b-roll`, orientation, quality, rights/approval, project/job/SKU/material וב־`truth` האופציונלי מהסכמה. אין קטלוג מדיה מקביל.

כאשר המוצר חייב להישאר זהה בין שוטים, בנה Subject Pack בתוך Content Contract:

- reference asset ids אמיתיים מכל זווית זמינה.
- geometry / material / color invariants.
- `mustNotChange` מפורש.
- אין להמציא view חסר כאילו הוא אמת; generation שאינו שומר fidelity נכשל ב־reference check.

## Progressive Multi-Variant Director

אל תרנדר 12 סרטונים מלאים כדי לבחור אחד. עבוד ב־progressive commitment מתוך `FOUNDRY.json`:

```text
עד 12 concepts
-> עד 6 storyboard/mock previews
-> score
-> עד 4 rough cuts
-> score
-> עד 2 final renders
-> targeted repair
-> winner + alternate
```

הווריאציות חייבות לבדוק מכניקה יצירתית אמיתית: first frame, proof mechanic, story structure, length, pacing, overlay density, audio, cover. שינוי צבע בלבד אינו variant משמעותי.

## Evaluation Engine — לא שבעה agents נפרדים

הרץ pass מובנה אחד עם rubrics, ובצמוד אליו בדיקות דטרמיניסטיות:

- deterministic: aspect ratio, resolution, safe zones, subtitle bounds, frame integrity, audio loudness.
- perceptual: Brand, Hook, composition/cinematic quality, Reality, Originality.
- reference: subject/material/geometry fidelity.
- artifacts: flicker, malformed geometry, unreadable text, temporal jitter.

ה־evaluator מחזיר score + evidence + repair action אחת ברורה לכל failure. Reality/Artifact הם שערים קריטיים לפי `FOUNDRY.json`; Visual OS `brandScore >=80` ו־`CONTENT-RUBRIC >=20/25` נשארים gate קיים.

## Artifact Repair Router

כשל איכות רגיל הוא עבודה פנימית. נתח ואבחן את סוג הכשל ורק אז תקן:

- עברית משובשת בתוך AI video -> הסר text מהוידאו ובנה overlay deterministic (SVG/HTML/FFmpeg/Canva path קיים).
- malformed hands/object -> החלף shot או חזור ל־real footage; אל תסתיר proof פגום.
- flicker/jitter -> regenerate segment / camera lock / replace segment.
- subject drift -> tighten Subject Pack/reference lock או השתמש בנכס אמיתי.
- color mismatch -> existing Velvet grade/template; אל תמציא palette.
- weak first frame -> החלף ב־proof shot מדורג גבוה יותר.
- generic/stock feel -> הוסף floor footage, studio audio או product detail אמיתי.

ה־repair loop bounded לפי `maxRepairCycles`; אחרי חסם קשיח מתועד בלבד -> `human_required`.

## Novelty / Fatigue Memory

לפני concept סופי, בדוק history קיים דרך office-learning/vfinsights — אין creative-memory DB חדש. השווה לפחות:

- אותו מוצר.
- אותו first-frame mechanic.
- אותה הוכחה.
- אותו story structure.
- אותה זווית/visual reference mechanic.

`FOUNDRY.json` מגדיר review/reject similarity ו־cooldown. similarity גבוה דורש שינוי מכניקה, cooldown או series override מנומק. המטרה: ללמוד מהצלחה בלי לשכפל את אותו Reel.

למידה אחרי פרסום שומרת recipe רק לצד performance evidence אמיתי. לא מפיקים style recommendation לפני מינימום המדגם הקיים של `vfinsights`. exploration policy שומרת מקום ל־controlled variation ו־experimental work במקום exploit בלבד.

## Budget Governor

ה־Foundry אינו רשאי להמציא כסף או לפתוח spend. הוא כן מנהל תקציב חישובי/יצירתי איכותי:

- real approved footage קודם ל־generation.
- reuse approved asset לפני generation חדש.
- concept חלש נעצר לפני render יקר.
- preview זול לפני full-quality render.
- provider/spend בתשלום נשאר human gate לפי instance/constitution.

## Edit Director

`EDIT-DIRECTOR.md` מייצר EDL אופרטיבי: asset refs אמיתיים, in/out, crop, speed, cut, overlay, audio. אם חסר shot קריטי — בקשה מינימלית אחת במקום שאלה יצירתית.

## Render & Derivative Factory

אחרי master שעבר QA, הפק דרך השירותים/כלים הקיימים בלבד את הנגזרות הרלוונטיות: 9:16 master, Reel cover, feed crop, Story cuts, carousel proof sequence, hero still, silent-safe/כתוביות. שמור נגזרות חזרה תחת Media Vault `derivativeIds`; אין render database שני.

## Publishing Director / Exception Queue

אחד `Cover Art Director` + `Feed Architect` + Brand QA:

1. ליצור 3 cover directions ולבחור אחד.
2. לבדוק Visual OS + CONTENT-RUBRIC + Content Contract + policy + rights.
3. לתקן אוטונומית כשאפשר.
4. לבחור slot מתוך `vfgrowth/CALENDAR.md`; לא להמציא cadence חדש.
5. לסווג סיכון:
   - **LOW**: proof/rights ידועים, פורמט שגרתי, scores מעל הסף -> standing authorization יכול לשלוח אוטונומית.
   - **MEDIUM**: כיוון חריג/סינתטי משמעותי/score גבולי -> existing human approval path אם policy דורש.
   - **HIGH**: customer identity/private CAD, unsupported claim, price/spend, rights ambiguity, safety/commercial claim חריג -> `human_required`.
6. לפרסם דרך כלי Instagram מחובר רק אם ה־instance מאפשר standing authorization וכל שערי ה־preflight עברו.
7. אין receipt אמיתי / live verification -> לא לטעון שפורסם; להיכנס ל־Degraded/failover לפי `constitution/SEND.md`.

## Human Intervention Policy

### AUTO

- concept, hook, shot ordering, edit plan, captions, cover direction.
- media classification / archive / search.
- progressive variant ranking.
- deterministic/perceptual QA and targeted repair.
- feed balancing and slot choice within the locked calendar.
- tool failover that does not change business terms.

### AUTO_WITH_GUARDRAILS

- routine Instagram publish when instance `creativeAutonomy.publish.standingAuthorization=true`, all gates pass, rights are known, claims are supported, and a real publish tool exists.
- factual claims only when backed by floor proof/source and Content Contract evidence.
- customer-visible assets only when customer/media rights are explicitly clear.

### HUMAN_REQUIRED

- missing physical footage / reshoot / product staging that the office cannot create truthfully.
- unclear customer permission, private CAD/customer identity, or rights uncertainty.
- unsupported high-stakes factual claim that cannot be repaired by removal/reframe.
- price, spend, boost/ads, purchase, irreversible destructive action.
- customer WhatsApp send / commercial commitment.
- Print from HQ.
- hard blocker after documented failover/repair limit.

## Don't Bother Christian

Low quality is not a human gate. A failed hook, cover, caption, crop, edit, reference fidelity or ordinary artifact is an internal repair loop. Escalate only a `HUMAN_REQUIRED` condition. When asking for footage, ask for the smallest concrete shot package possible.

## Standing authorization

An instance may opt in once through its profile. Opt-in removes per-asset creative approval for LOW routine content, not constitutional locks. It never authorizes auto-DM, boost, invented ₪/Insights, unsupported claims, customer WhatsApp send, Print from HQ, or publication without rights/tool receipt.

## Done

A content job is done only when one of these is true:

- `published_verified` — real tool receipt + live verification/evidence.
- `performance_learned` — published item has later evidence and recipe learning was recorded.
- `ready_for_publish` — gates passed but no publish tool; honest failover packet exists.
- `waiting_for_media` — exact physical shotRequest exists.
- `human_required` — named non-creative gate with evidence.
- `archived` — opportunity intentionally rejected by qualification/novelty/budget logic with reason.

Never end as “waiting for owner approval” merely because a normal creative choice exists.
