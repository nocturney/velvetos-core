---
name: vf-prepress-qa
description: Verify professional print-production output across InDesign, Acrobat, Illustrator, CorelDRAW, Corel PHOTO-PAINT and Affinity workflows. Use for printer handoff, PDF/X or print PDF export, bleed, links/fonts, spot/process color, overprint, separations, ink coverage, image resolution, page-box or packaging checks. Printer/provider specifications override generic defaults; this skill adds QA and never invents a print specification.
---

# Velvet Prepress QA

Use this skill when the deliverable is intended for physical print or a print provider requires production-ready files.
Do not assume social/web export rules apply to print.

## Workflow

1. Obtain the printer/provider specification when available. Treat it as the authority for bleed, profile, PDF standard, ink limits, marks and packaging.
2. Read the relevant references: `preflight.md`, `color-overprint.md`, `color-output-qa.md`, `pdf-output.md`, `tool-routing.md`.
3. Run document/application preflight before export and repair critical issues at the source.
4. Export the exact requested print artifact using the provider preset/specification or a documented fallback.
5. Re-open and inspect the exported PDF/file rather than trusting the source document state.
6. Record unresolved provider-dependent questions instead of guessing.

## Hard stops

- Do not claim that one PDF/X flavor, one bleed value, CMYK conversion or one ink limit is universally correct.
- Do not package or redistribute fonts without checking the font license/embedding rights.
- Do not assume 100% black overprint behavior is appropriate for every object or workflow.
- Do not use a screen preview as proof of trapping or press behavior.
- Do not overwrite the editable source when producing a delivery artifact.

## Completion contract

Report: `source_preflight_passed`, `links_fonts_checked`, `color_separations_checked`, `bleed_boxes_checked`, `pdf_exported`, `export_reopened`, `provider_spec_satisfied`.