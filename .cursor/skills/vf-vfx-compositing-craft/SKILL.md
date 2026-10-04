---
name: vf-vfx-compositing-craft
description: Apply professional VFX compositing craft for plate cleanup, roto, keying, tracking and matchmove, CG/AOV integration, lens-distortion workflow, alpha/premultiplication, edge/grain/defocus/motion-blur integration and shot technical review. Use for VFX shots, compositing, roto, key/greenscreen, tracking, matchmove, plate cleanup, render-pass reconstruction, lens distortion or CG integration across accepted local compositing surfaces. Editorial and creative color remain vf-post-production-craft; 3D asset creation remains DCC/material authority. Use only when explicitly routed by Creative Craft, Fabrication Router, or another accepted VelvetOS pipeline for a matching task; do not auto-select this specialist from unrelated ambient context.
---

# Velvet VFX Compositing Craft

Own shot-level image integration without becoming the editorial/color owner or a new scripting runtime. Preserve source plates, camera/lens evidence, upstream 3D/material truth and downstream delivery authority.

## Workflow

1. Lock plate/source identity, frame range, format, color-management context, camera/lens metadata and intended delivery.
2. Read only the needed references: `shot-setup-plate-lens.md`, `roto-key-mattes.md`, `tracking-matchmove.md`, `render-pass-reconstruction.md`, `integration-finishing.md`, `shot-qc.md`, `tool-routing.md`, `provenance.md`.
3. Resolve lens/distortion and plate preparation before judging track, matte or CG alignment.
4. Build mattes/tracks and CG/pass reconstruction as inspectable stages with explicit premultiplication and color-space assumptions.
5. Integrate edges, grain, sharpness, defocus, motion blur, light/color relationship and contact cues from broad to local.
6. Critique first, middle, last and worst/stress frames; repair the cause at the stage where it originates.
7. Re-open/read back the exact shot output and hand it to post-production for creative grade/editorial/delivery as required.

## Core rules

- Undistort/redistort or equivalent lens workflows must be internally coherent; do not track one geometry and composite another.
- Keep alpha and premultiplication state explicit when edges are processed or merged.
- Treat roto/key mattes as technical evidence: inspect hair/detail, motion, chatter, holes, despill and edge treatment over time.
- A good single frame does not prove a shot; temporal continuity and worst frames are mandatory.
- Match inserted elements to the plate image system: perspective, motion, grain/noise, sharpness, defocus, motion blur, exposure relationship and atmospheric depth.
- Keep creative shot matching/color finishing with `vf-post-production-craft`; use color operations here only to integrate elements coherently.

## Hard stops

- Do not redesign or remodel upstream 3D assets to hide a comp issue.
- Do not use arbitrary Nuke/After Effects/Fusion scripting when the accepted surface does not expose the required operation.
- Do not erase source evidence or overwrite the only plate/master.
- Do not fabricate a clean key/track/roto result from one favorable frame.
- Do not let a comp receipt authorize editorial, publication or product claims.

## Completion contract

Report `plate_locked`, `lens_workflow_checked`, `matte_checked`, `track_checked`, `passes_reconstructed`, `integration_checked`, `worst_frames_checked`, and `shot_output_verified` separately.
