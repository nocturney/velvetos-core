# Creative / Media Orchestration — Phase 2 consolidation handoff

Date: 2026-10-02
Status: PASS_WITH_TYPED_GAPS
Scope: orchestration design + representative real acceptance, isolated from the shared final CreativeCraftRouter/registry.

## Result

Creative Craft now has an evidence-backed orchestration design for all 13 required creative/media workflow families.
The design preserves the existing authority hierarchy instead of creating a second Visual Foundry, Media Vault, approval queue, publishing path or tool runtime.

Canonical flow:
`existing intent/truth authority -> relevant craft Skill(s) -> accepted typed adapter -> file-backed stage receipt -> exact-output QA -> existing review/publish gate`

For public Velvet creative, `vf-content-sprint` + `velvet-creative-director` / vfom remain authoritative for Product Truth, Visual OS, brand, Hebrew copy, Creative Manifest and review evidence.
Engineering/CAD/fabrication sources remain authoritative for physical and engineering truth.
Craft Skills own professional method and QA only.
Execution is permitted only through a current accepted bounded/typed surface.

The shared `CreativeCraftRouter.py` and `creative-craft-registry.json` were intentionally not modified.

## Workflow routing matrix

| Intent | Primary | Secondary/specialist | Current readiness |
| --- | --- | --- | --- |
| Product-image finishing | Photoshop craft preference | PHOTO-PAINT, Affinity, vector overlay tools | PARTIAL_TYPED_AUTOMATION |
| Vector/logo/layout | CorelDRAW | Illustrator, Affinity, InDesign | READY_BOUNDED_WITH_COREL |
| Technical illustration | XVL -> Corel DESIGNER | DESIGNER direct, XVL HTML5 | READY_BOUNDED |
| PBR/material pipeline | Substance Painter | Substance Designer + Blender/Maya/3ds Max | PARTIAL_ORCHESTRATION |
| 3D turntable/product viz | Blender | Maya, 3ds Max, Painter | PARTIAL_ORCHESTRATION |
| Short social video | HyperFrames | AE, Resolve/Fusion, Fusion Studio, VoiceStudio | READY_WITH_AUTHORITY_AND_BOUNDED_RENDER |
| Long/edit-heavy video | DaVinci Resolve Studio | Premiere, Fusion, Topaz, AME | READY_BOUNDED_IN_RESOLVE |
| Color/finish | DaVinci Resolve Studio | ffprobe verification | READY_BOUNDED_IN_RESOLVE |
| Video enhancement | Topaz Video | Resolve/ffprobe before-after QA | READY_BOUNDED |
| Hebrew narration/subtitles | VoiceStudio + faster-whisper | Resolve, ffmpeg/ffprobe | READY_BOUNDED |
| Technical explainer animation | Manim | HyperFrames, AE, Fusion, Resolve | READY_WITH_TYPED_WRAPPER_GAP |
| Engineering/technical publication | XVL/DESIGNER -> InDesign -> Acrobat | XVL HTML5 | PARTIAL_END_TO_END_AUTOMATION |
| Reusable derivative factory | Adobe Media Encoder | ffmpeg/ffprobe | READY_BOUNDED_ONE_PRESET |

## Motion/compositing decision

- Manim: semantic geometry, measurements, process and technical-diagram motion.
- HyperFrames: deterministic templated/social composition under existing vfom authority.
- After Effects: art-directed Adobe-native layer/motion-graphics work.
- Fusion Studio standalone: dedicated/reusable node graphs and VFX independent of an edit timeline.
- Resolve Fusion: comps tightly coupled to a Resolve timeline/color/finish job.

## Speech placement

Script/copy authority always precedes speech generation.
VoiceStudio/OmniVoice or faster-whisper then creates file-backed audio/transcript/timing, followed by pronunciation/back-transcription QA.
The editor consumes those artifacts; a speech receipt never grants publication authorization.

## Host lifecycle — important production rule

GUI/COM Phase 2 candidate hosts must be launched through the existing `VelvetOS Phase2 Candidate <id>` Scheduled Tasks using InteractiveToken.
Direct Session 0 launch is not a valid production path and must not be “fixed” by weakening the guard.
Headless CLI adapters may run directly only when their accepted contract allows it.
## Acceptance evidence

