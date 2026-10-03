# Creative Craft 2.0 architecture

## Control flow

```text
ChatGPT / owner request
        |
        v
Creative Craft
(high-level domain + workflow routing only)
        |
        +--> public Velvet creative
        |      vf-content-sprint -> velvet-creative-director / vfom
        |      -> specialist craft Skill -> accepted local execution surface
        |      -> exact-final QA -> existing review/publish gates
        |
        +--> fabrication / engineering
        |      canonical vfprod Fabrication Router
        |      -> vf-3d-router / CAD / DfAM / engineering-drawing / slicer
        |      -> artifact/readback/validation receipts
        |
        +--> technical media / publications
        |      engineering or file-backed source authority
        |      -> XVL/Corel/InDesign/Acrobat/SketchUp/LayOut/Office as bounded
        |      -> exact output QA
        |
        +--> media / speech
        |      HyperFrames / Resolve / Fusion / Topaz / Manim / VoiceStudio
        |      -> named bounded operation -> probe/QC receipt
        |
        +--> support operations
               existing repo/deployment authority
               -> gcloud / gh / 7-Zip as bounded support tools
```

Creative Craft is never the source of Product Truth, brand truth, engineering geometry, publish authorization, ledger/BOM facts, or physical-printer authority.

## Layers

| Layer | Responsibility | Authority / evidence |
| --- | --- | --- |
| Request routing | choose only the high-level production workflow | Creative Craft registry + `route` |
| Creative authority | public creative decisions and existing approval flow | vfom / Creative Director / current review gates |
| Fabrication authority | internal CAD/3D/DfAM/slicer chain | `packages/vfprod/FABRICATION-ROUTER.json` |
| Craft method | professional method, constraints, QA | specialist Skills |
| Execution | accepted typed/bounded adapters and local runtimes | DCC adapters, candidate adapters, CLIs, state receipts |
| Availability | fail-closed permission to auto-route | Update Sentinel, accepted candidate hashes, runtime state, authority hashes |
| Artifact truth | exact produced file + provenance | SHA-256/readback/probe/inspection receipts |
| Physical/publish boundary | owner/existing authority only | printer I/O disabled; render receipt != publish authorization |

## Capability families

| Family | Principal production surfaces |
| --- | --- |
| Fabrication/CAD | Fabrication Router, Fusion, AutoCAD, Inventor, OpenSCAD, Meshmixer, Blender/3ds Max/Maya/ZBrush where accepted |
| Materials/3D | Substance Painter/Designer, Blender/DCC material lookdev |
| Product visualization | Product Visualization craft over accepted DCC/render surfaces; consumes geometry/material truth |
| Image/vector | Photoshop, CorelDRAW, PHOTO-PAINT, Illustrator, Affinity |
| Technical publication | XVL Studio Corel, Corel DESIGNER, InDesign, Acrobat, XVL HTML5 |
| Spatial planning | SketchUp + LayOut |
| VFX/compositing | VFX Compositing craft over accepted Resolve/Fusion/After Effects surfaces |
| Video/motion/post | HyperFrames, Resolve, After Effects, Premiere, Media Encoder, Topaz Video, Manim |
| Speech | VoiceStudio/OmniVoice + faster-whisper QA |
| Documents/BOM | Office Word/Excel/PowerPoint typed workers |
| Support | ffmpeg/ffprobe, gcloud, gh, 7-Zip |

ElegooSlicer 1.5.3.5 and Flash Studio 1.7.18 remain vendor-profile/reference candidates, not routing authorities. Sampler/Modeler/Stager are inventory-only. Owner exclusions remain non-routable.

## Runtime source pointer

The final router reads `D:\Velvet\State\CreativeCraft\authority-roots.json`. Phase 2 currently points the Fabrication authority to the accepted worktree because the canonical main checkout has not been merged. Critical files are SHA-256 pinned. Switching the pointer to main is allowed only after an explicit merge/deployment preserves the accepted behavior and hashes are re-baselined through validation.
