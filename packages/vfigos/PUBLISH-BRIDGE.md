# VelvetOS Publish Bridge

Canonical transport bridge between an **approved publish derivative** and Instagram's requirement for a public HTTPS media URL.

This is not a second media vault, not an approval system, and not evidence that content is live. Source media stays private in Drive/Media Vault. The bridge receives only the exact derivative that has already passed the applicable creative/version/rights/privacy gates.

## Current provider

`github-branch` on repository `nocturney/velvetos-core`, dedicated branch **`publish-bridge`**.

Active transport prefix: `publish-bridge/assets/`  
Archive prefix: `publish-bridge/archive/`

Public active URL shape:

```text
https://raw.githubusercontent.com/nocturney/velvetos-core/publish-bridge/publish-bridge/assets/<YYYY-MM-DD>/<correlation>/<sha20>.jpg
```

`main` is never a media staging target. Assets older than the configured active window leave the active transport path and move to the archive path. **They are not automatically deleted.** Archived assets are retained indefinitely unless the owner explicitly approves a different retention policy.

Because the current provider is Git-backed and assets are already public-release-approved, both active and archived derivatives must be safe to remain retrievable. Archive is preservation, not privacy restoration.

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
  -> approved export handoff (register local + Canva sourceRef)
  -> Publish Bridge normalize + stage in assets/
  -> external HTTPS fetch verification
  -> Instagram publish_* using the active bridge URL
  -> real publish receipt
  -> live list_media/get_media verification
  -> only then published_verified / liveVerified
  -> after active window: move assets/<date>/... -> archive/<date>/...
```

`staged`, `fetch_verified`, `publish_requested`, or a Calendar slot are **not** publication.

## Artifact handoff / recovery (do not strand Cursor exports)

Cursor may write approved delivery PNGs under `/opt/cursor/artifacts/...`. That path is **ephemeral** — ChatGPT/HQ cannot rely on it alone.

After PREFLIGHT / public-release approval:

1. `python3 scripts/vf_publish_handoff.py register …` writes a **manifest** under `packages/vfigos/handoff/` (git, no binaries on `main`).
2. Prefer immediate `recover --stage` so the exact export lands on `publish-bridge` the same turn.
3. If a later agent finds `approved_export_local` but no bridge asset: run recovery automatically — re-read local file if still present, else re-export from `sourceRef` (`canva:DESIGN_ID`), stage, fetch-verify. Only after those paths fail emit a **layer-specific** blocker (`blocked_artifact_retrieval` / `blocked_bridge_staging` / `blocked_public_fetch`), never a vague immediate `blocked_publish_transport`.

Rejected as current delivery source (fail closed): historical `vfcanva/jobs/**/story-*.png`, Canva preview/thumbnail URLs, private Drive URLs, `wsrv.nl` as SoT, arbitrary files from `main`.

Publication ledger: `packages/vfigos/data/publications/<CORRELATION>.json` tracks `approved → staged → fetch_verified → published → published_verified` with receipts. Idempotent on content hash + media_id.

## Archive retention

The active transport window is currently 14 days. `.github/workflows/publish-bridge-cleanup.yml` runs daily and moves expired dated directories from:

```text
publish-bridge/assets/<YYYY-MM-DD>/...
```

to:

```text
publish-bridge/archive/<YYYY-MM-DD>/...
```

Rules:

- archive retention is **unlimited**;
- automatic deletion of archived assets is **disabled**;
- existing archive destinations are never overwritten; a collision fails closed;
- the move preserves the derivative and its metadata together;
- the archive is not used as the normal Instagram transport path;
- reusing an archived asset for a new publication should create/re-stage the exact currently approved derivative through the normal bridge flow rather than silently treating an old archived URL as current approval.

## Fallbacks and limits

- `wsrv.nl` may be used only as a format/transport converter for an already-public approved bridge asset. It is not the source of truth and should not be needed for normal image staging because the bridge emits JPEG.
- The Velvet bridge fails closed at 50 MiB for MP4 and 20 MiB for images. GitHub blocks regular Git objects above 100 MiB, so large reels/video must use an object-storage provider rather than being forced into Git.
- Planned stronger provider: dedicated GCS object storage. The provider can change without changing the approval/publish contract; if that happens, archive-preservation remains the default unless Christian explicitly changes it.

## Never

- never change sharing on the private Drive source merely to satisfy Instagram;
- never stage raw intake (`01 - נכנס` / `02 - מקור`) or unapproved work;
- never put publish binaries on `main`;
- never treat public URL creation as approval or live publication;
- never bypass PREFLIGHT/rights/privacy because transport is available;
- never automatically delete archived publish assets;
- never overwrite an archive collision;
- never auto-DM, boost, change price, send customer WhatsApp, or trigger Print from this bridge.
