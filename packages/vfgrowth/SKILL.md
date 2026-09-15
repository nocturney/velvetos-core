# vfgrowth — תוכן מעבודה גמורה

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

מושב: צמיחה. זה סוכן התוכן מהשיתוף.

כל עבודה על המיטה יכולה להיות חומר. הפק מוציא חבילת טיוטה.  
`#vfcovers` כריכה. `#vfigos` סקירה/שיבוץ. מסגרות אופציונליות: `vfmskill` (`social` / `video`). אין בוסט, אין צפיית־סטורי כטריק.

**לוח עומד:** `CALENDAR.md` + `RHYTHM.md` — לא שואלים כל יום «מה לפרסם?».  
חסר גלם מכריסטיאן → `MEDIA-NEEDED-FROM-CHRISTIAN`. לא ממציאים מדיה.

לוח **קבוע**: `CALENDAR.md` + `LEDGER.md` + `HANDOFF-he.md`. שיבוץ ב־instagram.com (לא סוויט).  
שער עריכה: `EDIT-GATE.md`. פריפלייט כתוב: `PREFLIGHT.md` (VOICE + ציון עצמי + 2–3 קומפס) — בלי `preflight/<id>.md` עבור = נכשל-סגור.  
אל תפנה לכריסטיאן על מדדים חלשים. לוח אוטונומי: `CALENDAR-OPS.md`. סנסור `scripts/check-vfgrowth.py`.

צמיחת עוקבים → פנייה (לא מרדף מספר): `hq/FOLLOWER-GROWTH.md`.  
משפך פרופיל→הודעת Instagram: `hq/PROFILE-TO-WHATSAPP.md` (שם היסטורי; תוכן = PUBLIC_CURRENT_CTA). תהליך-קצר = עקבו; סיפור-מוצר = הודעה.  
לולאת בוקר: `python3 scripts/vfops_loop.py brief` · מסירה: `HANDOFF-he.md` (G004).

## מומחה — Social Booster

מודול: `expert-social-booster` · `experts/SOCIAL-BOOSTER.md` · `@carousel-growth-engine`

## מומחה — Revenue Loop

מודול: `expert-revenue-loop` · `experts/REVENUE-LOOP.md` · `@offer-lead-gen-strategist` · skill `vf-revenue-loop`

## מפעל צמיחה אורגני

חוקה: `constitution/ORGANIC_GROWTH.md` · פלייבוק: `ORGANIC-GROWTH.md` · CLI: `python3 scripts/vf_organic_growth.py brief --write`  
לא מפרסם. לא אוטו־DM. תור 07:00 = [אישור][עריכה][דחייה].

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

> LEGACY / provenance only for VF publication; not a provider route: This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

