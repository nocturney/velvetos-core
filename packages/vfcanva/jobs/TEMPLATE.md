# Canva job — @velvets_cloud

| Field | Value |
|---|---|
| Date | |
| Job / SKU / print | |
| Format id | `ig_feed_square` / `ig_feed_portrait` / `ig_story` / `ig_reel_cover` / `ig_carousel_square` |
| Caption (`vfcopy`) | or `חסר` |
| Proof (Drive / file the user named) | or `חסר` |
| Extra sizes | square / story / portrait — list only what was asked |
| Canva design id | |
| Edit URL | |
| Brand check | on brand / off brand / `Can't verify` |
| `vfigos` | review only — not sent |

## Notes

- CTA: שלחו לנו הודעה כאן באינסטגרם · איסוף שדרות (`PUBLIC_CURRENT_CTA`). Not WhatsApp / `050-2517000` on public frames.
- Do not invent ₪ or a floor scene.
- HQ does not send.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.

### Visual-standard evidence contract

A Velvet Factory creative job cannot advance to design handoff, quality_checked, authorized_for_tool_publish, export or publish unless the same job records all of: `visual_standard_gate=PASS`, `visual_standard_canva_asset_id=MAHVL7PKpvE`, `visual_standard_artifact_sha256=df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`, concrete `product_truth_source_refs`, and the exact-final artifact digest. Missing or mismatched evidence is `visual_standard_unavailable` and blocks the branch.
