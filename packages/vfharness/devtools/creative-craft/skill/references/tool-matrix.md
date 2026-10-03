# Tool matrix

The final registry contains 38 routable tools/capabilities. Availability is evaluated through the appropriate gate: DCC Update Sentinel, accepted Phase 2 candidate evidence plus deployed adapter hash, verified runtime state, support CLI/file presence, or the configured Fabrication authority.

## Engineering / 3D

| Tool | Accepted surface | Important limit |
| --- | --- | --- |
| Fabrication Router | route/status/DfAM/local slice+validate | owns internal engine/slicer choice; no printer I/O |
| Fusion | read/electronics + bounded new box -> STL/STEP | no generic geometry write or existing-document mutation |
| Meshmixer | probe/list/info/import/screenshot | review-oriented; no generic mm-api stream |
| Blender / 3ds Max | accepted DCC surfaces | standardized job-owned turntable contract remains a gap |
| Maya | accepted DCC surface only while Sentinel is healthy | fail closed on compatibility-repair state |
| AutoCAD / Inventor / ZBrush | accepted DCC surfaces | no arbitrary agent scripting |
| OpenSCAD Nightly | typed SCAD -> STL/3MF CLI | latest-compatible Nightly with post-update smoke |
| Substance Painter / Designer | accepted DCC/material surfaces | cross-app material orchestration remains partial |

## Image / vector / publication

| Tool | Accepted surface | Important limit |
| --- | --- | --- |
| Photoshop | version/active/read-only batchPlay + temporary-doc cycle | bounded finishing authoring/export remains a typed gap |
| Illustrator | accepted read-only surface | vector authoring/export typed gap |
| CorelDRAW / DESIGNER | typed composition/import/CDR/PDF | no Evaluate/VBA/GMS/generic COM |
| PHOTO-PAINT | typed raster COM adapter | no generic COM/VBA |
| Affinity | probe/status/render-current | broader authoring/export remains limited |
| InDesign | typed title/body -> IDML/PDF | place/link/styles/preflight/package/presets remain gaps |
| Acrobat | typed PDF inspection | deeper prepress inspection remains limited |
| XVL Studio Corel | XVL -> editable CDR/PDF | direct XVL Player SDK is optional/unavailable |
| XVL HTML5 | bundled xvlgenhtm -> HTML5 package | no claim of full XVL SDK |

## Video / motion / speech

| Tool | Accepted surface | Important limit |
| --- | --- | --- |
| Resolve | media/timeline/project-settings/render/LUT | narrower subtitle/Fairlight/node operations remain gaps |
| Topaz Video | accepted ahq-12, scale 1/2/4 | no automatic model download or arbitrary ffmpeg args |
| HyperFrames | verified local doctor/render | no publish authority |
| Fusion Studio | bounded official scripting acceptance/render-solid | broader job-owned comp operations remain gaps |
| After Effects | typed read surface | bounded authoring/render remains limited |
| Premiere Pro | first-party limited surface | real timeline authoring remains a typed gap |
| Media Encoder | Watch Folder h264-high + job status | additional named presets required |
| Manim | verified local 0.21.0 smoke | declarative wrapper required; no arbitrary agent Python |
| VoiceStudio/OmniVoice | TTS/ASR/back-transcription QA | cloning requires consent; subtitle/timing wrapper remains a gap |
| ffmpeg/ffprobe | deterministic probe/verification | no arbitrary user filtergraph through Creative Craft |

## Spatial / documents / support

| Tool | Accepted surface | Important limit |
| --- | --- | --- |
| SketchUp | official headless C API | spatial authority, not manufacturing CAD |
| LayOut | official headless C API save/PDF | spatial/documentation authority |
| Office Word/Excel/PowerPoint | typed InteractiveToken workers | Outlook/email excluded; no generic COM/macros |
| gcloud | read/describe/logs and explicitly authorized deployment | no silent project/IAM/paid-resource changes |
| GitHub CLI | local-repo-aware support | prefer connected GitHub authority when appropriate |
| 7-Zip | deterministic archive/test/extraction proof | no source deletion or SFX by default |

## Inventory-only and exclusions

Sampler 6.0.3, Modeler 1.22.7.1239, Stager 3.1.8, ElegooSlicer 1.5.3.5, and Flash Studio 1.7.18 remain inventory/reference only.

Exclude Rainmeter, Plex Media Server, NVIDIA Broadcast, Brother scanner/PC-FAX, ASUSTOR tools, Outlook, Topaz Gigapixel, and Cinema 4D.

Never attach to or close a pre-existing user GUI session. Any non-available DCC route, missing/unaccepted/hash-mismatched candidate, failed state receipt, missing support binary, or missing authority file fails closed for that capability.
