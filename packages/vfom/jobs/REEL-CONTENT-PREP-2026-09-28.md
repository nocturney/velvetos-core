# Reel content prep — 2026-09-28

Scope: data and documentation only. No media was rendered, scheduled or published.

## Live rich stills → Reel job folders

| Job | Live post | Variables | Text-free master |
|---|---|---|---|
| `VF-R006` | owl · 2026-09-19 | `VF-R006/variables.json` | **missing** |
| `VF-R007` | dragon tray · 2026-09-20 | `VF-R007/variables.json` | **missing** |
| `VF-R008` | deer · 2026-09-23 | `VF-R008/variables.json` | **missing** |
| `VF-R009` | octopus carousel · 2026-09-27 | `VF-R009/variables.json` | **missing** |

Each folder also contains `prep-status.json`, which records the source search and fails closed with `status=needs_input`.

Search result: no tracked product/date/text-free-master file exists in the repo for these four live posts. The current ChatGPT Project asset bundle contains S01–S07 style references, the two approved logo images, and the 6.6.9 authority/runtime files; it does **not** contain a text-free owl/dragon/deer/octopus master. Published composites are not treated as reversible masters.

The variables preserve the exact live captions captured read-only in PR2. They remain `needs_input`: hero master, real-motion beat and approved/documented audio are empty rather than fabricated.

## Printer-to-shelf inventory

See `printer-to-shelf-candidates.json`.

The current catalog has 38 video items and 34 usable source videos after existing exclusions. The canonical `vf_reel_candidates.py` filename pattern supports **11 unused printer timelapses with positive filename evidence**. This does not support the approximate figure of ~17 as a verified fact.

Confirmed filename-family matches include:
- `king_v3_...` → likely chess king / possible Regnum family; exact linkage remains unverified because `productLink=null`;
- `SoccerBall final_...` → SoccerBall family;
- `MMM_RoboOctopus_Connector_...` → RoboOctopus connector;
- `MMM_SeaTurtle_Head_...` → SeaTurtle head;
- `dragon_multi2tests_...` → dragon family only, **not** verified as the live dragon tray;
- two `Object_1_...`, one UUID-named file and one plate-named file remain product-uncertain.

There are also **13 generic `video_YYYY-MM-DD...` source videos** with no productLink. They are listed separately as possible printer timelapses requiring visual review; they are not silently promoted to printer-to-shelf candidates.

## Turntable inventory

See `turntable-candidates.json`.

Verified local paths on Chris exist for:
- RoboLotl 3MF;
- Axolotl 3MF;
- Jackalope STL variant(s);
- Regnum Chess Set 3MF.

They are local Chris-PC inputs, not repo assets. No turntable was rendered. Colour matching must use embedded print-file material data or explicit verified printed-product colour evidence.

## VF-R001..VF-R005

See `VF-R001-R005-RICH-V2-REVIEW.md`.

All five current manifests and preflights record `PASS / ready_for_publish`. Repository search did not find a publication receipt/live-media binding proving that any of those exact packages became live posts. Treat live publication state as unverified until a read-side live check is performed.

The v2 review gives a concrete current-rich-style route for each package and names blockers rather than fabricating motion, alternate product views or print-file identity.

## Owner-only inputs still needed

The repo/Project evidence cannot supply:
1. text-free masters for the four live rich stills;
2. verified real-motion beats for those still-driven Reels (unless an existing catalog clip is visually bound to the same product);
3. approval/evidence for the selected audio where source sound is insufficient;
4. exact product linkage for generic/ambiguous timelapses;
5. printed-product colour evidence when a Blender turntable should override embedded file colours;
6. exact print-file identity for R002/R004/R005 if turntable is chosen as their missing motion beat.

No price, material, dimensions, stock, durability, print-time claim or product linkage was added without source evidence.
