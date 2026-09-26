# findings — OpenPost release watch 2026-09-21

## Authority (current main)

- `currentBaseline` / `latestReviewedVersion` / `stagingVersion` = v4.35.0
- `productionHost.version` = v4.35.0-vfbridge6
- `pinExactVersion=true`; `productionUsesLatestTag=false`; `autoPromoteWithoutTests=false`
- `OPENPOST_DIAGNOSTICS_ENABLED=false` unchanged
- `deliveryApproval.currentLiveEvidence` = LIVE_VERIFIED already recorded; no new liveVerified invented

## Upstream (GitHub Releases API, this run)

- Latest tip: v5.2.2 published `2026-09-20T20:49:34Z`
- URL: https://github.com/getopenpost/openpost/releases/tag/v5.2.2
- Linux asset `openpost-server-linux-amd64` digest `sha256:cd4fae925584564214da0b40d94676b20ae4a8a0f406a48d8644620866c54d2d` — record only, not deployed
- Gap: v5.2.2, v5.1.2, v5.0.0, v4.36.3, v4.35.3, baseline v4.35.0
- Compare v4.35.0...v5.2.2: ahead_by=304; migrations `137_mcp_media_upload_tickets.sql`, `138_publication_creation_source.sql`

## Classification (release bodies only)

- v4.36.3 remains highest VF-relevant hop / next staging review target
- v5.0.0 major tag; breaking completeness UNPROVEN
- v5.1.2 low VF (Android CI skip)
- v5.2.2 incremental vs v5.1.2; nested comment replies + clearer FB Pages error + multi-arch images; HOLD unchanged
- v4.35.3 low VF (Android APK race)

## Prior PR

https://github.com/nocturney/velvetos-core/pull/279 recorded tip v5.1.2 against stale main. Superseded for tip currency only.
