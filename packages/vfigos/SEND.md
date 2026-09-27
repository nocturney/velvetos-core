# שליחת אינסטגרם מ־HQ

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.  
MCP קנוני: [`CONNECT-IG.md`](CONNECT-IG.md) (`adelaidasofia/instagram-mcp`).  
Scheduled publishing control-plane: [`PUBLISHER.json`](PUBLISHER.json) + [`cloudflare-publisher/README.md`](cloudflare-publisher/README.md). OpenPost is [`legacy-read-only`](OPENPOST.md) and must not receive new VF schedules.
Scheduled media transport: Cloudflare Publisher KV, exact SHA-bound and write-once. [`PUBLISH-BRIDGE.md`](PUBLISH-BRIDGE.md) remains available for immediate/legacy transport where a public HTTPS derivative is needed.
Authorization boundary: future schedules require an exact immutable `owner_schedule_authorization` at enqueue; immediate direct `publish_*` writes retain the short-lived signed `velvet.delivery_approval.v1` boundary in [`approval/OPERATOR-SETUP.md`](approval/OPERATOR-SETUP.md).

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / «הזמנות» / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא «שלחו DM». לא וואטסאפ בכיתוב. מקסימום 5 האשטגים. לא אוטו־DM. לא ₪ מומצא.
> LEGACY / provenance only for VF publication; not a provider route: 2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva או `studio/render.py` חוזרת למסלול נגזרת→אישור.
3. **QA final render + PREFLIGHT v2** — לפני transport/publish, בודקים את הייצוא הסופי עצמו. לסטורי: Brand Guardian + copy QA + readability + contrast = `PASS`; Rubric ≥20/25; `artifact_digest`; ו־`final_package_sha256` של חבילת הפריימים המדויקת. אין waiver ל״ניגודיות רכה״. שינוי ויזואל/קופי אחרי אישור מבטל את האישור.
4. **Transport של המדיה** — schedule עתידי מעלה **רק את הנגזרת המדויקת שאושרה** ל־Cloudflare Publisher KV דרך endpoint מוגן, עם SHA-256 צפוי. ה־KV הוא write-once/idempotent: אותו key+hash מותר שוב; collision עם bytes אחרים נחסם. לפני יצירת job ולפני publish ה־Worker קורא את bytes מחדש ומאמת hash. למסלול immediate/legacy בלבד, `PUBLISH-BRIDGE.md` נשאר transport אפשרי. אסור להפוך את המקור ב־Drive לציבורי. upload/staged ≠ scheduled ≠ published.
5. **פריפלייט שליחה** — בדיקת transport בלבד מותרת לאבחון:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram --transport-only
   ```
   אבל היא **לעולם אינה הרשאת publish**. לפני כל schedule חדש או `publish_*` ישיר חובה:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram \
     --content-id <GID> --format <story|reel|carousel|post> \
     --approval-ref packages/vfgrowth/preflight/<GID>.md \
     --package-sha256 <SHA256-OF-EXACT-FINAL-PACKAGE>
   ```
   exit `0` + `publication_quality.publishAuthorized=true` מוכיחים publication/preflight eligibility בלבד. exit `1/2` = **לא מפרסמים**; מתקנים איכות או מבצעים failover transport לפי הסיבה.
   עבור תוצר שנוצר ב־VF Project Revision `6.6.9`, PREFLIGHT schema `4` רשאי לצרוך ישירות את `.vf-run.json` + `release.json` + reviews + transport-QA + caption receipt דרך `scripts/vf_project669_publication.py`. אסור לתרגם את הריצה בדיעבד לראיות legacy מומצאות. ה־runner נשאר `publication_authorized=false`; רק owner approval + שער השליחה נותנים publication eligibility.
6. **Authorization לפני delivery** — יש שני מסלולים נפרדים ואסור לערבב ביניהם. **Schedule עתידי:** יצירת ה־job היא אירוע ההרשאה; נדרש `owner_schedule_authorization` שמקושר במדויק ל־`content_id`, package SHA-256, `scheduled_at`, caption ורשימת media/hash מסודרת. לאחר enqueue ה־job HMAC-bound ואינו ניתן לעריכה; שינוי דורש cancel + authorization חדש. **Publish מיידי:** `velvet.delivery_approval.v1` חתום ותקף מה־dedicated issuer נשאר חובה. PREFLIGHT או transport readiness לבדם אינם authorization.
7. **בחירת נתיב apply** — office logic קורא את `PUBLISHER.json` בזמן אמת:
   - **עתידי/גאנט:** אם Cloudflare Publisher health, cron heartbeat ו־Meta health תקינים, המדיה exact-hash verified, והבעלים אישר את אותו package/time/caption/media — יוצרים job מתוזמן. D1 הוא מקור ה־queue; KV הוא transport. אין OpenPost schedule חדש.
   - **מיידי:** direct Instagram MCP: תמונה `publish_image`; קרוסלה `publish_carousel`; ריל/וידאו `publish_reel`/`publish_video`; סטורי `publish_story`, ורק עם `velvet.delivery_approval.v1` תקף.
   - **שינוי ל־schedule קיים:** אין PATCH סמנטי. מבטלים job שעדיין `scheduled/retry`, מאמתים שהביטול נקלט, ואז יוצרים job חדש עם authorization חדש.
