# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
Runtime baseline: **v4.35.0**
Latest reviewed upstream: **v4.35.0** (2026-09-17)
Upstream head observed (watch only): **v5.2.2** (2026-09-21) — pin **UNCHANGED**
Role: **scheduler + queue + retry/delivery status + multi-channel publication control + analytics collector**.

## החלטת ארכיטקטורה

OpenPost נכנס **בתוך `vfigos` הקיים** כשכבת publication operations/control-plane בלבד.

```text
Content decision / creative pipeline
  -> Media Vault + exact versionApproval
  -> packages/vfom/PUBLICATION-PREP-EXECUTION.md
  -> Product Truth + Owner-Approved Grid Standard
  -> VISIBLE_TEXT + Brand Guardian + executable creative preflight
  -> PREFLIGHT/publicationEvidence + exact artifact/package hash
  -> signed velvet.delivery_approval.v1 for the exact write mutation
  -> OpenPost queue/schedule/apply OR direct Instagram MCP failover
  -> Instagram MCP list_media/get_media live verification
  -> liveVerified + ledger
  -> Insights / learning loop
```

OpenPost רשאי לקבל רק artifact שעבר את מסלול הפרסום הקנוני וקיבל את הראיות הנדרשות. הוא **לא** יוצר bypass ל־VISIBLE_TEXT, `packages/vfom/PUBLICATION-PREP-EXECUTION.md`, Product Truth, Media Vault/versionApproval, Owner-Approved Grid Standard, Brand Guardian, PREFLIGHT/publicationEvidence, rights/privacy, exact-hash binding או signed `velvet.delivery_approval.v1`.

## Instagram / Meta

- חשבון יעד: `@velvets_cloud`.
- Direct/canonical Instagram MCP נשאר `adelaidasofia/instagram-mcp` לקריאה, live verification ו־same-turn failover.
- OpenPost מיועד ל־orchestration של publication; הוא לא מקור האמת ל־Instagram capabilities ולא ראיית live.
- OpenPost upload/schedule/publish success לעולם אינו `liveVerified`; רק `list_media` / `get_media` מה־Instagram MCP הקנוני הם ראיית live.
- אין auto-DM, אין boost/Ads, אין שינוי מחיר/Spend ואין המצאת Insights/metrics.

## Authenticated write boundary

כל Instagram write mutation — גם דרך OpenPost וגם דרך direct Instagram MCP — חייבת לעבור את אותו mutation boundary עם receipt חתום מסוג `velvet.delivery_approval.v1` מה־dedicated issuer.

- `packages/vfigos/approval/OPERATOR-SETUP.md` הוא מסמך ההקמה/סטטוס הקנוני.
- כל עוד live evidence נשאר `NEEDS_OPERATOR_SETUP`, אין production promotion ואין write authorization.
- Publication evidence, standing authorization או transport success אינם תחליף ל־delivery approval חתום.
- Direct Instagram MCP הוא failover תעבורתי בלבד; הוא **לא** approval bypass.

## מצבי הפעלה

1. `shadow` — OpenPost מקבל/מאמת payloads ותזמון בלי להחליף את הנתיב הקנוני.
2. `staging` — בדיקות מבוקרות: health/auth, queue/schedule, post/carousel/reel/story contract, forced failure/retry, analytics ingest ומיגרציות על staging בלבד.
3. `primary-control-plane` — רק אחרי שכל הבדיקות, provider OAuth/public HTTPS, signed delivery approval וה־Instagram live verification עוברים.
4. `degraded` — כשל OpenPost מחזיר מיד ל־direct Instagram MCP; אותה הרשאת delivery חתומה עדיין חובה לכל write.

## Release / upgrade policy

לא משתמשים ב־`latest` ב־production. גרסה או digest ננעצים במפורש ומתקדמים רק לאחר review.

לכל release חדש:

1. לקרוא release notes + changelog + breaking/migration notes.
2. לסווג השפעה על Meta/Instagram auth, API/MCP, media limits, scheduler/queue/retry, analytics, database/schema/storage ו־security/privacy.
3. לעדכן `latestReviewedVersion` רק עם ראיית upstream אמיתית.
4. אם יש migration/schema change — לבצע backup אמיתי לפני upgrade ולבצע staging migration smoke.
5. staging מקבל גרסה מדויקת / immutable digest, לא `latest`.
6. לפני v4.32+ חובה להציב במפורש `OPENPOST_DIAGNOSTICS_ENABLED=false` כל עוד אין אישור מפורש לשיתוף maintainer diagnostics חיצוני.
7. smoke: health/auth + queue/schedule + post/carousel/reel/story contract + retry + analytics read; publish smoke דורש גם provider prerequisites וגם signed delivery approval.
8. Instagram live verification נשאר `list_media` / `get_media`.
9. רק אם אין regression וכל gates הדרושים PASS — ניתן לשקול production pin.

