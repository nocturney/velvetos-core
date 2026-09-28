# vfprod — רצפה + מהנדס הדפסה

מושב: ייצור. מכיל גם כדאיות (מהשיתוף) וגם תור ההדפסה. לא פק שני.

לפני התחייבות ללקוח: `hq/PLAYBOOK.md`.  
פריפלייט STL: `PREFLIGHT.md` · `python3 scripts/vf_office.py print preflight`.  
רצפה: `FLOOR.md` · ניתוב חומר→מיטה: `ROUTING.md` · `python3 scripts/vfprod.py route`.  
אחרי הדפסה תקינה: `PRINT-DONE.md` (כרטיס → טיוטת תוכן, לא Publish אוטומטי).  
תביעות חומר: `CLAIMS.md`. מפעל תוכן: `vfgrowth/ORGANIC-GROWTH.md`.  
בריף: `python3 scripts/vfprod.py brief` + `python3 scripts/vfprod.py print-done`.  
תחזוקה מונעת: `MAINTENANCE.md` · `python3 scripts/vfprod.py maintain`.
דשבורד חווה עתידי (Watchtower): `WATCHTOWER.md` — Edge על LAN שדרות, לא daemon בליבה.  
CAD/fabrication routing: `FABRICATION-ROUTER.md` → `TEXT-TO-CAD.md` · natural request: `python scripts/vf_fabrication_router.py decide --request "<request>"` · resolved route: `route --intent <intent>` · host: `python scripts/vf_cad.py doctor`.
3D modeling-engine routing תחת Fabrication Router: `BLENDER-MCP.md` · `python scripts/vf_3d.py route --request "..."` · `python scripts/vf_3d.py doctor`.
Open expert capability graft: `SCENARIO-EXPERT-CAPABILITIES.md` · `python scripts/vf_blender_expert.py plan --request "..."`; this is local/provider-neutral knowledge and does not require Scenario MCP/subscription.
גרסאות כלי 3D/slicer אינן allowlist: משתמשים במה שמותקן בפועל, מאמתים capability/acceptance, ושומרים גרסה/commit רק כ־provenance ב־receipt.
3D AI Studio נשאר יכולת אופציונלית בלבד: `3DAISTUDIO.md` · `CONNECT-3DAI.md`; אין להסלים אליו כאשר המסלול המקומי מספיק, ואין שימוש בתשלום בלי סמכות עלות מפורשת.
אחרי אישור רצפה: תור על הצינור `הדפסה`.
רישיון קובץ: `#vlicense`.

## Fabrication tool routing

For every CAD, 3D-model, manufacturability, drawing, DXF, slicing, G-code or robot-description request, resolve `FABRICATION-ROUTER.md` before execution. Use the smallest required tool chain; do not invoke every installed skill.

When the router selects an upstream text-to-cad skill, read the pinned project copy at `.agents/skills/<skill>/SKILL.md` and follow that skill. In ChatGPT/HQ sessions where project Skills are not natively discoverable, use the same pinned file as the execution authority through the authorized host. Do not reimplement a selected skill from memory when its pinned instructions are available.

Native reasoning/vision may win when no exact engineering artifact is required. Deterministic geometry, measurement, CAD review and manufacturing files must use the specialized route. `bambu-labs` and all printer-control/upload/start actions are excluded.

## מומחה — 3D model analyze / make / build

מודול: `expert-3d-model` · `experts/3D-MODEL.md` · `@technical-artist` + `@studio-producer`

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. For 3D routing run `python scripts/check-vf-3d-router.py`; for a live host also require `python scripts/vf_3d.py doctor` and the applicable geometry gate. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.
