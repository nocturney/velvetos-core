# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.  
MCP קנוני: [`CONNECT-IG.md`](CONNECT-IG.md) (`adelaidasofia/instagram-mcp`).  
Publishing control-plane: [`OPENPOST.md`](OPENPOST.md) + [`OPENPOST.json`](OPENPOST.json) — כרגע `shadow_pending_runtime_deploy`; אינו עוקף את ה־MCP הקנוני או את שערי האיכות.  
Transport קנוני למדיה פרטית: [`PUBLISH-BRIDGE.md`](PUBLISH-BRIDGE.md) + [`PUBLISH-BRIDGE.json`](PUBLISH-BRIDGE.json).

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / «הזמנות» / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא «שלחו DM». לא וואטסאפ בכיתוב. מקסימום 5 האשטגים. לא אוטו־DM. לא ₪ מומצא.
2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva או `studio/render.py` חוזרת למסלול נגזרת→אישור.
3. **QA final render + PREFLIGHT v2** — לפני transport/publish, בודקים את הייצוא הסופי עצמו. לסטורי: Brand Guardian + copy QA + readability + contrast = `PASS`; Rubric ≥20/25; `artifact_digest`; ו־`final_package_sha256` של חבילת הפריימים המדויקת. אין waiver ל״ניגודיות רכה״. שינוי ויזואל/קופי אחרי אישור מבטל את האישור.
4. **Publish Bridge** — כאשר הנגזרת אינה כבר ב־HTTPS ציבורי מתאים, מעבירים **רק את הנגזרת שאושרה לפרסום** דרך `PUBLISH-BRIDGE.md`: normalize → strip metadata → content hash → stage בענף `publish-bridge` → external fetch verify. אסור לשנות שיתוף של המקור ב־Drive. `staged`/`fetch_verified` ≠ published.
5. **פריפלייט שליחה** — בדיקת transport בלבד מותרת לאבחון:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram --transport-only
   ```
   אבל היא **לעולם אינה הרשאת publish**. לפני כל apply — בין אם OpenPost ובין אם `publish_*` ישיר — חובה:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram \
     --content-id <GID> --format <story|reel|carousel|post> \
     --approval-ref packages/vfgrowth/preflight/<GID>.md \
     --package-sha256 <SHA256-OF-EXACT-FINAL-PACKAGE>
   ```
   רק exit `0` + `publication_quality.publishAuthorized=true` מאפשרים מעבר ל־apply. exit `1/2` = **לא מפרסמים**; מתקנים איכות או מבצעים failover transport לפי הסיבה.
6. **בחירת נתיב apply** — office logic נשאר capability-based:
   - אם `OPENPOST.json.integrationMode` הוא `staging` או `primary-control-plane`, ה־runtime מאומת ובריא, וה־artifact הוא אותו hash שאושר — מותר להעביר ל־OpenPost לצורך queue/schedule/publish. תשובת OpenPost מסמנת לכל היותר `publishRequested`/delivery status, לא `liveVerified`.
   - אם OpenPost במצב `shadow_pending_runtime_deploy`, `shadow`, `degraded`, לא מאומת או נכשל — מפרסמים ישירות דרך Instagram MCP: תמונה `publish_image`; קרוסלה `publish_carousel`; ריל/וידאו `publish_reel`/`publish_video`; סטורי `publish_story`.
7. **אימות אחרי שליחה נשאר עצמאי** — `list_media` / `get_media` מה־Instagram MCP הקנוני מאשרים שהמדיה חיה. רק אז `#נשלח-מ-HQ` ו־`liveVerified`. success מ־OpenPost או `publish_*` בלי אימות חי → `publish_pending_verification`.
8. **Failover** — כשל OpenPost מחזיר ל־Instagram MCP באותו תור. אם גם Publish MCP אינו חי → Drive `create_file` + Gmail עם אותה חבילה; `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה. אין idle.
9. אסור לכתוב שעלה לפיד אם לא עלה. Calendar / upload / bridge staging / OpenPost scheduled / delivery accepted / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

## OpenPost — גבולות סמכות

OpenPost הוא שכבת publication operations בלבד: scheduler, queue, retry/delivery status, multi-channel control ו־analytics collection. כלי AI writing/image/video שלו אינם מקור סמכות ל־creative approved ואינם רשאים לעקוף את `vfcopy`, Media Vault, Brand Guardian, PREFLIGHT, rights/privacy או exact-hash binding. מדיניות גרסאות ו־upgrade: `OPENPOST.md`/`OPENPOST.json` — production נעוץ לגרסה מדויקת, לא `latest`.

## חוזה איכות → פרסום

`transport-ready` ≠ `creative-approved` ≠ `published_verified`.

האישור חייב להתייחס **לאותו hash** שמגיע ל־Publish Bridge/OpenPost/Instagram. אסור למחזר PREFLIGHT ישן אחרי שינוי תוצר או אחרי שינוי במדיניות האיכות. PREFLIGHT ללא `publish_gate_schema: 2` אינו מקור הרשאה לפרסום חדש.

## Publish Bridge — כללי בטיחות

- source of truth למדיה נשאר Drive/Media Vault; ה־bridge הוא transport בלבד ואינו קטלוג שני.
- `approved_for_public_release` הוא שער קשיח. upload או folder placement לא מספיקים.
- correlation בנתיב חייב להיות non-PII; לא שם לקוח.
- metadata ציבורי שומר hash של source reference, לא URL פרטי של Drive/Canva.
- cleanup יומי מסיר נכסים ישנים מראש הענף אחרי חלון retention; הוא **לא** secure erase מהיסטוריית Git.
- לכן בענף מותרת רק נגזרת שממילא מותר לפרסם לציבור.

## דפוס validate → transport → apply → verify

| שלב | כאן |
|---|---|
| validate | PREFLIGHT v2 + exact final-package hash + Brand/Copy/Readability/Contrast + rights/privacy |
| transport | Publish Bridge רק לנגזרת המאושרת; HTTPS fetch verified |
| apply | OpenPost כשהוא מאומת ומורשה **או** `publish_*` ישיר; כשל OpenPost → direct MCP |
| verify | `list_media` / `get_media` מה־MCP הקנוני · לא «פורסם» בלי ראיה |

## אסור

- לפרסם על בסיס `--transport-only`
- למחזר approval ישן שלא קשור ל־final package המדויק
- waiver לניגודיות/קריאות חלשות
- לתת ל־OpenPost AI/editor להפוך תוכן ל־approved בלי ה־pipeline הקנוני
- להריץ production על image/tag `latest` של OpenPost
- סרק / «תעלה ידנית» כברירת מחדל
- להפוך מקור/תיקיית Drive לציבוריים כדי לפתור transport
- לשים publish binaries על `main`
- להכניס ל־`publish-bridge` חומר שלא עבר `approved_for_public_release`
- להמציא Insights אחרי «שליחה»
- לטעון live מ־OpenPost או publish tool בלי verify
- Treg · אוטו־DM · `INSTAGRAM_MCP_DM_ENABLED`

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVL7PKpvE` and SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