## Review v4.34.2 -> v4.35.0

- **Meta/Instagram auth:** no Instagram/Facebook/OAuth provider code changed; the same Meta app, callback and public-media prerequisites remain.
- **API/MCP:** no VF-relevant contract change identified.
- **Media limits:** no Instagram media-limit change identified.
- **Scheduler/queue/retry:** no VF publication scheduler/queue/retry change identified.
- **Analytics:** PieFed analytics fixes only; no Instagram analytics contract change identified.
- **Database/schema/storage:** no new migrations; isolated smoke and promoted staging remain on schema `136` with `integrity_check=ok` and zero foreign-key violations.
- **Security/privacy:** no VF provider-security boundary change identified. The current runtime explicitly sets `OPENPOST_DIAGNOSTICS_ENABLED=false`; the pre-upgrade backup also captured `false`, but that snapshot is not treated as proof of uninterrupted historical enforcement.
- **Pinned artifact reviewed:** Windows server v4.35.0 SHA-256 `be6520f495def72b1b466a69c9a223954b4403c3c7c40881b52ce0f030334cc8`.
- **Production-host artifact:** Linux server v4.35.0 SHA-256 `157abefc2810dde09e914b78915f79c0160fcf60047856a30a1261c1721d2856`.

## Current runtime decision

OpenPost is now the production publication control-plane on the dedicated GCP host at `https://openpost.34.9.7.22.sslip.io`. The host remains pinned to upstream **v4.35.0** plus the reproducible Velvet overlay `vfbridge6`; both `openpost` and `openpost-worker` run `/opt/openpost/v4.35.0-vfbridge6/openpost-server`. The deployed server SHA-256 is `7680c802ddb9de55e51b5fc68ef7dafae659a2798b9ba2fd07cfeab907100293`, the token-helper SHA-256 is `a31030d4bb9c8234266e168f9aa6435970a44f9cbc6923a5a60ba5735cf1dc31`, and `/api/v1/ready` returns `status=ready` with `database=ok`. The exact build/deploy provenance is preserved under `packages/vfigos/openpost/vfbridge6/`.

The Meta provider OAuth for `@velvets_cloud` is valid and a real owner-approved Instagram write has now been completed and canonically verified with the Instagram MCP (`media_id=17899807347597720`). The live mutation service is Cloud Run revision `velvet-instagram-mcp-00018-8mk`, image digest `sha256:5336f9b4ae3db34bb954e31522f07d4e6f85462a1e416964be516704c08569c2`, which waits for feed-image container `FINISHED` before `media_publish` and returns sanitized `error_class`, `stage`, `write_outcome` and `retry_safety` metadata for safe recovery. Delivery approval is therefore **LIVE_VERIFIED** rather than `LIVE_BLOCKED`.

`vfbridge6` preserves safe Meta/Instagram diagnostics: definite auth/permission/validation/rate-limit failures retain their class/code; timeout/network/provider interruption after the durable write fence remains ambiguous and is never blindly replayed. A GrokBot recovery path is available under `packages/vfigos/failover/`, but it is fenced by exact manifest binding, fresh preflight, live duplicate check, signed delivery approval and a read-only OpenPost state check. Grok cannot call Graph directly or publish when the primary outcome is ambiguous/processing/reconcile-only.

Every production `publish_image` schedule must prepare a `velvet.instagram_failover.v1` manifest at staging time so a definitively failed delivery can be recovered inside the delivery window without inventing bindings during the incident. Owner-approved scheduled image posts arm automatic failover by default when `scheduled_at_utc` is present; `--no-auto-failover` is the explicit opt-out. The boot-supervised watcher performs a read-only OpenPost coverage audit every 60 seconds and records `UNPROTECTED_SCHEDULE` when an active Instagram image schedule has no armed exact manifest.

## Watch 2026-09-21 — upstream tip v5.2.2 vs pin v4.35.0

Watch-only follow-up. Pin, staging, `currentBaseline`, and `latestReviewedVersion` stay **v4.35.0**. Production host stays **v4.35.0-vfbridge6**. No staging/production promotion. `ownerNotify=false`. Decision: **PIN_HOLD_REVIEW_REQUIRED**. Existing `deliveryApproval` **LIVE_VERIFIED** is unchanged and not newly invented. Draft PR #279 recorded tip v5.1.2 against stale main and is superseded for tip currency only.

Evidence (GitHub Releases API `get_latest_release`, Asia/Jerusalem 2026-09-21 ~07:20):

