# VelvetOS Publish Bridge

Canonical transport bridge between an **approved publish derivative** and Instagram's requirement for a public HTTPS media URL.

This is not a second media vault, not an approval system, and not evidence that content is live. Source media stays private in Drive/Media Vault. The bridge receives only the exact derivative that has already passed the applicable creative/version/rights/privacy gates.

## Current provider

`github-branch` on repository `nocturney/velvetos-core`, dedicated branch **`publish-bridge`**, prefix `publish-bridge/assets/`.

Public URL shape:

```text
https://raw.githubusercontent.com/nocturney/velvetos-core/publish-bridge/publish-bridge/assets/<YYYY-MM-DD>/<correlation>/<sha20>.jpg
```

`main` is never a media staging target. A branch cleanup workflow removes old assets from the current branch head after the configured retention window. **Git cleanup is not secure erasure from repository history**, so this provider is allowed only for media that is already `approved_for_public_release` and may safely become public permanently.

## Hard gate

Before staging, all of these must be true:

1. exact derivative/version is approved for public release; folder placement or upload alone is not approval;
2. rights/privacy are known; no private CAD/customer identity ambiguity;
3. required EDIT-GATE/PREFLIGHT/CTA checks passed for that content;
4. no secret, token, private Drive URL, customer phone/email, or unapproved price claim is embedded in the derivative;
5. correlation is non-PII (job/content id such as `G004`, not a customer name).

If any item fails, **do not make the file public**. Keep working inside Drive/Canva/Media Vault.

## Normalize before stage

Images are normalized to JPEG, metadata stripped, orientation applied, and hashed. This avoids relying on HEIC/private originals and gives the Instagram publisher a transport-friendly public asset. Videos are limited to MP4 under the configured bridge limit and require `ffmpeg` metadata stripping.

Local/Cursor CLI:

```bash
python3 scripts/vf_publish_bridge.py prepare \
  --file /path/to/approved-export.png \
  --correlation G004 \
  --approval-ref packages/vfgrowth/preflight/G004.md \
  --source-ref canva:DESIGN_ID

python3 scripts/vf_publish_bridge.py stage \
  --file /path/to/approved-export.png \
  --correlation G004 \
  --approval-ref packages/vfgrowth/preflight/G004.md \
  --source-ref canva:DESIGN_ID \
  --public-release-approved
```

`stage` needs `GH_TOKEN`/`GITHUB_TOKEN`. ChatGPT/agent runs can execute the same contract with the connected GitHub connector: create a binary blob on `publish-bridge`, create a dated/hash path, advance only that branch, then externally fetch-verify the resulting raw URL. Never expose a GitHub token to content or logs.

The public metadata sibling stores only a hash of the private source reference, not the Drive/Canva URL itself.

## Publish flow

```text
private source (Drive / Media Vault)
  -> approved derivative (Canva / vfcovers / vfcanva)
  -> exact version approval + PREFLIGHT + rights/privacy
  -> Publish Bridge normalize + stage
  -> external HTTPS fetch verification
  -> Instagram publish_* using the bridge URL
  -> real publish receipt
  -> live list_media/get_media verification
  -> only then published_verified / liveVerified
```

`staged`, `fetch_verified`, `publish_requested`, or a Calendar slot are **not** publication.

## Fallbacks and limits

- `wsrv.nl` may be used only as a format/transport converter for an already-public approved bridge asset. It is not the source of truth and should not be needed for normal image staging because the bridge emits JPEG.
- The Velvet bridge fails closed at 50 MiB for MP4 and 20 MiB for images. GitHub blocks regular Git objects above 100 MiB, so large reels/video must use an object-storage provider rather than being forced into Git.
- Planned stronger provider: dedicated GCS object storage with expiring/signed publishing objects. Until that is deployed, do not claim Git retention is true expiry.

## Retention

`.github/workflows/publish-bridge-cleanup.yml` removes dated asset directories older than `retention.activeDays` from the **branch head**. The cleanup job is hygiene/deindexing only. It does not rewrite Git history.

## Never

- never change sharing on the private Drive source merely to satisfy Instagram;
- never stage raw intake (`01 - נכנס` / `02 - מקור`) or unapproved work;
- never put publish binaries on `main`;
- never treat public URL creation as approval or live publication;
- never bypass PREFLIGHT/rights/privacy because transport is available;
- never auto-DM, boost, change price, send customer WhatsApp, or trigger Print from this bridge.
