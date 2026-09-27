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
CAD/DfAM/slicing מקומי: `TEXT-TO-CAD.md` · `python scripts/vf_cad.py doctor`.
3D routing מקומי: `BLENDER-MCP.md` · `python scripts/vf_3d.py route --request "..."` · `python scripts/vf_3d.py doctor`.
3D AI Studio נשאר יכולת אופציונלית בלבד: `3DAISTUDIO.md` · `CONNECT-3DAI.md`; אין להסלים אליו כאשר המסלול המקומי מספיק, ואין שימוש בתשלום בלי סמכות עלות מפורשת.
אחרי אישור רצפה: תור על הצינור `הדפסה`.
רישיון קובץ: `#vlicense`.

## מומחה — 3D model analyze / make / build

מודול: `expert-3d-model` · `experts/3D-MODEL.md` · `@technical-artist` + `@studio-producer`

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. For 3D routing run `python scripts/check-vf-3d-router.py`; for a live host also require `python scripts/vf_3d.py doctor` and the applicable geometry gate. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.
