# OpenPost Release Watch

Read `automation/antigravity/CONTRACT.md`, current `packages/vfigos/OPENPOST.json`, `OPENPOST.md`, release authority and delivery-approval authority.

Check current upstream OpenPost release state against the repository baseline. No-change is a valid silent result. Never treat OpenPost as creative authority or as a bypass around signed delivery approval/live verification.

In shadow mode: perform read-only release comparison and return `SHADOW_PASS` with current baseline/upstream evidence, or `SHADOW_BLOCKED`. Do not update files, branches, runtime, or owner surfaces.
