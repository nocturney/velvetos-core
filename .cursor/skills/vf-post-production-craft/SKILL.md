---
name: vf-post-production-craft
description: Apply professional editorial, cinematography, color, motion direction, kinetic typography, audio-post, restoration/enhancement and delivery QA across DaVinci Resolve Studio, Premiere Pro, After Effects, Media Encoder, ffmpeg/ffprobe, HyperFrames and Topaz Video. Use for editing, shot language, grading, motion design, animated type, audio finishing, video restoration/upscale, transcodes or final delivery. Plate VFX, roto/key, tracking and CG integration belong to vf-vfx-compositing-craft. This skill supplies craft and QA only; preserve existing content, DCC/Adobe and publishing authorities.
---

# Velvet Post-Production Craft

Apply post craft after the creative/story authority has defined what the piece must communicate. Do not become a second content orchestrator or publishing path.

## Workflow

1. Identify the task class: edit, color, motion/2D composition, audio, restoration/enhancement, delivery, or a combination. Route plate VFX, roto/key, tracking/matchmove, lens-distortion and CG integration to `vf-vfx-compositing-craft`.
2. Lock the source manifest, timeline/frame-rate assumptions and final delivery specification before destructive work.
3. Read only the needed references: `editing.md`, `cinematography.md`, `color.md`, `color-management.md`, `compositing.md`, `motion-direction.md`, `kinetic-typography.md`, `audio.md`, `video-restoration.md`, `media-qa.md`, `delivery.md`, `tool-routing.md`. `compositing-tech-check.md` is retained as a compatibility pointer for VFX handoff; actual VFX shot integration applies `vf-vfx-compositing-craft`. If the task includes TTS, generated voice, ASR, transcript or speech-specific QA, also apply `.cursor/skills/vf-speech-qa/SKILL.md` and keep its consent/license evidence separate.
4. Work from broad corrections to local polish. Preserve recoverable source and a known-good master.
5. Verify the actual rendered/exported artifact with metadata plus visual/audio review.

## Core rules

- Story/communication intent outranks flashy transitions or effects.
- Do not change product truth, chronology or factual meaning during polish.
- Normalize and balance before applying a creative look.
- Keep alpha/premultiplication and color-space assumptions explicit in motion/2D composites. For plate/VFX integration, defer shot-level matte/track/lens/grain decisions to `vf-vfx-compositing-craft`.
- Apply restoration/denoise/sharpen/upscale conservatively and compare against source; enhancement must not invent important evidence.
- Use delivery targets from the destination specification, not generic codec/loudness numbers from memory.

## Hard stops

- Do not publish or schedule content from this skill.
- Do not introduce paid/cloud render or enhancement services automatically.
- Do not claim a render is good because the encoder exited successfully.
- Do not overwrite the only source/master when a reversible workflow is possible.
- Do not fabricate missing frames, details or speech in evidence-bearing content.
- Do not absorb plate/VFX shot ownership merely because the selected host also supports compositing.

## Completion contract

Report relevant states separately: `edit_locked`, `color_checked`, `composite_checked`, `audio_checked`, `master_rendered`, `delivery_qc_passed`, `publication_authorized`.
This skill can never set `publication_authorized` by itself.