1. **XVL -> Corel DESIGNER -> Acrobat: PASS**
   - input XVL SHA-256: `FA9FE9CAA6E3FE3255CFBA3B89CDBEB1F4F30A3E5FECBB421BD1F28FCD8B4F88`
   - editable CDR SHA-256: `01ED79D95F5903E886E504EAC47130CB9A4211899BF6AEC83D9B3B1DCD6B7639`
   - PDF SHA-256: `63E203D91E3D87D8E14DC2868C9DE3C7AA3D86C5639D96A6BEC4098A9B828E64`
   - Acrobat inspected that exact generated PDF: PASS, 1 page.

2. **InDesign -> IDML/PDF -> Acrobat: PASS**
   - IDML SHA-256: `7A0B189142C567FF6223B3F51C34EBE9254BF6C80ECE4830C1BE703660FCDD98`
   - PDF SHA-256: `895F3083DF8206D6AB642BF55FF004BED2C1527B82E8737B1294F19CD62B8017`
   - Acrobat exact-PDF inspection: PASS.
   - Scope caveat: current InDesign typed compose is text-only.

3. **HyperFrames master -> Adobe Media Encoder derivative: PASS**
   - source SHA-256: `3F854F8298BA1BDEA1844B9BE4C807FBE2D2B1AE12DDD963DB053AD200B60374`
   - preset: `h264-high`
   - output SHA-256: `0B2B2467AC86E0A0267903FEBF71EBAE432DF8AC40DE7DB0C13E74D56A047CE0`
   - ffprobe: 2.0 s, 1080x1920, H.264, 30 fps, AAC.
   - owned AME cleanup: PASS.

4. **XVL -> HTML5 package: PASS**
   - index.html SHA-256: `08653545269E4BB31E0463C257C72FBA5F337331B55BF593CEDD97ECC612B2CF`
   - package: 111 files, 88 JPGs, 21 resource PNGs.
   - manifest SHA-256: `ABE7847DE96AA99D94088C825695470F00E5BDDADA75A37554466883D079A86E`.

Final acceptance cleanup: ports 6781/6787/6788/6789/6790 FREE; InDesign/AME/XVL/DESIGNER/Acrobat process counts 0; tested Scheduled Tasks Ready.
## Typed-operation gaps to close

### P0
- Photoshop: bounded job-owned source open/duplicate, crop/resize, adjustments/masks, exact asset/text placement, save/export.
- Premiere Pro: job-owned project, media import, sequence/clip editing, audio basics, captions, named export/AME queue.
- InDesign: placed image/PDF/vector, styles, multipage frames, links readback, preflight, package, named PDF preset.
- Media Encoder: named preset registry beyond the single accepted `h264-high` route.
- Manim: declarative technical-scene adapter; never expose arbitrary Python.

### P1
- Illustrator bounded authoring/export.
- After Effects bounded comp/layer/render operations.
- Affinity bounded authoring/export.
- Resolve subtitles/Fairlight plus narrower node-level color/Fusion operations.
- Fusion Studio bounded reusable comp templates.
- Acrobat deeper typed prepress facts where officially supported.
- VoiceStudio normalized subtitle/timing handoff.
- Shared bounded turntable operation for Blender/Maya/3ds Max.

## Isolated design artifacts

- `packages/vfharness/devtools/creative-craft/orchestration-phase2/orchestration-catalog.json`
- `packages/vfharness/devtools/creative-craft/orchestration-phase2/pipeline-contract.schema.json`
- `packages/vfharness/devtools/creative-craft/orchestration-phase2/typed-operation-gaps.json`
- `packages/vfharness/devtools/creative-craft/orchestration-phase2/acceptance-test-plan.json`
- `packages/vfharness/devtools/creative-craft/orchestration-phase2/ORCHESTRATION-DESIGN.md`
- `docs/evidence/creative-craft/creative-media-orchestration-phase2-2026-10-02.json`

Operational evidence mirror:
`D:\Velvet\Logs\CreativeCraft\creative-media-orchestration-phase2-2026-10-02.json`

## Consolidation instructions

The next consolidation must remain thin:
1. map high-level intent to the existing authority;
2. load only the relevant craft Skill(s);
3. resolve the accepted typed surface from current routing/runtime state;
4. enforce the file-backed pipeline contract and stage receipts;
5. fail closed on an unavailable typed operation instead of falling back to arbitrary scripting;
6. keep `publish_authorization=false`; existing review/publish systems remain authoritative.

Do not duplicate specialist knowledge into one giant router prompt.
Do not broaden adapter authority merely to make a workflow appear complete.
Do not treat an accepted tool installation as proof that every desired operation is automated.
