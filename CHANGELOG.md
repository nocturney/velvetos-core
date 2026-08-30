# Changelog

All notable changes to Velvet Factory Headquarters & OS.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- 2026-08-30 ~18:17 Asia/Jerusalem — **vfcanva**: Canva ככלי תוכן לאינסטגרם (יצירה / ריסייז / סקירה; HQ לא שולח). Canva as Instagram content tool. [bc-2020e135-820c-40b6-a922-e2822b5e81bf](https://cursor.com/agents/bc-2020e135-820c-40b6-a922-e2822b5e81bf). Open [PR #6](https://github.com/nocturney/velvet-factory-headquarters-os/pull/6) (not merged). HQ-native; Origin not cloned.
- 2026-08-30 ~18:17 Asia/Jerusalem — **vfagents**: מיפוי 500-AI-Agents-Projects על המשרד הקיים. Mapped onto existing office. [bc-9765dc13-6ca2-4c51-a550-6dfb1d3b0027](https://cursor.com/agents/bc-9765dc13-6ca2-4c51-a550-6dfb1d3b0027). Open [PR #10](https://github.com/nocturney/velvet-factory-headquarters-os/pull/10) (not merged). HQ-native; Origin not cloned.
- 2026-08-30 ~18:17 Asia/Jerusalem — שתילת שיתוף ChatGPT. ChatGPT share embed overlay. [bc-40637134-3705-4fa3-8de8-2b05282cf23e](https://cursor.com/agents/bc-40637134-3705-4fa3-8de8-2b05282cf23e). Open [PR #1](https://github.com/nocturney/velvet-factory-headquarters-os/pull/1) (not merged; not a new pack).
- 2026-08-30 ~18:17 Asia/Jerusalem — הטמעת שיתוף Gemini (Perplexity לא נפתח). Gemini share embed overlay. [bc-970e9c12-9ce3-4501-b4e3-61320042defa](https://cursor.com/agents/bc-970e9c12-9ce3-4501-b4e3-61320042defa). Open [PR #2](https://github.com/nocturney/velvet-factory-headquarters-os/pull/2) (not merged; not a new pack).
- 2026-08-30 ~18:17 Asia/Jerusalem — הטמעת גוף Perplexity מה-PDF. Perplexity PDF embed overlay. [bc-33617d43-0488-4be5-97e1-d50b3d0ee4e0](https://cursor.com/agents/bc-33617d43-0488-4be5-97e1-d50b3d0ee4e0). Open [PR #5](https://github.com/nocturney/velvet-factory-headquarters-os/pull/5) (not merged; not a new pack).
- 2026-08-30 ~18:17 Asia/Jerusalem — חיבור מומחי Agency לכלים החיים. Agency tools workflow overlay. [bc-4b0e71c9-d130-44a2-8ca8-454521264392](https://cursor.com/agents/bc-4b0e71c9-d130-44a2-8ca8-454521264392). Open [PR #4](https://github.com/nocturney/velvet-factory-headquarters-os/pull/4) (not merged; not a new pack).
- 2026-08-30 ~18:17 Asia/Jerusalem — VF-G005 קרוסלת מדיה מקורית תחת `packages/vfcovers/g005` (לא פק חדש). Native carousel media. [bc-3afa6a77-f856-4237-8591-3e525e279f68](https://cursor.com/agents/bc-3afa6a77-f856-4237-8591-3e525e279f68). Open [PR #7](https://github.com/nocturney/velvet-factory-headquarters-os/pull/7) (not merged).
- 2026-08-30 ~18:17 Asia/Jerusalem — תזמורת Cursor+GPT+Gemini+Perplexity: בטיוטה, לא קוטלג כפק. Orchestra in progress, not catalogued. [bc-b6e689af-8efc-4190-a7a6-69d3a72b1770](https://cursor.com/agents/bc-b6e689af-8efc-4190-a7a6-69d3a72b1770). Draft [PR #11](https://github.com/nocturney/velvet-factory-headquarters-os/pull/11).
- 2026-08-30 — **The Agency**: הותקנו 273 סוכני Cursor מ-[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (`3c95888`) ככללי פרויקט ב-`.cursor/rules/`. Installed 273 Cursor specialists from The Agency as project rules; mention `@slug` to activate. Refresh: `scripts/install-agency-agents.sh`. Roster: `docs/AGENCY-AGENTS.md`.
- 2026-08-30 — **vfe2b**: מפת [awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) (209) לחמישה צוותי משרד על הפאקים הקיימים; בלי ראנטיים שני, בלי שליחה, בלי ₪ מומצא. Awesome-AI-agents desk: five crews on existing packs; no second runtime, no send, no invented ₪. [bc-21cee8d9-a82a-468d-b0a5-1d8fa87ef057](https://cursor.com/agents/bc-21cee8d9-a82a-468d-b0a5-1d8fa87ef057).
- 2026-08-30 — **vfmcp**: מחקר התאמת שרתי MCP לסטודיו מתוך awesome-mcp-servers (bc-1764e30f). שלושה פערים ראשונים: WhatsApp, Google Sheets, צינור הדפסה. MCP fit research from awesome-mcp-servers; first gaps: WhatsApp, Google Sheets, print pipeline. See `docs/MCP-FIT.md`.
- 2026-08-30 — פקודת קבע: גיטהאב הוא גיבוי רציף; כל פק חדש נרשם באותו יום במפה גם אם Origin לא משכפל. Standing order: GitHub is the constant backup; catalogue every new pack the same day even when Origin will not clone. See `docs/BACKUP.md`.
- 2026-08-30 — **vfbriefux**: מחקר פורמט הבריף (bc-9e0be231). Brief format research; Origin slug unknown, tree not cloned.

## [0.1.0] — 2026-08-30

- Initial GitHub backup of Cursor office packs.

### Added

- Headquarters catalog on GitHub (`packages/manifest.json`, `packages/<name>/ORIGIN.md`).
- `scripts/vendor-origin-packs.sh` to clone Origin trees when `origin auth login` or `CURSOR_API_KEY` is available.
- Pack list (one line each). Origin source trees were **not** copied in this environment (Origin CLI not logged in; GitHub token rejected by `origin.cursor.com`; pack agent transcripts not readable from this HQ).

#### Packs

- **vfigos** — VF Instagram OS: Instagram office pack (review and schedule; this HQ does not send). Origin `christian-velvet/tmp-20e9908caebda9d0`, [bc-c4a53ee3](https://cursor.com/agents/bc-c4a53ee3).
- **vfcost** — Studio cost pack: unit economics and spend, without invented prices. Origin `christian-velvet/tmp-8a55585f5a73bd06`, [bc-a4dc99c9](https://cursor.com/agents/bc-a4dc99c9).
- **vfconvert** — Conversion pack: inquiry-to-order path. Origin `christian-velvet/tmp-4460086f23171633`, [bc-9644a175](https://cursor.com/agents/bc-9644a175).
- **vfgrowth** — Growth pack: content sprints and acquisition work. Origin `christian-velvet/tmp-0093db8b6deea44f`, [bc-e68393a0](https://cursor.com/agents/bc-e68393a0).
- **vfprod** — Production pack: print-floor and job tracking. Origin `christian-velvet/tmp-c9ca74be9225ac7d`, [bc-cd4a5cde](https://cursor.com/agents/bc-cd4a5cde).
- **vfsales** — Sales pack: quotes and follow-up. Origin `christian-velvet/tmp-b467d4882113eabd`, [bc-28017566](https://cursor.com/agents/bc-28017566).
- **vfops** — Operations pack: run-the-studio procedures. [bc-93fbfca6](https://cursor.com/agents/bc-93fbfca6). Origin slug not found in this dump.
- **vfcovers** — Covers pack: brief and post cover art. [bc-390e0de1](https://cursor.com/agents/bc-390e0de1). Origin slug not found in this dump.
- **vfinsights** — Insights pack: performance reads; does not invent metrics. [bc-02df9e72](https://cursor.com/agents/bc-02df9e72). Origin slug not found in this dump.
- **vfbooks** — Books pack: receivables and studio ledger work. [bc-280dd241](https://cursor.com/agents/bc-280dd241). Origin slug not found in this dump.
- **vfresearch** — Research pack: source gathering and notes. [bc-01278e9b](https://cursor.com/agents/bc-01278e9b). Origin slug not found in this dump.
- **vfbiz** — Business pack: studio strategy and decisions. [bc-3921041e](https://cursor.com/agents/bc-3921041e). Origin slug not found in this dump.
- **vfcopy** — Copy desk: homework, draft, and lint. [bc-b6bc8b8c-136d-4d95-812e-177991534e42](https://cursor.com/agents/bc-b6bc8b8c-136d-4d95-812e-177991534e42). Origin slug not found in this dump.
- **vlicense** — License gate: studio license / access check. [bc-0a6460b1](https://cursor.com/agents/bc-0a6460b1). Origin slug not found in this dump.
- **vfseason** — Seasonal calendar: studio calendar and season marks. [bc-2a4a3260](https://cursor.com/agents/bc-2a4a3260). Origin slug not found in this dump.
- **vfsku** — SKU cards and repeats: product cards and reprint runs. [bc-68f7f06c](https://cursor.com/agents/bc-68f7f06c). Origin slug not found in this dump.

See **Unreleased** for **The Agency** (273 Cursor specialists), **vfmcp** (MCP fit research; HQ-native), and **vfe2b** (awesome-ai-agents desk; HQ-native).

[Unreleased]: https://github.com/nocturney/velvet-factory-headquarters-os/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nocturney/velvet-factory-headquarters-os/releases/tag/v0.1.0
