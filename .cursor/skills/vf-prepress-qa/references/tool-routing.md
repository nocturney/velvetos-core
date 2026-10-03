# Prepress tool notes

- InDesign: use live Preflight, Links, Package and Adobe PDF (Print) export when the source is InDesign. Current Adobe docs explicitly support preflight profiles, packaging linked assets/fonts and PDF/X presets.
- Acrobat: use for inspecting the exact exported PDF, page boxes, fonts, output preview/separations and other final-artifact checks available in the installed edition.
- Illustrator: use document/output checks for vector artwork and packaging/export where Illustrator is the source authority.
- CorelDRAW/Corel PHOTO-PAINT: use equivalent preflight/color/export checks when the native source lives in Corel; do not force an Adobe round-trip solely for QA.
- Affinity: use its native preflight/export path when the source is an Affinity document; verify the resulting PDF independently.