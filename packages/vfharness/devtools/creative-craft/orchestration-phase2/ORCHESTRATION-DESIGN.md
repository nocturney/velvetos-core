# Creative / Media Orchestration — Phase 2 design

Date: 2026-10-02
Status: isolated design candidate; shared CreativeCraftRouter/registry intentionally untouched.

## Purpose
This layer coordinates existing authorities, craft Skills, accepted adapters and exact-output QA. It is not a second Visual Foundry, Media Vault, approval queue, publisher or runtime orchestrator.

## Authority model
1. Public Velvet creative enters through `vf-content-sprint` and `velvet-creative-director` / vfom. Product Truth, Visual OS, brand, Hebrew copy, Creative Manifest and review evidence stay there.
2. Engineering and fabrication truth stays with CAD/3D/fabrication authorities. Creative/media files may illustrate that truth but never become geometry or physical-claim authority.
3. Craft Skills decide professional method and QA. They do not grant execution or business authority.
4. Execution may use only an accepted typed/bounded adapter whose current routing state is available.
5. Every cross-tool handoff must be file-backed and hash-addressed. Tool success is not publish authorization.

## Primary routing decisions
- Product raster finishing: Photoshop by craft preference; Corel PHOTO-PAINT is the currently stronger bounded automation option. Photoshop needs typed edit/export operations before autonomous finishing is claimed.
- Vector/layout: CorelDRAW is the strongest current typed vector authoring surface. Illustrator remains preferred for Illustrator-native work but its accepted automated surface is still read-only.
- Technical illustration: XVL Studio Corel Edition -> Corel DESIGNER is the primary 3D-derived path. Corel DESIGNER direct is primary for already-2D technical work.
- PBR/lookdev: Substance Painter for asset-level baking/painting; Substance Designer for procedural materials; Blender/Maya/3ds Max for geometry/UV/destination checks.
- 3D turntable: keep it in one DCC unless a specialist material stage is actually needed. A shared bounded turntable operation is still missing.
- Short social: HyperFrames for deterministic social assembly, with AE/Resolve/Fusion only when the creative requirement genuinely needs custom compositing/motion.
- Long-form edit: Resolve is primary because its accepted surface already covers media/timeline/settings/render/LUT. Premiere is not yet an autonomous timeline editor through the current first-party bridge.
- Color/finish: Resolve.
- Enhancement: Topaz Video only when diagnosis justifies it; never a mandatory stage.
- Hebrew narration/subtitles: VoiceStudio/faster-whisper -> back-check/timing -> editor.
- Technical explainer: Manim for semantic technical motion, then optional HyperFrames/AE/Fusion/Resolve for finish.
- Engineering publication: CAD/XVL -> Corel DESIGNER -> InDesign -> Acrobat, but the InDesign place/link/preflight/package surface is the remaining blocker for a true end-to-end automated publication.
- Derivatives: Media Encoder becomes the Adobe derivative factory only through named accepted presets. Today that means `h264-high`, not arbitrary export settings.

## Motion/compositing split
Use Manim when coordinates, dimensions, geometry or process semantics should drive the animation.
Use HyperFrames when the job is deterministic templated social/motion composition under vfom.
Use After Effects when art-directed layers, typography and Adobe-native motion graphics are the real requirement.
Use standalone Fusion Studio for dedicated/reusable node comps and batch-style VFX work.
Use Resolve Fusion when the comp is tightly coupled to a Resolve edit/color timeline.

## Speech placement
Script/copy authority comes first. VoiceStudio TTS or faster-whisper ASR then creates file-backed audio/transcript/timing. Back-transcription/pronunciation QA must pass before editor consumption. Speech receipts never authorize publication.

## Stage receipt contract
Record job/pipeline/stage id, authority and source refs, exact input SHA-256, tool/version/typed operation/preset, session ownership, exact output SHA-256, technical probe/craft QA, fallback if any, and `publish_authorization=false`.
A downstream stage consumes the previous file-backed artifact + receipt, never an unverified in-memory claim.

## Immediate typed-operation priorities
P0: InDesign place/link/styles/preflight/package; Photoshop bounded finishing; Premiere bounded timeline; Media Encoder named preset registry; declarative Manim adapter.
P1: Affinity authoring/export; Illustrator authoring/export; AE bounded comp/render; Resolve subtitle/Fairlight/node-level operations; Fusion Studio bounded comp templates; normalized VoiceStudio subtitle/timing handoff; standardized DCC turntable operation.

## Acceptance strategy
Run only small, reversible, file-backed tests with synthetic/vendor samples. First: XVL -> Corel DESIGNER CDR/PDF -> Acrobat inspection. Second: harmless local MP4 -> Media Encoder `h264-high` -> ffprobe validation.
No test may publish, send, overwrite an existing artifact, attach to a pre-existing user GUI session, or widen an adapter scripting surface.

## Consolidation boundary
This folder is evidence/design input for later shared-router consolidation. Keep the final router thin: resolve authority -> load relevant craft Skills -> select accepted typed surface -> require stage receipts -> return artifact lineage.

## Runtime host lifecycle confirmed by acceptance

GUI/COM Phase 2 candidate hosts must be launched through the existing InteractiveToken Scheduled Tasks. Direct launch from Remote Desktop Commander's Session 0 is not a valid production-path test: XVL GUI could not become UI-ready there, InDesign COM stalled there, and Media Encoder correctly refused Session 0.

The same operations passed when their existing Scheduled Tasks were used. Therefore host lifecycle is part of the orchestration contract, not an implementation detail:
- GUI/COM candidate: start its existing `VelvetOS Phase2 Candidate <id>` task, wait for the localhost adapter, execute the typed operation, then use the adapter's shutdown route or stop only the task started for the job.
- Headless CLI candidate: direct execution is allowed only when the accepted adapter contract supports it.
- A failed Session 0 launch must never be "fixed" by weakening session guards or attaching to an arbitrary user process.

## Acceptance results — 2026-10-02

- XVL Studio Corel Edition -> Corel DESIGNER -> Acrobat: PASS via InteractiveToken. Produced editable CDR + PDF; Acrobat inspected the exact PDF.
- InDesign -> IDML/PDF -> Acrobat: PASS via InteractiveToken. This proves the bounded text-publication handoff only; rich placed-asset/preflight/package operations remain a typed gap.
- HyperFrames smoke master -> Adobe Media Encoder `h264-high`: PASS via InteractiveToken. ffprobe validated 1080x1920 H.264/AAC, and the owned AME host cleaned up.
- XVL -> HTML5 package: PASS headless. Package validation found 111 files including 88 JPGs plus manifest/hash evidence.
- Final cleanup: tested adapter ports free, tested GUI processes absent, and tested Scheduled Tasks returned to Ready.
