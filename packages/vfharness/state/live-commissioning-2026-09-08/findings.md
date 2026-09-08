# VelvetOS Live Commissioning Evidence — 2026-09-08

## Sensors
- `python3 scripts/check-all.py` → **34/34 PASS** (before and after fixes)

## Media Vault production proof
- Drive inbox `01 - נכנס` scanned: ≥399 real phone uploads (HEIC/JPEG/MOV/MP4/PNG)
- Catalogued into single SoT `packages/vfmedia/catalog.json` (399 items)
- Viewed sample `IMG_0911.JPG` (Velvet Factory logo) downloaded + described honestly
- Moved to `02 - מקור` via Drive `update_file` (parentId proof)
- No SKU/job association invented from filenames
- Upload ≠ approval preserved (`versionApproval.state=none`)

## WIP→Finished
- `vf_control_plane.py selftest` PASS (defensible_match, no-media, close-only-on-live rules)
- `check-production-content.py` PASS
- Canonical store: `office/control/followups.json`

## Instagram
- CAPABILITIES `currentStatus=needsAuth` (not faked ready)
- Meta app `1748471159829574`: admin access via DevTools MCP; `contact_email_verified=false`; `app_status=dev_mode`
- No Metricool/Publer/Suite dependency added

## Failover
- `simulate --scenario failover` documents Manager B path via existing HANDOFF
- HANDOFF refreshed with media counts + safe_for_next_ai commands

## Morning Brief
- `vfops_loop.py brief --write` generated from truth sources
- Gmail send preflight: `no token` exit 2 (not claimed sent)

## PR hygiene
- #125/#126/#127: draft best-skills pulses; unique `writing-plans.md` extracted into this branch; mark superseded/close
