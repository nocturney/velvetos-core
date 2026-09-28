# 3D Model — מנתח / יוצר / בונה

מושב: ייצור. מודול: `expert-3d-model`.  
לפני כל משימת CAD/ייצור יש לפתור `../FABRICATION-ROUTER.md` ולקרוא את ה־Skill שנבחר מ־`.agents/skills/<skill>/SKILL.md` כאשר קיים route כזה.
אין שליטה/שליחה למדפסת מ־HQ. אין מפתח API בגיט. ברירת המחדל היא local / zero-new-recurring-cost.

## Fabrication Router → 3D sub-router

Fabrication Router הוא שער העל לבחירת כלי הייצור. כאשר הוא מפנה למשימת מידול 3D, בקשת המידול עוברת דרך:

```bash
python scripts/vf_3d.py route --request "<owner request>"
```

ה־router מחזיר אחד משלושה מסלולים קנוניים:

- `TEXT_TO_CAD` — CAD פונקציונלי פרמטרי, מידות, tolerances, holes, fits, STEP/B-rep.
- `BLENDER_NATIVE` — אורגני/סקלפטורלי, reconstruction מרפרנסים, mesh קיים, refinement/repair.
- `HYBRID_CAD_THEN_BLENDER` — ממשקים/מידות פונקציונליים נשמרים ב־STEP, ואז מעטפת/צורה אורגנית ב־Blender.

אין לבחור Blender רק כי הוא יודע ליצור 3D; master הנדסי שנדרש להיות פרמטרי נשאר CAD.

ה־Fabrication Router מכסה גם CAD פונקציונלי, `step-parts`, `cad-viewer`, `dfam-check`, `dfm`, `dxf`, `engineering-drawing`, `gcode`, `urdf`/`srdf`/`sdf` ו־SendCutSend preflight בלבד. `bambu-labs`, printer upload/start/heating/motion ו־SendCutSend order submission נשארים מחוץ לסמכות.

גרסאות runtime אינן נעולות. `vf_3d.py doctor` בוחר את Blender המותקן בפועל ומאמת את ה־addon באותה התקנה; `vf_cad.py` מגלה OrcaSlicer מקומית. גרסה/commit מדויקים הם provenance של בדיקה, לא רשימת גרסאות מותרות. אחרי upgrade דורשים evidence חדש התואם לגרסה המותקנת במקום לדחות אותה לפי מספר גרסה.

## Analyze

קלט: קובץ / Drive / תמונות / תיאור.

1. קבע דרישות פיזיות, מידות, interfaces, חומר/שימוש כשיש מקור.
2. נעל unknowns במקום להמציא.
3. אם יש מקור ויזואלי, התייחס אליו כ־geometry/reference evidence ולא כהיתר לשינוי פונקציונלי.
4. נתח printability: manifold, wall thickness, overhang/support, clearances, orientation.
5. מחיר/זמן/חומר מסחריים רק ממקורות הקנוניים הקיימים.

## Make / Build

### TEXT_TO_CAD

`TEXT-TO-CAD.md` → STEP master → STL/3MF sidecars → DfAM → Orca dry-run.

### BLENDER_NATIVE

`BLENDER-MCP.md` → hardened local `blender-ai-mcp` for bounded modeling/measure/assert.
Use `design-os-3d-blender` for headless passes and evidence-first geometry/print gates.
Then apply `packages/vfprod/SCENARIO-EXPERT-CAPABILITIES.md` and run
`python scripts/vf_blender_expert.py plan --request "<resolved request>"` to select the
minimum expert domains and stage gates. This is open workflow knowledge, not a Scenario
runtime dependency.

When external AI mesh generation is genuinely part of the job, prefer the already-integrated
3D AI Studio capability and treat its Meshy/Tripo-family output as a candidate mesh. Materialize
the file + provenance, then audit/repair/retopologize it locally before any production/print claim.
Do not add a parallel Scenario/Meshy/Tripo account merely because an upstream expert guide names it.

Workflow patterns adopted from `cc-blender-skill` include source manifests, contour/orthographic registration,
multiview correction, fit repair and quality loops. Its Claude runtime is not a VelvetOS dependency.

### HYBRID_CAD_THEN_BLENDER

1. Build and verify functional skeleton/interfaces in Text-to-CAD.
2. Freeze dimensions/mating surfaces as protected constraints.
3. Transfer a derivative mesh/reference to Blender for non-critical organic refinement.
4. Re-measure protected interfaces after Blender work.
5. Keep STEP as engineering source of truth; BLEND is the appearance/form source.

## Verification

For Blender work, use deterministic measures/assertions before visual judgement where possible.
A digital gate PASS proves only the checked geometry. It does not prove real fit, material behavior or successful printing.

Minimum handoff for printable work:
- editable master: STEP and/or BLEND according to the routed contract;
- STL/3MF sidecars;
- geometry/print gate report;
- slicer dry-run against the existing `printer_matrix.json`;
- license/source provenance;
- no physical printer action from HQ.

## Cost / provider boundary

Local Blender/Text-to-CAD is preferred. External AI model generation, Premium, Hyper3D, Hunyuan3D,
Meshy/Tripo or similar services are not fallback-by-convenience. They require the applicable cost/license gate
and explicit authority when a new or usage-based charge is possible.

## Specialists

- `@technical-artist` — mesh/form, reconstruction, cleanup, export.
- `@studio-producer` — print-floor handoff only.
- `@legal-compliance-checker` — source/license gate.

## Learning loop

Record failures as actionable geometry/router lessons, not provider folklore. If routing itself was wrong,
add a regression case to `scripts/check-vf-3d-router.py`; do not create a second router.
