# awesome-ai-motion phase 1 intake (2026-10-18)

**Status:** `P2 INTAKE RECORDED / IMPLEMENTATION NOT RUN`.
**Issue:** [#716](https://github.com/nocturney/velvetos-core/issues/716) phase 1 only.
**Queue:** CLQ-7 on [#612](https://github.com/nocturney/velvetos-core/issues/612).
**Owner of a later trial:** `vf-post-production-craft` and Creative Media Orchestration, inside the existing Creative Craft 2.0 → `vfom` path. This file does not add a renderer, skill, registry row, scheduler, or publish path.
**Not in this pass:** `Tejashmakwana/motionmaxxing` (already a separate #716 candidate and registry row `candidate-intake-tejashmakwana-motionmaxxing`). No install, no `npm`, no Playwright, no Chromium, no FFmpeg, no render.

## Pinned source

| Field | Value |
| --- | --- |
| Upstream | https://github.com/gongnyang/awesome-ai-motion |
| Default branch | `main` |
| Commit | `1e3c249073c61b42ceb556d7800f628d565d9312` |
| Commit date | 2026-09-30T09:45:54Z |
| Subject | Fix path-highlight and vector-tip-to-tail clips |
| Tree | `8d3fcc05f852a0705f0cfd28cd328cd686db5e19` |
| Parent | `5ab08c26a23e1c66268fbc06b9984de90f66d46e` |
| GitHub profile | `gongnyang` (name field `kongnyng`, location empty). Commit author name on the pin is `kimsh-1` (that login 404s). |
| Stars at read | 245 |
| Repo size at read | 58372 KB |
| Archive flag | not archived |

Provenance of this read: GitHub REST on 2026-10-18 for the commit object, root listing, `LICENSE`, `package.json`, `README.md`, `SKILL.md`, `ATTRIBUTIONS.md`, `lib/gsap.min.js`, `lib/stage.css`, and `lib/fonts/*.ttf`. A depth-1 clone of the same SHA was used only to count files and scan URL strings. Nothing was executed.

README at this SHA says "637 techniques · 128 reference clips · 11 recipes · 7 design routes". Counted on the tree: **129** `effects/*/index.html`, **11** `recipes/*/index.html`, **7** `routes/` entries. `index.json` is about 3.5 MB and was not re-counted (the contents API rejects it). The 637 figure stays a README claim.

What it is: an effect-selection field guide plus HTML/GSAP/SVG templates and an agent `SKILL.md`. It is not a generative video model. Default stage in `lib/stage.css` is **1280×720**, not 1080×1920.

## Licenses

#632 as applied here: any license, including NC, may be sold. The Israeli-creator approval gate applies only to 3D-printing models. This repository is HTML motion templates, not a print model. No Israeli-creator stop was found, and none is required for this intake.

| Asset | What was checked | License |
| --- | --- | --- |
| Repository original work | `LICENSE` (SHA-256 `34ed46f84ea23835415254acb1ca2432bb3143f3dc5cf79d5220d755d27a17d9`); `package.json` `"license": "MIT"`; `ATTRIBUTIONS.md` says clip implementations, cards, and prompts are original and MIT, and that `effects/` and `recipes/` do not copy third-party code | MIT, Copyright (c) 2026 gongnyang. GitHub API SPDX is `NOASSERTION` because the LICENSE text points at third-party files. |
| `lib/gsap.min.js` | 72779 bytes, SHA-256 `c174bfce53a729418d57a8ad8625e7247c793a22fef8e2851e3cfa3de9cd8280`. Header: GSAP 3.14.2, Copyright 2025 GreenSock, "Subject to the terms at https://gsap.com/standard-license" | GreenSock / Webflow **Standard License** (not MIT, not open source). Page read 2026-10-18 (effective 2025-04-30, modified 2025-05-30): no-charge use, including commercial projects, is allowed. Prohibited use is a no-code visual animation builder that competes with Webflow. Reverse engineering GSAP to build that kind of product is prohibited. Notices must stay. Webflow can revise later terms; already-licensed copies of this version stay on the terms that applied when they were taken. |
| `lib/fonts/BodoniModa.ttf` | Name table: family `Bodoni Moda`, version 2.005, copyright 2020 The Bodoni Moda Project Authors, SHA-256 `550f5e34ee0a828d7941b1fe9bc58b34e5260d3f33a61532e6d0a0114e79a5cf` | SIL Open Font License 1.1, as named in the font and in `ATTRIBUTIONS.md` (upstream: indestructible-type/Bodoni, Owen Earl). OFL forbids selling the font alone. Embedding in a document or program is the usual OFL grant. |
| `lib/fonts/IBMPlexMono-Regular.ttf` | Name table: family `IBM Plex Mono`, version 2.3, copyright 2017 IBM Corp., SHA-256 `6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46` | SIL Open Font License 1.1, as named in the font and in `ATTRIBUTIONS.md` (upstream: IBM/plex). Same OFL resale limit on the font file itself. |
| Site webfonts, not in `lib/fonts` | `ATTRIBUTIONS.md` plus `<link>` tags under `site/` | Noto Serif KR via `fonts.googleapis.com` (OFL 1.1, not vendored). Pretendard 1.3.9 via `cdn.jsdelivr.net` (OFL 1.1, not vendored). |
| Concept citations | `ATTRIBUTIONS.md` rows only. Not re-audited as copied code. | Mixed, and **not** a reason to reject the MIT templates under #632. Notable rows: `DavidHDev/react-bits` MIT + Commons Clause; `IanLunn/Hover` MIT for personal/open-source plus a paid commercial license; `3b1b/videos` CC-BY-NC-SA-4.0 on two chapter files; several Adobe/Flourish/unknown rows. Those are cited techniques. They are not a grant to copy those repos. |

`lib/stage.css` sets `--serif` to `"Noto Serif KR"` and `--sans` to `"Pretendard"` but does not `@import` them. Clip HTML loads `../../lib/gsap.min.js` and `../../lib/stage.css` only.

## Dedupe

`candidate-registry-v0.json` has **no** row for `gongnyang/awesome-ai-motion`, `iart-ai/motion-design-skills`, `bangtutorial/bang-motion`, HyperFrames, Remotion, or Manim (string search on 2026-10-18). This pass does not add one. #595 still owns registry reconciliation. Overlap with the current stack is not a rejection.

| Existing tool | Where it already lives | Same job? |
| --- | --- | --- |
| HyperFrames | Canonical master compositor. `packages/vfom/VIDEO-TOOLCHAIN.json` `animationSlots.hyperframes`. Bridge `scripts/vf_hyperframes.py`. Pin in `packages/vfom/HYPERFRAMES-BACKEND.json`: package `hyperframes`, minimum/recovery `0.8.34`, Node `>=22`, requires `ffmpeg` and `ffprobe`, `networkInstallAllowed: false`. | Same broad class (HTML to video) and already the Foundry renderer. awesome-ai-motion also **cites** `heygen-com/hyperframes` and "local/HyperFrames-skills" as concept sources in `ATTRIBUTIONS.md`. It does not replace the compositor. A later adapter would be a template source feeding the existing render host, not a second pipeline. |
| Remotion | `VIDEO-TOOLCHAIN.json` slot `remotion`, origin `remotion-dev/remotion`, reviewed baseline 4.0.523, `installByDefault: false`, Free License eligible at business headcount 1. `packages/vfom/LOCK.md` keeps it optional. | React component animation. Different runtime from GSAP templates. Not installed by this intake. |
| Manim | `VIDEO-TOOLCHAIN.json` slot `manim`, origin `ManimCommunity/manim`, MIT, minimum 0.21.0, host-smoke historical evidence on sderot-windows and sderot-mac. Forbidden as physical-product proof. | Python explainer / diagram slot. `ATTRIBUTIONS.md` cites ManimCommunity and `3b1b/manim` as technique sources. Not the same renderer. |
| motion-design-skills | `iart-ai/motion-design-skills`, MIT, HEAD `3c129f769d90a1328c209c386492333c9ac62312` (2026-06-22). Already named as a knowledge source in `docs/CREATIVE-CRAFT-DEEP-RESEARCH-GRAFT-ROUND2-2026-10-03.md` and `.cursor/skills/vf-post-production-craft/references/provenance.md`. | Craft language (timing, restraint, consistency). Not a clip renderer. awesome-ai-motion cites the sibling `iart-ai/webgl-animation-skills`, not this skills repo, in `ATTRIBUTIONS.md`. |
| bang-motion | **Absent** from this repo's docs and registry. Public repo `bangtutorial/bang-motion`, MIT, HEAD `c1aa65e921c970d858705fcb4a53a8294d1a4131` (2026-09-15), "agent skill for browser motion graphics" and a single `index.html`. | Same product class as this intake (agent skill + browser motion). Not vendored. Do not open a second motion pipeline for it inside this phase. |
| motionmaxxing | Registry id `candidate-intake-tejashmakwana-motionmaxxing`. #716 already records it as research-only. | Sibling HTML/GSAP/FFmpeg candidate. Out of scope here. |
| html-video | Registry id `candidate-nexu-io-html-video`, routed to `creative-video-rendering` in `owner-repo-intake-2026-10-13.md`. | Another local HTML + FFmpeg idea. Already tracked. |

## Renderer sandbox risk

Source read: `scripts/render.mjs` and `package.json` at the pinned SHA. Not executed.

- **Node.** `engines.node` is `>=20`. The existing HyperFrames host contract is Node `>=22`. A later fixture has to pick one host Node and not assume they match.
- **Playwright.** `devDependencies.playwright` is `^1.50.0` (floating). `loadPlaywright()` imports `playwright` or falls back to the global npm root. `chromium.launch({ headless: true })` passes no extra args. The script does not disable the Chromium sandbox, and it also does not set a network allowlist, a user-data dir, or `--disable-background-networking`.
- **Local server.** `127.0.0.1` on port 0. It serves rewritten input HTML plus files under `lib/` and the input directory. Path checks use `path.relative` and `realpath`. That is a local file server, not an authentication boundary.
- **FFmpeg.** `execFileSync('ffmpeg', [...])` with an argument array (no shell). Writes `clip.mp4` (libx264, yuv420p, 30 fps from JPEG frames), `preview.gif`, and `poster.jpg`. Default `--jobs` is 3.
- **Writes.** Without `--out`, output is written **beside the source `index.html`**. `--all` would write into the checkout. A later fixture must set an explicit output directory outside the upstream tree.
- **Default frame.** Capture size comes from `window.__size` or **1280×720**. `lib/stage.css` is 1280×720. #716 phase 2 asks for 1080×1920. That resize is not in this renderer.
- **Network.** All 140 `effects/*/index.html` and `recipes/*/index.html` files lack `fonts.googleapis.com` and `jsdelivr` link tags. Their GSAP and stage CSS are local. `site/**/*.html` does load Google Fonts and jsDelivr Pretendard. Chromium is still allowed to open the network, so rendering a `site/` page, or any HTML that later gains a remote URL, would egress. This intake did not run a packet capture.
- **Type.** Korean sample strings are in the templates (`lang="ko"`). Hebrew RTL, safe-area, and 9:16 are not implemented in `render.mjs` or `stage.css`. `--text` replaces a `data-slot` before the timeline starts. That is a string replace, not a shaping or direction engine.
- **Compute.** Frame-by-frame JPEG screenshots at 30 fps, default concurrency 3, then FFmpeg. Unmeasured here. Do not run it on a host that is already in the #612 / #604 P0 lease.

## Decision

Keep as a **research-only template catalog** for a later, separately approved fixture. Do not install it, do not render it, and do not point `vf_hyperframes.py` at it in this change.

Phase 2 (not authorized here) would be three synthetic clips on an isolated host, explicit `--out`, network egress recorded, GSAP Standard License notice kept next to `lib/gsap.min.js`, OFL notices kept next to the two font files, and a check that the output is 1080×1920 only if the template is actually changed to that size. Until that evidence exists, HyperFrames remains the compositor and Manim/Remotion remain the existing subordinate slots.
