---
name: creative-craft
description: Route and execute natural-language production requests across the approved VelvetOS fabrication/CAD/3D, technical-illustration, image/vector, material/lookdev, video/motion/speech, spatial-design, Office/document, and packaging/ops stack. Use automatically for ordinary chat requests that can benefit from these local workstation tools, including requests naming Maya, Blender, Fusion, Adobe, Corel, Resolve, SketchUp, Office, slicers, or related workflows. Choose the existing authority and specialist Skill, use the connected workstation execution transport, check live compatibility gates, execute only bounded typed operations, preserve user sessions and product/engineering truth, require file-backed QA receipts, and report typed gaps instead of inventing unsafe execution paths.
---

# Creative Craft

Treat Creative Craft as the upper-level production router. Keep existing authorities authoritative; do not turn this Skill into a second Fabrication Router, Visual Foundry, Media Vault, publishing gate, or tool-specific scripting layer.

## Chat execution transport

In ChatGPT, treat the connected Remote Desktop Commander workstation as the execution transport for the local VelvetOS stack. Do not assume Windows paths such as `D:\Velvet` are mounted directly into the chat runtime.

- For an ordinary natural-language request, trigger Creative Craft automatically; do not require the user to name this Skill, the router, MCP, CLI, or a local path.
- Run the Creative Craft router on the authorized workstation through Remote Desktop Commander.
- If the user explicitly names a local application, preserve that preference when it does not conflict with the selected authority or a failed compatibility gate.
- Before using a DCC host, check `status --tool <id>`. When the host is required and not already running, use `host --tool <id> --action start`; never open a visible GUI merely to satisfy an automation request when an accepted hidden/headless route exists.
- Execute only a typed operation exposed by the selected authority/adapter. If the requested operation is not yet exposed, report the typed gap instead of falling back to arbitrary shell, Python, COM, Lua, eval, or unrestricted MCP calls.
- Verify exact files/readbacks/receipts after execution. Stop only an agent-owned host when cleanup is appropriate; never close a pre-existing user session.
- If Remote Desktop Commander is not connected or authorized, fail closed for local execution and ask the user to connect it. Planning/explanation may still proceed without pretending execution happened.

Read `references/chat-activation.md` when the request originates as a normal chat instruction rather than an already-resolved low-level operation.

## Workflow

1. Route the request at the highest useful level:
   `C:\Python314\python.exe D:\Velvet\Runtime\CreativeCraft\CreativeCraftRouter.py route --request "<request>"`
2. If the intent is already known, inspect it directly with `plan --intent <intent>`.
3. Read the returned authority, specialist Skills, readiness, required/optional tools, typed gaps, expected artifacts, QA, and cleanup policy.
4. Stop automatic execution when status is `BLOCKED`. A partial readiness label is not a failure; execute only operations explicitly exposed by the accepted surface and report the listed gap for anything else.
5. Load only the specialist Skill(s) named by the plan. Do not copy their craft guidance into Creative Craft.
6. Execute through the selected existing authority or typed adapter. Preserve all upstream source/product/engineering facts.
7. For quality-critical, repeatable or cross-specialist work, read `references/creative-qa-engineering.md` and define the comparison/acceptance evidence before final review. For significant specialist changes, also apply `references/skill-authoring-standard.md` and the bundled `evals/` contract.
8. Verify exact outputs, hashes/readbacks, stage receipts, and cleanup before returning the result. A render/tool receipt never authorizes publication.

## Authority boundaries
- Fabrication requests delegate to `packages/vfprod/FABRICATION-ROUTER.json`; never choose CAD engines, slicers, or printer profiles around it.
- Public Velvet creative work remains under `vfom` / `velvet-creative-director` and the existing review/publish gates.
- Engineering/CAD/XVL source remains geometry truth for technical media and publications.
- Derivative/transcode workflows inherit an approved file-backed master and do not create new creative approval.
- Support tools such as gcloud, gh, and 7-Zip remain subordinate to existing deployment/repository authority.

## Typed control surfaces

Use `fabrication-status`, `fabrication-route`, `fabrication-dfam`, and `fabrication-slice` for the canonical fabrication subsystem. Local slicing defaults to dry-run; `--execute` may only generate and validate local G-code.

Keep the backward-compatible direct commands `fusion-box`, `meshmixer-review`, `mesh-technical-sheet`, `corel-craft`, and `topaz-enhance` for their already accepted bounded operations.

For accepted Phase 2 adapters (InDesign, PHOTO-PAINT, Fusion Studio, Office, Acrobat, SketchUp/LayOut, Media Encoder, XVL), follow the named pipeline and adapter contract. Never substitute raw COM, Python/Lua, generic GUI control, or unrestricted scripting when a typed operation is missing.

## Safety

- Preserve pre-existing user sessions; stop only processes owned by the current job.
- Fail closed on unavailable DCC routing, candidate hash mismatch, failed runtime-state receipt, missing CLI, or missing authority files.
- Never overwrite outputs by default.
- Never weaken integrity/signature/licensing/security checks.
- Never control a physical printer, upload/start/pause/cancel a print, heat, or move hardware.
- Never auto-publish, send unapproved email, incur unapproved cloud spend, or invent product/engineering facts.
- Keep arbitrary raw script execution disabled.

## References
Read `references/tool-routing.md` for domain selection, `references/pipelines.md` for router commands and pipeline readiness, `references/tool-matrix.md` for accepted/blocked surfaces, `references/creative-qa-engineering.md` for golden/reference states and regression evidence, `references/skill-authoring-standard.md` when changing specialist craft, and `references/corel-craft-spec.md` only when authoring a Corel typed job.
