# Creative Craft pipelines

Command prefix: `C:\Python314\python.exe D:\Velvet\Runtime\CreativeCraft\CreativeCraftRouter.py`.

## Control commands

- `status [--tool <id>]`: check live availability using the correct gate for each capability.
- `route --request "<request>"`: select a high-level pipeline from the request and immediately return its plan.
- `plan --intent <intent>`: return authority, specialist Skills, readiness, required/optional tools, expected artifacts, QA, and cleanup policy.
- Router status is `PASS` when every required gate is available and `BLOCKED` when a required gate is unavailable or no intent can be resolved.
- Readiness is separate from status. Labels such as `PARTIAL_TYPED_AUTOMATION` or `READY_WITH_TYPED_WRAPPER_GAP` mean the route is valid but some authoring operations remain intentionally unavailable.

## Production pipelines

| Intent | Primary authority / route | Readiness |
| --- | --- | --- |
| `fabrication` | canonical Fabrication Router | READY_BOUNDED |
| `cad-inspect` | Fusion read surface | READY_BOUNDED |
| `mesh-review` | Meshmixer review | READY_REVIEW_LIMITED |
| `mesh-technical-sheet` | Meshmixer -> Corel DESIGNER | READY_BOUNDED |
| `product-image-finishing` | Photoshop + bounded alternative | PARTIAL_TYPED_AUTOMATION |
| `vector-logo-layout` | CorelDRAW | READY_BOUNDED_WITH_COREL |
| `technical-illustration` | XVL -> Corel DESIGNER | READY_BOUNDED |
| `pbr-material-pipeline` | Substance + destination DCC | PARTIAL_ORCHESTRATION |
| `3d-turntable-product-visualization` | DCC + materials + Product Visualization | PARTIAL_ORCHESTRATION |
| `vfx-composite` | VFX Compositing + accepted Resolve/AE/Fusion surfaces | PARTIAL_TYPED_AUTOMATION |
| `short-social-video` | vfom + HyperFrames | READY_WITH_AUTHORITY_AND_BOUNDED_RENDER |
| `long-edit-heavy-video` | Resolve | PARTIAL_TYPED_AUTOMATION |
| `color-finish` | Resolve + probe | PARTIAL_TYPED_AUTOMATION |
| `video-enhancement` | Topaz Video + probe | READY_BOUNDED |
| `hebrew-narration-subtitles` | VoiceStudio/ASR | READY_BOUNDED |
| `technical-explainer-animation` | Manim + optional finish | READY_WITH_TYPED_WRAPPER_GAP |
| `engineering-technical-publication` | XVL/Corel -> InDesign -> Acrobat | PARTIAL_END_TO_END_AUTOMATION |
| `reusable-derivative-export-factory` | Media Encoder + ffprobe | READY_BOUNDED_ONE_PRESET |
| `spatial-planning` | SketchUp + LayOut C APIs | READY_BOUNDED |
| `document-report-bom` | Office typed workers | READY_BOUNDED |
| `ops-package-release` | existing repo/deploy authority + support tools | READY_SUPPORT |

Legacy aliases `vector-design`, `video-edit`, and `video-finish` remain for compatibility. `video-edit` and `video-finish` inherit Resolve's `PARTIAL_TYPED_AUTOMATION` state until bounded timeline authoring and master-render job operations are accepted.

## Fabrication commands

- `fabrication-status`: run canonical Fabrication verify/doctor plus CAD doctor.
- `fabrication-route --request "<request>" [--file <path>]`: delegate intent selection to `vf_fabrication_router.py decide`.
- `fabrication-dfam --input <mesh> [--angle-limit <deg>]`: run fact-only local DfAM analysis and bind the receipt to the input artifact.
- `fabrication-slice --input <mesh> --printer <h2d|u1|ecc2|c5|c5pro> --output <path> [--execute]`: default to dry-run. `--execute` only generates/validates local G-code; it never performs printer I/O.

## Existing direct typed commands

`fusion-box`, `meshmixer-review`, `mesh-technical-sheet`, `corel-craft`, and `topaz-enhance` remain backward compatible. Run the relevant status/plan gate first.