- Latest upstream: **v5.2.2** published `2026-09-20T20:49:34Z` — https://github.com/getopenpost/openpost/releases/tag/v5.2.2
- Gap since reviewed pin (newest first): `v5.2.2` → `v5.1.2` (`2026-09-20T00:27:03Z`) → `v5.0.0` (`2026-09-19T20:12:32Z`) → `v4.36.3` (`2026-09-19T11:44:55Z`) → `v4.35.3` (`2026-09-18T16:34:16Z`) → baseline `v4.35.0`
- Compare `v4.35.0...v5.2.2`: `ahead_by=304`; migrations present: `137_mcp_media_upload_tickets.sql`, `138_publication_creation_source.sql`
- Linux server asset recorded only (not deployed): `openpost-server-linux-amd64` digest `sha256:cd4fae925584564214da0b40d94676b20ae4a8a0f406a48d8644620866c54d2d`

### Preliminary classification (release bodies only — not requiredChecks PASS)

- **v4.36.3 — highest VF impact / next staging review target.** Facebook/Instagram OAuth now requests Meta dependency scopes `pages_read_user_content` and `pages_manage_metadata`. Facebook video Stories/Reels hosted-file upload + polling. Facebook analytics metric families. Threads UTF-8 byte limit. MCP lists every operation as its own tool by default; `OPENPOST_MCP_MODE=search` restores search-first. Archive-reader DoS fix. Credential-bearing URL scrub. Migrations 137/138 sit on this hop range.
- **v5.0.0 — do not consider before v4.36.3 evidence.** Editor UX + public docs reorg (including MCP guides). Major tag; breaking-change completeness is UNPROVEN from notes alone.
- **v5.1.2 — low VF impact on notes.** Server-only release CI no longer waits for a skipped Android package.
- **v5.2.2 — incremental vs v5.1.2; HOLD unchanged.** Mostly free-tools / editors / docs. VF-adjacent: nested Instagram/Facebook/LinkedIn/YouTube comment replies into the engagement inbox; clearer Facebook "no manageable Pages" error; native multi-arch `linux/amd64` + `linux/arm64` container images.
- **v4.35.3 — low VF impact on notes.** Android APK release-promotion race.

`OPENPOST_DIAGNOSTICS_ENABLED=false` policy text is unchanged and still required.

### requiredChecks (no PASS without evidence)

| Check | Status | Why |
|---|---|---|
| `release_notes_and_breaking_changes` | NOTES_READ_PRELIMINARY | Gap release bodies read, including new tip v5.2.2. Full changelog/source not a requiredChecks PASS. v5.0.0 breaking completeness UNPROVEN. |
| `meta_instagram_auth` | REVIEW_REQUIRED | v4.36.3 OAuth dependency scopes. Current OAuth proof is v4.35.0 only. |
| `api_mcp_contract` | REVIEW_REQUIRED | v4.36.3 MCP default tool-per-operation + new endpoints/metadata. No VF contract test. |
| `media_limits` | NOTES_ONLY_UNPROVEN | Threads byte-limit + Facebook hosted-file upload named. No Instagram media-limit named. Source not verified. |
| `scheduler_queue_retry` | NOTES_ONLY_UNPROVEN | Publication-source tracking named with migration 138. No VF IG scheduler change proven. |
| `database_schema_migrations` | MIGRATIONS_PRESENT_UNPROVEN | Compare names `137_mcp_media_upload_tickets.sql` and `138_publication_creation_source.sql`. No backup or isolated smoke on any gap tag. Pin remains schema 136. |
| `security` | NOTES_ONLY_UNPROVEN | Archive-reader DoS + credential-URL scrub named. Diagnostics stay fail-closed. No newer-artifact security review. |
| `staging_smoke` | NOT_RUN | No staging upgrade or isolated smoke on any tag newer than v4.35.0. |
| `instagram_live_verify` | PIN_RECORDED_UNCHANGED | Existing pin already records LIVE_VERIFIED. This watch invents no new `liveVerified`. |
| `analytics_read` | NOTES_ONLY_UNPROVEN | Facebook metric-family notes. Instagram analytics contract not verified. אין ספירה. |
| `signed_delivery_approval_live` | PIN_RECORDED_UNCHANGED | Existing `deliveryApproval.currentLiveEvidence=LIVE_VERIFIED` is unchanged. No new write. No approval bypass. |

### Next step

Staging review of **at least v4.36.3** (Meta/Instagram auth + MCP contract, plus backup/migration smoke for 137/138) before any 5.x consideration. Do not bump `latestReviewedVersion` until requiredChecks have real evidence.

Version state: [`OPENPOST.json`](OPENPOST.json).
