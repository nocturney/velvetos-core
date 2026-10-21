# Skill capability pilot — 2026-10-20

Evidence within the existing Office v2 Candidate Registry and Golden Fixture process; no second registry, admission, installation or production authority.

**Upstream:** https://github.com/plugin87/ux-ui-agent-skills (MIT), v2.10.0 at commit 55156b40e3a9aafa52448bde76cdcb5147b958db. All 26 upstream skills are independent RESEARCHED candidates, not globally installed.

| Actual use case | Incumbent(s) | Challenger(s) | Evidence and comparison outcome |
| --- | --- | --- | --- |
| SliceBridge compact desktop: source file details, thumbnails of target printers, both panes visible with minimal scroll | vf-web-ui-quality, ux-architect, ui-finish-gate-reviewer and SliceBridge window sizing | redesign, design-review, verify_screen_economy.mjs, verify_overflow.mjs | Potentially complementary viewport/overflow measurements; plugin87 browser gates require an HTML/Playwright adapter for Electron/Wails. No actual screenshot QA has been completed. |
| Office 2.0 dashboard: hierarchy, RTL, responsive, state variations | ui-designer, ux-architect, existing engineering-quality sensor and Impeccable wrapper | design-qa, gate, design-tokens, data-dashboard | Add state-aware token/contrast/RTL fixture checks if they provide measurable gain; local product contracts remain authoritative. |
| Product-specific adversarial critique | ui-finish-gate-reviewer | critique and design-critic | Two complementary reviews are possible: product-context critique then independent blind artifact critique. Forked-context behavior is Claude-specific, requiring an adapter; no claim of equivalent fork for other agents. |
| Accessibility | accessibility-auditor (manual screen reader and keyboard required) | a11y-audit, design-qa | Complement standards-linked automated findings with real assistive-technology testing. Never claim automated-only accessibility compliance. |
| Component/tokens | Impeccable (pinned 9d715cc4) and ui-designer | apply-aesthetic, design-component, token-build | Evaluate same resulting UI with identical fixtures; do not replace by reputation, novelty, or overlap. |

## Executable evidence, not subjective UX scores

- Upstream pinned source checkout: node mcp/server.mjs --selftest → 25/25 PASS; npm test → PASS on upstream fixtures. Real-render browser checks were not proven here.
- SliceBridge open PR #13 at 986161df3cdc9485e71bda2bbcd9a4bcd877dab7, isolated source checkout and **no edits**: node --test tests/window-sizing.test.js → 6/6 PASS; python3 -m unittest discover -s catalog/tests -p test_picker_ui.py → 4/4 PASS.
- Running the broader Mac IPC suite reported failure because bin/bridge-core.exe (the Windows engine helper) was absent from the isolated checkout; this is not evidence of an actual UI defect.
- The existing SliceBridge notes still require real Wails UI screenshots and interactions at 1100×830 and shorter window heights. Neither code inspection nor the upstream selftests replace that.

## Next controlled fixture

Use one source 3MF with multiple filenames and four printer targets. At fixed compact desktop sizes, measure visible file-detail rows, target printer photo/fallback count, source/destination panel reachability, scrolling, tab-focus order, light/dark/RTL states, and post-change behavior. Evaluate incumbent-only vs challenger-assisted implementations with the same artifacts and independent QA. Do not change or merge SliceBridge PR #13 without its own process.

## Non-UX control lane

CAD/OpenSCAD routing finds vf-cad-design-craft, vf-3d-router, cad, cad-viewer and vf-cli-anything-cad without injecting UX-only plugin87 skills. This is a routing regression, not a quality comparison of actual meshes. Next fixture: one OpenSCAD reference solid, dimension/bounding-box checks, watertight validation and independent mesh inspection.

**Admission discipline:** All candidates remain discoverable for revisiting; no winner, runtime availability, successful execution, paid API, replacement, or production capability is inferred from retrieval alone.
