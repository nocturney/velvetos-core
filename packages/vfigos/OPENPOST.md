# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
Runtime baseline: **v4.35.0**
Latest reviewed upstream: **v4.35.0** (2026-09-17)
Upstream head observed (watch only): **v5.1.2** (2026-09-20) — pin **UNCHANGED**
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

Windows staging remains pinned to **v4.35.0** with its verified backup/migration evidence. A dedicated GCP production host is now deployed at `https://openpost.34.9.7.22.sslip.io` using the exact Linux v4.35.0 artifact `sha256:157abefc2810dde09e914b78915f79c0160fcf60047856a30a1261c1721d2856` behind Caddy. Public `/api/v1/ready` returns HTTP 200 with `status=ready` and `database=ok`; TLS verification passes, HTTP redirects to HTTPS, direct external TCP/18080 is blocked, public SSH/RDP are denied by higher-priority target-specific firewall rules, IAP-only SSH is verified, diagnostics are disabled, and a full VM reset returned the same ready response. This proves the stable public app/media origin, not production promotion. The first OpenPost user is now verified as instance admin, one workspace with one member exists, and new registrations are disabled (`OPENPOST_DISABLE_REGISTRATIONS=true`, `/api/v1/auth/config` reports `registration_enabled=false`). The Meta provider app is loaded from the encrypted database configuration and OAuth for `@velvets_cloud` is verified with a valid, unrevoked grant. No real Instagram write was performed, so `LIVE=false` and production promotion remains blocked on one authorized write plus canonical `list_media` / `get_media` verification. Delivery approval remains **BOUNDARY_SMOKE_VERIFIED / LIVE_BLOCKED**.

## Watch 2026-09-20 — upstream head v5.1.2 vs pin v4.35.0

Watch-only observation. Pin, staging, production host, `currentBaseline`, and `latestReviewedVersion` stay **v4.35.0**. No staging/production promotion. `ownerNotify=false`. Decision: **PIN_HOLD_REVIEW_REQUIRED**.

Evidence (GitHub Releases API, Asia/Jerusalem 2026-09-20 ~07:16, re-verified same morning):

- Latest upstream: **v5.1.2** published `2026-09-20T00:27:03Z` — https://github.com/getopenpost/openpost/releases/tag/v5.1.2
- Gap since reviewed pin (newest first): `v5.1.2` → `v5.0.0` (`2026-09-19T20:12:32Z`) → `v4.36.3` (`2026-09-19T11:44:55Z`) → `v4.35.3` (`2026-09-18T16:34:16Z`) → baseline `v4.35.0`

### Preliminary classification (release bodies only — not requiredChecks PASS)

- **v4.36.3 — highest VF impact / next staging review target.** Facebook/Instagram OAuth now requests Meta dependency scopes `pages_read_user_content` and `pages_manage_metadata` (fixes `Invalid Scopes`). Facebook video Stories/Reels hosted-file upload session + polling. Facebook analytics metric families per Graph object type. Threads UTF-8 byte limit vs character check. MCP lists every operation as its own tool by default; `OPENPOST_MCP_MODE=search` restores search-first (`both` combines). Meta analytics + TikTok reconciliation release-validation fixes. Archive-reader DoS fix for local AI models. Also: credential-bearing URL scrub in provider network errors; new default MCP endpoint / code-mode / RFC 9207 issuer metadata.
- **v5.0.0 — do not consider before v4.36.3 evidence.** Video/Image editor UX plus public docs reorg (Guides / Self-hosting / AI / Automate / editors / API). Major tag; breaking-change completeness is UNPROVEN from notes alone.
- **v5.1.2 — low VF impact on notes.** Server-only release CI no longer waits for a skipped Android package.
- **v4.35.3 — low VF impact on notes.** Release-promotion Android APK race.

`OPENPOST_DIAGNOSTICS_ENABLED=false` policy text is unchanged and still required.

### requiredChecks (no PASS without evidence)

| Check | Status | Why |
|---|---|---|
| `release_notes_and_breaking_changes` | NOTES_READ_PRELIMINARY | Gap release bodies read. Full changelog/source/migrations not reviewed. v5.0.0 breaking completeness UNPROVEN. |
| `meta_instagram_auth` | REVIEW_REQUIRED | v4.36.3 OAuth dependency scopes. Current OAuth proof is v4.35.0 only. |
| `api_mcp_contract` | REVIEW_REQUIRED | v4.36.3 MCP default tool-per-operation + new endpoints/metadata. No VF contract test. |
| `media_limits` | NOTES_ONLY_UNPROVEN | Threads byte-limit + Facebook hosted-file upload named. No Instagram media-limit named. Source not verified. |
| `scheduler_queue_retry` | NOTES_ONLY_UNPROVEN | TikTok reconcile / Facebook comment paging / publication-source tracking named. No VF IG scheduler change named. |
| `database_schema_migrations` | UNPROVEN | Notes do not name migrations. Absence ≠ proof. No smoke on gap tags. Pin remains schema 136. |
| `security` | NOTES_ONLY_UNPROVEN | Archive-reader DoS + credential-URL scrub named. Diagnostics stay fail-closed. No newer-artifact security review. |
| `staging_smoke` | NOT_RUN | No staging upgrade or isolated smoke on any tag newer than v4.35.0. |
| `instagram_live_verify` | BLOCKED_UNCHANGED | Remaining LIVE blocker unchanged: authorized Instagram Graph write + canonical `list_media` / `get_media`. |
| `analytics_read` | NOTES_ONLY_UNPROVEN | Facebook metric-family + Meta/TikTok validation notes. Instagram analytics contract not verified. אין ספירה. |
| `signed_delivery_approval_live` | BLOCKED_UNCHANGED | Still `BOUNDARY_SMOKE_VERIFIED / LIVE_BLOCKED`. No real Graph write. |

### Next step

Staging review of **at least v4.36.3** (Meta/Instagram auth + MCP contract, plus backup/migration smoke if files exist) before any 5.x consideration. Do not bump `latestReviewedVersion` until requiredChecks have real evidence.

Version state: [`OPENPOST.json`](OPENPOST.json).
