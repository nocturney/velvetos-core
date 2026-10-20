# Office v2 — UI ecosystem source intake & comparative pilot (2026-10-20)

**Status:** SOURCE-CATALOG-IMPLEMENTED / ISOLATED-CODE-QA-PASS / SLICERBRIDGE-CHROMIUM-LAYOUT-PASS-WITH-SCROLL-OBSERVATIONS / NATIVE-WINDOW-AND-XIAS-GATES-NOT-PROVEN. No installation, merge, publication or production behavior change.

## Why this is a supplement, not another registry

- The 42 URLs from the owner's Facebook post are preserved exactly in [ui-ecosystem-sources-2026-10-20.json](ui-ecosystem-sources-2026-10-20.json). Intake breakdown: **1 Skill directory, 18 component references, 8 motion/animation references, 11 inspiration/icon references, 4 design-system references**.
- They are *source-only* discovery candidates. `scripts/vf_skill_catalog.py` (created by upstream draft PR #921) remains the **single shared search/comparison entry point**. Use `sources`, `source-search <query> [--stack <framework>]`, `compare <query>`, `plan <query>`, and `audit`. No second Skill/Control Plane registry is created.
- Skills, libraries, animation engines, icon sets, design guidelines and inspiration are **different resource kinds**. References must never appear as executable Skills in `route` or gain installation, production-writer, credential, paid provider or runtime authority. The resource manifest is provenance-only; the Office v2 Candidate Registry retains its own admission policy for actual skill/runtime challengers.
- `ui-skills.com` itself is a directory with CLI/MCP. The site's MIT repository license does **not automatically license third-party Skills** listed in its registry. Source selection uses the smallest task-relevant set; importing all fetched instructions at once is unnecessary.

## Existing internal coverage vs. challenges

| Role / fixture | Existing coverage | Challengers or complements | Compared contribution | Disposition |
|---|---|---|---|---|
| UI architecture, tokens and RTL | `vfbriefux/hq/UI-SYSTEM.md`, UI/UX Pro Max | XIAS design tokens + design-system interoperability; OpenDesign/Material 3 | XIAS is deeper on mechanical component/token generation; internal contract is authoritative for Hebrew, brand, data truth, responsive behavior | COMPARE; do not replace authority |
| UI quality and anti-generic treatment | `vfbriefux/hq/UI-AUDIT.md`, Hallmark, Taste, pinned `vf-web-ui-quality`/Impeccable | XIAS 52 asserted objective gates; UI Skills `baseline-ui`/`improve-ui` | Complementary: audit taste & task hierarchy versus render/keyboard/WCAG and local source-specific plans | CROSS-TOOL BENCHMARK REQUIRED |
| Source-backed UI implementation | Existing Wails + vanilla HTML/CSS/JS in SliceBridge | 21st.dev, shadcn/ui, Mantine, HeroUI, Ant Design, Headless UI, Preline, Flowbite, daisyUI | React/Angular component catalogs are valuable for reference but not automatically suitable for a vanilla desktop webview; prefer existing app primitives until a stack change is justified | REFERENCE / CONDITIONAL |
| High-character components | Existing Velvet tokens + CSS primitives | Spell, Magic UI, Aceternity, Cult UI, Eldora, Vengence | Candidate for a single distinctive interaction, **not** a global default look | REFERENCE / RIGHTS REVIEW |
| Motion | CSS transitions and reduced-motion policy | Motion, GSAP, Anime.js, LottieFiles, Jitter, Swishy, Animmasterlib, Shaders | Pick runtime engine only when motion complexity requires it; Jitter/Lottie are asset workflows, not substitutes for timeline code | NO NEW RUNTIME IN SLICEBRIDGE PILOT |
| Icons | Existing app-approved icons | Lucide, Phosphor, Iconsax | Test semantic clarity and consistency, not number of glyphs; retain copyright notices in redistributed builds | REFERENCE / ICON PACK REVIEW |
| Flow inspiration | Current user workflows and screenshots | Mobbin, Design Spells, UI.live, Uiverse, Landings.dev, Recent.design, Dark.design, Ripplix | Visual reference only; avoid treating screenshots as reusable copyrighted code or pixels | REFERENCE |

XIAS upstream (plugin87/ux-ui-agent-skills) has 26 source-only candidates already imported in draft #921. The pinned Impeccable wrapper is already subject to `check-engineering-quality.py --strict` and project-specific restrictions. Neither of those constitutes a live head-to-head run on this intake alone.

## Resource licensing and rights, scoped accurately

Verified upstream **scope only**, not full third-party asset clearance:

- **UI Skills** repository: MIT (https://github.com/ibelick/ui-skills/blob/main/LICENSE); third-party skill documents may differ.
- **shadcn/ui** upstream: MIT (https://github.com/shadcn-ui/ui/blob/main/LICENSE.md); copied components and transitive dependencies need their own notices.
- **Motion** library: MIT (https://motion.dev/); premium example access and premium-component terms are separate.
- **Lucide**: ISC plus Feather-derived MIT notice (https://github.com/lucide-icons/lucide/blob/main/LICENSE); preserve full license notices in redistribution.
- **LottieFiles** free public animations: Lottie Simple License (https://lottiefiles.com/page/license), asset-specific, no competing bulk aggregation/scraping; premium and creator-specific asset terms can differ.

**Other 37 entries:** `REVIEW_REQUIRED` — no invented license or commercial approval. Differentiate private exploration, internal development, public showcase, marketing usage, redistribution of source/assets, and downloadable community software. Apple-like design references are not licenses to redistribute Apple's logos/assets.

## Pilot — one real SliceBridge surface, fixed criteria

**Target:** `nocturney/slicebridge`, isolated copy of draft PR #13 `feature/my-printers`, observed source commit `dba4a3b7c786544a6faececb7fdba1d3a3f8f237`, `native/frontend/dist/index.html`, `app.css`, local `native/tests/source-queue-layout-qa.cjs`.

**User task:** With zero, one or two 3MF files and a few target printers, source file details must stay readable; selected targets must remain visible; no clipped dropzone, useless empty-queue scrollbar, offscreen controls, misleading printer conversion status, unneeded scroll or destructive settings migration.

**Shared comparison criteria (apply identically to each future skill/tool benchmark):**

1. Product correctness and no fictional capabilities: only approved legacy adapters; catalog-only machines explicitly unavailable; no automatic manufacturer art redistribution.
2. Measured rendered layout in Hebrew RTL and English LTR at short/medium desktop window sizes and 745/746px responsive boundary; source panel, target panel, and Add Files control never clipped/inaccessible.
3. Keyboard/focus/contrast/target-size/reduced-motion/error/empty/loading checks. Do not count source string presence as rendered accessibility certification.
4. Low default scrolling with 0–2 files; report actual scroll deltas instead of claiming “no scroll” from a CSS rule.
5. License/maintenance/cross-platform cost and compatibility; never add a React/Angular runtime to the vanilla app for reference aesthetics alone.
6. Exact source SHA, commands, outcomes and independent QA. No score without observed tests.

**Runs on isolated MacMiniOffice2.local clone (no production changes):**
- `PYTHONPATH=scripts python3.12 packages/velvetos/living-studio/tests/test_skill_catalog.py`: **25/25 PASS**, covering 5 new UI-source/rights/search/cache vectors.
- `python3.12 scripts/check-living-studio.py`: **PASS**, embedded catalog regressions = 25.
- SliceBridge `node --test native/tests/source-queue-ui.test.js native/tests/my-printers-ui.test.js native/tests/brand-ui.test.js`: **28/28 PASS**.
- With `CHROME_BIN` explicitly set to installed Google Chrome, `node native/tests/source-queue-layout-qa.cjs`: **28/28 Chromium-rendered layout fixtures completed (exit 0)**, Hebrew/English, empty/1/2/8/12/15 files, window sizes ranging 720×500 to 1280×900.
- Representative measured outcomes: 1280×900 / 1 file **0px workspace overflow**; 1100×750 / 2 files **120px workspace scroll**; 900×830 / 2 files **60px workspace scroll**; 720×500 / 2 files **735px workspace scroll**. The Chrome headless inner viewport on macOS is shorter than the requested outer window height (e.g. 1100×750 gives actual 1100×607), so numbers are **not** native Wails client-area metrics.
**XIAS vs SliceBridge — real fixed-source evaluation, pinned upstream `plugin87/ux-ui-agent-skills@55156b40e3a9aafa52448bde76cdcb5147b958db`**:

Ran source-only, in a *separate temporary clone* with `npm install --ignore-scripts --no-audit --no-fund --no-package-lock`, Node 24, installed Chrome and `DS_REQUIRE_BROWSER=1`. No generated UI was committed to SliceBridge, and no provider hooks or model API calls were invoked. The target was the same SliceBridge `native/frontend/dist/index.html`, not a manufactured mock. Each command used `node scripts/<gate>.mjs <target> --widths=720,900,1100`:

| XIAS gate | Observed result | Assessment |
|---|---|---|
| `verify_overflow` | **PASS** — no clipped text/overlap at three widths | Rendered CSS/DOM check; does not assert zero vertical scroll |
| `verify_responsive` | **PASS** — no horizontal overflow at three widths | Consistent with SliceBridge's independent browser fixture |
| `verify_rtl` | **PASS** — 0 px RTL/LTR horizontal overflow | Checks mirroring/overflow, not complete Hebrew copy |
| `verify_target_size` | **PASS** — 42 targets >=24×24px or documented exceptions | Checks minimum interaction size, not keyboard usability |
| `measure_render` | **FAIL as implemented** — 8 alleged 4.5:1 text contrast violations | **NOT ACCEPTED AS EIGHT CONFIRMED APP DEFECTS** pending independent source-level adjudication |
| `axe_audit` | **PASS** — zero axe-core WCAG 2.2 A/AA violations on static DOM | Not native-app UI state and not a substitute for manual review |
| `verify_keyboard` | **PASS** — 14 controls + 0 composite widgets reachable, Enter/Space and arrows respond | Static fixture; product-specific Wails dialogs not exercised |
| `verify_reduced_motion` | **PASS** — reduced-motion policy present; transitions stopped, no content lost | Static-file render only |

A total of **7 of 8 executed XIAS gates returned PASS** and **1/8 (contrast) reported the eight findings below**. These are per-gate outcomes, **not** a clean overall application accessibility pass.

**False-positive adjudication of the eight XIAS contrast flags**:

- Four `span.target-printer-icon` glyphs `▣` are explicitly `aria-hidden="true"` decorative icons next to printed model-name text. XIAS compares their approximately **3.97:1** contrast to the **4.5:1 text threshold**; decorative glyphs are not required to meet the text criterion. They also exceed the 3:1 non-text criterion if assessed as information-bearing icons.
- Four child spans of `Add files` and `Convert` buttons are white on a **CSS gradient** (not a flat white background). The XIAS detector reports `1.00:1` because its ancestor `backgroundColor` read ignores `background-image:linear-gradient(110deg,#2F7F73,#193F38)`. Source color math for white on the two endpoint colors yields approximately **4.77:1** and **11.61:1** respectively. These are **likely detector errors**, and native-product raster verification remains appropriate before final accessibility signoff.
- This is a concrete reason to **compose complementary tools**: the in-repo browser layout harness is strong on scroll/reachability, while XIAS highlights categories such as contrast/targets, but its findings require semantic and gradient-aware review before a fail/pass decision.

- The layout harness's PASS means controls remain reachable and no unexpected horizontal overflow; it **does not prove the user's near-zero-scroll preference has been achieved**. The measurable residual scroll is a candidate for a follow-up layout optimization, not a fictitious full PASS.
- The first attempt used the test's default Edge path, which was unavailable on this host; an already-installed Chrome binary was selected instead. No browser installation required.

**Not completed in this pilot:** installed native Wails GUI screenshot verification on both operating systems, an Impeccable pinned detector run, UI Skills prompt-agent comparative repair, comprehensive keyboard tests and gradient-aware raster contrast certification, and real 3MF conversion. XIAS eight rendered gates *were* executed on the static desktop frontend; that is not the same as a fully verified product. Do not claim those from static or headless tests.

## Selection by task (no universal winner)

- **Compact source/target workflow, vanilla Wails:** start with existing app CSS + internal UI-SYSTEM and UI-AUDIT, feed XIAS objective gate cases, optionally UI Skills `improve-ui` for a read-only plan. Use 21st.dev/Spell/Design Spells as references, **not copied code**, until framework/license compatibility is proved.
- **New React administration screen:** compare shadcn/ui vs Mantine vs HeroUI vs Ant Design on the *same* dense form/table/RTL keyboard fixture. 21st.dev is the discovery entry point, not an assumed winner.
- **Complex keyframed micros:** compare Motion and GSAP with reduced-motion/fps/bundle/maintenance measurements. No engine installation solely for a button hover.
- **Angular interface:** keep Origin UI NG eligible; do not silently route to React Origin UI instead.
- **Icons in a distributable desktop app:** compare Lucide/Phosphor/Iconsax visually, then check notices per exact asset/package.

## Next admission / QA gates

1. Merge only via the normal independent QA workflow: this change is a **dependent PR** on draft #921, not a parallel rival registry or unilateral merge into main.
2. Evaluate a small fixed SliceBridge screenshot set with XIAS, pinned Impeccable and UI Skills focused instructions; log exact scripts/versions, false positives and actual repairs, not aesthetic assertions.
3. Investigate residual default scrolling using real Wails 1100×830 and 900×830 screenshots on Windows and macOS; change SliceBridge only via a separate owned PR, never in this intake.
4. If any source is selected for copied code or redistributed assets, pin package/commit, inspect licensing and complete the existing production release gate before embedding.
