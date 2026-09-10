---
name: vf-media-librarian
description: Classify, search and maintain Velvet Factory creative media inside the canonical vfmedia Media Vault. Use for raw footage intake, B-roll retrieval, shot-type tagging, orientation and quality assessment, project/material/SKU metadata, rights/approval status, Asset Truth, derivative linking and creative asset selection. Never create a second media catalog or treat Asset Truth as Claim Truth.
---

# Velvet Media Librarian

Operate on the existing `packages/vfmedia` catalog and Drive-backed Media Vault only. Do not create a parallel DAM, spreadsheet, database or creative-memory store.

## Authorities

Read `packages/vfmedia/SKILL.md`, `packages/vfmedia/catalog.schema.json`, `packages/vfmedia/INTAKE.md`, `docs/MEDIA-VAULT.md`, `packages/vfom/VISUAL-OS.md`, `packages/vfom/CREATIVE-MANIFEST.schema.json` and the active Content Contract.

## Intake and classification

For each real media item, record or infer only evidence-supported metadata:

- project/job/SKU/material/object when known.
- date/source/origin.
- `shotType`: `hero|macro|process|failure|proof|human|b-roll`.
- orientation: vertical/horizontal/square and dimensions when available.
- quality: `usable|needs_edit|unusable` with a short reason.
- likely uses: Reel/Story/cover/carousel/portfolio/B-roll.
- rights/approval/privacy/customer restrictions.
- Asset Truth: `verified_real|derived_real|illustrative_ai|synthetic|unverified` plus provenance.
- derivative relationships for crops, grades, exports and final masters.

Never infer permission from possession of a file. Never mark a physical result as proven merely because the asset is real.

## Retrieval

When the Creative Director asks for footage, search by proof need first, then project/product/material, shot type, orientation, recency, quality and rights. Prefer approved real footage and reusable B-roll over generation.

Return concrete media IDs/refs, not vague descriptions. If no suitable real asset exists, report the exact gap instead of fabricating one.

## Creative Manifest contribution

Update `sourceEvidence`, asset refs inside `shots.plan[]`, `shots.missing[]`, rights notes and derivative refs. Keep the canonical Media Vault as the source of truth and the Creative Manifest as the per-content-job coordination artifact.

## Boundaries

Asset Truth is provenance, not Claim Truth. Factual public claims still require evidence links in `CONTENT-CONTRACT.schema.json`. Rights/privacy uncertainty, private CAD uncertainty and missing physical filming are human-surface exceptions; routine tagging, search and quality classification are autonomous.