8. **אימות אחרי שליחה נשאר עצמאי** — `list_media` / `get_media` מה־Instagram MCP הקנוני מאשרים שהמדיה חיה. רק אז `#נשלח-מ-HQ` ו־`liveVerified`. success מה־Publisher או `publish_*` בלי אימות חי → `publish_pending_verification`.
8a. **Media Vault closeout** — רק אחרי `liveVerified`, מזיזים ב־Drive את **הנגזרת המדויקת שפורסמה** מ־`04 - מאושר לפרסום` ל־`05 - פורסם` (Folder ID `19A-_QOSvII-CvxjRMpQ2j5Z46UAjeNep`). באותה פעולה לוגית מעדכנים את שורת `packages/vfmedia/catalog.json`: `status=published` + `publication.state=published_verified` + provider/mediaId/permalink/publishedAt/verifiedAt + `publishedDerivative`. אם ה־live match חסר/שגוי, לא מזיזים את הקובץ מ־04. המקור נשאר ב־02.
9. **Recovery / failover** — ה־Publisher מבצע retry אוטומטי **רק לפני** `media_publish`. כשל חד־משמעי לפני גבול הפרסום רשאי להגיע ל־`retry`/`dead_letter`; אפשר ליצור job חדש רק אחרי בדיקת duplicate + authorization חדש. `reconcile_required`, lease שפג בזמן `publishing`, timeout/תגובה עמומה אחרי `media_publish` או outcome לא ידוע = **אין retry אוטומטי ואין direct failover**; קודם `list_media/get_media` reconciliation. פרסום מיידי דרך Instagram MCP אחרי כשל schedule דורש `velvet.delivery_approval.v1` חדש ומדויק. חבילת `packages/vfigos/failover/` הישנה היא OpenPost legacy ואינה חמושה ל־Publisher schedules.
10. אסור לכתוב שעלה לפיד אם לא עלה. Calendar mirror / KV upload / `scheduled` / delivery accepted / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

## OpenPost — legacy בלבד

OpenPost נשאר מותקן לצורכי provenance/recovery inspection של היסטוריה עד cutover 2026-09-24. הוא אינו scheduler, queue, retry plane או apply route לפרסומים חדשים. אין להפעיל את חבילת failover הישנה עבור jobs של Cloudflare Publisher.

## חוזה איכות → הרשאה → פרסום

`transport-ready` ≠ `creative-approved` ≠ `publication-authorized` ≠ `delivery-authorized` ≠ `published_verified`.

האישור חייב להתייחס **לאותו hash** שמגיע ל־Cloudflare Publisher KV / Instagram. אסור למחזר PREFLIGHT ישן אחרי שינוי תוצר או אחרי שינוי במדיניות האיכות. PREFLIGHT חדש חייב להיות schema `3` במסלול legacy publicationEvidence או schema `4` במסלול VF Project 6.6.9 הישיר. גם PREFLIGHT תקף אינו הרשאת write בלי receipt חתום `velvet.delivery_approval.v1` שעובר את ה־mutation boundary.

## Publish Bridge — כללי בטיחות

- source of truth למדיה נשאר Drive/Media Vault; ה־bridge הוא transport בלבד ואינו קטלוג שני.
- `approved_for_public_release` הוא שער קשיח. upload או folder placement לא מספיקים.
- correlation בנתיב חייב להיות non-PII; לא שם לקוח.
> LEGACY / provenance only for VF publication; not a provider route: - metadata ציבורי שומר hash של source reference, לא URL פרטי של Drive/Canva.
- archive יומי מעביר נכסים שיצאו מחלון ה־active מ־`publish-bridge/assets` אל `publish-bridge/archive`; `archiveRetention=unlimited` ו־`deleteArchived=false`. אין מחיקה אוטומטית ואין overwrite על collision.
- לכן בענף מותרת רק נגזרת שממילא מותר לפרסם לציבור.

## דפוס validate → transport → authorize → apply → verify

| שלב | כאן |
|---|---|
| validate | PREFLIGHT v2 + publicationEvidence + exact final-package hash + Brand/Copy/Readability/Contrast + rights/privacy |
| transport | schedule: Cloudflare KV exact-hash; immediate/legacy: public HTTPS derivative as required |
| authorize | schedule: `owner_schedule_authorization` exact-bound; immediate: signed `velvet.delivery_approval.v1` |
| apply | schedule: Cloudflare Publisher D1/Worker; immediate: `publish_*` direct MCP |
| verify | `list_media` / `get_media` מה־MCP הקנוני · לא «פורסם» בלי ראיה · אחרי live match סוגרים 04→05 + catalog publication evidence |

## אסור

- לפרסם על בסיס `--transport-only`
- למחזר approval ישן שלא קשור ל־final package המדויק
- לבצע Instagram write בלי `velvet.delivery_approval.v1` חתום ותקף
- להשתמש ב־direct Instagram MCP כדי לעקוף delivery approval
- waiver לניגודיות/קריאות חלשות
- להחזיר OpenPost למסלול schedule/apply בלי החלטת ארכיטקטורה חדשה ומפורשת
- להפעיל OpenPost legacy failover על Publisher job
- סרק / «תעלה ידנית» כברירת מחדל
- להפוך מקור/תיקיית Drive לציבוריים כדי לפתור transport
- לשים publish binaries על `main`
- להכניס ל־`publish-bridge` חומר שלא עבר `approved_for_public_release`
- להמציא Insights אחרי «שליחה»
- לטעון live מ־Publisher או publish tool בלי verify
- Treg · אוטו־DM · `INSTAGRAM_MCP_DM_ENABLED`

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVL7PKpvE` and SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.
