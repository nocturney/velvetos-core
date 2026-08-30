# Changelog

All notable changes to Velvet Factory Headquarters & OS.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- 2026-08-30 — **vffcc**: מפת [free-claude-code](https://github.com/Alishahryar1/free-claude-code) — פרוקסי מקומי BYOK, לא חוסך Cursor Cloud, בלי `fcc-server` ב־HQ. נהלי thrift / ניתוב / הורדה למק אחרי ראש צוות. FCC fit: local BYOK map only; does not cut this Cloud Agent bill. See `docs/FCC-FIT.md`.
- 2026-08-30 — **vfmem**: הטמעת דפוס [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) כגרף משרד חי (`scripts/vfmem.py`) על המפות הקיימות. בלי הבינארי, בלי דמון, בלי UI. Embedded the CBM query pattern as a live office graph over existing maps; no third-party binary. See `docs/VFMEM.md`.
- 2026-08-30 — **vfgraft**: דפוס [Graft](https://github.com/trailhq/Graft) כמפת משרד ב-Markdown (MAP + 12 צמתים + blast). בלי npm, בלי MCP, בלי מפתח ספק. Graft pattern as a committed office graph; skip the CLI. See `docs/GRAFT.md`, `packages/vfgraft/`.
- 2026-08-30 — **תזמורת**: פלייבוק 06:15 + מעבר ערב. ChatGPT וג׳מיני הוטמעו לפקים קיימים (מדף מק״ט, תבניות וואטסאפ, וי לפני הדפס, כרטיס עלות בלי ₪). Perplexity דולג — חומת מנוי, אין גוף. See `constitution/ORCHESTRA.md`, `docs/ORCHESTRA-2026-08-30.md`.
- 2026-08-30 — **VF-G005 d12b**: כיתוב מאושר (הוק + חמש עובדות השקפים + וואטסאפ / איסוף שדרות). לא פורסם. `packages/vfcopy/G005-d12b.md`.
- 2026-08-30 — **VF-G005**: קרוסלת פיד חדשה (נייבי/זהב, 1080×1350) לשיבוץ ב־instagram.com, כיתוב d12b. New native-IG carousel slides. `packages/vfcovers/g005/`.
- 2026-08-30 — **Perplexity PDFs:** הבעלים המיר את השיחה שנחסמה ב־Cloudflare; הגוף הוטמע במקום על vfops/vfigos/vfsales/vfcost/vfprod/vfconvert/vfbiz/vfbooks/… בלי פק חדש, בלי ₪, בלי בוט/אתר/ווידג׳ט חי. Owner converted the blocked Perplexity thread to PDFs; body mapped onto existing packs in place. See `docs/SHARES-2026-08-30.md`.
- 2026-08-30 — **Perplexity follow-up:** Cursor פתח את השיתוף בדפדפן אמיתי; נקרא רק דף Cloudflare («יש לאמת שאינך רובוט»). גוף השיחה לא הוטמע ולא הומצא. Cursor opened the Perplexity URL in a real browser; only the Cloudflare wall was readable. Thread body not invented. `packages/vfresearch/sources/perplexity-c950af30.md`.
- 2026-08-30 — **Gemini+Perplexity:** נקרא שיתוף ג׳מיני (סוכני בינה לעסק הדפסות) והוטמע במקום על vfops/vfgrowth/vfcopy/… + חוקה; פרפלקסיטי לא נפתח (Cloudflare) ולא הומצא. Gemini share read and embedded in place on existing packs + constitution; Perplexity blocked, not invented. See `docs/SHARES-2026-08-30.md`.
- 2026-08-30 — שתילת שיתוף ChatGPT (סוכני בנייה) לתוך הפקים הקיימים, החוקה והבריף — בלי פק חדש, בלי שליחה חיה, בלי מחירי ₪ מומצאים. Embedded ChatGPT share “building agents” into existing packs, constitution, and daily brief packet — no new tools, no live send, no invented ILS. See `docs/SHARE-EMBED-he.md`.
- 2026-08-30 — **שולחן Agency + כלים**: 28 סוכנים רלוונטיים חוברו לחמישה מושבים, לפקים, ולג׳ימייל (קריאה בלבד) / לוח שנה / דרייב / Superdesign / Treg / Mobbin. Desk overlay wires 28 relevant Agency specialists to the five seats, VF packs, and live tools (Gmail read-only, Calendar, Drive-by-job, Superdesign, Treg, Mobbin). See `docs/AGENCY-TOOLS.md`, `.cursor/vf-desk.json`, `.cursor/rules/velvet-factory-desk.mdc`.
- 2026-08-30 — **vfcanva**: Canva אומת ב-Desktop (עיצוב `DAGoYmCu4c4`). Cloud Agent עדיין בלי Canva. Desktop Canva verified; this cloud run still cannot call it.
- 2026-08-30 — **vfcanva**: תוסף מקומי + HTTP MCP + סטודיו PNG; בדיקה רק ב-Agent מקומי. Local plugin + HTTP MCP + studio PNG; verify in a local Agent chat only.
- 2026-08-30 — **vfcanva**: Canva ככלי תוכן לאינסטגרם `@velvets_cloud` (יצירה / שינוי גודל / סקירה; HQ לא שולח). Canva is the Instagram visual tool for `@velvets_cloud` (create / resize / review; HQ does not send). See `docs/CANVA.md`.
- 2026-08-30 — **vfagents**: מפת [500-AI-Agents-Projects](https://github.com/ashishpatel26/500-AI-Agents-Projects) על החבילות הקיימות + 12 נהלי משרד. בלי CrewAI חי, בלי שליחה. Fit map and twelve office playbooks; no live agent runtime. See `docs/500-AGENTS.md`.
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

See **Unreleased** for **vfcanva** (Canva Instagram desk; HQ-native), **The Agency** (273 Cursor specialists), **vfmcp** (MCP fit research; HQ-native), **vfe2b** (awesome-ai-agents desk; HQ-native), **vfagents** (500-list playbooks; HQ-native), **vfgraft** (Graft office graph; HQ-native), **vfmem** (HQ memory graph; HQ-native), and **vffcc** (Free Claude Code fit; HQ-native).

[Unreleased]: https://github.com/nocturney/velvet-factory-headquarters-os/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nocturney/velvet-factory-headquarters-os/releases/tag/v0.1.0
