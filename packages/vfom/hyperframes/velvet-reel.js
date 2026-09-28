/* Velvet Factory HyperFrames runtime: deterministic overlays only. */
(function () {
  "use strict";

  const BRAND_TOKENS = "../../vfbrand/brand-tokens.json";
  // Resolve repo assets against this runtime file (packages/vfom/hyperframes/velvet-reel.js),
  // not document.baseURI: `hyperframes render <repo> -c <template>` serves the composition
  // from the project root, so page-relative ../../ paths escape the repo.
  const RUNTIME_URL = (document.currentScript && document.currentScript.src)
    || Array.from(document.scripts).map((s) => s.src).find((src) => /\/velvet-reel\.js(?:[?#]|$)/.test(src))
    || document.baseURI;

  function repoAsset(repoPath) {
    if (!repoPath) return "";
    if (/^(?:https?:|data:|blob:)/i.test(repoPath)) return repoPath;
    if (repoPath.startsWith("packages/")) {
      return new URL("../../" + repoPath.slice("packages/".length), RUNTIME_URL).href;
    }
    return new URL(repoPath, document.baseURI).href;
  }

  async function loadTokens() {
    const response = await fetch(new URL(BRAND_TOKENS, RUNTIME_URL));
    if (!response.ok) throw new Error("brand-tokens.json unavailable: " + response.status);
    const tokens = await response.json();
    if (tokens?.brand !== "Velvet Factory") throw new Error("brand token identity mismatch");
    return tokens;
  }

  function accentFrom(tokens, vars) {
    const samples = tokens?.accents?.samples || [];
    if (vars.accentId) {
      const hit = samples.find((row) => row.id === vars.accentId);
      if (!hit) throw new Error("unknown accentId: " + vars.accentId);
      return hit.hex;
    }
    if (vars.accentHex && vars.accentSource) return vars.accentHex;
    throw new Error("accent requires token accentId or verified accentHex+accentSource");
  }

  function applyTokens(tokens, vars) {
    const accent = accentFrom(tokens, vars);
    const gold = tokens?.brandMark?.gold?.hex;
    if (!gold) throw new Error("brand gold token missing");
    document.documentElement.style.setProperty("--vf-accent", accent);
    document.documentElement.style.setProperty("--vf-brand-gold", gold);
    return {
      accent,
      gold,
      logo: repoAsset(tokens?.logo?.preferred?.overlay || ""),
      headlineFont: tokens?.fonts?.roles?.headline,
      subheadFont: tokens?.fonts?.roles?.subhead,
      latinFont: tokens?.fonts?.roles?.latinDisplay,
    };
  }

  function text(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value || "";
  }

  function media(id, value) {
    const node = document.getElementById(id);
    // data-var-src elements are bound by HyperFrames itself before media discovery,
    // so video frames are extracted and audio is mixed; never race it at runtime.
    if (!node || !value || node.hasAttribute("data-var-src")) return;
    node.setAttribute("src", repoAsset(value));
  }

  const presets = {
    HEADLINE_REVEAL(tl, target, at = 0.20) {
      tl.fromTo(target, { opacity: 0, y: 38 }, { opacity: 1, y: 0, duration: 0.55 }, at);
    },
    ACCENT_RULE_WIPE(tl, target, at = 0.62) {
      tl.fromTo(target, { scaleX: 0 }, { scaleX: 1, duration: 0.42 }, at);
    },
    CHIP_SEQUENCE(tl, targets, at = 1.10) {
      Array.from(targets || []).forEach((target, index) => {
        tl.fromTo(target, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.30 }, at + index * 0.22);
      });
    },
    INSET_POP(tl, target, at = 2.05) {
      if (target) tl.fromTo(target, { opacity: 0, scale: 0.90 }, { opacity: 1, scale: 1, duration: 0.38 }, at);
    },
    VELVET_HARD_CUT(tl, target, at = 0) {
      if (target) tl.set(target, { opacity: 1, visibility: "visible" }, at);
    },
    VELVET_MACRO_PUNCH(tl, target, at = 0, duration = 0.32) {
      if (target) tl.to(target, { scale: 1.055, duration }, at);
    },
    VELVET_MATERIAL_LABEL(tl, target, at = 0) {
      if (target) tl.fromTo(target, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.32 }, at);
    },
    VELVET_FINAL_STAMP(tl, target, at = 0) {
      if (target) tl.fromTo(target, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 0.48 }, at);
    },
  };
  async function boot(compositionId, setup) {
    const vars = window.__hyperframes?.getVariables?.() || {};
    const tokens = await loadTokens();
    const applied = applyTokens(tokens, vars);
    await document.fonts.ready;
    const tl = gsap.timeline({ paused: true });
    await setup({ vars, tokens, applied, tl, presets, text, media, repoAsset });
    window.__timelines = window.__timelines || {};
    window.__timelines[compositionId] = tl;
    if (typeof window.__hfForceTimelineRebind === "function") window.__hfForceTimelineRebind();
  }

  window.VelvetReel = { boot, presets, repoAsset };
})();
