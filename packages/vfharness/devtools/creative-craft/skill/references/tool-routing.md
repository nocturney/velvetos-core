# Tool routing

Creative Craft chooses the domain/workflow. The selected existing authority chooses its own internal engine or sub-route.

| Request family | Pipeline | Authority / primary route |
| --- | --- | --- |
| Printable CAD, reference reconstruction, STL repair, engineering drawing, slicing | `fabrication` | canonical vfprod Fabrication Router |
| CAD read/inspection | `cad-inspect` | Fusion accepted read surface |
| Mesh inspection | `mesh-review` | Meshmixer controlled review |
| Product/raster finishing | `product-image-finishing` | Photoshop primary; PHOTO-PAINT bounded alternative |
| Vector/logo/layout | `vector-logo-layout` | CorelDRAW; vfom/Brand Guardian owns Velvet brand decisions |
| CAD/XVL technical illustration | `technical-illustration` | XVL Studio -> Corel DESIGNER; Acrobat inspection |
| PBR/material/lookdev | `pbr-material-pipeline` | Substance Painter/Designer + destination DCC |
| Product turntable/visualization | `3d-turntable-product-visualization` | Blender by default |
| Short social/motion | `short-social-video` | vfom + HyperFrames; speech/Fusion optional |
| Long editorial/color/finish | `long-edit-heavy-video` | DaVinci Resolve Studio |
| Video restoration/upscale | `video-enhancement` | Topaz Video when justified |
| Hebrew narration/subtitles | `hebrew-narration-subtitles` | VoiceStudio/OmniVoice + ASR QA |
| Semantic technical animation | `technical-explainer-animation` | Manim + optional bounded finishing |
| Engineering publication | `engineering-technical-publication` | XVL/Corel -> InDesign -> Acrobat |
| Delivery derivatives | `reusable-derivative-export-factory` | Media Encoder named preset + ffprobe |
| Spatial/installation planning | `spatial-planning` | SketchUp C API + LayOut C API |
| Word/Excel/PowerPoint/BOM | `document-report-bom` | typed Office workers |
| Release/archive/cloud support | `ops-package-release` | existing authority + gh/gcloud/7-Zip |

## Decision rules

1. Preserve Product Truth, engineering geometry, brand/copy authority, and publish authority.
2. Prefer one capable bounded tool; use multi-tool pipelines only for a clear file-backed handoff.
3. Use Manim for semantic technical animation, HyperFrames for deterministic template/social composition, standalone Fusion for reusable node comps, Resolve Fusion for timeline-local comps, and After Effects only where a bounded authoring surface exists.
4. Use Topaz only for a diagnosed enhancement need and compare against the source/master.
5. Treat Media Encoder as a derivative factory only through named accepted presets; currently `h264-high` is accepted.
6. Run GUI/COM candidates through their accepted InteractiveToken lifecycle; Session-0 diagnostics are not production routes.
7. If `route` returns `BLOCKED` with `no_intent_match`, resolve the high-level intent from request context; do not invent a lower-level execution path.
8. If a plan lists typed gaps, execute only the accepted operations and surface the relevant gap when the requested operation exceeds them.
